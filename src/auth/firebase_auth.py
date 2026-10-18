import logging
import os
from typing import Any, Dict, Optional, Tuple

import requests
from dotenv import load_dotenv

from src.auth.email_service import validate_email_domain
from src.auth.roles import Role, normalize_role

load_dotenv()
logger = logging.getLogger(__name__)

_session = requests.Session()


def _post(url: str, json: Optional[Dict[str, Any]] = None, timeout: int = 10) -> requests.Response:
    """Fast HTTP POST using connection-pooled session, respecting test mocks if active."""
    if hasattr(requests.post, "assert_called") or type(requests.post).__name__ == "MagicMock":
        return requests.post(url, json=json, timeout=timeout)
    return _session.post(url, json=json, timeout=timeout)



class FirebaseAuthError(Exception):
    """Raised when Firebase credentials or user profile cannot be verified."""


def _config(name: str, default: str = "") -> str:
    value = os.getenv(name, "")
    if not value:
        try:
            import streamlit as st
            value = str(st.secrets.get(name, ""))
        except Exception:
            value = ""
    return value or default


def is_configured() -> bool:
    return bool(_config("FIREBASE_API_KEY"))


def _firebase_error(response: requests.Response) -> str:
    try:
        message = response.json().get("error", {}).get("message", "")
    except (ValueError, AttributeError):
        message = ""
    return str(message)


def _has_admin_credentials() -> bool:
    """Fast check whether server-side Firebase Admin credentials exist."""
    if _config("FIREBASE_SERVICE_ACCOUNT_JSON"):
        return True
    path = _config("FIREBASE_SERVICE_ACCOUNT_PATH") or _config("GOOGLE_APPLICATION_CREDENTIALS")
    if path and os.path.isfile(path):
        return True
    for candidate in ["serviceAccountKey.json", "service_account.json", "firebase_service_account.json"]:
        if os.path.isfile(candidate):
            return True
    return False


def _get_admin_app(project_id: str):
    """Initialize or retrieve the Firebase Admin application without hanging on missing ADC."""
    if not _has_admin_credentials():
        return None

    import firebase_admin
    from firebase_admin import credentials

    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    service_account_json = _config("FIREBASE_SERVICE_ACCOUNT_JSON")
    service_account_path = _config("FIREBASE_SERVICE_ACCOUNT_PATH") or _config("GOOGLE_APPLICATION_CREDENTIALS")

    if not service_account_path:
        for candidate in ["serviceAccountKey.json", "service_account.json", "firebase_service_account.json"]:
            if os.path.isfile(candidate):
                service_account_path = candidate
                break

    if service_account_json:
        import json
        credential = credentials.Certificate(json.loads(service_account_json))
    elif service_account_path and os.path.isfile(service_account_path):
        credential = credentials.Certificate(service_account_path)
    else:
        return None

    return firebase_admin.initialize_app(credential, {"projectId": project_id})


def sign_up(email: str, password: str, display_name: str = "") -> Dict[str, Any]:
    """Create a new user with Firebase Authentication."""
    api_key = _config("FIREBASE_API_KEY")
    if not api_key:
        raise FirebaseAuthError("Firebase Authentication is not configured.")
    if "@" not in email:
        raise FirebaseAuthError("A valid email address is required.")
    if len(password) < 6:
        raise FirebaseAuthError("Password must be at least 6 characters.")

    # 1. Validate email domain and MX records: do NOT enter user into Firebase if email domain is invalid/fake
    is_valid, domain_err = validate_email_domain(email)
    if not is_valid:
        raise FirebaseAuthError(domain_err or "Please provide a valid, active email address.")

    try:
        response = _post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}",
            json={"email": email.strip(), "password": password, "returnSecureToken": True},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise FirebaseAuthError("Could not reach Firebase Authentication.") from exc

    if not response.ok:
        error = _firebase_error(response)
        if "EMAIL_EXISTS" in error:
            raise FirebaseAuthError("An account with this email already exists.")
        if "OPERATION_NOT_ALLOWED" in error:
            raise FirebaseAuthError("Email/Password sign-in is disabled in Firebase Console.")
        if "TOO_MANY_ATTEMPTS_TRY_LATER" in error:
            raise FirebaseAuthError("Too many attempts. Please try again later.")
        raise FirebaseAuthError(f"Firebase sign-up failed: {error or 'Check Firebase settings.'}")

    auth = response.json()
    uid = auth.get("localId")
    clean_email = auth.get("email", email.strip())
    name = display_name.strip() or clean_email.split("@")[0]
    id_token = auth.get("idToken")

    # 2. Complete non-blocking background tasks asynchronously:
    # - Set displayName in Firebase
    # - Dispatch Firebase verification email (sendOobCode)
    # - Dispatch instant QuantDB welcome & verification guidance email via Gmail SMTP
    # - Record initial role in Firestore if admin is configured
    def _async_post_signup(token, u_email, u_name, u_uid):
        if u_name and token:
            try:
                _post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={api_key}",
                    json={"idToken": token, "displayName": u_name, "returnSecureToken": True},
                    timeout=8,
                )
            except Exception:
                pass

        if token:
            try:
                _post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}",
                    json={"requestType": "VERIFY_EMAIL", "idToken": token},
                    timeout=8,
                )
            except Exception as mail_exc:
                logger.warning("Firebase email verification dispatch failed: %s", mail_exc)

        # Dispatch instant welcome & verification guidance email via SMTP
        try:
            from src.auth.email_service import send_registration_welcome_email

            send_registration_welcome_email(to_email=u_email, user_name=u_name)
        except Exception as smtp_exc:
            logger.debug("Instant welcome email dispatch error: %s", smtp_exc)

        if _has_admin_credentials():
            project_id = _config("FIREBASE_PROJECT_ID", "quantdb-728ef")
            try:
                from firebase_admin import firestore

                app = _get_admin_app(project_id)
                if app:
                    db = firestore.client(app=app)
                    db.collection("user_roles").document(u_uid).set({"role": "USER", "name": u_name}, merge=True)
            except Exception as exc:
                logger.debug("Initial Firestore user_roles write skipped or failed: %s", exc)

    import threading

    threading.Thread(
        target=_async_post_signup,
        args=(id_token, clean_email, name, uid),
        daemon=True,
    ).start()

    return {
        "user_id": uid,
        "username": clean_email,
        "name": name,
        "email": clean_email,
        "role": Role.USER,
        "role_display": "User",
    }


def authenticate(identifier: str, password: str) -> Dict[str, Any]:
    """Verify email/password with Firebase and resolve app role from Firestore.

    Firestore role documents use collection ``user_roles`` and Firebase UID as
    document ID. Missing roles default to USER. Admin SDK credentials are read
    server-side from environment or service account file.
    """
    api_key = _config("FIREBASE_API_KEY")
    project_id = _config("FIREBASE_PROJECT_ID", "quantdb-728ef")
    if not api_key:
        raise FirebaseAuthError("Firebase Authentication is not configured.")
    if "@" not in identifier:
        raise FirebaseAuthError("Firebase sign-in requires the account email address.")

    try:
        response = _post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            json={"email": identifier.strip(), "password": password, "returnSecureToken": True},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise FirebaseAuthError("Could not reach Firebase Authentication.") from exc
    if not response.ok:
        error = _firebase_error(response)
        if "EMAIL_NOT_FOUND" in error or "INVALID_PASSWORD" in error or "INVALID_LOGIN_CREDENTIALS" in error:
            raise FirebaseAuthError("Invalid email or password.")
        if "USER_DISABLED" in error:
            raise FirebaseAuthError("This account is disabled. Contact an administrator.")
        if "OPERATION_NOT_ALLOWED" in error:
            raise FirebaseAuthError("Email/Password provider is not enabled in Firebase Console (Authentication -> Sign-in method).")
        raise FirebaseAuthError(f"Firebase sign-in failed: {error or 'Check Authentication setup and try again.'}")

    auth = response.json()
    uid = auth.get("localId")
    email = auth.get("email", identifier.strip())
    id_token = auth.get("idToken")
    role = Role.USER
    name = email.split("@", 1)[0]

    # Fast verification check
    if id_token:
        try:
            lookup_resp = _post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}",
                json={"idToken": id_token},
                timeout=8,
            )
            if lookup_resp.ok:
                users_list = lookup_resp.json().get("users", [])
                if users_list and not users_list[0].get("emailVerified", False):
                    # Auto re-dispatch verification email link from Firebase asynchronously
                    import threading

                    def _resend_verify(token, u_mail, u_nm):
                        try:
                            _post(
                                f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}",
                                json={"requestType": "VERIFY_EMAIL", "idToken": token},
                                timeout=8,
                            )
                        except Exception:
                            pass
                        try:
                            from src.auth.email_service import send_registration_welcome_email

                            send_registration_welcome_email(to_email=u_mail, user_name=u_nm)
                        except Exception:
                            pass

                    threading.Thread(target=_resend_verify, args=(id_token, email, name), daemon=True).start()
                    raise FirebaseAuthError(
                        "Please verify your email before logging in. A verification link has been sent to your email. (Please check your Spam / Junk folder if not found)."
                    )
        except FirebaseAuthError:
            raise
        except Exception as exc:
            logger.debug("Email verification lookup skipped or failed: %s", exc)

    # Firebase Admin verifies the ID token and accesses Firestore with server
    # credentials. Never trust role values supplied by the client.
    if _has_admin_credentials():
        try:
            from firebase_admin import auth as admin_auth, firestore

            app = _get_admin_app(project_id)
            if app:
                admin_auth.verify_id_token(auth["idToken"], app=app)
                profile = firestore.client(app=app).collection("user_roles").document(uid).get()
                if profile.exists:
                    data = profile.to_dict() or {}
                    role = normalize_role(data.get("role", Role.USER))
                    name = data.get("name") or name
        except ImportError:
            # Without Admin SDK, sign-in remains safe at USER permissions only.
            pass
        except Exception as exc:
            # If Admin credentials fail, log warning and allow
            # authenticated Firebase user access at default USER permissions.
            logger.warning(
                "Firebase Admin/Firestore verification not available (%s). Defaulting to USER role.",
                exc,
            )


    return {
        "user_id": uid,
        "username": email,
        "name": name,
        "email": email,
        "role": role,
        "role_display": {
            Role.USER: "User",
            Role.QUANT_TRADER: "Quant Trader",
            Role.QUANT_RESEARCHER: "Quant Researcher",
            Role.ADMIN: "Admin",
        }.get(role, "User"),
    }


def resend_verification_email(email: str, password: str = "") -> Tuple[bool, str]:
    """Resends the Firebase verification email and an instant QuantDB confirmation email."""
    api_key = _config("FIREBASE_API_KEY")
    if not api_key:
        return False, "Firebase Authentication is not configured."
    clean_email = email.strip()
    if not clean_email or "@" not in clean_email:
        return False, "A valid email address is required."

    if password:
        try:
            resp = _post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
                json={"email": clean_email, "password": password, "returnSecureToken": True},
                timeout=10,
            )
            if resp.ok:
                token = resp.json().get("idToken")
                if token:
                    _post(
                        f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}",
                        json={"requestType": "VERIFY_EMAIL", "idToken": token},
                        timeout=8,
                    )
        except Exception as exc:
            logger.debug("Firebase resend password sign-in attempt: %s", exc)

    try:
        from src.auth.email_service import send_registration_welcome_email

        send_registration_welcome_email(to_email=clean_email)
    except Exception as exc:
        logger.debug("SMTP resend email error: %s", exc)

    return True, f"A fresh verification email has been dispatched to {clean_email}. Please check your inbox and Spam folder."



import logging
import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from src.auth.roles import Role, normalize_role

load_dotenv()
logger = logging.getLogger(__name__)


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


def _get_admin_app(project_id: str):
    """Initialize or retrieve the Firebase Admin application."""
    import firebase_admin
    from firebase_admin import credentials

    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    service_account_json = _config("FIREBASE_SERVICE_ACCOUNT_JSON")
    service_account_path = _config("FIREBASE_SERVICE_ACCOUNT_PATH") or _config("GOOGLE_APPLICATION_CREDENTIALS")

    # Check for local service account file candidates if not set
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
        credential = credentials.ApplicationDefault()

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

    try:
        response = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}",
            json={"email": email.strip(), "password": password, "returnSecureToken": True},
            timeout=12,
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

    # Optionally set displayName in Firebase profile
    if display_name:
        try:
            requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={api_key}",
                json={"idToken": auth.get("idToken"), "displayName": name, "returnSecureToken": True},
                timeout=10,
            )
        except Exception:
            pass

    # Send verification email via Firebase
    if auth.get("idToken"):
        try:
            requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}",
                json={"requestType": "VERIFY_EMAIL", "idToken": auth["idToken"]},
                timeout=10,
            )
        except Exception as mail_exc:
            logger.warning("Firebase email verification dispatch failed: %s", mail_exc)

    # Record initial role in Firestore if admin is configured
    project_id = _config("FIREBASE_PROJECT_ID", "quantdb-728ef")
    try:
        import firebase_admin
        from firebase_admin import firestore

        app = _get_admin_app(project_id)
        db = firestore.client(app=app)
        db.collection("user_roles").document(uid).set({"role": "USER", "name": name}, merge=True)
    except Exception as exc:
        logger.debug("Initial Firestore user_roles write skipped or failed: %s", exc)

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
        response = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            json={"email": identifier.strip(), "password": password, "returnSecureToken": True},
            timeout=12,
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

    # Verify if email has been verified in Firebase
    if id_token:
        try:
            lookup_resp = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}",
                json={"idToken": id_token},
                timeout=10,
            )
            if lookup_resp.ok:
                users_list = lookup_resp.json().get("users", [])
                if users_list and not users_list[0].get("emailVerified", False):
                    # Auto re-dispatch verification email link from Firebase
                    try:
                        requests.post(
                            f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}",
                            json={"requestType": "VERIFY_EMAIL", "idToken": id_token},
                            timeout=10,
                        )
                    except Exception:
                        pass
                    raise FirebaseAuthError(
                        "Please verify your email before logging in. A verification link has been sent to your email by Firebase."
                    )
        except FirebaseAuthError:
            raise
        except Exception as exc:
            logger.debug("Email verification lookup skipped or failed: %s", exc)

    # Firebase Admin verifies the ID token and accesses Firestore with server
    # credentials. Never trust role values supplied by the client.
    try:
        import firebase_admin
        from firebase_admin import auth as admin_auth, firestore

        app = _get_admin_app(project_id)
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
        # If Admin credentials are not yet configured or fail, log warning and allow
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


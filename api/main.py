"""FastAPI adapter for the existing QuantDB provider and quant services."""
from datetime import datetime, timedelta
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

import requests

from dashboard.providers.factory import get_provider
from dashboard.mock.backtests import get_latest_backtest_summary

# Load the repository-root .env even if uvicorn is started from another directory.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
logger = logging.getLogger(__name__)

app = FastAPI(title="QuantDB API", version="1.0.0", description="HTTP interface for QuantDB research and paper trading.")
_origins = [item.strip() for item in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if item.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def _firebase_admin_app():
    """Initialize Firebase Admin from server-only credentials if available."""
    import firebase_admin
    from firebase_admin import credentials

    try:
        return firebase_admin.get_app()
    except ValueError:
        pass
    inline = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.getenv("FIREBASE_PROJECT_ID", "quantdb-728ef")
    try:
        if inline:
            service_account = json.loads(inline)
            credential = credentials.Certificate(service_account)
            credential_project = service_account.get("project_id")
            if credential_project and project_id and credential_project != project_id:
                raise RuntimeError("Firebase Admin service account project does not match FIREBASE_PROJECT_ID.")
        elif path:
            credential_path = Path(path)
            if not credential_path.is_absolute():
                credential_path = Path(__file__).resolve().parents[1] / credential_path
            if not credential_path.is_file():
                raise RuntimeError("Firebase Admin credential file was not found on the API server.")
            service_account = json.loads(credential_path.read_text(encoding="utf-8"))
            credential_project = service_account.get("project_id")
            if credential_project and project_id and credential_project != project_id:
                raise RuntimeError("Firebase Admin service account project does not match FIREBASE_PROJECT_ID.")
            credential = credentials.Certificate(service_account)
        else:
            return None
        options = {"projectId": project_id} if project_id else {}
        return firebase_admin.initialize_app(credential, options)
    except Exception as exc:
        logger.warning("Firebase Admin could not load credentials (%s). Will use Identity Toolkit REST fallback.", exc)
        return None


def _verified_identity(request: Request) -> dict:
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in to continue.")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(401, "Sign in to continue.")

    claims = None
    # 1. Attempt verification with Firebase Admin if credentials are present
    try:
        admin_app = _firebase_admin_app()
        if admin_app:
            from firebase_admin import auth as firebase_admin_auth
            claims = firebase_admin_auth.verify_id_token(token, app=admin_app)
    except Exception as exc:
        logger.debug("Firebase Admin verification failed/skipped: %s", exc)

    # 2. Fallback to Google Identity Toolkit REST API (verifies token directly using Web API key)
    if not claims:
        api_key = os.getenv("FIREBASE_API_KEY")
        if not api_key:
            raise HTTPException(503, "Firebase Authentication is not configured on the API server.")
        try:
            resp = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}",
                json={"idToken": token},
                timeout=10,
            )
            if resp.ok:
                data = resp.json()
                users = data.get("users") or []
                if users:
                    u = users[0]
                    claims = {
                        "uid": u.get("localId"),
                        "email": u.get("email"),
                        "name": u.get("displayName") or (u.get("email", "").split("@")[0] if u.get("email") else ""),
                        "email_verified": u.get("emailVerified", False),
                    }
            elif resp.status_code == 400:
                err_text = resp.text
                if "INVALID_ID_TOKEN" in err_text or "TOKEN_EXPIRED" in err_text or "USER_NOT_FOUND" in err_text:
                    raise HTTPException(401, "Your session is invalid or expired. Please sign in again.")
                raise HTTPException(401, "Firebase rejected this sign-in token. Please sign in again.")
            else:
                logger.warning("Identity Toolkit lookup returned status %s: %s", resp.status_code, resp.text)
                raise HTTPException(503, "Could not reach Firebase Authentication service.")
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Failed to contact Firebase Identity Toolkit")
            raise HTTPException(503, "Could not reach Firebase Authentication service.") from exc

    if not claims or not claims.get("email"):
        raise HTTPException(401, "Your session is invalid or expired. Please sign in again.")
    if not claims.get("email_verified", False):
        raise HTTPException(403, "Verify your email address before accessing QuantDB.")

    email = claims["email"].strip().lower()
    return {"uid": claims.get("uid"), "email": email, "name": claims.get("name") or email.split("@")[0]}


def _profile_for_identity(identity: dict, allow_missing: bool = False) -> dict | None:
    from src.database.repository import Repository
    repo = Repository()
    user = repo.get_user_by_email(identity["email"])
    if not user:
        if allow_missing:
            return None
        # Auto-provision user in MySQL if not yet registered
        try:
            from src.auth.password import hash_password
            email = identity["email"]
            raw_uname = identity.get("name") or email.split("@")[0]
            clean_uname = re.sub(r"[^A-Za-z0-9_]", "_", raw_uname)[:30]
            if len(clean_uname) < 3:
                clean_uname = (clean_uname + "user")[:30]
            conn = repo._get_connection()
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT invitation_id, role FROM account_invitations WHERE email = %s AND status = 'PENDING' AND expires_at > CURRENT_TIMESTAMP FOR UPDATE", (email,))
                invitation = cursor.fetchone()
                default_role = invitation["role"] if invitation else ("ADMIN" if email == "darshilprajapati2006@gmail.com" else "USER")
                cursor.execute("INSERT INTO users (username, name, email, password_hash, role, status, is_verified, created_at) VALUES (%s, %s, %s, %s, %s, 'ACTIVE', 1, CURRENT_TIMESTAMP)", (clean_uname, identity.get("name") or clean_uname, email, hash_password("OAuthVerifiedUser!"), default_role))
                new_id = cursor.lastrowid
                if invitation:
                    cursor.execute("UPDATE account_invitations SET status = 'ACCEPTED', accepted_user_id = %s, accepted_at = CURRENT_TIMESTAMP WHERE invitation_id = %s AND status = 'PENDING'", (new_id, invitation["invitation_id"]))
                conn.commit()
                user = repo.get_user(int(new_id)) if new_id else None
            finally:
                conn.close()
        except Exception as exc:
            logger.warning("Could not auto-provision user profile: %s", exc)
            user = repo.get_user_by_email(identity["email"])
            if not user:
                raise HTTPException(403, "Your QuantDB profile is not set up yet. Please complete account setup.")
    if user and str(user.get("status", "ACTIVE")).upper() != "ACTIVE":
        raise HTTPException(403, "This QuantDB account is inactive. Contact the administrator.")
    return user


_PUBLIC_PATHS = {"/api/v1/health", "/api/v1/auth/sync"}


@app.middleware("http")
async def authenticate_api(request: Request, call_next):
    path = request.url.path
    if request.method != "OPTIONS" and path.startswith("/api/v1/") and path not in _PUBLIC_PATHS:
        try:
            identity = await run_in_threadpool(_verified_identity, request)
            profile = await run_in_threadpool(_profile_for_identity, identity)
            request.state.identity = identity
            request.state.profile = profile
            role = str(profile.get("role", "USER")).upper()
            required = None
            if path.startswith("/api/v1/database/") or path.startswith("/api/v1/admin/") or path == "/api/v1/mode": required = "admin"
            elif path.startswith("/api/v1/backtests"): required = "backtest"
            elif path.startswith("/api/v1/orders") and request.method == "POST": required = "trade"
            elif path.startswith("/api/v1/orders") or path.startswith("/api/v1/trades"): required = "trade"
            elif path.startswith("/api/v1/strategies"): required = "Strategies"
            elif path.startswith("/api/v1/analytics/"): required = "Reports"
            elif path.startswith("/api/v1/reports"): required = "Reports"
            elif path.startswith("/api/v1/portfolio"): required = "Portfolio"
            elif path.startswith("/api/v1/market-data") or path.startswith("/api/v1/securities") or path.startswith("/api/v1/exchanges"): required = "Market Data"
            elif path.startswith("/api/v1/overview"): required = "Overview"
            elif path.startswith("/api/v1/health"): required = "System Health"
            elif path.startswith("/api/v1/auth/me"): required = "Overview"
            if required:
                from src.auth.roles import can_backtest, can_trade, has_page_access, normalize_role
                canonical = normalize_role(role)
                allowed = (canonical == "ADMIN") if required == "admin" else can_backtest(role) if required == "backtest" else can_trade(role) if required == "trade" else has_page_access(role, required)
                if not allowed:
                    raise HTTPException(403, "Your assigned role does not have access to this module.")
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return await call_next(request)

def records(value: Any):
    if isinstance(value, pd.DataFrame):
        return value.astype(object).where(pd.notna(value), None).to_dict(orient="records")
    if isinstance(value, list):
        return value
    return value

class OrderRequest(BaseModel):
    portfolio_id: int = 1
    security_id: int
    symbol: str
    side: str
    order_type: str = "MARKET"
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

class BacktestRequest(BaseModel):
    strategy_id: int
    security_id: int
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = Field(default=100000, gt=0)
    transaction_cost_pct: float = Field(default=0.05, ge=0, le=5)
    parameters: dict = {}


class AccountSyncRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=3, max_length=30)


class RoleChangeRequest(BaseModel):
    role: str


class RoleRequestPayload(BaseModel):
    requested_role: str
    reason: str = Field(default="", max_length=500)


class RoleReviewPayload(BaseModel):
    decision: str

@app.get("/api/v1/health")
def health():
    return get_provider().get_system_status()


def _public_profile(user: dict, email: str | None = None) -> dict:
    from src.auth.roles import get_allowed_pages, get_role_display_name, normalize_role
    role = normalize_role(user.get("role", "USER"))
    return {
        "user_id": user.get("user_id"), "name": user.get("name") or "QuantDB member",
        "username": user.get("username") or "", "email": email or user.get("email", ""),
        "role": role, "role_display": get_role_display_name(role),
        "allowed_pages": get_allowed_pages(role),
    }


@app.post("/api/v1/auth/sync")
def sync_account(payload: AccountSyncRequest, request: Request):
    """Link a verified Firebase identity to the authoritative MySQL account and role."""
    identity = _verified_identity(request)
    if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", payload.username.strip()) or not payload.name.strip():
        raise HTTPException(422, "Enter a display name and a 3–30 character username using letters, numbers, or underscores.")
    from src.database.repository import Repository
    repo = Repository()
    user = repo.get_user_by_email(identity["email"])
    if user:
        if str(user.get("status", "ACTIVE")).upper() != "ACTIVE":
            raise HTTPException(403, "This QuantDB account is inactive. Contact the administrator.")
        conn = repo._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET name = %s, username = %s, is_verified = 1 WHERE user_id = %s", (payload.name.strip(), payload.username.strip(), user["user_id"]))
            conn.commit()
            cursor.close()
        except Exception as exc:
            raise HTTPException(409, "That username may already be in use. Please choose another.") from exc
        finally:
            repo._close_conn(conn)
    else:
        from src.database.connection import get_connection
        conn = get_connection(raise_on_error=True)
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT invitation_id, role FROM account_invitations WHERE email = %s AND status = 'PENDING' AND expires_at > CURRENT_TIMESTAMP FOR UPDATE", (identity["email"],))
            invitation = cursor.fetchone()
            assigned_role = invitation["role"] if invitation else "USER"
            cursor.execute("INSERT INTO users (username, name, email, password_hash, role, status, is_verified, created_at) VALUES (%s, %s, %s, %s, %s, 'ACTIVE', 1, CURRENT_TIMESTAMP)", (payload.username.strip(), payload.name.strip(), identity["email"], "firebase-managed", assigned_role))
            user_id = cursor.lastrowid
            if invitation:
                cursor.execute("UPDATE account_invitations SET status = 'ACCEPTED', accepted_user_id = %s, accepted_at = CURRENT_TIMESTAMP WHERE invitation_id = %s AND status = 'PENDING'", (user_id, invitation["invitation_id"]))
            conn.commit()
            user = repo.get_user(int(user_id))
        except Exception as exc:
            conn.rollback()
            if "Duplicate" in str(exc) or "1062" in str(exc):
                raise HTTPException(409, "That username may already be in use. Please choose another.") from exc
            raise HTTPException(503, "Could not create your QuantDB profile. Please retry when the database is available.") from exc
        finally:
            conn.close()
    if not user:
        user = repo.get_user_by_email(identity["email"])
    if not user:
        raise HTTPException(503, "Your QuantDB profile could not be loaded.")
    user["name"] = payload.name.strip()
    user["username"] = payload.username.strip()
    return _public_profile(user, identity["email"])


@app.get("/api/v1/auth/me")
def current_profile(request: Request):
    return _public_profile(request.state.profile, request.state.identity["email"])


@app.post("/api/v1/auth/role-request")
def request_role(payload: RoleRequestPayload, request: Request):
    """Store a verified user's role-change request for admin review."""
    from src.auth.roles import Role, normalize_role
    from src.database.connection import get_connection
    requested = normalize_role(payload.requested_role)
    if requested not in Role.ALL_ROLES or requested in {Role.USER, Role.ADMIN}:
        raise HTTPException(422, "Choose a supported non-admin role.")
    user = request.state.profile
    if normalize_role(user.get("role")) == requested:
        raise HTTPException(409, "That role is already assigned to your account.")
    conn = get_connection(raise_on_error=True)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s FOR UPDATE", (user["user_id"],))
        cursor.fetchone()
        cursor.execute("SELECT request_id FROM role_change_requests WHERE user_id = %s AND status = 'PENDING' LIMIT 1", (user["user_id"],))
        existing = cursor.fetchone()
        if existing:
            raise HTTPException(409, "You already have a role request awaiting review.")
        cursor.execute("INSERT INTO role_change_requests (user_id, requested_role, reason) VALUES (%s, %s, %s)", (user["user_id"], requested, payload.reason.strip()))
        conn.commit()
        return {"status": "PENDING", "requested_role": requested}
    finally:
        conn.close()


@app.get("/api/v1/auth/role-request")
def my_role_request(request: Request):
    from src.database.connection import get_connection
    conn = get_connection(raise_on_error=True)
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT requested_role, reason, status, created_at FROM role_change_requests WHERE user_id = %s ORDER BY request_id DESC LIMIT 1", (request.state.profile["user_id"],))
        row = cursor.fetchone()
        if row and hasattr(row.get("created_at"), "isoformat"):
            row["created_at"] = row["created_at"].isoformat()
        return row
    finally:
        conn.close()


@app.get("/api/v1/admin/role-requests")
def admin_role_requests():
    from src.database.connection import get_connection
    conn = get_connection(raise_on_error=True)
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT r.request_id, r.user_id, u.name, u.username, u.email, u.role AS current_role, r.requested_role, r.reason, r.status, r.created_at FROM role_change_requests r JOIN users u ON u.user_id = r.user_id WHERE r.status = 'PENDING' ORDER BY r.created_at")
        rows = cursor.fetchall()
        for row in rows:
            if hasattr(row.get("created_at"), "isoformat"):
                row["created_at"] = row["created_at"].isoformat()
        return rows
    finally:
        conn.close()


@app.patch("/api/v1/admin/role-requests/{request_id}")
def review_role_request(request_id: int, payload: RoleReviewPayload, request: Request):
    from src.auth.roles import Role, normalize_role
    from src.database.connection import get_connection
    decision = payload.decision.strip().upper()
    if decision not in {"APPROVED", "REJECTED"}:
        raise HTTPException(422, "Decision must be APPROVED or REJECTED.")
    conn = get_connection(raise_on_error=True)
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, requested_role FROM role_change_requests WHERE request_id = %s AND status = 'PENDING' FOR UPDATE", (request_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(404, "Pending role request not found.")
        if decision == "APPROVED":
            role = normalize_role(row["requested_role"])
            if role not in Role.ALL_ROLES or role in {Role.ADMIN, Role.USER}:
                raise HTTPException(422, "This requested role cannot be approved here.")
            cursor.execute("UPDATE users SET role = %s WHERE user_id = %s AND status = 'ACTIVE'", (role, row["user_id"]))
            if cursor.rowcount != 1:
                raise HTTPException(409, "This account is no longer active and its role cannot be changed.")
        cursor.execute("UPDATE role_change_requests SET status = %s, reviewed_at = CURRENT_TIMESTAMP, reviewed_by = %s WHERE request_id = %s", (decision, request.state.profile["user_id"], request_id))
        conn.commit()
        return {"request_id": request_id, "status": decision}
    finally:
        conn.close()


class InvitationRequest(BaseModel):
    email: str = Field(min_length=5, max_length=150)
    name: str = Field(default="", max_length=100)
    role: str = "USER"


@app.get("/api/v1/admin/invitations")
def admin_invitations():
    from src.database.connection import get_connection
    conn = get_connection(raise_on_error=True)
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE account_invitations SET status = 'EXPIRED' WHERE status = 'PENDING' AND expires_at <= CURRENT_TIMESTAMP")
        conn.commit()
        cursor.execute("SELECT invitation_id, email, name, role, status, created_at, expires_at FROM account_invitations WHERE status = 'PENDING' ORDER BY created_at DESC")
        rows = cursor.fetchall()
        for row in rows:
            for field in ("created_at", "expires_at"):
                if hasattr(row.get(field), "isoformat"):
                    row[field] = row[field].isoformat()
        return rows
    finally:
        conn.close()


@app.post("/api/v1/admin/invitations", status_code=201)
def create_invitation(payload: InvitationRequest, request: Request):
    from src.auth.roles import Role, normalize_role
    from src.database.connection import get_connection
    email = payload.email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(422, "Enter a valid email address.")
    role = normalize_role(payload.role)
    if role not in Role.ALL_ROLES or role == Role.ADMIN:
        raise HTTPException(422, "Choose a supported non-admin role.")
    conn = get_connection(raise_on_error=True)
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            raise HTTPException(409, "An account already exists for this email.")
        cursor.execute("SELECT invitation_id FROM account_invitations WHERE email = %s AND status = 'PENDING' AND expires_at > CURRENT_TIMESTAMP FOR UPDATE", (email,))
        if cursor.fetchone():
            raise HTTPException(409, "A pending invitation already exists for this email.")
        cursor.execute("INSERT INTO account_invitations (email, name, role, created_by, expires_at) VALUES (%s, %s, %s, %s, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 7 DAY))", (email, payload.name.strip(), role, request.state.profile["user_id"]))
        conn.commit()
        return {"invitation_id": cursor.lastrowid, "email": email, "role": role, "status": "PENDING"}
    except HTTPException:
        raise
    except Exception as exc:
        conn.rollback()
        if "Duplicate" in str(exc) or "1062" in str(exc):
            raise HTTPException(409, "A pending invitation already exists for this email.") from exc
        raise
    finally:
        conn.close()


@app.delete("/api/v1/admin/invitations/{invitation_id}")
def cancel_invitation(invitation_id: int):
    from src.database.connection import get_connection
    conn = get_connection(raise_on_error=True)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE account_invitations SET status = 'REVOKED' WHERE invitation_id = %s AND status = 'PENDING'", (invitation_id,))
        if cursor.rowcount != 1:
            raise HTTPException(404, "Pending invitation not found.")
        conn.commit()
        return {"invitation_id": invitation_id, "status": "REVOKED"}
    finally:
        conn.close()


@app.get("/api/v1/admin/users")
def admin_users():
    from src.database.repository import Repository
    users = Repository().get_users()
    return [{key: value for key, value in user.items() if key not in {"password_hash", "password"}} for user in users]


@app.patch("/api/v1/admin/users/{user_id}/role")
def change_user_role(user_id: int, payload: RoleChangeRequest, request: Request):
    from src.auth.roles import Role, normalize_role
    from src.database.repository import Repository
    if payload.role.strip().upper() not in Role.ALL_ROLES + [Role.SIMULATED_TRADER]:
        raise HTTPException(422, "Choose a valid QuantDB role.")
    role = normalize_role(payload.role)
    if role not in Role.ALL_ROLES:
        raise HTTPException(422, "Choose a valid QuantDB role.")
    if user_id == int(request.state.profile["user_id"]) and role != Role.ADMIN:
        raise HTTPException(409, "You cannot remove your own Admin access.")
    repo = Repository()
    if not repo.get_user(user_id):
        raise HTTPException(404, "QuantDB user not found.")
    repo.update_user_role(user_id, role)
    return {"user_id": user_id, "role": role, "status": "updated"}

def _portfolio_scope(request: Request, provider=None):
    provider = provider or get_provider()
    role = str(request.state.profile.get("role", "USER")).upper()
    portfolios = provider.get_portfolios() or []
    if role == "ADMIN":
        return portfolios
    # Mock portfolios are shared demonstration fixtures, not user records. Keep them
    # visibly in simulation mode while real MySQL portfolios remain owner scoped.
    if provider.__class__.__name__ == "MockProvider":
        return [dict(p, user_id=request.state.profile.get("user_id")) for p in portfolios if int(p.get("user_id", 0)) == 1]
    user_id = request.state.profile.get("user_id")
    return [p for p in portfolios if user_id is not None and str(p.get("user_id")) == str(user_id)]


@app.get("/api/v1/overview")
def overview(request: Request):
    p = get_provider()
    # Keep the first dashboard request small; heavy risk/backtest work runs in their own modules.
    return {"market": records(p.get_market_overview()), "portfolios": _portfolio_scope(request, p), "health": p.get_system_status(), "risk": {}, "backtest": {}}

@app.get("/api/v1/securities")
def securities(): return get_provider().get_securities()

@app.get("/api/v1/exchanges")
def exchanges(): return get_provider().get_exchanges()

@app.get("/api/v1/market-data/{security_id}")
def market_data(security_id: int, symbol: str = "RELIANCE", days: int = 180):
    end = datetime.now(); start = end - timedelta(days=max(1, min(days, 3650)))
    try: return records(get_provider().get_market_data(security_id, symbol, start, end, "1D"))
    except Exception as exc: raise HTTPException(503, str(exc)) from exc

@app.get("/api/v1/portfolios")
def portfolios(request: Request): return _portfolio_scope(request)

@app.get("/api/v1/portfolios/{portfolio_id}")
def portfolio(portfolio_id: int, request: Request):
    allowed = {int(item["portfolio_id"]) for item in _portfolio_scope(request)}
    if str(request.state.profile.get("role", "USER")).upper() != "ADMIN" and portfolio_id not in allowed:
        raise HTTPException(403, "This portfolio is not assigned to your QuantDB account.")
    p = get_provider(); result = p.get_portfolio(portfolio_id)
    if result is None: raise HTTPException(404, "Portfolio not found")
    return {"summary": result, "positions": records(p.get_positions(portfolio_id)), "equity": records(p.get_portfolio_equity_curve(portfolio_id))}

@app.get("/api/v1/orders")
def orders(request: Request):
    p = get_provider(); scope = _portfolio_scope(request, p)
    if str(request.state.profile.get("role", "USER")).upper() != "ADMIN" and not scope: return []
    allowed = {int(item["portfolio_id"]) for item in scope}
    user_id = None if str(request.state.profile.get("role", "USER")).upper() == "ADMIN" else int(request.state.profile["user_id"])
    portfolio_id = None if user_id is None else next(iter(allowed), None)
    try: values = p.get_orders(portfolio_id=portfolio_id, user_id=user_id)
    except TypeError: values = p.get_orders(portfolio_id=portfolio_id)
    return [row for row in records(values) if row.get("portfolio_id") is not None and int(row["portfolio_id"]) in allowed]

@app.post("/api/v1/orders")
def submit_order(payload: OrderRequest, request: Request):
    try:
        if str(request.state.profile.get("role", "USER")).upper() != "ADMIN" and payload.portfolio_id not in {int(p["portfolio_id"]) for p in _portfolio_scope(request)}:
            raise HTTPException(403, "Choose a portfolio assigned to your account.")
        return get_provider().submit_order(**payload.dict(), user_id=int(request.state.profile["user_id"]))
    except HTTPException: raise
    except Exception as exc: raise HTTPException(400, str(exc)) from exc

@app.get("/api/v1/trades")
def trades(request: Request):
    p = get_provider(); scope = _portfolio_scope(request, p)
    if str(request.state.profile.get("role", "USER")).upper() != "ADMIN" and not scope: return []
    allowed = {int(item["portfolio_id"]) for item in scope}
    user_id = None if str(request.state.profile.get("role", "USER")).upper() == "ADMIN" else int(request.state.profile["user_id"])
    portfolio_id = None if user_id is None else next(iter(allowed), None)
    try: values = p.get_trades(portfolio_id=portfolio_id, user_id=user_id)
    except TypeError: values = p.get_trades(portfolio_id=portfolio_id)
    return [row for row in records(values) if row.get("portfolio_id") is not None and int(row["portfolio_id"]) in allowed]

@app.get("/api/v1/strategies")
def strategies(): return get_provider().get_strategies()

@app.post("/api/v1/backtests")
def run_backtest(payload: BacktestRequest):
    try:
        from dashboard.services.backtest_service import execute_backtest
        ok, message, result = execute_backtest(**payload.dict())
        if not ok: raise HTTPException(400, message)
        return result
    except HTTPException: raise
    except Exception as exc: raise HTTPException(400, str(exc)) from exc

@app.get("/api/v1/analytics/risk")
def risk(request: Request, portfolio_id: int | None = None):
    scope = _portfolio_scope(request)
    allowed = {int(item["portfolio_id"]) for item in scope}
    if portfolio_id is None:
        portfolio_id = next(iter(allowed), 1) if allowed else 1
    if str(request.state.profile.get("role", "USER")).upper() != "ADMIN" and portfolio_id not in allowed:
        raise HTTPException(403, "This portfolio is not assigned to your QuantDB account.")
    return get_provider().get_risk_metrics(portfolio_id)

@app.get("/api/v1/reports")
def reports(request: Request):
    allowed = {int(item["portfolio_id"]) for item in _portfolio_scope(request)}
    portfolio_id = next(iter(allowed), 1)
    if str(request.state.profile.get("role", "USER")).upper() != "ADMIN" and not allowed:
        raise HTTPException(404, "No portfolio is assigned to your account yet.")
    provider = get_provider()
    backtest = get_latest_backtest_summary() if provider.__class__.__name__ == "MockProvider" else {}
    return {"risk": provider.get_risk_metrics(portfolio_id), "backtest": backtest}

class ModeRequest(BaseModel):
    mode: str

@app.post("/api/v1/mode")
def set_mode(payload: ModeRequest):
    from dashboard.providers.factory import set_data_mode
    try:
        set_data_mode(payload.mode)
        return {"mode": payload.mode.lower(), "status": "updated"}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc

@app.get("/api/v1/database/tables")
def database_tables():
    from src.database.connection import get_connection
    conn = get_connection(use_pool=False)
    if not conn or not conn.is_connected():
        raise HTTPException(503, "Database connection offline")
    try:
        cur = conn.cursor()
        cur.execute("SHOW FULL TABLES")
        raw = cur.fetchall()
        result = []
        for name, t_type in raw:
            try:
                cur.execute(f"SELECT COUNT(*) FROM `{name}`")
                cnt = cur.fetchone()[0]
            except Exception:
                cnt = 0
            result.append({
                "name": name,
                "type": "VIEW" if "VIEW" in t_type.upper() else "BASE TABLE",
                "row_count": cnt
            })
        return result
    finally:
        conn.close()

@app.get("/api/v1/database/tables/{table_name}")
def table_records(table_name: str, limit: int = 50):
    import re
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        raise HTTPException(400, "Invalid table name")
    from src.database.connection import get_connection
    conn = get_connection(use_pool=False)
    if not conn or not conn.is_connected():
        raise HTTPException(503, "Database connection offline")
    try:
        check = conn.cursor()
        check.execute("SHOW FULL TABLES")
        known_tables = {row[0] for row in check.fetchall()}
        check.close()
        if table_name not in known_tables:
            raise HTTPException(404, "Database table or view not found")
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT * FROM `{table_name}` LIMIT %s", (max(1, min(limit, 100)),))
        rows = cur.fetchall()
        clean_rows = []
        for r in rows:
            clean_r = {}
            for k, v in r.items():
                if hasattr(v, "isoformat"):
                    clean_r[k] = v.isoformat()
                elif hasattr(v, "__float__"):
                    clean_r[k] = float(v)
                else:
                    clean_r[k] = v
            clean_rows.append(clean_r)
        return {"table": table_name, "count": len(clean_rows), "records": clean_rows}
    finally:
        conn.close()

@app.get("/api/v1/database/schema")
def schema():
    return {"mode": "MOCK" if get_provider().__class__.__name__ == "MockProvider" else "REAL", "tables": ["users", "exchanges", "securities", "market_data", "orders", "trades", "portfolios", "positions", "strategies", "backtests", "backtest_results", "risk_metrics"]}


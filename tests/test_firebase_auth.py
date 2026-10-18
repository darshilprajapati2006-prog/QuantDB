from unittest.mock import MagicMock, patch
import pytest

from src.auth import firebase_auth
from src.auth.email_service import send_login_alert_email
from src.auth.roles import Role


def test_is_configured(monkeypatch):
    monkeypatch.setenv("FIREBASE_API_KEY", "test_api_key")
    assert firebase_auth.is_configured() is True

    monkeypatch.delenv("FIREBASE_API_KEY", raising=False)
    assert firebase_auth.is_configured() is False


def test_authenticate_requires_email(monkeypatch):
    monkeypatch.setenv("FIREBASE_API_KEY", "test_key")
    with pytest.raises(firebase_auth.FirebaseAuthError, match="requires the account email address"):
        firebase_auth.authenticate("notanemail", "password123")


@patch("src.auth.firebase_auth.requests.post")
def test_authenticate_invalid_credentials(mock_post, monkeypatch):
    monkeypatch.setenv("FIREBASE_API_KEY", "test_key")
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.json.return_value = {"error": {"message": "INVALID_PASSWORD"}}
    mock_post.return_value = mock_resp

    with pytest.raises(firebase_auth.FirebaseAuthError, match="Invalid email or password"):
        firebase_auth.authenticate("trader@quantdb.internal", "wrongpassword")


@patch("src.auth.firebase_auth.requests.post")
def test_authenticate_disabled_user(mock_post, monkeypatch):
    monkeypatch.setenv("FIREBASE_API_KEY", "test_key")
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.json.return_value = {"error": {"message": "USER_DISABLED"}}
    mock_post.return_value = mock_resp

    with pytest.raises(firebase_auth.FirebaseAuthError, match="account is disabled"):
        firebase_auth.authenticate("trader@quantdb.internal", "secret123")


@patch("src.auth.firebase_auth.requests.post")
def test_authenticate_no_verification_required(mock_post, monkeypatch):
    """Sign-in should succeed even when emailVerified is False — no verification wall."""
    monkeypatch.setenv("FIREBASE_API_KEY", "test_key")
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT_PATH", raising=False)

    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "localId": "uid_noverify",
        "email": "user@example.com",
        "idToken": "fake_token",
    }
    mock_post.return_value = mock_resp

    # Must NOT raise — no email verification check
    result = firebase_auth.authenticate("user@example.com", "password123")
    assert result["email"] == "user@example.com"


@patch("src.auth.firebase_auth.requests.post")
def test_authenticate_success_default_user_role(mock_post, monkeypatch):
    monkeypatch.setenv("FIREBASE_API_KEY", "test_key")
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT_PATH", raising=False)

    def side_effect(url, *args, **kwargs):
        resp = MagicMock()
        resp.ok = True
        if "signInWithPassword" in url:
            resp.json.return_value = {
                "localId": "uid_12345",
                "email": "trader@quantdb.internal",
                "idToken": "fake_token",
            }
        elif "lookup" in url:
            resp.json.return_value = {
                "users": [{"emailVerified": True}]
            }
        return resp

    mock_post.side_effect = side_effect

    result = firebase_auth.authenticate("trader@quantdb.internal", "secret123")
    assert result["user_id"] == "uid_12345"
    assert result["email"] == "trader@quantdb.internal"
    assert result["role"] == Role.USER
    assert result["role_display"] == "User"


def test_send_login_alert_email_mock(monkeypatch):
    monkeypatch.setenv("DATA_MODE", "mock")
    sent = send_login_alert_email("trader@quantdb.internal", "Trader Alan")
    assert sent is True


def test_validate_email_domain_rejects_fake():
    from src.auth.email_service import validate_email_domain
    valid, err = validate_email_domain("user@fake123notrealdomainxyz99.com")
    assert valid is False
    assert "does not exist" in err


def test_sign_up_allows_any_valid_email_format(monkeypatch):
    """sign_up should NOT reject based on MX/domain — removed in favour of password-only flow."""
    monkeypatch.setenv("FIREBASE_API_KEY", "test_key")
    # Firebase will reject the dummy key — verify it raises a Firebase error (not a domain error)
    with pytest.raises(firebase_auth.FirebaseAuthError) as exc_info:
        firebase_auth.sign_up("user@example.com", "Password123")
    assert "does not exist" not in str(exc_info.value)


def test_resend_verification_email(monkeypatch):
    monkeypatch.setenv("FIREBASE_API_KEY", "test_key")
    monkeypatch.setenv("DATA_MODE", "mock")
    ok, msg = firebase_auth.resend_verification_email("trader@quantdb.internal")
    assert ok is True
    assert "dispatched" in msg


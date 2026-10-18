from unittest.mock import MagicMock, patch
import pytest

from src.auth import firebase_auth
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
def test_authenticate_success_default_user_role(mock_post, monkeypatch):
    monkeypatch.setenv("FIREBASE_API_KEY", "test_key")
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT_PATH", raising=False)

    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "localId": "uid_12345",
        "email": "trader@quantdb.internal",
        "idToken": "fake_token",
    }
    mock_post.return_value = mock_resp

    result = firebase_auth.authenticate("trader@quantdb.internal", "secret123")
    assert result["user_id"] == "uid_12345"
    assert result["email"] == "trader@quantdb.internal"
    assert result["role"] == Role.USER
    assert result["role_display"] == "User"

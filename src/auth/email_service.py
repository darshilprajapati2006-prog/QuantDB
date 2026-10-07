"""
QuantDB Email Service Module.

Handles SMTP email dispatching for OTP verification.
Supports standard SMTP, STARTTLS (e.g., Gmail with App Passwords), and SSL.
Reads configuration from environment variables or Streamlit secrets.
Provides mock email dispatching for tests and offline/MOCK mode.
NEVER logs plaintext OTP values in application logs.
"""

import email.message
import logging
import os
import smtplib
from typing import Callable, Optional

from src.database.connection import _get_db_param

logger = logging.getLogger(__name__)

# Test hook: optional custom sender function for unit/integration tests
_test_email_sender: Optional[Callable[[str, str, str], bool]] = None


def set_test_email_sender(sender: Optional[Callable[[str, str, str], bool]]) -> None:
    """Sets a custom test email sender to intercept emails during automated tests."""
    global _test_email_sender
    _test_email_sender = sender


def get_smtp_config() -> dict:
    """Retrieves SMTP configuration from environment or Streamlit secrets."""
    host = _get_db_param("SMTP_HOST", "")
    port_str = _get_db_param("SMTP_PORT", "587")
    try:
        port = int(port_str)
    except ValueError:
        port = 587

    username = _get_db_param("SMTP_USERNAME", "")
    password = _get_db_param("SMTP_PASSWORD", "")
    from_email = _get_db_param("SMTP_FROM_EMAIL", username or "noreply@quantdb.local")
    use_tls_str = _get_db_param("SMTP_USE_TLS", "true").lower()
    use_tls = use_tls_str in ("true", "1", "yes")

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "from_email": from_email,
        "use_tls": use_tls,
    }


def send_otp_email(
    to_email: str = "",
    otp: str = "",
    user_name: str = "",
    recipient_email: str = "",
    recipient_name: str = "",
    expiry_minutes: int = 5,
) -> bool:
    """
    Sends a 6-digit verification OTP to the user's email via SMTP.

    Format complies with specifications:
        QuantDB
        Email Verification

        Your verification OTP is:
        123456

        This OTP expires in 5 minutes.
        If this was not you, ignore this email.

    Never logs the OTP value itself.
    """
    target_email = (to_email or recipient_email).strip()
    target_name = (user_name or recipient_name).strip()

    if not target_email or "@" not in target_email:
        raise ValueError("Invalid recipient email address.")

    greeting = f"Hello {target_name},\n\n" if target_name else ""
    body_text = (
        f"{greeting}QuantDB\n"
        f"Email Verification\n\n"
        f"Your verification OTP is:\n"
        f"{otp}\n\n"
        f"This OTP expires in {expiry_minutes} minutes.\n"
        f"If this was not you, ignore this email.\n"
    )
    subject = "QuantDB — Email Verification Code"

    # 1. Check if test interceptor is registered (e.g., during pytest)
    if _test_email_sender is not None:
        try:
            return _test_email_sender(target_email, subject, body_text)
        except TypeError:
            return _test_email_sender(target_email, otp, target_name)

    # 2. Check if running in mock/test mode or if SMTP is unconfigured
    is_mock = os.getenv("DATA_MODE", "").lower() == "mock" or os.getenv("MOCK_SMTP", "0") == "1"
    config = get_smtp_config()

    if not config["host"] or is_mock:
        # In mock mode or when SMTP is not configured, simulate email sending safely
        logger.info(f"Simulated SMTP dispatch: verification email queued for recipient {target_email}")
        return True

    # 3. Construct email message
    msg = email.message.EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config["from_email"]
    msg["To"] = target_email
    msg.set_content(body_text)

    # 4. Connect and send via SMTP
    host = config["host"]
    port = config["port"]
    username = config["username"]
    password = config["password"]
    use_tls = config["use_tls"]

    try:
        if port == 465:
            # SSL connection
            with smtplib.SMTP_SSL(host, port, timeout=10) as server:
                if username and password:
                    server.login(username, password)
                server.send_message(msg)
        else:
            # Standard connection with optional STARTTLS
            with smtplib.SMTP(host, port, timeout=10) as server:
                if use_tls:
                    server.starttls()
                if username and password:
                    server.login(username, password)
                server.send_message(msg)

        logger.info(f"Verification email successfully dispatched to {to_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        safe_msg = f"SMTP Authentication failed for user {username}. Please check SMTP credentials or App Password."
        logger.error(safe_msg)
        raise RuntimeError("Email delivery service authentication error. Please contact platform administrator.")

    except Exception as e:
        # Mask credentials from error logs
        err_str = str(e).replace(password, "******") if password else str(e)
        logger.error(f"Failed to send verification email to {to_email}: {err_str}")
        raise RuntimeError("Unable to deliver verification email. Please check server network configuration or try again.")

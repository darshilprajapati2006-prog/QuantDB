"""
QuantDB Email Service Module.

Handles SMTP email dispatching for OTP verification and account notifications.
Supports SMTP with STARTTLS (commonly port 587) and implicit SSL (port 465).
Configuration is read through the project's _get_db_param helper.
Supports test interception and mock/offline mode.

Security:
- Never logs plaintext OTP values or SMTP passwords.
- Does not claim that mock-mode emails were actually delivered.
"""

from __future__ import annotations

import email.message
import logging
import os
import re
import smtplib
import socket
from datetime import datetime, timezone
from email.utils import parseaddr
from typing import Callable, Optional, Tuple

from src.database.connection import _get_db_param

logger = logging.getLogger(__name__)

# Test hook: (recipient, subject, body) -> success
_test_email_sender: Optional[Callable[[str, str, str], bool]] = None


def set_test_email_sender(
    sender: Optional[Callable[[str, str, str], bool]],
) -> None:
    """Set or clear the custom sender used by tests."""
    global _test_email_sender
    _test_email_sender = sender


def _get_config_value(name: str, default: str = "") -> str:
    """Read a configuration value safely as a string."""
    value = _get_db_param(name, default)
    return default if value is None else str(value).strip()


def get_smtp_config() -> dict:
    """Return SMTP settings from environment/Streamlit configuration."""
    host = _get_config_value("SMTP_HOST")
    port_text = _get_config_value("SMTP_PORT", "587")
    username = _get_config_value("SMTP_USERNAME")
    password = _get_config_value("SMTP_PASSWORD")
    from_email = _get_config_value("SMTP_FROM_EMAIL", username or "noreply@quantdb.local")
    use_tls_text = _get_config_value("SMTP_USE_TLS", "true").lower()

    try:
        port = int(port_text)
    except (TypeError, ValueError):
        logger.warning("Invalid SMTP_PORT; defaulting to 587.")
        port = 587

    if not 1 <= port <= 65535:
        logger.warning("SMTP_PORT is outside the valid range; defaulting to 587.")
        port = 587

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "from_email": from_email,
        "use_tls": use_tls_text in {"true", "1", "yes", "on"},
    }


def _is_mock_mode() -> bool:
    """Return whether outbound email should be simulated."""
    return (
        os.getenv("DATA_MODE", "").strip().lower() == "mock"
        or os.getenv("MOCK_SMTP", "0").strip().lower() in {"1", "true", "yes", "on"}
    )


def _valid_email_address(address: str) -> bool:
    """Perform a basic syntax check without claiming the mailbox exists."""
    if not isinstance(address, str) or not address.strip():
        return False
    clean = address.strip()
    parsed_name, parsed_address = parseaddr(clean)
    if parsed_address != clean or parsed_name:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+", clean))


def _dispatch_email(to_email: str, subject: str, body_text: str) -> bool:
    """Send an email, or safely intercept/simulate it for tests and mock mode."""
    if _test_email_sender is not None:
        try:
            return bool(_test_email_sender(to_email, subject, body_text))
        except Exception:
            logger.exception("Test email sender failed.")
            return False

    config = get_smtp_config()
    if _is_mock_mode() or not config["host"]:
        logger.info("Simulated email dispatch for recipient %s (mock/unconfigured SMTP).", to_email)
        return True

    msg = email.message.EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config["from_email"]
    msg["To"] = to_email
    msg.set_content(body_text)

    host = config["host"]
    port = config["port"]
    username = config["username"]
    password = config["password"]
    use_tls = config["use_tls"]

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=10) as server:
                if username:
                    if not password:
                        raise RuntimeError("SMTP_PASSWORD is required when SMTP_USERNAME is configured.")
                    server.login(username, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.ehlo()
                if use_tls:
                    server.starttls()
                    server.ehlo()
                if username:
                    if not password:
                        raise RuntimeError("SMTP_PASSWORD is required when SMTP_USERNAME is configured.")
                    server.login(username, password)
                server.send_message(msg)

        logger.info("Email successfully dispatched to %s.", to_email)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed for configured user %s.", username or "(not set)")
        raise RuntimeError(
            "Email delivery authentication failed. Check the SMTP username and app password."
        ) from None
    except RuntimeError:
        raise
    except (smtplib.SMTPException, OSError, TimeoutError) as exc:
        # Log the exception type only; do not risk leaking credentials or message content.
        logger.error("Email delivery failed for %s (%s).", to_email, type(exc).__name__)
        raise RuntimeError(
            "Unable to deliver email. Check SMTP settings and network connectivity."
        ) from None


def send_otp_email(
    to_email: str = "",
    otp: str = "",
    user_name: str = "",
    recipient_email: str = "",
    recipient_name: str = "",
    expiry_minutes: int = 5,
) -> bool:
    """Send an email verification OTP without logging the OTP itself."""
    target_email = (to_email or recipient_email or "").strip()
    target_name = (user_name or recipient_name or "").strip()

    if not _valid_email_address(target_email):
        raise ValueError("Invalid recipient email address.")
    if not isinstance(otp, str) or not re.fullmatch(r"\d{6}", otp):
        raise ValueError("OTP must be a six-digit string.")
    if not isinstance(expiry_minutes, int) or expiry_minutes <= 0:
        raise ValueError("expiry_minutes must be a positive integer.")

    greeting = f"Hello {target_name},\n\n" if target_name else ""
    body_text = (
        f"{greeting}QuantDB\n"
        "Email Verification\n\n"
        "Your verification OTP is:\n"
        f"{otp}\n\n"
        f"This OTP expires in {expiry_minutes} minutes.\n"
        "If this was not you, ignore this email.\n"
    )
    return _dispatch_email(target_email, "QuantDB — Email Verification Code", body_text)


def send_login_alert_email(
    to_email: str,
    user_name: str = "",
    login_time: Optional[str] = None,
) -> bool:
    """Send a security notification when a user signs in."""
    target_email = (to_email or "").strip()
    target_name = (user_name or "").strip()

    if not _valid_email_address(target_email):
        return False

    # Use UTC explicitly when a timestamp is generated here.
    now_str = login_time or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    greeting = f"Hello {target_name},\n\n" if target_name else "Hello,\n\n"
    body_text = (
        f"{greeting}QuantDB Security Notification\n\n"
        "Your QuantDB terminal account was successfully signed into at:\n"
        f"{now_str}\n\n"
        "Details:\n"
        f"• Account: {target_email}\n"
        "• Platform: QuantDB Terminal\n\n"
        "If this was you, you can safely ignore this notification.\n"
        "If you did NOT perform this login, please change your password immediately.\n\n"
        "Regards,\n"
        "QuantDB Security Team\n"
    )

    try:
        return _dispatch_email(
            target_email,
            "QuantDB — Security Alert: New Login Detected",
            body_text,
        )
    except Exception:
        logger.warning("Unable to dispatch login alert to %s.", target_email)
        return False


def validate_email_domain(email_str: str) -> Tuple[bool, str]:
    """
    Validate email syntax and check whether its domain appears reachable.

    DNS checks cannot prove that a mailbox exists. DNS/network failures are
    treated as inconclusive rather than automatically rejecting the address.
    """
    if not isinstance(email_str, str) or not email_str.strip():
        return False, "An email address is required."

    clean = email_str.strip().lower()
    if not _valid_email_address(clean):
        return False, "Please enter a valid email address (e.g. name@example.com)."

    domain = clean.rsplit("@", 1)[1]

    try:
        import dns.resolver  # type: ignore[import-not-found]

        resolver = dns.resolver.Resolver()
        resolver.lifetime = 2.0
        try:
            answers = resolver.resolve(domain, "MX")
            if answers:
                return True, ""
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            # Some domains may accept mail without an explicit MX record.
            try:
                resolver.resolve(domain, "A")
                return True, ""
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                return False, (
                    f"The email domain '@{domain}' does not appear to accept mail. "
                    "Please check the address or use another email."
                )
        except (dns.resolver.NoNameservers, dns.resolver.Timeout):
            logger.debug("DNS check inconclusive for domain %s.", domain)
            return True, ""
    except ModuleNotFoundError:
        # dnspython is optional. A successful hostname lookup is a weaker check.
        try:
            socket.getaddrinfo(domain, None)
            return True, ""
        except (socket.gaierror, socket.herror):
            return False, (
                f"The email domain '@{domain}' does not exist or could not be found. "
                "Please check the address or use another email."
            )
    except Exception as exc:
        logger.debug("DNS check inconclusive for domain %s (%s).", domain, type(exc).__name__)

    # Avoid blocking sign-up when DNS is temporarily unavailable.
    return True, ""


def send_registration_welcome_email(
    to_email: str,
    user_name: str = "",
) -> bool:
    """Send a registration confirmation and email-verification instructions."""
    target_email = (to_email or "").strip()
    target_name = (user_name or "").strip()

    if not _valid_email_address(target_email):
        return False

    greeting = f"Hello {target_name},\n\n" if target_name else "Hello,\n\n"
    body_text = (
        f"{greeting}"
        "Welcome to QuantDB — Quantitative Finance Research & Simulation Platform!\n\n"
        "Your account registration has been initiated for:\n"
        f"Account: {target_email}\n\n"
        "ACTION REQUIRED: Complete Email Verification\n"
        "--------------------------------------------------\n"
        "1. Check your inbox for the Firebase Authentication verification email.\n"
        "2. If it does not arrive, check your Spam or Junk folder.\n"
        "3. Click the verification link to activate your QuantDB account.\n"
        "4. Once verified, visit https://quantdb.streamlit.app to sign in.\n\n"
        "If you did not create a QuantDB account, please ignore this email.\n\n"
        "Best regards,\n"
        "QuantDB Engineering Team\n"
    )

    try:
        return _dispatch_email(
            target_email,
            "QuantDB — Complete Your Email Verification",
            body_text,
        )
    except Exception:
        logger.warning("Unable to dispatch registration welcome email to %s.", target_email)
        return False

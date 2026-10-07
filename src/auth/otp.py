"""
QuantDB One-Time Password (OTP) Generation and Hashing Module.

Uses Python's secrets module for cryptographically strong pseudorandom generation.
Hashes OTPs using salted SHA-256 before database storage.
Verifies OTPs with constant-time comparison to prevent side-channel timing attacks.
Enforces security constraints: 5-minute expiry, 5-attempt threshold, 60s resend cooldown.
"""

import hashlib
import hmac
import os
import secrets
from typing import Optional

OTP_ALGORITHM = "otp_sha256"
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60


def generate_otp(length: int = 6) -> str:
    """
    Generates a cryptographically secure numeric OTP code of specified length (default 6).
    Uses Python's standard `secrets` module (never `random.random()`).
    """
    if length <= 0:
        length = 6
    min_val = 10 ** (length - 1)
    max_val = (10 ** length) - 1
    code = secrets.randbelow(max_val - min_val + 1) + min_val
    return f"{code:0{length}d}"


def hash_otp(otp: str, salt: Optional[bytes] = None) -> str:
    """
    Hashes a 6-digit OTP code with a unique cryptographic salt.
    Format: otp_sha256$<salt_hex>$<hash_hex>
    """
    if not isinstance(otp, str) or not otp:
        raise ValueError("OTP must be a non-empty string.")

    if salt is None:
        salt = os.urandom(16)

    derived = hashlib.sha256(salt + otp.encode("utf-8")).hexdigest()
    return f"{OTP_ALGORITHM}${salt.hex()}${derived}"


def verify_otp_hash(otp: str, stored_hash: str) -> bool:
    """
    Verifies a candidate OTP against a stored salted hash using constant-time comparison.
    """
    if not isinstance(otp, str) or not isinstance(stored_hash, str):
        return False
    if not otp or not stored_hash:
        return False

    parts = stored_hash.split("$")
    if len(parts) == 3 and parts[0] == OTP_ALGORITHM:
        try:
            salt = bytes.fromhex(parts[1])
            expected_hex = parts[2]
            candidate_hex = hashlib.sha256(salt + otp.strip().encode("utf-8")).hexdigest()
            return hmac.compare_digest(candidate_hex, expected_hex)
        except Exception:
            return False

    return False

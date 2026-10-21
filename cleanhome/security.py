"""Password hashing, verification, and password-policy helpers.

Uses PBKDF2-HMAC-SHA256 with a per-user random salt. Passwords are never
logged, printed, or stored in plain text.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import string

from cleanhome import config


def generate_salt() -> str:
    """Return a fresh random salt, hex-encoded."""
    return secrets.token_bytes(config.SALT_BYTES).hex()


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash ``password`` and return ``(salt_hex, hash_hex)``."""
    if salt is None:
        salt = generate_salt()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), config.PBKDF2_ITERATIONS
    )
    return salt, digest.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Constant-time check of ``password`` against a stored salt and hash."""
    if not salt or not expected_hash:
        return False
    try:
        _, candidate = hash_password(password, salt)
    except ValueError:
        return False
    return hmac.compare_digest(candidate, expected_hash)


def generate_password(length: int = 14) -> str:
    """Generate a readable random password for first-run accounts."""
    alphabet = string.ascii_letters + string.digits
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in password) and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)):
            return password


def password_problems(password: str) -> list[str]:
    """Return a list of human-readable password policy violations."""
    problems: list[str] = []
    if len(password) < config.MIN_PASSWORD_LENGTH:
        problems.append(f"Password must be at least {config.MIN_PASSWORD_LENGTH} characters long.")
    if not any(c.isalpha() for c in password):
        problems.append("Password must contain at least one letter.")
    if not any(c.isdigit() for c in password):
        problems.append("Password must contain at least one number.")
    return problems

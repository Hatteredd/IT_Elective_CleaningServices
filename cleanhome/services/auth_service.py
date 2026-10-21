"""Authentication, account management, and profile rules."""

from __future__ import annotations

import math
import re
from datetime import datetime, timedelta
from typing import Any

from cleanhome import config, db, security
from cleanhome.services import AuthError, ConflictError, PermissionDenied, ValidationError

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")
PHONE_PATTERN = re.compile(r"^(09\d{9}|\+639\d{9})$")

GENERIC_LOGIN_ERROR = "Incorrect email or password."


# ── Read helpers ─────────────────────────────────────────────────────────────
def _public_user(row) -> dict[str, Any]:
    """Strip the password material from a user row."""
    data = dict(row)
    data.pop("pw_salt", None)
    data.pop("pw_hash", None)
    data["is_active"] = bool(data.get("is_active"))
    data["must_change_password"] = bool(data.get("must_change_password"))
    return data


def get_user(user_id: int) -> dict[str, Any] | None:
    """Return one user without password material."""
    row = db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return _public_user(row) if row else None


def find_user_by_email(email: str) -> dict[str, Any] | None:
    """Return one user by email, without password material."""
    row = db.query_one("SELECT * FROM users WHERE email = ?", ((email or "").strip().lower(),))
    return _public_user(row) if row else None


def admin_exists() -> bool:
    """True when at least one administrator account is present."""
    row = db.query_one("SELECT COUNT(*) AS n FROM users WHERE role = 'admin'")
    return bool(row and row["n"])


# ── First run ────────────────────────────────────────────────────────────────
def create_first_admin(full_name: str, email: str, phone: str, password: str,
                       confirm_password: str) -> dict[str, Any]:
    """Create the very first administrator account.

    This is the only path that creates an admin without a signed-in actor,
    and it refuses to run once any administrator exists.
    """
    if admin_exists():
        raise ConflictError("An administrator account already exists.")

    clean_name = (full_name or "").strip()
    if not clean_name:
        raise ValidationError("Full name is required.", "full_name")
    if len(clean_name) > 120:
        raise ValidationError("Full name must be 120 characters or fewer.", "full_name")

    clean_email = (email or "").strip().lower()
    if not clean_email:
        raise ValidationError("Email is required.", "email")
    if not EMAIL_PATTERN.match(clean_email):
        raise ValidationError("Enter a valid email address.", "email")
    if db.query_one("SELECT id FROM users WHERE email = ?", (clean_email,)):
        raise ValidationError("An account with this email already exists.", "email")

    clean_phone = (phone or "").strip()
    if clean_phone and not PHONE_PATTERN.match(clean_phone):
        raise ValidationError("Enter a valid PH mobile number (09XXXXXXXXX).", "phone")

    if not password:
        raise ValidationError("Password is required.", "password")
    problems = security.password_problems(password)
    if problems:
        raise ValidationError(problems[0], "password")
    if password != confirm_password:
        raise ValidationError("Passwords do not match.", "confirm_password")

    salt, digest = security.hash_password(password)
    cursor = db.execute(
        "INSERT INTO users (full_name, email, phone, role, pw_salt, pw_hash, is_active, "
        "must_change_password) VALUES (?, ?, ?, 'admin', ?, ?, 1, 0)",
        (clean_name, clean_email, clean_phone, salt, digest),
    )
    return get_user(int(cursor.lastrowid)) or {}


# ── Registration ─────────────────────────────────────────────────────────────
def register(full_name: str, email: str, phone: str, password: str,
             confirm_password: str) -> dict[str, Any]:
    """Create a customer account.

    Sign-up can never create an administrator: the role is fixed here.
    """
    clean_name = (full_name or "").strip()
    if not clean_name:
        raise ValidationError("Full name is required.", "full_name")
    if len(clean_name) > 120:
        raise ValidationError("Full name must be 120 characters or fewer.", "full_name")

    clean_email = (email or "").strip().lower()
    if not clean_email:
        raise ValidationError("Email is required.", "email")
    if not EMAIL_PATTERN.match(clean_email):
        raise ValidationError("Enter a valid email address.", "email")
    if db.query_one("SELECT id FROM users WHERE email = ?", (clean_email,)):
        raise ValidationError("An account with this email already exists.", "email")

    clean_phone = (phone or "").strip()
    if clean_phone and not PHONE_PATTERN.match(clean_phone):
        raise ValidationError("Enter a valid PH mobile number (09XXXXXXXXX).", "phone")

    if not password:
        raise ValidationError("Password is required.", "password")
    problems = security.password_problems(password)
    if problems:
        raise ValidationError(problems[0], "password")
    if password != confirm_password:
        raise ValidationError("Passwords do not match.", "confirm_password")

    salt, digest = security.hash_password(password)
    cursor = db.execute(
        "INSERT INTO users (full_name, email, phone, role, pw_salt, pw_hash, is_active) "
        "VALUES (?, ?, ?, 'customer', ?, ?, 1)",
        (clean_name, clean_email, clean_phone, salt, digest),
    )
    return get_user(int(cursor.lastrowid)) or {}


# ── Login ────────────────────────────────────────────────────────────────────
def login(email: str, password: str) -> dict[str, Any]:
    """Authenticate a user and return their record.

    After five failed attempts for the same email the account is locked for
    five minutes. The failure message never reveals which part was wrong.
    """
    clean_email = (email or "").strip().lower()
    if not clean_email or not password:
        raise AuthError(GENERIC_LOGIN_ERROR)

    row = db.query_one("SELECT * FROM users WHERE email = ?", (clean_email,))
    if row is None:
        raise AuthError(GENERIC_LOGIN_ERROR)
    user = dict(row)

    if _is_locked(user):
        raise AuthError(_lockout_message(user))

    if not user["is_active"]:
        raise AuthError("This account has been deactivated. Please contact support.")

    if not security.verify_password(password, user["pw_salt"], user["pw_hash"]):
        _register_failure(user)
        raise AuthError(GENERIC_LOGIN_ERROR)

    _clear_failures(user)
    return _public_user(user)


def _is_locked(user: dict[str, Any]) -> bool:
    locked_until = _parse_datetime(user.get("locked_until"))
    return bool(locked_until and locked_until > datetime.now())


def _lockout_message(user: dict[str, Any]) -> str:
    locked_until = _parse_datetime(user.get("locked_until")) or datetime.now()
    minutes = max(1, math.ceil((locked_until - datetime.now()).total_seconds() / 60))
    return f"Too many failed attempts. Try again in {minutes} minute(s)."


def _register_failure(user: dict[str, Any]) -> None:
    attempts = int(user.get("failed_attempts") or 0) + 1
    if attempts >= config.MAX_FAILED_LOGINS:
        locked_until = datetime.now() + timedelta(minutes=config.LOCKOUT_MINUTES)
        db.execute(
            "UPDATE users SET failed_attempts = 0, locked_until = ? WHERE id = ?",
            (locked_until.strftime("%Y-%m-%d %H:%M:%S"), user["id"]),
        )
    else:
        db.execute("UPDATE users SET failed_attempts = ? WHERE id = ?", (attempts, user["id"]))


def _clear_failures(user: dict[str, Any]) -> None:
    db.execute(
        "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (user["id"],)
    )


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return None


# ── Self-service ─────────────────────────────────────────────────────────────
def change_password(actor: dict[str, Any], current_password: str,
                    new_password: str, confirm_password: str) -> dict[str, Any]:
    """Change the signed-in user's own password."""
    if not actor:
        raise AuthError("You must be signed in to change your password.")
    row = db.query_one("SELECT * FROM users WHERE id = ?", (actor["id"],))
    if row is None:
        raise AuthError("That account no longer exists.")
    if not security.verify_password(current_password, row["pw_salt"], row["pw_hash"]):
        raise ValidationError("Your current password is incorrect.", "current_password")
    problems = security.password_problems(new_password)
    if problems:
        raise ValidationError(problems[0], "new_password")
    if new_password != confirm_password:
        raise ValidationError("Passwords do not match.", "confirm_password")
    salt, digest = security.hash_password(new_password)
    db.execute(
        "UPDATE users SET pw_salt = ?, pw_hash = ?, failed_attempts = 0, "
        "locked_until = NULL, must_change_password = 0 WHERE id = ?",
        (salt, digest, actor["id"]),
    )
    return get_user(actor["id"]) or {}


def update_profile(actor: dict[str, Any], full_name: str, phone: str,
                   address: str) -> dict[str, Any]:
    """Update the signed-in user's own profile."""
    if not actor:
        raise AuthError("You must be signed in to edit your profile.")
    clean_name = (full_name or "").strip()
    if not clean_name:
        raise ValidationError("Full name is required.", "full_name")
    if len(clean_name) > 120:
        raise ValidationError("Full name must be 120 characters or fewer.", "full_name")
    clean_phone = (phone or "").strip()
    if clean_phone and not PHONE_PATTERN.match(clean_phone):
        raise ValidationError("Enter a valid PH mobile number (09XXXXXXXXX).", "phone")
    clean_address = (address or "").strip()
    if len(clean_address) > 255:
        raise ValidationError("Address must be 255 characters or fewer.", "address")
    db.execute(
        "UPDATE users SET full_name = ?, phone = ?, address = ? WHERE id = ?",
        (clean_name, clean_phone, clean_address, actor["id"]),
    )
    return get_user(actor["id"]) or {}


# ── Administration ───────────────────────────────────────────────────────────
def list_customers(actor: dict[str, Any], search: str = "") -> list[dict[str, Any]]:
    """List customer accounts with their booking counts."""
    _require_admin(actor)
    term = (search or "").strip()
    if term:
        like = f"%{term}%"
        rows = db.query(
            "SELECT u.id, u.full_name, u.email, u.phone, u.is_active, u.created_at, "
            "(SELECT COUNT(*) FROM bookings b WHERE b.user_id = u.id) AS booking_count "
            "FROM users u WHERE u.role = 'customer' AND "
            "(u.full_name LIKE ? OR u.email LIKE ? OR u.phone LIKE ?) "
            "ORDER BY u.full_name",
            (like, like, like),
        )
    else:
        rows = db.query(
            "SELECT u.id, u.full_name, u.email, u.phone, u.is_active, u.created_at, "
            "(SELECT COUNT(*) FROM bookings b WHERE b.user_id = u.id) AS booking_count "
            "FROM users u WHERE u.role = 'customer' ORDER BY u.full_name"
        )
    results = []
    for row in rows:
        data = dict(row)
        data["is_active"] = bool(data["is_active"])
        results.append(data)
    return results


def set_user_active(actor: dict[str, Any], user_id: int, active: bool) -> dict[str, Any]:
    """Deactivate or reactivate a customer account."""
    _require_admin(actor)
    if int(actor["id"]) == int(user_id):
        raise ConflictError("You cannot deactivate your own account.")
    target = db.query_one("SELECT id, role FROM users WHERE id = ?", (user_id,))
    if target is None:
        raise ValidationError("That account no longer exists.")
    if target["role"] != "customer":
        raise PermissionDenied("Only customer accounts can be deactivated.")
    db.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if active else 0, user_id))
    return get_user(user_id) or {}


def create_admin(actor: dict[str, Any], full_name: str, email: str,
                 password: str) -> dict[str, Any]:
    """Create another administrator account."""
    _require_admin(actor)
    clean_name = (full_name or "").strip()
    if not clean_name:
        raise ValidationError("Full name is required.", "full_name")
    clean_email = (email or "").strip().lower()
    if not EMAIL_PATTERN.match(clean_email):
        raise ValidationError("Enter a valid email address.", "email")
    if db.query_one("SELECT id FROM users WHERE email = ?", (clean_email,)):
        raise ConflictError("An account with this email already exists.")
    problems = security.password_problems(password)
    if problems:
        raise ValidationError(problems[0], "password")
    salt, digest = security.hash_password(password)
    cursor = db.execute(
        "INSERT INTO users (full_name, email, role, pw_salt, pw_hash, is_active) "
        "VALUES (?, ?, 'admin', ?, ?, 1)",
        (clean_name, clean_email, salt, digest),
    )
    return get_user(int(cursor.lastrowid)) or {}


def _require_admin(actor: dict[str, Any] | None) -> None:
    if not actor or actor.get("role") != "admin":
        raise PermissionDenied("Only an administrator can do that.")

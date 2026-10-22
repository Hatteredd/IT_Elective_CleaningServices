"""Business logic layer.

Every module in this package works with plain dictionaries and never imports
Tkinter, so the rules can be exercised by unit tests without a display.
"""

from __future__ import annotations

from typing import Any

ADMIN_ROLE = "admin"


class ServiceError(Exception):
    """Base class for every error raised by the logic layer."""


class ValidationError(ServiceError):
    """Input failed validation.

    ``field`` names the offending input so the UI can show the message
    inline under the right control.
    """

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


class AuthError(ServiceError):
    """Authentication failed or the account is locked out."""


class PermissionDenied(ServiceError):
    """The signed-in user is not allowed to perform this action."""


class ConflictError(ServiceError):
    """The requested change clashes with existing data."""


def require_admin(actor: dict[str, Any] | None) -> dict[str, Any]:
    """Return ``actor`` when they are an administrator, otherwise refuse.

    Every admin-only service call starts with this, so the rule lives in one
    place instead of being copied into each service module.
    """
    if not actor or actor.get("role") != ADMIN_ROLE:
        raise PermissionDenied("Only an administrator can do that.")
    return actor

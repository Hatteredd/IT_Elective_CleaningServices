"""Business logic layer.

Every module in this package works with plain dictionaries and never imports
Tkinter, so the rules can be exercised by unit tests without a display.
"""

from __future__ import annotations


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

"""Administrator maintenance actions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cleanhome import db
from cleanhome.services import require_admin


def create_backup(actor: dict[str, Any] | None) -> Path:
    """Copy the database to the backup folder and return the new file."""
    require_admin(actor)
    return db.backup_database()

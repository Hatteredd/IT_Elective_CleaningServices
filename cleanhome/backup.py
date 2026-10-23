"""Command-line database backup, usable without opening the app.

Run it from the project root::

    python -m cleanhome.backup
    python -m cleanhome.backup --output D:\\CleanHomeBackups

The copy is written to ``backups/`` inside the data folder by default:
``cleanhome/backups`` when running from source, or
``%LOCALAPPDATA%\\CleanHomePH\\backups`` for the packaged app.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from cleanhome import config, db


def main(argv: list[str] | None = None) -> int:
    """Copy the database and print where the backup was written."""
    parser = argparse.ArgumentParser(
        prog="python -m cleanhome.backup",
        description="Copy the CleanHome database to a timestamped backup file.",
    )
    parser.add_argument("--output", type=Path, default=None,
                        help=f"folder for the backup (default: {config.BACKUP_DIR})")
    args = parser.parse_args(argv)
    if not config.DB_PATH.exists():
        print(f"No database found at {config.DB_PATH}.")
        print("Start CleanHome once first so it can create the database.")
        return 1
    try:
        db.init_db()
        db.migrate()
        target = db.backup_database(args.output)
    except (sqlite3.Error, OSError) as error:
        print(f"The backup could not be created: {error}")
        return 1
    finally:
        db.close_connection()
    print(f"Backup written to {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

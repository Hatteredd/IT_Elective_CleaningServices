"""SQLite connection, schema, migrations, and seed data.

The app talks to SQLite through this module only. Every statement uses
parameter placeholders — no SQL is ever built by string concatenation.
"""

from __future__ import annotations

import logging
import re
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Iterable, Iterator, Sequence

from cleanhome import config

_lock = threading.RLock()
_connection: sqlite3.Connection | None = None

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name       TEXT    NOT NULL,
        email           TEXT    NOT NULL COLLATE NOCASE UNIQUE,
        phone           TEXT,
        address         TEXT,
        role            TEXT    NOT NULL DEFAULT 'customer'
                                CHECK (role IN ('customer', 'admin')),
        pw_salt         TEXT    NOT NULL,
        pw_hash         TEXT    NOT NULL,
        is_active       INTEGER NOT NULL DEFAULT 1,
        failed_attempts INTEGER NOT NULL DEFAULT 0,
        locked_until    TEXT,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS services (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT    NOT NULL UNIQUE,
        description   TEXT,
        price         REAL    NOT NULL,
        duration_mins INTEGER NOT NULL,
        is_active     INTEGER NOT NULL DEFAULT 1,
        created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS promotions (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id     INTEGER REFERENCES services(id) ON DELETE SET NULL,
        title          TEXT    NOT NULL,
        discount_type  TEXT    NOT NULL CHECK (discount_type IN ('percent', 'fixed')),
        discount_value REAL    NOT NULL,
        start_date     TEXT    NOT NULL,
        end_date       TEXT    NOT NULL,
        is_active      INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS bookings (
        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id            INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        service_id         INTEGER NOT NULL REFERENCES services(id),
        scheduled_at       TEXT    NOT NULL,
        address            TEXT    NOT NULL,
        notes              TEXT,
        price_at_booking   REAL    NOT NULL,
        discount_at_booking REAL    NOT NULL DEFAULT 0,
        status             TEXT    NOT NULL DEFAULT 'pending'
                                 CHECK (status IN ('pending', 'confirmed', 'in_progress',
                                                   'completed', 'cancelled')),
        cancel_reason      TEXT,
        created_at         TEXT    NOT NULL DEFAULT (datetime('now')),
        updated_at         TEXT    NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_bookings_scheduled ON bookings(scheduled_at)",
    "CREATE INDEX IF NOT EXISTS idx_promotions_service ON promotions(service_id)",
)

# Columns added after the first release; applied by migrate().
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
COLUMN_MIGRATIONS: tuple[tuple[str, str, str], ...] = (
    ("users", "address", "TEXT"),
    ("users", "phone", "TEXT"),
    ("users", "failed_attempts", "INTEGER NOT NULL DEFAULT 0"),
    ("users", "locked_until", "TEXT"),
    ("users", "must_change_password", "INTEGER NOT NULL DEFAULT 0"),
    ("bookings", "cancel_reason", "TEXT"),
    ("services", "inclusions", "TEXT DEFAULT ''"),
)


def get_connection() -> sqlite3.Connection:
    """Return the shared SQLite connection, opening it on first use."""
    global _connection
    with _lock:
        if _connection is None:
            _connection = _open()
        return _connection


def _open() -> sqlite3.Connection:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute(f"PRAGMA busy_timeout = {config.DB_BUSY_TIMEOUT_MS}")
    return connection


def close_connection() -> None:
    """Close the shared connection (called when the app exits)."""
    global _connection
    with _lock:
        if _connection is not None:
            _connection.commit()
            _connection.close()
            _connection = None


def query(sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
    """Run a SELECT and return every row."""
    try:
        return get_connection().execute(sql, tuple(params)).fetchall()
    except sqlite3.Error as error:
        raise _friendly_error(error) from error


def query_one(sql: str, params: Sequence[Any] = ()) -> sqlite3.Row | None:
    """Run a SELECT and return the first row, or None."""
    try:
        return get_connection().execute(sql, tuple(params)).fetchone()
    except sqlite3.Error as error:
        raise _friendly_error(error) from error


def execute(sql: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
    """Run an INSERT/UPDATE/DELETE and return the cursor."""
    connection = get_connection()
    try:
        cursor = connection.execute(sql, tuple(params))
        connection.commit()
        return cursor
    except sqlite3.Error as error:
        connection.rollback()
        raise _friendly_error(error) from error


def _friendly_error(error: sqlite3.Error) -> Exception:
    """Log a database failure and turn it into a message a user can read.

    The original exception is kept as the cause so the traceback in
    ``app.log`` still shows the real problem.
    """
    from cleanhome.services import ServiceError

    logging.exception("Database operation failed")
    if isinstance(error, sqlite3.IntegrityError):
        message = "That change conflicts with a record that already exists."
    elif isinstance(error, sqlite3.OperationalError):
        text = str(error).lower()
        if "locked" in text or "busy" in text:
            message = "The database is busy right now. Please try again."
        else:
            message = "The database could not run that request."
    else:
        message = "We could not reach the database. Please try again."
    return ServiceError(message)


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    """Run a block of statements as one transaction."""
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except BaseException:
        # The error is always re-raised; the rollback only undoes the
        # half-finished work inside the block.
        connection.rollback()
        raise


def init_db() -> None:
    """Create the schema if it does not exist yet."""
    connection = get_connection()
    with _lock:
        for statement in SCHEMA:
            connection.execute(statement)
        connection.commit()


def migrate() -> None:
    """Add any columns that a newer version of the app expects.

    SQLite cannot take a placeholder for a table or column name, so the
    identifiers are checked against a strict pattern first. They only ever
    come from the hard-coded ``COLUMN_MIGRATIONS`` list, never from input.
    """
    connection = get_connection()
    with _lock:
        for table, column, definition in COLUMN_MIGRATIONS:
            if not IDENTIFIER.fullmatch(table) or not IDENTIFIER.fullmatch(column):
                raise ValueError(f"Unsafe migration identifier: {table}.{column}")
            existing = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
            if column not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                logging.info("Migration: added %s.%s", table, column)
        connection.commit()


def seed() -> None:
    """Insert the default service catalogue and promotions."""
    connection = get_connection()
    with _lock:
        for name, description, price, duration in config.SEED_SERVICES:
            connection.execute(
                "INSERT OR IGNORE INTO services (name, description, price, duration_mins) "
                "VALUES (?, ?, ?, ?)",
                (name, description, price, duration),
            )
        connection.commit()
    _seed_promotions(connection)


def _seed_promotions(connection: sqlite3.Connection) -> None:
    """Insert the starter promotions when the table is empty."""
    existing = connection.execute("SELECT COUNT(*) AS n FROM promotions").fetchone()["n"]
    if existing:
        return
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=config.SEED_PROMOTION_SPAN_DAYS)
    for title, discount_type, value in config.SEED_PROMOTIONS:
        connection.execute(
            "INSERT INTO promotions (service_id, title, discount_type, discount_value, "
            "start_date, end_date, is_active) VALUES (NULL, ?, ?, ?, ?, ?, 1)",
            (title, discount_type, value,
             start.strftime("%Y-%m-%d %H:%M:%S"),
             end.strftime("%Y-%m-%d %H:%M:%S")),
        )
    connection.commit()


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    """Convert rows to plain dicts."""
    return [dict(row) for row in rows]

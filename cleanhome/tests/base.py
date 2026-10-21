"""Shared test setup.

Every test runs against its own throw-away SQLite file so the tests never
touch the real ``cleanhome.db``.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cleanhome import config, db


class ServiceTestCase(unittest.TestCase):
    """Base class that gives each test a clean, seeded database."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._original_path = config.DB_PATH
        config.DB_PATH = Path(self._tmpdir.name) / "test.db"
        db.close_connection()
        db.init_db()
        db.migrate()
        db.seed()

    def tearDown(self) -> None:
        db.close_connection()
        config.DB_PATH = self._original_path
        self._tmpdir.cleanup()

    # ── Helpers ──────────────────────────────────────────────────────────────
    def make_admin(self, email: str = "admin@test.ph",
                   password: str = "TestPass123") -> dict:
        from cleanhome import security
        from cleanhome.services import auth_service

        salt, digest = security.hash_password(password)
        cursor = db.execute(
            "INSERT INTO users (full_name, email, role, pw_salt, pw_hash, is_active) "
            "VALUES (?, ?, 'admin', ?, ?, 1)",
            ("Test Admin", email, salt, digest),
        )
        return auth_service.get_user(int(cursor.lastrowid)) or {}

    def make_customer(self, email: str = "customer@test.ph",
                      password: str = "TestPass123", name: str = "Test Customer") -> dict:
        from cleanhome import security
        from cleanhome.services import auth_service

        salt, digest = security.hash_password(password)
        cursor = db.execute(
            "INSERT INTO users (full_name, email, role, pw_salt, pw_hash, is_active) "
            "VALUES (?, ?, 'customer', ?, ?, 1)",
            (name, email, salt, digest),
        )
        return auth_service.get_user(int(cursor.lastrowid)) or {}

    def make_service(self, name: str = "Test Cleaning", price: float = 1000.0,
                     duration: int = 60) -> dict:
        from cleanhome.services import catalog_service

        admin = self.make_admin("owner@test.ph")
        service = catalog_service.create_service(admin, name, "A test service.",
                                                 price, duration)
        return service

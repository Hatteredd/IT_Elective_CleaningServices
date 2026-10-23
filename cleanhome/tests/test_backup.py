"""Creating a database backup, from the dashboard and from the console."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import date, datetime, time, timedelta
from pathlib import Path

from cleanhome import backup, config
from cleanhome.services import PermissionDenied, maintenance_service
from cleanhome.tests.base import ServiceTestCase


class BackupTests(ServiceTestCase):
    """A backup is a complete copy that can be opened on its own."""

    def setUp(self) -> None:
        super().setUp()
        self._original_backup_dir = config.BACKUP_DIR
        self.admin = self.make_admin("boss@test.ph")
        self.customer = self.make_customer("buyer@test.ph")
        from cleanhome.services import booking_service, catalog_service

        self.service = catalog_service.create_service(
            self.admin, "Standard Clean", "A test service", 1000.0, 60)
        when = datetime.combine(date.today() + timedelta(days=5), time(10, 0))
        self.booking = booking_service.create_booking(
            self.customer, self.service["id"], when, "12 Quezon Ave")

    def tearDown(self) -> None:
        config.BACKUP_DIR = self._original_backup_dir
        super().tearDown()

    def _use_folder(self, folder: str) -> None:
        config.BACKUP_DIR = Path(folder) / "backups"

    def _counts(self, path: Path) -> tuple[int, int]:
        connection = sqlite3.connect(path)
        try:
            users = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            bookings = connection.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        finally:
            connection.close()
        return int(users), int(bookings)

    def test_an_admin_can_back_up_the_database(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            self._use_folder(folder)
            target = maintenance_service.create_backup(self.admin)
            self.assertTrue(target.exists())
            users, bookings = self._counts(target)
        self.assertEqual(users, 2)
        self.assertEqual(bookings, 1)

    def test_a_customer_cannot_back_up_the_database(self) -> None:
        with self.assertRaises(PermissionDenied):
            maintenance_service.create_backup(self.customer)

    def test_two_backups_never_overwrite_each_other(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            self._use_folder(folder)
            first = maintenance_service.create_backup(self.admin)
            second = maintenance_service.create_backup(self.admin)
            self.assertNotEqual(first, second)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())

    def test_the_console_command_writes_a_backup(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(backup.main(["--output", folder]), 0)
            files = list(Path(folder).glob("cleanhome-*.db"))
            sizes = [path.stat().st_size for path in files]
        self.assertEqual(len(files), 1)
        self.assertGreater(sizes[0], 0)

    def test_the_backup_can_be_opened_and_read_without_the_live_connection(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            self._use_folder(folder)
            target = maintenance_service.create_backup(self.admin)
            from cleanhome import db

            db.close_connection()
            connection = sqlite3.connect(target)
            try:
                row = connection.execute(
                    "SELECT price_at_booking FROM bookings WHERE id = ?",
                    (self.booking["id"],)).fetchone()
            finally:
                connection.close()
        self.assertAlmostEqual(float(row[0]), 1000.0)


if __name__ == "__main__":
    unittest.main()

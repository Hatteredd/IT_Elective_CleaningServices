"""Data survives closing and reopening the connection."""

from __future__ import annotations

import unittest
from datetime import date, datetime, time, timedelta

from cleanhome import db
from cleanhome.services import auth_service, booking_service, catalog_service
from cleanhome.tests.base import ServiceTestCase


class PersistenceTests(ServiceTestCase):
    """The same database file is reopened, not recreated."""

    def test_accounts_bookings_and_prices_survive_a_reopen(self) -> None:
        admin = self.make_admin("boss@test.ph")
        customer = self.make_customer("buyer@test.ph", "TestPass123")
        service = catalog_service.create_service(admin, "Standard Clean",
                                                 "A test service", 1000.0, 60)
        when = datetime.combine(date.today() + timedelta(days=6), time(10, 0))
        booking = booking_service.create_booking(
            customer, service["id"], when, "12 Quezon Ave", "Bring soap")
        db.execute("UPDATE bookings SET status = 'confirmed' WHERE id = ?",
                   (booking["id"],))

        db.close_connection()
        db.init_db()
        db.migrate()

        stored = booking_service.get_booking(booking["id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["status"], "confirmed")
        self.assertEqual(stored["address"], "12 Quezon Ave")
        self.assertEqual(stored["notes"], "Bring soap")
        self.assertEqual(float(stored["price_at_booking"]), 1000.0)
        self.assertIsNotNone(auth_service.login("buyer@test.ph", "TestPass123"))
        self.assertIsNotNone(catalog_service.get_service(service["id"]))


if __name__ == "__main__":
    unittest.main()

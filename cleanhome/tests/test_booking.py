"""Booking rules: dates, business hours, capacity, price maths, and status flow."""

from __future__ import annotations

import unittest
from datetime import date, datetime, time, timedelta

from cleanhome import config, db
from cleanhome.services import (ConflictError, PermissionDenied, ValidationError,
                                booking_service, catalog_service)
from cleanhome.tests.base import ServiceTestCase


def future_day(days: int = 7) -> date:
    """Return a date far enough ahead that the lead-time rule is satisfied."""
    return date.today() + timedelta(days=days)


def slot_time(day: date, hour: int = 10) -> datetime:
    """Return a valid start time on the given day."""
    return datetime.combine(day, time(hour, 0))


class BookingCreationTests(ServiceTestCase):
    """When a booking may be made."""

    def setUp(self) -> None:
        super().setUp()
        self.admin = self.make_admin("boss@test.ph")
        self.customer = self.make_customer("buyer@test.ph")
        self.service = catalog_service.create_service(self.admin, "Standard Clean",
                                                      "A test service", 1000.0, 60)

    def test_booking_is_created_with_the_stored_price(self) -> None:
        booking = booking_service.create_booking(self.customer, self.service["id"],
                                                 slot_time(future_day()),
                                                 "12 Quezon Ave", "Please bring soap")
        self.assertEqual(booking["status"], "pending")
        self.assertEqual(float(booking["price_at_booking"]), 1000.0)
        self.assertEqual(booking["address"], "12 Quezon Ave")
        self.assertEqual(booking["notes"], "Please bring soap")

    def test_a_past_date_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            booking_service.create_booking(self.customer, self.service["id"],
                                           slot_time(date.today() - timedelta(days=1)),
                                           "12 Quezon Ave")

    def test_a_date_inside_the_lead_time_is_rejected(self) -> None:
        soon = datetime.now() + timedelta(hours=1)
        with self.assertRaises(ValidationError):
            booking_service.create_booking(self.customer, self.service["id"], soon,
                                           "12 Quezon Ave")

    def test_a_time_before_opening_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            booking_service.create_booking(self.customer, self.service["id"],
                                           slot_time(future_day(), config.BUSINESS_OPEN_HOUR - 1),
                                           "12 Quezon Ave")
        self.assertEqual(caught.exception.field, "scheduled_at")

    def test_a_time_that_runs_past_closing_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            booking_service.create_booking(self.customer, self.service["id"],
                                           slot_time(future_day(),
                                                     config.BUSINESS_CLOSE_HOUR),
                                           "12 Quezon Ave")

    def test_a_time_off_the_slot_interval_is_rejected(self) -> None:
        odd = datetime.combine(future_day(), time(10, 7))
        with self.assertRaises(ValidationError):
            booking_service.create_booking(self.customer, self.service["id"], odd,
                                           "12 Quezon Ave")

    def test_the_address_is_required(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            booking_service.create_booking(self.customer, self.service["id"],
                                           slot_time(future_day()), "   ")
        self.assertEqual(caught.exception.field, "address")

    def test_an_admin_cannot_book(self) -> None:
        with self.assertRaises(PermissionDenied):
            booking_service.create_booking(self.admin, self.service["id"],
                                           slot_time(future_day()), "12 Quezon Ave")

    def test_an_inactive_service_cannot_be_booked(self) -> None:
        catalog_service.archive_service(self.admin, self.service["id"])
        with self.assertRaises(ValidationError):
            booking_service.create_booking(self.customer, self.service["id"],
                                           slot_time(future_day()), "12 Quezon Ave")


class CapacityTests(ServiceTestCase):
    """No more than three cleanings may overlap."""

    def setUp(self) -> None:
        super().setUp()
        self.admin = self.make_admin("boss@test.ph")
        self.customer = self.make_customer("buyer@test.ph")
        self.service = catalog_service.create_service(self.admin, "Standard Clean",
                                                      "A test service", 1000.0, 60)
        self.day = future_day()
        self.start = slot_time(self.day, 10)

    def test_the_fourth_overlapping_booking_is_rejected(self) -> None:
        for _ in range(config.MAX_CONCURRENT_BOOKINGS):
            booking_service.create_booking(self.customer, self.service["id"], self.start,
                                           "12 Quezon Ave")
        with self.assertRaises(ValidationError) as caught:
            booking_service.create_booking(self.customer, self.service["id"], self.start,
                                           "12 Quezon Ave")
        self.assertIn("fully booked", str(caught.exception).lower())

    def test_a_cancelled_booking_frees_the_slot(self) -> None:
        bookings = []
        for _ in range(config.MAX_CONCURRENT_BOOKINGS):
            bookings.append(booking_service.create_booking(
                self.customer, self.service["id"], self.start, "12 Quezon Ave"))
        booking_service.cancel_booking(self.customer, bookings[0]["id"], "Change of plan")
        extra = booking_service.create_booking(self.customer, self.service["id"], self.start,
                                                "12 Quezon Ave")
        self.assertEqual(extra["status"], "pending")

    def test_a_booking_after_the_others_finish_is_allowed(self) -> None:
        for _ in range(config.MAX_CONCURRENT_BOOKINGS):
            booking_service.create_booking(self.customer, self.service["id"], self.start,
                                           "12 Quezon Ave")
        later = slot_time(self.day, 12)
        booking = booking_service.create_booking(self.customer, self.service["id"], later,
                                                  "12 Quezon Ave")
        self.assertEqual(booking["status"], "pending")


class PriceTests(ServiceTestCase):
    """Price, discount, and total maths."""

    def setUp(self) -> None:
        super().setUp()
        self.admin = self.make_admin("boss@test.ph")
        self.customer = self.make_customer("buyer@test.ph")
        self.service = catalog_service.create_service(self.admin, "Standard Clean",
                                                      "A test service", 1000.0, 60)
        self.when = slot_time(future_day(), 10)

    def test_quote_without_a_promotion_is_the_full_price(self) -> None:
        catalog_service.end_promotion(self.admin, 1)
        catalog_service.end_promotion(self.admin, 2)
        quote = booking_service.quote(self.service["id"], self.when)
        self.assertEqual(float(quote["price"]), 1000.0)
        self.assertEqual(float(quote["discount"]), 0.0)
        self.assertEqual(float(quote["total"]), 1000.0)

    def test_a_percentage_promotion_is_applied(self) -> None:
        for promo in catalog_service.list_promotions():
            catalog_service.end_promotion(self.admin, promo["id"])
        catalog_service.create_promotion(self.admin, "Ten Off", self.service["id"],
                                         "percent", 10, self.when - timedelta(days=1),
                                         self.when + timedelta(days=1))
        quote = booking_service.quote(self.service["id"], self.when)
        self.assertEqual(float(quote["discount"]), 100.0)
        self.assertEqual(float(quote["total"]), 900.0)

    def test_a_fixed_promotion_is_applied(self) -> None:
        for promo in catalog_service.list_promotions():
            catalog_service.end_promotion(self.admin, promo["id"])
        catalog_service.create_promotion(self.admin, "Two Hundred Off", self.service["id"],
                                         "fixed", 200, self.when - timedelta(days=1),
                                         self.when + timedelta(days=1))
        quote = booking_service.quote(self.service["id"], self.when)
        self.assertEqual(float(quote["discount"]), 200.0)
        self.assertEqual(float(quote["total"]), 800.0)

    def test_only_the_best_promotion_applies(self) -> None:
        for promo in catalog_service.list_promotions():
            catalog_service.end_promotion(self.admin, promo["id"])
        catalog_service.create_promotion(self.admin, "Ten Percent", self.service["id"],
                                         "percent", 10, self.when - timedelta(days=1),
                                         self.when + timedelta(days=1))
        catalog_service.create_promotion(self.admin, "Two Hundred Off", self.service["id"],
                                         "fixed", 200, self.when - timedelta(days=1),
                                         self.when + timedelta(days=1))
        quote = booking_service.quote(self.service["id"], self.when)
        self.assertEqual(float(quote["discount"]), 200.0)

    def test_a_promotion_that_ends_is_not_applied(self) -> None:
        for promo in catalog_service.list_promotions():
            catalog_service.end_promotion(self.admin, promo["id"])
        catalog_service.create_promotion(self.admin, "Over", self.service["id"],
                                         "percent", 50, self.when - timedelta(days=5),
                                         self.when - timedelta(days=2))
        quote = booking_service.quote(self.service["id"], self.when)
        self.assertEqual(float(quote["discount"]), 0.0)

    def test_the_booking_stores_the_price_it_was_quoted(self) -> None:
        for promo in catalog_service.list_promotions():
            catalog_service.end_promotion(self.admin, promo["id"])
        catalog_service.create_promotion(self.admin, "Ten Off", self.service["id"],
                                         "percent", 10, self.when - timedelta(days=1),
                                         self.when + timedelta(days=1))
        booking = booking_service.create_booking(self.customer, self.service["id"], self.when,
                                                  "12 Quezon Ave")
        self.assertEqual(float(booking["price_at_booking"]), 1000.0)
        self.assertEqual(float(booking["discount_at_booking"]), 100.0)
        self.assertEqual(float(booking["total_at_booking"]), 900.0)

    def test_a_later_price_change_does_not_rewrite_a_booking(self) -> None:
        for promo in catalog_service.list_promotions():
            catalog_service.end_promotion(self.admin, promo["id"])
        booking = booking_service.create_booking(self.customer, self.service["id"],
                                                  self.when, "12 Quezon Ave")
        catalog_service.update_service(self.admin, self.service["id"], "Standard Clean",
                                       "A test service", 1500.0, 60)
        stored = booking_service.get_booking(booking["id"])
        self.assertEqual(float(stored["price_at_booking"]), 1000.0)
        self.assertEqual(float(stored["total_at_booking"]), 1000.0)


class StatusFlowTests(ServiceTestCase):
    """The status of a booking may only move forward."""

    def setUp(self) -> None:
        super().setUp()
        self.admin = self.make_admin("boss@test.ph")
        self.customer = self.make_customer("buyer@test.ph")
        self.service = catalog_service.create_service(self.admin, "Standard Clean",
                                                      "A test service", 1000.0, 60)
        self.booking = booking_service.create_booking(
            self.customer, self.service["id"], slot_time(future_day()), "12 Quezon Ave")

    def test_pending_can_be_confirmed_started_and_completed(self) -> None:
        for status in ("confirmed", "in_progress", "completed"):
            booking = booking_service.change_status(self.admin, self.booking["id"], status)
            self.assertEqual(booking["status"], status)

    def test_pending_cannot_jump_straight_to_completed(self) -> None:
        with self.assertRaises(ConflictError):
            booking_service.change_status(self.admin, self.booking["id"], "completed")

    def test_a_customer_cannot_cancel_inside_the_cutoff(self) -> None:
        soon = datetime.now() + timedelta(hours=config.MIN_LEAD_TIME_HOURS + 1)
        cursor = db.execute(
            "INSERT INTO bookings (user_id, service_id, scheduled_at, address, "
            "price_at_booking, discount_at_booking, status) "
            "VALUES (?, ?, ?, ?, ?, 0, 'pending')",
            (self.customer["id"], self.service["id"],
             soon.strftime("%Y-%m-%d %H:%M:%S"), "12 Quezon Ave", 1000.0),
        )
        booking_id = int(cursor.lastrowid)
        with self.assertRaises(ConflictError) as caught:
            booking_service.cancel_booking(self.customer, booking_id, "Too late")
        self.assertIn(str(config.CANCEL_CUTOFF_HOURS), str(caught.exception))
        self.assertEqual(booking_service.get_booking(booking_id)["status"], "pending")

    def test_a_completed_booking_cannot_go_back_to_pending(self) -> None:
        booking_service.change_status(self.admin, self.booking["id"], "confirmed")
        booking_service.change_status(self.admin, self.booking["id"], "in_progress")
        booking_service.change_status(self.admin, self.booking["id"], "completed")
        with self.assertRaises(ConflictError):
            booking_service.change_status(self.admin, self.booking["id"], "pending")

    def test_a_cancelled_booking_cannot_be_reopened(self) -> None:
        booking_service.cancel_booking(self.customer, self.booking["id"], "Plans changed")
        with self.assertRaises(ConflictError):
            booking_service.change_status(self.admin, self.booking["id"], "confirmed")

    def test_a_customer_cannot_change_the_status(self) -> None:
        with self.assertRaises(PermissionDenied):
            booking_service.change_status(self.customer, self.booking["id"], "confirmed")

    def test_an_admin_cancellation_needs_a_reason(self) -> None:
        with self.assertRaises(ValidationError):
            booking_service.cancel_booking(self.admin, self.booking["id"], "")

    def test_a_cancellation_stores_the_reason(self) -> None:
        booking = booking_service.cancel_booking(self.admin, self.booking["id"],
                                                 "Cleaner unavailable")
        self.assertEqual(booking["status"], "cancelled")
        self.assertEqual(booking["cancel_reason"], "Cleaner unavailable")

    def test_rescheduling_moves_the_booking(self) -> None:
        new_time = slot_time(future_day(), 14)
        booking = booking_service.reschedule(self.admin, self.booking["id"], new_time)
        self.assertEqual(booking["scheduled_at_dt"].hour, 14)

    def test_rescheduling_into_the_past_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            booking_service.reschedule(self.admin, self.booking["id"],
                                       slot_time(date.today() - timedelta(days=1)))

    def test_a_customer_may_reschedule_their_own_booking(self) -> None:
        new_time = slot_time(future_day(), 14)
        booking = booking_service.reschedule(self.customer, self.booking["id"], new_time)
        self.assertEqual(booking["scheduled_at_dt"].hour, 14)

    def test_a_customer_cannot_reschedule_someone_elses_booking(self) -> None:
        other = self.make_customer("other@test.ph")
        with self.assertRaises(PermissionDenied):
            booking_service.reschedule(other, self.booking["id"],
                                       slot_time(future_day(), 14))


if __name__ == "__main__":
    unittest.main()

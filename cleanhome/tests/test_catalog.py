"""The catalogue: services, promotions, archiving, and the report screens."""

from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from cleanhome import config
from cleanhome.services import (PermissionDenied, ValidationError, booking_service,
                                catalog_service, report_service)
from cleanhome.tests.base import ServiceTestCase


class ServiceRuleTests(ServiceTestCase):
    """Service validation and the archive rule."""

    def setUp(self) -> None:
        super().setUp()
        self.admin = self.make_admin("boss@test.ph")
        self.customer = self.make_customer("buyer@test.ph")

    def test_a_service_is_created_active(self) -> None:
        service = catalog_service.create_service(self.admin, "Deep Clean", "Top to bottom",
                                                 2500.0, 180)
        self.assertTrue(service["is_active"])
        self.assertEqual(float(service["price"]), 2500.0)
        self.assertEqual(service["duration_mins"], 180)

    def test_a_customer_cannot_create_a_service(self) -> None:
        with self.assertRaises(PermissionDenied):
            catalog_service.create_service(self.customer, "Sneaky", "Nope", 100.0, 60)

    def test_the_name_is_required(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            catalog_service.create_service(self.admin, "  ", "No name", 100.0, 60)
        self.assertEqual(caught.exception.field, "name")

    def test_the_price_must_be_a_number_above_zero(self) -> None:
        with self.assertRaises(ValidationError):
            catalog_service.create_service(self.admin, "Bad", "Bad price", "abc", 60)
        with self.assertRaises(ValidationError):
            catalog_service.create_service(self.admin, "Bad", "Zero price", 0, 60)

    def test_the_duration_must_be_within_the_limits(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            catalog_service.create_service(self.admin, "Bad", "Too short", 100.0, 5)
        self.assertEqual(caught.exception.field, "duration")

    def test_a_service_with_bookings_is_archived_and_never_deleted(self) -> None:
        service = catalog_service.create_service(self.admin, "Deep Clean", "Top to bottom",
                                                 2500.0, 180)
        when = datetime.combine(datetime.now().date() + timedelta(days=7),
                                datetime.min.time()).replace(hour=10)
        booking_service.create_booking(self.customer, service["id"], when, "12 Quezon Ave")
        archived = catalog_service.archive_service(self.admin, service["id"])
        self.assertFalse(archived["is_active"])
        # The row and its bookings are still there.
        self.assertIsNotNone(catalog_service.get_service(service["id"]))
        self.assertEqual(len(booking_service.list_bookings_for_user(self.customer["id"])), 1)

    def test_an_archived_service_hides_from_the_catalogue(self) -> None:
        service = catalog_service.create_service(self.admin, "Deep Clean", "Top to bottom",
                                                 2500.0, 180)
        catalog_service.archive_service(self.admin, service["id"])
        active_ids = [item["id"] for item in catalog_service.list_services()]
        self.assertNotIn(service["id"], active_ids)
        with_inactive = [item["id"] for item in
                         catalog_service.list_services(include_inactive=True)]
        self.assertIn(service["id"], with_inactive)

    def test_a_service_can_be_restored(self) -> None:
        service = catalog_service.create_service(self.admin, "Deep Clean", "Top to bottom",
                                                 2500.0, 180)
        catalog_service.archive_service(self.admin, service["id"])
        restored = catalog_service.restore_service(self.admin, service["id"])
        self.assertTrue(restored["is_active"])

    def test_service_inclusions_persist(self) -> None:
        service = catalog_service.create_service(self.admin, "Deep Clean", "Top to bottom",
                                                 2500.0, 180, inclusions="Dusting\nMopping")
        fetched = catalog_service.get_service(service["id"])
        self.assertIn("Dusting", fetched.get("inclusions", ""))
        updated = catalog_service.update_service(self.admin, service["id"], "Deep Clean",
                                                  "Top to bottom", 2500.0, 180,
                                                  inclusions="Windows")
        self.assertIn("Windows", updated.get("inclusions", ""))


class PromotionRuleTests(ServiceTestCase):
    """Promotion validation and the one-promo-only rule."""

    def setUp(self) -> None:
        super().setUp()
        self.admin = self.make_admin("boss@test.ph")
        self.customer = self.make_customer("buyer@test.ph")
        self.service = catalog_service.create_service(self.admin, "Standard Clean",
                                                      "A test service", 1000.0, 60)
        self.start = datetime.now() - timedelta(days=1)
        self.end = datetime.now() + timedelta(days=30)
        for promo in catalog_service.list_promotions():
            catalog_service.end_promotion(self.admin, promo["id"])

    def test_a_percentage_promotion_is_created(self) -> None:
        promo = catalog_service.create_promotion(self.admin, "Ten Off", self.service["id"],
                                                 "percent", 10, self.start, self.end)
        self.assertEqual(promo["discount_type"], "percent")
        self.assertTrue(promo["is_active"])

    def test_a_customer_cannot_create_a_promotion(self) -> None:
        with self.assertRaises(PermissionDenied):
            catalog_service.create_promotion(self.customer, "Sneaky", self.service["id"],
                                            "percent", 10, self.start, self.end)

    def test_the_discount_type_must_be_known(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            catalog_service.create_promotion(self.admin, "Odd", self.service["id"],
                                            "money", 10, self.start, self.end)
        self.assertEqual(caught.exception.field, "discount_type")

    def test_the_percentage_must_be_within_the_limits(self) -> None:
        with self.assertRaises(ValidationError):
            catalog_service.create_promotion(self.admin, "Too much", self.service["id"],
                                            "percent", 95, self.start, self.end)

    def test_a_fixed_discount_must_be_less_than_the_service_price(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            catalog_service.create_promotion(self.admin, "Too much", self.service["id"],
                                            "fixed", 1000.0, self.start, self.end)
        self.assertEqual(caught.exception.field, "discount_value")

    def test_the_end_date_must_not_be_before_the_start_date(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            catalog_service.create_promotion(self.admin, "Backwards", self.service["id"],
                                            "percent", 10, self.end, self.start)
        self.assertEqual(caught.exception.field, "end_date")

    def test_ending_a_promotion_stops_it_applying(self) -> None:
        promo = catalog_service.create_promotion(self.admin, "Ten Off", self.service["id"],
                                                 "percent", 10, self.start, self.end)
        catalog_service.end_promotion(self.admin, promo["id"])
        active = catalog_service.applicable_promotion(self.service["id"], datetime.now())
        self.assertIsNone(active)

    def test_a_promotion_for_another_service_does_not_apply(self) -> None:
        other = catalog_service.create_service(self.admin, "Other Clean", "Different",
                                               500.0, 60)
        catalog_service.create_promotion(self.admin, "Only For Other", other["id"],
                                         "percent", 50, self.start, self.end)
        self.assertIsNone(catalog_service.applicable_promotion(self.service["id"],
                                                               datetime.now()))


class ReportTests(ServiceTestCase):
    """The dashboard and the revenue report."""

    def setUp(self) -> None:
        super().setUp()
        self.admin = self.make_admin("boss@test.ph")
        self.customer = self.make_customer("buyer@test.ph")
        self.service = catalog_service.create_service(self.admin, "Standard Clean",
                                                      "A test service", 1000.0, 60)
        for promo in catalog_service.list_promotions():
            catalog_service.end_promotion(self.admin, promo["id"])
        when = datetime.combine(datetime.now().date() + timedelta(days=3),
                                datetime.min.time()).replace(hour=10)
        self.booking = booking_service.create_booking(self.customer, self.service["id"],
                                                      when, "12 Quezon Ave")

    def test_a_customer_cannot_read_the_reports(self) -> None:
        with self.assertRaises(PermissionDenied):
            report_service.dashboard_stats(self.customer)
        with self.assertRaises(PermissionDenied):
            report_service.revenue_report(self.customer, datetime.now() - timedelta(days=1),
                                          datetime.now() + timedelta(days=1))

    def test_the_dashboard_counts_the_bookings(self) -> None:
        stats = report_service.dashboard_stats(self.admin)
        self.assertEqual(stats["pending_bookings"], 1)
        self.assertEqual(stats["active_customers"], 1)
        self.assertGreaterEqual(stats["active_services"], 1)

    def test_the_dashboard_returns_the_trend_and_the_rankings(self) -> None:
        stats = report_service.dashboard_stats(self.admin)
        self.assertEqual(len(stats["monthly_revenue"]),
                         config.DASHBOARD_TREND_MONTHS)
        self.assertTrue(all(month["label"] for month in stats["monthly_revenue"]))
        self.assertEqual(stats["status_counts"].get("pending"), 1)
        self.assertGreaterEqual(stats["bookings_this_month"], 0)
        self.assertEqual(stats["top_services"][0]["service_name"], "Standard Clean")
        self.assertEqual(stats["top_services"][0]["bookings"], 1)

        for status in ("confirmed", "in_progress", "completed"):
            booking_service.change_status(self.admin, self.booking["id"], status)
        stats = report_service.dashboard_stats(self.admin)
        self.assertEqual(stats["status_counts"].get("completed"), 1)
        self.assertEqual(float(stats["top_services"][0]["revenue"]), 1000.0)

    def test_the_revenue_report_ignores_unfinished_bookings(self) -> None:
        start = datetime.now() - timedelta(days=1)
        end = datetime.now() + timedelta(days=30)
        report = report_service.revenue_report(self.admin, start, end)
        self.assertEqual(report["total_bookings"], 1)
        self.assertEqual(float(report["revenue"]), 0.0)

        booking_service.change_status(self.admin, self.booking["id"], "confirmed")
        booking_service.change_status(self.admin, self.booking["id"], "in_progress")
        booking_service.change_status(self.admin, self.booking["id"], "completed")
        report = report_service.revenue_report(self.admin, start, end)
        self.assertEqual(float(report["revenue"]), 1000.0)

    def test_the_csv_export_contains_the_bookings(self) -> None:
        start = datetime.now() - timedelta(days=1)
        end = datetime.now() + timedelta(days=30)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.csv"
            report_service.export_revenue_csv(self.admin, str(path), start, end)
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
        self.assertGreaterEqual(len(rows), 1)
        self.assertIn("Service", rows[0][0] + " " + " ".join(rows[0]))

    def test_the_report_totals_each_status_and_counts_only_completed_revenue(self) -> None:
        start = datetime.now() - timedelta(days=1)
        end = datetime.now() + timedelta(days=30)
        for status in ("confirmed", "in_progress", "completed"):
            booking_service.change_status(self.admin, self.booking["id"], status)
        when = datetime.combine(datetime.now().date() + timedelta(days=4),
                                datetime.min.time()).replace(hour=11)
        cancelled = booking_service.create_booking(self.customer, self.service["id"],
                                                   when, "12 Quezon Ave")
        booking_service.cancel_booking(self.customer, cancelled["id"], "Plans changed")

        report = report_service.revenue_report(self.admin, start, end)
        self.assertEqual(report["total_bookings"], 2)
        self.assertEqual(report["completed"], 1)
        self.assertEqual(report["cancelled"], 1)
        self.assertEqual(float(report["revenue"]), 1000.0)
        self.assertEqual(len(report["revenue_per_service"]), 1)
        self.assertEqual(report["revenue_per_service"][0]["service_name"], "Standard Clean")
        self.assertEqual(float(report["revenue_per_service"][0]["revenue"]), 1000.0)

    def test_the_csv_has_a_header_and_one_row_per_booking(self) -> None:
        start = datetime.now() - timedelta(days=1)
        end = datetime.now() + timedelta(days=30)
        for status in ("confirmed", "in_progress", "completed"):
            booking_service.change_status(self.admin, self.booking["id"], status)
        when = datetime.combine(datetime.now().date() + timedelta(days=4),
                                datetime.min.time()).replace(hour=11)
        second = booking_service.create_booking(self.customer, self.service["id"],
                                                when, "12 Quezon Ave")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.csv"
            report_service.export_revenue_csv(self.admin, str(path), start, end)
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
        self.assertEqual(rows[0], ["Booking ID", "Scheduled At", "Customer", "Service",
                                   "Status", "Price", "Discount", "Total"])
        ids = {int(row[0]) for row in rows[1:]}
        self.assertEqual(ids, {self.booking["id"], second["id"]})
        first_row = next(row for row in rows[1:] if int(row[0]) == self.booking["id"])
        self.assertEqual(first_row[5:], ["1000.00", "0.00", "1000.00"])

    def test_a_customer_cannot_export_a_report(self) -> None:
        with self.assertRaises(PermissionDenied):
            with tempfile.TemporaryDirectory() as folder:
                report_service.export_revenue_csv(
                    self.customer, str(Path(folder) / "report.csv"),
                    datetime.now() - timedelta(days=1), datetime.now() + timedelta(days=1))


if __name__ == "__main__":
    unittest.main()

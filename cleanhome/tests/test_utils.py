"""The shared formatting helpers in ``cleanhome.utils``."""

from __future__ import annotations

import unittest
from datetime import date, datetime
from decimal import Decimal

from cleanhome import config, utils


class DecimalTests(unittest.TestCase):
    """Turning text into numbers."""

    def test_a_number_becomes_a_decimal(self) -> None:
        self.assertEqual(utils.parse_decimal("1299.50"), Decimal("1299.50"))
        self.assertEqual(utils.parse_decimal(Decimal("10")), Decimal("10"))

    def test_text_that_is_not_a_number_is_rejected(self) -> None:
        for value in ("abc", "", None, "1,299"):
            with self.assertRaises(ValueError):
                utils.parse_decimal(value)

    def test_a_boolean_is_not_a_number(self) -> None:
        with self.assertRaises(ValueError):
            utils.parse_decimal(True)

    def test_to_decimal_falls_back_instead_of_raising(self) -> None:
        self.assertEqual(utils.to_decimal("abc"), Decimal("0"))
        self.assertEqual(utils.to_decimal(None, "5"), Decimal("5"))


class WeightTests(unittest.TestCase):
    """Formatting money and dates."""

    def test_money_is_formatted_with_the_peso_sign(self) -> None:
        self.assertEqual(utils.format_peso(1299.5), f"{config.CURRENCY_SYMBOL}1,299.50")
        self.assertEqual(utils.format_peso("bad"), f"{config.CURRENCY_SYMBOL}0.00")

    def test_a_date_is_formatted_for_people(self) -> None:
        self.assertEqual(utils.format_date("2026-10-21"), "Oct 21, 2026")
        self.assertEqual(utils.format_date("not a date"), "—")

    def test_a_time_is_formatted_without_a_leading_zero(self) -> None:
        self.assertEqual(utils.format_time(datetime(2026, 10, 21, 14, 0)), "2:00 PM")
        self.assertEqual(utils.format_time(datetime(2026, 10, 21, 9, 30)), "9:30 AM")


class TimeSlotTests(unittest.TestCase):
    """The dropdown of bookable times."""

    def test_the_slots_cover_the_business_day(self) -> None:
        options = utils.time_slot_options()
        self.assertEqual(options[0], "8:00 AM")
        self.assertEqual(options[-1], "5:30 PM")
        self.assertIn("12:00 PM", options)

    def test_a_label_is_joined_back_to_a_date(self) -> None:
        joined = utils.combine_date_time(date(2026, 10, 21), "2:00 PM")
        self.assertEqual(joined, datetime(2026, 10, 21, 14, 0))

    def test_a_label_that_is_not_a_time_is_rejected(self) -> None:
        self.assertIsNone(utils.combine_date_time(date(2026, 10, 21), "half past two"))

    def test_a_timestamp_is_read_from_the_database(self) -> None:
        self.assertEqual(utils.parse_datetime("2026-10-21 14:00:00"),
                         datetime(2026, 10, 21, 14, 0))
        self.assertIsNone(utils.parse_datetime("rubbish"))


if __name__ == "__main__":
    unittest.main()

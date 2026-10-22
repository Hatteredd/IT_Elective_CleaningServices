"""Pure-Python formatting helpers shared by the logic layer and the UI.

This module deliberately has no Tkinter import so that ``cleanhome.services``
can use it without pulling in the UI toolkit.
"""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

from cleanhome import config

DATE_FORMAT = "%b %d, %Y"
TIME_FORMAT = "%I:%M %p"


def to_decimal(value: object, default: str = "0") -> Decimal:
    """Coerce database values to Decimal without raising on bad input."""
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def parse_decimal(value: object) -> Decimal:
    """Coerce user input to Decimal, raising ``ValueError`` when it is not a number."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise ValueError("A boolean is not a number.")
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError) as error:
        raise ValueError("Not a number.") from error


def format_peso(amount: object) -> str:
    """Format a peso amount as ``₱1,299.00``."""
    return f"{config.CURRENCY_SYMBOL}{to_decimal(amount):,.2f}"


def format_discount(promo: dict) -> str:
    """Return ``10% off`` or ``₱200.00 off`` for a promotion dictionary."""
    if promo.get("discount_type") == "percent":
        return f"{to_decimal(promo.get('discount_value')):,.0f}% off"
    return f"{format_peso(promo.get('discount_value'))} off"


def format_date(value: object) -> str:
    """Format a date as ``Oct 21, 2026``."""
    parsed = _as_date(value)
    return parsed.strftime(DATE_FORMAT) if parsed else "—"


def format_time(value: object) -> str:
    """Format a time as ``2:00 PM``."""
    parsed = _as_time(value)
    return parsed.strftime(TIME_FORMAT).lstrip("0") if parsed else "—"


def format_datetime(value: object) -> str:
    """Format a timestamp as ``Oct 21, 2026 · 2:00 PM``."""
    parsed = _as_datetime(value)
    if not parsed:
        return "—"
    return f"{parsed.strftime(DATE_FORMAT)} · {parsed.strftime(TIME_FORMAT).lstrip('0')}"


def business_hours() -> str:
    """Return the opening hours as ``8:00 AM - 6:00 PM``."""
    opening = time(config.BUSINESS_OPEN_HOUR, 0)
    closing = time(config.BUSINESS_CLOSE_HOUR, 0)
    return f"{format_time(opening)} - {format_time(closing)}"


def time_slot_options() -> list[str]:
    """Every bookable start time of the business day, as ``8:00 AM`` labels."""
    options: list[str] = []
    minutes = config.BUSINESS_OPEN_HOUR * config.MINUTES_PER_HOUR
    closing = config.BUSINESS_CLOSE_HOUR * config.MINUTES_PER_HOUR
    while minutes + config.SLOT_INTERVAL_MINUTES <= closing:
        hour, minute = divmod(minutes, config.MINUTES_PER_HOUR)
        meridiem = "AM" if hour < 12 else "PM"
        options.append(f"{hour % 12 or 12}:{minute:02d} {meridiem}")
        minutes += config.SLOT_INTERVAL_MINUTES
    return options


def combine_date_time(day: date, label: str) -> datetime | None:
    """Join a date with a ``8:00 AM`` label into a datetime."""
    for fmt in ("%I:%M %p", "%I:%M%p"):
        try:
            parsed = datetime.strptime(label.strip(), fmt)
        except ValueError:
            continue
        return datetime.combine(day, parsed.time())
    return None


def parse_datetime(value: object) -> datetime | None:
    """Read a timestamp from the database or from user input."""
    return _as_datetime(value)


def _as_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def _as_time(value: object) -> time | None:
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        for fmt in ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
    return None


def _as_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time())
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None

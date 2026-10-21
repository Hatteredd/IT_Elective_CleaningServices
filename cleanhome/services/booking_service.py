"""Booking rules: scheduling, capacity, pricing, and status transitions."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from cleanhome import config, db, utils
from cleanhome.services import (
    ConflictError,
    PermissionDenied,
    ValidationError,
    catalog_service,
)

STATUS_PENDING = "pending"
STATUS_CONFIRMED = "confirmed"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"

# Which status may follow which. Anything not listed here is rejected.
STATUS_FLOW: dict[str, set[str]] = {
    STATUS_PENDING: {STATUS_CONFIRMED, STATUS_CANCELLED},
    STATUS_CONFIRMED: {STATUS_IN_PROGRESS, STATUS_CANCELLED},
    STATUS_IN_PROGRESS: {STATUS_COMPLETED, STATUS_CANCELLED},
    STATUS_COMPLETED: set(),
    STATUS_CANCELLED: set(),
}

STATUS_LABELS = {
    STATUS_PENDING: "Pending",
    STATUS_CONFIRMED: "Confirmed",
    STATUS_IN_PROGRESS: "In Progress",
    STATUS_COMPLETED: "Completed",
    STATUS_CANCELLED: "Cancelled",
}

BOOKING_COLUMNS = (
    "b.id, b.user_id, b.service_id, b.scheduled_at, b.address, b.notes, "
    "b.price_at_booking, b.discount_at_booking, b.status, b.cancel_reason, "
    "b.created_at, b.updated_at, s.name AS service_name, s.duration_mins, "
    "u.full_name AS customer_name, u.email AS customer_email, u.phone AS customer_phone"
)

_JOIN = (
    "FROM bookings b "
    "JOIN services s ON s.id = b.service_id "
    "JOIN users u ON u.id = b.user_id"
)


def _row_to_booking(row) -> dict[str, Any]:
    data = dict(row)
    data["price_at_booking"] = utils.to_decimal(data.get("price_at_booking"))
    data["discount_at_booking"] = utils.to_decimal(data.get("discount_at_booking"))
    data["total_at_booking"] = data["price_at_booking"] - data["discount_at_booking"]
    data["scheduled_at_dt"] = _parse_datetime(data.get("scheduled_at"))
    return data


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return None


def _store_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


# ── Reading ──────────────────────────────────────────────────────────────────
def get_booking(booking_id: int) -> dict[str, Any] | None:
    """Return one booking with its service and customer details."""
    row = db.query_one(f"SELECT {BOOKING_COLUMNS} {_JOIN} WHERE b.id = ?", (booking_id,))
    return _row_to_booking(row) if row else None


def list_bookings_for_user(user_id: int, status: str | None = None) -> list[dict[str, Any]]:
    """Return the bookings belonging to one customer, newest first."""
    if status:
        rows = db.query(
            f"SELECT {BOOKING_COLUMNS} {_JOIN} WHERE b.user_id = ? AND b.status = ? "
            "ORDER BY b.scheduled_at DESC",
            (user_id, status),
        )
    else:
        rows = db.query(
            f"SELECT {BOOKING_COLUMNS} {_JOIN} WHERE b.user_id = ? "
            "ORDER BY b.scheduled_at DESC",
            (user_id,),
        )
    return [_row_to_booking(row) for row in rows]


def list_all_bookings(actor: dict[str, Any] | None, status: str | None = None,
                      search: str = "", date_from: date | None = None,
                      date_to: date | None = None) -> list[dict[str, Any]]:
    """Return every booking, for the administration screens."""
    _require_admin(actor)
    clauses: list[str] = []
    params: list[Any] = []
    if status:
        clauses.append("b.status = ?")
        params.append(status)
    if date_from:
        clauses.append("date(b.scheduled_at) >= date(?)")
        params.append(date_from.isoformat())
    if date_to:
        clauses.append("date(b.scheduled_at) <= date(?)")
        params.append(date_to.isoformat())
    term = (search or "").strip()
    if term:
        like = f"%{term}%"
        clauses.append("(u.full_name LIKE ? OR u.email LIKE ? OR b.address LIKE ?)")
        params.extend([like, like, like])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = db.query(
        f"SELECT {BOOKING_COLUMNS} {_JOIN} {where} ORDER BY b.scheduled_at DESC",
        params,
    )
    return [_row_to_booking(row) for row in rows]


def upcoming_bookings(actor: dict[str, Any] | None, limit: int = 10) -> list[dict[str, Any]]:
    """Return the next scheduled bookings, soonest first."""
    _require_admin(actor)
    rows = db.query(
        f"SELECT {BOOKING_COLUMNS} {_JOIN} "
        "WHERE b.status IN ('pending', 'confirmed', 'in_progress') "
        "AND datetime(b.scheduled_at) >= datetime('now') "
        "ORDER BY b.scheduled_at LIMIT ?",
        (limit,),
    )
    return [_row_to_booking(row) for row in rows]


# ── Scheduling ───────────────────────────────────────────────────────────────
def available_slots(service_id: int, day: date) -> list[datetime]:
    """Return the bookable start times for a service on a given day."""
    service = catalog_service.get_service(service_id)
    if service is None:
        return []
    duration = service["duration_mins"]
    open_time = time(config.BUSINESS_OPEN_HOUR, 0)
    close_time = time(config.BUSINESS_CLOSE_HOUR, 0)
    last_start_dt = datetime.combine(day, close_time) - timedelta(minutes=duration)
    if last_start_dt < datetime.combine(day, open_time):
        return []
    slot = datetime.combine(day, open_time)
    slots: list[datetime] = []
    now = datetime.now()
    earliest = now + timedelta(hours=config.MIN_LEAD_TIME_HOURS)
    while slot <= last_start_dt:
        if slot >= earliest and _capacity_used(slot, slot + timedelta(minutes=duration)) < config.MAX_CONCURRENT_BOOKINGS:
            slots.append(slot)
        slot += timedelta(minutes=config.SLOT_INTERVAL_MINUTES)
    return slots


def _capacity_used(start: datetime, end: datetime, exclude_booking_id: int | None = None) -> int:
    """Count the bookings that overlap a time window."""
    sql = (
        "SELECT b.id FROM bookings b JOIN services s ON s.id = b.service_id "
        "WHERE b.status != 'cancelled' "
        "AND datetime(b.scheduled_at) < ? "
        "AND datetime(b.scheduled_at, '+' || s.duration_mins || ' minutes') > ?"
    )
    params: list[Any] = [_store_datetime(end), _store_datetime(start)]
    if exclude_booking_id is not None:
        sql += " AND b.id != ?"
        params.append(exclude_booking_id)
    return len(db.query(sql, params))


def _validate_slot(service: dict[str, Any], when: datetime,
                   exclude_booking_id: int | None = None) -> None:
    """Raise ValidationError when a booking may not be placed at ``when``."""
    now = datetime.now()
    if when < now:
        raise ValidationError("Booking date cannot be in the past.", "scheduled_at")
    if when < now + timedelta(hours=config.MIN_LEAD_TIME_HOURS):
        raise ValidationError(
            f"Bookings must be made at least {config.MIN_LEAD_TIME_HOURS} hours in advance.",
            "scheduled_at")
    if when.minute % config.SLOT_INTERVAL_MINUTES or when.second:
        raise ValidationError(
            f"Start times must be on a {config.SLOT_INTERVAL_MINUTES}-minute step.", "scheduled_at")
    duration = service["duration_mins"]
    open_dt = datetime.combine(when.date(), time(config.BUSINESS_OPEN_HOUR, 0))
    close_dt = datetime.combine(when.date(), time(config.BUSINESS_CLOSE_HOUR, 0))
    if when < open_dt:
        raise ValidationError(
            f"We start at {config.BUSINESS_OPEN_HOUR}:00 AM, so that time is too early.",
            "scheduled_at")
    if when + timedelta(minutes=duration) > close_dt:
        last_start = close_dt - timedelta(minutes=duration)
        raise ValidationError(
            f"This service takes {duration} minutes, so the last start time is "
            f"{last_start.strftime('%I:%M %p').lstrip('0')}.", "scheduled_at")
    if _capacity_used(when, when + timedelta(minutes=duration), exclude_booking_id) >= config.MAX_CONCURRENT_BOOKINGS:
        raise ValidationError(
            f"That time slot is fully booked ({config.MAX_CONCURRENT_BOOKINGS} cleaners are "
            "already scheduled). Please choose another time.", "scheduled_at")


# ── Creating ─────────────────────────────────────────────────────────────────
def create_booking(actor: dict[str, Any], service_id: int, scheduled_at: datetime,
                   address: str, notes: str = "") -> dict[str, Any]:
    """Create a booking for the signed-in customer."""
    if not actor or actor.get("role") != "customer":
        raise PermissionDenied("Only a customer can book a cleaning.")

    service = catalog_service.get_service(service_id)
    if service is None or not service["is_active"]:
        raise ValidationError("That service is not available.", "service_id")

    clean_address = (address or "").strip()
    if not clean_address:
        raise ValidationError("Service address is required.", "address")
    if len(clean_address) > 255:
        raise ValidationError("Address must be 255 characters or fewer.", "address")

    clean_notes = (notes or "").strip()
    if len(clean_notes) > config.MAX_NOTES_LENGTH:
        raise ValidationError(
            f"Notes must be {config.MAX_NOTES_LENGTH} characters or fewer.", "notes")

    _validate_slot(service, scheduled_at)

    price = service["price"]
    promo = catalog_service.applicable_promotion(service_id, scheduled_at)
    discount = catalog_service.promo_discount(promo, price) if promo else utils.to_decimal(0)

    cursor = db.execute(
        "INSERT INTO bookings (user_id, service_id, scheduled_at, address, notes, "
        "price_at_booking, discount_at_booking, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')",
        (actor["id"], service_id, _store_datetime(scheduled_at), clean_address, clean_notes,
         float(price), float(discount)),
    )
    return get_booking(int(cursor.lastrowid)) or {}


def quote(service_id: int, scheduled_at: datetime) -> dict[str, Any]:
    """Return the price, discount, and total a booking would get."""
    service = catalog_service.get_service(service_id)
    if service is None:
        raise ValidationError("That service is not available.", "service_id")
    price = service["price"]
    promo = catalog_service.applicable_promotion(service_id, scheduled_at)
    discount = catalog_service.promo_discount(promo, price) if promo else utils.to_decimal(0)
    total = price - discount
    if total < 0:
        total = utils.to_decimal(0)
    return {
        "service": service,
        "price": price,
        "promo": promo,
        "discount": discount,
        "total": total,
    }


# ── Changing ─────────────────────────────────────────────────────────────────
def change_status(actor: dict[str, Any], booking_id: int, new_status: str) -> dict[str, Any]:
    """Move a booking to the next status in the lifecycle."""
    _require_admin(actor)
    booking = get_booking(booking_id)
    if booking is None:
        raise ValidationError("That booking no longer exists.")
    if new_status not in STATUS_FLOW:
        raise ValidationError("That is not a valid booking status.", "status")
    current = booking["status"]
    if current == new_status:
        return booking
    if new_status not in STATUS_FLOW[current]:
        raise ConflictError(
            f"A {STATUS_LABELS.get(current, current).lower()} booking cannot be moved to "
            f"{STATUS_LABELS.get(new_status, new_status).lower()}.")
    if new_status == STATUS_CANCELLED:
        raise ValidationError("Use Cancel Booking so a cancellation reason is recorded.",
                              "status")
    db.execute(
        "UPDATE bookings SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (new_status, booking_id),
    )
    return get_booking(booking_id) or {}


def cancel_booking(actor: dict[str, Any], booking_id: int, reason: str = "") -> dict[str, Any]:
    """Cancel a booking. Customers are limited; admins may cancel anything open."""
    if not actor:
        raise PermissionDenied("You must be signed in to cancel a booking.")
    booking = get_booking(booking_id)
    if booking is None:
        raise ValidationError("That booking no longer exists.")

    if actor.get("role") == "customer":
        if int(booking["user_id"]) != int(actor["id"]):
            raise PermissionDenied("You can only cancel your own bookings.")
        if booking["status"] not in (STATUS_PENDING, STATUS_CONFIRMED):
            raise ConflictError(
                f"A {STATUS_LABELS.get(booking['status'], booking['status']).lower()} "
                "booking cannot be cancelled.")
        scheduled_at = booking["scheduled_at_dt"]
        if scheduled_at and scheduled_at < datetime.now() + timedelta(hours=config.CANCEL_CUTOFF_HOURS):
            raise ConflictError(
                f"Bookings can only be cancelled at least {config.CANCEL_CUTOFF_HOURS} hours "
                "before the scheduled time.")
        clean_reason = (reason or "").strip() or "Cancelled by the customer"
    else:
        _require_admin(actor)
        if booking["status"] in (STATUS_COMPLETED, STATUS_CANCELLED):
            raise ConflictError(
                f"A {STATUS_LABELS.get(booking['status'], booking['status']).lower()} "
                "booking cannot be cancelled.")
        clean_reason = (reason or "").strip()
        if not clean_reason:
            raise ValidationError("A cancellation reason is required.", "reason")

    db.execute(
        "UPDATE bookings SET status = 'cancelled', cancel_reason = ?, "
        "updated_at = datetime('now') WHERE id = ?",
        (clean_reason, booking_id),
    )
    return get_booking(booking_id) or {}


def reschedule(actor: dict[str, Any], booking_id: int, new_scheduled_at: datetime) -> dict[str, Any]:
    """Move a booking to a different time."""
    if not actor:
        raise PermissionDenied("You must be signed in to reschedule a booking.")
    booking = get_booking(booking_id)
    if booking is None:
        raise ValidationError("That booking no longer exists.")
    service = catalog_service.get_service(booking["service_id"])
    if service is None:
        raise ValidationError("That service is not available.")

    is_customer = actor.get("role") == "customer"
    if is_customer:
        if int(booking["user_id"]) != int(actor["id"]):
            raise PermissionDenied("You can only reschedule your own bookings.")
        if booking["status"] not in (STATUS_PENDING, STATUS_CONFIRMED):
            raise ConflictError(
                f"A {STATUS_LABELS.get(booking['status'], booking['status']).lower()} "
                "booking cannot be rescheduled.")
        current = booking["scheduled_at_dt"]
        if current and current < datetime.now() + timedelta(hours=config.CANCEL_CUTOFF_HOURS):
            raise ConflictError(
                f"Bookings can only be changed at least {config.CANCEL_CUTOFF_HOURS} hours "
                "before the scheduled time.")
    else:
        _require_admin(actor)
        if booking["status"] in (STATUS_COMPLETED, STATUS_CANCELLED):
            raise ConflictError(
                f"A {STATUS_LABELS.get(booking['status'], booking['status']).lower()} "
                "booking cannot be rescheduled.")

    _validate_slot(service, new_scheduled_at, exclude_booking_id=booking_id)

    new_status = booking["status"]
    if is_customer and new_status == STATUS_CONFIRMED:
        new_status = STATUS_PENDING
    db.execute(
        "UPDATE bookings SET scheduled_at = ?, status = ?, updated_at = datetime('now') "
        "WHERE id = ?",
        (_store_datetime(new_scheduled_at), new_status, booking_id),
    )
    return get_booking(booking_id) or {}


def _require_admin(actor: dict[str, Any] | None) -> None:
    if not actor or actor.get("role") != "admin":
        raise PermissionDenied("Only an administrator can do that.")

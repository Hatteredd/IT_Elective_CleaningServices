"""Service catalogue and promotion rules."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from cleanhome import config, db, utils
from cleanhome.services import ConflictError, ValidationError, require_admin

SERVICE_COLUMNS = "id, name, description, price, duration_mins, is_active, created_at, inclusions"
PROMOTION_COLUMNS = (
    "id, service_id, title, discount_type, discount_value, start_date, end_date, is_active"
)


def _service_row(row) -> dict[str, Any]:
    data = dict(row)
    data["price"] = utils.to_decimal(data.get("price"))
    data["duration_mins"] = int(data.get("duration_mins") or 0)
    data["is_active"] = bool(data.get("is_active"))
    data["inclusions"] = data.get("inclusions") or ""
    return data


def list_services(include_inactive: bool = False) -> list[dict[str, Any]]:
    """Return the service catalogue, newest last."""
    if include_inactive:
        rows = db.query(f"SELECT {SERVICE_COLUMNS} FROM services ORDER BY name")
    else:
        rows = db.query(
            f"SELECT {SERVICE_COLUMNS} FROM services WHERE is_active = 1 ORDER BY name"
        )
    return [_service_row(row) for row in rows]


def get_service(service_id: int) -> dict[str, Any] | None:
    """Return one service, or None."""
    row = db.query_one(f"SELECT {SERVICE_COLUMNS} FROM services WHERE id = ?", (service_id,))
    return _service_row(row) if row else None


def featured_services(limit: int = config.FEATURED_SERVICE_COUNT) -> list[dict[str, Any]]:
    """Return the services shown on the home page."""
    rows = db.query(
        f"SELECT {SERVICE_COLUMNS} FROM services WHERE is_active = 1 "
        "ORDER BY price DESC LIMIT ?",
        (limit,),
    )
    return [_service_row(row) for row in rows]


def create_service(actor: dict[str, Any], name: str, description: str,
                   price: float, duration_mins: int, inclusions: str = "") -> dict[str, Any]:
    """Add a service to the catalogue."""
    require_admin(actor)
    clean = _validate_service_fields(name, description, price, duration_mins)
    inclusions_clean = (inclusions or "").strip()
    if db.query_one("SELECT id FROM services WHERE name = ? COLLATE NOCASE", (clean["name"],)):
        raise ConflictError("A service with that name already exists.")
    cursor = db.execute(
        "INSERT INTO services (name, description, price, duration_mins, inclusions) VALUES (?, ?, ?, ?, ?)",
        (clean["name"], clean["description"], float(clean["price"]), clean["duration_mins"], inclusions_clean),
    )
    return get_service(int(cursor.lastrowid)) or {}


def update_service(actor: dict[str, Any], service_id: int, name: str,
                   description: str, price: float, duration_mins: int, inclusions: str = "") -> dict[str, Any]:
    """Edit an existing service."""
    require_admin(actor)
    clean = _validate_service_fields(name, description, price, duration_mins)
    inclusions_clean = (inclusions or "").strip()
    clash = db.query_one(
        "SELECT id FROM services WHERE name = ? COLLATE NOCASE AND id != ?",
        (clean["name"], service_id),
    )
    if clash:
        raise ConflictError("A service with that name already exists.")
    db.execute(
        "UPDATE services SET name = ?, description = ?, price = ?, duration_mins = ?, inclusions = ? WHERE id = ?",
        (clean["name"], clean["description"], float(clean["price"]), clean["duration_mins"],
         inclusions_clean, service_id),
    )
    return get_service(service_id) or {}


def archive_service(actor: dict[str, Any], service_id: int) -> dict[str, Any]:
    """Deactivate a service. Services with bookings are never deleted."""
    require_admin(actor)
    service = get_service(service_id)
    if service is None:
        raise ValidationError("That service no longer exists.")
    db.execute("UPDATE services SET is_active = 0 WHERE id = ?", (service_id,))
    return get_service(service_id) or {}


def restore_service(actor: dict[str, Any], service_id: int) -> dict[str, Any]:
    """Reactivate an archived service."""
    require_admin(actor)
    db.execute("UPDATE services SET is_active = 1 WHERE id = ?", (service_id,))
    return get_service(service_id) or {}


def _validate_service_fields(name: str, description: str, price: float,
                              duration_mins: int) -> dict[str, Any]:
    clean_name = (name or "").strip()
    if not clean_name:
        raise ValidationError("Service name is required.", "name")
    if len(clean_name) > config.MAX_SERVICE_NAME_LENGTH:
        raise ValidationError(
            f"Service name must be {config.MAX_SERVICE_NAME_LENGTH} characters or fewer.", "name")
    try:
        clean_price = utils.parse_decimal(price)
    except ValueError:
        raise ValidationError("Price must be a number.", "price") from None
    if clean_price <= 0:
        raise ValidationError("Price must be greater than zero.", "price")
    try:
        clean_duration = int(duration_mins)
    except (TypeError, ValueError):
        raise ValidationError("Duration must be a whole number of minutes.", "duration") from None
    if not config.MIN_DURATION_MINUTES <= clean_duration <= config.MAX_DURATION_MINUTES:
        raise ValidationError(
            f"Duration must be between {config.MIN_DURATION_MINUTES} and "
            f"{config.MAX_DURATION_MINUTES} minutes.", "duration")
    return {
        "name": clean_name,
        "description": (description or "").strip(),
        "price": clean_price,
        "duration_mins": clean_duration,
    }


# ── Promotions ───────────────────────────────────────────────────────────────
def list_promotions(active_only: bool = False) -> list[dict[str, Any]]:
    """Return promotions, optionally only the ones that are currently active."""
    if active_only:
        rows = db.query(
            f"SELECT {PROMOTION_COLUMNS} FROM promotions "
            "WHERE is_active = 1 AND datetime('now') BETWEEN datetime(start_date) "
            "AND datetime(end_date) ORDER BY discount_value DESC"
        )
    else:
        rows = db.query(f"SELECT {PROMOTION_COLUMNS} FROM promotions ORDER BY id")
    return [_promotion_row(row) for row in rows]


def get_promotion(promotion_id: int) -> dict[str, Any] | None:
    """Return one promotion, or None."""
    row = db.query_one(f"SELECT {PROMOTION_COLUMNS} FROM promotions WHERE id = ?", (promotion_id,))
    return _promotion_row(row) if row else None


def _promotion_row(row) -> dict[str, Any]:
    data = dict(row)
    data["discount_value"] = utils.to_decimal(data.get("discount_value"))
    data["is_active"] = bool(data.get("is_active"))
    return data


def create_promotion(actor: dict[str, Any], title: str, service_id: int | None,
                     discount_type: str, discount_value: float,
                     start_date: datetime, end_date: datetime) -> dict[str, Any]:
    """Create a promotion."""
    require_admin(actor)
    clean = _validate_promotion_fields(title, discount_type, discount_value, start_date,
                                       end_date, service_id)
    cursor = db.execute(
        "INSERT INTO promotions (service_id, title, discount_type, discount_value, "
        "start_date, end_date, is_active) VALUES (?, ?, ?, ?, ?, ?, 1)",
        (service_id, clean["title"], clean["discount_type"], float(clean["discount_value"]),
         clean["start_date"], clean["end_date"]),
    )
    return get_promotion(int(cursor.lastrowid)) or {}


def update_promotion(actor: dict[str, Any], promotion_id: int, title: str,
                     service_id: int | None, discount_type: str, discount_value: float,
                     start_date: datetime, end_date: datetime) -> dict[str, Any]:
    """Edit a promotion."""
    require_admin(actor)
    clean = _validate_promotion_fields(title, discount_type, discount_value, start_date,
                                       end_date, service_id)
    db.execute(
        "UPDATE promotions SET service_id = ?, title = ?, discount_type = ?, "
        "discount_value = ?, start_date = ?, end_date = ? WHERE id = ?",
        (service_id, clean["title"], clean["discount_type"], float(clean["discount_value"]),
         clean["start_date"], clean["end_date"], promotion_id),
    )
    return get_promotion(promotion_id) or {}


def end_promotion(actor: dict[str, Any], promotion_id: int) -> dict[str, Any]:
    """Deactivate a promotion so it stops applying."""
    require_admin(actor)
    db.execute("UPDATE promotions SET is_active = 0 WHERE id = ?", (promotion_id,))
    return get_promotion(promotion_id) or {}


def _validate_promotion_fields(title: str, discount_type: str, discount_value: float,
                               start_date: datetime, end_date: datetime,
                               service_id: int | None = None) -> dict[str, Any]:
    clean_title = (title or "").strip()
    if not clean_title:
        raise ValidationError("Promotion title is required.", "title")
    kind = (discount_type or "").strip().lower()
    if kind not in ("percent", "fixed"):
        raise ValidationError("Discount type must be percent or fixed.", "discount_type")
    try:
        value = utils.parse_decimal(discount_value)
    except ValueError:
        raise ValidationError("Discount value must be a number.", "discount_value") from None
    if value <= 0:
        raise ValidationError("Discount value must be greater than zero.", "discount_value")
    if kind == "percent" and not (config.MIN_PERCENT_DISCOUNT <= value <= config.MAX_PERCENT_DISCOUNT):
        raise ValidationError(
            f"Percentage must be between {config.MIN_PERCENT_DISCOUNT} and "
            f"{config.MAX_PERCENT_DISCOUNT}.", "discount_value")
    if kind == "fixed" and service_id is not None:
        service = get_service(service_id)
        if service is None:
            raise ValidationError("That service no longer exists.", "service_id")
        if value >= service["price"]:
            raise ValidationError(
                "A fixed discount must be less than the service price of "
                f"{utils.format_peso(service['price'])}.", "discount_value")
    if start_date is None or end_date is None:
        raise ValidationError("Start and end dates are required.", "start_date")
    if end_date < start_date:
        raise ValidationError("End date must be on or after the start date.", "end_date")
    return {
        "title": clean_title,
        "discount_type": kind,
        "discount_value": value,
        "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
    }


def applicable_promotion(service_id: int, when: datetime) -> dict[str, Any] | None:
    """Return the single best promotion for a service on a given date.

    Only one promotion ever applies: the one that gives the customer the
    largest discount on this service. Promotions never stack.
    """
    service = get_service(service_id)
    if service is None:
        return None
    price = service["price"]
    rows = db.query(
        f"SELECT {PROMOTION_COLUMNS} FROM promotions "
        "WHERE is_active = 1 AND datetime(?) BETWEEN datetime(start_date) "
        "AND datetime(end_date) AND (service_id IS NULL OR service_id = ?) "
        "ORDER BY id",
        (when.strftime("%Y-%m-%d %H:%M:%S"), service_id),
    )
    best: dict[str, Any] | None = None
    best_value = Decimal("0")
    for row in rows:
        promo = _promotion_row(row)
        value = promo_discount(promo, price)
        if value > best_value:
            best, best_value = promo, value
    return best


def promo_discount(promo: dict[str, Any], price: Decimal) -> Decimal:
    """Return the discount a promotion gives on a price."""
    if promo["discount_type"] == "percent":
        value = price * promo["discount_value"] / Decimal("100")
    else:
        value = promo["discount_value"]
    if value > price:
        value = price
    return value if value > 0 else Decimal("0")


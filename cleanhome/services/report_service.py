"""Dashboard figures and revenue reporting."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Any

from cleanhome import db, utils
from cleanhome.services import require_admin

REVENUE_EXPRESSION = "(b.price_at_booking - b.discount_at_booking)"


def dashboard_stats(actor: dict[str, Any] | None) -> dict[str, Any]:
    """Return the numbers shown on the administration dashboard."""
    require_admin(actor)
    pending = db.query_one(
        "SELECT COUNT(*) AS n FROM bookings WHERE status = 'pending'")["n"]
    today = db.query_one(
        "SELECT COUNT(*) AS n FROM bookings WHERE date(scheduled_at) = date('now')")["n"]
    completed = db.query_one(
        "SELECT COUNT(*) AS n FROM bookings WHERE status = 'completed' "
        "AND strftime('%Y-%m', scheduled_at) = strftime('%Y-%m', 'now')")["n"]
    revenue = db.query_one(
        f"SELECT COALESCE(SUM({REVENUE_EXPRESSION}), 0) AS total FROM bookings b "
        "WHERE b.status = 'completed' "
        "AND strftime('%Y-%m', b.scheduled_at) = strftime('%Y-%m', 'now')"
    )["total"]
    customers = db.query_one(
        "SELECT COUNT(*) AS n FROM users WHERE role = 'customer' AND is_active = 1")["n"]
    services = db.query_one("SELECT COUNT(*) AS n FROM services WHERE is_active = 1")["n"]
    return {
        "pending_bookings": pending,
        "today_bookings": today,
        "completed_this_month": completed,
        "revenue_this_month": utils.to_decimal(revenue),
        "active_customers": customers,
        "active_services": services,
    }


def revenue_report(actor: dict[str, Any] | None, start: date | None = None,
                   end: date | None = None) -> dict[str, Any]:
    """Return booking totals and revenue for a date range."""
    require_admin(actor)
    clauses: list[str] = []
    params: list[Any] = []
    if start:
        clauses.append("date(b.scheduled_at) >= date(?)")
        params.append(start.isoformat())
    if end:
        clauses.append("date(b.scheduled_at) <= date(?)")
        params.append(end.isoformat())
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    totals = db.query_one(
        f"SELECT COUNT(*) AS total, "
        f"SUM(CASE WHEN b.status = 'completed' THEN 1 ELSE 0 END) AS completed, "
        f"SUM(CASE WHEN b.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled, "
        f"COALESCE(SUM(CASE WHEN b.status = 'completed' THEN {REVENUE_EXPRESSION} END), 0) AS revenue "
        f"FROM bookings b {where}",
        params,
    )
    per_service = db.query(
        f"SELECT s.name AS service_name, COUNT(b.id) AS bookings, "
        f"COALESCE(SUM(CASE WHEN b.status = 'completed' THEN {REVENUE_EXPRESSION} END), 0) AS revenue "
        f"FROM bookings b JOIN services s ON s.id = b.service_id {where} "
        "GROUP BY s.id ORDER BY revenue DESC",
        params,
    )
    return {
        "total_bookings": totals["total"] or 0,
        "completed": totals["completed"] or 0,
        "cancelled": totals["cancelled"] or 0,
        "revenue": utils.to_decimal(totals["revenue"]),
        "revenue_per_service": [
            {
                "service_name": row["service_name"],
                "bookings": row["bookings"],
                "revenue": utils.to_decimal(row["revenue"]),
            }
            for row in per_service
        ],
    }


def export_revenue_csv(actor: dict[str, Any] | None, path: str | Path,
                       start: date | None = None, end: date | None = None) -> Path:
    """Write a revenue report to a CSV file and return its path."""
    require_admin(actor)
    clauses: list[str] = []
    params: list[Any] = []
    if start:
        clauses.append("date(b.scheduled_at) >= date(?)")
        params.append(start.isoformat())
    if end:
        clauses.append("date(b.scheduled_at) <= date(?)")
        params.append(end.isoformat())
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    rows = db.query(
        f"SELECT b.id, b.scheduled_at, u.full_name AS customer_name, s.name AS service_name, "
        f"b.status, b.price_at_booking, b.discount_at_booking, {REVENUE_EXPRESSION} AS total "
        f"FROM bookings b JOIN services s ON s.id = b.service_id "
        f"JOIN users u ON u.id = b.user_id {where} "
        "ORDER BY b.scheduled_at",
        params,
    )
    target = Path(path)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "Booking ID", "Scheduled At", "Customer", "Service", "Status",
            "Price", "Discount", "Total",
        ])
        for row in rows:
            writer.writerow([
                row["id"],
                utils.format_datetime(row["scheduled_at"]),
                row["customer_name"],
                row["service_name"],
                row["status"],
                f"{utils.to_decimal(row['price_at_booking']):.2f}",
                f"{utils.to_decimal(row['discount_at_booking']):.2f}",
                f"{utils.to_decimal(row['total']):.2f}",
            ])
    return target


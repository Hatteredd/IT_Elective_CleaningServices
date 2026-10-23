"""Dashboard figures and revenue reporting."""

from __future__ import annotations

import csv
import calendar
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional, Any, Optional

from cleanhome import config, db, utils
from cleanhome.services import require_admin

REVENUE_EXPRESSION = "(b.price_at_booking - b.discount_at_booking)"


def _month_start(today: date, offset: int) -> date:
    """Return the first day of the month ``offset`` months before ``today``."""
    index = today.month - offset - 1
    return date(today.year + index // 12, index % 12 + 1, 1)


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
    bookings_this_month = db.query_one(
        "SELECT COUNT(*) AS n FROM bookings "
        "WHERE strftime('%Y-%m', scheduled_at) = strftime('%Y-%m', 'now')")["n"]
    status_rows = db.query(
        "SELECT status, COUNT(*) AS n FROM bookings GROUP BY status")
    status_counts = {row["status"]: row["n"] for row in status_rows}

    month_anchor = date.today()
    starts = [_month_start(month_anchor, offset)
              for offset in range(config.DASHBOARD_TREND_MONTHS - 1, -1, -1)]
    monthly_revenue = []
    for index, start in enumerate(starts):
        end = (_month_start(month_anchor, -1) if index == len(starts) - 1
               else starts[index + 1])
        total = db.query_one(
            f"SELECT COALESCE(SUM({REVENUE_EXPRESSION}), 0) AS total FROM bookings b "
            "WHERE b.status = 'completed' "
            "AND date(b.scheduled_at) >= date(?) AND date(b.scheduled_at) < date(?)",
            (start.isoformat(), end.isoformat()),
        )["total"]
        monthly_revenue.append({
            "label": start.strftime("%b"),
            "value": utils.to_decimal(total),
        })

    top_rows = db.query(
        f"SELECT s.name AS service_name, COUNT(b.id) AS bookings, "
        f"COALESCE(SUM(CASE WHEN b.status = 'completed' THEN {REVENUE_EXPRESSION} END), 0) "
        f"AS revenue FROM bookings b JOIN services s ON s.id = b.service_id "
        "GROUP BY s.id ORDER BY revenue DESC, bookings DESC LIMIT ?",
        (config.DASHBOARD_TOP_SERVICES,),
    )
    top_services = [
        {
            "service_name": row["service_name"],
            "bookings": row["bookings"],
            "revenue": utils.to_decimal(row["revenue"]),
        }
        for row in top_rows
    ]

    return {
        "pending_bookings": pending,
        "today_bookings": today,
        "completed_this_month": completed,
        "revenue_this_month": utils.to_decimal(revenue),
        "active_customers": customers,
        "active_services": services,
        "bookings_this_month": bookings_this_month,
        "status_counts": status_counts,
        "monthly_revenue": monthly_revenue,
        "top_services": top_services,
    }


def revenue_report(actor: dict[str, Any] | None, start: Optional[date] = None,
                   end: Optional[date] = None) -> dict[str, Any]:
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
    salaries = salaries_for_period(start, end)
    expenses = expenses_for_period(start, end)
    revenue = utils.to_decimal(totals["revenue"])

    return {
        "total_bookings": totals["total"] or 0,
        "completed": totals["completed"] or 0,
        "cancelled": totals["cancelled"] or 0,
        "revenue": revenue,
        "salaries": salaries,
        "expenses": expenses,
        "profit": revenue - salaries - expenses,
        "revenue_per_service": [
            {
                "service_name": row["service_name"],
                "bookings": row["bookings"],
                "revenue": utils.to_decimal(row["revenue"]),
            }
            for row in per_service
        ],
    }

def salaries_for_period(start: Optional[date] = None, end: Optional[date] = None) -> Decimal:
    """Return the prorated salary cost for a date range."""
    if not start or not end:
        # Default to a month if no range given, or return zero if ambiguous
        return Decimal("0")

    # Fetch active employees
    rows = db.query("SELECT monthly_salary FROM employees WHERE is_active = 1")
    total_monthly = sum(utils.to_decimal(row["monthly_salary"]) for row in rows)
    if total_monthly == 0:
        return Decimal("0")

    total_prorated = Decimal("0")
    current = start
    # Iterate month by month to handle varying month lengths
    while current <= end:
        month_start = current.replace(day=1)
        _, days_in_month = calendar.monthrange(month_start.year, month_start.month)
        month_end = current.replace(day=days_in_month)

        # Intersection of [start, end] and [month_start, month_end]
        overlap_start = max(start, month_start)
        overlap_end = min(end, month_end)
        overlap_days = (overlap_end - overlap_start).days + 1

        if overlap_days > 0:
            daily_rate = total_monthly / Decimal(str(days_in_month))
            total_prorated += daily_rate * Decimal(str(overlap_days))

        # Move to the first of the next month
        if month_start.month == 12:
            current = month_start.replace(year=month_start.year + 1, month=1)
        else:
            current = month_start.replace(month=month_start.month + 1)

    return total_prorated.quantize(Decimal("0.01"))


def expenses_for_period(start: Optional[date] = None, end: Optional[date] = None) -> Decimal:
    """Return the total expenses incurred in a date range."""
    clauses: list[str] = []
    params: list[Any] = []
    if start:
        clauses.append("date(incurred_date) >= date(?)")
        params.append(start.isoformat())
    if end:
        clauses.append("date(incurred_date) <= date(?)")
        params.append(end.isoformat())
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    result = db.query_one(f"SELECT COALESCE(SUM(amount), 0) AS total FROM expenses {where}", params)
    return utils.to_decimal(result["total"])

    


def export_revenue_csv(actor: dict[str, Any] | None, path: str | Path,
                       start: Optional[date] = None, end: Optional[date] = None) -> Path:
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


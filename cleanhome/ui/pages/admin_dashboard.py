"""Admin dashboard."""

from __future__ import annotations

import logging
import tkinter as tk

from cleanhome import config, theme, utils
from cleanhome.services import ServiceError, booking_service, maintenance_service, report_service
from cleanhome.ui import components, templates


class AdminDashboard(templates.AdminTemplate):
    """Key numbers and the next bookings."""

    page_name = "Dashboard"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(
            body, "Dashboard",
            f"Welcome back, {self.session.user.get('full_name', 'Admin')}.")
        header.pack(fill="x")

        stats = report_service.dashboard_stats(self.session.user)
        cards = tk.Frame(body, bg=theme.BG_PAGE)
        cards.pack(fill="x", pady=(theme.SPACE_LG, 0))
        for column in range(theme.DASHBOARD_COLUMNS):
            cards.grid_columnconfigure(column, weight=1)
        items = (
            ("Pending", stats["pending_bookings"], "Awaiting review"),
            ("Today", stats["today_bookings"], "Scheduled for today"),
            ("Completed this month", stats["completed_this_month"], "Jobs finished"),
            ("Revenue this month", utils.format_peso(stats["revenue_this_month"]),
             "Completed jobs"),
            ("Active customers", stats["active_customers"], "Signed up"),
            ("Active services", stats["active_services"], "In catalogue"),
        )
        for index, (title, value, caption) in enumerate(items):
            card = components.StatCard(cards, title, value, caption)
            card.grid(row=0, column=index, sticky="nsew",
                      padx=(0 if index == 0 else theme.SPACE_SM, 0))

        section = templates.section(
            body, "Upcoming bookings",
            f"Next {config.UPCOMING_BOOKINGS_LIMIT} jobs on the calendar.")
        table_frame = tk.Frame(section, bg=theme.BG_PAGE)
        table_frame.pack(fill="x")
        columns = ("id", "customer", "service", "when", "status", "total")
        table = components.DataTable(table_frame, columns,
                                     headings=["ID", "Customer", "Service", "When", "Status", "Total"],
                                     widths=theme.DASHBOARD_TABLE_WIDTHS)
        table.pack(fill="x")
        for booking in booking_service.upcoming_bookings(
                self.session.user, limit=config.UPCOMING_BOOKINGS_LIMIT):
            table.add_row((
                booking["id"],
                booking.get("customer_name", ""),
                booking.get("service_name", ""),
                booking.get("scheduled_at", ""),
                components.booking_service_label(booking["status"]),
                utils.format_peso(booking["total_at_booking"]),
            ))

        safety = templates.section(
            body, "Data safety",
            f"Backups are written to {config.BACKUP_DIR}.")
        components.SecondaryButton(safety, "Back up database now",
                                   command=self._backup).pack(anchor="w")

    def _backup(self) -> None:
        """Copy the live database and tell the administrator where it went."""
        try:
            target = maintenance_service.create_backup(self.session.user)
        except (ServiceError, OSError):
            logging.exception("Database backup failed")
            self.app.flash("The backup could not be created.", "error")
            return
        self.app.flash(f"Backup saved: {target.name}", "success")

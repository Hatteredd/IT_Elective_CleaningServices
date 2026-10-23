"""Admin dashboard."""

from __future__ import annotations

import tkinter as tk

from cleanhome import config, theme, utils
from cleanhome.services import booking_service, report_service
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
            ("Revenue this month", utils.format_peso(stats["revenue_this_month"]),
             f"{stats['completed_this_month']} completed jobs"),
            ("Bookings this month", stats["bookings_this_month"],
             f"{stats['today_bookings']} today · "
             f"{stats['status_counts'].get('confirmed', 0)} confirmed"),
            ("Pending", stats["pending_bookings"], "Awaiting review"),
            ("Active customers", stats["active_customers"],
             f"{stats['active_services']} services available"),
        )
        for index, (title, value, caption) in enumerate(items):
            card = components.StatCard(cards, title, value, caption)
            card.grid(row=0, column=index, sticky="nsew",
                      padx=(0 if index == 0 else theme.SPACE_SM, 0))

        workspace = tk.Frame(body, bg=theme.BG_PAGE)
        workspace.pack(fill="x", pady=(theme.SPACE_LG, 0))
        workspace.grid_columnconfigure(0, weight=2)
        workspace.grid_columnconfigure(1, weight=1)
        workspace.grid_rowconfigure(0, weight=1)

        trend_card = templates.card(workspace)
        trend_card.grid(row=0, column=0, sticky="nsew", padx=(0, theme.SPACE_MD))
        trend_inner = templates.card_body(trend_card)
        components.SubheadingLabel(trend_inner, text="Revenue trend",
                                   surface=True).pack(anchor="w")
        components.CaptionLabel(
            trend_inner,
            text=f"Completed revenue over the last {len(stats['monthly_revenue'])} months.",
            surface=True).pack(anchor="w")
        components.BarChart(
            trend_inner,
            [month["label"] for month in stats["monthly_revenue"]],
            [month["value"] for month in stats["monthly_revenue"]],
        ).pack(fill="both", expand=True, pady=(theme.SPACE_SM, 0))

        ranking_card = templates.card(workspace)
        ranking_card.grid(row=0, column=1, sticky="nsew")
        ranking_inner = templates.card_body(ranking_card)
        components.SubheadingLabel(ranking_inner, text="Top services",
                                   surface=True).pack(anchor="w")
        components.CaptionLabel(ranking_inner, text="All-time completed revenue.",
                                surface=True).pack(anchor="w")
        components.RankingList(
            ranking_inner,
            [
                {"label": service["service_name"],
                 "caption": (f"{service['bookings']} booking"
                             if service["bookings"] == 1
                             else f"{service['bookings']} bookings"),
                 "value": service["revenue"]}
                for service in stats["top_services"]
            ],
            empty_message="No completed bookings yet.",
        ).pack(fill="x", pady=(theme.SPACE_SM, 0))

        section = templates.section(
            body, "Upcoming bookings",
            f"Next {config.UPCOMING_BOOKINGS_LIMIT} jobs on the calendar.")
        upcoming = booking_service.upcoming_bookings(
            self.session.user, limit=config.UPCOMING_BOOKINGS_LIMIT)
        table_frame = tk.Frame(section, bg=theme.BG_PAGE)
        table_frame.pack(fill="x")
        columns = ("id", "customer", "service", "when", "status", "total")
        table = components.DataTable(table_frame, columns,
                                     headings=["ID", "Customer", "Service", "When", "Status", "Total"],
                                     widths=theme.DASHBOARD_TABLE_WIDTHS,
                                     height=max(1, len(upcoming)))
        table.pack(fill="x")
        for booking in upcoming:
            table.add_row((
                booking["id"],
                booking.get("customer_name", ""),
                booking.get("service_name", ""),
                booking.get("scheduled_at", ""),
                components.booking_service_label(booking["status"]),
                utils.format_peso(booking["total_at_booking"]),
            ))

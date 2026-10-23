"""Admin reports."""

from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from tkinter import filedialog

from cleanhome import config, theme, utils
from cleanhome.services import ServiceError, report_service
from cleanhome.ui import components, templates

class AdminReports(templates.AdminTemplate):
    page_name = "Reports"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(body, "Reports",
                                       "Revenue and bookings over a date range.")
        header.pack(fill="x")

        controls = tk.Frame(body, bg=theme.BG_PAGE)
        controls.pack(fill="x", pady=(theme.SPACE_LG, theme.SPACE_MD))
        components.CaptionLabel(controls, text="Start", surface=False).pack(side="left")
        self.start = components.DateCombo(controls, days=config.REPORT_WINDOW_DAYS + 1,
                                           start_offset=-config.REPORT_WINDOW_DAYS)
        self.start.set_date(date.today() - timedelta(days=config.REPORT_WINDOW_DAYS))
        self.start.pack(side="left", padx=(theme.SPACE_XS, theme.SPACE_MD))
        components.CaptionLabel(controls, text="End", surface=False).pack(side="left")
        self.end = components.DateCombo(controls, days=config.REPORT_WINDOW_DAYS + 1,
                                         start_offset=-config.REPORT_WINDOW_DAYS)
        self.end.set_date(date.today())
        self.end.pack(side="left", padx=(theme.SPACE_XS, theme.SPACE_MD))
        components.SecondaryButton(controls, "Run Report",
                                   command=self._run).pack(side="left",
                                                           padx=(theme.SPACE_MD, 0))
        components.SecondaryButton(controls, "Copy Summary",
                                   command=self._copy_summary).pack(side="left",
                                                                    padx=(theme.SPACE_SM, 0))
        components.PrimaryButton(controls, "Export CSV", command=self._export
                                 ).pack(side="left", padx=(theme.SPACE_SM, 0))

        self.summary = tk.Frame(body, bg=theme.BG_PAGE)
        self.summary.pack(fill="x")
        self.chart_frame = tk.Frame(body, bg=theme.BG_PAGE)
        self.chart_frame.pack(fill="x", pady=(theme.SPACE_MD, 0))
        self.table_frame = tk.Frame(body, bg=theme.BG_PAGE)
        self.table_frame.pack(fill="both", expand=True, pady=(theme.SPACE_MD, 0))
        self._run()

    def _dates(self):
        start = self.start.get_date()
        end = self.end.get_date()
        if start is None or end is None:
            self.app.flash("Pick a start and an end date.", "error")
            return None, None
        if end < start:
            self.app.flash("The end date must be on or after the start date.", "error")
            return None, None
        return start, end

    def _run(self) -> None:
        s, e = self._dates()
        if s is None:
            return
        report = report_service.revenue_report(self.session.user, s, e)
        self._report = report
        self._range = (s, e)
        for child in self.summary.winfo_children():
            child.destroy()
        for column in range(theme.REPORT_COLUMNS):
            self.summary.grid_columnconfigure(column, weight=1)
        items = (
            ("Total bookings", report["total_bookings"], ""),
            ("Completed", report["completed"], ""),
            ("Cancelled", report["cancelled"], ""),
            ("Revenue", utils.format_peso(report["revenue"]), "From completed bookings"),
        )
        for index, (title, value, caption) in enumerate(items):
            card = components.StatCard(self.summary, title, value, caption)
            card.grid(row=0, column=index, sticky="nsew",
                      padx=(0 if index == 0 else theme.SPACE_SM, 0))

        for child in self.chart_frame.winfo_children():
            child.destroy()
        top_services = report["revenue_per_service"][:config.REPORT_CHART_SERVICES]
        chart_card = templates.card(self.chart_frame)
        chart_card.pack(fill="x")
        chart_inner = templates.card_body(chart_card)
        components.SubheadingLabel(chart_inner, text="Revenue by service",
                                   surface=True).pack(anchor="w")
        components.CaptionLabel(
            chart_inner,
            text="Completed revenue per service in the selected range.",
            surface=True).pack(anchor="w")
        components.BarChart(
            chart_inner,
            [row["service_name"] for row in top_services],
            [row["revenue"] for row in top_services],
        ).pack(fill="both", expand=True, pady=(theme.SPACE_SM, 0))

        for child in self.table_frame.winfo_children():
            child.destroy()
        components.SubheadingLabel(self.table_frame, text="Service breakdown", surface=False).pack(anchor="w",
                                                            pady=(theme.SPACE_MD, theme.SPACE_SM))
        columns = ("service", "bookings", "revenue")
        table = components.DataTable(self.table_frame, columns,
                                     headings=["Service", "Bookings", "Revenue"],
                                     widths=theme.REPORT_TABLE_WIDTHS)
        table.pack(fill="x")
        for row in report["revenue_per_service"]:
            table.add_row((
                row["service_name"],
                row["bookings"],
                utils.format_peso(row["revenue"]),
            ))

    def _copy_summary(self) -> None:
        report = getattr(self, "_report", None)
        if report is None:
            self.app.flash("Run the report first.", "info")
            return
        start, end = getattr(self, "_range", (None, None))
        lines = [
            f"{config.COMPANY_NAME} revenue report: {start} to {end}",
            f"Total bookings: {report['total_bookings']}",
            f"Completed: {report['completed']}",
            f"Cancelled: {report['cancelled']}",
            f"Revenue: {utils.format_peso(report['revenue'])}",
            "Revenue by service:",
        ]
        for row in report["revenue_per_service"]:
            lines.append(f"  {row['service_name']}: {row['bookings']} bookings, "
                         f"{utils.format_peso(row['revenue'])}")
        self.clipboard_clear()
        self.clipboard_append("\n".join(lines))
        self.update_idletasks()
        self.app.flash("Copied!", "copied")

    def _export(self) -> None:
        s, e = self._dates()
        if s is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"cleanhome-revenue-{s}-{e}.csv")
        if not path:
            return
        try:
            report_service.export_revenue_csv(self.session.user, path, s, e)
        except (ServiceError, OSError) as error:
            self.app.flash(str(error), "error")
            return
        self.app.flash("Report exported.", "success")

"""Admin bookings."""

from __future__ import annotations

import tkinter as tk

from cleanhome import theme, utils
from cleanhome.services import ServiceError, booking_service
from cleanhome.ui import components, templates


class AdminBookings(templates.AdminTemplate):
    page_name = "Bookings"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(body, "Bookings", "View and update every booking.")
        header.pack(fill="x")

        toolbar = tk.Frame(body, bg=theme.BG_PAGE)
        toolbar.pack(fill="x", pady=(theme.SPACE_LG, theme.SPACE_MD))
        self.search = components.SearchBar(toolbar, placeholder="Search customer or address",
                                           on_change=self._refresh)
        self.search.pack(side="left")
        _STATUS_OPTIONS = [("All", None), ("Pending", "pending"), ("Confirmed", "confirmed"),
                           ("In Progress", "in_progress"), ("Completed", "completed"),
                           ("Cancelled", "cancelled")]
        self._status_map = {label: raw for label, raw in _STATUS_OPTIONS}
        self.status = components.Dropdown(
            toolbar, [label for label, _ in _STATUS_OPTIONS],
            width=theme.DROPDOWN_STATUS, on_change=lambda value: self._refresh())
        self.status.pack(side="left", padx=theme.SPACE_SM)

        components.CaptionLabel(toolbar, text="From", surface=False).pack(
            side="left", padx=(theme.SPACE_MD, theme.SPACE_XS))
        self.date_from = components.DateCombo(
            toolbar, days=theme.DATE_SPAN_YEAR, start_offset=-theme.DATE_SPAN_YEAR,
            optional=True)
        self.date_from.bind("<<ComboboxSelected>>", lambda event: self._refresh())
        self.date_from.pack(side="left")
        components.CaptionLabel(toolbar, text="To", surface=False).pack(
            side="left", padx=(theme.SPACE_SM, theme.SPACE_XS))
        self.date_to = components.DateCombo(toolbar, days=theme.DATE_SPAN_YEAR,
                                            optional=True)
        self.date_to.bind("<<ComboboxSelected>>", lambda event: self._refresh())
        self.date_to.pack(side="left")

        self.table_frame = tk.Frame(body, bg=theme.BG_PAGE)
        self.table_frame.pack(fill="both", expand=True)

        actions = tk.Frame(body, bg=theme.BG_PAGE)
        actions.pack(anchor="e", pady=(theme.SPACE_MD, 0))
        components.SecondaryButton(actions, "Mark Confirmed",
                                   command=lambda: self._change("confirmed")
                                   ).pack(side="left", padx=(0, theme.SPACE_SM))
        components.SecondaryButton(actions, "Start Job",
                                   command=lambda: self._change("in_progress")
                                   ).pack(side="left", padx=(0, theme.SPACE_SM))
        components.PrimaryButton(actions, "Mark Completed",
                                 command=lambda: self._change("completed")
                                 ).pack(side="left", padx=(0, theme.SPACE_SM))
        components.DangerButton(actions, "Cancel with Reason",
                                command=self._cancel_with_reason
                                ).pack(side="left")

        self.table = components.DataTable(
            self.table_frame,
            ("id", "customer", "email", "phone", "service", "when", "address", "status",
             "total"),
            headings=["ID", "Customer", "Email", "Phone", "Service", "When", "Address",
                      "Status", "Total"],
            widths=theme.BOOKINGS_TABLE_WIDTHS)
        self.table.pack(fill="both", expand=True)
        self._refresh()

    def _refresh(self) -> None:
        status_label = self.status.get()
        status = self._status_map.get(status_label)
        date_from = self.date_from.get_date()
        date_to = self.date_to.get_date()
        if date_from and date_to and date_from > date_to:
            date_from, date_to = date_to, date_from
        bookings = booking_service.list_all_bookings(
            self.session.user, status=status, search=self.search.get(),
            date_from=date_from, date_to=date_to)
        self.table.clear()
        for booking in bookings:
            self.table.add_row((
                booking["id"],
                booking.get("customer_name", ""),
                booking.get("customer_email", ""),
                booking.get("customer_phone") or "",
                booking.get("service_name", ""),
                booking.get("scheduled_at", ""),
                booking.get("address", ""),
                components.booking_service_label(booking["status"]),
                utils.format_peso(booking["total_at_booking"]),
            ))

    def _change(self, new_status: str) -> None:
        booking_id = self._selected_id()
        if booking_id is None:
            self.app.flash("Select a booking from the table.", "info")
            return
        try:
            booking_service.change_status(self.session.user, booking_id, new_status)
        except ServiceError as error:
            self.app.flash(str(error), "error")
            return
        self.app.flash("Booking updated.", "success")
        self._refresh()

    def _cancel_with_reason(self) -> None:
        booking_id = self._selected_id()
        if booking_id is None:
            self.app.flash("Select a booking from the table.", "info")
            return
        components.CancelDialog(self, require_reason=True,
                                on_submit=lambda reason: self._do_cancel(booking_id,
                                                                          reason))

    def _do_cancel(self, booking_id: int, reason: str) -> None:
        try:
            booking_service.cancel_booking(self.session.user, booking_id, reason)
        except ServiceError as error:
            self.app.flash(str(error), "error")
            return
        self.app.flash("Booking cancelled.", "info")
        self._refresh()

    def _selected_id(self):
        selection = self.table.tree.selection()
        if not selection:
            return None
        values = self.table.tree.item(selection[0], "values")
        try:
            return int(values[0])
        except (ValueError, IndexError):
            return None

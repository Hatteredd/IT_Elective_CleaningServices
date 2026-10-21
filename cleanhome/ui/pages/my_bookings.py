"""My bookings for the signed-in customer."""

from __future__ import annotations

import tkinter as tk

from cleanhome import theme, utils
from cleanhome.services import ServiceError, booking_service, catalog_service
from cleanhome.ui import components, templates
from tkinter import ttk


class MyBookings(templates.PageTemplate):
    """List, cancel, or reschedule the customer's bookings."""

    page_name = "My Bookings"
    required_role = "customer"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(body, "My Bookings",
                                       "Track upcoming, ongoing and past cleanings.")
        header.pack(fill="x")

        tabs = ttk.Notebook(body)
        tabs.pack(fill="both", expand=True, pady=(theme.SPACE_LG, 0))

        self.frames = {}
        for label, status in (("Upcoming", None), ("Pending", "pending"),
                              ("Confirmed", "confirmed"), ("Completed", "completed"),
                              ("Cancelled", "cancelled")):
            frame = ttk.Frame(tabs)
            tabs.add(frame, text=label)
            self.frames[label] = frame
        self._render_all()

    def _render_all(self) -> None:
        user_id = self.session.user["id"]
        for label, status in (("Upcoming", None), ("Pending", "pending"),
                              ("Confirmed", "confirmed"), ("Completed", "completed"),
                              ("Cancelled", "cancelled")):
            if label == "Upcoming":
                bookings = [b for b in booking_service.list_bookings_for_user(user_id)
                            if b["status"] in ("pending", "confirmed", "in_progress")]
            else:
                bookings = booking_service.list_bookings_for_user(user_id, status=status)
            self._render_tab(self.frames[label], bookings, label)

    def _render_tab(self, frame, bookings, label: str) -> None:
        for child in frame.winfo_children():
            child.destroy()
        if not bookings:
            if label == "Upcoming":
                empty = "No bookings yet — browse services to book your first cleaning."
            else:
                empty = f"No {label.lower()} bookings yet."
            components.CaptionLabel(frame, text=empty).pack(
                anchor="w", padx=theme.SPACE_MD, pady=theme.SPACE_MD)
            if label == "Upcoming":
                components.SecondaryButton(frame, "Browse Services",
                                           command=lambda: self.app.go("Services")
                                           ).pack(anchor="w", padx=theme.SPACE_MD)
            return
        for booking in bookings:
            card = templates.card(frame)
            card.pack(fill="x", padx=theme.SPACE_MD, pady=(theme.SPACE_MD, 0))
            inner = templates.card_body(card)
            inner.grid_columnconfigure(0, weight=1)

            top = tk.Frame(inner, bg=theme.BG_SURFACE)
            top.grid(row=0, column=0, sticky="ew")
            components.SubheadingLabel(top, text=booking["service_name"], surface=True).pack(side="left")
            components.Badge(top, components.booking_service_label(booking["status"]),
                             booking["status"]).pack(side="left", padx=theme.SPACE_SM)
            components.PriceLabel(top, text=utils.format_peso(booking["total_at_booking"]), surface=True).pack(side="right")

            info = tk.Frame(inner, bg=theme.BG_SURFACE)
            info.grid(row=1, column=0, sticky="ew", pady=(theme.SPACE_XS, 0))
            components.BodyLabel(info, text=utils.format_datetime(booking.get("scheduled_at")), surface=True).pack(anchor="w")
            components.CaptionLabel(info, text=booking.get("address", ""),
                     wraplength=800, justify="left", surface=True).pack(anchor="w")
            if booking.get("notes"):
                components.CaptionLabel(info, text=f"Notes: {booking['notes']}",
                         wraplength=800, justify="left", surface=True).pack(anchor="w")
            if booking.get("cancel_reason"):
                components.CaptionLabel(info, text=f"Cancellation reason: {booking['cancel_reason']}", wraplength=800,
                         justify="left", surface=True).pack(anchor="w")

            actions = tk.Frame(inner, bg=theme.BG_SURFACE)
            actions.grid(row=2, column=0, sticky="e", pady=(theme.SPACE_MD, 0))
            if booking["status"] in ("pending", "confirmed"):
                components.SecondaryButton(actions, "Reschedule",
                                           command=lambda b=booking: self._reschedule(b)
                                           ).pack(side="left", padx=(0, theme.SPACE_SM))
                components.DangerButton(actions, "Cancel",
                                        command=lambda b=booking: self._cancel(b)
                                        ).pack(side="left")

    def _cancel(self, booking: dict) -> None:
        components.CancelDialog(
            self, require_reason=False,
            on_submit=lambda reason: self._do_cancel(booking["id"], reason))

    def _do_cancel(self, booking_id: int, reason: str) -> None:
        try:
            booking_service.cancel_booking(self.session.user, booking_id, reason)
        except ServiceError as error:
            self.app.flash(str(error), "error")
            return
        self.app.flash("Booking cancelled.", "info")
        self._render_all()

    def _reschedule(self, booking: dict) -> None:
        service = catalog_service.get_service(booking["service_id"])
        if service is None:
            self.app.flash("That service is no longer available.", "error")
            return

        def on_submit(new_when):
            if new_when is None:
                return
            try:
                booking_service.reschedule(self.session.user, booking["id"], new_when)
            except ServiceError as error:
                self.app.flash(str(error), "error")
                return
            self.app.flash("Booking rescheduled.", "success")
            self._render_all()

        components.RescheduleDialog(self, service, on_submit)

"""Book a cleaning."""

from __future__ import annotations

import logging
import sqlite3
import tkinter as tk
from datetime import date, datetime, time

from cleanhome import config, theme, utils
from cleanhome.services import ServiceError, auth_service, booking_service, catalog_service
from cleanhome.ui import components, templates


class Book(templates.PageTemplate):
    """Pick a service, a date and time, address and notes."""

    page_name = "Book"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body
        service_id = kwargs.get("service_id")

        header = templates.page_header(
            body, "Book a Cleaning",
            f"Pick a time between {utils.business_hours()}. We need at least "
            f"{config.MIN_LEAD_TIME_HOURS} hours' notice.")
        header.pack(fill="x")

        form = templates.card(body)
        form.pack(fill="x", pady=(theme.SPACE_LG, 0))
        inner = templates.card_body(form)

        components.CaptionLabel(inner, text="Service", surface=True).pack(anchor="w")
        self.service_var = tk.StringVar()
        services = catalog_service.list_services()
        self.service_map = {service["name"]: service["id"] for service in services}
        self.service_box = components.Dropdown(
            inner, [service["name"] for service in services],
            textvariable=self.service_var, width=theme.DROPDOWN_SERVICE,
            on_change=lambda value: self._update_quote())
        self.service_box.pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_MD))
        if service_id:
            for name, sid in self.service_map.items():
                if sid == service_id:
                    self.service_var.set(name)
                    break

        components.CaptionLabel(inner, text="Date", surface=True).pack(anchor="w")
        self.date_box = components.DateCombo(inner, days=config.BOOKING_WINDOW_DAYS)
        self.date_box.pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_MD))
        self.date_box.bind("<<ComboboxSelected>>", lambda event: (self._load_slots(),
                                                                  self._update_quote()))

        components.CaptionLabel(inner, text="Time", surface=True).pack(anchor="w")
        self.time_var = tk.StringVar()
        self.time_box = components.Dropdown(inner, [], textvariable=self.time_var,
                                            width=theme.DROPDOWN_WIDTH,
                                            on_change=lambda value: self._update_quote())
        self.time_box.pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_MD))
        self.slots: list[datetime] = []

        self.address = components.FormField(inner, "Service address", width=theme.FIELD_WIDTH_WIDE)
        self.address.pack(fill="x")
        if self.session.user and self.session.user.get("address"):
            self.address.set(self.session.user["address"])
        save_var = tk.BooleanVar(value=False)
        self.save_address = components.CheckBox(inner, variable=save_var,
                                                text="Save this address to my profile")
        self.save_address.pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_MD))

        self.notes = components.FormField(inner, "Notes (optional)", width=theme.FIELD_WIDTH_WIDE)
        self.notes.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.notes.bind_return(self._submit)
        self.address.bind_return(self._submit)
        self.address.input.bind("<FocusOut>", lambda event: self._update_quote(), add="+")
        components.bind_tab_order(self.address.input, self.notes.input)

        quote = templates.card(body)
        quote.pack(fill="x", pady=(theme.SPACE_MD, 0))
        quote_inner = templates.card_body(quote)
        components.SubheadingLabel(quote_inner, text="Booking summary", surface=True).pack(anchor="w")
        self.summary_label = components.BodyLabel(quote_inner, text="—", surface=True,
                                                  wraplength=theme.WRAP_SECTION, justify="left")
        self.summary_label.pack(anchor="w", pady=(theme.SPACE_XS, 0))
        components.SubheadingLabel(quote_inner, text="Price breakdown", surface=True).pack(
            anchor="w", pady=(theme.SPACE_MD, 0))
        self.price_label = components.BodyLabel(quote_inner, text="—", surface=True)
        self.price_label.pack(anchor="w", pady=(theme.SPACE_XS, 0))
        self.total_label = components.PriceLabel(quote_inner, text="", surface=True)
        self.total_label.pack(anchor="w", pady=(theme.SPACE_XS, 0))

        self.error_label = components.BodyLabel(body, text="", wraplength=theme.WRAP_FULL, justify="left", surface=False)
        self.error_label.pack(anchor="w", pady=(theme.SPACE_MD, 0))
        self.error_label.pack_forget()

        components.PrimaryButton(body, "Confirm Booking",
                                 command=self._submit).pack(anchor="w",
                                                            pady=(theme.SPACE_LG, 0))

        self._update_quote()

    def _selected_service(self):
        name = self.service_var.get()
        sid = self.service_map.get(name)
        return catalog_service.get_service(sid) if sid else None

    def _selected_date(self) -> date | None:
        return self.date_box.get_date()

    def _load_slots(self) -> None:
        self.time_var.set("")
        self.time_box.set_options([])
        self.slots = []
        service = self._selected_service()
        if not service:
            return
        day = self._selected_date()
        if day is None:
            return
        self.slots = booking_service.available_slots(service["id"], day)
        if not self.slots:
            self.app.flash("No open slots on that date.", "info")
            return
        self.time_box.set_options(
            [slot.strftime("%I:%M %p").lstrip("0") for slot in self.slots])

    def _update_quote(self) -> None:
        service = self._selected_service()
        day = self._selected_date()
        address = self.address.get()
        parts = []
        if service:
            parts.append(service["name"])
        if day:
            parts.append(utils.format_date(day))
        if self.time_var.get():
            parts.append(self.time_var.get())
        if address:
            parts.append(address)
        self.summary_label.configure(text="  •  ".join(parts) if parts else "—")
        if not service:
            self.price_label.configure(text="—")
            self.total_label.configure(text="")
            return
        day = day or date.today()
        when = self._selected_slot() or datetime.combine(
            day, time(config.BUSINESS_OPEN_HOUR, 0))
        q = booking_service.quote(service["id"], when)
        discount = q["discount"]
        total = q["total"]
        if discount > 0 and q["promo"]:
            discount_text = f"Discount ({q['promo']['title']}): -{utils.format_peso(discount)}"
        else:
            discount_text = f"Discount: -{utils.format_peso(0)}"
        self.price_label.configure(
            text=f"Price: {utils.format_peso(q['price'])}  •  {discount_text}")
        self.total_label.configure(text=f"Total: {utils.format_peso(total)}")

    def _selected_slot(self) -> datetime | None:
        choice = self.time_var.get()
        if not choice:
            return None
        for slot in self.slots:
            if slot.strftime("%I:%M %p").lstrip("0") == choice:
                return slot
        return None

    def _show_error(self, message: str) -> None:
        self.error_label.configure(text=message)
        self.error_label.pack(anchor="w", pady=(theme.SPACE_MD, 0))

    def _clear_error(self) -> None:
        self.error_label.configure(text="")
        self.error_label.pack_forget()

    def _submit(self) -> None:
        self._clear_error()
        if not self.session.is_authenticated or self.session.role != "customer":
            self.session.pending = ("Book", {"service_id": self._selected_service()["id"]
                                             if self._selected_service() else None})
            self.app.flash("Sign in to book a cleaning.", "info")
            return self.app.go("Login")
        service = self._selected_service()
        if not service:
            self._show_error("Pick a service first.")
            return
        if not self.time_var.get() or not self.slots:
            self._show_error("Pick a date and an available time.")
            return
        when = self._selected_slot()
        if when is None:
            self._show_error("That time slot is no longer available.")
            return
        try:
            booking = booking_service.create_booking(
                self.session.user, service["id"], when,
                self.address.get(), self.notes.get())
        except ServiceError as error:
            self._show_error(str(error))
            return
        except sqlite3.Error as error:
            logging.exception("Booking could not be saved")
            self._show_error("We could not save that booking. Please try again.")
            return
        if self.save_address.variable.get() and self.session.user.get("address") != self.address.get():
            try:
                updated = auth_service.update_profile(
                    self.session.user,
                    self.session.user.get("full_name", ""),
                    self.session.user.get("phone", ""),
                    self.address.get())
                self.app.session.sign_in(updated)
            except ServiceError:
                logging.exception("Default address could not be saved")
        self.app.flash("Booking requested. We'll review it shortly.", "success")
        self.app.go("MyBookings")

"""Admin promotions."""

from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk

from cleanhome import theme, utils
from cleanhome.services import ServiceError, catalog_service
from cleanhome.ui import components, templates


class AdminPromotions(templates.AdminTemplate):
    page_name = "Promotions"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(body, "Promotions", "Create and end promotions.")
        header.pack(fill="x")

        columns = ("id", "title", "type", "value", "service", "start", "end", "status")
        self.table = components.DataTable(
            body, columns,
            headings=["ID", "Title", "Type", "Value", "Service", "Start", "End", "Status"],
            widths=[50, 160, 80, 80, 160, 130, 130, 80])
        self.table.pack(fill="both", expand=True, pady=(theme.SPACE_LG, 0))
        self._refresh()

        actions = tk.Frame(body, bg=theme.BG_PAGE)
        actions.pack(anchor="e", pady=(theme.SPACE_MD, 0))
        components.PrimaryButton(actions, "Add Promotion", command=self._add).pack(
            side="left", padx=(0, theme.SPACE_SM))
        components.SecondaryButton(actions, "Edit Selected", command=self._edit).pack(
            side="left", padx=(0, theme.SPACE_SM))
        components.DangerButton(actions, "End Promotion", command=self._end).pack(side="left")

    def _refresh(self) -> None:
        self.table.clear()
        services = {s["id"]: s["name"] for s in catalog_service.list_services(include_inactive=True)}
        for index, promo in enumerate(catalog_service.list_promotions(active_only=False)):
            value = f"{promo['discount_value']:,.0f}%" if promo["discount_type"] == "percent" else f"₱{promo['discount_value']:,.0f}"
            self.table.add_row((
                promo["id"],
                promo["title"],
                promo["discount_type"],
                value,
                services.get(promo["service_id"], "All services"),
                promo["start_date"],
                promo["end_date"],
                "Active" if promo["is_active"] else "Ended",
            ), index=index)

    def _selected(self):
        tree = self.table.tree
        selection = tree.selection()
        if not selection:
            self.app.flash("Select a promotion first.", "info")
            return None
        values = tree.item(selection[0], "values")
        pid = int(values[0])
        return catalog_service.get_promotion(pid), pid

    def _add(self) -> None:
        PromoForm(self, self.session.user, None, self._refresh)

    def _edit(self) -> None:
        result = self._selected()
        if result is None:
            return
        promo, pid = result
        PromoForm(self, self.session.user, promo, self._refresh)

    def _end(self) -> None:
        result = self._selected()
        if result is None:
            return
        promo, pid = result
        if not promo["is_active"]:
            self.app.flash("That promotion has already ended.", "info")
            return

        def apply() -> None:
            try:
                catalog_service.end_promotion(self.session.user, pid)
            except ServiceError as error:
                self.app.flash(str(error), "error")
                return
            self.app.flash("Promotion ended.", "info")
            self._refresh()

        components.ConfirmDialog(
            self.winfo_toplevel(), "End promotion",
            f"End “{promo['title']}”? Customers will stop seeing this discount.",
            apply, confirm_label="End Promotion", danger=True)


class PromoForm(tk.Toplevel):
    def __init__(self, parent, actor, promo, on_saved):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title("Add Promotion" if promo is None else "Edit Promotion")
        self.resizable(False, False)
        self.actor = actor
        self.promo = promo
        self.on_saved = on_saved

        frame = tk.Frame(self, bg=theme.BG_SURFACE, padx=theme.SPACE_XL, pady=theme.SPACE_LG)
        frame.pack(fill="both", expand=True)

        self.title_field = components.FormField(frame, "Title")
        self.title_field.pack(fill="x", pady=(0, theme.SPACE_MD))
        components.CaptionLabel(frame, text="Service (leave blank for all)", surface=True).pack(anchor="w")
        services = [("All services", None)]
        for s in catalog_service.list_services(include_inactive=True):
            services.append((s["name"], s["id"]))
        self.service_map = {name: sid for name, sid in services}
        self.service_var = tk.StringVar()
        self.service_box = components.Dropdown(
            frame, [name for name, _ in services],
            textvariable=self.service_var, width=40)
        self.service_box.pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_MD))

        components.CaptionLabel(frame, text="Discount type", surface=True).pack(anchor="w")
        self.type_var = tk.StringVar(value="percent")
        type_row = tk.Frame(frame, bg=theme.BG_SURFACE)
        type_row.pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_MD))
        ttk.Radiobutton(type_row, text="Percent (%)", variable=self.type_var,
                        value="percent").pack(side="left")
        ttk.Radiobutton(type_row, text="Fixed (₱)", variable=self.type_var,
                        value="fixed").pack(side="left", padx=(theme.SPACE_MD, 0))

        self.value = components.FormField(frame, "Discount value")
        self.value.pack(fill="x", pady=(0, theme.SPACE_MD))

        components.CaptionLabel(frame, text="Starts", surface=True).pack(anchor="w")
        start_row = tk.Frame(frame, bg=theme.BG_SURFACE)
        start_row.pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_MD))
        self.start_date = components.DateCombo(start_row, days=730, start_offset=-365)
        self.start_date.set_date(date.today())
        self.start_date.pack(side="left")
        self.start_time = components.Dropdown(start_row, utils.time_slot_options(), width=14)
        self.start_time.pack(side="left", padx=(theme.SPACE_SM, 0))

        components.CaptionLabel(frame, text="Ends", surface=True).pack(anchor="w")
        end_row = tk.Frame(frame, bg=theme.BG_SURFACE)
        end_row.pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_MD))
        self.end_date = components.DateCombo(end_row, days=730, start_offset=-365)
        self.end_date.set_date(date.today() + timedelta(days=30))
        self.end_date.pack(side="left")
        self.end_time = components.Dropdown(end_row, utils.time_slot_options(), width=14)
        self.end_time.pack(side="left", padx=(theme.SPACE_SM, 0))

        if promo:
            self.title_field.set(promo["title"])
            for name, sid in self.service_map.items():
                if sid == promo["service_id"]:
                    self.service_var.set(name)
                    break
            self.type_var.set(promo["discount_type"])
            self.value.set(str(promo["discount_value"]))
            self._select_datetime(self.start_date, self.start_time, promo["start_date"])
            self._select_datetime(self.end_date, self.end_time, promo["end_date"])

        actions = tk.Frame(frame, bg=theme.BG_SURFACE)
        actions.pack(anchor="e", pady=(theme.SPACE_MD, 0))
        components.SecondaryButton(actions, "Cancel", command=self.destroy).pack(
            side="left", padx=(0, theme.SPACE_SM))
        components.PrimaryButton(actions, "Save", command=self._save).pack(side="left")

    def _select_datetime(self, date_box, time_box, value) -> None:
        """Show an existing timestamp in the date and time pickers."""
        parsed = utils.parse_datetime(value)
        if parsed is None:
            return
        date_box.set_date(parsed.date())
        label = parsed.strftime("%I:%M %p").lstrip("0")
        options = utils.time_slot_options()
        if label in options:
            time_box.set(label)

    def _save(self) -> None:
        for field in (self.title_field, self.value):
            if hasattr(field, "clear_error"):
                field.clear_error()
        start = utils.combine_date_time(self.start_date.get_date(), self.start_time.get())
        end = utils.combine_date_time(self.end_date.get_date(), self.end_time.get())
        if start is None or end is None:
            self._flash("Pick a start date and time and an end date and time.")
            return
        try:
            value = float(self.value.get())
        except ValueError:
            self.value.set_error("Enter a number.")
            return
        if end <= start:
            self._flash("The end must be after the start.")
            return
        service_id = self.service_map.get(self.service_var.get())
        try:
            if self.promo is None:
                catalog_service.create_promotion(
                    self.actor, self.title_field.get(), service_id,
                    self.type_var.get(), value, start, end)
            else:
                catalog_service.update_promotion(
                    self.actor, self.promo["id"], self.title_field.get(),
                    service_id, self.type_var.get(), value, start, end)
        except ServiceError as error:
            field_map = {"title": self.title_field, "discount_value": self.value}
            field = field_map.get(error.field or "")
            if field is not None:
                field.set_error(str(error))
            else:
                self._flash(str(error))
            return
        self.on_saved()
        self.destroy()

    def _flash(self, message: str) -> None:
        app = getattr(self.master, "app", None)
        if app is not None:
            app.flash(message, "error")

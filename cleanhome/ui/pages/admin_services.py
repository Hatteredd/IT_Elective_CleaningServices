"""Admin services."""

from __future__ import annotations

import tkinter as tk

from cleanhome import theme, utils
from cleanhome.services import ServiceError, catalog_service
from cleanhome.ui import components, templates


class AdminServices(templates.AdminTemplate):
    page_name = "Services"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(body, "Services", "Add, edit or archive services.")
        header.pack(fill="x")

        columns = ("id", "name", "price", "duration", "status")
        self.table = components.DataTable(body, columns,
                                          headings=["ID", "Name", "Price", "Duration", "Status"],
                                          widths=theme.SERVICES_TABLE_WIDTHS)
        self.table.pack(fill="both", expand=True, pady=(theme.SPACE_LG, 0))
        self._refresh()

        actions = tk.Frame(body, bg=theme.BG_PAGE)
        actions.pack(anchor="e", pady=(theme.SPACE_MD, 0))
        components.PrimaryButton(actions, "Add Service", command=self._add).pack(
            side="left", padx=(0, theme.SPACE_SM))
        components.SecondaryButton(actions, "Edit Selected", command=self._edit).pack(
            side="left", padx=(0, theme.SPACE_SM))
        components.SecondaryButton(actions, "Archive/Restore", command=self._toggle
                                   ).pack(side="left")

        settings = tk.Frame(body, bg=theme.BG_PAGE)
        settings.pack(anchor="w", pady=(theme.SPACE_MD, 0))
        self.active_toggle = components.Toggle(settings, command=self._toggle)
        self.active_toggle.pack(side="left")
        components.CaptionLabel(settings, text="Active in catalogue", surface=False).pack(
            side="left", padx=(theme.SPACE_SM, 0))
        self.table.tree.bind("<<TreeviewSelect>>", lambda event: self._sync_toggle())
        self._sync_toggle()

    def _selected_service(self):
        selection = self.table.tree.selection()
        if not selection:
            return None
        values = self.table.tree.item(selection[0], "values")
        return catalog_service.get_service(int(values[0]))

    def _sync_toggle(self) -> None:
        service = self._selected_service()
        self.active_toggle.variable.set(bool(service and service["is_active"]))

    def _toggle(self) -> None:
        service = self._selected_service()
        if service is None:
            self.active_toggle.variable.set(False)
            self.app.flash("Select a service first.", "info")
            return
        if service["is_active"] == bool(self.active_toggle.variable.get()):
            return
        if service["is_active"]:
            self._archive(service)
        else:
            self._restore(service)

    def _archive(self, service: dict) -> None:
        def apply() -> None:
            try:
                catalog_service.archive_service(self.session.user, service["id"])
            except ServiceError as error:
                self.app.flash(str(error), "error")
                self._sync_toggle()
                return
            self.app.flash("Service archived.", "info")
            self._refresh()

        components.ConfirmDialog(
            self.winfo_toplevel(), "Archive service",
            f"Archive “{service['name']}”? Customers will no longer be able to book it.",
            apply, confirm_label="Archive", danger=True)

    def _restore(self, service: dict) -> None:
        try:
            catalog_service.restore_service(self.session.user, service["id"])
        except ServiceError as error:
            self.app.flash(str(error), "error")
            self._sync_toggle()
            return
        self.app.flash("Service restored.", "success")
        self._refresh()

    def _refresh(self) -> None:
        self.table.clear()
        for index, service in enumerate(catalog_service.list_services(include_inactive=True)):
            self.table.add_row((
                service["id"],
                service["name"],
                utils.format_peso(service["price"]),
                f"{service['duration_mins']} mins",
                "Active" if service["is_active"] else "Archived",
            ), index=index)

    def _selected(self):
        service = self._selected_service()
        if service is None:
            self.app.flash("Select a service first.", "info")
            return None
        return service, service["id"]

    def _add(self) -> None:
        ServiceForm(self, self.session.user, None, self._refresh)

    def _edit(self) -> None:
        result = self._selected()
        if result is None:
            return
        service, sid = result
        ServiceForm(self, self.session.user, service, self._refresh)


class ServiceForm(components.FormDialog):
    """Modal form to add or edit a service."""

    def __init__(self, parent, actor, service, on_saved):
        super().__init__(parent, "Add Service" if service is None else "Edit Service",
                         on_saved)
        self.actor = actor
        self.service = service

        self.name = components.FormField(self.body, "Name")
        self.name.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.description = components.FormField(self.body, "Description")
        self.description.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.inclusions = components.FormField(self.body, "Inclusions")
        self.inclusions.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.price = components.FormField(self.body, "Price (₱)")
        self.price.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.duration = components.FormField(self.body, "Duration (minutes)")
        self.duration.pack(fill="x", pady=(0, theme.SPACE_MD))
        self._fields = {
            "name": self.name,
            "description": self.description,
            "inclusions": self.inclusions,
            "price": self.price,
            "duration_mins": self.duration,
        }

        if service:
            self.name.set(service["name"])
            self.description.set(service["description"] or "")
            self.inclusions.set(service.get("inclusions") or "")
            self.price.set(str(service["price"]))
            self.duration.set(str(service["duration_mins"]))

    def _submit(self) -> None:
        self.clear_form_errors()
        try:
            price = float(self.price.get())
        except ValueError:
            self.price.set_error("Price must be a number.")
            return
        try:
            duration = int(self.duration.get())
        except ValueError:
            self.duration.set_error("Duration must be a whole number of minutes.")
            return
        try:
            if self.service is None:
                catalog_service.create_service(
                    self.actor, self.name.get(), self.description.get(), price, duration,
                    inclusions=self.inclusions.get())
            else:
                catalog_service.update_service(
                    self.actor, self.service["id"], self.name.get(),
                    self.description.get(), price, duration,
                    inclusions=self.inclusions.get())
        except ServiceError as error:
            self.show_field_error(error)
            return
        self.saved()

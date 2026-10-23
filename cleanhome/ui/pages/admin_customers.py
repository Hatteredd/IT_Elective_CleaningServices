"""Admin customers."""

from __future__ import annotations

import tkinter as tk

from cleanhome import theme
from cleanhome.services import ServiceError, auth_service
from cleanhome.ui import components, templates


class AdminCustomers(templates.AdminTemplate):
    page_name = "Customers"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(body, "Customers", "Manage customer accounts.")
        header.pack(fill="x")

        toolbar = tk.Frame(body, bg=theme.BG_PAGE)
        toolbar.pack(fill="x", pady=(theme.SPACE_LG, theme.SPACE_MD))
        self.search = components.SearchBar(toolbar, placeholder="Search customers",
                                           on_change=self._refresh)
        self.search.pack(side="left")

        columns = ("id", "name", "email", "phone", "bookings", "status")
        self.table = components.DataTable(
            body, columns,
            headings=["ID", "Name", "Email", "Phone", "Bookings", "Status"],
            widths=theme.CUSTOMERS_TABLE_WIDTHS)
        self.table.pack(fill="both", expand=True)
        self._refresh()

        actions = tk.Frame(body, bg=theme.BG_PAGE)
        actions.pack(anchor="e", pady=(theme.SPACE_MD, 0))
        components.PrimaryButton(actions, "Add Admin", command=self._add_admin).pack(
            side="left", padx=(0, theme.SPACE_SM))
        components.SecondaryButton(actions, "Toggle Active/Inactive",
                                   command=self._toggle
                                   ).pack(side="left")

    def _refresh(self) -> None:
        self.table.clear()
        for index, customer in enumerate(auth_service.list_customers(self.session.user,
                                                                    self.search.get())):
            self.table.add_row((
                customer["id"],
                customer["full_name"],
                customer["email"],
                customer.get("phone") or "",
                customer.get("booking_count", 0),
                "Active" if customer["is_active"] else "Inactive",
            ), index=index)

    def _toggle(self) -> None:
        tree = self.table.tree
        selection = tree.selection()
        if not selection:
            self.app.flash("Select a customer first.", "info")
            return
        values = tree.item(selection[0], "values")
        cid = int(values[0])
        name = values[1]
        active = values[5] == "Active"
        if active:
            self._confirm_deactivate(cid, name)
        else:
            self._set_active(cid, True, f"Reactivated {name}.")

    def _confirm_deactivate(self, cid: int, name: str) -> None:
        def apply() -> None:
            self._set_active(cid, False, f"Deactivated {name}.")

        components.ConfirmDialog(
            self.winfo_toplevel(), "Deactivate account",
            f"Deactivate {name}? They will no longer be able to sign in.",
            apply, confirm_label="Deactivate", danger=True)

    def _set_active(self, cid: int, active: bool, success: str) -> None:
        try:
            auth_service.set_user_active(self.session.user, cid, active)
        except ServiceError as error:
            self.app.flash(str(error), "error")
            return
        self.app.flash(success, "success")
        self._refresh()

    def _add_admin(self) -> None:
        AddAdminDialog(self, self.session.user, self._refresh)


class AddAdminDialog(components.FormDialog):
    """Create another administrator account."""

    def __init__(self, parent, actor, on_saved):
        super().__init__(parent, "Add Admin", on_saved, save_label="Create Admin")
        self.actor = actor

        self.name = components.FormField(self.body, "Full name", required=True)
        self.name.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.email = components.FormField(self.body, "Email",
                                          placeholder="name@example.com",
                                          required=True)
        self.email.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.password = components.FormField(self.body, "Password", secret=True,
                                             required=True)
        self.password.pack(fill="x", pady=(0, theme.SPACE_MD))
        self._fields = {
            "full_name": self.name,
            "email": self.email,
            "password": self.password,
        }
        components.bind_tab_order(self.name.input, self.email.input, self.password.input)
        self.name.focus_field()

    def _submit(self) -> None:
        self.clear_form_errors()
        try:
            auth_service.create_admin(self.actor, self.name.get(), self.email.get(),
                                      self.password.get())
        except ServiceError as error:
            self.show_field_error(error)
            return
        self.saved()

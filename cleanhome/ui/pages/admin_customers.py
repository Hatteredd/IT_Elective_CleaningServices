"""Admin customers."""

from __future__ import annotations

import tkinter as tk

from cleanhome import theme
from cleanhome.services import ServiceError, ValidationError, auth_service
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
            widths=[50, 160, 200, 140, 90, 90])
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


class AddAdminDialog(tk.Toplevel):
    """Create another administrator account."""

    def __init__(self, parent, actor, on_saved):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title("Add Admin")
        self.resizable(False, False)
        self.actor = actor
        self.on_saved = on_saved

        frame = tk.Frame(self, bg=theme.BG_SURFACE, padx=theme.SPACE_XL, pady=theme.SPACE_LG)
        frame.pack(fill="both", expand=True)

        self.name = components.FormField(frame, "Full name")
        self.name.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.email = components.FormField(frame, "Email", placeholder="name@cleanhome.ph")
        self.email.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.password = components.FormField(frame, "Password", secret=True)
        self.password.pack(fill="x", pady=(0, theme.SPACE_MD))
        self._fields = {
            "full_name": self.name,
            "email": self.email,
            "password": self.password,
        }

        actions = tk.Frame(frame, bg=theme.BG_SURFACE)
        actions.pack(anchor="e", pady=(theme.SPACE_MD, 0))
        components.SecondaryButton(actions, "Cancel", command=self.destroy).pack(
            side="left", padx=(0, theme.SPACE_SM))
        components.PrimaryButton(actions, "Create Admin", command=self._save).pack(side="left")
        self.bind("<Escape>", lambda event: self.destroy())

    def _save(self) -> None:
        for field in (self.name, self.email, self.password):
            field.clear_error()
        try:
            auth_service.create_admin(self.actor, self.name.get(), self.email.get(),
                                      self.password.get())
        except ValidationError as error:
            widget = self._fields.get(error.field or "")
            if widget is not None:
                widget.set_error(error.message)
                return
            self._flash(error.message)
            return
        except ServiceError as error:
            self._flash(str(error))
            return
        self.on_saved()
        self.destroy()

    def _flash(self, message: str) -> None:
        app = getattr(self.master, "app", None)
        if app is not None:
            app.flash(message, "error")

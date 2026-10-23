"""First-run screen: create the very first administrator account."""

from __future__ import annotations

import tkinter as tk

from cleanhome import config, theme
from cleanhome.services import ConflictError, ServiceError, ValidationError, auth_service
from cleanhome.ui import components, templates


class CreateAdmin(templates.FormMixin, templates.AuthTemplate):
    """The setup screen shown once, when no administrator exists yet."""

    page_name = "Create Admin Account"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        card = templates.card(body, padding=theme.SPACE_XL)
        card.pack()
        inner = templates.card_body(card)

        components.HeadingLabel(inner, text=f"Set up {config.COMPANY_NAME}",
                                surface=True).pack(anchor="w")
        components.BodyLabel(
            inner, text="This computer has no administrator yet. Create the first "
                       "account to start managing services, bookings and customers.",
            surface=True, wraplength=theme.WRAP_FORM, justify="left").pack(
            anchor="w", pady=(theme.SPACE_XS, theme.SPACE_LG))

        self.full_name = components.FormField(inner, "Full name")
        self.full_name.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.email = components.FormField(inner, "Email", placeholder="you@example.com")
        self.email.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.phone = components.FormField(inner, "Mobile number (optional)")
        self.phone.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.password = components.FormField(inner, "Password", secret=True)
        self.password.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.confirm = components.FormField(inner, "Confirm password", secret=True)
        self.confirm.pack(fill="x", pady=(0, theme.SPACE_MD))

        self._fields = {
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "password": self.password,
            "confirm_password": self.confirm,
        }
        for field in self._fields.values():
            field.bind_return(self._create)
        self.bind("<Return>", lambda event: self._create())
        components.bind_tab_order(self.full_name.input, self.email.input,
                                  self.phone.input, self.password.input,
                                  self.confirm.input)

        self.error_label = components.BodyLabel(inner, text="", wraplength=theme.WRAP_FORM,
                                                justify="left", surface=True)
        self.error_label.pack_forget()

        components.PrimaryButton(inner, "Create Admin Account",
                                 command=self._create).pack(fill="x",
                                                            pady=(theme.SPACE_MD, 0))
        components.CaptionLabel(
            inner, text="Customers can register from the Sign Up page once setup is done.",
            surface=True).pack(anchor="w", pady=(theme.SPACE_MD, 0))

        self.full_name.focus_field()

    def _create(self) -> None:
        self.clear_form_errors()
        try:
            user = auth_service.create_first_admin(
                self.full_name.get(), self.email.get(), self.phone.get(),
                self.password.input.get(), self.confirm.input.get())
        except ValidationError as error:
            self.show_field_error(error)
            return
        except ConflictError as error:
            self.app.flash(str(error), "error")
            self.app.go("Login")
            return
        except ServiceError as error:
            self.show_form_error(str(error))
            return
        self.app.sign_in(user)
        self.app.flash("Administrator account created.", "success")


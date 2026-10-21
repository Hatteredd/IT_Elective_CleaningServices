"""The sign-up page."""

from __future__ import annotations

import tkinter as tk

from cleanhome import theme
from cleanhome.services import ValidationError, auth_service
from cleanhome.ui import components, templates


class Signup(templates.AuthTemplate):
    """Create a customer account."""

    page_name = "Signup"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        card = templates.card(body, padding=theme.SPACE_XL)
        card.pack()
        inner = templates.card_body(card)

        components.HeadingLabel(inner, text="Create your account", surface=True).pack(anchor="w")
        components.BodyLabel(inner, text="It takes less than a minute to sign up.", surface=True).pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_LG))

        self.full_name = components.FormField(inner, "Full name", placeholder="Juan Dela Cruz")
        self.full_name.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.email = components.FormField(inner, "Email", placeholder="you@example.com")
        self.email.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.phone = components.FormField(inner, "Mobile number (optional)",
                                          placeholder="09171234567")
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
            field.input.bind("<Return>", lambda event: self._create_account())
        self.bind("<Return>", lambda event: self._create_account())

        self.error_label = components.BodyLabel(inner, text="", wraplength=380,
                                    justify="left", surface=True)
        self.error_label.pack_forget()

        components.PrimaryButton(inner, "Create Account", command=self._create_account).pack(
            fill="x", pady=(theme.SPACE_MD, 0))

        footer = tk.Frame(inner, bg=theme.BG_SURFACE)
        footer.pack(anchor="w", pady=(theme.SPACE_LG, 0))
        components.CaptionLabel(footer, text="Already have an account?", surface=True).pack(side="left")
        link = components.CaptionLabel(footer, text="Sign in", cursor="hand2", surface=True)
        link.pack(side="left", padx=(theme.SPACE_XS, 0))
        link.bind("<Button-1>", lambda event: self.app.go("Login"))

    def _create_account(self) -> None:
        self._clear_errors()
        try:
            user = auth_service.register(
                self.full_name.get(),
                self.email.get(),
                self.phone.get(),
                self.password.input.get(),
                self.confirm.input.get(),
            )
        except ValidationError as error:
            field = self._fields.get(error.field or "")
            if field is not None:
                field.set_error(str(error))
            else:
                self._show_error(str(error))
            return
        self.app.sign_in(user)
        self.app.flash("Your account is ready. Welcome to CleanHome!", "success")

    def _show_error(self, message: str) -> None:
        self.error_label.configure(text=message)
        self.error_label.pack(anchor="w", pady=(0, theme.SPACE_SM))

    def _clear_errors(self) -> None:
        self.error_label.pack_forget()
        for field in (self.full_name, self.email, self.phone, self.password, self.confirm):
            field.clear_error()

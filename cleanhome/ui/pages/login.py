"""The sign-in page."""

from __future__ import annotations

import tkinter as tk

from cleanhome import theme
from cleanhome.services import AuthError, ValidationError, auth_service
from cleanhome.ui import components, templates


class Login(templates.AuthTemplate):
    """Sign in with an email address and a password."""

    page_name = "Login"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        card = templates.card(body, padding=theme.SPACE_XL)
        card.pack()
        inner = templates.card_body(card)

        components.HeadingLabel(inner, text="Welcome back", surface=True).pack(anchor="w")
        components.BodyLabel(inner, text="Sign in to book and manage your cleanings.",
                             surface=True).pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_LG))

        self.email = components.FormField(inner, "Email", placeholder="you@example.com")
        self.email.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.password = components.FormField(inner, "Password", secret=True)
        self.password.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.email.bind_return(self._sign_in)
        self.password.bind_return(self._sign_in)
        self.bind("<Return>", lambda event: self._sign_in())
        components.bind_tab_order(self.email.input, self.password.input)

        self.error_label = components.BodyLabel(inner, text="", wraplength=380,
                                                justify="left", surface=True)
        self.error_label.pack_forget()

        components.PrimaryButton(inner, "Log In", command=self._sign_in).pack(
            fill="x", pady=(theme.SPACE_MD, 0))

        footer = tk.Frame(inner, bg=theme.BG_SURFACE)
        footer.pack(anchor="w", pady=(theme.SPACE_LG, 0))
        components.CaptionLabel(footer, text="New to CleanHome?", surface=True).pack(side="left")
        link = components.CaptionLabel(footer, text="Create an account", cursor="hand2",
                                       surface=True)
        link.pack(side="left", padx=(theme.SPACE_XS, 0))
        link.bind("<Button-1>", lambda event: self.app.go("Signup"))

        self.email.focus_field()

    def _sign_in(self) -> None:
        self._clear_errors()
        email = self.email.get()
        password = self.password.input.get()
        try:
            user = auth_service.login(email, password)
        except ValidationError as error:
            if error.field == "email":
                self.email.set_error(str(error))
            elif error.field == "password":
                self.password.set_error(str(error))
            else:
                self._show_error(str(error))
            return
        except AuthError as error:
            self._show_error(str(error))
            return
        self.app.sign_in(user)
        self.app.flash(f"Welcome back, {user['full_name'].split(' ')[0]}.", "success")

    def _show_error(self, message: str) -> None:
        self.error_label.configure(text=message)
        self.error_label.pack(anchor="w", pady=(0, theme.SPACE_SM))

    def _clear_errors(self) -> None:
        self.error_label.pack_forget()
        self.email.clear_error()
        self.password.clear_error()

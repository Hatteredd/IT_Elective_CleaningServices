"""Change the signed-in user's password."""

from __future__ import annotations


from cleanhome import theme
from cleanhome.services import ValidationError, auth_service
from cleanhome.ui import components, templates


class ChangePassword(templates.FormMixin, templates.PageTemplate):
    """Set a new password for the current account."""

    page_name = "Change Password"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(body, "Change Password",
                                       "Choose a new password you have not used before.")
        header.pack(fill="x")

        card = templates.card(body)
        card.pack(fill="x", pady=(theme.SPACE_LG, 0))
        inner = templates.card_body(card)

        self.current = components.FormField(inner, "Current password", secret=True)
        self.current.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.new = components.FormField(inner, "New password", secret=True)
        self.new.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.confirm = components.FormField(inner, "Confirm new password", secret=True)
        self.confirm.pack(fill="x", pady=(0, theme.SPACE_MD))
        self._fields = {
            "current_password": self.current,
            "new_password": self.new,
            "confirm_password": self.confirm,
        }
        for field in self._fields.values():
            field.input.bind("<Return>", lambda event: self._update())
        self.bind("<Return>", lambda event: self._update())

        self.forced = bool(self.session.user and
                           self.session.user.get("must_change_password"))
        if self.forced:
            components.CaptionLabel(
                inner, text="For security, set your own password before continuing.",
                surface=True).pack(anchor="w", pady=(0, theme.SPACE_MD))

        components.PrimaryButton(inner, "Update Password", command=self._update).pack(
            anchor="w", pady=(theme.SPACE_MD, 0))
        if not self.forced:
            components.SecondaryButton(inner, "Back to Profile",
                                       command=lambda: self.app.go("Profile")
                                       ).pack(anchor="w", pady=(theme.SPACE_SM, 0))

    def _update(self) -> None:
        self.clear_form_errors()
        try:
            user = auth_service.change_password(
                self.session.user,
                self.current.input.get(),
                self.new.input.get(),
                self.confirm.input.get(),
            )
        except ValidationError as error:
            self.show_field_error(error)
            return
        self.app.session.sign_in(user)
        self.app.flash("Password updated.", "success")
        self.app.go(self.session.home_page() if self.forced else "Profile")

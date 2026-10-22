"""Customer profile and password change."""

from __future__ import annotations


from cleanhome import theme
from cleanhome.services import ValidationError, auth_service
from cleanhome.ui import components, templates


class Profile(templates.FormMixin, templates.PageTemplate):
    """Edit profile details."""

    page_name = "Profile"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(body, "My Profile", "Update your contact details.")
        header.pack(fill="x")

        components.ProfileCard(body, self.session.user).pack(fill="x",
                                                             pady=(theme.SPACE_LG, 0))

        card = templates.card(body)
        card.pack(fill="x", pady=(theme.SPACE_LG, 0))
        inner = templates.card_body(card)

        self.full_name = components.FormField(inner, "Full name")
        self.full_name.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.email = components.BodyLabel(inner, text=self.session.user.get("email", ""), surface=True)
        self.email.pack(anchor="w", pady=(0, theme.SPACE_MD))
        self.phone = components.FormField(inner, "Mobile number")
        self.phone.pack(fill="x", pady=(0, theme.SPACE_MD))
        self.address = components.FormField(inner, "Default address")
        self.address.pack(fill="x", pady=(0, theme.SPACE_MD))

        self.full_name.set(self.session.user.get("full_name", ""))
        self.phone.set(self.session.user.get("phone", ""))
        self.address.set(self.session.user.get("address", ""))
        self._fields = {
            "full_name": self.full_name,
            "phone": self.phone,
            "address": self.address,
        }
        for field in self._fields.values():
            field.input.bind("<Return>", lambda event: self._save())
        self.bind("<Return>", lambda event: self._save())

        components.PrimaryButton(inner, "Save Changes", command=self._save).pack(
            anchor="w", pady=(theme.SPACE_MD, 0))
        components.SecondaryButton(inner, "Change Password",
                                   command=lambda: self.app.go("ChangePassword")
                                   ).pack(anchor="w", pady=(theme.SPACE_SM, 0))

    def _save(self) -> None:
        self.clear_form_errors()
        try:
            user = auth_service.update_profile(
                self.session.user, self.full_name.get(), self.phone.get(), self.address.get())
        except ValidationError as error:
            self.show_field_error(error)
            return
        self.app.session.sign_in(user)
        self.app.flash("Profile updated.", "success")

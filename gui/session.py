"""Session manager — replaces Flask-Login for the desktop GUI."""


class Session:
    """Holds the currently logged-in user across frames."""

    def __init__(self):
        self.user = None

    @property
    def is_authenticated(self):
        return self.user is not None

    @property
    def role(self):
        return self.user.role if self.user else None

    def login(self, user):
        self.user = user

    def logout(self):
        self.user = None

    def require_customer(self):
        return self.is_authenticated and self.role == "customer"

    def require_admin(self):
        return self.is_authenticated and self.role == "admin"

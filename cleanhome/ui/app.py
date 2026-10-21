"""The application shell: session handling, routing, and the window itself."""

from __future__ import annotations

import logging
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from cleanhome import config, db, theme
from cleanhome.ui import components


class Session:
    """Who is signed in right now.

    The session holds nothing but the current user record. Logging out
    replaces it with ``None`` so no state survives a sign-out.
    """

    def __init__(self) -> None:
        self._user: dict[str, Any] | None = None
        self.pending: tuple[str, dict[str, Any]] | None = None

    @property
    def user(self) -> dict[str, Any] | None:
        return self._user

    @property
    def is_authenticated(self) -> bool:
        return self._user is not None

    @property
    def role(self) -> str:
        return self._user.get("role", "guest") if self._user else "guest"

    def sign_in(self, user: dict[str, Any]) -> None:
        self._user = dict(user)

    def sign_out(self) -> None:
        self._user = None
        self.pending = None

    def home_page(self) -> str:
        """The page this role lands on."""
        return "AdminDashboard" if self.role == "admin" else "Home"


class CleanHomeApp(tk.Tk):
    """The main window and the router in front of every page."""

    def __init__(self) -> None:
        super().__init__()
        self.title(config.COMPANY_NAME)
        self.geometry(f"{config.WINDOW_DEFAULT_WIDTH}x{config.WINDOW_DEFAULT_HEIGHT}")
        self.minsize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
        theme.configure_style(self)

        self.session = Session()
        self.container = ttk.Frame(self, style="TFrame")
        self.container.pack(fill="both", expand=True)
        self.toast = components.Toast(self, self)
        self.current: str = ""

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", lambda event: self.on_close())

    # ── Routing ───────────────────────────────────────────────────────────────
    def first_run_required(self) -> bool:
        """True until the first administrator account has been created."""
        from cleanhome.services import auth_service

        return not auth_service.admin_exists()

    def go(self, page_name: str, **kwargs) -> None:
        """Show a page, applying the role rules first."""
        from cleanhome.ui.pages import PAGES

        entry = PAGES.get(page_name)
        if entry is None:
            logging.error("Unknown page requested: %s", page_name)
            return
        page_class, allowed_roles = entry

        if self.first_run_required() and page_name != "CreateAdmin":
            return self.go("CreateAdmin")
        if page_name == "CreateAdmin" and not self.first_run_required():
            return self.go(self.session.home_page() if self.session.is_authenticated
                           else "Login")

        if allowed_roles:
            if not self.session.is_authenticated:
                self.session.pending = (page_name, kwargs)
                self.flash("Please sign in to continue.", "info")
                return self.go("Login")
            if self.session.role not in allowed_roles:
                self.flash("You do not have access to that page.", "error")
                return self.go(self.session.home_page())
        if page_name == "Login" and self.session.is_authenticated:
            return self.go(self.session.home_page())
        if (self.session.is_authenticated
                and self.session.user.get("must_change_password")
                and page_name != "ChangePassword"):
            self.flash("Set a new password before continuing.", "info")
            return self.go("ChangePassword")

        for child in self.container.winfo_children():
            child.destroy()

        page = page_class(self.container, self)
        page.pack(fill="both", expand=True)
        self.current = page_name
        page.on_show(**kwargs)

    def logout(self) -> None:
        """Sign the current user out and return to the home page."""
        if not self.session.is_authenticated:
            return
        name = self.session.user.get("full_name", "you")
        confirmed = messagebox.askyesno(
            "Log out", f"Log out of CleanHome as {name}?", parent=self)
        if not confirmed:
            return
        self.session.sign_out()
        self.flash("You have been logged out.", "info")
        self.go("Home")

    def flash(self, message: str, kind: str = "info") -> None:
        """Show a transient message."""
        self.toast.show(message, kind)

    def sign_in(self, user: dict[str, Any]) -> None:
        """Store the signed-in user and open the page they were heading to."""
        self.session.sign_in(user)
        pending = self.session.pending
        self.session.pending = None
        if pending:
            page_name, kwargs = pending
            return self.go(page_name, **kwargs)
        return self.go(self.session.home_page())

    # ── Shutdown ──────────────────────────────────────────────────────────────
    def on_close(self) -> None:
        """Close the database cleanly and destroy the window."""
        try:
            db.close_connection()
        except sqlite3.Error:  # pragma: no cover - shutdown must never block exit
            logging.exception("Failed to close the database connection")
        self.destroy()

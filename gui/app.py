"""Main Tkinter application — frame controller for CleanHome PH."""

from contextlib import contextmanager
import tkinter as tk
from tkinter import ttk, messagebox

from app import create_app, db
from app.models import User
from gui.session import Session
from gui import theme


class BaseFrame(ttk.Frame):
    """Base class for all app frames. Provides refresh hook + helpers."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.session = app.session

    def on_show(self, **kwargs):
        """Called every time the frame is raised. Re-renders frame content by default."""
        self.refresh()

    def refresh(self):
        """Force re-render of the frame's content."""
        for child in self.winfo_children():
            child.destroy()
        self.build()

    def build(self):
        """Build the frame's widgets. Override in subclasses."""
        pass

    def flash(self, message, kind="info"):
        """Show a transient status message at the top of the content area."""
        self.app.show_flash(message, kind)

    def go(self, frame_name, **kwargs):
        self.app.show_frame(frame_name, **kwargs)


class MainApp(tk.Tk):
    """Root window managing a stack of frames + sidebar/topbar."""

    def __init__(self):
        super().__init__()
        self.title("CleanHome PH — Home Cleaning Services")
        self.geometry("1180x760")
        self.minsize(980, 600)
        self.configure(bg=theme.BG)

        # Initialise the Flask app purely for db / models context
        self.flask_app = create_app()
        self.db = db
        self.session = Session()

        # Push the Flask app context once and keep it alive for the GUI's
        # lifetime. This keeps a single SQLAlchemy session open so that
        # lazy-loaded relationships remain usable across frames without DetachedInstanceError.
        self._app_ctx = self.flask_app.app_context()
        self._app_ctx.push()

        theme.configure_style(self)

        self._flash_var = tk.StringVar()
        self._flash_after_id = None

        self._build_layout()
        self._register_frames()

        # Start at Home frame
        self.show_frame("Home")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Layout ────────────────────────────────────────────────────────────
    def _build_layout(self):
        # Flash label floats as an overlay at the top, so showing/hiding it
        # never pushes the frame stack down.
        self.flash_label = tk.Label(
            self, textvariable=self._flash_var,
            bg=theme.INFO, fg="#FFFFFF", font=("Segoe UI", 10, "bold"),
            padx=16, pady=10, anchor="w",
        )
        self.flash_label.place(relx=0, rely=0, relwidth=1.0, height=0)
        self.flash_label.place_forget()

        # Container for content frames
        self.container = ttk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

    def _register_frames(self):
        from gui.frames.public import Home, Services, ServiceDetail, About, Contact, Promotions
        from gui.frames.auth import Login, Register, ForgotPassword, ResetPassword
        from gui.frames.customer import (
            CustomerDashboard, BookService, MyBookings, BookingDetail,
            Addresses, CustomerProfile, Notifications,
        )
        from gui.frames.admin import (
            AdminDashboard, AdminBookings, AdminBookingDetail, AdminServices,
            AdminCleaners, AdminPromotions, AdminUsers, AdminSettings,
        )
        for cls in (
            Home, Services, ServiceDetail, About, Contact, Promotions,
            Login, Register, ForgotPassword, ResetPassword,
            CustomerDashboard, BookService, MyBookings, BookingDetail,
            Addresses, CustomerProfile, Notifications,
            AdminDashboard, AdminBookings, AdminBookingDetail, AdminServices,
            AdminCleaners, AdminPromotions, AdminUsers, AdminSettings,
        ):
            frame = cls(self.container, self)
            self.frames[cls.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    # ── Navigation ────────────────────────────────────────────────────────
    def show_frame(self, name, **kwargs):
        frame = self.frames.get(name)
        if frame is None:
            raise ValueError(f"Unknown frame: {name}")
        frame.tkraise()
        frame.on_show(**kwargs)

    def show_flash(self, message, kind="info"):
        colors = {
            "success": theme.SUCCESS,
            "error": theme.DANGER,
            "warning": theme.WARNING,
            "info": theme.INFO,
        }
        self.flash_label.configure(bg=colors.get(kind, theme.INFO))
        self._flash_var.set(message)
        # Show as an overlay at the top of the window (no layout shift)
        self.flash_label.place(relx=0, rely=0, relwidth=1.0, height=44)
        self.flash_label.lift()
        if self._flash_after_id:
            self.after_cancel(self._flash_after_id)
        self._flash_after_id = self.after(3500, self._hide_flash)

    def _hide_flash(self):
        self.flash_label.place_forget()
        self._flash_after_id = None

    def login(self, user):
        self.session.login(user)
        if user.role == "admin":
            self.show_frame("AdminDashboard")
        else:
            self.show_frame("CustomerDashboard")

    def logout(self):
        self.session.logout()
        self.show_frame("Home")
        self.show_flash("You have been logged out.", "info")

    @contextmanager
    def db_session(self):
        """Yield within the persistent app context.

        The Flask app context is pushed once at startup, so the SQLAlchemy
        session stays alive across frames. This wrapper only rolls back on
        exception so a failed query never leaves the session poisoned.
        """
        try:
            yield
        except Exception:
            db.session.rollback()
            raise

    def _on_close(self):
        """Pop the app context and release resources on window close."""
        try:
            db.session.remove()
        except Exception:
            pass
        try:
            self._app_ctx.pop()
        except Exception:
            pass
        self.destroy()


def run():
    app = MainApp()
    app.mainloop()


if __name__ == "__main__":
    run()

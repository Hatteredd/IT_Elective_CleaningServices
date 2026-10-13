"""Authentication frames: Login, Register, Forgot Password."""

import secrets
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone, timedelta

from gui.app import BaseFrame
from gui import theme
from app import db
from app.models import User, CustomerProfile, PasswordResetToken


class _AuthLayout(BaseFrame):
    """Centered card layout shared by auth frames."""

    def _card(self, width=480, height=None):
        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True)

        # Back to Home pill at top-left
        top_bar = ttk.Frame(outer)
        top_bar.pack(fill="x", padx=theme.SPACE_XL, pady=theme.SPACE_MD)
        ttk.Button(top_bar, text="← Back to Home", style="Secondary.TButton",
                   command=lambda: self.go("Home")).pack(side="left")

        card = tk.Frame(outer, bg=theme.SURFACE, highlightbackground=theme.BORDER,
                        highlightthickness=1, bd=0, width=width)
        if height:
            card.config(height=height)
            card.pack_propagate(False)
        card.place(relx=0.5, rely=0.52, anchor="center")
        return card


class Login(_AuthLayout):
    def build(self):
        card = self._card(width=460)
        ttk.Label(card, text="Welcome Back", style="Surface.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(pady=(theme.SPACE_2XL, theme.SPACE_XS))
        ttk.Label(card, text="Log in to your CleanHome PH account",
                  style="Surface.Muted.TLabel", font=("Segoe UI", 10)).pack(pady=(0, theme.SPACE_MD))

        # Quick Demo Account Selectors
        demo_frame = tk.Frame(card, bg="#F1F5F9", highlightbackground=theme.BORDER,
                              highlightthickness=1, padx=14, pady=10)
        demo_frame.pack(fill="x", padx=32, pady=(0, theme.SPACE_MD))
        ttk.Label(demo_frame, text="⚡ Quick 1-Click Demo Login:", background="#F1F5F9",
                  font=("Segoe UI", 8, "bold"), foreground=theme.TEXT_MUTED).pack(anchor="w", pady=(0, theme.SPACE_XS))
        pills_row = tk.Frame(demo_frame, bg="#F1F5F9")
        pills_row.pack(fill="x")

        def _fill_creds(email, pwd):
            self.email.delete(0, tk.END)
            self.email.insert(0, email)
            self.password.delete(0, tk.END)
            self.password.insert(0, pwd)
            self._submit()

        tk.Button(pills_row, text="👑 Admin Demo", relief="groove", bg="#FEF3C7", fg="#92400E",
                  font=("Segoe UI", 9, "bold"), cursor="hand2", padx=12, pady=4,
                  command=lambda: _fill_creds("admin@cleanhome.ph", "Admin123!")).pack(side="left", padx=(0, theme.SPACE_SM))
        tk.Button(pills_row, text="👤 Customer Demo", relief="groove", bg="#CCFBF1", fg="#0F766E",
                  font=("Segoe UI", 9, "bold"), cursor="hand2", padx=12, pady=4,
                  command=lambda: _fill_creds("customer@cleanhome.ph", "Customer123!")).pack(side="left")

        ttk.Label(card, text="Email Address", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=32, pady=(theme.SPACE_SM, theme.SPACE_XS))
        self.email = ttk.Entry(card, width=40)
        self.email.pack(fill="x", padx=32)
        self.email.bind("<Return>", lambda e: self._submit())

        ttk.Label(card, text="Password", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=32, pady=(theme.SPACE_MD, theme.SPACE_XS))
        pw_box = ttk.Frame(card, style="Surface.TFrame")
        pw_box.pack(fill="x", padx=32)
        self.password = ttk.Entry(pw_box, show="\u2022")
        self.password.pack(side="left", fill="x", expand=True)
        self.password.bind("<Return>", lambda e: self._submit())

        self._show_pw = False
        def _toggle_pw():
            self._show_pw = not self._show_pw
            self.password.config(show="" if self._show_pw else "\u2022")
            eye_btn.config(text="Hide" if self._show_pw else "Show")

        eye_btn = tk.Button(pw_box, text="Show", relief="flat", bg=theme.SURFACE,
                            fg=theme.PRIMARY, font=("Segoe UI", 9, "bold"),
                            cursor="hand2", padx=10, pady=2, width=6, anchor="center",
                            activebackground=theme.PRIMARY_LIGHT,
                            command=_toggle_pw)
        eye_btn.pack(side="right", padx=(theme.SPACE_SM, 0))

        ttk.Button(card, text="Log In", command=self._submit).pack(fill="x", padx=32, pady=(theme.SPACE_XL, theme.SPACE_SM))

        bottom = ttk.Frame(card, style="Surface.TFrame")
        bottom.pack(fill="x", padx=32, pady=(0, theme.SPACE_2XL))
        ttk.Button(bottom, text="Forgot password?", style="Secondary.TButton",
                   command=lambda: self.go("ForgotPassword")).pack(side="left")
        ttk.Button(bottom, text="Create account", style="Secondary.TButton",
                   command=lambda: self.go("Register")).pack(side="right")

    def _submit(self):
        email = self.email.get().strip().lower()
        pw = self.password.get()
        if not email or not pw:
            self.flash("Please enter both email and password.", "error")
            return
        with self.app.db_session():
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(pw) and user.is_active:
                self.app.login(user)
                return
        self.flash("Invalid email or password.", "error")


class Register(_AuthLayout):
    def build(self):
        card = self._card(width=480)
        ttk.Label(card, text="Create an Account", style="Surface.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(pady=(theme.SPACE_XL, theme.SPACE_XS))
        ttk.Label(card, text="Join CleanHome PH and book in minutes",
                  style="Surface.Muted.TLabel", font=("Segoe UI", 10)).pack(pady=(0, theme.SPACE_MD))

        self.fields = {}
        for label, key in [("First Name *", "first_name"), ("Last Name *", "last_name"),
                           ("Email Address *", "email"), ("Contact Phone", "phone")]:
            ttk.Label(card, text=label, style="Surface.TLabel",
                      font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=32, pady=(theme.SPACE_XS, 2))
            e = ttk.Entry(card, width=40)
            e.pack(fill="x", padx=32)
            e.bind("<Return>", lambda ev: self._submit())
            self.fields[key] = e

        # Password with eye toggle
        ttk.Label(card, text="Password *", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=32, pady=(theme.SPACE_SM, 2))
        pw_box = ttk.Frame(card, style="Surface.TFrame")
        pw_box.pack(fill="x", padx=32)
        pw_entry = ttk.Entry(pw_box, show="\u2022")
        pw_entry.pack(side="left", fill="x", expand=True)
        pw_entry.bind("<Return>", lambda ev: self._submit())
        self.fields["password"] = pw_entry

        self._show_reg_pw = False
        def _toggle_reg_pw():
            self._show_reg_pw = not self._show_reg_pw
            pw_entry.config(show="" if self._show_reg_pw else "\u2022")
            eye_pw_btn.config(text="Hide" if self._show_reg_pw else "Show")

        eye_pw_btn = tk.Button(pw_box, text="Show", relief="flat", bg=theme.SURFACE,
                               fg=theme.PRIMARY, font=("Segoe UI", 9, "bold"),
                               cursor="hand2", padx=10, pady=2, width=6, anchor="center",
                               activebackground=theme.PRIMARY_LIGHT,
                               command=_toggle_reg_pw)
        eye_pw_btn.pack(side="right", padx=(theme.SPACE_SM, 0))

        # Confirm Password with eye toggle
        ttk.Label(card, text="Confirm Password *", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=32, pady=(theme.SPACE_SM, 2))
        cpw_box = ttk.Frame(card, style="Surface.TFrame")
        cpw_box.pack(fill="x", padx=32)
        cpw_entry = ttk.Entry(cpw_box, show="\u2022")
        cpw_entry.pack(side="left", fill="x", expand=True)
        cpw_entry.bind("<Return>", lambda ev: self._submit())
        self.fields["confirm"] = cpw_entry

        self._show_reg_cpw = False
        def _toggle_reg_cpw():
            self._show_reg_cpw = not self._show_reg_cpw
            cpw_entry.config(show="" if self._show_reg_cpw else "\u2022")
            eye_cpw_btn.config(text="Hide" if self._show_reg_cpw else "Show")

        eye_cpw_btn = tk.Button(cpw_box, text="Show", relief="flat", bg=theme.SURFACE,
                                fg=theme.PRIMARY, font=("Segoe UI", 9, "bold"),
                                cursor="hand2", padx=10, pady=2, width=6, anchor="center",
                                activebackground=theme.PRIMARY_LIGHT,
                                command=_toggle_reg_cpw)
        eye_cpw_btn.pack(side="right", padx=(theme.SPACE_SM, 0))

        ttk.Button(card, text="Create Account", command=self._submit).pack(fill="x", padx=32, pady=(theme.SPACE_LG, theme.SPACE_SM))
        ttk.Button(card, text="Already have an account? Log in", style="Secondary.TButton",
                   command=lambda: self.go("Login")).pack(pady=(0, theme.SPACE_XL))

    def _submit(self):
        d = {k: v.get().strip() for k, v in self.fields.items()}
        if not all([d["first_name"], d["last_name"], d["email"], d["password"]]):
            self.flash("First name, last name, email, and password are required.", "error")
            return
        if d["password"] != d["confirm"]:
            self.flash("Passwords do not match.", "error")
            return
        with self.app.db_session():
            if User.query.filter_by(email=d["email"].lower()).first():
                self.flash("An account with this email already exists.", "error")
                return
            user = User(email=d["email"].lower(), role="customer")
            user.set_password(d["password"])
            profile = CustomerProfile(user=user, first_name=d["first_name"],
                                      last_name=d["last_name"], phone=d["phone"])
            db.session.add_all([user, profile])
            db.session.commit()
        self.flash("Registration successful! Please log in.", "success")
        self.go("Login")


class ForgotPassword(_AuthLayout):
    def build(self):
        card = self._card(width=460)
        ttk.Label(card, text="Reset Password", style="Surface.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(pady=(theme.SPACE_2XL, theme.SPACE_XS))
        ttk.Label(card, text="Enter your email to receive a password reset token",
                  style="Surface.Muted.TLabel", font=("Segoe UI", 10)).pack(pady=(0, theme.SPACE_LG))

        ttk.Label(card, text="Registered Email Address", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=32, pady=(theme.SPACE_SM, theme.SPACE_XS))
        self.email = ttk.Entry(card, width=40)
        self.email.pack(fill="x", padx=32)
        self.email.bind("<Return>", lambda e: self._submit())

        self.token_label = ttk.Label(card, text="", style="Surface.TLabel", wraplength=380, justify="center")
        self.token_label.pack(pady=(theme.SPACE_MD, theme.SPACE_XS), padx=32)

        ttk.Button(card, text="Generate Reset Link", command=self._submit).pack(fill="x", padx=32, pady=(theme.SPACE_LG, theme.SPACE_SM))
        ttk.Button(card, text="Back to Login", style="Secondary.TButton",
                   command=lambda: self.go("Login")).pack(pady=(0, theme.SPACE_2XL))

    def _submit(self):
        email = self.email.get().strip().lower()
        if not email:
            self.flash("Please enter your email.", "error")
            return
        token_value = None
        with self.app.db_session():
            user = User.query.filter_by(email=email).first()
            if user:
                PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({"used": True})
                token_value = secrets.token_urlsafe(32)
                token = PasswordResetToken(user_id=user.id, token=token_value,
                                           expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
                db.session.add(token)
                db.session.commit()
        if token_value:
            self.token_label.configure(text=f"🔑 Reset Token Generated:\n{token_value}", foreground=theme.SUCCESS)
            self.flash("Password reset token generated successfully.", "success")
            # Show direct action button to proceed to reset password
            if not hasattr(self, '_btn_proceed'):
                self._btn_proceed = ttk.Button(
                    self.token_label.master,
                    text="Proceed to Set New Password →",
                    command=lambda: self.go("ResetPassword", token=token_value)
                )
                self._btn_proceed.pack(fill="x", padx=32, pady=(0, theme.SPACE_MD))
        else:
            self.token_label.configure(text="")
            self.flash("If that email is registered you will receive a reset link shortly.", "info")


class ResetPassword(_AuthLayout):
    """Allows customer or admin to set a new password using a reset token."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.prefill_token = ""

    def on_show(self, token="", **kwargs):
        self.prefill_token = token
        self.refresh()

    def build(self):
        card = self._card(width=460)
        ttk.Label(card, text="Set New Password", style="Surface.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(pady=(theme.SPACE_2XL, theme.SPACE_XS))
        ttk.Label(card, text="Enter your reset token and choose a new password",
                  style="Surface.Muted.TLabel", font=("Segoe UI", 10)).pack(pady=(0, theme.SPACE_LG))

        ttk.Label(card, text="Reset Token *", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=32, pady=(theme.SPACE_SM, theme.SPACE_XS))
        self.token_entry = ttk.Entry(card, width=40)
        self.token_entry.pack(fill="x", padx=32)
        if self.prefill_token:
            self.token_entry.insert(0, self.prefill_token)

        ttk.Label(card, text="New Password * (min. 8 characters)", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=32, pady=(theme.SPACE_MD, theme.SPACE_XS))
        self.new_pwd = ttk.Entry(card, width=40, show="•")
        self.new_pwd.pack(fill="x", padx=32)

        ttk.Label(card, text="Confirm New Password *", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=32, pady=(theme.SPACE_MD, theme.SPACE_XS))
        self.confirm_pwd = ttk.Entry(card, width=40, show="•")
        self.confirm_pwd.pack(fill="x", padx=32)
        self.confirm_pwd.bind("<Return>", lambda e: self._submit())

        ttk.Button(card, text="Update Password", command=self._submit).pack(fill="x", padx=32, pady=(theme.SPACE_LG, theme.SPACE_SM))
        ttk.Button(card, text="Back to Login", style="Secondary.TButton",
                   command=lambda: self.go("Login")).pack(pady=(0, theme.SPACE_2XL))

    def _submit(self):
        token_str = self.token_entry.get().strip()
        pwd = self.new_pwd.get().strip()
        confirm = self.confirm_pwd.get().strip()

        if not token_str or not pwd or not confirm:
            self.flash("All fields are required.", "error")
            return
        if len(pwd) < 8:
            self.flash("Password must be at least 8 characters long.", "error")
            return
        if pwd != confirm:
            self.flash("Passwords do not match.", "error")
            return

        with self.app.db_session():
            record = PasswordResetToken.query.filter_by(token=token_str, used=False).first()
            now = datetime.now(timezone.utc)
            if not record or record.expires_at.replace(tzinfo=timezone.utc) < now:
                self.flash("Reset token is invalid or has expired.", "error")
                return

            record.user.set_password(pwd)
            record.used = True
            db.session.commit()

        self.flash("Password updated successfully! Please log in with your new password.", "success")
        self.go("Login")

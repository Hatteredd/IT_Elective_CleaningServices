"""Customer frames: Dashboard, Book, Bookings, Booking Detail, Addresses, Profile, Notifications."""

import json
import secrets
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal

from gui.app import BaseFrame
from gui import theme
from gui.theme import ScrollableFrame, make_treeview_with_scrollbar
from app import db
from app.models import (
    User, CustomerProfile as CustomerProfileModel, Address, Service, AddOn, Booking, BookingItem,
    Promotion, PromotionRedemption, Review, Payment, Notification,
)


def _customer_sidebar(parent, app, active):
    sb = tk.Frame(parent, bg=theme.SIDEBAR, width=224)
    sb.pack(side="left", fill="y")
    sb.pack_propagate(False)

    # App Brand Header
    brand_box = tk.Frame(sb, bg=theme.SIDEBAR)
    brand_box.pack(fill="x", padx=16, pady=(20, 14))
    tk.Label(brand_box, text="✨ CleanHome PH", bg=theme.SIDEBAR, fg="#FFFFFF",
             font=("Segoe UI", 15, "bold")).pack(anchor="w")

    # User Profile Badge Box
    profile = app.session.user.customer_profile if app.session.user else None
    first = profile.first_name if profile else "Customer"
    last = profile.last_name if profile else "Account"
    full_name = f"{first} {last}"
    initials = f"{first[0] if first else ''}{last[0] if last else ''}".upper() or "CH"

    u_box = tk.Frame(sb, bg="#1E293B", padx=12, pady=10)
    u_box.pack(fill="x", padx=12, pady=(0, 16))

    u_top = tk.Frame(u_box, bg="#1E293B")
    u_top.pack(fill="x")
    avatar = tk.Label(u_top, text=initials, bg=theme.PRIMARY, fg="#FFFFFF",
                      font=("Segoe UI", 10, "bold"), width=3, pady=2)
    avatar.pack(side="left")

    u_info = tk.Frame(u_top, bg="#1E293B")
    u_info.pack(side="left", padx=(10, 0), fill="x", expand=True)
    tk.Label(u_info, text=full_name, bg="#1E293B", fg="#FFFFFF",
             font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
    tk.Label(u_info, text="● Verified Customer", bg="#1E293B", fg="#2DD4BF",
             font=("Segoe UI", 8), anchor="w").pack(fill="x")

    # Menu Label
    tk.Label(sb, text="CUSTOMER PORTAL", bg=theme.SIDEBAR, fg="#64748B",
             font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(0, 6))

    items = [
        ("Dashboard", "CustomerDashboard", "📊"),
        ("Book a Service", "BookService", "📅"),
        ("My Bookings", "MyBookings", "📋"),
        ("Addresses", "Addresses", "📍"),
        ("Notifications", "Notifications", "🔔"),
        ("Profile", "CustomerProfile", "👤"),
    ]
    for label, target, icon in items:
        is_active = (label == active)
        style = "Sidebar.Active.TButton" if is_active else "Sidebar.TButton"
        ttk.Button(sb, text=f"{icon}  {label}", style=style,
                   command=lambda t=target: app.show_frame(t)).pack(fill="x", padx=10, pady=2)

    # Bottom Actions Frame
    sb_bottom = tk.Frame(sb, bg=theme.SIDEBAR)
    sb_bottom.pack(side="bottom", fill="x", padx=10, pady=(0, 14))

    sep = tk.Frame(sb_bottom, bg="#1E293B", height=1)
    sep.pack(fill="x", pady=(0, 10))

    ttk.Button(sb_bottom, text="🏠 Public Home", style="Sidebar.TButton",
               command=lambda: app.show_frame("Home")).pack(fill="x", pady=2)
    ttk.Button(sb_bottom, text="🚪 Logout", style="Sidebar.TButton",
               command=app.logout).pack(fill="x", pady=(2, 8))
    tk.Label(sb_bottom, text="CleanHome Desktop v2.4", bg=theme.SIDEBAR, fg="#475569",
             font=("Segoe UI", 8)).pack()


class _CustomerFrame(BaseFrame):
    def _layout(self, active):
        for child in self.winfo_children():
            child.destroy()
        _customer_sidebar(self, self.app, active)
        self.scroll = ScrollableFrame(self)
        self.scroll.pack(side="left", fill="both", expand=True)
        self.content = self.scroll.inner


class CustomerDashboard(_CustomerFrame):
    def build(self):
        pass

    def on_show(self, **kwargs):
        self._layout("Dashboard")
        if not self.session.require_customer():
            self.flash("Please log in as a customer.", "error")
            self.go("Login")
            return
        profile = self.session.user.customer_profile
        with self.app.db_session():
            profile_obj = CustomerProfileModel.query.get(profile.id)
            bookings = (Booking.query.filter_by(customer_id=profile.id)
                        .order_by(Booking.created_at.desc()).limit(6).all())
            booking_count = Booking.query.filter_by(customer_id=profile.id).count()
            completed = Booking.query.filter_by(customer_id=profile.id, status="completed").count()
            unpaid = Booking.query.filter_by(customer_id=profile.id, payment_status="unpaid").count()

        top = ttk.Frame(self.content)
        top.pack(fill="x", padx=24, pady=(24, 12))
        top_left = ttk.Frame(top)
        top_left.pack(side="left")
        ttk.Label(top_left, text=f"Welcome back, {profile_obj.first_name}! 👋",
                  style="Title.TLabel", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(top_left, text="Manage your bookings, schedules, and profile settings in real-time.",
                  style="Muted.TLabel", font=("Segoe UI", 9)).pack(anchor="w")

        ttk.Button(top, text="＋ Book a Service",
                   command=lambda: self.go("BookService")).pack(side="right")

        # Stats Cards
        stats = ttk.Frame(self.content)
        stats.pack(fill="x", padx=24, pady=8)
        sc1 = theme.make_stat_card(stats, "Total Bookings", booking_count,
                                   subtitle="Lifetime reservations", icon="📋",
                                   icon_bg="#F0FDFA", icon_fg=theme.PRIMARY)
        sc1.grid(row=0, column=0, padx=6, sticky="nsew")

        sc2 = theme.make_stat_card(stats, "Completed Cleanings", completed,
                                   subtitle="Sparkling clean spaces", icon="✅",
                                   icon_bg="#F0FDF4", icon_fg=theme.SUCCESS)
        sc2.grid(row=0, column=1, padx=6, sticky="nsew")

        unpaid_text = "All accounts clear" if unpaid == 0 else f"{unpaid} pending payment"
        sc3 = theme.make_stat_card(stats, "Action Needed", unpaid,
                                   subtitle=unpaid_text, icon="⚠️",
                                   icon_bg="#FFFBEB", icon_fg=theme.WARNING)
        sc3.grid(row=0, column=2, padx=6, sticky="nsew")

        for col in range(3):
            stats.grid_columnconfigure(col, weight=1)

        # Quick Actions Strip
        qa_frame = ttk.Frame(self.content)
        qa_frame.pack(fill="x", padx=24, pady=(12, 16))
        for (q_label, q_target, q_style) in [
            ("📅 Schedule Cleaning", "BookService", "Secondary.TButton"),
            ("📍 Saved Addresses", "Addresses", "Secondary.TButton"),
            ("👤 Account Profile", "CustomerProfile", "Secondary.TButton"),
        ]:
            ttk.Button(qa_frame, text=q_label, style=q_style,
                       command=lambda t=q_target: self.go(t)).pack(side="left", padx=(0, theme.SPACE_SM))

        # Recent Bookings Table
        sec = ttk.Frame(self.content)
        sec.pack(fill="x", padx=24, pady=(8, 8))
        sec_left = ttk.Frame(sec)
        sec_left.pack(side="left")
        ttk.Label(sec_left, text="Recent Bookings", style="Heading.TLabel",
                  font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Label(sec_left, text=f"  ({booking_count} total)", style="Muted.TLabel",
                  font=("Segoe UI", 9)).pack(side="left")
        ttk.Button(sec, text="View All Bookings →", style="Secondary.TButton",
                   command=lambda: self.go("MyBookings")).pack(side="right")

        if not bookings:
            empty_card = theme.make_card(self.content)
            empty_card.pack(fill="x", padx=20, pady=8)
            inner = theme.make_inner(empty_card)
            inner.pack(fill="x", padx=20, pady=24)
            ttk.Label(inner, text="No bookings yet. Let's get your home cleaned!",
                      style="Surface.Muted.TLabel", font=("Segoe UI", 11)).pack(anchor="center", pady=(0, 12))
            ttk.Button(inner, text="Book Your First Service",
                       command=lambda: self.go("BookService")).pack(anchor="center")
        else:
            cols = ("id", "service", "date", "status", "payment", "total")
            container, tree = make_treeview_with_scrollbar(
                self.content, columns=cols,
                headings=["ID", "Service", "Scheduled Date & Time", "Status", "Payment", "Total"],
                widths=[50, 200, 180, 110, 100, 100], height=6
            )
            for i, b in enumerate(bookings):
                svc_name = b.items[0].service_name if b.items else "—"
                tag = "even" if i % 2 == 0 else "odd"
                tree.insert("", "end", values=(b.id, svc_name,
                                               f"{b.scheduled_date} {b.scheduled_time.strftime('%I:%M %p')}",
                                               b.status.upper(), b.payment_status.upper(),
                                               f"₱{b.total_amount:,.2f}"), tags=(tag,))
            container.pack(fill="x", padx=20, pady=4)
            tree.bind("<Double-1>", lambda e: self._open(tree))

    def _open(self, tree):
        sel = tree.selection()
        if sel:
            bid = tree.item(sel[0])["values"][0]
            self.go("BookingDetail", booking_id=int(bid))


class BookService(_CustomerFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.prefill_service_id = None

    def build(self):
        pass

    def on_show(self, service_id=None, **kwargs):
        self._layout("Book a Service")
        if not self.session.require_customer():
            self.flash("Please log in as a customer.", "error")
            self.go("Login")
            return
        self.prefill_service_id = service_id
        self._build_form()

    def _build_form(self):
        profile = self.session.user.customer_profile
        with self.app.db_session():
            addresses = Address.query.filter_by(customer_id=profile.id).all()
            services = Service.query.filter_by(is_active=True, is_archived=False).all()

        ttk.Label(self.content, text="Book a Cleaning Service", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=20, pady=(20, 8))

        if not addresses:
            warn_card = theme.make_card(self.content)
            warn_card.pack(fill="x", padx=20, pady=12)
            inner = theme.make_inner(warn_card)
            inner.pack(fill="x", padx=24, pady=20)
            ttk.Label(inner, text="📍 Address Required", style="Surface.TLabel",
                      font=("Segoe UI", 14, "bold"), foreground=theme.DANGER).pack(anchor="w", pady=(0, 6))
            ttk.Label(inner, text="Please save at least one service address before making a booking.",
                      style="Surface.Muted.TLabel").pack(anchor="w", pady=(0, 14))
            ttk.Button(inner, text="＋ Add Address Now",
                       command=lambda: self.go("Addresses")).pack(anchor="w")
            return

        form_card = theme.make_card(self.content)
        form_card.pack(fill="both", expand=True, padx=20, pady=8)
        body = theme.make_inner(form_card)
        body.pack(fill="both", expand=True, padx=24, pady=20)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        # Service selection
        ttk.Label(body, text="Select Cleaning Service *", style="Surface.TLabel",
                  font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
        svc_choices = []
        for s in services:
            price = s.discounted_price if (s.discounted_price and s.discounted_price < s.base_price) else s.base_price
            svc_choices.append((s.id, f"{s.name}  —  ₱{price:,.0f}"))
        self.svc_combo = ttk.Combobox(body, values=[c[1] for c in svc_choices], state="readonly")
        self.svc_combo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        self._svc_map = {c[1]: c[0] for c in svc_choices}
        self._id_to_svc = {s.id: s for s in services}

        if self.prefill_service_id and self.prefill_service_id in self._id_to_svc:
            s = self._id_to_svc[self.prefill_service_id]
            price = s.discounted_price if (s.discounted_price and s.discounted_price < s.base_price) else s.base_price
            self.svc_combo.set(f"{s.name}  —  ₱{price:,.0f}")
        elif svc_choices:
            self.svc_combo.current(0)

        self.svc_combo.bind("<<ComboboxSelected>>", lambda e: self._update_addons())

        # Date & Time (side by side)
        ttk.Label(body, text="Preferred Date (YYYY-MM-DD) *", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 2))
        ttk.Label(body, text="Preferred Time (HH:MM) *", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).grid(row=2, column=1, sticky="w", pady=(0, 2), padx=(16, 0))

        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.var_date = tk.StringVar(value=tomorrow)
        ttk.Entry(body, textvariable=self.var_date).grid(row=3, column=0, sticky="ew", pady=(0, 14))
        self.var_time = tk.StringVar(value="09:00")
        ttk.Entry(body, textvariable=self.var_time).grid(row=3, column=1, sticky="ew", pady=(0, 14), padx=(16, 0))

        # Address selection
        ttk.Label(body, text="Service Location / Address *", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 2))
        self.addr_combo = ttk.Combobox(body, state="readonly")
        addr_values = [f"{a.id} | {a.label or 'Address'}: {a.street}, {a.city}" for a in addresses]
        self.addr_combo["values"] = addr_values
        default = next((a for a in addresses if a.is_default), addresses[0])
        self.addr_combo.set(f"{default.id} | {default.label or 'Address'}: {default.street}, {default.city}")
        self.addr_combo.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        # Add-ons section
        ttk.Label(body, text="Available Service Add-ons (Optional)", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.addons_frame = ttk.Frame(body, style="Surface.TFrame")
        self.addons_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        self.addon_vars = {}

        # Promo Code
        ttk.Label(body, text="Promotional Code (Optional)", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).grid(row=8, column=0, columnspan=2, sticky="w", pady=(0, 2))
        promo_row = ttk.Frame(body, style="Surface.TFrame")
        promo_row.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        promo_row.grid_columnconfigure(0, weight=1)
        self.var_promo = tk.StringVar()
        promo_entry = ttk.Entry(promo_row, textvariable=self.var_promo)
        promo_entry.grid(row=0, column=0, sticky="ew")
        promo_entry.bind("<KeyRelease>", lambda e: self._update_summary())
        ttk.Button(promo_row, text="Apply Code", style="Secondary.TButton",
                   command=self._update_summary).grid(row=0, column=1, padx=(8, 0))

        # Notes
        ttk.Label(body, text="Special Instructions / Access Notes", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).grid(row=10, column=0, columnspan=2, sticky="w", pady=(0, 2))
        self.notes = tk.Text(body, height=3, wrap="word", relief="solid", borderwidth=1,
                             bg=theme.SURFACE, fg=theme.TEXT, insertbackground=theme.TEXT)
        self.notes.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        # Price Summary Box
        self.summary_box = tk.Frame(body, bg="#F1F5F9", padx=16, pady=12,
                                    highlightbackground=theme.BORDER, highlightthickness=1)
        self.summary_box.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(4, 16))
        self.summary_lbl = tk.Label(self.summary_box, text="", bg="#F1F5F9",
                                    font=("Segoe UI", 12, "bold"), fg=theme.PRIMARY, justify="left", anchor="w")
        self.summary_lbl.pack(fill="x")

        # Submit Button
        btn_bar = ttk.Frame(body, style="Surface.TFrame")
        btn_bar.grid(row=13, column=0, columnspan=2, sticky="w")
        ttk.Button(btn_bar, text="Confirm & Book Cleaning", command=self._submit).pack(side="left", padx=(0, 8))
        ttk.Button(btn_bar, text="Cancel", style="Secondary.TButton",
                   command=lambda: self.go("CustomerDashboard")).pack(side="left")

        self._update_addons()

    def _current_service(self):
        text = self.svc_combo.get()
        sid = self._svc_map.get(text)
        return self._id_to_svc.get(sid) if sid else None

    def _update_addons(self):
        for w in self.addons_frame.winfo_children():
            w.destroy()
        self.addon_vars = {}
        svc = self._current_service()
        if not svc:
            return
        with self.app.db_session():
            addons = [a for a in svc.add_ons if a.is_active]
        if not addons:
            ttk.Label(self.addons_frame, text="No extra add-ons available for this service.",
                      style="Surface.Muted.TLabel").pack(anchor="w")
        else:
            for a in addons:
                v = tk.BooleanVar()
                cb = ttk.Checkbutton(self.addons_frame, text=f"{a.name}  (+₱{a.price:,.0f})",
                                     variable=v, command=self._update_summary)
                cb.pack(anchor="w", pady=2)
                self.addon_vars[a.id] = (v, a)
        self._update_summary()

    def _update_summary(self):
        svc = self._current_service()
        if not svc:
            self.summary_lbl.config(text="")
            return
        service_price = (svc.discounted_price if (svc.discounted_price and svc.discounted_price < svc.base_price)
                         else svc.base_price)
        subtotal = Decimal(str(service_price))
        for aid, (v, a) in self.addon_vars.items():
            if v.get():
                subtotal += Decimal(str(a.price))

        discount = Decimal("0")
        code = self.var_promo.get().strip().upper()
        promo_info = ""
        if code:
            with self.app.db_session():
                promo = Promotion.query.filter_by(code=code, is_active=True).first()
            if promo:
                if promo.discount_type == "percentage":
                    discount = subtotal * (Decimal(str(promo.discount_value)) / Decimal("100"))
                else:
                    discount = Decimal(str(promo.discount_value))
                if promo.max_discount_amount:
                    discount = min(discount, Decimal(str(promo.max_discount_amount)))
                promo_info = f"  (Code: {code} applied!)"

        total = max(Decimal("0.00"), subtotal - discount)
        self.summary_lbl.config(
            text=f"Subtotal: ₱{subtotal:,.2f}   |   Discount: ₱{discount:,.2f}{promo_info}   |   TOTAL: ₱{total:,.2f}"
        )

    def _submit(self):
        svc = self._current_service()
        if not svc:
            self.flash("Please select a cleaning service.", "error")
            return
        try:
            bdate = datetime.strptime(self.var_date.get(), "%Y-%m-%d").date()
        except ValueError:
            self.flash("Invalid date format. Please use YYYY-MM-DD.", "error")
            return
        try:
            btime = datetime.strptime(self.var_time.get(), "%H:%M").time()
        except ValueError:
            self.flash("Invalid time format. Please use HH:MM (24-hour).", "error")
            return
        if bdate < date.today():
            self.flash("Booking date cannot be in the past.", "error")
            return

        addr_text = self.addr_combo.get()
        if not addr_text:
            self.flash("Please select an address.", "error")
            return
        addr_id = int(addr_text.split("|")[0].strip())

        profile = self.session.user.customer_profile
        selected_addons = [a for aid, (v, a) in self.addon_vars.items() if v.get()]

        with self.app.db_session():
            conflict = Booking.query.filter_by(scheduled_date=bdate, scheduled_time=btime).filter(
                Booking.status.notin_(["cancelled"])).first()
            if conflict:
                self.flash("The selected date and time slot is already reserved. Please choose another time.", "error")
                return

            service_price = (svc.discounted_price if (svc.discounted_price and svc.discounted_price < svc.base_price)
                             else svc.base_price)
            subtotal = Decimal(str(service_price))
            for a in selected_addons:
                subtotal += Decimal(str(a.price))

            discount = Decimal("0")
            applied = []
            code = self.var_promo.get().strip().upper()
            if code:
                promo = Promotion.query.filter_by(code=code, is_active=True).first()
                now = datetime.now(timezone.utc)
                if not promo:
                    self.flash(f'Promo code "{code}" is invalid.', "error")
                    return
                ps = promo.start_date.replace(tzinfo=timezone.utc) if promo.start_date.tzinfo is None else promo.start_date
                pe = promo.end_date.replace(tzinfo=timezone.utc) if promo.end_date.tzinfo is None else promo.end_date
                if not (ps <= now <= pe):
                    self.flash(f'Promo code "{code}" has expired or is not yet active.', "error")
                    return
                if promo.usage_limit is not None and promo.usage_count >= promo.usage_limit:
                    self.flash(f'Promo code "{code}" has reached its usage limit.', "error")
                    return
                if subtotal < Decimal(str(promo.min_order_value)):
                    self.flash(f'Minimum order of ₱{promo.min_order_value:,.2f} required for "{code}".', "error")
                    return
                if promo.discount_type == "percentage":
                    d = subtotal * (Decimal(str(promo.discount_value)) / Decimal("100"))
                else:
                    d = Decimal(str(promo.discount_value))
                if promo.max_discount_amount:
                    d = min(d, Decimal(str(promo.max_discount_amount)))
                discount = d
                applied.append(promo)

            total = max(Decimal("0.00"), subtotal - discount)
            booking = Booking(customer_id=profile.id, address_id=addr_id,
                              scheduled_date=bdate, scheduled_time=btime,
                              subtotal=subtotal, discount_amount=discount,
                              total_amount=total, notes=self.notes.get("1.0", "end").strip(),
                              status="pending", payment_status="unpaid")
            db.session.add(booking)
            db.session.flush()

            db.session.add(BookingItem(booking_id=booking.id, service_id=svc.id, quantity=1,
                                       unit_price=Decimal(str(service_price)),
                                       total_price=Decimal(str(service_price)),
                                       service_name=svc.name, service_description=svc.description))
            for a in selected_addons:
                db.session.add(BookingItem(booking_id=booking.id, add_on_id=a.id, quantity=1,
                                           unit_price=Decimal(str(a.price)),
                                           total_price=Decimal(str(a.price)),
                                           service_name=a.name, service_description=a.description))
            for promo in applied:
                if promo.usage_limit is not None and promo.usage_count >= promo.usage_limit:
                    self.flash(f'Promo code "{promo.code}" has reached its usage limit.', "error")
                    db.session.rollback()
                    return
                db.session.add(PromotionRedemption(promotion_id=promo.id, booking_id=booking.id,
                                                   discount_amount=discount))
                promo.usage_count += 1
            bid = booking.id
            db.session.commit()

        self.flash("Booking created successfully! Please review details and proceed to payment.", "success")
        self.go("BookingDetail", booking_id=bid)


class MyBookings(_CustomerFrame):
    def build(self):
        pass

    def on_show(self, **kwargs):
        self._layout("My Bookings")
        if not self.session.require_customer():
            self.flash("Please log in.", "error")
            self.go("Login")
            return
        profile = self.session.user.customer_profile
        with self.app.db_session():
            bookings = (Booking.query.filter_by(customer_id=profile.id)
                        .order_by(Booking.created_at.desc()).all())

        top = ttk.Frame(self.content)
        top.pack(fill="x", padx=20, pady=(20, 10))
        ttk.Label(top, text="My Bookings", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(top, text="＋ New Booking",
                   command=lambda: self.go("BookService")).pack(side="right")

        if not bookings:
            card = theme.make_card(self.content)
            card.pack(fill="x", padx=20, pady=16)
            inner = theme.make_inner(card)
            inner.pack(fill="x", padx=20, pady=24)
            ttk.Label(inner, text="You have no bookings recorded yet.",
                      style="Surface.Muted.TLabel", font=("Segoe UI", 11)).pack(anchor="center", pady=(0, 10))
            ttk.Button(inner, text="Book a Cleaning Service",
                       command=lambda: self.go("BookService")).pack(anchor="center")
            return

        cols = ("id", "service", "date", "status", "payment", "total")
        container, tree = make_treeview_with_scrollbar(
            self.content, columns=cols,
            headings=["ID", "Service", "Scheduled Date & Time", "Status", "Payment", "Total"],
            widths=[50, 200, 180, 110, 100, 100], height=14
        )
        for i, b in enumerate(bookings):
            svc_name = b.items[0].service_name if b.items else "—"
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=(b.id, svc_name,
                                           f"{b.scheduled_date} {b.scheduled_time.strftime('%I:%M %p')}",
                                           b.status.upper(), b.payment_status.upper(),
                                           f"₱{b.total_amount:,.2f}"), tags=(tag,))
        container.pack(fill="both", expand=True, padx=20, pady=8)
        tree.bind("<Double-1>", lambda e: self._open(tree))

        ttk.Label(self.content, text="💡 Tip: Double-click any booking row to view full details, pay, or reschedule.",
                  style="Muted.TLabel", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(4, 16))

    def _open(self, tree):
        sel = tree.selection()
        if sel:
            bid = tree.item(sel[0])["values"][0]
            self.go("BookingDetail", booking_id=int(bid))


class BookingDetail(_CustomerFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.booking_id = None

    def build(self):
        pass

    def on_show(self, booking_id=None, **kwargs):
        self._layout("My Bookings")
        self.booking_id = booking_id
        if not self.session.require_customer():
            self.go("Login")
            return
        if not booking_id:
            self.go("MyBookings")
            return
        with self.app.db_session():
            booking = Booking.query.get(booking_id)
            if not booking:
                self.flash("Booking not found.", "error")
                self.go("MyBookings")
                return
            profile = self.session.user.customer_profile
            if booking.customer_id != profile.id:
                self.flash("Access denied.", "error")
                self.go("MyBookings")
                return
            self._render(booking)

    def _render(self, b):
        top = ttk.Frame(self.content)
        top.pack(fill="x", padx=20, pady=(20, 10))
        ttk.Label(top, text=f"Booking #{b.id}", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(top, text="← Back to Bookings", style="Secondary.TButton",
                   command=lambda: self.go("MyBookings")).pack(side="right")

        card = theme.make_card(self.content)
        card.pack(fill="x", padx=20, pady=8)
        body = theme.make_inner(card)
        body.pack(fill="x", padx=24, pady=20)
        body.grid_columnconfigure(0, weight=1)

        # Status & payment badges row
        badge_row = ttk.Frame(body, style="Surface.TFrame")
        badge_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        badge_row.grid_columnconfigure(0, weight=1)
        theme.make_badge(badge_row, f"STATUS: {b.status.upper()}", b.status).grid(row=0, column=0, sticky="w")
        theme.make_badge(badge_row, f"PAYMENT: {b.payment_status.upper()}", b.payment_status).grid(row=0, column=1, sticky="e")

        ttk.Label(body, text=f"Scheduled Date: {b.scheduled_date.strftime('%B %d, %Y')} at {b.scheduled_time.strftime('%I:%M %p')}",
                  style="Surface.TLabel", font=("Segoe UI", 12, "bold")).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 2))

        if b.address:
            ttk.Label(body, text=f"📍 Location: {b.address.street}, {b.address.city}, {b.address.province} {b.address.postal_code or ''}",
                      style="Surface.Muted.TLabel", font=("Segoe UI", 10)).grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 4))

        # Cleaner Information (Fixed bug: direct access to cleaner columns)
        cleaner_name = "Not yet assigned"
        cleaner_phone = ""
        if b.cleaner:
            cleaner_name = f"{b.cleaner.first_name} {b.cleaner.last_name}".strip()
            if not cleaner_name and b.cleaner.user:
                cleaner_name = b.cleaner.user.email
            cleaner_phone = f" • Phone: {b.cleaner.phone}" if b.cleaner.phone else ""
        ttk.Label(body, text=f"🧹 Cleaner: {cleaner_name}{cleaner_phone}",
                  style="Surface.TLabel", font=("Segoe UI", 10, "bold"),
                  foreground=theme.PRIMARY if b.cleaner else theme.TEXT_MUTED).grid(row=3, column=0, columnspan=2, sticky="w", pady=(2, 10))

        # Items breakdown
        ttk.Label(body, text="Services & Add-ons Breakdown", style="Surface.TLabel",
                  font=("Segoe UI", 11, "bold")).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 4))
        for i, item in enumerate(b.items, start=5):
            ttk.Label(body, text=f"  • {item.service_name} — ₱{item.total_price:,.2f}",
                      style="Surface.Muted.TLabel", font=("Segoe UI", 10)).grid(row=i, column=0, columnspan=2, sticky="w", padx=(8, 0), pady=1)

        r = 5 + len(b.items)
        ttk.Separator(body).grid(row=r, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Label(body, text=f"Subtotal: ₱{b.subtotal:,.2f}", style="Surface.Muted.TLabel").grid(row=r + 1, column=0, sticky="w")
        ttk.Label(body, text=f"Discount Applied: -₱{b.discount_amount:,.2f}",
                  style="Surface.Muted.TLabel", foreground=theme.SUCCESS).grid(row=r + 2, column=0, sticky="w")
        ttk.Label(body, text=f"Total Amount: ₱{b.total_amount:,.2f}", style="Surface.TLabel",
                  font=("Segoe UI", 14, "bold"), foreground=theme.PRIMARY).grid(row=r + 3, column=0, sticky="w", pady=(4, 0))

        if b.notes:
            ttk.Label(body, text=f"Special Instructions: {b.notes}", style="Surface.Muted.TLabel",
                      wraplength=650).grid(row=r + 4, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # Review display
        if b.review:
            stars = "★" * b.review.rating + "☆" * (5 - b.review.rating)
            ttk.Label(body, text=f"Your Review: {stars} — \"{b.review.comment}\"",
                      style="Surface.TLabel", font=("Segoe UI", 10, "bold"),
                      foreground="#D97706").grid(row=r + 5, column=0, columnspan=2, sticky="w", pady=(12, 0))

        # Action Buttons Bar
        actions_card = theme.make_card(self.content)
        actions_card.pack(fill="x", padx=20, pady=12)
        actions = theme.make_inner(actions_card)
        actions.pack(fill="x", padx=16, pady=12)

        if b.payment_status != "paid" and b.status != "cancelled":
            ttk.Button(actions, text="💳 Pay Now (Sandbox / Cash)", style="Success.TButton",
                       command=lambda: self._pay(b.id)).pack(side="left", padx=4)
        if b.status in ["pending", "confirmed"]:
            ttk.Button(actions, text="📅 Reschedule", style="Secondary.TButton",
                       command=lambda: self._reschedule_dialog(b.id)).pack(side="left", padx=4)
            ttk.Button(actions, text="✕ Cancel Booking", style="Danger.TButton",
                       command=lambda: self._cancel(b.id)).pack(side="left", padx=4)
        if b.status == "completed" and not b.review:
            ttk.Button(actions, text="⭐ Write a Review", command=lambda: self._review_dialog(b.id)).pack(side="left", padx=4)

    def _pay(self, bid, auto_confirm=False, method="gcash"):
        with self.app.db_session():
            b = Booking.query.get(bid)
            if not b:
                return
            if b.payment_status == "paid":
                self.flash("This booking is already paid.", "info")
                return
            total_amt = b.total_amount

        if auto_confirm:
            is_cash = (method == "cash")
            with self.app.db_session():
                b = Booking.query.get(bid)
                if b and b.payment_status != "paid":
                    ref = f"{method.upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"
                    db.session.add(Payment(
                        booking_id=b.id,
                        payment_method=method,
                        payment_reference=ref,
                        amount=b.total_amount,
                        status="pending" if is_cash else "completed",
                        paid_at=None if is_cash else datetime.now(timezone.utc),
                        payment_metadata='{"mode": "sandbox", "channel": "' + method + '"}'
                    ))
                    b.payment_status = "unpaid" if is_cash else "paid"
                    b.status = "confirmed"
                    db.session.commit()
            msg = "Cash payment recorded. Your booking is confirmed!" if is_cash else "Payment completed successfully! Booking confirmed."
            self.flash(msg, "success")
            self.on_show(booking_id=bid)
            return

        top = tk.Toplevel(self)
        top.title(f"Payment Checkout — Booking #{bid}")
        theme.configure_toplevel(top, 460, 390)

        ttk.Label(top, text="Select Payment Method", font=("Segoe UI", 12, "bold")).pack(pady=(16, 4), padx=20, anchor="w")
        ttk.Label(top, text=f"Total Payable: ₱{total_amt:,.2f}", font=("Segoe UI", 11, "bold"), foreground=theme.PRIMARY).pack(padx=20, anchor="w", pady=(0, 10))

        # Sandbox notice
        notice = tk.Frame(top, bg="#FFFBEB", highlightbackground="#FCD34D", highlightthickness=1, padx=12, pady=6)
        notice.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(notice, text="🧪 Sandbox Simulation: Secure mock payment for testing.", bg="#FFFBEB", fg="#92400E", font=("Segoe UI", 8)).pack(anchor="w")

        method_var = tk.StringVar(value="gcash")
        for val, title, sub in [
            ("gcash", "📱 GCash (E-Wallet)", "Instant simulated GCash payment confirmation"),
            ("maya", "💳 Maya / QR Ph", "Instant simulated Maya mobile checkout"),
            ("card", "💳 Credit or Debit Card", "Simulated Visa / Mastercard checkout"),
            ("cash", "💵 Cash on Service", "Pay cash directly to cleaning staff on visit"),
        ]:
            row = ttk.Frame(top)
            row.pack(fill="x", padx=20, pady=3)
            ttk.Radiobutton(row, text=f"{title}  —  {sub}", variable=method_var, value=val).pack(anchor="w")

        def confirm_payment():
            method = method_var.get()
            is_cash = (method == "cash")
            with self.app.db_session():
                b = Booking.query.get(bid)
                if not b or b.payment_status == "paid":
                    top.destroy()
                    return
                ref = f"{method.upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"
                db.session.add(Payment(
                    booking_id=b.id,
                    payment_method=method,
                    payment_reference=ref,
                    amount=b.total_amount,
                    status="pending" if is_cash else "completed",
                    paid_at=None if is_cash else datetime.now(timezone.utc),
                    payment_metadata='{"mode": "sandbox", "channel": "' + method + '"}'
                ))
                b.payment_status = "unpaid" if is_cash else "paid"
                b.status = "confirmed"
                db.session.commit()
            top.destroy()
            msg = "Cash payment recorded. Your booking is confirmed!" if is_cash else "Payment completed successfully! Booking confirmed."
            self.flash(msg, "success")
            self.on_show(booking_id=bid)

        btn_row = ttk.Frame(top)
        btn_row.pack(pady=16, padx=20, fill="x")
        ttk.Button(btn_row, text="Proceed with Payment", command=confirm_payment).pack(side="left")
        ttk.Button(btn_row, text="Cancel", style="Secondary.TButton", command=top.destroy).pack(side="right")

    def _cancel(self, bid):
        if not messagebox.askyesno("Cancel Booking", "Are you sure you want to cancel this booking?"):
            return
        with self.app.db_session():
            b = Booking.query.get(bid)
            if b.status in ["pending", "confirmed"]:
                b.status = "cancelled"
                db.session.commit()
                self.flash("Booking cancelled successfully.", "success")
            else:
                self.flash("Cannot cancel this booking in its current state.", "error")
        self.on_show(booking_id=bid)

    def _reschedule_dialog(self, bid):
        top = tk.Toplevel(self)
        top.title("Reschedule Appointment")
        top.geometry("380x260")
        top.transient(self)
        top.grab_set()
        theme.configure_toplevel(top, 380, 260)

        ttk.Label(top, text="Reschedule Booking", font=("Segoe UI", 12, "bold")).pack(pady=(16, 8), padx=20, anchor="w")
        ttk.Label(top, text="New Date (YYYY-MM-DD):").pack(pady=(4, 2), padx=20, anchor="w")
        tomorrow = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
        dvar = tk.StringVar(value=tomorrow)
        ttk.Entry(top, textvariable=dvar).pack(fill="x", padx=20)
        ttk.Label(top, text="New Time (HH:MM):").pack(pady=(8, 2), padx=20, anchor="w")
        tvar = tk.StringVar(value="09:00")
        ttk.Entry(top, textvariable=tvar).pack(fill="x", padx=20)

        def save():
            try:
                nd = datetime.strptime(dvar.get(), "%Y-%m-%d").date()
                nt = datetime.strptime(tvar.get(), "%H:%M").time()
            except ValueError:
                messagebox.showerror("Invalid", "Please provide a valid date (YYYY-MM-DD) and time (HH:MM).")
                return
            if nd < date.today():
                messagebox.showerror("Invalid", "Booking date cannot be in the past.")
                return
            with self.app.db_session():
                conflict = Booking.query.filter_by(scheduled_date=nd, scheduled_time=nt).filter(
                    Booking.id != bid, Booking.status.notin_(["cancelled"])).first()
                if conflict:
                    messagebox.showerror("Slot Unavailable", "That date and time slot is already booked. Please pick another.")
                    return
                b = Booking.query.get(bid)
                b.scheduled_date = nd
                b.scheduled_time = nt
                b.status = "pending"
                b.cleaner_id = None
                db.session.commit()
            top.destroy()
            self.flash("Booking rescheduled successfully! Status set to pending for confirmation.", "success")
            self.on_show(booking_id=bid)

        btn_row = ttk.Frame(top)
        btn_row.pack(pady=16, padx=20, fill="x")
        ttk.Button(btn_row, text="Confirm Reschedule", command=save).pack(side="left")
        ttk.Button(btn_row, text="Cancel", style="Secondary.TButton", command=top.destroy).pack(side="right")

    def _review_dialog(self, bid):
        top = tk.Toplevel(self)
        top.title("Write Service Review")
        top.geometry("440x340")
        top.transient(self)
        top.grab_set()
        theme.configure_toplevel(top, 440, 340)

        ttk.Label(top, text="Rate Your Cleaning Experience", font=("Segoe UI", 12, "bold")).pack(pady=(16, 8), padx=20, anchor="w")
        ttk.Label(top, text="Rating (1 to 5 Stars):").pack(pady=(4, 2), padx=20, anchor="w")
        rvar = tk.IntVar(value=5)
        ttk.Combobox(top, textvariable=rvar, values=[5, 4, 3, 2, 1], state="readonly").pack(fill="x", padx=20)
        ttk.Label(top, text="Your Feedback / Comments:").pack(pady=(8, 2), padx=20, anchor="w")
        ctext = tk.Text(top, height=5, wrap="word", bg=theme.SURFACE, fg=theme.TEXT,
                        relief="solid", borderwidth=1, insertbackground=theme.TEXT)
        ctext.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        def save():
            comment = ctext.get("1.0", "end").strip()
            profile = self.session.user.customer_profile
            with self.app.db_session():
                db.session.add(Review(booking_id=bid, customer_id=profile.id,
                                      rating=int(rvar.get()), comment=comment))
                db.session.commit()
            top.destroy()
            self.flash("Thank you for your review! It helps us maintain top quality.", "success")
            self.on_show(booking_id=bid)

        btn_row = ttk.Frame(top)
        btn_row.pack(pady=(0, 16), padx=20, fill="x")
        ttk.Button(btn_row, text="Submit Review", command=save).pack(side="left")
        ttk.Button(btn_row, text="Cancel", style="Secondary.TButton", command=top.destroy).pack(side="right")


class Addresses(_CustomerFrame):
    def build(self):
        pass

    def on_show(self, **kwargs):
        self._layout("Addresses")
        if not self.session.require_customer():
            self.go("Login")
            return
        profile = self.session.user.customer_profile
        with self.app.db_session():
            addresses = Address.query.filter_by(customer_id=profile.id).all()

        top = ttk.Frame(self.content)
        top.pack(fill="x", padx=20, pady=(20, 10))
        ttk.Label(top, text="Saved Addresses", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(top, text="＋ Add New Address",
                   command=lambda: self._address_dialog()).pack(side="right")

        if not addresses:
            card = theme.make_card(self.content)
            card.pack(fill="x", padx=20, pady=16)
            inner = theme.make_inner(card)
            inner.pack(fill="x", padx=20, pady=24)
            ttk.Label(inner, text="No addresses saved yet. Add your home or office address.",
                      style="Surface.Muted.TLabel", font=("Segoe UI", 11)).pack(anchor="center", pady=(0, 10))
            ttk.Button(inner, text="＋ Add Address", command=lambda: self._address_dialog()).pack(anchor="center")
            return

        for a in addresses:
            card = theme.make_card(self.content)
            card.pack(fill="x", padx=20, pady=6)
            row = theme.make_inner(card)
            row.pack(fill="x", padx=16, pady=14)

            left = ttk.Frame(row, style="Surface.TFrame")
            left.pack(side="left", fill="both", expand=True)

            head_row = ttk.Frame(left, style="Surface.TFrame")
            head_row.pack(anchor="w")
            ttk.Label(head_row, text=a.label or "Address", style="Surface.TLabel",
                      font=("Segoe UI", 12, "bold")).pack(side="left")
            if a.is_default:
                tag = tk.Label(head_row, text="DEFAULT", bg="#E8F4FD", fg=theme.PRIMARY,
                               font=("Segoe UI", 8, "bold"), padx=6, pady=1)
                tag.pack(side="left", padx=8)

            ttk.Label(left, text=f"{a.street}, {a.city}, {a.province} {a.postal_code or ''}",
                      style="Surface.Muted.TLabel", font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

            btns = ttk.Frame(row, style="Surface.TFrame")
            btns.pack(side="right")
            ttk.Button(btns, text="Edit", style="Secondary.TButton",
                       command=lambda x=a: self._address_dialog(x)).pack(side="left", padx=3)
            ttk.Button(btns, text="Delete", style="Danger.TButton",
                       command=lambda x=a.id: self._delete(x)).pack(side="left", padx=3)

    def _address_dialog(self, addr=None):
        top = tk.Toplevel(self)
        top.title("Edit Address" if addr else "Add Address")
        top.geometry("440x440")
        top.transient(self)
        top.grab_set()
        theme.configure_toplevel(top, 440, 440)

        ttk.Label(top, text="Address Details", font=("Segoe UI", 12, "bold")).pack(pady=(16, 6), padx=20, anchor="w")

        fields = {}
        for label, key in [("Label (e.g. Home, Office)", "label"), ("Street / Unit / Building *", "street"),
                           ("City *", "city"), ("Province *", "province"), ("Postal Code", "postal_code")]:
            ttk.Label(top, text=label, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(6, 1))
            e = ttk.Entry(top, width=40)
            if addr:
                e.insert(0, getattr(addr, key) or "")
            elif key == "province":
                e.insert(0, "Metro Manila")
            e.pack(fill="x", padx=20)
            fields[key] = e

        def_var = tk.BooleanVar(value=addr.is_default if addr else False)
        ttk.Checkbutton(top, text="Set as default service address", variable=def_var).pack(anchor="w", padx=20, pady=10)

        def save():
            data = {k: v.get().strip() for k, v in fields.items()}
            if not data["street"] or not data["city"] or not data["province"]:
                messagebox.showerror("Invalid", "Street, City, and Province are required.")
                return
            profile = self.session.user.customer_profile
            with self.app.db_session():
                if def_var.get():
                    Address.query.filter_by(customer_id=profile.id).update({"is_default": False})
                if addr:
                    a = Address.query.get(addr.id)
                    for k, v in data.items():
                        setattr(a, k, v)
                    a.is_default = def_var.get()
                else:
                    db.session.add(Address(customer_id=profile.id, is_default=def_var.get(), **data))
                db.session.commit()
            top.destroy()
            self.flash("Address saved successfully.", "success")
            self.on_show()

        btn_row = ttk.Frame(top)
        btn_row.pack(pady=12, padx=20, fill="x")
        ttk.Button(btn_row, text="Save Address", command=save).pack(side="left")
        ttk.Button(btn_row, text="Cancel", style="Secondary.TButton", command=top.destroy).pack(side="right")

    def _delete(self, aid):
        if not messagebox.askyesno("Delete Address", "Are you sure you want to delete this address?"):
            return
        with self.app.db_session():
            linked = Booking.query.filter_by(address_id=aid).first()
            if linked:
                self.flash("This address is linked to existing bookings and cannot be deleted.", "error")
                return
            a = Address.query.get(aid)
            if a:
                db.session.delete(a)
                db.session.commit()
                self.flash("Address removed.", "success")
        self.on_show()


class CustomerProfile(_CustomerFrame):
    def build(self):
        pass

    def on_show(self, **kwargs):
        self._layout("Profile")
        if not self.session.require_customer():
            self.go("Login")
            return
        profile = self.session.user.customer_profile
        with self.app.db_session():
            p = CustomerProfileModel.query.get(profile.id)

        ttk.Label(self.content, text="My Profile", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=20, pady=(20, 10))

        card = theme.make_card(self.content)
        card.pack(fill="x", padx=20, pady=8)
        body = theme.make_inner(card)
        body.pack(fill="x", padx=24, pady=20)
        body.grid_columnconfigure(1, weight=1)

        self.fields = {}
        for i, (label, key) in enumerate([("First Name *", "first_name"), ("Last Name *", "last_name"), ("Contact Phone", "phone")]):
            ttk.Label(body, text=label, style="Surface.TLabel",
                      font=("Segoe UI", 10, "bold")).grid(row=i, column=0, sticky="w", pady=6)
            e = ttk.Entry(body)
            e.insert(0, getattr(p, key) or "")
            e.grid(row=i, column=1, sticky="ew", padx=12, pady=6)
            self.fields[key] = e

        ttk.Label(body, text="Email Address", style="Surface.TLabel",
                  font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w", pady=6)
        ttk.Label(body, text=f"{p.user.email}  (Account Identifier)", style="Surface.Muted.TLabel",
                  font=("Segoe UI", 10)).grid(row=3, column=1, sticky="w", padx=12, pady=6)

        def save():
            data = {k: v.get().strip() for k, v in self.fields.items()}
            if not data["first_name"] or not data["last_name"]:
                self.flash("First and Last name are required.", "error")
                return
            with self.app.db_session():
                pr = CustomerProfileModel.query.get(profile.id)
                pr.first_name = data["first_name"]
                pr.last_name = data["last_name"]
                pr.phone = data["phone"]
                db.session.commit()
            self.flash("Profile details updated successfully.", "success")
            self.on_show()

        self.save = save
        btn_row = ttk.Frame(body, style="Surface.TFrame")
        btn_row.grid(row=4, column=0, columnspan=2, sticky="w", pady=(16, 0))
        ttk.Button(btn_row, text="Save Changes", command=save).pack(side="left")

        # Change Password Card
        pwd_card = theme.make_card(self.content)
        pwd_card.pack(fill="x", padx=20, pady=(16, 24))
        pwd_body = theme.make_inner(pwd_card)
        pwd_body.pack(fill="x", padx=24, pady=20)
        pwd_body.grid_columnconfigure(1, weight=1)

        ttk.Label(pwd_body, text="Security & Password", style="Surface.TLabel",
                  font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(pwd_body, text="Current Password *", style="Surface.TLabel",
                  font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        self.entry_curr_pwd = ttk.Entry(pwd_body, show="•")
        self.entry_curr_pwd.grid(row=1, column=1, sticky="ew", padx=12, pady=6)

        ttk.Label(pwd_body, text="New Password * (min. 8 chars)", style="Surface.TLabel",
                  font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        self.entry_new_pwd = ttk.Entry(pwd_body, show="•")
        self.entry_new_pwd.grid(row=2, column=1, sticky="ew", padx=12, pady=6)

        ttk.Label(pwd_body, text="Confirm New Password *", style="Surface.TLabel",
                  font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w", pady=6)
        self.entry_conf_pwd = ttk.Entry(pwd_body, show="•")
        self.entry_conf_pwd.grid(row=3, column=1, sticky="ew", padx=12, pady=6)

        def change_pwd():
            curr = self.entry_curr_pwd.get().strip()
            new_p = self.entry_new_pwd.get().strip()
            conf = self.entry_conf_pwd.get().strip()
            if not curr or not new_p or not conf:
                self.flash("All password fields are required.", "error")
                return
            if len(new_p) < 8:
                self.flash("New password must be at least 8 characters long.", "error")
                return
            if new_p != conf:
                self.flash("New passwords do not match.", "error")
                return

            with self.app.db_session():
                u = User.query.get(self.session.user.id)
                if not u.check_password(curr):
                    self.flash("Current password is incorrect.", "error")
                    return
                u.set_password(new_p)
                db.session.commit()

            self.entry_curr_pwd.delete(0, tk.END)
            self.entry_new_pwd.delete(0, tk.END)
            self.entry_conf_pwd.delete(0, tk.END)
            self.flash("Password updated successfully!", "success")

        self.change_password = change_pwd
        pwd_btn_row = ttk.Frame(pwd_body, style="Surface.TFrame")
        pwd_btn_row.grid(row=4, column=0, columnspan=2, sticky="w", pady=(16, 0))
        ttk.Button(pwd_btn_row, text="Update Password", command=change_pwd).pack(side="left")


class Notifications(_CustomerFrame):
    def build(self):
        pass

    def on_show(self, **kwargs):
        self._layout("Notifications")
        if not self.session.require_customer():
            self.go("Login")
            return
        with self.app.db_session():
            notifs = (Notification.query.filter_by(user_id=self.session.user.id)
                      .order_by(Notification.created_at.desc()).all())
            Notification.query.filter_by(user_id=self.session.user.id, is_read=False).update({"is_read": True})
            db.session.commit()

        ttk.Label(self.content, text="Account Notifications", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=20, pady=(20, 10))

        if not notifs:
            card = theme.make_card(self.content)
            card.pack(fill="x", padx=20, pady=16)
            inner = theme.make_inner(card)
            inner.pack(fill="x", padx=20, pady=24)
            ttk.Label(inner, text="🔔 You have no new notifications right now.",
                      style="Surface.Muted.TLabel", font=("Segoe UI", 11)).pack(anchor="center")
            return

        for n in notifs:
            card = theme.make_card(self.content)
            card.pack(fill="x", padx=20, pady=4)
            inner = theme.make_inner(card)
            inner.pack(fill="x", padx=16, pady=12)

            top_row = ttk.Frame(inner, style="Surface.TFrame")
            top_row.pack(fill="x")
            ttk.Label(top_row, text=f"🔔 {n.title}", style="Surface.TLabel",
                      font=("Segoe UI", 11, "bold")).pack(side="left")
            created_str = n.created_at.strftime("%b %d, %Y %I:%M %p") if n.created_at else ""
            ttk.Label(top_row, text=created_str, style="Surface.Muted.TLabel",
                      font=("Segoe UI", 9)).pack(side="right")

            ttk.Label(inner, text=n.message, style="Surface.Muted.TLabel",
                      wraplength=700, justify="left").pack(anchor="w", pady=(4, 0))

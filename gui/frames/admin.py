"""Admin frames: Dashboard, Bookings, Booking Detail, Services, Cleaners, Promotions, Users, Settings."""

import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal

from gui.app import BaseFrame
from gui import theme
from gui.theme import ScrollableFrame, make_treeview_with_scrollbar
from app import db
from app.models import (
    Service, AddOn, Promotion, Booking, BookingItem, CustomerProfile, User,
    Cleaner, Payment, AuditLog, Inquiry, BusinessSettings, Review, Address,
)


def _admin_sidebar(parent, app, active):
    sb = tk.Frame(parent, bg=theme.SIDEBAR, width=224)
    sb.pack(side="left", fill="y")
    sb.pack_propagate(False)

    # App Brand Header
    brand_box = tk.Frame(sb, bg=theme.SIDEBAR)
    brand_box.pack(fill="x", padx=16, pady=(20, 14))
    tk.Label(brand_box, text="✨ CleanHome PH", bg=theme.SIDEBAR, fg="#FFFFFF",
             font=("Segoe UI", 15, "bold")).pack(anchor="w")

    # Admin Badge Box
    admin_user = app.session.user
    email = admin_user.email if admin_user else "admin"
    initials = email[:2].upper() if email else "AD"

    u_box = tk.Frame(sb, bg="#1E293B", padx=12, pady=10)
    u_box.pack(fill="x", padx=12, pady=(0, 16))

    u_top = tk.Frame(u_box, bg="#1E293B")
    u_top.pack(fill="x")
    avatar = tk.Label(u_top, text=initials, bg=theme.WARNING, fg="#FFFFFF",
                      font=("Segoe UI", 10, "bold"), width=3, pady=2)
    avatar.pack(side="left")

    u_info = tk.Frame(u_top, bg="#1E293B")
    u_info.pack(side="left", padx=(10, 0), fill="x", expand=True)
    tk.Label(u_info, text=email, bg="#1E293B", fg="#FFFFFF",
             font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x")
    tk.Label(u_info, text="● Super Administrator", bg="#1E293B", fg="#FBBF24",
             font=("Segoe UI", 8), anchor="w").pack(fill="x")

    # Menu Categories
    tk.Label(sb, text="OPERATIONS", bg=theme.SIDEBAR, fg="#64748B",
             font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(0, 4))

    ops_items = [
        ("Dashboard", "AdminDashboard", "📊"),
        ("Bookings", "AdminBookings", "📋"),
        ("Services", "AdminServices", "🧹"),
        ("Cleaners", "AdminCleaners", "👥"),
        ("Promotions", "AdminPromotions", "🏷️"),
    ]
    for label, target, icon in ops_items:
        is_active = (label == active)
        style = "Sidebar.Active.TButton" if is_active else "Sidebar.TButton"
        ttk.Button(sb, text=f"{icon}  {label}", style=style,
                   command=lambda t=target: app.show_frame(t)).pack(fill="x", padx=10, pady=2)

    tk.Label(sb, text="SYSTEM", bg=theme.SIDEBAR, fg="#64748B",
             font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(10, 4))

    sys_items = [
        ("Customers", "AdminUsers", "👤"),
        ("Settings", "AdminSettings", "⚙️"),
    ]
    for label, target, icon in sys_items:
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
    tk.Label(sb_bottom, text="CleanHome Desktop v2.4 (Admin)", bg=theme.SIDEBAR, fg="#475569",
             font=("Segoe UI", 8)).pack()


class _AdminFrame(BaseFrame):
    def _layout(self, active):
        for child in self.winfo_children():
            child.destroy()
        _admin_sidebar(self, self.app, active)
        self.scroll = ScrollableFrame(self)
        self.scroll.pack(side="left", fill="both", expand=True)
        self.content = self.scroll.inner

    def _check_admin(self):
        if not self.session.require_admin():
            self.flash("Admin access required. Please log in with admin privileges.", "error")
            self.go("Login")
            return False
        return True


class AdminDashboard(_AdminFrame):
    def build(self):
        pass

    def on_show(self, **kwargs):
        self._layout("Dashboard")
        if not self._check_admin():
            return
        with self.app.db_session():
            total_bookings = Booking.query.count()
            total_revenue = db.session.query(db.func.sum(Payment.amount)).filter_by(status="completed").scalar() or Decimal("0")
            total_customers = CustomerProfile.query.filter_by(is_archived=False).count()
            active_services = Service.query.filter_by(is_active=True, is_archived=False).count()
            pending = Booking.query.filter_by(status="pending").count()
            completed = Booking.query.filter_by(status="completed").count()
            recent = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()
            upcoming = (Booking.query.filter(Booking.status.in_(["confirmed", "in_progress"]),
                                             Booking.scheduled_date >= date.today())
                        .order_by(Booking.scheduled_date, Booking.scheduled_time).limit(6).all())

        top = ttk.Frame(self.content)
        top.pack(fill="x", padx=24, pady=(24, 12))
        top_left = ttk.Frame(top)
        top_left.pack(side="left")
        ttk.Label(top_left, text="Admin Overview 📊", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(top_left, text="Live operational metrics, appointment dispatch queues, and financial performance.",
                  style="Muted.TLabel", font=("Segoe UI", 9)).pack(anchor="w")

        top_right = ttk.Frame(top)
        top_right.pack(side="right")
        ttk.Label(top_right, text=f"Today is {date.today().strftime('%B %d, %Y')}", style="Muted.TLabel",
                  font=("Segoe UI", 10)).pack(anchor="e")
        sys_chip = tk.Label(top_right, text="● System Healthy | WAL DB Active", bg="#ECFDF5", fg="#059669",
                            font=("Segoe UI", 8, "bold"), padx=8, pady=2)
        sys_chip.pack(anchor="e", pady=(4, 0))

        # Stats Cards Grid (2 rows of 3 cards for clean, spacious display)
        stats = ttk.Frame(self.content)
        stats.pack(fill="x", padx=24, pady=8)

        sc1 = theme.make_stat_card(stats, "Total Bookings", total_bookings,
                                   subtitle="All customer reservations", icon="📋",
                                   icon_bg="#F0FDFA", icon_fg=theme.PRIMARY)
        sc1.grid(row=0, column=0, padx=6, pady=4, sticky="nsew")

        sc2 = theme.make_stat_card(stats, "Total Revenue", f"₱{total_revenue:,.0f}",
                                   subtitle="Completed online & cash orders", icon="₱",
                                   icon_bg="#F0FDF4", icon_fg=theme.SUCCESS)
        sc2.grid(row=0, column=1, padx=6, pady=4, sticky="nsew")

        sc3 = theme.make_stat_card(stats, "Active Customers", total_customers,
                                   subtitle="Registered client profiles", icon="👥",
                                   icon_bg="#EFF6FF", icon_fg=theme.INFO)
        sc3.grid(row=0, column=2, padx=6, pady=4, sticky="nsew")

        sc4 = theme.make_stat_card(stats, "Active Services", active_services,
                                   subtitle="Live catalog offerings", icon="🧹",
                                   icon_bg="#E0F2FE", icon_fg=theme.SECONDARY)
        sc4.grid(row=1, column=0, padx=6, pady=4, sticky="nsew")

        sc5 = theme.make_stat_card(stats, "Pending Confirmation", pending,
                                   subtitle="Awaiting dispatch / cleaner", icon="⏳",
                                   icon_bg="#FFFBEB", icon_fg=theme.WARNING)
        sc5.grid(row=1, column=1, padx=6, pady=4, sticky="nsew")

        sc6 = theme.make_stat_card(stats, "Completed Jobs", completed,
                                   subtitle="Successfully delivered", icon="⭐",
                                   icon_bg="#F0FDFA", icon_fg=theme.PRIMARY_DARK)
        sc6.grid(row=1, column=2, padx=6, pady=4, sticky="nsew")

        for col in range(3):
            stats.grid_columnconfigure(col, weight=1)

        # Quick Dispatch Toolbar
        qb_frame = ttk.Frame(self.content)
        qb_frame.pack(fill="x", padx=24, pady=(12, 16))
        for (q_label, q_target) in [
            ("📋 All Bookings", "AdminBookings"),
            ("🧹 Service Catalog", "AdminServices"),
            ("👥 Cleaners Roster", "AdminCleaners"),
            ("🏷️ Promo Vouchers", "AdminPromotions"),
            ("👤 Customers List", "AdminUsers"),
            ("⚙️ Business Settings", "AdminSettings"),
        ]:
            ttk.Button(qb_frame, text=q_label, style="Secondary.TButton",
                       command=lambda t=q_target: self.go(t)).pack(side="left", padx=(0, theme.SPACE_SM))

        # Recent Bookings Table
        sec1 = ttk.Frame(self.content)
        sec1.pack(fill="x", padx=20, pady=(20, 6))
        ttk.Label(sec1, text="Recent Bookings", style="Heading.TLabel",
                  font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Button(sec1, text="View All Bookings →", style="Secondary.TButton",
                   command=lambda: self.go("AdminBookings")).pack(side="right")

        cols = ("id", "customer", "service", "date", "status", "total")
        container, tree = make_treeview_with_scrollbar(
            self.content, columns=cols,
            headings=["ID", "Customer", "Service", "Scheduled Date & Time", "Status", "Total"],
            widths=[50, 150, 180, 140, 100, 100], height=6
        )
        for i, b in enumerate(recent):
            cust = f"{b.customer.first_name} {b.customer.last_name}" if b.customer else "—"
            svc = b.items[0].service_name if b.items else "—"
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=(b.id, cust, svc,
                                           f"{b.scheduled_date} {b.scheduled_time.strftime('%I:%M %p')}",
                                           b.status.upper(), f"₱{b.total_amount:,.0f}"), tags=(tag,))
        container.pack(fill="x", padx=20, pady=4)
        tree.bind("<Double-1>", lambda e: self._open(tree))

        # Upcoming Appointments
        ttk.Label(self.content, text="Upcoming Appointments", style="Heading.TLabel",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 8))

        if not upcoming:
            ttk.Label(self.content, text="No upcoming confirmed appointments for today onwards.",
                      style="Muted.TLabel").pack(anchor="w", padx=20, pady=4)
        else:
            for b in upcoming:
                cust = f"{b.customer.first_name} {b.customer.last_name}" if b.customer else "—"
                svc = b.items[0].service_name if b.items else "—"
                row = theme.make_card(self.content)
                row.pack(fill="x", padx=20, pady=3)
                inner = theme.make_inner(row)
                inner.pack(fill="x", padx=16, pady=10)

                left_info = ttk.Frame(inner, style="Surface.TFrame")
                left_info.pack(side="left")
                ttk.Label(left_info, text=f"Booking #{b.id} — {b.scheduled_date.strftime('%b %d, %Y')} at {b.scheduled_time.strftime('%I:%M %p')}",
                          style="Surface.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
                ttk.Label(left_info, text=f"Customer: {cust}  •  Service: {svc}",
                          style="Surface.Muted.TLabel", font=("Segoe UI", 9)).pack(anchor="w")

                right_info = ttk.Frame(inner, style="Surface.TFrame")
                right_info.pack(side="right")
                status_badge = theme.make_badge(right_info, b.status.upper(), b.status)
                status_badge.pack(side="left", padx=8)
                ttk.Button(right_info, text="View Detail", style="Secondary.TButton",
                           command=lambda bid=b.id: self.go("AdminBookingDetail", booking_id=bid)).pack(side="left")

    def _open(self, tree):
        sel = tree.selection()
        if sel:
            bid = tree.item(sel[0])["values"][0]
            self.go("AdminBookingDetail", booking_id=int(bid))


class AdminBookings(_AdminFrame):
    def build(self):
        pass

    def on_show(self, **kwargs):
        self._layout("Bookings")
        if not self._check_admin():
            return
        self._render()

    def _render(self, status_filter=None):
        top = ttk.Frame(self.content)
        top.pack(fill="x", padx=20, pady=(20, 8))
        ttk.Label(top, text="Manage Bookings", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(side="left")

        # Filters Bar
        filters = ttk.Frame(self.content)
        filters.pack(fill="x", padx=20, pady=(4, 12))
        ttk.Label(filters, text="Filter:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))

        all_style = "TButton" if status_filter is None else "Secondary.TButton"
        ttk.Button(filters, text="All Bookings", style=all_style,
                   command=lambda: self._refilter(None)).pack(side="left", padx=2)
        for s in ["pending", "confirmed", "in_progress", "completed", "cancelled"]:
            cur_style = "TButton" if status_filter == s else "Secondary.TButton"
            ttk.Button(filters, text=s.replace("_", " ").title(), style=cur_style,
                       command=lambda x=s: self._refilter(x)).pack(side="left", padx=2)

        with self.app.db_session():
            q = Booking.query
            if status_filter:
                q = q.filter_by(status=status_filter)
            bookings = q.order_by(Booking.created_at.desc()).all()

        cols = ("id", "customer", "service", "date", "status", "payment", "cleaner", "total")
        container, tree = make_treeview_with_scrollbar(
            self.content, columns=cols,
            headings=["ID", "Customer", "Service", "Scheduled Date & Time", "Status", "Payment", "Cleaner", "Total"],
            widths=[45, 140, 160, 130, 95, 90, 120, 85], height=15
        )
        for i, b in enumerate(bookings):
            cust = f"{b.customer.first_name} {b.customer.last_name}" if b.customer else "—"
            svc = b.items[0].service_name if b.items else "—"
            cleaner_str = f"{b.cleaner.first_name} {b.cleaner.last_name}" if b.cleaner else "Unassigned"
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=(b.id, cust, svc,
                                           f"{b.scheduled_date} {b.scheduled_time.strftime('%I:%M %p')}",
                                           b.status.upper(), b.payment_status.upper(),
                                           cleaner_str, f"₱{b.total_amount:,.0f}"), tags=(tag,))
        container.pack(fill="both", expand=True, padx=20, pady=4)
        tree.bind("<Double-1>", lambda e: self._open(tree))

        ttk.Label(self.content, text="💡 Double-click any booking to open details, assign cleaners, or change status.",
                  style="Muted.TLabel", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(4, 16))

    def _refilter(self, status):
        for child in self.content.winfo_children():
            child.destroy()
        self._render(status)

    def _open(self, tree):
        sel = tree.selection()
        if sel:
            bid = tree.item(sel[0])["values"][0]
            self.go("AdminBookingDetail", booking_id=int(bid))


class AdminBookingDetail(_AdminFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.booking_id = None

    def build(self):
        pass

    def on_show(self, booking_id=None, **kwargs):
        self._layout("Bookings")
        self.booking_id = booking_id
        if not self._check_admin():
            return
        if not booking_id:
            self.go("AdminBookings")
            return
        with self.app.db_session():
            b = Booking.query.get(booking_id)
            if not b:
                self.flash("Booking record not found.", "error")
                self.go("AdminBookings")
                return
            cleaners = Cleaner.query.all()
            self._render(b, cleaners)

    def _render(self, b, cleaners):
        top = ttk.Frame(self.content)
        top.pack(fill="x", padx=20, pady=(20, 10))
        ttk.Label(top, text=f"Booking Detail #{b.id}", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(top, text="← Back to Bookings", style="Secondary.TButton",
                   command=lambda: self.go("AdminBookings")).pack(side="right")

        card = theme.make_card(self.content)
        card.pack(fill="x", padx=20, pady=8)
        body = theme.make_inner(card)
        body.pack(fill="x", padx=24, pady=20)
        body.grid_columnconfigure(0, weight=1)

        cust = f"{b.customer.first_name} {b.customer.last_name}" if b.customer else "—"
        cust_phone = f" • Phone: {b.customer.phone}" if (b.customer and b.customer.phone) else ""
        ttk.Label(body, text=f"Customer: {cust}{cust_phone}", style="Surface.TLabel",
                  font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        status_badge = theme.make_badge(body, b.status.upper(), b.status)
        status_badge.grid(row=0, column=1, sticky="e")

        ttk.Label(body, text=f"Scheduled Date: {b.scheduled_date.strftime('%B %d, %Y')} at {b.scheduled_time.strftime('%I:%M %p')}",
                  style="Surface.Muted.TLabel", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=(4, 2))
        if b.address:
            ttk.Label(body, text=f"📍 Location: {b.address.street}, {b.address.city}, {b.address.province}",
                      style="Surface.Muted.TLabel").grid(row=2, column=0, sticky="w")

        # Cleaner name (Fixed direct attribute access)
        cleaner_name = "Unassigned"
        if b.cleaner:
            cleaner_name = f"{b.cleaner.first_name} {b.cleaner.last_name}".strip()
            if b.cleaner.phone:
                cleaner_name += f" ({b.cleaner.phone})"
        ttk.Label(body, text=f"Assigned Cleaner: {cleaner_name}",
                  style="Surface.TLabel", font=("Segoe UI", 10, "bold"),
                  foreground=theme.PRIMARY if b.cleaner else theme.TEXT_MUTED).grid(row=3, column=0, sticky="w", pady=(2, 6))

        # Items list
        for i, item in enumerate(b.items, start=4):
            ttk.Label(body, text=f"  • {item.service_name} — ₱{item.total_price:,.2f}",
                      style="Surface.Muted.TLabel").grid(row=i, column=0, sticky="w")
        r = 4 + len(b.items)
        ttk.Separator(body).grid(row=r, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Label(body, text=f"Subtotal: ₱{b.subtotal:,.2f}  |  Discount: -₱{b.discount_amount:,.2f}",
                  style="Surface.Muted.TLabel").grid(row=r + 1, column=0, sticky="w")
        ttk.Label(body, text=f"TOTAL AMOUNT: ₱{b.total_amount:,.2f}", style="Surface.TLabel",
                  font=("Segoe UI", 13, "bold"), foreground=theme.PRIMARY).grid(row=r + 2, column=0, sticky="w", pady=(2, 0))
        payment_badge = theme.make_badge(body, f"PAYMENT: {b.payment_status.upper()}", b.payment_status)
        payment_badge.grid(row=r + 3, column=0, sticky="w", pady=(4, 0))

        # Assign cleaner card
        assign_card = theme.make_card(self.content)
        assign_card.pack(fill="x", padx=20, pady=8)
        assign = theme.make_inner(assign_card)
        assign.pack(fill="x", padx=16, pady=12)

        ttk.Label(assign, text="Assign Cleaner:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 8))
        cleaner_map = {}
        choices = ["-- Unassign Cleaner --"]
        cleaner_map["-- Unassign Cleaner --"] = None
        for c in cleaners:
            c_label = f"{c.id} | {c.first_name} {c.last_name}"
            if c.phone:
                c_label += f" ({c.phone})"
            choices.append(c_label)
            cleaner_map[c_label] = c.id

        cvar = tk.StringVar()
        combo = ttk.Combobox(assign, textvariable=cvar, values=choices, state="readonly", width=36)
        if b.cleaner:
            cur_label = f"{b.cleaner.id} | {b.cleaner.first_name} {b.cleaner.last_name}"
            if b.cleaner.phone:
                cur_label += f" ({b.cleaner.phone})"
            combo.set(cur_label)
        else:
            combo.current(0)
        combo.pack(side="left")

        def assign_cleaner():
            val = cvar.get()
            cid = cleaner_map.get(val)
            with self.app.db_session():
                booking = Booking.query.get(b.id)
                if cid:
                    conflict = Booking.query.filter(
                        Booking.cleaner_id == cid,
                        Booking.scheduled_date == booking.scheduled_date,
                        Booking.scheduled_time == booking.scheduled_time,
                        Booking.id != booking.id,
                        Booking.status.notin_(["cancelled"])).first()
                    if conflict:
                        self.flash("Selected cleaner is already booked for another service at this time slot.", "error")
                        return
                booking.cleaner_id = cid
                db.session.commit()
            self.flash("Cleaner assignment updated successfully.", "success")
            self.go("AdminBookingDetail", booking_id=b.id)

        ttk.Button(assign, text="Update Assignment", style="Secondary.TButton", command=assign_cleaner).pack(side="left", padx=8)

        # Status update action buttons
        actions_card = theme.make_card(self.content)
        actions_card.pack(fill="x", padx=20, pady=8)
        actions = theme.make_inner(actions_card)
        actions.pack(fill="x", padx=16, pady=12)

        ttk.Label(actions, text="Change Status:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 8))
        for status, label, style in [
            ("confirmed", "Confirm", "Success.TButton"),
            ("in_progress", "Start Service", "Secondary.TButton"),
            ("completed", "Mark Completed", "Success.TButton"),
            ("cancelled", "Cancel Booking", "Danger.TButton"),
        ]:
            ttk.Button(actions, text=label, style=style,
                       command=lambda s=status: self._set_status(b.id, s)).pack(side="left", padx=4)

        ttk.Button(actions, text="Reschedule", style="Secondary.TButton",
                   command=lambda: self._reschedule(b.id)).pack(side="left", padx=4)

    def _set_status(self, bid, status):
        with self.app.db_session():
            b = Booking.query.get(bid)
            b.status = status
            db.session.commit()
        self.flash(f"Booking status updated to {status.replace('_', ' ').title()}.", "success")
        self.go("AdminBookingDetail", booking_id=bid)

    def _reschedule(self, bid):
        top = tk.Toplevel(self)
        top.title("Reschedule Booking")
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
                messagebox.showerror("Invalid", "Date cannot be in the past.")
                return
            with self.app.db_session():
                conflict = Booking.query.filter_by(scheduled_date=nd, scheduled_time=nt).filter(
                    Booking.id != bid, Booking.status.notin_(["cancelled"])).first()
                if conflict:
                    messagebox.showerror("Conflict", "That slot is already booked.")
                    return
                b = Booking.query.get(bid)
                b.scheduled_date = nd
                b.scheduled_time = nt
                b.status = "pending"
                b.cleaner_id = None
                db.session.commit()
            top.destroy()
            self.flash("Booking rescheduled successfully.", "success")
            self.go("AdminBookingDetail", booking_id=bid)

        btn_row = ttk.Frame(top)
        btn_row.pack(pady=16, padx=20, fill="x")
        ttk.Button(btn_row, text="Confirm", command=save).pack(side="left")
        ttk.Button(btn_row, text="Cancel", style="Secondary.TButton", command=top.destroy).pack(side="right")


class AdminServices(_AdminFrame):
    def build(self):
        pass

    def on_show(self, **kwargs):
        self._layout("Services")
        if not self._check_admin():
            return
        self._render()

    def _render(self):
        top = ttk.Frame(self.content)
        top.pack(fill="x", padx=20, pady=(20, 8))
        ttk.Label(top, text="Services Catalog", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(top, text="＋ Add New Service",
                   command=lambda: self._service_dialog()).pack(side="right")

        with self.app.db_session():
            services = Service.query.filter_by(is_archived=False).order_by(Service.name).all()

        cols = ("id", "name", "base", "discounted", "duration", "active")
        container, tree = make_treeview_with_scrollbar(
            self.content, columns=cols,
            headings=["ID", "Service Name", "Base Price", "Promo Price", "Duration", "Active"],
            widths=[45, 220, 100, 100, 90, 70], height=14
        )
        for i, s in enumerate(services):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=(s.id, s.name, f"₱{s.base_price:,.0f}",
                                           f"₱{s.discounted_price:,.0f}" if s.discounted_price else "—",
                                           f"{s.duration_minutes}m", "Yes" if s.is_active else "No"), tags=(tag,))
        container.pack(fill="both", expand=True, padx=20, pady=8)
        tree.bind("<Double-1>", lambda e: self._open(tree))

        ttk.Label(self.content, text="💡 Double-click any service to edit details, pricing, duration, or active status.",
                  style="Muted.TLabel", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(4, 16))

    def _open(self, tree):
        sel = tree.selection()
        if sel:
            sid = tree.item(sel[0])["values"][0]
            self._service_dialog(int(sid))

    def _service_dialog(self, sid=None):
        with self.app.db_session():
            svc = Service.query.get(sid) if sid else None
            top = tk.Toplevel(self)
            top.title("Edit Service" if svc else "Add New Service")
            top.geometry("480x540")
            top.transient(self)
            top.grab_set()
            theme.configure_toplevel(top, 480, 540)

            ttk.Label(top, text="Service Information", font=("Segoe UI", 12, "bold")).pack(pady=(16, 6), padx=20, anchor="w")

            fields = {}
            for label, key in [("Service Name *", "name"), ("Description", "description"),
                               ("Base Price (₱) *", "base_price"), ("Discounted Price (₱)", "discounted_price"),
                               ("Duration (minutes)", "duration_minutes"), ("Image URL", "image_url")]:
                ttk.Label(top, text=label, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(4, 1))
                if key == "description":
                    w = tk.Text(top, height=3, wrap="word", bg=theme.SURFACE, fg=theme.TEXT,
                                relief="solid", borderwidth=1, insertbackground=theme.TEXT)
                    if svc and getattr(svc, key):
                        w.insert("1.0", getattr(svc, key))
                else:
                    w = ttk.Entry(top, width=40)
                    if svc and getattr(svc, key) is not None:
                        w.insert(0, str(getattr(svc, key)))
                    elif key == "duration_minutes":
                        w.insert(0, "60")
                w.pack(fill="x", padx=20)
                fields[key] = w

            active_var = tk.BooleanVar(value=svc.is_active if svc else True)
            ttk.Checkbutton(top, text="Service is Active and bookable", variable=active_var).pack(anchor="w", padx=20, pady=8)

            def save():
                try:
                    data = {
                        "name": fields["name"].get().strip(),
                        "description": fields["description"].get("1.0", "end").strip(),
                        "base_price": Decimal(fields["base_price"].get() or "0"),
                        "discounted_price": Decimal(fields["discounted_price"].get()) if fields["discounted_price"].get().strip() else None,
                        "duration_minutes": int(fields["duration_minutes"].get() or "60"),
                        "image_url": fields["image_url"].get().strip(),
                        "is_active": active_var.get(),
                    }
                except ValueError:
                    messagebox.showerror("Invalid Input", "Please enter valid numeric values for prices and integer minutes for duration.")
                    return
                if not data["name"] or data["base_price"] <= 0:
                    messagebox.showerror("Invalid Input", "Service name and a positive base price are required.")
                    return
                with self.app.db_session():
                    if svc:
                        s = Service.query.get(svc.id)
                        for k, v in data.items():
                            setattr(s, k, v)
                    else:
                        db.session.add(Service(**data))
                    db.session.commit()
                top.destroy()
                self.flash("Service saved successfully.", "success")
                self.on_show()

            btn_row = ttk.Frame(top)
            btn_row.pack(pady=14, padx=20, fill="x")
            ttk.Button(btn_row, text="Save Service", command=save).pack(side="left")
            ttk.Button(btn_row, text="Cancel", style="Secondary.TButton", command=top.destroy).pack(side="right")


class AdminCleaners(_AdminFrame):
    def build(self):
        pass

    def on_show(self, **kwargs):
        self._layout("Cleaners")
        if not self._check_admin():
            return
        self._render()

    def _render(self):
        top = ttk.Frame(self.content)
        top.pack(fill="x", padx=20, pady=(20, 8))
        ttk.Label(top, text="Professional Cleaners", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(top, text="＋ Add New Cleaner",
                   command=self._cleaner_dialog).pack(side="right")

        with self.app.db_session():
            cleaners = Cleaner.query.all()

        cols = ("id", "name", "email", "phone", "available", "active")
        container, tree = make_treeview_with_scrollbar(
            self.content, columns=cols,
            headings=["ID", "Cleaner Name", "Email", "Phone", "Available", "User Active"],
            widths=[45, 170, 200, 130, 90, 80], height=14
        )
        for i, cl in enumerate(cleaners):
            name = f"{cl.first_name} {cl.last_name}".strip() or "—"
            email = cl.user.email if cl.user else "—"
            phone = cl.phone or "—"
            avail = "Yes" if cl.is_available else "No"
            act = "Yes" if (cl.user and cl.user.is_active) else "No"
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=(cl.id, name, email, phone, avail, act), tags=(tag,))
        container.pack(fill="both", expand=True, padx=20, pady=8)
        tree.bind("<Double-1>", lambda e: self._open(tree))

        ttk.Label(self.content, text="💡 Double-click any cleaner to edit contact details, availability, and active status.",
                  style="Muted.TLabel", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(4, 16))

    def _open(self, tree):
        sel = tree.selection()
        if sel:
            cid = tree.item(sel[0])["values"][0]
            self._cleaner_dialog(int(cid))

    def _cleaner_dialog(self, cid=None):
        with self.app.db_session():
            cleaner = Cleaner.query.get(cid) if cid else None
            top = tk.Toplevel(self)
            top.title("Edit Cleaner" if cleaner else "Add Cleaner")
            top.geometry("440x440")
            top.transient(self)
            top.grab_set()
            theme.configure_toplevel(top, 440, 440)

            ttk.Label(top, text="Cleaner Profile", font=("Segoe UI", 12, "bold")).pack(pady=(16, 6), padx=20, anchor="w")

            fields = {}
            for label, key in [("First Name *", "first_name"), ("Last Name *", "last_name"),
                               ("Email Address *", "email"), ("Contact Phone", "phone")]:
                ttk.Label(top, text=label, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(5, 1))
                e = ttk.Entry(top, width=40)
                if cleaner:
                    if key == "email":
                        e.insert(0, cleaner.user.email if cleaner.user else "")
                    else:
                        e.insert(0, getattr(cleaner, key) or "")
                e.pack(fill="x", padx=20)
                fields[key] = e

            avail_var = tk.BooleanVar(value=cleaner.is_available if cleaner else True)
            ttk.Checkbutton(top, text="Available for New Bookings", variable=avail_var).pack(anchor="w", padx=20, pady=(10, 4))

            active_var = tk.BooleanVar(value=cleaner.user.is_active if (cleaner and cleaner.user) else True)
            ttk.Checkbutton(top, text="Account Active", variable=active_var).pack(anchor="w", padx=20, pady=4)

            def save():
                data = {k: v.get().strip() for k, v in fields.items()}
                if not data["email"] or not data["first_name"] or not data["last_name"]:
                    messagebox.showerror("Invalid Input", "First Name, Last Name, and Email are required.")
                    return
                with self.app.db_session():
                    if cleaner:
                        cl_obj = Cleaner.query.get(cleaner.id)
                        cl_obj.first_name = data["first_name"]
                        cl_obj.last_name = data["last_name"]
                        cl_obj.phone = data["phone"]
                        cl_obj.is_available = avail_var.get()
                        if cl_obj.user:
                            cl_obj.user.email = data["email"]
                            cl_obj.user.is_active = active_var.get()
                    else:
                        existing = User.query.filter_by(email=data["email"].lower()).first()
                        if existing:
                            messagebox.showerror("Duplicate", "A user with this email address already exists.")
                            return
                        u = User(email=data["email"].lower(), role="cleaner")
                        u.set_password("Cleaner123!")
                        u.is_active = active_var.get()
                        db.session.add(u)
                        db.session.flush()
                        db.session.add(Cleaner(user_id=u.id, first_name=data["first_name"],
                                               last_name=data["last_name"], phone=data["phone"],
                                               is_available=avail_var.get()))
                    db.session.commit()
                top.destroy()
                self.flash("Cleaner saved successfully.", "success")
                self.on_show()

            btn_row = ttk.Frame(top)
            btn_row.pack(pady=16, padx=20, fill="x")
            ttk.Button(btn_row, text="Save Cleaner", command=save).pack(side="left")
            ttk.Button(btn_row, text="Cancel", style="Secondary.TButton", command=top.destroy).pack(side="right")


class AdminPromotions(_AdminFrame):
    def build(self):
        pass

    def on_show(self, **kwargs):
        self._layout("Promotions")
        if not self._check_admin():
            return
        self._render()

    def _render(self):
        top = ttk.Frame(self.content)
        top.pack(fill="x", padx=20, pady=(20, 8))
        ttk.Label(top, text="Promotional Codes & Discounts", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(top, text="＋ Add New Promotion",
                   command=self._promo_dialog).pack(side="right")

        with self.app.db_session():
            promos = Promotion.query.order_by(Promotion.start_date.desc()).all()

        cols = ("id", "code", "type", "value", "min_order", "usage", "active")
        container, tree = make_treeview_with_scrollbar(
            self.content, columns=cols,
            headings=["ID", "Promo Code", "Type", "Discount Value", "Min Spend", "Redemptions", "Active"],
            widths=[45, 140, 95, 110, 95, 95, 65], height=14
        )
        for i, p in enumerate(promos):
            val = f"{p.discount_value}%" if p.discount_type == "percentage" else f"₱{p.discount_value:,.0f}"
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=(p.id, p.code, p.discount_type.title(), val,
                                           f"₱{p.min_order_value:,.0f}", f"{p.usage_count}/{p.usage_limit or '∞'}",
                                           "Yes" if p.is_active else "No"), tags=(tag,))
        container.pack(fill="both", expand=True, padx=20, pady=8)
        tree.bind("<Double-1>", lambda e: self._open(tree))

        ttk.Label(self.content, text="💡 Double-click any promo code to adjust discount rates, validity dates, or usage limits.",
                  style="Muted.TLabel", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(4, 16))

    def _open(self, tree):
        sel = tree.selection()
        if sel:
            pid = tree.item(sel[0])["values"][0]
            self._promo_dialog(int(pid))

    def _promo_dialog(self, pid=None):
        with self.app.db_session():
            promo = Promotion.query.get(pid) if pid else None
            top = tk.Toplevel(self)
            top.title("Edit Promotion" if promo else "Add Promotion")
            top.geometry("480x560")
            top.transient(self)
            top.grab_set()
            theme.configure_toplevel(top, 480, 560)

            ttk.Label(top, text="Promotion Details", font=("Segoe UI", 12, "bold")).pack(pady=(16, 6), padx=20, anchor="w")

            fields = {}
            for label, key in [("Promo Code *", "code"), ("Description", "description"),
                               ("Discount Value *", "discount_value"), ("Minimum Spend (₱)", "min_order_value"),
                               ("Max Discount Cap (₱)", "max_discount_amount"), ("Usage Limit (Count)", "usage_limit"),
                               ("Start Date (YYYY-MM-DD) *", "start_date"), ("End Date (YYYY-MM-DD) *", "end_date")]:
                ttk.Label(top, text=label, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(3, 1))
                e = ttk.Entry(top, width=40)
                if promo and getattr(promo, key) is not None:
                    val = getattr(promo, key)
                    if hasattr(val, "strftime"):
                        val = val.strftime("%Y-%m-%d")
                    e.insert(0, str(val))
                elif not promo:
                    if key == "start_date":
                        e.insert(0, date.today().strftime("%Y-%m-%d"))
                    elif key == "end_date":
                        e.insert(0, (date.today() + timedelta(days=30)).strftime("%Y-%m-%d"))
                e.pack(fill="x", padx=20)
                fields[key] = e

            type_var = tk.StringVar(value=promo.discount_type if promo else "percentage")
            ttk.Label(top, text="Discount Type *", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(5, 1))
            ttk.Combobox(top, textvariable=type_var, values=["percentage", "fixed"], state="readonly").pack(fill="x", padx=20)

            active_var = tk.BooleanVar(value=promo.is_active if promo else True)
            ttk.Checkbutton(top, text="Promotion is Active", variable=active_var).pack(anchor="w", padx=20, pady=8)

            def save():
                try:
                    data = {
                        "code": fields["code"].get().strip().upper(),
                        "description": fields["description"].get().strip(),
                        "discount_type": type_var.get(),
                        "discount_value": Decimal(fields["discount_value"].get() or "0"),
                        "min_order_value": Decimal(fields["min_order_value"].get() or "0"),
                        "max_discount_amount": Decimal(fields["max_discount_amount"].get()) if fields["max_discount_amount"].get().strip() else None,
                        "usage_limit": int(fields["usage_limit"].get()) if fields["usage_limit"].get().strip() else None,
                        "start_date": datetime.strptime(fields["start_date"].get(), "%Y-%m-%d"),
                        "end_date": datetime.strptime(fields["end_date"].get(), "%Y-%m-%d"),
                        "is_active": active_var.get(),
                    }
                except ValueError:
                    messagebox.showerror("Invalid Input", "Please check all numeric values and ensure dates follow YYYY-MM-DD.")
                    return
                if not data["code"] or data["discount_value"] <= 0:
                    messagebox.showerror("Invalid Input", "Code and a positive discount value are required.")
                    return
                with self.app.db_session():
                    if promo:
                        p = Promotion.query.get(promo.id)
                        for k, v in data.items():
                            setattr(p, k, v)
                    else:
                        existing = Promotion.query.filter_by(code=data["code"]).first()
                        if existing:
                            messagebox.showerror("Duplicate", "A promo with this code already exists.")
                            return
                        db.session.add(Promotion(**data))
                    db.session.commit()
                top.destroy()
                self.flash("Promotion saved successfully.", "success")
                self.on_show()

            btn_row = ttk.Frame(top)
            btn_row.pack(pady=14, padx=20, fill="x")
            ttk.Button(btn_row, text="Save Promotion", command=save).pack(side="left")
            ttk.Button(btn_row, text="Cancel", style="Secondary.TButton", command=top.destroy).pack(side="right")


class AdminUsers(_AdminFrame):
    def build(self):
        pass

    def on_show(self, **kwargs):
        self._layout("Customers")
        if not self._check_admin():
            return
        self._render()

    def _render(self):
        top = ttk.Frame(self.content)
        top.pack(fill="x", padx=20, pady=(20, 8))
        ttk.Label(top, text="Customer Accounts", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(side="left")

        with self.app.db_session():
            customers = CustomerProfile.query.filter_by(is_archived=False).all()

        cols = ("id", "name", "email", "phone", "bookings")
        container, tree = make_treeview_with_scrollbar(
            self.content, columns=cols,
            headings=["ID", "Customer Name", "Email Address", "Phone Number", "Total Bookings"],
            widths=[45, 180, 220, 130, 90], height=16
        )
        for i, cp in enumerate(customers):
            count = Booking.query.filter_by(customer_id=cp.id).count()
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=(cp.id, f"{cp.first_name} {cp.last_name}",
                                           cp.user.email, cp.phone or "—", count), tags=(tag,))
        container.pack(fill="both", expand=True, padx=20, pady=8)


class AdminSettings(_AdminFrame):
    def build(self):
        pass

    def on_show(self, **kwargs):
        self._layout("Settings")
        if not self._check_admin():
            return
        top = ttk.Frame(self.content)
        top.pack(fill="x", padx=20, pady=(20, 8))
        ttk.Label(top, text="Business & Service Settings", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(side="left")

        with self.app.db_session():
            settings_map = {s.key: s.value for s in BusinessSettings.query.all()}

        card = theme.make_card(self.content)
        card.pack(fill="x", padx=20, pady=8)
        body = theme.make_inner(card)
        body.pack(fill="x", padx=24, pady=20)
        body.grid_columnconfigure(1, weight=1)

        field_defs = [
            ("Business / Brand Name", "business_name", "CleanHome PH"),
            ("Support Contact Email", "contact_email", "support@cleanhome.ph"),
            ("Hotline Phone Number", "contact_phone", "+63 2 8123 4567"),
            ("Operating Hours", "operating_hours", "Mon - Sun: 7:00 AM - 8:00 PM"),
            ("Office Address", "address", "Makati City, Metro Manila"),
            ("Covered Service Areas", "service_areas", "Makati, BGC, Taguig, Pasig, Mandaluyong, Quezon City"),
        ]
        fields = {}
        for i, (label, key, def_val) in enumerate(field_defs):
            ttk.Label(body, text=label, style="Surface.TLabel",
                      font=("Segoe UI", 9, "bold")).grid(row=i, column=0, sticky="w", pady=6)
            e = ttk.Entry(body)
            val = settings_map.get(key, "") or def_val
            e.insert(0, val)
            e.grid(row=i, column=1, sticky="ew", padx=12, pady=6)
            fields[key] = e

        def save():
            data = {k: v.get().strip() for k, v in fields.items()}
            with self.app.db_session():
                for k, v in data.items():
                    row = BusinessSettings.query.filter_by(key=k).first()
                    if row:
                        row.value = v
                    else:
                        db.session.add(BusinessSettings(key=k, value=v))
                db.session.commit()
            self.flash("Business settings updated successfully.", "success")

        btn_row = ttk.Frame(body, style="Surface.TFrame")
        btn_row.grid(row=len(fields), column=0, columnspan=2, sticky="w", pady=(16, 0))
        ttk.Button(btn_row, text="Save Settings", command=save).pack(side="left")

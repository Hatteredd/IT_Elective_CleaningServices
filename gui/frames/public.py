"""Public (unauthenticated) frames: Home, Services, Service Detail, About, Contact, Promotions."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone

from gui.app import BaseFrame
from gui import theme
from gui.theme import ScrollableFrame
from app import db
from app.models import Service, Promotion, Inquiry


PAD = theme.SPACE_LG  # Consistent page horizontal padding


class _PublicHeader(BaseFrame):
    """Shared top nav for public pages."""

    def build(self, active="Home"):
        bar = tk.Frame(self, bg=theme.SURFACE, highlightbackground=theme.BORDER,
                       highlightthickness=1, bd=0)
        bar.pack(fill="x", pady=(0, theme.SPACE_MD))

        # Brand Logo / Title
        brand_frame = tk.Frame(bar, bg=theme.SURFACE)
        brand_frame.pack(side="left", padx=PAD, pady=12)

        tk.Label(brand_frame, text="✨ CleanHome PH", bg=theme.SURFACE,
                 font=("Segoe UI", 16, "bold"), fg=theme.PRIMARY).pack(side="left")

        # Location status chip
        loc_chip = tk.Label(brand_frame, text="● Metro Manila", bg="#ECFDF5", fg="#059669",
                            font=("Segoe UI", 8, "bold"), padx=8, pady=3)
        loc_chip.pack(side="left", padx=(10, 0))

        # Nav Links
        nav = tk.Frame(bar, bg=theme.SURFACE)
        nav.pack(side="left", padx=theme.SPACE_LG)
        for label, target in [("Home", "Home"), ("Services", "Services"),
                              ("Promotions", "Promotions"), ("About", "About"),
                              ("Contact", "Contact")]:
            is_cur = (label == active)
            btn = tk.Button(nav, text=label, relief="flat",
                            bg=theme.PRIMARY_LIGHT if is_cur else theme.SURFACE,
                            fg=theme.PRIMARY if is_cur else theme.TEXT,
                            font=("Segoe UI", 10, "bold" if is_cur else "normal"),
                            padx=14, pady=6, cursor="hand2", bd=0,
                            activebackground=theme.PRIMARY_LIGHT,
                            activeforeground=theme.PRIMARY,
                            command=lambda t=target: self.go(t))
            btn.pack(side="left", padx=theme.SPACE_XS)

        # Auth Controls
        auth = tk.Frame(bar, bg=theme.SURFACE)
        auth.pack(side="right", padx=PAD)
        if self.session.is_authenticated:
            if self.session.user.role == "admin":
                name = "Admin"
                target_dash = "AdminDashboard"
            else:
                profile = self.session.user.customer_profile
                name = profile.first_name if profile else "Customer"
                target_dash = "CustomerDashboard"

            tk.Label(auth, text=f"👤 {name}", bg=theme.SURFACE_ALT, fg=theme.TEXT,
                     font=("Segoe UI", 9, "bold"), padx=10, pady=5).pack(side="left", padx=(0, theme.SPACE_SM))
            ttk.Button(auth, text="Dashboard", style="Secondary.TButton",
                       command=lambda: self.go(target_dash)).pack(side="left", padx=theme.SPACE_XS)
            ttk.Button(auth, text="Logout", style="Secondary.TButton",
                       command=self.app.logout).pack(side="left", padx=theme.SPACE_XS)
        else:
            login_btn = tk.Button(auth, text="Log In", relief="flat",
                                  bg=theme.SURFACE_ALT, fg=theme.TEXT,
                                  font=("Segoe UI", 9, "bold"), padx=14, pady=6, cursor="hand2", bd=0,
                                  activebackground=theme.BORDER,
                                  command=lambda: self.go("Login"))
            login_btn.pack(side="left", padx=theme.SPACE_XS)

            signup_btn = tk.Button(auth, text="✨ Sign Up Free", relief="flat",
                                   bg=theme.PRIMARY, fg="#FFFFFF",
                                   font=("Segoe UI", 9, "bold"), padx=14, pady=6, cursor="hand2", bd=0,
                                   activebackground=theme.PRIMARY_DARK, activeforeground="#FFFFFF",
                                   command=lambda: self.go("Register"))
            signup_btn.pack(side="left", padx=theme.SPACE_XS)


class Home(_PublicHeader):
    def build(self):
        super().build("Home")
        with self.app.db_session():
            services = Service.query.filter_by(is_active=True, is_archived=False).limit(3).all()
            now = datetime.now(timezone.utc)
            promotions = Promotion.query.filter_by(is_active=True).filter(
                Promotion.end_date >= now
            ).limit(3).all()

        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        body = scroll.inner

        # ── Hero Section ──────────────────────────────────────────────────────
        hero_card = tk.Frame(body, bg="#0F172A", highlightbackground=theme.BORDER,
                             highlightthickness=0, bd=0)
        hero_card.pack(fill="x", padx=PAD, pady=(theme.SPACE_XS, theme.SPACE_MD))
        hero_inner = tk.Frame(hero_card, bg="#0F172A", padx=32, pady=32)
        hero_inner.pack(fill="x")

        # Eyebrow Tag
        eyebrow = tk.Label(hero_inner, text="✨ PHILIPPINES' #1 RATED HOME CLEANING SERVICE",
                           bg="#1E293B", fg="#2DD4BF", font=("Segoe UI", 8, "bold"),
                           padx=10, pady=4)
        eyebrow.pack(anchor="w", pady=(0, 10))

        # Hero Title
        tk.Label(hero_inner, text="Spotless Living, Zero Effort.",
                 bg="#0F172A", fg="#FFFFFF",
                 font=("Segoe UI", 26, "bold")).pack(anchor="w", pady=(0, 6))

        # Hero Subtitle
        tk.Label(hero_inner, text="Book vetted, 5-star professional cleaners across Metro Manila in 60 seconds. Hospital-grade supplies, transparent upfront pricing, and guaranteed satisfaction.",
                 bg="#0F172A", fg="#94A3B8",
                 font=("Segoe UI", 11), wraplength=760, justify="left").pack(anchor="w", pady=(0, 20))

        # Action Buttons
        btn_row = tk.Frame(hero_inner, bg="#0F172A")
        btn_row.pack(anchor="w", pady=(0, 24))

        def _book():
            if self.session.require_customer():
                self.go("BookService")
            elif self.session.require_admin():
                self.go("AdminDashboard")
            else:
                self.go("Login")

        book_cta = tk.Button(btn_row, text="✨ Book a Cleaning Now →", relief="flat",
                             bg=theme.PRIMARY, fg="#FFFFFF",
                             font=("Segoe UI", 11, "bold"), padx=20, pady=10, cursor="hand2", bd=0,
                             activebackground=theme.PRIMARY_DARK, activeforeground="#FFFFFF",
                             command=_book)
        book_cta.pack(side="left", padx=(0, theme.SPACE_MD))

        browse_cta = tk.Button(btn_row, text="Browse All Services", relief="flat",
                               bg="#1E293B", fg="#F8FAFC",
                               font=("Segoe UI", 10, "bold"), padx=16, pady=10, cursor="hand2", bd=0,
                               activebackground="#334155", activeforeground="#FFFFFF",
                               command=lambda: self.go("Services"))
        browse_cta.pack(side="left")

        # Value propositions inside hero
        props_bar = tk.Frame(hero_inner, bg="#0F172A")
        props_bar.pack(anchor="w", fill="x")
        for prop in ["🛡️ 100% Background-Checked Staff", "⚡ Same-Day Slots Available",
                     "💵 Cash & E-Wallet (GCash/Maya)", "⭐ 4.9/5 Rating (15k+ Cleanings)"]:
            pill = tk.Label(props_bar, text=prop, bg="#1E293B", fg="#CBD5E1",
                            font=("Segoe UI", 8, "bold"), padx=10, pady=4)
            pill.pack(side="left", padx=(0, theme.SPACE_SM))

        # ── Trust Metrics Strip ───────────────────────────────────────────────
        metrics_grid = ttk.Frame(body)
        metrics_grid.pack(fill="x", padx=PAD, pady=(0, theme.SPACE_LG))
        trust_stats = [
            ("Homes Cleaned", "15,000+", "Verified completed jobs", "🏡", "#F0FDFA", theme.PRIMARY),
            ("Customer Rating", "4.9 / 5.0", "Based on 3,400+ reviews", "⭐", "#FEF3C7", "#D97706"),
            ("Vetted Staff", "100%", "Police & health checked", "🛡️", "#F0FDF4", theme.SUCCESS),
            ("Cities Covered", "12 Cities", "Active in Metro Manila", "📍", "#EFF6FF", theme.INFO),
        ]
        for i, (title, val, sub, ic, bg_c, fg_c) in enumerate(trust_stats):
            sc = theme.make_stat_card(metrics_grid, title, val, subtitle=sub,
                                      icon=ic, icon_bg=bg_c, icon_fg=fg_c)
            sc.grid(row=0, column=i, padx=theme.SPACE_XS, sticky="nsew")
            metrics_grid.grid_columnconfigure(i, weight=1)

        # ── Featured Services ─────────────────────────────────────────────────
        sec_head = ttk.Frame(body)
        sec_head.pack(fill="x", padx=PAD, pady=(theme.SPACE_MD, theme.SPACE_SM))
        head_left = ttk.Frame(sec_head)
        head_left.pack(side="left")
        ttk.Label(head_left, text="Featured Cleaning Services", style="Heading.TLabel",
                  font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(head_left, text="Handpicked packages tailored for condominiums, townhouses, and family homes.",
                  style="Muted.TLabel", font=("Segoe UI", 9)).pack(anchor="w")
        ttk.Button(sec_head, text="View All Services →", style="Secondary.TButton",
                   command=lambda: self.go("Services")).pack(side="right")

        grid = ttk.Frame(body)
        grid.pack(fill="x", padx=PAD, pady=(0, theme.SPACE_MD))
        for i, svc in enumerate(services):
            card = theme.make_card(grid)
            card.grid(row=0, column=i, padx=theme.SPACE_SM, sticky="nsew")
            grid.grid_columnconfigure(i, weight=1)

            card_inner = theme.make_inner(card)
            card_inner.pack(fill="both", expand=True, padx=theme.SPACE_LG, pady=theme.SPACE_LG)

            # Badge pill
            badge_text = "⭐ MOST POPULAR" if i == 0 else "✨ SIGNATURE SERVICE"
            badge = tk.Label(card_inner, text=badge_text, bg="#F0FDFA", fg=theme.PRIMARY,
                             font=("Segoe UI", 8, "bold"), padx=8, pady=3)
            badge.pack(anchor="w", pady=(0, theme.SPACE_SM))

            ttk.Label(card_inner, text=svc.name, style="Surface.TLabel",
                      font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, theme.SPACE_XS))

            price = svc.discounted_price if (svc.discounted_price and svc.discounted_price < svc.base_price) else svc.base_price
            price_row = ttk.Frame(card_inner, style="Surface.TFrame")
            price_row.pack(anchor="w", pady=(0, theme.SPACE_SM))
            ttk.Label(price_row, text=f"₱{price:,.0f}", background=theme.SURFACE,
                      foreground=theme.PRIMARY, font=("Segoe UI", 16, "bold")).pack(side="left")
            if svc.duration_minutes:
                ttk.Label(price_row, text=f" • ⏱️ {svc.duration_minutes} mins", style="Surface.Muted.TLabel",
                          font=("Segoe UI", 9)).pack(side="left", padx=(4, 0))

            desc_text = (svc.description or "Professional cleaning service.")
            if len(desc_text) > 110:
                desc_text = desc_text[:107] + "..."
            ttk.Label(card_inner, text=desc_text, style="Surface.Muted.TLabel",
                      wraplength=240, justify="left").pack(anchor="w", pady=(0, theme.SPACE_LG))

            btn_box = ttk.Frame(card_inner, style="Surface.TFrame")
            btn_box.pack(anchor="w", fill="x")
            ttk.Button(btn_box, text="Details", style="Secondary.TButton",
                       command=lambda s=svc.id: self.go("ServiceDetail", service_id=s)).pack(side="left", padx=(0, theme.SPACE_XS))
            ttk.Button(btn_box, text="Book Now",
                       command=lambda s=svc.id: self.go("BookService" if self.session.require_customer() else "Login", service_id=s)).pack(side="left")

        # ── Active Promotions ─────────────────────────────────────────────────
        if promotions:
            p_head = ttk.Frame(body)
            p_head.pack(fill="x", padx=PAD, pady=(theme.SPACE_LG, theme.SPACE_SM))
            p_head_left = ttk.Frame(p_head)
            p_head_left.pack(side="left")
            ttk.Label(p_head_left, text="Special Offers & Vouchers", style="Heading.TLabel",
                      font=("Segoe UI", 16, "bold")).pack(anchor="w")
            ttk.Label(p_head_left, text="Apply these coupon codes during checkout for instant savings.",
                      style="Muted.TLabel", font=("Segoe UI", 9)).pack(anchor="w")
            ttk.Button(p_head, text="All Promotions →", style="Secondary.TButton",
                       command=lambda: self.go("Promotions")).pack(side="right")

            pgrid = ttk.Frame(body)
            pgrid.pack(fill="x", padx=PAD, pady=(0, theme.SPACE_LG))
            for i, promo in enumerate(promotions):
                card = tk.Frame(pgrid, bg=theme.SURFACE, highlightbackground=theme.PRIMARY_BORDER,
                                highlightthickness=1, bd=0)
                card.grid(row=0, column=i, padx=theme.SPACE_SM, sticky="nsew")
                pgrid.grid_columnconfigure(i, weight=1)

                inner = tk.Frame(card, bg=theme.SURFACE, padx=18, pady=16)
                inner.pack(fill="both", expand=True)

                code_tag = tk.Label(inner, text=f"🏷 {promo.code}", bg="#E6F9F1", fg="#0F766E",
                                    font=("Segoe UI", 11, "bold"), padx=10, pady=4)
                code_tag.pack(anchor="w", pady=(0, theme.SPACE_XS))

                disc = (f"{promo.discount_value}% OFF" if promo.discount_type == "percentage"
                        else f"₱{promo.discount_value:,.0f} OFF")
                ttk.Label(inner, text=disc, background=theme.SURFACE,
                          foreground=theme.SECONDARY, font=("Segoe UI", 15, "bold")).pack(anchor="w")

                ttk.Label(inner, text=promo.description or "Limited time discount offer.",
                          background=theme.SURFACE, foreground=theme.TEXT_MUTED,
                          wraplength=240, justify="left").pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_SM))

        # ── Why Choose CleanHome PH Guarantee Cards ───────────────────────────
        g_head = ttk.Frame(body)
        g_head.pack(fill="x", padx=PAD, pady=(theme.SPACE_LG, theme.SPACE_SM))
        ttk.Label(g_head, text="Why Metro Manila Trusts CleanHome PH", style="Heading.TLabel",
                  font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(g_head, text="Built on trust, safety, and hospital-grade standards for your peace of mind.",
                  style="Muted.TLabel", font=("Segoe UI", 9)).pack(anchor="w")

        guarantees = [
            ("🛡️ Vetted & Insured", "Every cleaner undergoes 5-step screening, NBI verification, and comprehensive training."),
            ("⚡ 60-Second Booking", "Real-time calendar booking with instant confirmation. Zero phone tags or hassle."),
            ("🧼 Hospital-Grade Supplies", "Eco-friendly, child and pet-safe products that sanitize without harsh chemical residue."),
            ("💯 100% Happiness Guarantee", "If you're not completely satisfied with any area, our team will re-clean it free."),
        ]
        g_grid = ttk.Frame(body)
        g_grid.pack(fill="x", padx=PAD, pady=(0, theme.SPACE_XL))
        for i, (title, desc) in enumerate(guarantees):
            g_card = theme.make_card(g_grid)
            g_card.grid(row=0, column=i, padx=theme.SPACE_XS, sticky="nsew")
            g_grid.grid_columnconfigure(i, weight=1)

            g_inner = theme.make_inner(g_card)
            g_inner.pack(fill="both", expand=True, padx=theme.SPACE_LG, pady=theme.SPACE_LG)

            ttk.Label(g_inner, text=title, style="Surface.TLabel",
                      font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, theme.SPACE_XS))
            ttk.Label(g_inner, text=desc, style="Surface.Muted.TLabel",
                      font=("Segoe UI", 9), wraplength=180, justify="left").pack(anchor="w")

        # ── Bottom CTA Banner ─────────────────────────────────────────────────
        cta_card = theme.make_card(body)
        cta_card.pack(fill="x", padx=PAD, pady=(0, theme.SPACE_2XL))
        cta_inner = theme.make_inner(cta_card)
        cta_inner.pack(fill="x", padx=theme.SPACE_2XL, pady=theme.SPACE_XL)

        cta_left = ttk.Frame(cta_inner, style="Surface.TFrame")
        cta_left.pack(side="left")
        ttk.Label(cta_left, text="Ready for a sparkling clean home?", style="Surface.TLabel",
                  font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(cta_left, text="Join thousands of delighted homeowners and condo dwellers across Metro Manila.",
                  style="Surface.Muted.TLabel", font=("Segoe UI", 10)).pack(anchor="w")

        ttk.Button(cta_inner, text="✨ Book Your Cleaning Now", command=_book).pack(side="right")


class Services(_PublicHeader):
    def build(self):
        super().build("Services")
        with self.app.db_session():
            services = Service.query.filter_by(is_active=True, is_archived=False).order_by(Service.base_price).all()

        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        body = scroll.inner

        top_row = ttk.Frame(body)
        top_row.pack(fill="x", padx=PAD, pady=(theme.SPACE_SM, theme.SPACE_MD))
        ttk.Label(top_row, text="All Cleaning Services", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Label(top_row, text=f"{len(services)} services available", style="Muted.TLabel",
                  font=("Segoe UI", 10)).pack(side="right")

        for svc in services:
            card = theme.make_card(body)
            card.pack(fill="x", padx=PAD, pady=theme.SPACE_SM)
            inner = theme.make_inner(card)
            inner.pack(fill="x", padx=theme.SPACE_XL, pady=theme.SPACE_LG)

            left = ttk.Frame(inner, style="Surface.TFrame")
            left.pack(side="left", fill="both", expand=True)

            ttk.Label(left, text=svc.name, style="Surface.TLabel",
                      font=("Segoe UI", 14, "bold")).pack(anchor="w")

            meta_row = ttk.Frame(left, style="Surface.TFrame")
            meta_row.pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_SM))

            price = svc.discounted_price if (svc.discounted_price and svc.discounted_price < svc.base_price) else svc.base_price
            ttk.Label(meta_row, text=f"₱{price:,.0f}", background=theme.SURFACE,
                      foreground=theme.PRIMARY, font=("Segoe UI", 14, "bold")).pack(side="left")

            if svc.discounted_price and svc.discounted_price < svc.base_price:
                ttk.Label(meta_row, text=f"  (Orig: ₱{svc.base_price:,.0f})",
                          style="Surface.Muted.TLabel").pack(side="left")

            ttk.Label(meta_row, text=f"  •  ⏱ {svc.duration_minutes} mins",
                      style="Surface.Muted.TLabel").pack(side="left")

            if svc.add_ons:
                active_addons = [a for a in svc.add_ons if a.is_active]
                if active_addons:
                    ttk.Label(meta_row, text=f"  •  {len(active_addons)} add-ons available",
                              style="Surface.Muted.TLabel").pack(side="left")

            ttk.Label(left, text=svc.description or "", style="Surface.Muted.TLabel",
                      wraplength=650, justify="left").pack(anchor="w")

            right = ttk.Frame(inner, style="Surface.TFrame")
            right.pack(side="right", padx=(theme.SPACE_LG, 0))

            ttk.Button(right, text="View Details", style="Secondary.TButton",
                       command=lambda s=svc.id: self.go("ServiceDetail", service_id=s)).pack(fill="x", pady=(0, theme.SPACE_XS))
            ttk.Button(right, text="Book Now",
                       command=lambda s=svc.id: self.go("BookService" if self.session.require_customer() else "Login", service_id=s)).pack(fill="x")


class ServiceDetail(_PublicHeader):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.service_id = None

    def on_show(self, service_id=None, **kwargs):
        self.service_id = service_id
        self.refresh()

    def build(self):
        super().build("Services")
        if not self.service_id:
            with self.app.db_session():
                first_svc = Service.query.filter_by(is_active=True, is_archived=False).first()
                if first_svc:
                    self.service_id = first_svc.id

        if not self.service_id:
            ttk.Label(self, text="No service selected.", style="Muted.TLabel").pack(padx=PAD, pady=PAD)
            return

        with self.app.db_session():
            svc = Service.query.get(self.service_id)
            if not svc:
                ttk.Label(self, text="Service not found.", style="Muted.TLabel").pack(padx=PAD, pady=PAD)
                return
            add_ons = [a for a in svc.add_ons if a.is_active]

        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        body = scroll.inner

        # Back link
        back_btn = ttk.Button(body, text="← Back to All Services", style="Secondary.TButton",
                              command=lambda: self.go("Services"))
        back_btn.pack(anchor="w", padx=PAD, pady=(theme.SPACE_SM, theme.SPACE_MD))

        # Main service detail card
        card = theme.make_card(body)
        card.pack(fill="x", padx=PAD, pady=theme.SPACE_SM)
        inner = theme.make_inner(card)
        inner.pack(fill="x", padx=theme.SPACE_2XL, pady=theme.SPACE_XL)

        ttk.Label(inner, text=svc.name, style="Surface.TLabel",
                  font=("Segoe UI", 22, "bold")).pack(anchor="w")

        price = svc.discounted_price if (svc.discounted_price and svc.discounted_price < svc.base_price) else svc.base_price
        p_row = ttk.Frame(inner, style="Surface.TFrame")
        p_row.pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_MD))
        ttk.Label(p_row, text=f"₱{price:,.0f}", background=theme.SURFACE,
                  foreground=theme.PRIMARY, font=("Segoe UI", 20, "bold")).pack(side="left")
        if svc.discounted_price and svc.discounted_price < svc.base_price:
            ttk.Label(p_row, text=f"  Regular Price: ₱{svc.base_price:,.0f}",
                      style="Surface.Muted.TLabel").pack(side="left")
        ttk.Label(p_row, text=f"  •  Duration: ~{svc.duration_minutes} minutes",
                  style="Surface.TLabel").pack(side="left")

        ttk.Label(inner, text=svc.description or "", style="Surface.Muted.TLabel",
                  font=("Segoe UI", 11), wraplength=720, justify="left").pack(anchor="w", pady=(0, theme.SPACE_LG))

        if add_ons:
            ttk.Label(inner, text="Available Service Add-ons", style="Surface.TLabel",
                      font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(theme.SPACE_MD, theme.SPACE_SM))
            for ao in add_ons:
                ao_frame = tk.Frame(inner, bg=theme.SURFACE_ALT, padx=12, pady=8,
                                    highlightbackground=theme.BORDER, highlightthickness=1)
                ao_frame.pack(fill="x", pady=theme.SPACE_XS)
                ttk.Label(ao_frame, text=f"➕ {ao.name}", background=theme.SURFACE_ALT,
                          font=("Segoe UI", 10, "bold")).pack(side="left")
                if ao.description:
                    ttk.Label(ao_frame, text=f" — {ao.description}", background=theme.SURFACE_ALT,
                              style="Muted.TLabel").pack(side="left", padx=4)
                ttk.Label(ao_frame, text=f"+₱{ao.price:,.0f}", background=theme.SURFACE_ALT,
                          foreground=theme.PRIMARY, font=("Segoe UI", 10, "bold")).pack(side="right")

        def _book():
            if self.session.require_customer():
                self.go("BookService", service_id=svc.id)
            else:
                self.go("Login")

        ttk.Button(inner, text="Book This Service Now", command=_book).pack(anchor="w", pady=(theme.SPACE_XL, theme.SPACE_SM))


class Promotions(_PublicHeader):
    def build(self):
        super().build("Promotions")
        with self.app.db_session():
            now = datetime.now(timezone.utc)
            promos = Promotion.query.filter_by(is_active=True).filter(
                Promotion.end_date >= now
            ).order_by(Promotion.end_date).all()

        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        body = scroll.inner

        ttk.Label(body, text="Active Promo Codes & Deals", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=PAD, pady=(theme.SPACE_SM, theme.SPACE_MD))

        if not promos:
            ttk.Label(body, text="No promotions active at this moment. Check back soon!",
                      style="Muted.TLabel").pack(padx=PAD, pady=PAD)
            return

        for promo in promos:
            card = theme.make_card(body)
            card.pack(fill="x", padx=PAD, pady=theme.SPACE_SM)
            inner = theme.make_inner(card)
            inner.pack(fill="x", padx=theme.SPACE_XL, pady=theme.SPACE_LG)

            top = ttk.Frame(inner, style="Surface.TFrame")
            top.pack(fill="x")

            code_lbl = tk.Label(top, text=f"🏷 {promo.code}", bg="#E8F4FD", fg=theme.PRIMARY,
                                font=("Segoe UI", 13, "bold"), padx=10, pady=4)
            code_lbl.pack(side="left")

            disc = (f"{promo.discount_value}% OFF" if promo.discount_type == "percentage"
                    else f"₱{promo.discount_value:,.0f} OFF")
            ttk.Label(top, text=disc, background=theme.SURFACE, foreground=theme.SUCCESS,
                      font=("Segoe UI", 13, "bold")).pack(side="left", padx=theme.SPACE_MD)

            end_str = promo.end_date.strftime("%B %d, %Y")
            ttk.Label(top, text=f"Expires {end_str}", style="Surface.Muted.TLabel").pack(side="right")

            if promo.description:
                ttk.Label(inner, text=promo.description, style="Surface.Muted.TLabel",
                          wraplength=700, justify="left").pack(anchor="w", pady=(theme.SPACE_SM, 0))

            rules = []
            if promo.min_order_value and promo.min_order_value > 0:
                rules.append(f"Min. spend: ₱{promo.min_order_value:,.0f}")
            if promo.max_discount_amount:
                rules.append(f"Max discount: ₱{promo.max_discount_amount:,.0f}")
            if promo.usage_limit:
                rules.append(f"{promo.usage_count}/{promo.usage_limit} redeemed")

            if rules:
                ttk.Label(inner, text=" • ".join(rules), style="Surface.Muted.TLabel",
                          font=("Segoe UI", 9)).pack(anchor="w", pady=(theme.SPACE_XS, 0))


class About(_PublicHeader):
    def build(self):
        super().build("About")

        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        body = scroll.inner

        ttk.Label(body, text="About CleanHome PH", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=PAD, pady=(theme.SPACE_SM, theme.SPACE_MD))

        card = theme.make_card(body)
        card.pack(fill="x", padx=PAD, pady=theme.SPACE_SM)
        inner = theme.make_inner(card)
        inner.pack(fill="x", padx=theme.SPACE_2XL, pady=theme.SPACE_XL)

        ttk.Label(inner, text="Who We Are", style="Surface.TLabel",
                  font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(0, theme.SPACE_SM))
        ttk.Label(inner, text=(
            "CleanHome PH is the premier professional home cleaning service platform in the Philippines. "
            "We match busy homeowners, condo dwellers, and businesses with vetted, reliable, and trained cleaning professionals. "
            "Our mission is to bring sparkling clean spaces and peace of mind to every Filipino household."
        ), style="Surface.Muted.TLabel", font=("Segoe UI", 11), wraplength=720, justify="left").pack(anchor="w", pady=(0, theme.SPACE_LG))

        # Core Values Grid
        ttk.Label(inner, text="Our Commitments", style="Surface.TLabel",
                  font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(theme.SPACE_MD, theme.SPACE_SM))

        v_grid = ttk.Frame(inner, style="Surface.TFrame")
        v_grid.pack(fill="x", pady=(0, theme.SPACE_LG))
        values = [
            ("🛡️ Trust & Security", "Every cleaner undergoes identity verification, background screening, and practical training."),
            ("💰 Transparent Pricing", "No hidden fees. Upfront prices and clear estimates before you confirm your booking."),
            ("⭐ Quality Guaranteed", "If you are not satisfied with the cleaning, our support team will make it right.")
        ]
        for i, (title, desc) in enumerate(values):
            box = tk.Frame(v_grid, bg=theme.SURFACE_ALT, padx=14, pady=12,
                           highlightbackground=theme.BORDER, highlightthickness=1)
            box.grid(row=0, column=i, padx=theme.SPACE_XS, sticky="nsew")
            v_grid.grid_columnconfigure(i, weight=1)
            ttk.Label(box, text=title, background=theme.SURFACE_ALT,
                      font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, theme.SPACE_XS))
            ttk.Label(box, text=desc, background=theme.SURFACE_ALT,
                      style="Muted.TLabel", wraplength=210, justify="left").pack(anchor="w")

        # Service coverage
        ttk.Label(inner, text="Service Coverage", style="Surface.TLabel",
                  font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(theme.SPACE_MD, theme.SPACE_SM))
        ttk.Label(inner, text=(
            "We proudly service Makati City, Taguig (BGC), Pasig (Ortigas), Mandaluyong, Quezon City, "
            "San Juan, City of Manila, Pasay, Parañaque, and Muntinlupa (Alabang)."
        ), style="Surface.Muted.TLabel", font=("Segoe UI", 11), wraplength=720, justify="left").pack(anchor="w")


class Contact(_PublicHeader):
    def build(self):
        super().build("Contact")

        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        body = scroll.inner

        ttk.Label(body, text="Contact CleanHome PH", style="Title.TLabel",
                  font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=PAD, pady=(theme.SPACE_SM, theme.SPACE_MD))

        container = ttk.Frame(body)
        container.pack(fill="x", padx=PAD, pady=theme.SPACE_SM)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=2)

        # Left Info Card
        info_card = theme.make_card(container)
        info_card.grid(row=0, column=0, sticky="nsew", padx=(0, theme.SPACE_MD))
        info_inner = theme.make_inner(info_card)
        info_inner.pack(fill="both", expand=True, padx=theme.SPACE_LG, pady=theme.SPACE_LG)

        ttk.Label(info_inner, text="Get In Touch", style="Surface.TLabel",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, theme.SPACE_MD))

        info_items = [
            ("📞 Phone", "+63 2 8123 4567 / 0917 123 4567"),
            ("✉️ Email", "support@cleanhome.ph"),
            ("⏰ Hours", "Mon - Sun: 7:00 AM - 8:00 PM"),
            ("📍 Office", "Unit 1204, Ayala Tower One, Makati City, Metro Manila")
        ]
        for label, val in info_items:
            ttk.Label(info_inner, text=label, style="Surface.TLabel",
                      font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(theme.SPACE_SM, 1))
            ttk.Label(info_inner, text=val, style="Surface.Muted.TLabel",
                      wraplength=220, justify="left").pack(anchor="w", pady=(0, theme.SPACE_XS))

        # Right Contact Form Card
        form_card = theme.make_card(container)
        form_card.grid(row=0, column=1, sticky="nsew")
        form_inner = theme.make_inner(form_card)
        form_inner.pack(fill="both", expand=True, padx=theme.SPACE_XL, pady=theme.SPACE_LG)

        ttk.Label(form_inner, text="Send us a Message", style="Surface.TLabel",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, theme.SPACE_MD))

        fields = {}
        for label, key in [("Your Name *", "name"), ("Email Address *", "email"),
                           ("Contact Phone", "phone"), ("Subject *", "subject")]:
            ttk.Label(form_inner, text=label, style="Surface.TLabel",
                      font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(theme.SPACE_SM, 2))
            e = ttk.Entry(form_inner)
            e.pack(anchor="w", fill="x")
            fields[key] = e

        ttk.Label(form_inner, text="Message *", style="Surface.TLabel",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(theme.SPACE_SM, 2))
        msg = tk.Text(form_inner, height=4, wrap="word", relief="solid", borderwidth=1,
                      bg=theme.SURFACE, fg=theme.TEXT, insertbackground=theme.TEXT)
        msg.pack(anchor="w", fill="x", pady=(0, theme.SPACE_MD))
        fields["message"] = msg

        def submit():
            data = {k: (v.get("1.0", "end").strip() if k == "message" else v.get().strip())
                    for k, v in fields.items()}
            if not data["name"] or not data["email"] or not data["subject"] or not data["message"]:
                self.flash("Please fill in all required fields (Name, Email, Subject, Message).", "error")
                return
            with self.app.db_session():
                inquiry = Inquiry(**data)
                db.session.add(inquiry)
                db.session.commit()
            self.flash("Your inquiry has been sent successfully! Our team will reply shortly.", "success")
            for k, v in fields.items():
                if k == "message":
                    v.delete("1.0", "end")
                else:
                    v.delete(0, "end")

        ttk.Button(form_inner, text="Submit Inquiry", command=submit).pack(anchor="w", pady=(theme.SPACE_SM, 0))

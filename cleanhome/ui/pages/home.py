"""The public home page."""

from __future__ import annotations

import tkinter as tk

from cleanhome import config, theme, utils
from cleanhome.services import catalog_service
from cleanhome.ui import components, templates


class Home(templates.PageTemplate):
    """Landing page: what we do, what it costs, and how to book."""

    page_name = "Home"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        hero = templates.card(body)
        hero.pack(fill="x")
        hero_inner = templates.card_body(hero)
        hero_inner.grid_columnconfigure(0, weight=3)
        hero_inner.grid_columnconfigure(1, weight=2)

        left = tk.Frame(hero_inner, bg=theme.BG_SURFACE)
        left.grid(row=0, column=0, sticky="nsew")
        components.HeroLabel(left, text="A cleaner home,\nwithout the hassle.",
                 justify="left").pack(anchor="w")
        components.BodyLabel(left,
                 text=f"{config.COMPANY_NAME} brings vetted cleaners to your door in "
                      f"{config.SERVICE_AREAS}. Book in under a minute, pay after the job "
                      "is done.",
                 wraplength=theme.WRAP_HERO, justify="left", surface=True).pack(anchor="w",
                                                      pady=(theme.SPACE_MD, 0))
        actions = tk.Frame(left, bg=theme.BG_SURFACE)
        actions.pack(anchor="w", pady=(theme.SPACE_LG, 0))
        components.PrimaryButton(actions, "Book a Cleaning",
                                 command=lambda: self.app.go("Book")).pack(side="left",
                                                                        padx=(0, theme.SPACE_SM))
        components.SecondaryButton(actions, "View Services",
                                   command=lambda: self.app.go("Services")).pack(side="left")

        facts = tk.Frame(hero_inner, bg=theme.BG_SURFACE)
        facts.grid(row=0, column=1, sticky="nsew", padx=(theme.SPACE_LG, 0))
        services = catalog_service.list_services()
        areas = [area.strip() for area in config.SERVICE_AREAS.split(",") if area.strip()]
        for label, value in (
            ("Services in the catalogue", str(len(services))),
            ("Cities we cover", str(len(areas))),
            ("Booking hours", utils.business_hours()),
            ("Free cancellation", f"up to {config.CANCEL_CUTOFF_HOURS} hours before"),
        ):
            row = tk.Frame(facts, bg=theme.BG_SURFACE)
            row.pack(fill="x", pady=theme.SPACE_SM)
            components.SubheadingLabel(row, text=value, width=theme.LABEL_WIDTH, anchor="w", surface=True).pack(side="left")
            components.CaptionLabel(row, text=label, wraplength=theme.WRAP_NARROW,
                     justify="left", surface=True).pack(side="left", fill="x", expand=True)

        promos = catalog_service.list_promotions(active_only=True)
        if promos:
            promo_section = templates.section(
                body, "Active promotions",
                "Book during a promotion and the discount is applied at checkout.")
            promo_row = tk.Frame(promo_section, bg=theme.BG_PAGE)
            promo_row.pack(fill="x")
            for column in range(min(len(promos), theme.CARD_COLUMNS)):
                promo_row.grid_columnconfigure(column, weight=1, uniform="promos")
            for index, promo in enumerate(promos[:theme.CARD_COLUMNS]):
                holder = tk.Frame(promo_row, bg=theme.BG_PAGE)
                holder.grid(row=0, column=index, sticky="nsew",
                            padx=(0 if index == 0 else theme.SPACE_SM, 0))
                components.PromoCard(
                    holder, promo,
                    on_book=lambda p=promo: self.app.go("Book",
                                                       service_id=p.get("service_id")),
                ).pack(fill="both", expand=True)

        services_section = templates.section(
            body, "Popular services",
            "Every service includes our own supplies, a background-checked cleaner, "
            "and a satisfaction promise.")
        row = tk.Frame(services_section, bg=theme.BG_PAGE)
        row.pack(fill="x")
        for column in range(theme.CARD_COLUMNS):
            row.grid_columnconfigure(column, weight=1, uniform="cards")
        featured = catalog_service.featured_services()
        for index, service in enumerate(featured):
            holder = tk.Frame(row, bg=theme.BG_PAGE)
            holder.grid(row=0, column=index, sticky="nsew",
                        padx=(0 if index == 0 else theme.SPACE_SM, 0))
            components.ServiceCard(
                holder, service,
                on_book=lambda s=service: self.app.go("Book", service_id=s["id"]),
                on_details=lambda s=service: self.app.go("ServiceDetails", service_id=s["id"]),
                featured=index == 0,
            ).pack(fill="both", expand=True)

        why = templates.section(body, "Why CleanHome",
                                "What you can expect every time we visit.")
        why_row = tk.Frame(why, bg=theme.BG_PAGE)
        why_row.pack(fill="x")
        for column in range(theme.CARD_COLUMNS):
            why_row.grid_columnconfigure(column, weight=1, uniform="why")
        for index, (icon, title, text) in enumerate((
            (components.ShieldIcon, "Vetted cleaners",
             "Every cleaner is background-checked and trained before the first booking."),
            (components.ClockIcon, "Booked in a minute",
             "Pick a service, pick a slot, and pay after the job is done."),
            (components.SparkleIcon, "Supplies included",
             "Your cleaner arrives with everything needed — nothing for you to buy."),
        )):
            cell = tk.Frame(why_row, bg=theme.BG_PAGE)
            cell.grid(row=0, column=index, sticky="nsew",
                      padx=(0 if index == 0 else theme.SPACE_MD, 0))
            icon(cell, bg=theme.BG_PAGE).pack(anchor="w")
            components.SubheadingLabel(cell, text=title, surface=False).pack(anchor="w",
                                                                             pady=(theme.SPACE_SM, 0))
            components.BodyLabel(cell, text=text, wraplength=theme.WRAP_NARROW,
                                 justify="left", surface=False).pack(anchor="w",
                                                                   pady=(theme.SPACE_XS, 0))

        steps = templates.section(body, "How it works",
                                  "Three steps from booking to a spotless home.")
        step_row = tk.Frame(steps, bg=theme.BG_PAGE)
        step_row.pack(fill="x")
        for column in range(theme.CARD_COLUMNS):
            step_row.grid_columnconfigure(column, weight=1, uniform="steps")
        for index, (title, text) in enumerate((
            ("1. Pick a service", "Choose what you need and see the price before you commit."),
            ("2. Choose a time", f"Book any open slot from {utils.business_hours()}, up to "
                                  f"{config.BOOKING_WINDOW_DAYS} days ahead."),
            ("3. Come home clean", "Your cleaner arrives with supplies and confirms when the job is done."),
        )):
            step = tk.Frame(step_row, bg=theme.BG_PAGE)
            step.grid(row=0, column=index, sticky="nsew",
                      padx=(0 if index == 0 else theme.SPACE_MD, 0))
            components.SubheadingLabel(step, text=title, surface=False).pack(anchor="w")
            components.BodyLabel(step, text=text, wraplength=theme.WRAP_COLUMN,
                     justify="left", surface=False).pack(anchor="w", pady=(theme.SPACE_XS, 0))

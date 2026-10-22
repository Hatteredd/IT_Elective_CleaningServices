"""Full details for one service."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime

from cleanhome import theme, utils
from cleanhome.services import catalog_service
from cleanhome.ui import components, templates


class ServiceDetails(templates.PageTemplate):
    """A single service: description, price, duration, and any promotion."""

    page_name = "Services"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        service_id = kwargs.get("service_id")
        service = catalog_service.get_service(service_id) if service_id else None
        if service is None:
            components.HeadingLabel(body, text="Service not found").pack(anchor="w")
            components.BodyLabel(body, text="That service is no longer in the catalogue."
                                 ).pack(anchor="w", pady=(theme.SPACE_XS, 0))
            components.SecondaryButton(body, "Back to Services",
                                       command=lambda: self.app.go("Services")
                                       ).pack(anchor="w", pady=(theme.SPACE_MD, 0))
            return

        card = templates.card(body)
        card.pack(fill="x")
        inner = templates.card_body(card)

        components.SubheadingLabel(inner, text=service["name"], surface=True).pack(anchor="w")
        components.PriceLabel(inner, text=utils.format_peso(service["price"]),
                              surface=True).pack(anchor="w", pady=(theme.SPACE_XS, 0))
        components.CaptionLabel(inner, text=f"{service['duration_mins']} minutes",
                                 surface=True).pack(anchor="w")
        if service.get("description"):
            components.BodyLabel(inner, text=service["description"],
                                 wraplength=theme.WRAP_SECTION,
                                 justify="left", surface=True).pack(anchor="w",
                                                                  pady=(theme.SPACE_MD, 0))

        promo = catalog_service.applicable_promotion(service["id"], datetime.now())
        if promo:
            promo_row = tk.Frame(inner, bg=theme.BG_SURFACE)
            promo_row.pack(anchor="w", fill="x", pady=(0, theme.SPACE_MD))
            components.SubheadingLabel(promo_row, text=promo["title"], surface=True).pack(
                side="left")
            components.BodyLabel(promo_row, text=utils.format_discount(promo),
                                 surface=True).pack(
                side="left", padx=(theme.SPACE_SM, 0))
            components.CaptionLabel(
                promo_row,
                text=f"until {utils.format_date(promo['end_date'])}",
                surface=True).pack(side="left", padx=(theme.SPACE_SM, 0))

        actions = tk.Frame(inner, bg=theme.BG_SURFACE)
        actions.pack(anchor="w")
        if self.session.role == "customer":
            components.PrimaryButton(actions, "Book Now",
                                     command=lambda: self.app.go("Book",
                                                                service_id=service["id"])
                                     ).pack(side="left", padx=(0, theme.SPACE_SM))
        components.SecondaryButton(actions, "Back to Services",
                                   command=lambda: self.app.go("Services")).pack(side="left")

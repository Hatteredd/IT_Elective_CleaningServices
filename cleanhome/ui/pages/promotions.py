"""The public promotions page."""

from __future__ import annotations

import tkinter as tk

from cleanhome import theme
from cleanhome.services import catalog_service
from cleanhome.ui import components, templates


class Promotions(templates.PageTemplate):
    """Promotions that are running right now."""

    page_name = "Promotions"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(
            body, "Promotions",
            "One promotion is applied to each booking — the one that saves you the most. "
            "Promotions never stack.")
        header.pack(fill="x")

        active = catalog_service.list_promotions(active_only=True)
        if not active:
            empty = templates.card(body)
            empty.pack(fill="x")
            inner = templates.card_body(empty)
            components.BodyLabel(inner, text="No promotions are running at the moment.", surface=True).pack(anchor="w")
            return

        can_book = self.session.role != "admin"
        grid = tk.Frame(body, bg=theme.BG_PAGE)
        grid.pack(fill="both", expand=True)
        for column in range(theme.CARD_COLUMNS):
            grid.grid_columnconfigure(column, weight=1, uniform="promos")
        for index, promo in enumerate(active):
            row, column = divmod(index, theme.CARD_COLUMNS)
            holder = tk.Frame(grid, bg=theme.BG_PAGE)
            holder.grid(row=row, column=column, sticky="nsew",
                        padx=(0 if column == 0 else theme.SPACE_SM,
                              0 if column == theme.CARD_COLUMNS - 1 else theme.SPACE_SM),
                        pady=(0, theme.SPACE_MD))
            components.PromoCard(
                holder, promo,
                on_book=(lambda p=promo: self.app.go(
                    "Book", service_id=p.get("service_id"))) if can_book else None,
            ).pack(fill="both", expand=True)

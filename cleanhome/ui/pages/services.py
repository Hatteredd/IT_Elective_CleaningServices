"""The public service catalogue."""

from __future__ import annotations

import tkinter as tk

from cleanhome import theme
from cleanhome.services import catalog_service
from cleanhome.ui import components, templates


class Services(templates.PageTemplate):
    """Every active service, with a live search filter."""

    page_name = "Services"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(
            body, "Services",
            "Fixed prices, no surprises. A promotion is applied automatically when one is "
            "running for the service you pick.")
        header.pack(fill="x")

        toolbar = tk.Frame(body, bg=theme.BG_PAGE)
        toolbar.pack(fill="x", pady=(theme.SPACE_LG, theme.SPACE_MD))
        self.search = components.SearchBar(toolbar, placeholder="Search services",
                                           on_change=self._filter)
        self.search.pack(side="left")
        self.count_label = components.CaptionLabel(toolbar, text="", surface=False)
        self.count_label.pack(side="left", padx=theme.SPACE_MD)
        self.sort = components.SelectBox(
            toolbar, "Sort by",
            [("name", "Name (A-Z)"), ("price_asc", "Price (low to high)"),
             ("price_desc", "Price (high to low)"), ("duration", "Duration (shortest first)")],
            on_change=self._sort)
        self.sort.label.pack(side="left", padx=(theme.SPACE_MD, theme.SPACE_XS))
        self.sort.pack(side="left")

        self.grid = tk.Frame(body, bg=theme.BG_PAGE)
        self.grid.pack(fill="both", expand=True)
        for column in range(3):
            self.grid.grid_columnconfigure(column, weight=1, uniform="services")

        self._services = catalog_service.list_services()
        self._render()

    def _filter(self, term: str) -> None:
        self._render()

    def _sort(self, key: str) -> None:
        self._render()

    def _sorted(self, matches: list[dict]) -> list[dict]:
        key = self.sort.get_key()
        if key == "price_asc":
            return sorted(matches, key=lambda s: s["price"])
        if key == "price_desc":
            return sorted(matches, key=lambda s: -s["price"])
        if key == "duration":
            return sorted(matches, key=lambda s: s["duration_mins"])
        return sorted(matches, key=lambda s: s["name"].lower())

    def _render(self) -> None:
        for child in self.grid.winfo_children():
            child.destroy()
        term = self.search.get().lower()
        matches = [service for service in self._services
                   if term in service["name"].lower()
                   or term in (service["description"] or "").lower()]
        matches = self._sorted(matches)
        if not self._services:
            self.count_label.configure(text="No services available yet.")
        elif len(matches) == len(self._services):
            self.count_label.configure(text=f"{len(self._services)} services available")
        else:
            self.count_label.configure(text=f"{len(matches)} of {len(self._services)} services")
        if not matches:
            empty = tk.Frame(self.grid, bg=theme.BG_PAGE)
            empty.grid(row=0, column=0, columnspan=3, sticky="ew")
            components.BodyLabel(empty, text="No service matches that search.", surface=False).pack(anchor="w")
            return
        for index, service in enumerate(matches):
            row, column = divmod(index, 3)
            holder = tk.Frame(self.grid, bg=theme.BG_PAGE)
            holder.grid(row=row, column=column, sticky="nsew",
                        padx=(0 if column == 0 else theme.SPACE_SM,
                              0 if column == 2 else theme.SPACE_SM),
                        pady=(0, theme.SPACE_MD))
            components.ServiceCard(
                holder, service,
                on_book=lambda s=service: self.app.go("Book", service_id=s["id"]),
                on_details=lambda s=service: self.app.go("ServiceDetails", service_id=s["id"]),
            ).pack(fill="both", expand=True)

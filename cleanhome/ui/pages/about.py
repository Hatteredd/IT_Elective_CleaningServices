"""The about page."""

from __future__ import annotations

import tkinter as tk

from cleanhome import config, theme
from cleanhome.ui import components, templates


class About(templates.PageTemplate):
    """What the company is and where it works."""

    page_name = "About"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(
            body, "About CleanHome",
            f"{config.COMPANY_NAME} is a home cleaning service covering "
            f"{config.SERVICE_AREAS}.")
        header.pack(fill="x")

        story = templates.card(body)
        story.pack(fill="x", pady=(theme.SPACE_LG, 0))
        story_inner = templates.card_body(story)
        components.SubheadingLabel(story_inner, text="What we do", surface=True).pack(anchor="w")
        components.BodyLabel(story_inner,
                 text="We send background-checked cleaners to homes and offices across "
                      "Metro Manila. Every cleaning includes our own supplies, a fixed "
                      "price agreed before the visit, and a cleaner who is paid on the "
                      "quality of the work, not the clock.",
                 wraplength=900, justify="left", surface=True).pack(anchor="w",
                                                      pady=(theme.SPACE_SM, 0))

        values = templates.section(body, "How we work", "Three promises we keep.")
        row = tk.Frame(values, bg=theme.BG_PAGE)
        row.pack(fill="x")
        for column in range(3):
            row.grid_columnconfigure(column, weight=1, uniform="values")
        for index, (title, text) in enumerate((
            ("Fixed prices", "You see the full price before you book. No hourly surprises."),
            ("Vetted cleaners", "Every cleaner passes a background check and a skills "
                                "assessment before joining the team."),
            ("Easy changes", f"Reschedule or cancel free up to {config.CANCEL_CUTOFF_HOURS} "
                             "hours before the scheduled start."),
        )):
            column = tk.Frame(row, bg=theme.BG_PAGE)
            column.grid(row=0, column=index, sticky="nsew",
                        padx=(0 if index == 0 else theme.SPACE_MD, 0))
            components.SubheadingLabel(column, text=title, surface=False).pack(anchor="w")
            components.BodyLabel(column, text=text, wraplength=300,
                     justify="left", surface=False).pack(anchor="w", pady=(theme.SPACE_XS, 0))

        areas = templates.card(body)
        areas.pack(fill="x", pady=(theme.SPACE_LG, 0))
        areas_inner = templates.card_body(areas)
        components.SubheadingLabel(areas_inner, text="Service areas", surface=True).pack(anchor="w")
        components.BodyLabel(areas_inner, text=config.SERVICE_AREAS, wraplength=900,
                 justify="left", surface=True).pack(anchor="w", pady=(theme.SPACE_SM, 0))
        components.CaptionLabel(areas_inner, text=config.COMPANY_HOURS, surface=True).pack(anchor="w",
                                                                       pady=(theme.SPACE_XS, 0))
        components.SecondaryButton(areas_inner, "Book a Cleaning",
                                   command=lambda: self.app.go("Book")).pack(anchor="w",
                                                                             pady=(theme.SPACE_MD, 0))

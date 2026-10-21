"""The contact page."""

from __future__ import annotations

import os
import subprocess
import tkinter as tk

from cleanhome import config, theme
from cleanhome.ui import components, templates


class Contact(templates.PageTemplate):
    """How to reach the company."""

    page_name = "Contact"

    def build(self, **kwargs) -> None:
        super().build(**kwargs)
        body = self.body

        header = templates.page_header(
            body, "Contact us",
            "We answer every message during business hours, usually within the same day.")
        header.pack(fill="x")

        card = templates.card(body)
        card.pack(fill="x", pady=(theme.SPACE_LG, 0))
        inner = templates.card_body(card)

        for label, value in (
            ("Phone", config.COMPANY_PHONE),
            ("Email", config.COMPANY_EMAIL),
            ("Hours", config.COMPANY_HOURS),
            ("Office", config.COMPANY_ADDRESS),
            ("Areas covered", config.SERVICE_AREAS),
        ):
            row = tk.Frame(inner, bg=theme.BG_SURFACE)
            row.pack(fill="x", pady=(theme.SPACE_SM, 0))
            components.CaptionLabel(row, text=label, width=14, anchor="w", surface=True).pack(side="left")
            components.BodyLabel(row, text=value, wraplength=600,
                     justify="left", surface=True).pack(side="left", fill="x", expand=True)

        actions = tk.Frame(inner, bg=theme.BG_SURFACE)
        actions.pack(anchor="w", pady=(theme.SPACE_LG, 0))
        components.PrimaryButton(actions, "Send an Email",
                                 command=lambda: self._open_link(
                                     f"mailto:{config.COMPANY_EMAIL}")).pack(side="left",
                                                                               padx=(0, theme.SPACE_SM))
        components.SecondaryButton(actions, "Call Us",
                                   command=lambda: self._open_link(
                                       f"tel:{config.COMPANY_PHONE.replace(' ', '')}")
                                   ).pack(side="left")

    def _open_link(self, target: str) -> None:
        """Hand a mailto: or tel: link to the operating system."""
        try:
            if target.startswith("mailto:"):
                os.startfile(target)  # noqa: S606 - the OS handles the protocol
            else:
                subprocess.Popen(["start", "", target], shell=False)  # noqa: S603,S607
        except OSError:
            self.app.flash("Open that link manually: " + target, "warning")

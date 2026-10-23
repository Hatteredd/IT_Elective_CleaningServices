"""Page templates.

Three shells are used by the whole app:

* :class:`PageTemplate` — the public shell (navbar, scrolling body, footer).
* :class:`AdminTemplate` — the administration shell (navbar, scrolling body).
* :class:`AuthTemplate` — the sign-in and sign-up shell (navbar, centred card).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from cleanhome import theme
from cleanhome.ui import components
from cleanhome.ui.components import FormMixin


class Page(ttk.Frame):
    """Base class for every screen in the app."""

    page_name = ""

    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame")
        self.app = app
        self.session = app.session

    def on_show(self, **kwargs) -> None:
        """Called each time the page is opened."""
        self.build(**kwargs)

    def build(self, **kwargs) -> None:
        """Draw the page. Subclasses override this."""
        raise NotImplementedError


class PageTemplate(Page):
    """Public shell: navigation bar, scrolling body, footer."""

    show_footer = True

    def build(self, **kwargs) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.navbar = components.NavBar(self, self.app, active=self.page_name)
        self.navbar.grid(row=0, column=0, sticky="ew")

        self.scroller = theme.ScrollableFrame(self)
        self.scroller.grid(row=1, column=0, sticky="nsew")

        inner = self.scroller.inner
        inner.grid_columnconfigure(0, weight=1)
        self.body = ttk.Frame(inner, style="TFrame")
        self.body.grid(row=0, column=0, sticky="nsew", padx=theme.SPACE_XL,
                       pady=theme.SPACE_XL)
        self.scroller.canvas.bind("<Configure>", self._fit_content_width, add="+")

        if self.show_footer:
            self.footer = components.Footer(self, self.app)
            self.footer.grid(row=2, column=0, sticky="ew")

    def _fit_content_width(self, event) -> None:
        """Centre the body and keep it from growing past ``CONTENT_MAX_WIDTH``."""
        extra = max(0, (event.width - theme.CONTENT_MAX_WIDTH) // 2)
        self.body.grid_configure(padx=theme.SPACE_XL + extra)


class AdminTemplate(PageTemplate):
    """Administration shell: navigation bar and a scrolling body."""

    show_footer = False


class AuthTemplate(Page):
    """Sign-in and sign-up shell: navigation bar and a centred card."""

    def build(self, **kwargs) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.navbar = components.NavBar(self, self.app, active=self.page_name)
        self.navbar.grid(row=0, column=0, sticky="ew")

        holder = ttk.Frame(self, style="TFrame")
        holder.grid(row=1, column=0, sticky="nsew", padx=theme.SPACE_XL,
                    pady=theme.SPACE_XL)
        holder.grid_columnconfigure(0, weight=1)
        holder.grid_rowconfigure(0, weight=1)

        self.body = ttk.Frame(holder, style="TFrame")
        self.body.grid(row=0, column=0, sticky="n")


# ── Small shared helpers ──────────────────────────────────────────────────────
def page_header(parent, title: str, subtitle: str = "") -> tk.Frame:
    """Return a frame holding a page title and an optional subtitle."""
    frame = tk.Frame(parent, bg=theme.BG_PAGE)
    components.HeadingLabel(frame, text=title).pack(anchor="w")
    if subtitle:
        components.BodyLabel(frame, text=subtitle, wraplength=theme.WRAP_SECTION,
                             justify="left").pack(anchor="w", pady=(theme.SPACE_XS, 0))
    return frame


def card(parent, padding: int = theme.CARD_PAD) -> tk.Frame:
    """Return a white card: a 1px border plus a soft bottom/right shadow edge."""
    outer = tk.Frame(parent, bg=theme.SHADOW_EDGE)
    inner = tk.Frame(outer, bg=theme.BG_SURFACE, highlightbackground=theme.BORDER,
                     highlightthickness=theme.BORDER_WIDTH, bd=0,
                     padx=padding, pady=padding)
    inner.pack(fill="both", expand=True, padx=(0, theme.BORDER_WIDTH),
               pady=(0, theme.BORDER_WIDTH))
    outer.inner = inner
    return outer


def card_body(card_frame) -> tk.Frame:
    """Return the white inside of a card."""
    return getattr(card_frame, "inner", card_frame)


def section(parent, title: str, subtitle: str = "") -> tk.Frame:
    """Return a titled section with a card body, ready for content."""
    frame = tk.Frame(parent, bg=theme.BG_PAGE)
    frame.pack(fill="x", pady=(theme.SPACE_2XL, 0))
    components.SubheadingLabel(frame, text=title).pack(anchor="w")
    if subtitle:
        components.CaptionLabel(frame, text=subtitle).pack(anchor="w",
                                                           pady=(theme.SPACE_XS, 0))
    body = tk.Frame(frame, bg=theme.BG_PAGE)
    body.pack(fill="x", pady=(theme.SPACE_MD, 0))
    return body

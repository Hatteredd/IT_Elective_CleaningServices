"""Design tokens, font detection, type scale, and ttk styles.

All colours, spacing, and font sizes used by the UI are defined here.
Pages import from this module and never hard-code a colour or a pixel value.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# ── Colours ──────────────────────────────────────────────────────────────────
BG_PAGE = "#FAFAFA"      # page background (ultra light neutral)
BG_SURFACE = "#FFFFFF"   # cards, panels, header
BORDER = "#E4E4E7"       # 1px crisp border
SHADOW_EDGE = "#E4E4E7"  # kept for compatibility, unused in Atomic Grid
PRIMARY = "#0070F3"      # digital blue accent
PRIMARY_HOVER = "#0059C1"
PRIMARY_SOFT = "#E8F1FE"  # active nav pill, selected rows, badges bg
TEXT = "#09090B"         # high-contrast primary text
TEXT_BODY = "#18181B"    # body paragraphs
TEXT_MUTED = "#666666"   # captions, hints
DANGER = "#E5484D"       # errors
DANGER_SOFT = "#FDECEC"
SUCCESS = "#12A150"      # confirmed / completed
SUCCESS_SOFT = "#E6F6EC"
WARNING = "#B7791F"      # pending
WARNING_SOFT = "#FEF3C7"
TEXT_ON_ACCENT = "#FFFFFF"  # text drawn on a coloured button or toast
TOAST_BG = "#111827"     # the dark "Copied!" toast
TOAST_TEXT = "#FFFFFF"   # text on the dark toast
TOGGLE_ON = PRIMARY      # a switch that is on
TOGGLE_OFF = "#D1D5DB"   # a switch that is off
TOGGLE_THUMB = "#FFFFFF"  # the knob of a switch
CHECK_MARK = PRIMARY     # the tick inside a checked box
BG_ROW_ALT = "#FAFAFA"   # every other row of a table
BG_INPUT_IDLE = "#F4F4F5"  # muted surface accents for inputs/tabs
PRIMARY_DISABLED = "#B9C6D4"
PRIMARY_DISABLED_TEXT = "#F0F3F6"
DANGER_HOVER = "#C43B40"
DANGER_DISABLED = "#EFC0C2"
DANGER_DISABLED_TEXT = "#FDF3F3"
NAVBAR_BORDER = "#E5E7EB"   # 1px line under the nav bar
SELECTED_ROW = "#DBEAFE"    # highlighted row in a treeview
SELECTED_ROW_FG = "#1E3A5F"  # text on a selected row
LINK_COLOR = "#0A6CF0"       # clickable text (same as PRIMARY)
REQUIRED_MARK = "#E5484D"    # the * next to required field labels

# ── Spacing (16px grid: multiples of 4 and 8 only) ───────────────────────────
SPACE_XS, SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL, SPACE_2XL = 4, 8, 12, 16, 24, 32

# ── Sizes ────────────────────────────────────────────────────────────────────
BUTTON_HEIGHT = 40
BUTTON_PAD_X = 18
BUTTON_PAD_Y = 10
INPUT_HEIGHT = 40
CARD_PAD = 20
CONTENT_MAX_WIDTH = 1120
NAVBAR_HEIGHT = 72
ACCENT_HEIGHT = 3
DIVIDER_HEIGHT = 1
TOAST_HEIGHT = 44
FOCUS_RING = 2           # the 2px PRIMARY ring drawn around a focused input
ICON_SIZE = 40           # the square icon tile on a card
TOGGLE_WIDTH = 40
TOGGLE_HEIGHT = 22
CHECK_SIZE = 18          # the square box of a check box

# ── Layout ────────────────────────────────────────────────────────────────────
# How many cards sit side by side in a grid.
CARD_COLUMNS = 3
DASHBOARD_COLUMNS = 4    # the stat cards on the admin dashboard
REPORT_COLUMNS = 4       # the stat cards on the report screen

# Column widths of the label/value pairs (in characters).
LABEL_WIDTH = 16
LABEL_WIDTH_NARROW = 14

# How wide a block of text may grow before it wraps (in pixels).
WRAP_NARROW = 280        # a line inside a three-column card
WRAP_COLUMN = 300        # a line inside a card column
WRAP_FORM = 420          # the setup screen intro
WRAP_HERO = 520          # the home page hero paragraph
WRAP_DIALOG = 380        # a dialog paragraph
WRAP_CONTACT = 600       # the contact detail column
WRAP_SECTION = 760       # a section paragraph
WRAP_FULL = 900          # a full-width paragraph
WRAP_CARD = 800          # a line inside a booking card

# Input and dropdown widths (in characters).
FIELD_WIDTH = 40
FIELD_WIDTH_WIDE = 60
FIELD_WIDTH_SHORT = 14
FIELD_WIDTH_DATE = 26
FIELD_WIDTH_DIALOG = 44
DROPDOWN_WIDTH = 24
DROPDOWN_SERVICE = 40
DROPDOWN_STATUS = 16
DROPDOWN_SORT = 22
BUTTON_WIDTH_TOGGLE = 6
SEARCH_WIDTH = 320

# The height of a table when it is first drawn (in rows).
DATA_TABLE_HEIGHT = 12

# How long a toast stays on screen (in milliseconds).
TOAST_DURATION_MS = 3500

# How far the promotion form can reach back and forward (in days).
PROMO_DATE_SPAN_DAYS = 730
PROMO_DATE_SPAN_OFFSET = -365
DATE_SPAN_YEAR = 365

# ── Fonts ────────────────────────────────────────────────────────────────────
# The reference design uses Geist Sans / Inter, which are not installed by
# default. Detect what this machine actually has and fall back in order.
FONT_CANDIDATES = ("Inter", "Geist", "Segoe UI", "Helvetica")
FONT_FAMILY = "Segoe UI"
FONT_AVAILABLE: list[str] = []

# Font sizes that are not part of the type scale.
BRAND_FONT_SIZE = 13
BRAND_BOLD_SIZE = 15
HERO_FONT_SIZE = 28
PROMO_PRICE_FONT_SIZE = 22
AVATAR_INITIAL_FONT_SIZE = 18
OVERSTRIKE_FONT_SIZE = 10
CLEAR_ICON_FONT_SIZE = 12

# ── Canvas drawing ───────────────────────────────────────────────────────────
STROKE_WIDTH = 2         # the width of a drawn line
ICON_EDGE_INSET = 2      # how far a drawn shape stays from the tile edge
ICON_DOT_RADIUS = 3      # the radius of the dot in the sparkle icon
ICON_ARM_LENGTH = 6      # how far the arms of the sparkle reach
ICON_RING_INSET = 6      # the inset of the clock face
ICON_HAND_LONG = 8       # the long hand of the clock
ICON_HAND_SHORT = 6      # the short hand of the clock
ICON_SHIELD_INSET = 6    # the inset of the shield outline
ICON_SHIELD_SHOULDER = 10  # the width of the top of the shield
# The three points of the tick inside the shield, relative to its centre.
ICON_SHIELD_TICK = ((-4, 0), (-1, 3), (4, -2))
TOGGLE_RADIUS = 11       # the rounded end of the switch
TOGGLE_INSET = 2         # how far the knob sits from the end of the track
CHECK_TICK = ((4, 9), (7, 12), (14, 5))  # the three points of the tick
AVATAR_SIZE = 56         # the square avatar on the profile card
AVATAR_INSET = 2         # the gap between the avatar and its ring
BORDER_WIDTH = 1         # the 1px border of a card or a table cell

CHART_HEIGHT = 260
CHART_PAD_LEFT = 48
CHART_PAD_RIGHT = 6
CHART_PAD_TOP = 18
CHART_PAD_BOTTOM = 28
CHART_GRID_LINES = 4
CHART_BAR_RATIO = 0.65
CHART_BAR_MIN_HEIGHT = 2
CHART_LABEL_GAP = 6
CHART_VALUE_GAP = 4
CHART_COLUMN_LABEL_MAX_CHARS = 14   # longer column labels are truncated
CHART_LABEL_WRAP = 14

# ── Table column widths (in pixels) ───────────────────────────────────────────
BOOKINGS_TABLE_WIDTHS = (40, 110, 150, 110, 130, 140, 170, 80, 70)
SERVICES_TABLE_WIDTHS = (50, 280, 100, 100, 90)
PROMOTIONS_TABLE_WIDTHS = (50, 160, 80, 80, 160, 130, 130, 80)
CUSTOMERS_TABLE_WIDTHS = (50, 160, 200, 140, 90, 90)
DASHBOARD_TABLE_WIDTHS = (60, 160, 160, 180, 110, 100)
REPORT_TABLE_WIDTHS = (320, 120, 140)


def detect_fonts() -> str:
    """Pick the first available family from ``FONT_CANDIDATES``."""
    global FONT_FAMILY, FONT_AVAILABLE
    try:
        available = {name.lower() for name in tkfont.families()}
    except tk.TclError:
        available = set()
    FONT_AVAILABLE = sorted(available)
    for candidate in FONT_CANDIDATES:
        if candidate.lower() in available:
            FONT_FAMILY = candidate
            return candidate
    FONT_FAMILY = "TkDefaultFont"
    return FONT_FAMILY


# Type scale tokens: (size, weight)
SCALE = {
    # Semantic aliases for documentation
    # TITLE = "H1", SUBHEADING = "H2", BODY_TEXT = "BODY", CAPTION_TEXT = "CAPTION"
    "H1": (24, "bold"),
    "H2": (14, "bold"),
    "BODY": (12, "normal"),
    "CAPTION": (10, "normal"),
    "PRICE": (16, "bold"),
}


def font(token: str) -> tuple[str, int, str]:
    """Return a Tk font tuple for a type-scale token."""
    size, weight = SCALE.get(token, SCALE["BODY"])
    return (FONT_FAMILY, size, weight)


def configure_style(root: tk.Misc) -> None:
    """Apply the CleanHome theme to every widget under ``root``."""
    detect_fonts()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=BG_PAGE, foreground=TEXT, font=font("BODY"))
    style.configure("TFrame", background=BG_PAGE)
    style.configure("TLabel", background=BG_PAGE, foreground=TEXT, font=font("BODY"))
    style.configure("Caption.TLabel", font=font("CAPTION"), foreground=TEXT_MUTED)

    style.configure("TEntry", fieldbackground=BG_INPUT_IDLE, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, padding=(10, 8),
                    insertcolor=TEXT)
    style.map("TEntry",
              bordercolor=[("focus", PRIMARY)],
              lightcolor=[("focus", PRIMARY)],
              darkcolor=[("focus", PRIMARY)])

    # The input inside a FormField carries no border of its own: the 2px ring
    # drawn around it by the field is the only border.
    style.configure("Field.TEntry", fieldbackground=BG_SURFACE, bordercolor=BG_SURFACE,
                    lightcolor=BG_SURFACE, darkcolor=BG_SURFACE, padding=(10, 8),
                    insertcolor=TEXT)
    style.map("Field.TEntry",
              bordercolor=[("focus", BG_SURFACE)],
              lightcolor=[("focus", BG_SURFACE)],
              darkcolor=[("focus", BG_SURFACE)])
    style.configure("Primary.TButton", relief="flat", padding=(12, 8), font=font("BODY"),
                    background=PRIMARY, foreground=TEXT_ON_ACCENT, borderwidth=0,
                    focusthickness=0)
    style.map("Primary.TButton",
              background=[("pressed", PRIMARY_HOVER), ("active", PRIMARY_HOVER), ("disabled", PRIMARY_DISABLED)],
              foreground=[("disabled", PRIMARY_DISABLED_TEXT)])

    style.configure("Secondary.TButton", relief="flat", padding=(12, 8), font=font("BODY"),
                    background=BG_SURFACE, foreground=TEXT, borderwidth=1)
    style.map("Secondary.TButton",
              background=[("pressed", BG_PAGE), ("active", BG_PAGE), ("disabled", BG_SURFACE)],
              foreground=[("disabled", TEXT_MUTED)],
              bordercolor=[("!disabled", BORDER), ("disabled", BORDER)],
              lightcolor=[("!disabled", BORDER)], darkcolor=[("!disabled", BORDER)])

    style.configure("Danger.TButton", relief="flat", padding=(12, 8), font=font("BODY"),
                    background=DANGER, foreground=TEXT_ON_ACCENT, borderwidth=0, focusthickness=0)
    style.map("Danger.TButton",
              background=[("pressed", DANGER_HOVER), ("active", DANGER_HOVER), ("disabled", DANGER_DISABLED)],
              foreground=[("disabled", DANGER_DISABLED_TEXT)])

    style.configure("TCombobox", fieldbackground=BG_INPUT_IDLE, background=BG_SURFACE,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    arrowcolor=TEXT_BODY, padding=(8, 6))
    style.map("TCombobox",
              bordercolor=[("focus", PRIMARY)],
              lightcolor=[("focus", PRIMARY)], darkcolor=[("focus", PRIMARY)],
              fieldbackground=[("readonly", BG_SURFACE)])

    style.configure("Treeview", background=BG_SURFACE, fieldbackground=BG_SURFACE,
                    foreground=TEXT, rowheight=28, borderwidth=0, font=font("BODY"))
    style.configure("Treeview.Heading", background=BG_PAGE, foreground=TEXT_BODY,
                    font=font("CAPTION"), relief="flat", padding=(6, 6))
    style.map("Treeview.Heading", background=[("active", BG_PAGE)])
    style.map("Treeview",
              background=[("selected", SELECTED_ROW)],
              foreground=[("selected", SELECTED_ROW_FG)])

    style.configure("TNotebook", background=BG_PAGE, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(14, 8), font=font("BODY"))
    style.map("TNotebook.Tab",
              background=[("selected", BG_SURFACE)],
              foreground=[("selected", TEXT)],
              font=[("selected", font("BODY"))])

    for name, bg, fg in (
        ("Badge.Pending", WARNING_SOFT, WARNING),
        ("Badge.Confirmed", PRIMARY_SOFT, PRIMARY),
        ("Badge.InProgress", PRIMARY_SOFT, PRIMARY),
        ("Badge.Completed", SUCCESS_SOFT, SUCCESS),
        ("Badge.Cancelled", DANGER_SOFT, DANGER),
        ("Badge.Neutral", BG_PAGE, TEXT_MUTED),
    ):
        style.configure(f"{name}.TLabel", background=bg, foreground=fg,
                        font=font("CAPTION"), padding=(8, 3))


# ── Badge colours per status ─────────────────────────────────────────────────
STATUS_BADGE = {
    "pending": ("Badge.Pending", WARNING),
    "confirmed": ("Badge.Confirmed", PRIMARY),
    "in_progress": ("Badge.InProgress", PRIMARY),
    "completed": ("Badge.Completed", SUCCESS),
    "cancelled": ("Badge.Cancelled", DANGER),
}


def badge_style(status: str) -> tuple[str, str]:
    """Return the (style name, colour) for a booking status."""
    return STATUS_BADGE.get(status, ("Badge.Neutral", TEXT_MUTED))


# ── Widget factories ─────────────────────────────────────────────────────────
def make_treeview_with_scrollbar(parent: tk.Misc, columns, headings=None,
                                 widths=None, height=DATA_TABLE_HEIGHT, **kwargs):
    """Create a Treeview with an attached vertical scrollbar."""
    container = ttk.Frame(parent, style="TFrame")
    tree = ttk.Treeview(container, columns=columns, show="headings",
                         height=height, **kwargs)
    vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    if headings:
        for col, head in zip(columns, headings):
            tree.heading(col, text=head)
    else:
        for col in columns:
            tree.heading(col, text=col.replace("_", " ").title())

    if widths:
        for col, width in zip(columns, widths):
            tree.column(col, width=width, anchor="w")

    tree.tag_configure("even", background=BG_SURFACE)
    tree.tag_configure("odd", background=BG_ROW_ALT)
    return container, tree


class ScrollableFrame(ttk.Frame):
    """A vertically scrollable container.

    The scroll region is derived from the embedded window only, so decorative
    content can never inflate it and leave a blank slab under the content.
    The scrollbar hides itself whenever the content fits.
    """

    def __init__(self, parent: tk.Misc, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        self.canvas = tk.Canvas(self, bg=BG_PAGE, highlightthickness=0, bd=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas, style="TFrame")
        self._window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self._on_scroll_set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar_visible = False
        self._sync_scrollbar()

        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

    # -- layout ----------------------------------------------------------------
    def _on_inner_configure(self, event: tk.Event) -> None:
        self._update_scrollregion()
        self._sync_scrollbar()

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfig(self._window_id, width=event.width)
        self._update_scrollregion()
        self._sync_scrollbar()

    def _update_scrollregion(self) -> None:
        bbox = self.canvas.bbox(self._window_id)
        if bbox:
            self.canvas.configure(scrollregion=bbox)

    def _on_scroll_set(self, first, last) -> None:
        if self.vsb.winfo_ismapped():
            self.vsb.set(first, last)

    def _sync_scrollbar(self) -> None:
        """Show the scrollbar only when the content is taller than the view."""
        bbox = self.canvas.bbox(self._window_id)
        if not bbox:
            return
        content_height = bbox[3] - bbox[1]
        view_height = self.canvas.winfo_height()
        needed = content_height > view_height + 2
        if needed and not self._scrollbar_visible:
            self.vsb.pack(side="right", fill="y")
            self._scrollbar_visible = True
        elif not needed and self._scrollbar_visible:
            self.vsb.pack_forget()
            self._scrollbar_visible = False

    # -- mouse wheel -----------------------------------------------------------
    def _bind_wheel(self, event: tk.Event) -> None:
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_wheel(self, event: tk.Event) -> None:
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def _contains(self, widget: tk.Misc) -> bool:
        current: tk.Misc | None = widget
        while current is not None:
            if current is self:
                return True
            current = getattr(current, "master", None)
        return False

    def _on_mousewheel(self, event: tk.Event) -> None:
        widget = self.winfo_containing(event.x_root, event.y_root)
        if widget is None or not self._contains(widget):
            return
        if getattr(event, "num", None) == 4:
            steps = -1
        elif getattr(event, "num", None) == 5:
            steps = 1
        else:
            delta = getattr(event, "delta", 0)
            steps = int(delta / 120) if abs(delta) >= 120 else int(delta)
        if steps:
            self.canvas.yview_scroll(-steps, "units")

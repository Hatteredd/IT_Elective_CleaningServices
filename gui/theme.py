"""Color palette and ttk style configuration for the CleanHome GUI."""

import tkinter as tk
from tkinter import ttk


# ── Colors ────────────────────────────────────────────────────────────────────
PRIMARY = "#0D9488"         # Modern Emerald/Teal 600
PRIMARY_DARK = "#0F766E"    # Teal 700
PRIMARY_LIGHT = "#F0FDFA"   # Teal 50
PRIMARY_BORDER = "#99F6E4"  # Teal 200
SECONDARY = "#0284C7"       # Sky 600
SECONDARY_LIGHT = "#E0F2FE"
DANGER = "#DC2626"          # Red 600
DANGER_LIGHT = "#FEF2F2"
WARNING = "#D97706"         # Amber 600
WARNING_LIGHT = "#FFFBEB"
INFO = "#2563EB"            # Blue 600
INFO_LIGHT = "#EFF6FF"
SUCCESS = "#16A34A"         # Green 600
SUCCESS_LIGHT = "#F0FDF4"

BG = "#F8FAFC"              # Slate 50
SURFACE = "#FFFFFF"         # Pure white
SURFACE_ALT = "#F1F5F9"     # Slate 100
BORDER = "#E2E8F0"          # Slate 200
BORDER_LIGHT = "#F1F5F9"
TEXT = "#0F172A"            # Slate 900
TEXT_MUTED = "#64748B"      # Slate 500
SIDEBAR = "#0F172A"         # Slate 900
SIDEBAR_ACTIVE = "#0D9488"  # Teal 600
SIDEBAR_HOVER = "#1E293B"   # Slate 800
SIDEBAR_TEXT = "#94A3B8"    # Slate 400


# ── Spacing scale (4px rhythm) ────────────────────────────────────────────────
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 20
SPACE_2XL = 24
SPACE_3XL = 32


def configure_style(root):
    """Apply a clean, modern ttk theme."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # ── Base ──────────────────────────────────────────────────────────────
    style.configure(".", background=BG, foreground=TEXT, font=("Segoe UI", 10))
    style.configure("TFrame", background=BG)
    style.configure("Surface.TFrame", background=SURFACE)
    style.configure("SurfaceAlt.TFrame", background=SURFACE_ALT)
    style.configure("Sidebar.TFrame", background=SIDEBAR)

    # ── Labels ────────────────────────────────────────────────────────────
    style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
    style.configure("Surface.TLabel", background=SURFACE)
    style.configure("SurfaceAlt.TLabel", background=SURFACE_ALT)
    style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground=TEXT)
    style.configure("Heading.TLabel", font=("Segoe UI", 14, "bold"), foreground=TEXT)
    style.configure("Subheading.TLabel", font=("Segoe UI", 11, "bold"), foreground=TEXT)
    style.configure("Muted.TLabel", foreground=TEXT_MUTED)
    style.configure("Surface.Muted.TLabel", background=SURFACE, foreground=TEXT_MUTED)
    style.configure("SurfaceAlt.Muted.TLabel", background=SURFACE_ALT, foreground=TEXT_MUTED)
    style.configure("Sidebar.TLabel", background=SIDEBAR, foreground=SIDEBAR_TEXT, font=("Segoe UI", 10))
    style.configure("Sidebar.Title.TLabel", background=SIDEBAR, foreground="#FFFFFF", font=("Segoe UI", 16, "bold"))
    style.configure("Big.TLabel", font=("Segoe UI", 18, "bold"), foreground=TEXT)
    style.configure("Card.Value.TLabel", background=SURFACE, font=("Segoe UI", 24, "bold"), foreground=PRIMARY)
    style.configure("Card.Label.TLabel", background=SURFACE, foreground=TEXT_MUTED, font=("Segoe UI", 9))

    # ── Entry / Field ─────────────────────────────────────────────────────
    style.configure("TEntry", fieldbackground=SURFACE, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, padding=8)
    style.map("TEntry", bordercolor=[("focus", PRIMARY)],
              lightcolor=[("focus", PRIMARY)], darkcolor=[("focus", PRIMARY)])

    # ── Buttons ───────────────────────────────────────────────────────────
    style.configure("TButton", padding=(16, 9), font=("Segoe UI", 10, "bold"),
                    borderwidth=0, focusthickness=0)
    style.map("TButton",
              background=[("active", PRIMARY_DARK), ("pressed", PRIMARY_DARK), ("!disabled", PRIMARY)],
              foreground=[("!disabled", "#FFFFFF")])

    style.configure("Secondary.TButton", padding=(14, 7), font=("Segoe UI", 10))
    style.map("Secondary.TButton",
              background=[("active", "#EEF2F5"), ("pressed", "#E2E8ED"), ("!disabled", SURFACE)],
              foreground=[("!disabled", TEXT)],
              bordercolor=[("!disabled", BORDER)],
              borderwidth=[("!disabled", 1)],
              lightcolor=[("!disabled", BORDER)],
              darkcolor=[("!disabled", BORDER)])

    style.configure("Danger.TButton", padding=(14, 7), font=("Segoe UI", 10, "bold"))
    style.map("Danger.TButton",
              background=[("active", "#C0392B"), ("pressed", "#A93226"), ("!disabled", DANGER)],
              foreground=[("!disabled", "#FFFFFF")])

    style.configure("Success.TButton", padding=(14, 7), font=("Segoe UI", 10, "bold"))
    style.map("Success.TButton",
              background=[("active", "#0D8B6A"), ("pressed", "#0B6E54"), ("!disabled", SUCCESS)],
              foreground=[("!disabled", "#FFFFFF")])

    style.configure("Sidebar.TButton", padding=(14, 11), font=("Segoe UI", 10))
    style.map("Sidebar.TButton",
              background=[("active", "#1E293B"), ("pressed", "#334155"), ("!disabled", SIDEBAR)],
              foreground=[("active", "#FFFFFF"), ("!disabled", SIDEBAR_TEXT)],
              borderwidth=[("!disabled", 0)])

    style.configure("Sidebar.Active.TButton", padding=(14, 11), font=("Segoe UI", 10, "bold"))
    style.map("Sidebar.Active.TButton",
              background=[("active", PRIMARY_DARK), ("!disabled", SIDEBAR_ACTIVE)],
              foreground=[("!disabled", "#FFFFFF")],
              borderwidth=[("!disabled", 0)])

    # ── Treeview (tables) ─────────────────────────────────────────────────
    style.configure("Treeview",
                    background=SURFACE, fieldbackground=SURFACE, foreground=TEXT,
                    rowheight=36, bordercolor=BORDER, borderwidth=0)
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                    background=BORDER_LIGHT, foreground=TEXT, relief="flat",
                    padding=(10, 8))
    style.map("Treeview",
              background=[("selected", PRIMARY)],
              foreground=[("selected", "#FFFFFF")])
    style.map("Treeview.Heading",
              background=[("active", BORDER)])

    # ── Badges (status pills) ─────────────────────────────────────────────
    style.configure("Badge.TLabel", font=("Segoe UI", 9, "bold"), padding=(10, 4))
    for name, fg, bg in [
        ("Pending", "#92400E", WARNING_LIGHT),
        ("Confirmed", "#1E40AF", "#DBEAFE"),
        ("InProgress", "#1E3A8A", PRIMARY_LIGHT),
        ("Completed", "#065F46", SUCCESS_LIGHT),
        ("Cancelled", "#991B1B", DANGER_LIGHT),
        ("Paid", "#065F46", SUCCESS_LIGHT),
        ("Unpaid", "#92400E", WARNING_LIGHT),
        ("Info", "#1E3A8A", PRIMARY_LIGHT),
    ]:
        style.configure(f"Badge.{name}.TLabel", foreground=fg, background=bg)

    # ── Notebook ──────────────────────────────────────────────────────────
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(16, 10), font=("Segoe UI", 10))
    style.map("TNotebook.Tab",
              background=[("selected", SURFACE), ("!selected", BORDER_LIGHT)],
              foreground=[("selected", PRIMARY), ("!selected", TEXT_MUTED)])

    # ── Combobox ──────────────────────────────────────────────────────────
    style.configure("TCombobox", fieldbackground=SURFACE, padding=8,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
    style.map("TCombobox", bordercolor=[("focus", PRIMARY)],
              lightcolor=[("focus", PRIMARY)], darkcolor=[("focus", PRIMARY)])

    # ── Scrollbar ─────────────────────────────────────────────────────────
    style.configure("Vertical.TScrollbar", background=BORDER, bordercolor=BORDER,
                    arrowcolor=TEXT_MUTED, troughcolor=BG)
    style.configure("Horizontal.TScrollbar", background=BORDER, bordercolor=BORDER,
                    arrowcolor=TEXT_MUTED, troughcolor=BG)
    style.map("Vertical.TScrollbar", background=[("active", TEXT_MUTED)])
    style.map("Horizontal.TScrollbar", background=[("active", TEXT_MUTED)])

    # ── Checkbutton / Radiobutton ─────────────────────────────────────────
    style.configure("TCheckbutton", background=BG, foreground=TEXT, padding=4)
    style.configure("Surface.TCheckbutton", background=SURFACE, foreground=TEXT, padding=4)
    style.configure("TRadiobutton", background=BG, foreground=TEXT, padding=4)

    # ── Separator ─────────────────────────────────────────────────────────
    style.configure("TSeparator", background=BORDER)


def make_card(parent, **kwargs):
    """Create a consistent surfaced card with a subtle border."""
    card = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER,
                    highlightthickness=1, bd=0, **kwargs)
    return card


def make_inner(parent, **kwargs):
    """Create the inner content frame of a card."""
    return ttk.Frame(parent, style="Surface.TFrame", **kwargs)


def make_stat_card(parent, title, value, subtitle=None, icon="📊", icon_bg="#F0FDFA", icon_fg="#0D9488", **kwargs):
    """Create a modern elevated KPI metric card with an icon badge and bold typography."""
    card = make_card(parent, **kwargs)
    inner = tk.Frame(card, bg=SURFACE, padx=20, pady=18)
    inner.pack(fill="both", expand=True)

    top_row = tk.Frame(inner, bg=SURFACE)
    top_row.pack(fill="x", pady=(0, 8))

    icon_box = tk.Label(top_row, text=icon, bg=icon_bg, fg=icon_fg,
                        font=("Segoe UI", 12), padx=8, pady=4, relief="flat")
    icon_box.pack(side="left")

    tk.Label(top_row, text=title.upper(), bg=SURFACE, fg=TEXT_MUTED,
             font=("Segoe UI", 8, "bold")).pack(side="left", padx=(8, 0))

    val_lbl = tk.Label(inner, text=str(value), bg=SURFACE, fg=TEXT,
                       font=("Segoe UI", 22, "bold"))
    val_lbl.pack(anchor="w")

    if subtitle:
        tk.Label(inner, text=subtitle, bg=SURFACE, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(3, 0))

    return card


# ── Badge helpers ─────────────────────────────────────────────────────────────
_BADGE_STYLES = {
    "pending": "Badge.Pending.TLabel",
    "confirmed": "Badge.Confirmed.TLabel",
    "in_progress": "Badge.InProgress.TLabel",
    "completed": "Badge.Completed.TLabel",
    "cancelled": "Badge.Cancelled.TLabel",
    "paid": "Badge.Paid.TLabel",
    "unpaid": "Badge.Unpaid.TLabel",
}


def make_badge(parent, text, status):
    """Return a ttk.Label styled as a colored status pill."""
    style = _BADGE_STYLES.get(status, "Badge.Info.TLabel")
    return ttk.Label(parent, text=text, style=style)


# ── Section / form helpers ────────────────────────────────────────────────────
def section_label(parent, text, **kwargs):
    """A consistent section heading label."""
    return ttk.Label(parent, text=text, style="Heading.TLabel", **kwargs)


def field_label(parent, text, **kwargs):
    """A consistent form field label with standard bottom spacing."""
    return ttk.Label(parent, text=text, style="Surface.TLabel", **kwargs)


def empty_state(parent, text, **kwargs):
    """A centered muted label for empty lists."""
    return ttk.Label(parent, text=text, style="Muted.TLabel",
                     font=("Segoe UI", 11), **kwargs)


def configure_toplevel(top, min_width=360, min_height=200, resizable=True):
    """Apply app theme to a Toplevel dialog, bind Escape key, and constrain its size."""
    top.configure(bg=BG)
    top.minsize(min_width, min_height)
    if not resizable:
        top.resizable(False, False)
    else:
        top.resizable(True, True)
    top.bind("<Escape>", lambda e: top.destroy())
    for child in top.winfo_children():
        try:
            child.configure(bg=BG)
        except (tk.TclError, AttributeError):
            pass


class ScrollableFrame(ttk.Frame):
    """A reusable scrollable container with canvas and vertical scrollbar.
    Automatically expands the inner frame to the canvas width and provides smooth mouse scrolling.
    """

    def __init__(self, parent, bg=BG, **kwargs):
        super().__init__(parent, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")

        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_inner_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        w = self.winfo_containing(event.x_root, event.y_root)
        if w is not None and str(w).startswith(str(self)):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def make_treeview_with_scrollbar(parent, columns, headings=None, widths=None, height=12, **kwargs):
    """Creates a ttk.Treeview with attached vertical scrollbar inside a container frame."""
    container = ttk.Frame(parent)
    tree = ttk.Treeview(container, columns=columns, show="headings", height=height, **kwargs)
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
        for col, w in zip(columns, widths):
            tree.column(col, width=w, anchor="w")

    tree.tag_configure("even", background=SURFACE)
    tree.tag_configure("odd", background=SURFACE_ALT)

    return container, tree


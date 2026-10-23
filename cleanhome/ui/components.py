"""Reusable UI building blocks.

Atoms -> molecules -> organisms, in the order used by the reference design.
Pages assemble these and never create one-off styled widgets of their own.
"""

from __future__ import annotations

import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import ttk
from typing import Callable

from cleanhome import config, theme, utils
from cleanhome.services.booking_service import STATUS_LABELS, available_slots


# ── Icons (Canvas-drawn, no external assets) ─────────────────────────────────
class _IconCanvas(tk.Canvas):
    def __init__(self, parent, size: int = theme.ICON_SIZE, bg: str = theme.BG_SURFACE, **kwargs):
        kwargs.setdefault("width", size)
        kwargs.setdefault("height", size)
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bd", 0)
        super().__init__(parent, bg=bg, **kwargs)
        self.size = size


class SparkleIcon(_IconCanvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        s = self.size
        c = s / 2.0
        dot = theme.ICON_DOT_RADIUS
        arm = theme.ICON_ARM_LENGTH
        edge = theme.ICON_EDGE_INSET
        self.create_oval(c - dot, c - dot, c + dot, c + dot, fill=theme.PRIMARY, outline="")
        self.create_line(c, edge, c, c - arm, fill=theme.PRIMARY, width=theme.STROKE_WIDTH)
        self.create_line(c, s - edge, c, c + arm, fill=theme.PRIMARY, width=theme.STROKE_WIDTH)
        self.create_line(edge, c, c - arm, c, fill=theme.PRIMARY, width=theme.STROKE_WIDTH)
        self.create_line(s - edge, c, c + arm, c, fill=theme.PRIMARY, width=theme.STROKE_WIDTH)


class ClockIcon(_IconCanvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        s = self.size
        c = s / 2.0
        ring = theme.ICON_RING_INSET
        self.create_oval(ring, ring, s - ring, s - ring, outline=theme.PRIMARY,
                         width=theme.STROKE_WIDTH)
        self.create_line(c, c, c, c - theme.ICON_HAND_LONG, fill=theme.PRIMARY,
                         width=theme.STROKE_WIDTH)
        self.create_line(c, c, c + theme.ICON_HAND_SHORT, c + theme.ICON_EDGE_INSET,
                         fill=theme.PRIMARY, width=theme.STROKE_WIDTH)


class ShieldIcon(_IconCanvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        s = self.size
        c = s / 2.0
        side = theme.ICON_SHIELD_INSET
        shoulder = theme.ICON_SHIELD_SHOULDER
        self.create_polygon(c, side, s - side, shoulder, s - side, c, c, s - side,
                            side, c, side, shoulder,
                            fill="", outline=theme.PRIMARY, width=theme.STROKE_WIDTH)
        (x1, y1), (x2, y2), (x3, y3) = theme.ICON_SHIELD_TICK
        self.create_line(c + x1, c + y1, c + x2, c + y2, fill=theme.PRIMARY,
                         width=theme.STROKE_WIDTH)
        self.create_line(c + x2, c + y2, c + x3, c + y3, fill=theme.PRIMARY,
                         width=theme.STROKE_WIDTH)


class HeadingLabel(tk.Label):
    """A page title (H1)."""

    def __init__(self, parent, text: str = "", *, surface: bool = False, **kwargs):
        kwargs.setdefault("bg", theme.BG_SURFACE if surface else theme.BG_PAGE)
        kwargs.setdefault("fg", theme.TEXT)
        kwargs.setdefault("font", theme.font("H1"))
        kwargs.setdefault("anchor", "w")
        super().__init__(parent, text=text, **kwargs)


class SubheadingLabel(tk.Label):
    """A card or section title (H2)."""

    def __init__(self, parent, text: str = "", *, surface: bool = False, **kwargs):
        kwargs.setdefault("bg", theme.BG_SURFACE if surface else theme.BG_PAGE)
        kwargs.setdefault("fg", theme.TEXT)
        kwargs.setdefault("font", theme.font("H2"))
        kwargs.setdefault("anchor", "w")
        super().__init__(parent, text=text, **kwargs)


class BodyLabel(tk.Label):
    """A description (BODY)."""

    def __init__(self, parent, text: str = "", *, surface: bool = False, **kwargs):
        kwargs.setdefault("bg", theme.BG_SURFACE if surface else theme.BG_PAGE)
        kwargs.setdefault("fg", theme.TEXT_BODY)
        kwargs.setdefault("font", theme.font("BODY"))
        kwargs.setdefault("anchor", "w")
        super().__init__(parent, text=text, **kwargs)


class CaptionLabel(tk.Label):
    """A hint or muted caption (CAPTION)."""

    def __init__(self, parent, text: str = "", *, surface: bool = False, **kwargs):
        kwargs.setdefault("bg", theme.BG_SURFACE if surface else theme.BG_PAGE)
        kwargs.setdefault("fg", theme.TEXT_MUTED)
        kwargs.setdefault("font", theme.font("CAPTION"))
        kwargs.setdefault("anchor", "w")
        super().__init__(parent, text=text, **kwargs)


class PriceLabel(tk.Label):
    """A price (PRICE, in the primary colour)."""

    def __init__(self, parent, text: str = "", *, surface: bool = False, **kwargs):
        kwargs.setdefault("bg", theme.BG_SURFACE if surface else theme.BG_PAGE)
        kwargs.setdefault("fg", theme.PRIMARY)
        kwargs.setdefault("font", theme.font("PRICE"))
        kwargs.setdefault("anchor", "w")
        super().__init__(parent, text=text, **kwargs)


class BrandLabel(tk.Label):
    """The company name in the navigation bar and the footer."""

    def __init__(self, parent, text: str = "", size: int = theme.BRAND_FONT_SIZE, **kwargs):
        kwargs.setdefault("bg", theme.BG_SURFACE)
        kwargs.setdefault("fg", theme.TEXT)
        kwargs.setdefault("font", (theme.FONT_FAMILY, size, "bold"))
        kwargs.setdefault("anchor", "w")
        super().__init__(parent, text=text, **kwargs)


class HeroLabel(tk.Label):
    """The large headline on the home page."""

    def __init__(self, parent, text: str = "", **kwargs):
        kwargs.setdefault("bg", theme.BG_SURFACE)
        kwargs.setdefault("fg", theme.TEXT)
        kwargs.setdefault("font", (theme.FONT_FAMILY, theme.HERO_FONT_SIZE, "bold"))
        super().__init__(parent, text=text, **kwargs)


class DateCombo(ttk.Combobox):
    """A read-only date picker.

    The customer never types a date: the list is generated from today onwards.
    """

    def __init__(self, parent, days: int = config.DATE_PICKER_DAYS, start_offset: int = 0,
                 optional: bool = False, **kwargs):
        self._values: list[tuple[str, str]] = []
        self._offset = 1 if optional else 0
        first = date.today() + timedelta(days=start_offset)
        for offset in range(days):
            day = first + timedelta(days=offset)
            self._values.append((day.isoformat(), day.strftime("%a, %b %d, %Y")))
        kwargs.setdefault("state", "readonly")
        kwargs.setdefault("width", theme.FIELD_WIDTH_DATE)
        labels = [label for _, label in self._values]
        if optional:
            labels.insert(0, "Any date")
        kwargs.setdefault("values", labels)
        super().__init__(parent, **kwargs)
        self.current(0)

    def get_date(self) -> date | None:
        """Return the selected date, or None when nothing is selected."""
        index = self.current() - self._offset
        if index < 0 or index >= len(self._values):
            return None
        return date.fromisoformat(self._values[index][0])

    def set_date(self, value: date) -> bool:
        """Select a date, adding it to the list when it is missing."""
        for index, (iso, _) in enumerate(self._values):
            if iso == value.isoformat():
                self.current(index + self._offset)
                return True
        label = value.strftime("%a, %b %d, %Y")
        self._values.append((value.isoformat(), label))
        labels = [text for _, text in self._values]
        if self._offset:
            labels.insert(0, "Any date")
        self.configure(values=labels)
        self.current(len(self._values) - 1 + self._offset)
        return True


class Dropdown(ttk.Combobox):
    """A dropdown the user picks from; nothing is ever typed by hand."""

    def __init__(self, parent, options: list[str], *, on_change: Callable | None = None,
                 textvariable: tk.StringVar | None = None, width: int = theme.DROPDOWN_WIDTH,
                 **kwargs):
        kwargs.setdefault("state", "readonly")
        super().__init__(parent, textvariable=textvariable, width=width, **kwargs)
        self.configure(values=list(options))
        if options:
            self.current(0)
        if on_change:
            self.bind("<<ComboboxSelected>>", lambda event: on_change(self.get()))

    def set_options(self, options: list[str], keep: str = "") -> None:
        """Replace the choices, keeping the current one when it still exists."""
        self.configure(values=list(options))
        if keep and keep in options:
            self.set(keep)
        elif options:
            self.current(0)
        else:
            self.set("")


class SelectBox(ttk.Combobox):
    """A labelled dropdown the user can only pick from.

    Used for sorting and for any other fixed set of choices so nothing is
    ever typed by hand.
    """

    def __init__(self, parent, label: str, options: list[tuple[str, str]], *,
                 on_change: Callable | None = None, width: int = theme.DROPDOWN_SORT, **kwargs):
        super().__init__(parent, style="TCombobox", width=width, **kwargs)
        self.label = ttk.Label(parent, text=label, style="Caption.TLabel")
        self._values = list(options)
        self.configure(values=[text for _, text in self._values],
                       state="readonly")
        if self._values:
            self.current(0)
        if on_change:
            self.bind("<<ComboboxSelected>>", lambda event: on_change(self.get_key()))

    def get_key(self) -> str:
        """Return the key of the selected option."""
        index = self.current()
        if index < 0 or index >= len(self._values):
            return ""
        return self._values[index][0]


class _ClickButton(ttk.Button):
    """A button that shows the pointer cursor only while it is clickable."""

    def __init__(self, parent, text: str, command: Callable | None = None, **kwargs):
        kwargs.setdefault("padding", (theme.BUTTON_PAD_X, theme.BUTTON_PAD_Y))
        super().__init__(parent, text=text, command=command, **kwargs)
        self.bind("<Enter>", self._sync_cursor)
        self.bind("<Leave>", self._reset_cursor)
        self.bind("<Configure>", lambda event: self._ensure_height(), add="+")
        self._sync_cursor()
        self._ensure_height()

    def _ensure_height(self) -> None:
        try:
            self.configure(height=theme.BUTTON_HEIGHT)
        except tk.TclError:
            pass

    def _sync_cursor(self, event: tk.Event | None = None) -> None:
        if "disabled" in self.state():
            self.configure(cursor="")
        else:
            self.configure(cursor="hand2")

    def _reset_cursor(self, event: tk.Event | None = None) -> None:
        self.configure(cursor="")

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        super().configure(cnf, **kwargs)
        if "state" in kwargs:
            self._sync_cursor()
        self._ensure_height()


class PrimaryButton(_ClickButton):
    """The single blue call to action."""

    def __init__(self, parent, text: str, command: Callable | None = None, **kwargs):
        super().__init__(parent, text=text, command=command, style="Primary.TButton", **kwargs)


class SecondaryButton(_ClickButton):
    """A white button with a 1px border."""

    def __init__(self, parent, text: str, command: Callable | None = None, **kwargs):
        super().__init__(parent, text=text, command=command, style="Secondary.TButton", **kwargs)


class DangerButton(_ClickButton):
    """A red button for destructive actions."""

    def __init__(self, parent, text: str, command: Callable | None = None, **kwargs):
        super().__init__(parent, text=text, command=command, style="Danger.TButton", **kwargs)


class TextInput(ttk.Entry):
    """A single-line input that shows a placeholder until it has a value."""

    def __init__(self, parent, placeholder: str = "", **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        self._has_value = False
        if placeholder:
            self.insert(0, placeholder)
            self.configure(foreground=theme.TEXT_MUTED)
            self.bind("<FocusIn>", self._on_focus_in)
            self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, event: tk.Event) -> None:
        if not self._has_value:
            self.delete(0, tk.END)
            self.configure(foreground=theme.TEXT)
            self._has_value = True

    def _on_focus_out(self, event: tk.Event) -> None:
        if not self.get().strip():
            self.insert(0, self.placeholder)
            self.configure(foreground=theme.TEXT_MUTED)
            self._has_value = False

    def get(self) -> str:  # type: ignore[override]
        value = super().get()
        if not self._has_value and value == self.placeholder:
            return ""
        return value.strip()

    def set(self, value: str) -> None:  # type: ignore[override]
        self.delete(0, tk.END)
        if value:
            self.insert(0, value)
            self._has_value = True
            self.configure(foreground=theme.TEXT)
        else:
            self._on_focus_out(tk.Event())


class PasswordInput(ttk.Entry):
    """A password input with a show/hide toggle."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, show="•", **kwargs)
        self._visible = False

    @property
    def revealed(self) -> bool:
        """True while the password is shown as plain text."""
        return self._visible

    def toggle(self) -> None:
        self._visible = not self._visible
        self.configure(show="" if self._visible else "•")

    def get(self) -> str:  # type: ignore[override]
        return super().get()

    def set(self, value: str) -> None:  # type: ignore[override]
        self.delete(0, tk.END)
        if value:
            self.insert(0, value)


class Badge(ttk.Label):
    """A coloured status pill."""

    def __init__(self, parent, text: str, status: str = "", **kwargs):
        style, _ = theme.badge_style(status)
        super().__init__(parent, text=text, style=f"{style}.TLabel", **kwargs)


class Divider(tk.Frame):
    """A 1px horizontal rule."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=theme.BORDER, height=theme.DIVIDER_HEIGHT, **kwargs)
        self.pack_propagate(False)


# ── Molecules ────────────────────────────────────────────────────────────────
class InputRing(tk.Frame):
    """A 2px ring that shows PRIMARY on focus and DANGER on error."""

    def __init__(self, parent, widget: tk.Widget, **kwargs):
        super().__init__(parent, bg=theme.BG_SURFACE, highlightthickness=theme.FOCUS_RING,
                         highlightbackground=theme.BORDER, highlightcolor=theme.PRIMARY,
                         bd=0, **kwargs)
        self._widget = widget
        self._error = False
        widget.pack(in_=self, fill="both", expand=True)
        widget.lift()

    def set_error(self, has_error: bool) -> None:
        self._error = bool(has_error)
        if self._error:
            self.configure(highlightbackground=theme.DANGER)
        else:
            self.configure(highlightbackground=theme.BORDER)

    def set_focus(self, focused: bool) -> None:
        if self._error:
            self.configure(highlightbackground=theme.DANGER)
            return
        if focused:
            self.configure(highlightbackground=theme.PRIMARY,
                           highlightcolor=theme.PRIMARY)
        else:
            self.configure(highlightbackground=theme.BORDER,
                           highlightcolor=theme.PRIMARY)


class FormField(ttk.Frame):
    """A label, a 2px-ring input, and an inline error message."""

    def __init__(self, parent, label: str, *, secret: bool = False,
                 placeholder: str = "", width: int = theme.FIELD_WIDTH,
                 required: bool = False, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        label_row = tk.Frame(self, bg=theme.BG_PAGE)
        label_row.pack(anchor="w", pady=(0, theme.SPACE_XS))
        ttk.Label(label_row, text=label, style="Caption.TLabel").pack(side="left")
        if required:
            tk.Label(label_row, text=" *", bg=theme.BG_PAGE, fg=theme.REQUIRED_MARK,
                     font=theme.font("CAPTION")).pack(side="left")
        if secret:
            row = ttk.Frame(self, style="TFrame")
            row.pack(fill="x")
            self.input = PasswordInput(row, width=width, style="Field.TEntry")
            self._ring = InputRing(row, self.input)
            self._ring.pack(side="left", fill="x", expand=True)
            self._toggle = SecondaryButton(row, "Show", command=self.toggle_password,
                                           width=theme.BUTTON_WIDTH_TOGGLE)
            self._toggle.pack(side="right", padx=(theme.SPACE_SM, 0))
        else:
            self.input = TextInput(self, placeholder=placeholder, width=width,
                                   style="Field.TEntry")
            self._ring = InputRing(self, self.input)
            self._ring.pack(fill="x")
            self._toggle = None

        self.input.bind("<FocusIn>", lambda e: self._ring.set_focus(True), add="+")
        self.input.bind("<FocusOut>", lambda e: self._ring.set_focus(False), add="+")

        self.error_var = tk.StringVar()
        self._error_label = ttk.Label(self, textvariable=self.error_var,
                                      style="Caption.TLabel", foreground=theme.DANGER)
        self._error_label.pack(anchor="w", pady=(theme.SPACE_XS, 0))

    def toggle_password(self) -> None:
        self.input.toggle()
        self._toggle.configure(text="Show" if not self.input.revealed else "Hide")

    def get(self) -> str:
        return self.input.get()

    def set(self, value: str) -> None:
        self.input.set(value)

    def set_error(self, message: str | None) -> None:
        self.error_var.set(message or "")
        self._ring.set_error(bool(message))
        if message:
            self._error_label.pack(anchor="w", pady=(theme.SPACE_XS, 0))
        else:
            self._error_label.pack_forget()

    def clear_error(self) -> None:
        self.set_error(None)

    def focus_field(self) -> None:
        self.input.focus_set()

    def bind_return(self, command: Callable) -> None:
        self.input.bind("<Return>", lambda event: command())


class SearchBar(ttk.Frame):
    """A search box with a clear '×' button."""

    def __init__(self, parent, placeholder: str = "Search", on_change: Callable | None = None,
                 **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        self.input = ttk.Entry(self, style="Field.TEntry")
        self._placeholder = placeholder
        self.input.insert(0, placeholder)
        self.input.configure(foreground=theme.TEXT_MUTED)
        self.input.bind("<FocusIn>", self._ph_in)
        self.input.bind("<FocusOut>", self._ph_out)
        self._ring = InputRing(self, self.input)
        self._ring.pack(side="left")
        self._ring.configure(width=theme.SEARCH_WIDTH)
        self._ring.pack_propagate(False)
        self._ring.configure(height=theme.INPUT_HEIGHT)
        self.input.pack_configure(fill="x", expand=True)
        clear_frame = tk.Frame(self, bg=theme.BG_SURFACE)
        clear_frame.pack(side="left", padx=(theme.SPACE_XS, 0))
        self._clear = tk.Label(clear_frame, text="×", bg=theme.BG_SURFACE, fg=theme.TEXT_MUTED,
                               font=(theme.FONT_FAMILY, theme.CLEAR_ICON_FONT_SIZE, "bold"),
                               cursor="hand2")
        self._clear.pack()
        self._clear.bind("<Button-1>", lambda e: self.clear())
        self._on_change = on_change
        if on_change:
            self.input.bind("<KeyRelease>", lambda e: on_change(self.get()))
            self.input.bind("<KeyRelease>", lambda e: self._update_clear(), add="+")
        self._update_clear()

    def _ph_in(self, event):
        if self.input.get() == self._placeholder:
            self.input.delete(0, tk.END)
            self.input.configure(foreground=theme.TEXT)
        self._ring.set_focus(True)
        self._update_clear()

    def _ph_out(self, event):
        if not self.input.get().strip():
            self.input.insert(0, self._placeholder)
            self.input.configure(foreground=theme.TEXT_MUTED)
        self._ring.set_focus(False)
        self._update_clear()

    def _update_clear(self):
        val = self.input.get()
        if val and val != self._placeholder:
            self._clear.configure(fg=theme.TEXT)
        else:
            self._clear.configure(fg=theme.TEXT_MUTED)

    def get(self) -> str:
        val = self.input.get()
        if val == self._placeholder:
            return ""
        return val.strip()

    def set(self, value: str) -> None:
        self.input.delete(0, tk.END)
        if value:
            self.input.insert(0, value)
            self.input.configure(foreground=theme.TEXT)
        else:
            self.input.insert(0, self._placeholder)
            self.input.configure(foreground=theme.TEXT_MUTED)
        self._update_clear()

    def clear(self):
        self.set("")
        if self._on_change:
            self._on_change("")



class NavItem(tk.Frame):
    """A navigation link: active pill plus a 2px blue accent underline."""

    def __init__(self, parent, text: str, command: Callable, active: bool = False, **kwargs):
        super().__init__(parent, bg=theme.BORDER if not active else theme.BG_SURFACE, 
                         highlightbackground=theme.BORDER, highlightthickness=1 if not active else 0,
                         **kwargs)
        self._active = active
        background = theme.PRIMARY_SOFT if active else theme.BG_SURFACE
        foreground = theme.PRIMARY if active else theme.TEXT
        self._label = tk.Label(self, text=text, bg=background, fg=foreground,
                               font=theme.font("BODY"), padx=theme.SPACE_MD, pady=theme.SPACE_SM,
                               cursor="hand2", bd=0)
        self._label.pack(fill="x")
        self._underline = tk.Frame(self, bg=theme.PRIMARY if active else theme.BG_SURFACE,
                                   height=theme.ACCENT_HEIGHT)
        self._underline.pack(fill="x")
        self._underline.pack_propagate(False)

        self._label.bind("<Button-1>", lambda e: command())
        self._label.bind("<Enter>", self._on_enter)
        self._label.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        if not self._active:
            self._label.configure(bg=theme.BG_PAGE)

    def _on_leave(self, event=None):
        if not self._active:
            self._label.configure(bg=theme.BG_SURFACE)



class StatCard(tk.Frame):
    """A big number with a caption, used on the admin dashboard."""

    def __init__(self, parent, title: str, value: str, caption: str = "", **kwargs):
        super().__init__(parent, bg=theme.BG_SURFACE, highlightbackground=theme.BORDER,
                         highlightthickness=theme.BORDER_WIDTH, bd=0, **kwargs)
        inner = tk.Frame(self, bg=theme.BG_SURFACE, padx=theme.CARD_PAD, pady=theme.CARD_PAD)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=title.upper(), bg=theme.BG_SURFACE, fg=theme.TEXT_MUTED,
                 font=theme.font("CAPTION")).pack(anchor="w")
        tk.Label(inner, text=str(value), bg=theme.BG_SURFACE, fg=theme.TEXT,
                 font=theme.font("H1")).pack(anchor="w", pady=(theme.SPACE_XS, 0))
        if caption:
            tk.Label(inner, text=caption, bg=theme.BG_SURFACE, fg=theme.TEXT_MUTED,
                     font=theme.font("CAPTION")).pack(anchor="w", pady=(theme.SPACE_XS, 0))


class BarChart(tk.Frame):
    """A small labelled column chart drawn on a canvas."""

    def __init__(self, parent, labels, values, *, formatter=utils.format_peso,
                 height: int = theme.CHART_HEIGHT, **kwargs):
        super().__init__(parent, bg=theme.BG_SURFACE, **kwargs)
        self._labels = list(labels)
        self._values = [float(value) for value in values]
        self._formatter = formatter
        self.canvas = tk.Canvas(self, bg=theme.BG_SURFACE, height=height,
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._draw)
        self._draw()

    def _draw(self, event=None) -> None:
        canvas = self.canvas
        canvas.delete("all")
        width = event.width if event is not None else canvas.winfo_width()
        height = event.height if event is not None else canvas.winfo_height()
        left = theme.CHART_PAD_LEFT
        right = width - theme.CHART_PAD_RIGHT
        top = theme.CHART_PAD_TOP
        bottom = height - theme.CHART_PAD_BOTTOM
        if right - left < theme.CHART_PAD_LEFT or bottom - top < theme.CHART_PAD_TOP:
            return
        if not self._values:
            canvas.create_text(width / 2, height / 2, text="No data yet.",
                               fill=theme.TEXT_MUTED, font=theme.font("CAPTION"))
            return

        for line in range(theme.CHART_GRID_LINES + 1):
            y = top + (bottom - top) * line / theme.CHART_GRID_LINES
            canvas.create_line(left, y, right, y, fill=theme.BORDER)

        peak = max(self._values) or 1.0
        span = (right - left) / len(self._values)
        bar_width = max(1.0, span * theme.CHART_BAR_RATIO)
        for index, (label, value) in enumerate(zip(self._labels, self._values)):
            if len(label) > theme.CHART_COLUMN_LABEL_MAX_CHARS:
                label = label[:theme.CHART_COLUMN_LABEL_MAX_CHARS - 1] + "…"
            center = left + span * (index + 0.5)
            bar_top = bottom - (value / peak) * (bottom - top)
            if value > 0:
                bar_top = min(bar_top, bottom - theme.CHART_BAR_MIN_HEIGHT)
                canvas.create_rectangle(center - bar_width / 2, bar_top,
                                        center + bar_width / 2, bottom,
                                        fill=theme.PRIMARY, outline="")
            canvas.create_text(center, bottom + theme.CHART_LABEL_GAP, text=label,
                               anchor="n", fill=theme.TEXT_MUTED,
                               font=theme.font("CAPTION"))
            if value > 0:
                canvas.create_text(center, bar_top - theme.CHART_VALUE_GAP,
                                   text=self._formatter(value), anchor="s",
                                   fill=theme.TEXT_MUTED, font=theme.font("CAPTION"))


class RankingList(tk.Frame):
    """A numbered list of labels with a value on the right."""

    def __init__(self, parent, items, *, value_formatter=utils.format_peso,
                 empty_message: str = "No data yet.", **kwargs):
        super().__init__(parent, bg=theme.BG_SURFACE, **kwargs)
        if not items:
            CaptionLabel(self, text=empty_message, surface=True).pack(
                anchor="w", pady=(theme.SPACE_XS, 0))
            return
        for index, item in enumerate(items):
            row = tk.Frame(self, bg=theme.BG_SURFACE)
            row.pack(fill="x", pady=theme.SPACE_SM)
            rank = tk.Label(row, text=str(index + 1), bg=theme.PRIMARY_SOFT,
                            fg=theme.PRIMARY, font=theme.font("CAPTION"),
                            padx=theme.SPACE_XS, pady=theme.SPACE_XS)
            rank.pack(side="left", anchor="n")
            text = tk.Frame(row, bg=theme.BG_SURFACE)
            text.pack(side="left", fill="x", expand=True, padx=(theme.SPACE_SM, 0))
            BodyLabel(text, text=item["label"], wraplength=theme.WRAP_NARROW,
                      justify="left", surface=True).pack(anchor="w")
            if item.get("caption"):
                CaptionLabel(text, text=item["caption"], surface=True).pack(anchor="w")
            PriceLabel(row, text=value_formatter(item["value"]),
                       surface=True).pack(side="right", anchor="n")
            if index < len(items) - 1:
                Divider(self).pack(fill="x")


class PriceTag(tk.Frame):
    """A price, an optional struck-through original, and the duration."""

    def __init__(self, parent, price, original=None, duration_mins: int | None = None,
                 **kwargs):
        super().__init__(parent, bg=theme.BG_SURFACE, **kwargs)
        tk.Label(self, text=utils.format_peso(price), bg=theme.BG_SURFACE, fg=theme.PRIMARY,
                 font=theme.font("PRICE")).pack(side="left")
        if original is not None and utils.to_decimal(original) > utils.to_decimal(price):
            original_label = tk.Label(self, text=utils.format_peso(original),
                                      bg=theme.BG_SURFACE, fg=theme.TEXT_MUTED,
                                      font=theme.font("CAPTION"))
            original_label.pack(side="left", padx=(theme.SPACE_SM, 0))
            original_label.configure(
                font=(theme.FONT_FAMILY, theme.OVERSTRIKE_FONT_SIZE, "overstrike"))
        if duration_mins:
            tk.Label(self, text=f"  •  {duration_mins} mins", bg=theme.BG_SURFACE,
                     fg=theme.TEXT_MUTED, font=theme.font("CAPTION")).pack(side="left")


class Toggle(tk.Canvas):
    """A toggle switch (atom)."""

    def __init__(self, parent, variable: tk.BooleanVar | None = None, command: Callable | None = None, **kwargs):
        super().__init__(parent, width=theme.TOGGLE_WIDTH, height=theme.TOGGLE_HEIGHT,
                         highlightthickness=0, bd=0, bg=kwargs.pop("bg", theme.BG_SURFACE), **kwargs)
        self.variable = variable or tk.BooleanVar(value=False)
        self.command = command
        self._draw()
        self.bind("<Button-1>", self._toggle)
        self.variable.trace_add("write", lambda *args: self._draw())

    def _draw(self):
        self.delete("all")
        on = bool(self.variable.get())
        track = theme.TOGGLE_ON if on else theme.TOGGLE_OFF
        inset = theme.TOGGLE_INSET
        self.create_rounded_rect(0, 0, theme.TOGGLE_WIDTH, theme.TOGGLE_HEIGHT,
                                 fill=track, outline="")
        thumb_x = (theme.TOGGLE_WIDTH - theme.TOGGLE_HEIGHT + inset) if on else inset
        self.create_oval(thumb_x, inset, thumb_x + theme.TOGGLE_HEIGHT - 2 * inset,
                         theme.TOGGLE_HEIGHT - inset,
                         fill=theme.TOGGLE_THUMB, outline=theme.BORDER)

    def _toggle(self, event=None):
        self.variable.set(not bool(self.variable.get()))
        if self.command:
            self.command()

    def create_rounded_rect(self, x1, y1, x2, y2, radius=theme.TOGGLE_RADIUS, **kwargs):
        points = [x1 + radius, y1,
                  x1 + radius, y1,
                  x2 - radius, y1,
                  x2 - radius, y1,
                  x2, y1,
                  x2, y1 + radius,
                  x2, y1 + radius,
                  x2, y2 - radius,
                  x2, y2 - radius,
                  x2, y2,
                  x2 - radius, y2,
                  x2 - radius, y2,
                  x1 + radius, y2,
                  x1 + radius, y2,
                  x1, y2,
                  x1, y2 - radius,
                  x1, y2 - radius,
                  x1, y1 + radius,
                  x1, y1 + radius,
                  x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)


class CheckBox(tk.Canvas):
    """A checkbox (atom)."""

    def __init__(self, parent, variable: tk.BooleanVar | None = None, text: str = "",
                 command: Callable | None = None, **kwargs):
        background = kwargs.pop("bg", theme.BG_SURFACE)
        self._frame = tk.Frame(parent, bg=background)
        super().__init__(self._frame, width=theme.CHECK_SIZE, height=theme.CHECK_SIZE,
                         highlightthickness=0, bd=0, bg=background)
        super().pack(side="left")
        self.variable = variable or tk.BooleanVar(value=False)
        self.command = command
        self._draw()
        self.bind("<Button-1>", self._toggle)
        self.variable.trace_add("write", lambda *args: self._draw())
        if text:
            label = tk.Label(self._frame, text=text, bg=background, fg=theme.TEXT_BODY,
                             font=theme.font("BODY"), cursor="hand2")
            label.pack(side="left", padx=(theme.SPACE_SM, 0))
            label.bind("<Button-1>", self._toggle)

    def _draw(self):
        self.delete("all")
        checked = bool(self.variable.get())
        edge = theme.BORDER_WIDTH
        size = theme.CHECK_SIZE
        self.create_rectangle(edge, edge, size - edge, size - edge,
                              outline=theme.BORDER, fill=theme.BG_SURFACE)
        if checked:
            points = [coordinate for point in theme.CHECK_TICK for coordinate in point]
            self.create_line(*points, fill=theme.CHECK_MARK, width=theme.STROKE_WIDTH)

    def _toggle(self, event=None):
        self.variable.set(not bool(self.variable.get()))
        if self.command:
            self.command()

    def pack(self, **kwargs):
        return self._frame.pack(**kwargs)

    def grid(self, **kwargs):
        return self._frame.grid(**kwargs)

    def place(self, **kwargs):
        return self._frame.place(**kwargs)


# ── Organisms ────────────────────────────────────────────────────────────────
class NavBar(tk.Frame):
    """The top navigation bar. Its links depend on the signed-in role."""

    def __init__(self, parent, app, active: str = ""):
        super().__init__(parent, bg=theme.BG_SURFACE, height=theme.NAVBAR_HEIGHT,
                         highlightbackground=theme.NAVBAR_BORDER, highlightthickness=1)
        self.app = app
        self.pack_propagate(False)
        inner = tk.Frame(self, bg=theme.BG_SURFACE)
        inner.pack(fill="both", expand=True, padx=theme.SPACE_XL)

        brand = BrandLabel(inner, text=config.COMPANY_NAME, size=theme.BRAND_BOLD_SIZE,
                           cursor="hand2")
        brand.pack(side="left", pady=theme.SPACE_MD)
        brand.bind("<Button-1>", lambda e: app.go(app.home_page()))

        badge = tk.Label(inner, text=config.COMPANY_REGION, bg=theme.PRIMARY_SOFT,
                         fg=theme.PRIMARY,
                         font=theme.font("CAPTION"), padx=theme.SPACE_SM, pady=theme.SPACE_XS)
        badge.pack(side="left", padx=(theme.SPACE_SM, 0), pady=theme.SPACE_MD)

        links = tk.Frame(inner, bg=theme.BG_SURFACE)
        links.pack(side="left", padx=theme.SPACE_XL)
        for label, target in self._links():
            NavItem(links, label, lambda t=target: app.go(t), active=label == active).pack(
                side="left", padx=theme.SPACE_XS, pady=theme.SPACE_MD)

        auth = tk.Frame(inner, bg=theme.BG_SURFACE)
        auth.pack(side="right", pady=theme.SPACE_MD)
        self._build_auth(auth)

    def _links(self) -> list[tuple[str, str]]:
        role = self.app.session.role
        if role == "admin":
            return [("Dashboard", "AdminDashboard"), ("Bookings", "AdminBookings"),
                    ("Services", "AdminServices"), ("Promotions", "AdminPromotions"),
                    ("Customers", "AdminCustomers"), ("Reports", "AdminReports")]
        if role == "customer":
            return [("Home", "Home"), ("Services", "Services"), ("Promotions", "Promotions"),
                    ("My Bookings", "MyBookings"), ("About", "About"), ("Contact", "Contact")]
        return [("Home", "Home"), ("Services", "Services"), ("Promotions", "Promotions"),
                ("About", "About"), ("Contact", "Contact")]

    def _build_auth(self, parent: tk.Frame) -> None:
        app = self.app
        if not app.session.is_authenticated:
            login_btn = SecondaryButton(parent, "Log In", command=lambda: app.go("Login"))
            login_btn.pack(side="left", padx=theme.SPACE_XS)
            signup_btn = PrimaryButton(parent, "Sign Up", command=lambda: app.go("Signup"))
            signup_btn.pack(side="left", padx=theme.SPACE_XS)
            return
        name = app.session.user.get("full_name", "")
        tk.Label(parent, text=name, bg=theme.BG_SURFACE, fg=theme.TEXT,
                 font=theme.font("BODY")).pack(side="left", padx=theme.SPACE_SM)
        SecondaryButton(parent, "My Profile",
                        command=lambda: app.go("Profile")).pack(side="left", padx=theme.SPACE_XS)
        DangerButton(parent, "Log Out", command=app.logout).pack(side="left",
                                                                 padx=theme.SPACE_XS)


class ServiceCard(tk.Frame):
    """A service in the catalogue."""

    def __init__(self, parent, service: dict, on_book: Callable | None = None,
                 on_details: Callable | None = None, show_book: bool = True,
                 featured: bool = False, **kwargs):
        border = theme.PRIMARY if featured else theme.BORDER
        thickness = theme.FOCUS_RING if featured else theme.BORDER_WIDTH
        super().__init__(parent, bg=theme.BG_SURFACE, highlightbackground=border,
                         highlightthickness=thickness, bd=0, **kwargs)
        inner = tk.Frame(self, bg=theme.BG_SURFACE, padx=theme.CARD_PAD, pady=theme.CARD_PAD)
        inner.pack(fill="both", expand=True)

        header = tk.Frame(inner, bg=theme.BG_SURFACE)
        header.pack(fill="x")
        SparkleIcon(header, bg=theme.BG_SURFACE).pack(side="left")
        SubheadingLabel(header, text=service["name"], surface=True).pack(
            side="left", padx=(theme.SPACE_SM, 0))
        PriceTag(inner, service["price"], duration_mins=service["duration_mins"]).pack(
            anchor="w", pady=(theme.SPACE_SM, 0))
        if service.get("description"):
            BodyLabel(inner, text=service["description"], wraplength=theme.WRAP_COLUMN,
                      justify="left", surface=True).pack(anchor="w",
                                                       pady=(theme.SPACE_SM, 0))

        if on_details or (on_book and show_book):
            actions = tk.Frame(inner, bg=theme.BG_SURFACE)
            actions.pack(fill="x", pady=(theme.SPACE_MD, 0))
            actions.grid_columnconfigure(0, weight=1, uniform="svc")
            actions.grid_columnconfigure(1, weight=1, uniform="svc")
            column = 0
            if on_details:
                SecondaryButton(actions, "View Details",
                                 command=on_details).grid(row=0, column=column,
                                                          sticky="ew",
                                                          padx=(0, theme.SPACE_SM))
                column += 1
            if on_book and show_book:
                PrimaryButton(actions, "Book Now",
                              command=on_book).grid(row=0, column=column, sticky="ew")


class PromoCard(tk.Frame):
    """A promotion: blue accent line, pill label, big price, full-width CTA."""

    def __init__(self, parent, promo: dict, on_book: Callable | None = None, **kwargs):
        super().__init__(parent, bg=theme.BG_SURFACE, highlightbackground=theme.BORDER,
                         highlightthickness=theme.BORDER_WIDTH, bd=0, **kwargs)
        accent = tk.Frame(self, bg=theme.PRIMARY, height=theme.ACCENT_HEIGHT)
        accent.pack(fill="x")
        inner = tk.Frame(self, bg=theme.BG_SURFACE, padx=theme.CARD_PAD, pady=theme.CARD_PAD)
        inner.pack(fill="both", expand=True)

        pill = tk.Label(inner, text="LIMITED TIME", bg=theme.PRIMARY_SOFT, fg=theme.PRIMARY,
                        font=theme.font("CAPTION"), padx=theme.SPACE_SM, pady=theme.SPACE_XS)
        pill.pack(anchor="w")
        tk.Label(inner, text=promo["title"], bg=theme.BG_SURFACE, fg=theme.TEXT,
                 font=theme.font("H2")).pack(anchor="w", pady=(theme.SPACE_SM, 0))
        value = utils.format_discount(promo)
        tk.Label(inner, text=value, bg=theme.BG_SURFACE, fg=theme.PRIMARY,
                 font=(theme.FONT_FAMILY, theme.PROMO_PRICE_FONT_SIZE, "bold")).pack(
            anchor="w", pady=(theme.SPACE_XS, 0))
        tk.Label(inner, text=f"Ends {utils.format_date(promo['end_date'])}",
                 bg=theme.BG_SURFACE, fg=theme.TEXT_MUTED,
                 font=theme.font("CAPTION")).pack(anchor="w", pady=(theme.SPACE_XS, 0))
        if on_book:
            PrimaryButton(inner, "Book Now", command=on_book).pack(
                fill="x", pady=(theme.SPACE_MD, 0))


class BookingRow(tk.Frame):
    """One booking in a customer's list, with the actions they may take."""

    def __init__(self, parent, booking: dict, *, on_reschedule: Callable | None = None,
                 on_cancel: Callable | None = None, on_open: Callable | None = None,
                 **kwargs):
        super().__init__(parent, bg=theme.BG_SURFACE, highlightbackground=theme.BORDER,
                         highlightthickness=theme.BORDER_WIDTH, bd=0, **kwargs)
        inner = tk.Frame(self, bg=theme.BG_SURFACE, padx=theme.CARD_PAD, pady=theme.CARD_PAD)
        inner.pack(fill="both", expand=True)

        top = tk.Frame(inner, bg=theme.BG_SURFACE)
        top.pack(fill="x")
        SubheadingLabel(top, text=booking.get("service_name", "—"), surface=True).pack(side="left")
        Badge(top, booking_service_label(booking.get("status", "")),
              booking.get("status", "")).pack(side="left", padx=theme.SPACE_SM)
        PriceLabel(top, text=utils.format_peso(booking.get("total_at_booking", 0)),
                   surface=True).pack(side="right")

        BodyLabel(inner, text=utils.format_datetime(booking.get("scheduled_at")),
                  surface=True).pack(anchor="w", pady=(theme.SPACE_XS, 0))
        if booking.get("address"):
            CaptionLabel(inner, text=booking["address"], wraplength=theme.WRAP_CARD,
                         justify="left", surface=True).pack(anchor="w")
        if booking.get("notes"):
            CaptionLabel(inner, text=f"Notes: {booking['notes']}", wraplength=theme.WRAP_CARD,
                         justify="left", surface=True).pack(anchor="w")
        if booking.get("cancel_reason"):
            CaptionLabel(inner, text=f"Cancellation reason: {booking['cancel_reason']}",
                         wraplength=theme.WRAP_CARD, justify="left", surface=True).pack(anchor="w")

        if on_open or on_reschedule or on_cancel:
            actions = tk.Frame(inner, bg=theme.BG_SURFACE)
            actions.pack(anchor="e", pady=(theme.SPACE_MD, 0))
            if on_open:
                SecondaryButton(actions, "View", command=on_open).pack(
                    side="left", padx=(0, theme.SPACE_SM))
            if on_reschedule:
                SecondaryButton(actions, "Reschedule", command=on_reschedule).pack(
                    side="left", padx=(0, theme.SPACE_SM))
            if on_cancel:
                DangerButton(actions, "Cancel", command=on_cancel).pack(side="left")


class NextBookingCard(tk.Frame):
    """The customer's next scheduled cleaning, with a shortcut to their list."""

    def __init__(self, parent, booking: dict, *, on_view: Callable,
                 on_book: Callable | None = None, **kwargs):
        super().__init__(parent, bg=theme.BG_SURFACE, highlightbackground=theme.BORDER,
                         highlightthickness=theme.BORDER_WIDTH, bd=0, **kwargs)
        accent = tk.Frame(self, bg=theme.PRIMARY, height=theme.ACCENT_HEIGHT)
        accent.pack(fill="x")
        inner = tk.Frame(self, bg=theme.BG_SURFACE, padx=theme.CARD_PAD,
                         pady=theme.CARD_PAD)
        inner.pack(fill="both", expand=True)

        top = tk.Frame(inner, bg=theme.BG_SURFACE)
        top.pack(fill="x")
        CaptionLabel(top, text="YOUR NEXT CLEANING", surface=True).pack(side="left")
        Badge(top, booking_service_label(booking.get("status", "")),
              booking.get("status", "")).pack(side="left", padx=theme.SPACE_SM)
        PriceLabel(top, text=utils.format_peso(booking.get("total_at_booking", 0)),
                   surface=True).pack(side="right")

        SubheadingLabel(inner, text=booking.get("service_name", ""),
                        surface=True).pack(anchor="w", pady=(theme.SPACE_SM, 0))
        BodyLabel(inner, text=utils.format_datetime(booking.get("scheduled_at")),
                  surface=True).pack(anchor="w", pady=(theme.SPACE_XS, 0))
        if booking.get("address"):
            CaptionLabel(inner, text=booking["address"], wraplength=theme.WRAP_CARD,
                         justify="left", surface=True).pack(anchor="w")

        actions = tk.Frame(inner, bg=theme.BG_SURFACE)
        actions.pack(anchor="w", pady=(theme.SPACE_MD, 0))
        PrimaryButton(actions, "View My Bookings", command=on_view).pack(side="left")
        if on_book:
            SecondaryButton(actions, "Book Another", command=on_book).pack(
                side="left", padx=(theme.SPACE_SM, 0))


class DataTable(ttk.Frame):
    """A treeview table with a scrollbar."""

    def __init__(self, parent, columns, headings=None, widths=None,
                 height=theme.DATA_TABLE_HEIGHT, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        self.container, self.tree = theme.make_treeview_with_scrollbar(
            self, columns=columns, headings=headings, widths=widths, height=height)
        self.container.pack(fill="both", expand=True)

    def add_row(self, values, index: int = 0) -> None:
        tag = "even" if index % 2 == 0 else "odd"
        self.tree.insert("", "end", values=values, tags=(tag,))

    def clear(self) -> None:
        self.tree.delete(*self.tree.get_children())


class Footer(tk.Frame):
    """The site footer: brand, quick links, contact, and a copyright line.

    The footer is deliberately compact (about 130px). It is pinned to the
    bottom of the window, so a short page shows the gap in the page
    background colour above the footer rather than inside it.
    """

    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, bg=theme.BG_SURFACE, highlightbackground=theme.BORDER,
                         highlightthickness=0, **kwargs)
        self.app = app
        columns = tk.Frame(self, bg=theme.BG_SURFACE)
        columns.pack(fill="x", padx=theme.SPACE_XL, pady=(theme.SPACE_LG, theme.SPACE_SM))

        brand = tk.Frame(columns, bg=theme.BG_SURFACE)
        brand.pack(side="left", fill="x", expand=True)
        BrandLabel(brand, text=config.COMPANY_NAME).pack(anchor="w")
        tk.Label(brand, text=config.COMPANY_TAGLINE, bg=theme.BG_SURFACE, fg=theme.TEXT_MUTED,
                 font=theme.font("CAPTION"), wraplength=theme.WRAP_COLUMN,
                 justify="left").pack(anchor="w", pady=(theme.SPACE_XS, 0))

        links = tk.Frame(columns, bg=theme.BG_SURFACE)
        links.pack(side="left", padx=theme.SPACE_LG)
        tk.Label(links, text="QUICK LINKS", bg=theme.BG_SURFACE, fg=theme.TEXT_MUTED,
                 font=theme.font("CAPTION")).pack(anchor="w", pady=(0, theme.SPACE_XS))
        link_row = tk.Frame(links, bg=theme.BG_SURFACE)
        link_row.pack(anchor="w")
        for index, (label, target) in enumerate((("Services", "Services"),
                                                 ("Promotions", "Promotions"),
                                                 ("About", "About"),
                                                 ("Contact", "Contact"))):
            link = tk.Label(link_row, text=label, bg=theme.BG_SURFACE, fg=theme.TEXT_BODY,
                            font=theme.font("CAPTION"), cursor="hand2")
            link.pack(side="left", padx=(0 if index == 0 else theme.SPACE_MD, 0))
            if app is not None:
                link.bind("<Button-1>", lambda e, t=target: app.go(t))

        contact = tk.Frame(columns, bg=theme.BG_SURFACE)
        contact.pack(side="left", padx=theme.SPACE_LG)
        tk.Label(contact, text="CONTACT", bg=theme.BG_SURFACE, fg=theme.TEXT_MUTED,
                 font=theme.font("CAPTION")).pack(anchor="w", pady=(0, theme.SPACE_XS))
        tk.Label(contact,
                 text=f"{config.COMPANY_PHONE}  ·  {config.COMPANY_EMAIL}",
                 bg=theme.BG_SURFACE, fg=theme.TEXT_BODY,
                 font=theme.font("CAPTION")).pack(anchor="w")
        tk.Label(contact, text=config.COMPANY_HOURS, bg=theme.BG_SURFACE, fg=theme.TEXT_MUTED,
                 font=theme.font("CAPTION")).pack(anchor="w")

        Divider(self).pack(fill="x", padx=theme.SPACE_XL)
        tk.Label(self, text=f"© {date.today().year} {config.COMPANY_NAME}. All rights reserved.",
                 bg=theme.BG_SURFACE, fg=theme.TEXT_MUTED,
                 font=theme.font("CAPTION")).pack(anchor="w", padx=theme.SPACE_XL,
                                                   pady=(theme.SPACE_SM, theme.SPACE_MD))


class Toast(tk.Frame):
    """A small transient message shown at the top of the window."""

    KINDS = {
        "info": (theme.PRIMARY, theme.TEXT_ON_ACCENT),
        "success": (theme.SUCCESS, theme.TEXT_ON_ACCENT),
        "warning": (theme.WARNING, theme.TEXT_ON_ACCENT),
        "error": (theme.DANGER, theme.TEXT_ON_ACCENT),
        "copied": (theme.TOAST_BG, theme.TOAST_TEXT),
    }

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=theme.TOAST_BG, **kwargs)
        self.app = app
        self.var = tk.StringVar()
        self.label = tk.Label(self, textvariable=self.var, bg=theme.TOAST_BG,
                              fg=theme.TOAST_TEXT,
                              font=theme.font("BODY"), padx=theme.SPACE_MD, pady=theme.SPACE_SM)
        self.label.pack(side="left")
        self._after_id = None
        self.place(relx=0, rely=0, relwidth=1.0, height=0)
        self.place_forget()

    def show(self, message: str, kind: str = "info") -> None:
        background, foreground = self.KINDS.get(kind, self.KINDS["info"])
        self.configure(bg=background)
        self.label.configure(bg=background, fg=foreground)
        self.var.set(message)
        self.place(relx=0, rely=0, relwidth=1.0, height=theme.TOAST_HEIGHT)
        self.lift()
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(theme.TOAST_DURATION_MS, self.hide)

    def hide(self) -> None:
        self.place_forget()
        self._after_id = None


def booking_service_label(status: str) -> str:
    """Return the human label for a booking status."""
    return STATUS_LABELS.get(status, status.replace("_", " ").title())


# ── Dialogs ──────────────────────────────────────────────────────────────────
class FormMixin:
    """Shared error handling for a form built from ``FormField`` widgets.

    A page or dialog sets ``_fields`` (a dict keyed by the service's field
    name) and, for a page, ``error_label``; it then reuses these helpers
    instead of writing its own copies.
    """

    _fields: dict

    def clear_form_errors(self) -> None:
        """Clear the inline error on every field."""
        for field in self._fields.values():
            field.clear_error()

    def show_form_error(self, message: str) -> None:
        """Show a message that does not belong to one particular field."""
        self.error_label.configure(text=message)
        self.error_label.pack(anchor="w", pady=(0, theme.SPACE_SM))

    def show_field_error(self, error) -> None:
        """Put a validation error under its field, or on the form if unknown."""
        field = self._fields.get(getattr(error, "field", None) or "")
        if field is not None:
            field.set_error(str(error))
        else:
            self.show_form_error(str(error))


class FormDialog(FormMixin, tk.Toplevel):
    """A modal dialog with a form body and Cancel / Save buttons.

    Subclasses fill ``self.body`` with fields and implement ``_submit``.
    Call ``self.saved()`` after a successful save.
    """

    def __init__(self, parent, title: str, on_saved: Callable[[], None] | None = None,
                 save_label: str = "Save"):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title(title)
        self.resizable(False, False)
        self.on_saved = on_saved
        self._center_on_parent(parent)

        container = tk.Frame(self, bg=theme.BG_SURFACE, padx=theme.SPACE_XL,
                             pady=theme.SPACE_LG)
        container.pack(fill="both", expand=True)
        self.body = tk.Frame(container, bg=theme.BG_SURFACE)
        self.body.pack(fill="both", expand=True)
        actions = tk.Frame(container, bg=theme.BG_SURFACE)
        actions.pack(anchor="e", pady=(theme.SPACE_MD, 0))
        SecondaryButton(actions, "Cancel", command=self.close).pack(
            side="left", padx=(0, theme.SPACE_SM))
        PrimaryButton(actions, save_label, command=self._submit).pack(side="left")
        self.bind("<Escape>", lambda event: self.close())

    def _submit(self) -> None:
        raise NotImplementedError

    def show_form_error(self, message: str) -> None:
        self.app_flash(message)

    def app_flash(self, message: str, kind: str = "error") -> None:
        """Send a message to the window that opened this dialog."""
        app = getattr(self.master, "app", None)
        if app is not None:
            app.flash(message, kind)

    def close(self) -> None:
        self.grab_release()
        self.destroy()

    def saved(self) -> None:
        """Close the dialog and tell the page that something changed."""
        self.close()
        if self.on_saved is not None:
            self.on_saved()

    def _center_on_parent(self, parent: tk.Misc) -> None:
        """Position this dialog over the centre of its parent window."""
        self.update_idletasks()
        try:
            root = parent.winfo_toplevel()
            px = root.winfo_rootx() + root.winfo_width() // 2
            py = root.winfo_rooty() + root.winfo_height() // 2
            w, h = self.winfo_width(), self.winfo_height()
            self.geometry(f"+{px - w // 2}+{py - h // 2}")
        except tk.TclError:
            pass


class CancelDialog(tk.Toplevel):
    """Ask for a cancellation reason before a booking is cancelled."""

    def __init__(self, parent, on_submit: Callable[[str], None], *,
                 require_reason: bool = True, title: str = "Cancel Booking"):
        super().__init__(parent)
        self.result: str | None = None
        self.submitted = False
        self.require_reason = require_reason
        self.on_submit = on_submit
        self.title(title)
        self.transient(parent)
        self.resizable(False, False)
        self.grab_set()
        self._center_on_parent(parent)

        frame = tk.Frame(self, bg=theme.BG_SURFACE, padx=theme.SPACE_XL,
                         pady=theme.SPACE_LG)
        frame.pack(fill="both", expand=True)
        SubheadingLabel(frame, text=title, surface=True).pack(anchor="w")
        prompt = ("Tell us why you are cancelling. This helps us improve."
                  if require_reason else
                  "Add a reason (optional).")
        BodyLabel(frame, text=prompt, wraplength=theme.WRAP_DIALOG,
                  justify="left", surface=True).pack(anchor="w",
                                                    pady=(theme.SPACE_XS, theme.SPACE_MD))
        self.reason = TextInput(frame, width=theme.FIELD_WIDTH_DIALOG)
        self.reason.pack(fill="x")
        self.reason.bind("<Return>", lambda event: self._submit())
        self.error = CaptionLabel(frame, text="", surface=True)
        self.error.configure(fg=theme.DANGER)
        self.error.pack(anchor="w", pady=(theme.SPACE_XS, 0))

        actions = tk.Frame(frame, bg=theme.BG_SURFACE)
        actions.pack(anchor="e", pady=(theme.SPACE_MD, 0))
        SecondaryButton(actions, "Keep It", command=self._close).pack(
            side="left", padx=(0, theme.SPACE_SM))
        DangerButton(actions, "Cancel Booking", command=self._submit).pack(side="left")

        self.bind("<Escape>", lambda event: self._close())
        self.wait_window(self)
        if self.submitted:
            on_submit(self.result or "")

    def _submit(self) -> None:
        reason = self.reason.get()
        if not reason and self.require_reason:
            self.error.configure(text="A reason is required.")
            return
        self.result = reason
        self.submitted = True
        self._close()

    def _close(self) -> None:
        self.grab_release()
        self.destroy()

    def _center_on_parent(self, parent: tk.Misc) -> None:
        """Position this dialog over the centre of its parent window."""
        self.update_idletasks()
        try:
            root = parent.winfo_toplevel()
            px = root.winfo_rootx() + root.winfo_width() // 2
            py = root.winfo_rooty() + root.winfo_height() // 2
            w, h = self.winfo_width(), self.winfo_height()
            self.geometry(f"+{px - w // 2}+{py - h // 2}")
        except tk.TclError:
            pass


class RescheduleDialog(tk.Toplevel):
    """Pick a new date and time for a booking."""

    def __init__(self, parent, service: dict, on_submit: Callable[[object], None]):
        super().__init__(parent)
        self.result: datetime | None = None
        self.submitted = False
        self.service = service
        self._slots: list[datetime] = []
        self.title("Reschedule Booking")
        self.transient(parent)
        self.resizable(False, False)
        self.grab_set()
        self._center_on_parent(parent)

        frame = tk.Frame(self, bg=theme.BG_SURFACE, padx=theme.SPACE_XL,
                         pady=theme.SPACE_LG)
        frame.pack(fill="both", expand=True)
        SubheadingLabel(frame, text="Reschedule Booking", surface=True).pack(anchor="w")
        CaptionLabel(frame, text=service["name"], surface=True).pack(
            anchor="w", pady=(theme.SPACE_XS, theme.SPACE_MD))

        CaptionLabel(frame, text="New date", surface=True).pack(anchor="w")
        self.date = DateCombo(frame, days=config.BOOKING_WINDOW_DAYS)
        self.date.pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_MD))
        self.date.bind("<<ComboboxSelected>>", lambda event: self._refresh_slots())

        CaptionLabel(frame, text="Available times", surface=True).pack(anchor="w")
        self.time = ttk.Combobox(frame, state="readonly", width=theme.DROPDOWN_WIDTH)
        self.time.pack(anchor="w", pady=(theme.SPACE_XS, theme.SPACE_SM))
        self.time.bind("<Return>", lambda event: self._submit())
        self.hint = CaptionLabel(frame, text="", surface=True)
        self.hint.configure(fg=theme.DANGER, wraplength=theme.WRAP_DIALOG, justify="left")
        self.hint.pack(anchor="w")

        actions = tk.Frame(frame, bg=theme.BG_SURFACE)
        actions.pack(anchor="e", pady=(theme.SPACE_MD, 0))
        SecondaryButton(actions, "Close", command=self._close).pack(
            side="left", padx=(0, theme.SPACE_SM))
        PrimaryButton(actions, "Confirm New Time", command=self._submit).pack(side="left")

        self.bind("<Escape>", lambda event: self._close())
        self._refresh_slots()
        self.wait_window(self)
        if self.submitted and self.result is not None:
            on_submit(self.result)

    def _refresh_slots(self) -> None:
        self.time.set("")
        self.hint.configure(text="")
        day = self.date.get_date()
        if day is None:
            self.hint.configure(text="Pick a date first.")
            return
        slots = available_slots(self.service["id"], day)
        if not slots:
            self.hint.configure(text="There are no open slots on that day.")
            return
        self._slots = slots
        self.time.configure(values=[slot.strftime("%I:%M %p").lstrip("0") for slot in slots])
        self.time.current(0)

    def _submit(self) -> None:
        choice = self.time.get()
        if not choice:
            self.hint.configure(text="Choose a time first.")
            return
        day = self.date.get_date()
        if day is None:
            self.hint.configure(text="Pick a date first.")
            return
        for slot in self._slots:
            if slot.strftime("%I:%M %p").lstrip("0") == choice:
                self.result = slot
                self.submitted = True
                self._close()
                return
        self.hint.configure(text="That time is no longer available. Pick another one.")

    def _close(self) -> None:
        self.grab_release()
        self.destroy()

    def _center_on_parent(self, parent: tk.Misc) -> None:
        """Position this dialog over the centre of its parent window."""
        self.update_idletasks()
        try:
            root = parent.winfo_toplevel()
            px = root.winfo_rootx() + root.winfo_width() // 2
            py = root.winfo_rooty() + root.winfo_height() // 2
            w, h = self.winfo_width(), self.winfo_height()
            self.geometry(f"+{px - w // 2}+{py - h // 2}")
        except tk.TclError:
            pass


class ProfileCard(tk.Frame):
    """Avatar initials, name, and role — used on the Profile page."""

    def __init__(self, parent, user: dict, **kwargs):
        super().__init__(parent, bg=theme.BG_SURFACE, highlightbackground=theme.BORDER,
                         highlightthickness=theme.BORDER_WIDTH, bd=0, **kwargs)
        inner = tk.Frame(self, bg=theme.BG_SURFACE, padx=theme.CARD_PAD, pady=theme.CARD_PAD)
        inner.pack(fill="both", expand=True)

        name = (user.get("full_name") or "").strip()
        initials = "".join(part[0] for part in name.split()[:2]).upper() or "?"
        size = theme.AVATAR_SIZE
        avatar = tk.Canvas(inner, width=size, height=size, bg=theme.BG_SURFACE,
                           highlightthickness=0, bd=0)
        avatar.pack(side="left", anchor="n")
        avatar.create_oval(theme.AVATAR_INSET, theme.AVATAR_INSET,
                           size - theme.AVATAR_INSET, size - theme.AVATAR_INSET,
                           fill=theme.PRIMARY_SOFT, outline="")
        avatar.create_text(size / 2, size / 2, text=initials, fill=theme.PRIMARY,
                           font=(theme.FONT_FAMILY, theme.AVATAR_INITIAL_FONT_SIZE, "bold"))

        details = tk.Frame(inner, bg=theme.BG_SURFACE)
        details.pack(side="left", fill="x", expand=True, padx=(theme.SPACE_MD, 0))
        tk.Label(details, text=name or "—", bg=theme.BG_SURFACE, fg=theme.TEXT,
                 font=theme.font("H2")).pack(anchor="w")
        role = (user.get("role") or "").capitalize()
        tk.Label(details, text=role, bg=theme.BG_SURFACE, fg=theme.TEXT_MUTED,
                 font=theme.font("CAPTION")).pack(anchor="w", pady=(theme.SPACE_XS, 0))
        if user.get("email"):
            tk.Label(details, text=user["email"], bg=theme.BG_SURFACE, fg=theme.TEXT_BODY,
                     font=theme.font("CAPTION")).pack(anchor="w", pady=(theme.SPACE_XS, 0))


class ConfirmDialog:
    """A yes/no dialog. Pass danger=True for destructive actions."""

    def __init__(self, parent, title: str, message: str, on_confirm: "Callable[[], None]",
                 confirm_label: str = "Confirm", cancel_label: str = "Cancel",
                 danger: bool = False):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.transient(parent)
        self.window.resizable(False, False)
        self.window.grab_set()
        self._center_on_parent(parent)

        frame = tk.Frame(self.window, bg=theme.BG_SURFACE, padx=theme.SPACE_XL,
                         pady=theme.SPACE_LG)
        frame.pack(fill="both", expand=True)
        SubheadingLabel(frame, text=title, surface=True).pack(anchor="w")
        BodyLabel(frame, text=message, surface=True, wraplength=theme.WRAP_DIALOG,
                  justify="left").pack(anchor="w", pady=(theme.SPACE_SM, theme.SPACE_MD))

        actions = tk.Frame(frame, bg=theme.BG_SURFACE)
        actions.pack(anchor="e")
        SecondaryButton(actions, cancel_label, command=self._close).pack(
            side="left", padx=(0, theme.SPACE_SM))
        button_cls = DangerButton if danger else PrimaryButton
        button_cls(actions, confirm_label, command=lambda: self._confirm(on_confirm)).pack(
            side="left")

        self.window.bind("<Escape>", lambda event: self._close())

    def _confirm(self, on_confirm: "Callable[[], None]") -> None:
        on_confirm()
        self._close()

    def _close(self) -> None:
        self.window.grab_release()
        self.window.destroy()

    def _center_on_parent(self, parent: tk.Misc) -> None:
        """Position this dialog over the centre of its parent window."""
        self.window.update_idletasks()
        try:
            root = parent.winfo_toplevel()
            px = root.winfo_rootx() + root.winfo_width() // 2
            py = root.winfo_rooty() + root.winfo_height() // 2
            w, h = self.window.winfo_width(), self.window.winfo_height()
            self.window.geometry(f"+{px - w // 2}+{py - h // 2}")
        except tk.TclError:
            pass


def bind_tab_order(*widgets) -> None:
    """Give a list of focusable widgets a logical Tab / Shift-Tab order."""
    focusables = [widget for widget in widgets if widget is not None]
    for index, widget in enumerate(focusables):
        nxt = focusables[(index + 1) % len(focusables)]
        prv = focusables[(index - 1) % len(focusables)]

        def _focus_next(event, target=nxt):
            target.focus_set()
            return "break"

        def _focus_prev(event, target=prv):
            target.focus_set()
            return "break"

        widget.bind("<Tab>", _focus_next)
        widget.bind("<Shift-Tab>", _focus_prev)


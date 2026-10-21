# CleanHome PH — Production Improvement Spec

> **How to use this file:** Put it in your project root and tell opencode:
> *"Read CLEANHOME_IMPROVEMENT_SPEC.md fully. Do Phase 0 first and stop for my approval before changing any code."*

---

## 0. Ground Rules for the AI

1. **Python 3.11+ and Tkinter/ttk only.** Standard library only (`tkinter`, `sqlite3`, `hashlib`, `secrets`, `re`, `datetime`, `unittest`, `logging`, `dataclasses`). **No** CustomTkinter, Pillow, ttkbootstrap, or any `pip install` for runtime.
2. **Do not invent features** that are not in this spec. If something is unclear, ask before coding.
3. **Back up first.** Copy the current project to `backup_original/` before editing.
4. **The app must run after every phase.** Do not leave it half-broken between phases.
5. **Report, don't hide.** For every bug found, say what it was, where it was, and how it was fixed.
6. **No placeholder text, leftover debug text, or fake data in the UI.** (Example of a real bug already visible: the service name `Window Deep Wash d1ff` has stray characters.)
7. Keep code readable: type hints, short functions, docstrings only where logic is not obvious, no dead code, no commented-out code.

---

## 1. Product Purpose

CleanHome PH is a desktop app for a cleaning-services company in Metro Manila.
**Customers** browse services, book a cleaning, and track their bookings.
**Admins** (company staff) manage services, promos, bookings, and customers.

Currency is Philippine peso (₱). Times are Philippine Standard Time.

---

## 2. Phase 0 — Audit (NO code changes yet)

Read every file, then produce `AUDIT.md` containing:

| Section | What to list |
|---|---|
| Bugs & crashes | Exceptions, unhandled `None`, wrong widget references, broken navigation |
| Logic flaws | Double-booking, past-date bookings, wrong price math, promo applied incorrectly, role leaks |
| Security flaws | Plaintext passwords, SQL string-building, hardcoded admin credentials, no input validation |
| UI/UX flaws | Inconsistent fonts/colors/spacing, blank gaps, unclickable areas, missing feedback, missing empty states |
| Dead code | Unused imports, functions, variables, widgets, files, duplicated blocks |
| Inconsistencies | Naming, text casing, currency formatting, date formats |

Also check these **known issues** from the current screenshot:

- Stray text in a service name (`Window Deep Wash d1ff`).
- The `₱` sign may render wrongly on some fonts — verify and fix by choosing a font that supports it.
- Emoji used as icons (timer icon) render differently per machine — replace with a consistent approach (see §5.6).
- Header shows both **Log In** and **Sign Up Free** with different styles from the rest of the buttons.
- Big blank area at the bottom of the Home page above/below the footer (see §6).
- Scroll area behavior: scrollbar, mouse wheel, and resize must all work.

**Stop after writing `AUDIT.md` and wait for approval.**

---

## 3. Roles, Permissions, and Visibility

There are three kinds of visitors. The role is decided **only by the account in the database**, never by a button on the login screen.

### 3.1 Permission Matrix

| Capability | Guest (not logged in) | Customer | Admin |
|---|:---:|:---:|:---:|
| View Home, Services, Promotions, About, Contact | ✅ | ✅ | ✅ |
| View service details (price, duration, description) | ✅ | ✅ | ✅ |
| Sign up / Log in | ✅ | — | — |
| Click **Book Now** | ➜ sent to Login, then returned to the booking | ✅ | ❌ (hidden) |
| Create a booking | ❌ | ✅ | ❌ |
| View **own** bookings | ❌ | ✅ | ❌ |
| Cancel **own** booking (only if Pending/Confirmed and ≥ 24 h before) | ❌ | ✅ | ✅ (any, with reason) |
| Edit own profile (name, phone, address) | ❌ | ✅ | ✅ (own) |
| Change own password | ❌ | ✅ | ✅ |
| View **all** bookings | ❌ | ❌ | ✅ |
| Change booking status | ❌ | ❌ | ✅ |
| Add / edit / archive services | ❌ | ❌ | ✅ |
| Add / edit / end promotions | ❌ | ❌ | ✅ |
| View customer list & contact info | ❌ | ❌ | ✅ |
| Deactivate / reactivate a customer account | ❌ | ❌ | ✅ |
| View dashboard & reports | ❌ | ❌ | ✅ |
| Create other admin accounts | ❌ | ❌ | ✅ |

### 3.2 What each role SEES (navigation)

- **Guest:** `Home · Services · Promotions · About · Contact` + `Log In` + `Sign Up`
- **Customer:** `Home · Services · Promotions · My Bookings · About · Contact` + profile menu (`My Profile · Change Password · Log Out`)
- **Admin:** `Dashboard · Bookings · Services · Promotions · Customers · Reports` + profile menu (`My Profile · Change Password · Log Out`).
  Admins do **not** see the customer marketing pages as their main navigation, and do **not** see **Book Now**.

Rules:
- Hide controls a role cannot use. Do not just disable them.
- **Enforce permissions in the logic layer too**, not only by hiding buttons. Every admin function must re-check `current_user.role == "admin"` and raise `PermissionError` otherwise.

---

## 4. Authentication Redesign

### 4.1 Login screen
- Fields: **Email**, **Password** (with show/hide toggle). One **Log In** button. A "Don't have an account? Sign up" link.
- **Remove the Customer/Admin selector entirely.** After a successful login, read `role` from the user record and route:
  - `customer` → Home (or the page they were trying to reach)
  - `admin` → Dashboard
- Error message must be generic: *"Incorrect email or password."* (never reveal which one was wrong).
- Pressing **Enter** submits. Focus starts in the Email field.
- After **5 failed attempts** for the same email, lock login for 5 minutes and show the remaining time.

### 4.2 Sign-up screen (customers only)
Fields: Full name, Email, Mobile number, Password, Confirm password.
Validation:
- Email: valid format, unique (case-insensitive).
- Mobile: PH format `09XXXXXXXXX` or `+639XXXXXXXXX`.
- Password: min 8 chars, at least 1 letter and 1 number.
- Show an inline red error message under the field (see Atomic Grid "Email / Error message" molecule), not only a popup.
- Sign-up can **never** create an admin.

### 4.3 Admin accounts
- No hardcoded admin password in source code.
- On first run, if no admin exists, show a one-time **"Create Admin Account"** screen.
- Additional admins can only be created by an existing admin (Customers → Add Admin).

### 4.4 Password storage
- Hash with `hashlib.pbkdf2_hmac('sha256', password, salt, 200_000)`; store `salt` and `hash`. Use `secrets.token_bytes(16)` for salt and `hmac.compare_digest` to compare.
- Never log or print passwords.

---

## 5. UI/UX — Copy the "Atomic Grid" Reference Style

The reference image (`ui_that_i_like.webp`) is the **template**. Copy its look, structure, and spacing logic. Tkinter cannot do true shadows or rounded corners; imitate them (see §5.5).

### 5.1 Design tokens — put ALL of these in one `theme.py` and use nothing else

```python
# Colors
BG_PAGE      = "#F5F6F8"   # page background (very light gray)
BG_SURFACE   = "#FFFFFF"   # cards, panels, header
BORDER       = "#E5E7EB"   # 1px card borders (fake shadow edge)
SHADOW_EDGE  = "#D9DCE1"   # 1px bottom/right edge to fake a soft shadow
PRIMARY      = "#0A6CF0"   # buttons, links, prices, active nav
PRIMARY_HOVER= "#0856C4"
PRIMARY_SOFT = "#E8F1FE"   # active nav pill, selected rows, badges bg
TEXT         = "#000000"   # headings
TEXT_BODY    = "#666666"   # body text
TEXT_MUTED   = "#9CA3AF"   # captions, hints
DANGER       = "#E5484D"   # errors
SUCCESS      = "#12A150"   # confirmed / completed
SUCCESS_SOFT = "#E6F6EC"
WARNING      = "#B7791F"   # pending
WARNING_SOFT = "#FEF3C7"

# Spacing — 16px grid (multiples of 4/8 only)
SPACE_XS, SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL = 4, 8, 16, 24, 32

# Sizes
BUTTON_HEIGHT = 40
INPUT_HEIGHT  = 40
CARD_PAD      = 16
CONTENT_MAX_WIDTH = 1100   # center content; do not stretch to full width on big monitors
```

**Fonts:** the reference uses Geist Sans / Inter, which are not installed by default. Detect with `tkinter.font.families()` and pick the first available of: `Inter`, `Geist`, `Segoe UI`, `Helvetica`. Define a single type scale:

| Token | Size / weight | Use |
|---|---|---|
| `H1` | 24 bold | Page title |
| `H2` | 16 bold | Card title |
| `BODY` | 11 normal | Descriptions |
| `CAPTION` | 10 normal | Hints, muted text |
| `PRICE` | 16 bold, PRIMARY | Prices |

### 5.2 Atomic structure (mirror the reference: Atoms → Molecules → Organisms → Templates)

Build reusable widgets in `ui/components.py`. **Pages must only be assembled from these** — no one-off styled widgets inside pages.

| Level | Components to build |
|---|---|
| **Atoms** | `PrimaryButton`, `SecondaryButton` (white + border), `DangerButton`, `TextInput` (with placeholder), `PasswordInput`, `Badge` (status pill), `Divider`, `Label` variants |
| **Molecules** | `FormField` (label + input + inline error), `SearchBar`, `NavItem` (active pill state), `StatCard` (big number + caption, like "99.9% Uptime"), `PriceTag` (₱ + original strikethrough price + duration) |
| **Organisms** | `NavBar` (logo, badge "Metro Manila", links, auth buttons), `ServiceCard`, `PromoCard` (blue top accent line like the "Pro" card), `BookingRow`, `DataTable`, `Footer` |
| **Templates** | `PageTemplate` (navbar + scrollable content + footer), `AuthTemplate` (centered card), `AdminTemplate` (sidebar/top nav + content) |

### 5.3 Layout rules (from the reference)
- Everything snaps to the 4/8/16 spacing scale. No random `padx=13`.
- White cards on a light gray page. Cards have 1px border, 16px padding, 12px gap between cards.
- One primary action per card (blue button). Secondary action = white button with border.
- Active nav item = `PRIMARY_SOFT` pill with `PRIMARY` text (already close in the screenshot — keep it).
- Content is centered with a max width; side margins grow on large windows.

### 5.4 Button & input behavior
- Hover state, pressed state, disabled state (greyed, no pointer cursor change) for every button.
- Cursor `hand2` on clickable things only.
- Focus ring (2px `PRIMARY` border) on focused inputs; red border on invalid inputs.
- Tab order is logical; **Enter** submits forms; **Esc** closes dialogs.

### 5.5 Faking shadows and rounded look in Tkinter
- Card = outer `Frame(bg=SHADOW_EDGE)` with 1px extra at bottom/right, containing inner `Frame(bg=BG_SURFACE, highlightbackground=BORDER, highlightthickness=1)`.
- Buttons: use `Label`/`Frame`-based custom buttons (or `ttk.Style` with a custom theme) so hover colors work consistently on Windows. Do not use raw `tk.Button` with default relief.
- Do not draw rounded corners on a `Canvas` unless it is a tiny reusable helper; flat 4px-looking corners via borders are acceptable.

### 5.6 Icons
- Do **not** use emoji as icons. Use either plain text symbols that exist in the chosen font, or tiny `Canvas`-drawn shapes (clock, check, X) built once in `components.py`.

### 5.7 Required UX behaviors
- **Empty states:** "No bookings yet — Browse services" instead of a blank page.
- **Loading/feedback:** after any action show a small toast/inline message ("Booking submitted"). Use a reusable `Toast` component, not scattered `messagebox` popups. Keep `messagebox` only for destructive confirmations (cancel booking, archive service).
- **Confirm before destructive actions.**
- **Services page:** show real count ("7 services available" must equal the actual number), add search box + sort (price low→high, duration, name). Card layout stays as in the screenshot; make "Book Now" and "View Details" the same width and align them.
- **Service Details:** modal or page with full description, inclusions, price, duration, promo (if any), and a Book Now button (Customers only).
- **Window:** min size 1000×650, resizable, remember nothing weird; layout must not break when resized or maximized.
- **Scrolling:** mouse wheel scrolls the page on Windows/Linux/Mac only when the cursor is over the scroll area; scrollbar hidden when content fits.
- Consistent casing: Title Case for buttons/nav, sentence case for descriptions.
- Currency always `₱1,299.00` style via one `format_peso()` helper. Dates via one helper, e.g. `Oct 21, 2026 · 2:00 PM`.

---

## 6. Fix: Blank Space in Home Footer

**Symptom:** a large empty area appears at the bottom of the Home page around the footer.

**Likely causes to check and fix (do not guess — find the real one):**
1. Scroll canvas `scrollregion` computed once and never updated → bind `<Configure>` on the inner frame: `canvas.configure(scrollregion=canvas.bbox("all"))`.
2. Inner frame width not synced to canvas width → bind canvas `<Configure>` to `canvas.itemconfigure(window_id, width=event.width)`.
3. Fixed `height=` on a frame, or empty `Frame`/`Label(text="")` used as spacers at the end of the page → delete them.
4. Footer packed with `expand=True` or `fill="both"` → footer must be `fill="x"` with natural height.
5. Excess `pady` on last section.

**Desired result:**
- The footer sits **directly after the last content section**, with only `SPACE_XL` above it.
- If the page content is shorter than the window, the footer sticks to the **bottom of the window** (sticky footer), with the gap placed **between content and footer in the page background color**, never as a white/blank slab inside the footer.
- Footer height is compact (about 120–160px): logo + short tagline, quick links, contact, copyright line.
- Same fix applies to every page that uses `PageTemplate`.

---

## 7. Business Logic

### 7.1 Data (SQLite, file `cleanhome.db`)
Use parameterized queries only (`?` placeholders). Enable `PRAGMA foreign_keys = ON`.

```
users(id, full_name, email UNIQUE, phone, address, role CHECK('customer','admin'),
      pw_salt, pw_hash, is_active, failed_attempts, locked_until, created_at)

services(id, name, description, price, duration_mins, is_active, created_at)

promotions(id, service_id NULL, title, discount_type CHECK('percent','fixed'),
           discount_value, start_date, end_date, is_active)

bookings(id, user_id, service_id, scheduled_at, address, notes,
         price_at_booking, discount_at_booking, status, cancel_reason,
         created_at, updated_at)
```

- **Never delete** a service or user that has bookings. Archive (`is_active = 0`) instead.
- **Store `price_at_booking`** so past bookings don't change when prices change.

### 7.2 Booking rules
- Date/time picker built from `ttk.Combobox` (date, hour, minute) — no free typing of dates.
- Business hours: **8:00 AM – 6:00 PM**, last start time = closing time − service duration. Put hours in `config.py`.
- Cannot book in the past; must be at least **3 hours** from now (configurable).
- **No overlap:** the same time slot cannot be double-booked beyond the company's team capacity (`MAX_CONCURRENT_BOOKINGS = 3` in `config.py`).
- Address is required (prefilled from profile, editable). Notes optional (max 300 chars).
- Show a **summary before confirming**: service, date/time, address, price, discount, total.
- Price math: if a promo is active for that service on that date, apply it once (never stack). Total can never be negative.

### 7.3 Booking status lifecycle

```
Pending ──► Confirmed ──► In Progress ──► Completed
   │            │
   └────────────┴──────► Cancelled
```

- Customer creates → `Pending`.
- Only Admin moves a booking forward. Invalid jumps (e.g., Completed → Pending) are blocked in logic.
- Customer can cancel only `Pending`/`Confirmed` and only ≥ 24 h before the schedule. Admin can cancel any non-completed booking and must enter a reason.
- Each status has a `Badge` color: Pending = WARNING, Confirmed = PRIMARY, In Progress = PRIMARY, Completed = SUCCESS, Cancelled = DANGER.

### 7.4 Customer screens
1. **Home** — hero, featured services (3), active promos, why-choose-us, footer.
2. **Services** — list/search/sort, View Details, Book Now.
3. **Promotions** — only currently active promos, with end date.
4. **Book Service** — form + summary (§7.2).
5. **My Bookings** — table/list, filter by status, cancel, view details. Shows only the logged-in customer's bookings.
6. **My Profile / Change Password.**
7. **About, Contact** — static, no fake data (use a placeholder constant in `config.py` for company phone/email that the company can edit).

### 7.5 Admin screens
1. **Dashboard** — `StatCard`s: Pending bookings, Today's bookings, Completed this month, Revenue this month, Active customers. Below: list of today's and upcoming bookings.
2. **Bookings** — all bookings, filter by status/date/search by customer, change status, cancel with reason, view details (customer name, phone, address).
3. **Services** — table with Add / Edit / Archive. Validation: name unique, price > 0, duration 15–480 mins.
4. **Promotions** — Add / Edit / End promo. Validation: end ≥ start, percent 1–90, fixed < service price.
5. **Customers** — list with search; view booking count; Deactivate/Reactivate. Admin cannot deactivate themselves.
6. **Reports** — date range → total bookings, completed, cancelled, revenue, revenue per service. Export to CSV (`csv` module).

### 7.6 Input validation (everywhere)
- Strip whitespace; reject empty required fields; enforce max lengths.
- Show errors inline under the field. Never crash on bad input.
- Handle `sqlite3` errors with a friendly message and `logging` to `app.log`.

---

## 8. Required Project Structure

```
cleanhome/
├─ main.py                  # entry point only
├─ config.py                # business hours, capacity, company info
├─ theme.py                 # design tokens (§5.1)
├─ db.py                    # connection, schema, migrations, seed
├─ security.py              # hashing, lockout
├─ services/                # logic layer (no tkinter imports)
│   ├─ auth_service.py
│   ├─ booking_service.py
│   ├─ catalog_service.py   # services + promos
│   └─ report_service.py
├─ ui/
│   ├─ components.py        # atoms/molecules/organisms (§5.2)
│   ├─ templates.py
│   ├─ app.py               # window + page router
│   └─ pages/
│       ├─ home.py  services.py  promotions.py  about.py  contact.py
│       ├─ login.py  signup.py  book.py  my_bookings.py  profile.py
│       └─ admin_*.py
├─ tests/                   # unittest for the logic layer
├─ AGENTS.md                # rules for opencode
└─ README.md
```

Rules:
- **Logic layer must not import tkinter.** UI calls services; services call db.
- One page class per file; pages receive `app` (router) and `session` only.
- A single `Session` object holds the current user; clear it on logout and rebuild the navbar.
- Replace global variables with the `Session`/router objects.

---

## 9. Cleanup Checklist (Remove / Fix)

- [ ] All unused imports, functions, variables, widgets, and files deleted
- [ ] No duplicate code blocks (extract helpers)
- [ ] No commented-out code, no `print()` debugging
- [ ] No bare `except:`; catch specific exceptions
- [ ] No hardcoded credentials or sample data in the UI path
- [ ] No magic numbers/colors outside `theme.py` and `config.py`
- [ ] No text typos or stray characters (e.g., `d1ff`)
- [ ] Every button does something; no dead buttons
- [ ] Logout fully resets state; going Back never shows another user's data
- [ ] App closes cleanly (DB connection closed on exit)

---

## 10. Phases and Acceptance Criteria

| Phase | Work | Done when |
|---|---|---|
| **0** | Audit → `AUDIT.md` | I approved it |
| **1** | Restructure folders, `theme.py`, `config.py`, `db.py`, security | App launches; old features still work |
| **2** | Auth redesign (§4) + role routing + permission checks | Login has no role toggle; wrong role can't open other pages |
| **3** | Component library + templates (§5), footer fix (§6) | Home, Services match the reference style; no blank footer gap |
| **4** | Customer features (§7.2–7.4) | Customer can sign up, book, view, cancel |
| **5** | Admin features (§7.5) | Admin can manage everything in the matrix |
| **6** | Tests, cleanup checklist, README | All tests pass; checklist 100% |

After each phase: run the app, list what changed, list anything not finished, and wait for my "continue".

### Minimum tests (`python -m unittest`)
- Password hash/verify, lockout after 5 failures
- Sign-up validation (email, phone, password)
- Booking: past date rejected, outside business hours rejected, capacity overlap rejected, price/promo math
- Status transitions (valid and invalid)
- Permission: customer calling an admin function raises `PermissionError`
- Archive instead of delete when bookings exist

---

## 11. Final Deliverables

1. Working app launched with `python main.py`
2. `AUDIT.md` (what was wrong) and `CHANGELOG.md` (what was fixed)
3. `README.md` — how to run, default first-run admin setup, folder map
4. Passing tests
5. A short **Known Limitations** list (be honest about what Tkinter cannot do)

---

# PART B — For You (not for the AI): Skills, Tools, and Installation

## B1. What "skills" mean here
There are two things: **(a)** the tools/knowledge you need on your computer, and **(b)** "Agent Skills" — reusable instruction folders that opencode can load so its output is more consistent.

## B2. Tools to install (Windows, VS Code)

| Need | Why | Where to get it |
|---|---|---|
| **Python 3.11+** | Runs the app (Tkinter is bundled; tick *"tcl/tk and IDLE"* in the installer) | python.org/downloads → tick **Add Python to PATH** |
| **VS Code** | Editor | code.visualstudio.com |
| **Python + Pylance extensions** | Autocomplete, error hints | VS Code → Extensions (Ctrl+Shift+X) → search "Python" (Microsoft) |
| **Ruff extension** *(dev only)* | Finds unused imports/dead code automatically | Extensions → search "Ruff" (Astral Software) |
| **DB Browser for SQLite** | To look inside `cleanhome.db` | sqlitebrowser.org |
| **Node.js LTS** | Needed to install opencode with npm | nodejs.org |
| **Git** | Lets you undo bad AI edits | git-scm.com |
| **opencode** | Your AI agent | see B3 |

Check your install in the VS Code terminal:
```bash
python --version
python -m tkinter        # a small test window should appear
node --version
git --version
```

Optional dev-only helper (not part of the app): `pip install ruff`, then `ruff check .` to list unused code.

## B3. Installing opencode
(Commands as I know them; confirm on **opencode.ai/docs** since this tool updates fast.)

```bash
npm install -g opencode-ai
```
Then, in your project folder, in the VS Code terminal:
```bash
opencode
```
- Run `/connect` to add your AI provider/API key, and `/models` to pick a model.
- Run `/init` to generate `AGENTS.md` (project rules the AI reads every session). Paste §0 of this file into it.
- opencode also has a VS Code extension (search "opencode" in Extensions); otherwise, just run it in the integrated terminal.

**Workflow tip:** run `git init` and `git commit -am "before AI"` before each phase so you can roll back.

## B4. Agent Skills (optional but recommended)
A skill is a folder with a `SKILL.md` file (name + description + instructions). opencode loads them from the project or your user config. Typical locations (verify in the opencode docs under "Skills"):

- Project: `.opencode/skills/<skill-name>/SKILL.md`
- Global: `~/.config/opencode/skills/<skill-name>/SKILL.md`

**Where to get ready-made skills:** github.com/anthropics/skills (official examples, including `frontend-design` and `skill-creator`). Download the repo, copy the wanted folder into one of the locations above, restart opencode.

```bash
git clone https://github.com/anthropics/skills
# then copy e.g. skills/frontend-design into .opencode/skills/
```
Note: `frontend-design` is written for web UI, but its advice on typography, spacing, and consistency still helps. Tkinter-specific skills are rare, so **write your own**:

### Starter skill you can create: `.opencode/skills/tkinter-design-system/SKILL.md`
```markdown
---
name: tkinter-design-system
description: Use when building or editing any Tkinter UI in this project. Enforces theme tokens, reusable components, and the Atomic Grid style.
---

# Rules
- Import colors, fonts, spacing only from theme.py. Never hardcode hex values or pixel paddings in pages.
- Build UI from components in ui/components.py (atoms -> molecules -> organisms -> templates).
- Pages must not call sqlite3 or contain business logic; call services/ instead.
- Every button needs hover, pressed, and disabled states.
- Every form field uses FormField with inline error text.
- After editing UI, run python main.py and check resize, scroll, and footer spacing.
```

A second one worth making: `python-code-audit` (instructions to find unused code, bare excepts, duplicate logic, and report in `AUDIT.md` format).

## B5. Skills *you* should know (to review the AI's work)
- Tkinter layout: `pack` vs `grid` (don't mix both in the same parent), `Canvas` + scrollbar, `ttk.Style`
- Basic SQL / SQLite (SELECT, INSERT, UPDATE, JOIN)
- Python OOP basics (classes, inheritance for widgets)
- Reading tracebacks and using `git diff`

Free learning: docs.python.org/3/library/tkinter.html, the Python `unittest` docs, and sqlitetutorial.net.

---

## Honest Limitations
- Tkinter cannot render true drop shadows, blur, or smooth rounded corners; the reference style will be an **approximation** (flat cards, borders, consistent spacing/colors).
- Geist/Inter fonts may not exist on every company PC; the app falls back to Segoe UI.
- A desktop SQLite app is single-machine. If several staff need to use it at once on different PCs, the company will need a server-based database — this spec does not cover that.

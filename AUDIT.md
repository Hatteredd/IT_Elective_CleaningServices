# CleanHome PH — Phase 0 Audit

**Date:** 2026-10-21
**Auditor:** opencode
**Scope:** every file in the repository (excluding `venv/`, `.git/`, `__pycache__/`, `.pytest_cache/`)
**Code changed in this phase:** none. `backup_original/` was created before this file was written.
**Spec:** `CLEANHOME_IMPROVEMENT_SPEC.md`

---

## 0. How this audit was performed

| Activity | Result |
|---|---|
| Read every `.py`, `.md`, `.css`, `.html`, `.js`, `.env`, `.txt` file in the repo | Done |
| Launched the Tkinter app and inspected live widget trees | Done (geometry/children captured programmatically) |
| Queried the live SQLite database (`instance/app.db`) | Done |
| Ran runtime behaviour probes (booking, promo, auth, nav) | Done — see §7 Evidence log |
| Ran the existing test suite | `37 passed in 5.36s` — but see DEAD-05 |
| Static scan for unused imports / dead functions / bare `except` | Done (AST-based scanner) |

### Current architecture (as-is)

```
run.py / gui_app.py  ──►  gui/app.py (MainApp: tk.Tk + frame router)
                              │
                              ├── gui/session.py        in-memory Session
                              ├── gui/theme.py          colours, ttk styles, ScrollableFrame
                              └── gui/frames/           public.py, auth.py, customer.py, admin.py
                                      │
                                      ▼
                        app/__init__.py  (create_app → Flask app, used ONLY for db context)
                        app/models.py   (SQLAlchemy models)
                        instance/app.db (SQLite)
```

**The single biggest structural problem:** the desktop app is built on Flask + SQLAlchemy + Werkzeug. The spec (§0, §8) requires a standard-library-only, pure-Tkinter application with its own `sqlite3` layer, a `services/` logic layer, and a `cleanhome/` package. The Flask web app in `app/` (37 Jinja templates, 4 blueprints, WTForms) is a **separate legacy product** that is not part of the spec's target structure.

---

## 1. Bugs & crashes

| ID | What | Where | Evidence | Planned fix |
|---|---|---|---|---|
| **BUG-01** | **Home page scroll area is ~3.5× taller than its content, producing a huge blank slab below the last section.** The canvas scrollregion is `(-2, -2, 2002, 5002)` while the real content is only `1415px` tall. Scrolling to the bottom shows nothing but background grid. | `gui/theme.py:306-318` `_draw_grid()` draws a fixed `2000×5000` grid of ~291 canvas line items; `gui/theme.py:320-321` `_on_inner_configure()` sets `scrollregion = canvas.bbox("all")`, which therefore includes that 5000px grid. | `scrollregion: -2 -2 2002 5002` / `inner req h: 1415` / after scroll-to-bottom `yview: (0.8617, 1.0)` — all content already scrolled past, view shows blank grid. | Phase 3 (§6): draw the grid inside the inner frame, or exclude it from the bbox; recompute `scrollregion` from the inner frame only. **This is the real cause of the "big blank area" — the grid, not a stale scrollregion.** |
| **BUG-02** | **Admin clicking "Book Now" navigates to the Login screen while already authenticated.** | `gui/frames/public.py:367-368` — the button is rendered for every role; `self.go("BookService" if self.session.require_customer() else "Login", …)` sends admins to `Login`. | Runtime probe: admin visits `Services` → click `Book Now` → frames visited `['Services', 'Login']`. | Phase 2/3: hide `Book Now` for admins (spec §3.1: Admin = ❌ hidden); router rejects the target for the wrong role. |
| **BUG-03** | **Guest clicks "Book Now" → Login → after login the customer lands on `CustomerDashboard`, not the booking page.** The intended `service_id` is discarded. | `gui/frames/public.py:368` calls `self.go("Login")` with no payload; `gui/app.py:148-153` `login()` always routes to `CustomerDashboard`/`AdminDashboard`. | Code path confirmed; no "return-to" mechanism exists anywhere. | Phase 2: store the pending target in the session, restore it after login (spec §3.1). |
| **BUG-04** | **Registration accepts a 3-digit phone number and a 3-character password with no digit.** | `gui/frames/auth.py:185-204` `_submit()` only checks emptiness, password match, and email uniqueness. No email-format, no PH-phone-format, no password-strength validation. | Runtime probe: registered with `phone="123"` and password `abc` → `Registration successful! Please log in.` / `phone stored: 123`. | Phase 2: inline `FormField` errors per spec §4.2. |
| **BUG-05** | **`BookService` accepts a booking with 400-character notes.** | `gui/frames/customer.py:315-320` (`tk.Text`, no limit) and `:471` `notes=self.notes.get("1.0", "end").strip()`. | Runtime probe: `stored notes len: 400` (spec limit 300). | Phase 4: enforce max 300 chars with a live counter. |
| **BUG-06** | **Admin can move a booking from `completed` back to `pending`; there is no status-transition validation at all.** | `gui/frames/admin.py:474-480` `_set_status()` writes `b.status = status` unconditionally. The UI at `:462-469` always offers all four target statuses. | Confirmed by direct call; no `status in (...)` guard exists. | Phase 5: enforce the lifecycle in the service layer (spec §7.3). |
| **BUG-07** | **`AdminBookingDetail` "Reschedule" silently resets the booking to `pending` and wipes the assigned cleaner**, even for a completed booking. | `gui/frames/admin.py:499-523`, specifically `:518-519` `b.status = "pending"; b.cleaner_id = None`. | Code read; no status check before reschedule. | Phase 5: guard on current status. |
| **BUG-08** | **Customer-side reschedule has the same unconditional `status = "pending"` / `cleaner_id = None` reset.** | `gui/frames/customer.py:789-810` (`:808-809`). | Code read. | Phase 4. |
| **BUG-09** | **The customer's booking is rejected only for past dates.** Bookings were accepted at `23:30` (after 6 PM close), at `06:00` (before 8 AM open), and same-day with no lead time. | `gui/frames/customer.py:412-414` — the only date guard is `if bdate < date.today()`. | Runtime probes: `23:30` accepted; `06:00` accepted; same-day accepted. | Phase 4: business hours + 3-hour lead time + last-start = closing − duration, all in `config.py`. |
| **BUG-10** | **Notes field on the booking form has no character counter and no `maxlength`; the summary label overflows with long content.** | `gui/frames/customer.py:315-320` | Visual/code read. | Phase 4. |
| **BUG-11** | **`AdminUsers` (Customers) is a read-only table — no search, no deactivate/reactivate, no "Add Admin".** | `gui/frames/admin.py:887-917` `_render()` only inserts rows. | Code read; spec §3.1 and §7.5 require all three. | Phase 5. |
| **BUG-12** | **Admin Services table has no Archive action** (only Add/Edit via double-click). Archived services still show up in the catalog table. | `gui/frames/admin.py:541-567`; column set is `("id","name","base","discounted","duration","active")` — no archive control. | Code read. | Phase 5. |
| **BUG-13** | **No Reports screen exists anywhere in the GUI.** | No `AdminReports` class in `gui/frames/admin.py`; `gui/app.py:104-107` registers no reports frame. | Code read. | Phase 5 (spec §7.5, incl. CSV export). |
| **BUG-14** | **Admin promotions have no "End promo" action** (Add/Edit only). | `gui/frames/admin.py:797` hint text, `_promo_dialog` at `:866-876`. | Code read; spec §7.5 requires Add/Edit/End. | Phase 5. |
| **BUG-15** | **`AdminSettings` cannot reach the `service_areas` field** — `field_defs` has 6 entries but only 5 are written to the grid. | `gui/frames/admin.py:942-957` — loop `for i, (label, key, def_val) in enumerate(field_defs)` runs `i = 0..5`, but the grid was only given `rowconfigure` for column 1; `row=5` is written while the "Save Settings" button occupies `row=len(fields)` = 6. Rows are correct, but `service_areas` is missing from the **saved** set because `save()` iterates `fields` — see INC-09. | Code read. | Phase 5. |
| **BUG-16** | **The flash message overlay covers the top of the page** and is `place()`d at `height=44` over the content area, hiding the page header. | `gui/app.py:81-87`, `:138` `self.flash_label.place(relx=0, rely=0, relwidth=1.0, height=44)`. | Code read — the overlay is above the frame stack (`self.container` is packed at `side="top"`), so it overlays the header. | Phase 3: move feedback into a `Toast` component that does not cover content (spec §5.7). |
| **BUG-17** | **Exceptions raised inside a frame are swallowed with no message and no log.** | `gui/app.py:168-172` `db_session()` re-raises after `db.session.rollback()`, but nothing catches it; `gui/app.py:176-183` `_on_close()` uses `except Exception: pass`. | Code read. | Phase 1/6: `logging` to `app.log` (spec §7.6). |
| **BUG-18** | **Admin views the public marketing navigation.** When an admin is authenticated, `_PublicHeader.build()` still renders `Home · Services · Promotions · About · Contact` plus a `Dashboard` button. | `gui/frames/public.py:40-52` (nav) and `:57-71` (auth block) — no role branch for the nav list. | Code read; spec §3.2: "Admins do not see the customer marketing pages as their main navigation." | Phase 2. |
| **BUG-19** | **The `promo.usage_limit` check is duplicated** — checked at `:452` and again at `:486` inside the redemption loop, after the booking row is already flushed. | `gui/frames/customer.py:452-454` and `:486-489` | Code read. | Phase 4: remove the duplicate. |
| **BUG-20** | **The Services page has no search box and no sort control** (0 `Entry`, 0 `Combobox` on the page). | `gui/frames/public.py:310-368` | Runtime probe: `Combobox count: 0`, `Entry count: 0`. | Phase 4 (spec §5.7). |
| **BUG-21** | **Login does not set initial focus to the Email field and the email `Entry` is created but never focused.** | `gui/frames/auth.py:67-71` | Code read; spec §4.1 requires focus in Email. | Phase 2. |
| **BUG-22** | **`Enter` submits on the Login password field but the focused widget is never the email field, and there is no `<Return>` binding on the `confirm` field of Register.** | `gui/frames/auth.py:71,79` (Login — both bound) vs `:132,165` (Register — `confirm` bound, `phone` not) | Code read. | Phase 2. |
| **BUG-23** | **`scroll.canvas` window width is synced but the inner frame's *height* is never used** — `itemconfig(window_id, width=event.width)` only fixes width; the 5000px height comes from the grid, compounding BUG-01. | `gui/theme.py:323-325` | Code read. | Phase 3. |
| **BUG-24** | **`_draw_grid()` is re-invoked on every canvas `<Configure>`**, recreating ~291 canvas items on every window resize or maximise. | `gui/theme.py:323-325` → `self._draw_grid()` | Code read. | Phase 3. |
| **BUG-25** | **Mouse-wheel scrolling uses `bind_all` plus a string-prefix hack** (`str(w).startswith(str(self))`) and divides `event.delta` by 120, which is Windows-only — macOS trackpad deltas are tiny, so scrolling breaks there. | `gui/theme.py:301-302`, `:327-330` | Code read. | Phase 3. |
| **BUG-26** | **The scrollbar is never hidden when the content fits.** | `gui/theme.py:290,299` — `self.vsb.pack(side="right", fill="y")` unconditionally. | Runtime: Home content 1415px vs 692px view, scrollbar always drawn; spec §5.7 requires auto-hide. | Phase 3. |

---

## 2. Logic flaws

| ID | What | Where | Evidence | Planned fix |
|---|---|---|---|---|
| **LOG-01** | **Overlapping bookings are allowed; the slot check is exact-minute only, so capacity is effectively 1 instead of 3.** A 180-minute "Deep Cleaning" at 10:00 and another at 11:00 were both accepted — two cleaners' worth of work overlapping. | `gui/frames/customer.py:426-427` `Booking.query.filter_by(scheduled_date=bdate, scheduled_time=btime)` | Runtime probe: `10:00` created, `11:00` created, `bookings that day: [(11,'10:00:00'), (12,'11:00:00')]`. An exact duplicate IS rejected (`"The selected date and time slot is already reserved."`). | Phase 4: interval-overlap check + `MAX_CONCURRENT_BOOKINGS = 3` in `config.py`. |
| **LOG-02** | **Service-level `discounted_price` and a promo code are both applied → double discount.** The subtotal is built from the *already-discounted* price, then the promo percentage is subtracted from it. | `gui/frames/customer.py:257`, `:370-371`, `:432-433` (price = `discounted_price` if lower than `base_price`) then `:458-463` (promo subtracted from that subtotal). | Runtime probe on `Window Deep Wash d1ff` (base 899 → discounted 799): `WELCOME10` was computed on the discounted subtotal → `Discount: ₱129.90` on top of an already-reduced price. | Phase 4: apply exactly one discount (spec §7.2 "apply it once, never stack"). |
| **LOG-03** | **The live booking summary and the actual submission use different promo rules.** The summary only checks `code` + `is_active`; it ignores the date window, usage limit, minimum order, and `eligible_services`. | `gui/frames/customer.py:380-390` (summary) vs `:440-465` (submit) | Code read — `_update_summary` has no `start_date`/`end_date`/`usage_limit`/`min_order_value`/`eligible_services` checks. | Phase 4: one shared pricing function. |
| **LOG-04** | **A service-scoped promo applies to every service.** `promo.eligible_services` (a JSON list of service IDs) is never read. | `gui/frames/customer.py:382` and `:442` — `Promotion.query.filter_by(code=code, is_active=True).first()` | Code read. | Phase 4. |
| **LOG-05** | **`is_stackable` is never evaluated.** | `gui/frames/customer.py` — no reference to `is_stackable`; `app/models.py:131` defines it. | Grep. | Phase 4. |
| **LOG-06** | **Customer cancellation ignores the 24-hour rule and stores no reason.** A booking scheduled for 2026-10-15 was cancelled on 2026-10-21 — 6 days in the past. | `gui/frames/customer.py:759-770` `_cancel()` — only checks `b.status in ["pending","confirmed"]` | Runtime probe: past confirmed booking cancelled successfully. | Phase 4/5: 24-hour guard; add `cancel_reason` column. |
| **LOG-07** | **Admin cancellation requires no reason and there is no `cancel_reason` column to store one in.** | `gui/frames/admin.py:462-469` — the "Cancel Booking" button calls `_set_status(b.id, "cancelled")` with no dialog; `app/models.py:145-165` `Booking` has no `cancel_reason`. | Code read. | Phase 5. |
| **LOG-08** | **Admin "Cancel Booking" is a single button next to "Confirm"/"Start Service"/"Mark Completed"** — one mis-click cancels a live job with no confirmation. | `gui/frames/admin.py:466` `("cancelled", "Cancel Booking", "Danger.TButton")` | Code read; spec §7.3 requires a reason prompt. | Phase 5. |
| **LOG-09** | **No customer can be created as an admin, and there is no first-run "Create Admin Account" screen.** | `gui/frames/auth.py:197` hardcodes `role="customer"`; `gui/app.py:73` always starts at `Home`; no admin-creation frame exists. | Code read; spec §4.3. | Phase 2. |
| **LOG-10** | **Cleaners are created with a hardcoded shared password `[redacted]` and cannot change it.** | `gui/frames/admin.py:743` `u.set_password("[redacted]")` | Code read. | Phase 5. |
| **LOG-11** | **Cleaner double-assignment is checked at the exact slot only**, so the same cleaner can be given two overlapping jobs. | `gui/frames/admin.py:440-444` | Code read (same exact-minute pattern as LOG-01). | Phase 5. |
| **LOG-12** | **The booking price is not snapshotted immutably per spec.** `subtotal`/`discount_amount`/`total_amount` are stored, but there is no `price_at_booking` / `discount_at_booking` and `BookingItem.unit_price` stores the *discounted* price, so a later promo change cannot be reconstructed. | `app/models.py:159-161`, `gui/frames/customer.py:476-484` | Code read. | Phase 1 (schema) / Phase 4. |
| **LOG-13** | **There is no business-hours concept anywhere.** Operating hours are a free-text setting ("Mon - Sun: 7:00 AM - 8:00 PM") and the public Contact page hardcodes the same string, contradicting the spec's 8:00 AM – 6:00 PM. | `gui/frames/admin.py:946` `("Operating Hours", "operating_hours", "Mon - Sun: 7:00 AM - 8:00 PM")`; `gui/frames/public.py:596` `("⏰ Hours", "Mon - Sun: 7:00 AM - 8:00 PM")` | Code read. | Phase 1 (`config.py`) + Phase 5. |
| **LOG-14** | **Role enforcement lives in the frame, not in a logic layer, and the router enforces nothing.** `show_frame()` will display any frame to any user; each frame re-implements its own `if not self.session.require_customer(): go("Login")`. | `gui/app.py:121-126` `show_frame()` has no role check; `gui/session.py:24-28` `require_customer()/require_admin()` return a bool but are only consulted inside frames. | Code read. | Phase 2: router-level guard + `PermissionError` in the service layer (spec §3.2). |
| **LOG-15** | **Several frames render their layout *before* the permission check**, so a guest briefly sees an admin/customer shell.** | `gui/frames/customer.py:504-509` (`_layout(...)` then `require_customer()` check); same pattern in `gui/frames/admin.py` `_layout(...)` then `_check_admin()`. | Code read. | Phase 2. |
| **LOG-16** | **A booking can be created for a customer whose account is deactivated**, and `is_active` is not re-checked after login. | `gui/frames/auth.py:111` checks `user.is_active` at login only; no per-action check. | Code read. | Phase 2. |
| **LOG-17** | **`Services` sorts by `base_price` at the DB level but displays the discounted price**, so the on-screen order is not the order the customer sees. | `gui/frames/public.py:314` `order_by(Service.base_price)` vs `:342-344` displays `discounted_price` when lower. | Code read. | Phase 4. |
| **LOG-18** | **The promo "Apply Code" button only re-renders the summary — it does not validate the code.** An invalid code produces no error until the booking is submitted. | `gui/frames/customer.py:312-313` `command=self._update_summary` | Code read. | Phase 4. |
| **LOG-19** | **`Booking` status vocabulary includes `rescheduled`, which is not in the spec lifecycle**, and a live booking row has that status. | `app/models.py:156` comment `pending, confirmed, in_progress, completed, cancelled, rescheduled`; `instance/app.db` booking id=3 has `status='rescheduled'`. | DB query. | Phase 1/5: normalise to the 5 spec states. |
| **LOG-20** | **`Promotion.discount_type` uses `'percentage'`; the spec's schema says `CHECK('percent','fixed')`.** | `app/models.py:121`; usage at `gui/frames/customer.py:384`, `:458` | Code read. | Phase 1 (schema) — pick one vocabulary. |

---

## 3. Security flaws

| ID | What | Where | Evidence | Planned fix |
|---|---|---|---|---|
| **SEC-01** | **Hardcoded admin and customer credentials are embedded in the login screen and auto-submit on click.** | `gui/frames/auth.py:60-65` — `tk.Button(..., text="👑 Admin Demo", …, command=lambda: _fill_creds("admin@cleanhome.ph", "[redacted]"))` and `("customer@cleanhome.ph", "[redacted]")`. `_fill_creds` calls `self._submit()` immediately. | Code read. | Phase 2: remove the demo block entirely (spec §4.3, §9). |
| **SEC-02** | **Hardcoded credentials in the seed scripts and in the admin panel.** | `seed_demo_data.py:3, 36, 40, 51, 144` (`[redacted]`, `[redacted]`, `[redacted]`); `gui/frames/admin.py:743` `u.set_password("[redacted]")` | Grep. | Phase 1/5. |
| **SEC-03** | **No login lockout.** Six consecutive wrong passwords for the same account still allowed a subsequent correct login. `users` has no `failed_attempts` or `locked_until` column. | `gui/frames/auth.py:103-114` `_submit()`; `app/models.py:22-30` `User` columns are only `id, email, password_hash, role, is_active, created_at`; `gui/session.py` has no lock state. | Runtime probe: 6 failures → then success. | Phase 1/2: add `failed_attempts` + `locked_until`; 5 attempts → 5-minute lock (spec §4.1). |
| **SEC-04** | **The password-reset flow reveals which emails are registered.** The token is printed in the UI for a known address while an unknown address gets a different message and no token. | `gui/frames/auth.py:228-256` — `:243-245` sets `text=f"🔑 Reset Token Generated:\n{token_value}"` and flashes "Password reset token generated successfully."; `:254-256` flashes the generic "If that email is registered…" | Code read. | Phase 2: always show the identical generic message; never render the token in the client. |
| **SEC-05** | **The reset token is displayed on screen and handed straight to the next screen via a "Proceed to Set New Password" button**, i.e. the token is not a secret from the person at the machine. | `gui/frames/auth.py:244-253` | Code read. | Phase 2. |
| **SEC-06** | **Password hashing is Werkzeug `scrypt`/`pbkdf2`, not the spec's `hashlib.pbkdf2_hmac('sha256', …, 200_000)` with a stored `salt` and `hash`.** The `users` table has one opaque `password_hash` column and no `pw_salt`/`pw_hash` pair. | `app/models.py:27`; `gui/frames/auth.py:198` `user.set_password(pw)`; `app/models.py:26-30` | Code read. | Phase 1: `cleanhome/security.py` per spec §4.4. |
| **SEC-07** | **The Flask `SECRET_KEY` has an insecure hardcoded default** that is used whenever `.env` is missing. | `app/__init__.py:26` `os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')` | Code read. | Phase 1 (or remove Flask entirely). |
| **SEC-08** | **No input validation on sign-up** — no email format, no PH mobile format, no password strength, no max lengths. | `gui/frames/auth.py:185-204` | Runtime probe (phone `123`, password `abc` accepted). | Phase 2 (spec §4.2). |
| **SEC-09** | **No input validation on the booking form beyond a date/time parse** — no length limits, no address re-validation, no notes limit. | `gui/frames/customer.py:397-423` | Runtime probe (400-char notes). | Phase 4. |
| **SEC-10** | **`PRAGMA foreign_keys = ON` is never issued**, so SQLite does not enforce referential integrity. | `app/__init__.py:86-90` issues only `journal_mode=WAL` and `busy_timeout=10000`. Grep for `foreign_keys` → 0 hits in the project. | Grep. | Phase 1 (`cleanhome/db.py`, spec §7.1). |
| **SEC-11** | **SQL string-building: none found in application code.** ORM parameterisation is used throughout (`filter_by` / `filter`). The only raw SQL is the two `PRAGMA` statements at `app/__init__.py:89-90`, which take no user input. | Verified by grep for `text(`/`execute(`/`f"…SELECT…"`. | Grep. | No action; keep parameterised queries in the rewrite (spec §7.1). |
| **SEC-12** | **No `sqlite3` error handling or logging.** Errors surface as raw tracebacks; there is no `app.log`. | No `logging` import anywhere in `gui/`. `gui/app.py:168-172` rolls back and re-raises. | Grep for `logging` → 0 hits in `gui/`. | Phase 1/6 (spec §7.6). |
| **SEC-13** | **A `cleaner` role exists in the database and in the code**, but the spec's permission matrix has only three roles (guest, customer, admin). A live user `cleaner_3cc0370c@cleanhome.ph` holds it. | `app/models.py:28` `role = db.Column(db.String(20), …) # customer, admin, cleaner`; `gui/session.py:27-28` `require_admin()` only matches `"admin"`, so a `cleaner` gets no admin access and no customer access either. | DB query. | Phase 2: reduce the role set to `customer`/`admin` per spec §7.1 `CHECK('customer','admin')`. |
| **SEC-14** | **An admin can be deactivated or locked out by the "Customer Accounts" table** — and the spec explicitly says an admin must not be able to deactivate themselves. There is currently no deactivate control at all, but the role model would allow it. | `gui/frames/admin.py:887-917` (no deactivate control today) | Code read. | Phase 5: add deactivate/reactivate with a self-guard (spec §7.5). |

---

## 4. UI/UX flaws

| ID | What | Where | Evidence | Planned fix |
|---|---|---|---|---|
| **UI-01** | **No footer exists anywhere in the Tkinter app.** Public pages end abruptly; the spec requires a `Footer` organism (~120–160px) on every `PageTemplate` page. | Grep for "footer" in `gui/` → 0 hits. `gui/frames/public.py` `Home.build()` ends with a CTA card at `:295-307`. | Grep. | Phase 3 (spec §5.2, §6). |
| **UI-02** | **The "big blank area" known issue is confirmed and its root cause is the grid, not the scrollregion timing.** | See BUG-01. | Runtime probe. | Phase 3. |
| **UI-03** | **"Log In" and "✨ Sign Up Free" are styled differently** — Log In is a grey/white flat button, Sign Up is a solid blue primary button, and both are raw `tk.Button` while the rest of the app uses `ttk`. | `gui/frames/public.py:73-78` (Log In, `bg=theme.SURFACE_ALT`, `fg=theme.TEXT`) vs `:80-85` (Sign Up, `bg=theme.PRIMARY`, `fg="#FFFFFF"`). | Code read — this is the exact known issue from the screenshot. | Phase 3: one `PrimaryButton` / `SecondaryButton` component pair. |
| **UI-04** | **Emoji are used as icons in 86 places** — sidebar icons, stat cards, service badges, payment method icons, the timer icon `⏱`/`⏱️`, and the `✨`/`📊`/`🧹`/`👤` set. They render differently per machine. | `gui/theme.py:203` `icon="📊"`; `gui/frames/public.py:110,137,154-155,164-167,198,212,252,274-277,307,350,485,545-547,594-597`; `gui/frames/customer.py:28,59-64,79,81,120,132,137,154-156,237,549,614,625,662-670,715,719-722,1115,1127`; `gui/frames/admin.py:27,56-60,72,88,90,137,155,165,170,175,180,191-195,315,379,566,682,797`; `gui/frames/auth.py:48,60,63,244` | Grep (86 matches). | Phase 3: text symbols or tiny `Canvas` shapes built once in `components.py` (spec §5.6). |
| **UI-05** | **`Inter` is not installed, so every `("Inter", …)` font silently falls back to Arial** while other widgets use `("Segoe UI", …)` — two different typefaces on the same screen. | `gui/theme.py:55-60, 80-83, 213, 217, 220, 225` use `("Inter", …)`; `gui/frames/*.py` use `("Segoe UI", …)`. `tkinter.font.families()` has no `Inter` and no `Geist`. | Font enumeration. | Phase 3: detect once, pick the first of `Inter`/`Geist`/`Segoe UI`/`Helvetica`, define one type scale (spec §5.1). |
| **UI-06** | **The `₱` sign is rendered with fonts that were never verified to contain U+20B1.** | `gui/frames/public.py:258, 343, 347`; `gui/frames/customer.py:394`; `gui/frames/admin.py:560-561` | `Segoe UI` (available) does contain U+20B1; the Arial fallback for `Inter` is not guaranteed to. | Phase 3: pin the peso-capable font (spec known issue). |
| **UI-07** | **No empty states.** `theme.empty_state()` exists but is **never called**; pages render an empty table instead. The spec's exact copy "No bookings yet — Browse services" does not exist. | `gui/theme.py:259-262` (defined, 0 call sites) | AST scan. | Phase 3/4. |
| **UI-08** | **Feedback uses a top-of-window banner plus raw `messagebox` popups, with no reusable `Toast`.** | `gui/app.py:128-145` `show_flash`; `messagebox.showerror` at `gui/frames/admin.py:504,507,513,860,863,873` and `gui/frames/customer.py:794,797,803` | Grep. | Phase 3: `Toast` component; keep `messagebox` only for destructive confirms (spec §5.7). |
| **UI-09** | **The booking summary is a single `Label` with `|` separators and is missing the service, date/time, and address.** | `gui/frames/customer.py:393-395` `text=f"Subtotal: ₱{subtotal:,.2f}   |   Discount: … |   TOTAL: …"` | Runtime probe output: `Subtotal: ₱1,299.00   |   Discount: ₱129.90  (Code: WELCOME10 applied!)   |   TOTAL: ₱1,169.10`. | Phase 4: a proper summary panel with all six fields (spec §7.2). |
| **UI-10** | **"View Details" and "Book Now" have different styles and different heights** (`Secondary.TButton` `padding=(18,8)` vs default `TButton` `padding=(20,10)`), so the two buttons on every service card are not aligned. | `gui/frames/public.py:365-368` | Code read. | Phase 3/4 (spec §5.7). |
| **UI-11** | **The service list is a single-column stack of full-width cards with no search, no sort, and no max content width** — the content stretches edge-to-edge on a wide monitor. | `gui/frames/public.py:327-368`; `PAD = theme.SPACE_LG` (`:14`) with no `CONTENT_MAX_WIDTH` anywhere | Grep: `CONTENT_MAX_WIDTH` → 0 hits. | Phase 3/4 (spec §5.3, §5.7). |
| **UI-12** | **Design tokens do not match the spec.** Current `theme.py` uses `PRIMARY = "#0070F3"`, `BG = "#FAFAFA"`, `SPACE_XL = 20`, `SPACE_MD = 12`; the spec requires `PRIMARY = "#0A6CF0"`, `BG_PAGE = "#F5F6F8"`, `SPACE_XL = 32`, `SPACE_MD = 16`, and a `CONTENT_MAX_WIDTH` of 1100. None of the spec token names exist. | `gui/theme.py:8-33, 36-44` | Grep for `BG_PAGE`/`PRIMARY_SOFT`/`SUCCESS_SOFT`/`WARNING_SOFT`/`CONTENT_MAX_WIDTH` → 0 hits. | Phase 1: rebuild `theme.py` to the spec's token set. |
| **UI-13** | **Magic hex colours are scattered across the frames** instead of living in `theme.py`. | `gui/frames/public.py:164-166` (`#F0FDFA`, `#FEF3C7`, `#D97706`, `#F0FDF4`, `#EFF6FF`), `:252` (`#E6F9F1`), `:485` (`#E8F4FD`); `gui/frames/customer.py:237`, `:323` (`#F1F5F9`), `:326`, `:715` (`#FFFBEB`); `gui/frames/admin.py:946`; `gui/frames/auth.py:46,60,63,151,174` | Grep. | Phase 1/3 (spec §9). |
| **UI-14** | **The window is smaller than the spec's minimum.** | `gui/app.py:50` `self.minsize(980, 600)` | Code read; spec §5.7 requires 1000×650. | Phase 3. |
| **UI-15** | **Two different button systems are in use** — raw `tk.Button` (header nav, auth pills, "Show" toggles) and `ttk.Button`. | `gui/frames/public.py:44, 66, 73, 80`; `gui/frames/auth.py:60, 63, 87, 151, 174`; rest of the app uses `ttk.Button` | Grep. | Phase 3: `PrimaryButton`/`SecondaryButton`/`DangerButton` components (spec §5.2, §5.5). |
| **UI-16** | **The "Show" password toggle is a 6-character-wide `tk.Button` with `relief="flat"`** — it does not look like a button and has no hover/pressed states. | `gui/frames/auth.py:87-92`, `:151-156`, `:174-179` | Code read. | Phase 3. |
| **UI-17** | **Fake marketing data is hardcoded in the UI** — "15,000+ Homes Cleaned", "4.9 / 5.0 Customer Rating", "Based on 3,400+ reviews", "100% Vetted Staff", "12 Cities Covered", "MONTHLY RATING 4.9★". | `gui/frames/public.py:164-167` | Code read; spec ground rule 6 forbids fake data in the UI. | Phase 3/4: source real counts or drop. |
| **UI-18** | **Company contact details are hardcoded in the Contact page instead of being read from settings/config.** | `gui/frames/public.py:594-597` (`+63 2 8123 4567 / 0917 123 4567`, `Unit 1204, Ayala Tower One, Makati City`) — the same values exist as editable defaults in `AdminSettings` (`gui/frames/admin.py:943-948`) but the public page never reads them. | Code read; spec §7.4 requires a `config.py` placeholder constant. | Phase 1/3. |
| **UI-19** | **Booking notes use a raw `tk.Text` widget** styled by hand (`relief="solid"`, `borderwidth=1`) instead of the themed input component — it does not get the focus ring or the invalid state. | `gui/frames/customer.py:318-319` | Code read. | Phase 3/4. |
| **UI-20** | **Form errors are shown as a window-level banner, never inline under the field.** | `gui/frames/auth.py:107, 188, 191` etc. all use `self.flash(...)`; there is no error-label widget anywhere. | Code read; spec §4.2 requires an inline red error under the field. | Phase 2/3. |
| **UI-21** | **The admin Customers table and the Services table both use `height=14`/`height=16` fixed row counts**, so on a tall window they leave a large empty area, and on a short one they overflow. | `gui/frames/admin.py:556`, `:910` | Code read. | Phase 5. |

---

## 5. Dead code

| ID | What | Where | Evidence | Planned fix |
|---|---|---|---|---|
| **DEAD-01** | **Unused imports.** | `gui/app.py:5` `messagebox`; `gui/frames/admin.py:3` `json`, `:6` `timezone`; `gui/frames/customer.py:3` `json`; `app/models.py:2` `SQLAlchemy`; `app/routes/admin.py:1` `jsonify`; `app/routes/customer.py:4` `CustomerProfile`, `:5` `PromoCodeForm`, `:7` `timedelta`; `app/routes/public.py:1` `request`; `tests/test_auth_permissions.py:4` `CustomerProfile`; `tests/test_availability.py:3` `datetime, timezone`; `tests/test_payment.py:4,7` `datetime, timezone, CustomerProfile, Service` | AST scan. | Phase 6. |
| **DEAD-02** | **Unused theme helpers.** `section_label()`, `field_label()`, `empty_state()` are defined and never called anywhere in the project. | `gui/theme.py:249-262` | AST scan: 0 call sites. | Phase 3 (use `empty_state`) / Phase 6 (delete the rest). |
| **DEAD-03** | **The whole legacy Flask web app is dead relative to the spec.** `app/` contains 4 blueprints, 37 Jinja templates, a 3101-line stylesheet, and WTForms — none of it is in the spec's §8 target structure, and the GUI only borrows `app/` for the SQLAlchemy models and DB session. | `app/` tree; `gui/app.py:7-8` imports only `create_app`, `db`, `User` | Code read. | Phase 1: decide whether to port the models into `cleanhome/db.py` and delete `app/`, or keep it as a separate web product. **Needs your decision.** |
| **DEAD-04** | **Duplicate entry points.** `run.py` and `gui_app.py` both do the same thing. | `run.py`, `gui_app.py` | Both call `gui.app.run()`. | Phase 1: one entry point (`cleanhome/main.py`). |
| **DEAD-05** | **All 37 existing tests exercise the Flask app, not the desktop app.** `tests/test_availability.py` asserts "no double-booking same slot" and "cleaner not double-assigned" — but those are the *web* routes' behaviour, and the web routes and the GUI implement the rules differently. The GUI has no test coverage at all. | `tests/` (5 files) all import `from app import create_app, db` | Test run: `37 passed`. Spec §10 requires `unittest` for the logic layer. | Phase 6: new `cleanhome/tests/` per spec §10. |
| **DEAD-06** | **Duplicated pricing logic in three places** — `gui/frames/customer.py:257`, `:370-371`, `:432-433` all recompute "price = discounted if lower else base". | `gui/frames/customer.py` | Code read. | Phase 4: one `catalog_service` price function. |
| **DEAD-07** | **Duplicated reschedule dialogs** — the customer reschedule dialog (`gui/frames/customer.py:772-818`) and the admin reschedule dialog (`gui/frames/admin.py:482-528`) are near-identical copies. | as listed | Code read. | Phase 5: extract one helper. |
| **DEAD-08** | **The `status` / `payment_status` badge style map is incomplete** — `app/models.py:156` documents `rescheduled` but `gui/theme.py:231-239` has no `rescheduled` badge style, so such a booking falls back to `Badge.Info.TLabel`. | `gui/theme.py:231-245` | Code read; live booking id=3 has that status. | Phase 1/5: normalise statuses (LOG-19). |
| **DEAD-09** | **`seed_data.py` and `seed_demo_data.py` overlap** — both seed services/add-ons/promotions with different values. | `seed_data.py`, `seed_demo_data.py` | Code read. | Phase 1: one seeder in `cleanhome/db.py`. |
| **DEAD-10** | **`app/utils.py`, `app/forms.py`, and the `app/templates/` tree** are used only by the legacy web app. | `app/utils.py`, `app/forms.py`, `app/templates/*` | Code read. | Phase 1 (see DEAD-03). |
| **DEAD-11** | **No `print()` debugging and no bare `except:` were found** — this part of the spec's §9 cleanup checklist is already clean. | Project-wide grep | Grep → 0 hits for `except:`; 0 `print(` in runtime paths. | Keep it that way. |

---

## 6. Inconsistencies

| ID | What | Where | Evidence | Planned fix |
|---|---|---|---|---|
| **INC-01** | **Currency is formatted three different ways**: `₱{price:,.0f}` (no decimals) in the catalog, `₱{subtotal:,.2f}` in the summary, `₱{a.price:,.0f}` for add-ons. | `gui/frames/public.py:258, 343, 347, 420, 423`; `gui/frames/customer.py:258, 359, 394`; `gui/frames/admin.py:560-561` | Code read. | Phase 1: one `format_peso()` → `₱1,299.00` (spec §5.7). |
| **INC-02** | **Two font families are mixed** — `("Inter", …)` (falls back to Arial) and `("Segoe UI", …)`. | `gui/theme.py` vs `gui/frames/*.py` | Font enumeration. | Phase 3 (UI-05). |
| **INC-03** | **Two date formats are in use**: `YYYY-MM-DD` in every form and `Mon - Sun: 7:00 AM - 8:00 PM` for hours. The spec wants `Oct 21, 2026 · 2:00 PM`. | `gui/frames/customer.py:274-283`; `gui/frames/admin.py:491-497` | Code read. | Phase 1: one date helper (spec §5.7). |
| **INC-04** | **Model column names differ from the spec's schema** — `base_price`/`discounted_price` vs `price`; `duration_minutes` vs `duration_mins`; `scheduled_date`+`scheduled_time` vs `scheduled_at`; `subtotal`/`discount_amount`/`total_amount` vs `price_at_booking`/`discount_at_booking`; `password_hash` vs `pw_salt`+`pw_hash`; `is_archived` vs `is_active`. | `app/models.py:86-165` | Code read vs spec §7.1. | Phase 1: adopt the spec schema. |
| **INC-05** | **The promo `discount_type` vocabulary differs from the spec** (`percentage` vs `percent`). | `app/models.py:121`; `gui/frames/customer.py:384, 458` | Code read. | Phase 1 (LOG-20). |
| **INC-06** | **The role vocabulary differs from the spec** — the code has a third `cleaner` role. | `app/models.py:28` | Code read. | Phase 1/2 (SEC-13). |
| **INC-07** | **Button/nav casing is inconsistent** — "Log In" / "Sign Up Free" / "Book Now" / "View Details" / "Create account" / "Forgot password?" / "Confirm & Book Cleaning" / "Mark Completed" / "Start Service". | `gui/frames/public.py:80, 365, 367`; `gui/frames/auth.py:98, 100, 181, 182`; `gui/frames/customer.py:333`; `gui/frames/admin.py:462-466` | Code read. | Phase 3: Title Case for buttons/nav, sentence case for descriptions (spec §5.7). |
| **INC-08** | **Status strings are rendered in inconsistent forms** — `b.status.upper()` in badges, `status.replace('_',' ').title()` in the flash, and raw `pending`/`confirmed` in the model. | `gui/frames/admin.py:250, 373, 402, 479`; `gui/theme.py:231-239` | Code read. | Phase 3/5: one status-label map. |
| **INC-09** | **`AdminSettings` declares 6 fields but the save path and the table do not line up** — `service_areas` is the 6th entry while the button row is placed at `row=len(fields)`; the settings written to the DB are only those in the `fields` dict, so `service_areas` is written but `operating_hours` semantics differ from the public page. | `gui/frames/admin.py:942-974` | Code read. | Phase 5. |
| **INC-10** | **Booking time is stored as `scheduled_time` (a `Time` column) and compared as a time, but the business-hours concept is a plain text setting** — the two can never agree. | `app/models.py:153-154` vs `gui/frames/admin.py:946` | Code read. | Phase 1/4 (LOG-13). |
| **INC-11** | **The `7 services available` count is CORRECT and must not be "fixed".** The query filters `is_active=True, is_archived=False` and returns exactly 7 rows, matching the label. | `gui/frames/public.py:314`, `:324` | DB query: 7 active non-archived services; label renders `7 services available`. | No change. The spec's concern is that it must *stay* equal — see Phase 4 (the `d1ff` service makes it 7, and it is a typo that should be corrected in place, not deleted, so the count stays 7). |

---

## 7. Data integrity findings (live database `instance/app.db`)

| ID | What | Evidence | Planned fix |
|---|---|---|---|
| **DATA-01** | **A service name contains stray characters: `Window Deep Wash d1ff` (id=8, base 899, discounted 799, 90 min, active, not archived).** | DB query. The string appears **nowhere** in `seed_data.py` or `seed_demo_data.py` — it was introduced by a manual/one-off insert, which is why it looks like debug residue. | Phase 1: correct the name in place (keep id=8 so the count stays 7). |
| **DATA-02** | **A corrupted email address is stored**: `reg_user_98736d43@cleanhome.phreg_user_98736d43@cleanhome.ph` — a test-registration artifact from a script that concatenated the email twice. | DB query on `users`. | Phase 1: purge the test row. |
| **DATA-03** | **Test/demo accounts are mixed into the live database**: `test_customer_manual@cleanhome.ph`, `cleaner_3cc0370c@cleanhome.ph` (role `cleaner`), plus the `reg_user_…` row. | DB query. | Phase 1: clean. |
| **DATA-04** | **A booking with `status = 'rescheduled'` exists** — a state that is not in the spec lifecycle and has no badge style. | DB query (booking id=3). | Phase 1/5: normalise to `pending`. |
| **DATA-05** | **Seed bookings are scheduled outside business hours and in the past** — e.g. booking id=7 at **23:33**, and many bookings dated before today (2026-10-21). | DB query. | Phase 1: reseed with valid slots. |
| **DATA-06** | **Service id=1 (`Basic Home Cleaning`) has `is_active = 0` and `is_archived = 1`** — it is invisible in the catalog. The count of 7 therefore excludes it. | DB query. | Intentional or not — needs your confirmation. |
| **DATA-07** | **Promotion `SAVE200` has `is_stackable = True`** while the spec says a promo is applied once and never stacked; `is_stackable` is never read by the code. | DB query + `gui/frames/customer.py`. | Phase 1/4. |
| **DATA-08** | **The database lives at `instance/app.db`**, not `cleanhome.db` as the spec requires. | `app/__init__.py:28`. | Phase 1. |
| **DATA-09** | **The `services` table has no `duration` constraint** — durations in the live data are 60/90/120/180/240 min, all inside the spec's 15–480 range, but nothing enforces it. | DB query + `app/models.py:94`. | Phase 5. |

---

## 8. The six known issues from the screenshot — verification results

| Known issue | Verdict | Detail |
|---|---|---|
| Stray text in a service name (`Window Deep Wash d1ff`) | **Confirmed** | DATA-01. It is in the live DB only, not in any seed script. |
| The `₱` sign may render wrongly on some fonts | **Confirmed as a risk, not yet a visible break** | `Inter` is not installed → those widgets fall back to Arial. `Segoe UI` (the family actually used for most peso labels) does contain U+20B1. The real problem is that the font is never chosen deliberately (UI-05, UI-06). |
| Emoji used as icons (timer icon) render differently per machine | **Confirmed — 86 occurrences** | UI-04. The timer icon `⏱`/`⏱️` is at `gui/frames/public.py:212` and `:350`. |
| Header shows both **Log In** and **Sign Up Free** with different styles | **Confirmed** | UI-03 — `gui/frames/public.py:73-85`. |
| Big blank area at the bottom of the Home page above/below the footer | **Confirmed, and the root cause is not the one the spec guessed** | BUG-01. The spec §6 suspected a stale `scrollregion`; in fact `scrollregion` *is* recomputed on `<Configure>` (`gui/theme.py:321`) — but `canvas.bbox("all")` includes the fixed **2000×5000 background grid** drawn at `gui/theme.py:306-318`. Real content is 1415px, scrollregion is 5002px → ~3.5× too tall. Compounding it, the Tkinter app has **no footer at all** (UI-01), so there is nothing at the end of the page to anchor the scroll. A second, independent instance of the same symptom exists in the legacy web app: `app/static/css/style.css:99` `min-height: calc(100vh - 76px - 240px)` subtracts a 76px navbar (actual: 72px) and a 240px footer (actual: ≈320px), so the main column is forced taller than the viewport and the footer is pushed below the fold instead of sticking to the bottom. |
| Scroll area behavior: scrollbar, mouse wheel, and resize must all work | **Partially broken** | Scrollbar: always visible even when the content fits (BUG-26). Mouse wheel: Windows-only delta math and a fragile `str(w).startswith(str(self))` guard (BUG-25). Resize: works, but `_draw_grid()` re-creates ~291 canvas items on every `<Configure>` (BUG-24) and the grid still inflates the scrollregion (BUG-01). |

---

## 9. Missing features (spec §3, §5, §7) — feature-gap map

| Spec requirement | Present? | Note |
|---|---|---|
| Guest nav `Home · Services · Promotions · About · Contact` | Partly | Correct for guests; admins see the same marketing nav (BUG-18). |
| Customer nav `Home · Services · Promotions · My Bookings · About · Contact` | **No** | The customer uses a sidebar with `Dashboard, Book a Service, My Bookings, Addresses, Notifications, Profile` (`gui/frames/customer.py:59-64`) — there is no customer nav bar with Promotions/About/Contact. |
| Admin nav `Dashboard · Bookings · Services · Promotions · Customers · Reports` | Partly | Sidebar has `Dashboard, Bookings, Services, Cleaners, Promotions, Customers, Settings` — **no Reports** (BUG-13) and an extra **Cleaners** + **Settings**. |
| Profile menu `My Profile · Change Password · Log Out` for both roles | Partly | Customer has Profile + Logout; there is **no Change Password** page for a logged-in user (only the token-based reset flow). |
| Hide controls a role cannot use | **No** | "Book Now" is shown to admins (BUG-02); admin can reach customer frames. |
| Enforce permissions in the logic layer, raise `PermissionError` | **No** | LOG-14. |
| Login: email + password, show/hide toggle, one button, no role selector, Enter submits, focus in Email, generic error, 5-fail lockout | Partly | No role selector exists (good), but no lockout (SEC-03), no focus (BUG-21), message reads "Invalid email or password." (spec wording is "Incorrect email or password."). |
| Sign-up: full name, email, mobile, password, confirm + validation + inline errors + customer-only | Partly | Customer-only ✔ (`auth.py:197`); full validation ✘ (SEC-08); inline errors ✘ (UI-20). |
| First-run "Create Admin Account" screen | **No** | LOG-09. |
| `hashlib.pbkdf2_hmac('sha256', …, 200_000)` + stored salt/hash + `secrets.token_bytes(16)` + `hmac.compare_digest` | **No** | SEC-06. |
| `theme.py` with the exact token set + detected font + type scale | **No** | UI-12, UI-05. |
| `ui/components.py` with atoms/molecules/organisms/templates | **No** | UI-15, UI-01. |
| `PageTemplate` (navbar + scrollable content + footer) | **No** | UI-01. |
| `Toast` feedback component | **No** | UI-08. |
| Service Details modal/page with description, inclusions, price, duration, promo, Book Now | Partly | `ServiceDetail` exists (`gui/frames/public.py:371`) but has no inclusions list and shows Book Now to admins. |
| Empty states | **No** | UI-07. |
| Services page: correct count, search, sort, aligned Book Now / View Details | Partly | Count ✔; search ✘ (BUG-20); sort ✘; alignment ✘ (UI-10). |
| Date/time picker from `ttk.Combobox` | **No** | `gui/frames/customer.py:274-283` uses free-text `ttk.Entry`. |
| Business hours 8 AM–6 PM, last start = closing − duration | **No** | LOG-13. |
| Min 3-hour lead time | **No** | BUG-09. |
| `MAX_CONCURRENT_BOOKINGS = 3`, no overlap | **No** | LOG-01. |
| Address required, prefilled **and editable** in the booking form | Partly | Required ✔; prefilled ✔; **not editable** — read-only Combobox of saved addresses (`gui/frames/customer.py:288-293`). |
| Notes optional, max 300 chars | **No** | BUG-05. |
| Summary before confirming: service, date/time, address, price, discount, total | **No** | UI-09. |
| Price math: one promo, applied once, never negative | Partly | Negative is clamped ✔ (`customer.py:467`); stacking ✘ (LOG-02); service scoping ✘ (LOG-04). |
| Status lifecycle + invalid-jump blocking + badge colours | Partly | Badges exist (`theme.py:231-239`); transitions are not validated (BUG-06). |
| Customer cancel ≥ 24 h before; admin cancel any non-completed **with reason** | **No** | LOG-06, LOG-07. |
| Admin Bookings: filter by status/date, search by customer, view customer phone/address | Partly | Details show phone/address; no filters, no customer search. |
| Admin Services: Add / Edit / **Archive**, validation (unique name, price > 0, duration 15–480) | Partly | Add/Edit ✔; **Archive ✘** (BUG-12); validation ✘. |
| Admin Promotions: Add / Edit / **End**, validation (end ≥ start, percent 1–90, fixed < price) | Partly | Add/Edit ✔; **End ✘** (BUG-14); validation partial. |
| Admin Customers: search, booking count, Deactivate/Reactivate, no self-deactivate | **No** | BUG-11, SEC-14. |
| Admin Reports: date range → bookings, completed, cancelled, revenue, revenue per service, **CSV export** | **No** | BUG-13. |
| Create other admin accounts | **No** | LOG-09. |
| SQLite `cleanhome.db`, `PRAGMA foreign_keys = ON`, parameterised queries, archive-not-delete | Partly | Parameterised ✔ (SEC-11); FK pragma ✘ (SEC-10); file name ✘ (DATA-08). |
| `services/` logic layer that never imports tkinter | **No** | All logic is inside `gui/frames/*.py`, which import tkinter. |
| `unittest` suite for the logic layer | **No** | DEAD-05. |
| `app.log` via `logging` | **No** | SEC-12. |

---

## 10. Known-issue severity ranking (for planning)

| Priority | Issues |
|---|---|
| **P0 — security** | SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, SEC-07, SEC-08 |
| **P0 — data corruption** | DATA-01, DATA-02, DATA-03 |
| **P1 — wrong behaviour** | BUG-02, BUG-03, BUG-04, BUG-05, BUG-06, BUG-09, LOG-01, LOG-02, LOG-06, LOG-11, LOG-14 |
| **P1 — broken visual** | BUG-01, UI-01, UI-03, UI-04, UI-05 |
| **P2 — missing features** | BUG-11, BUG-12, BUG-13, BUG-14, UI-20, and the §9 feature-gap map |
| **P3 — polish / consistency** | DEAD-01, DEAD-02, DEAD-06, DEAD-07, INC-01 … INC-11 |
| **P3 — legacy cleanup** | DEAD-03, DEAD-04, DEAD-05, DEAD-09, DEAD-10 |

---

## 11. Open questions — I need your answers before Phase 1

1. **The legacy Flask app (`app/`, 37 templates, 4 blueprints).** The spec's §8 target structure is a pure-stdlib `cleanhome/` package. Do I:
   - **(a)** port the models/data into `cleanhome/db.py` and **delete** `app/`, `tests/`, `run.py`, `gui_app.py`, `init_db.py`, `seed_data.py`, `seed_demo_data.py`, `create_admin.py`; or
   - **(b)** keep `app/` as a separate product and build `cleanhome/` alongside it?
2. **The `d1ff` service.** Correct the name in place (keeping id=8, so the catalog stays at 7 services), or delete the row (count becomes 6)? §5.7 says the label must equal the real number either way.
3. **Service id=1 `Basic Home Cleaning` is `is_active=0, is_archived=1`.** Intentional, or should it be reactivated (count becomes 8)?
4. **The seeded demo users** (`admin@cleanhome.ph` / `customer@cleanhome.ph` / cleaners). The spec forbids hardcoded credentials — should the seeded accounts be deleted from the live DB, and should the seeding script keep creating them with a **random** password printed once at first run?
5. **The `cleaner` role.** The spec's matrix has only guest/customer/admin. Should the `Cleaners` admin screen and the `cleaner` role be dropped, or kept as a third role with its own permissions?
6. **Reference image `ui_that_i_like.webp` is not in the repository.** Please add it (or confirm that §5's token table + text description is enough to proceed).

---

## 12. Evidence log (how the runtime claims were verified)

All probes were run against a **temporary copy** of the database; `instance/app.db` was not modified by the audit. Scripts live outside the project in `C:\Users\Rick\AppData\Local\Temp\opencode\`.

| # | Probe | Result |
|---|---|---|
| 1 | Exact duplicate slot | 1st → *"Booking created successfully!"*; 2nd → *"The selected date and time slot is already reserved."* |
| 2 | Overlapping (10:00 vs 11:00, 180-min Deep Cleaning) | Both **created**; `bookings that day: [(11,'10:00:00'), (12,'11:00:00')]` |
| 3 | Notes > 300 chars | Created; `stored notes len: 400` |
| 4 | Service discount + promo | `Subtotal: ₱1,299.00 | Discount: ₱129.90 (Code: WELCOME10 applied!) | TOTAL: ₱1,169.10` (promo applied on top of the already-discounted subtotal) |
| 5 | Register with `phone="123"`, weak password | `Registration successful! Please log in.` / `user created? True | phone stored: 123` |
| 6 | Home scroll region | `scrollregion: -2 -2 2002 5002`; `canvas bbox: (-2,-2,2002,5002)`; `inner req h: 1415`; `canvas view h: 692`; `yview` after scrolling to bottom `(0.8617, 1.0)` |
| 7 | Services page search/sort | `Combobox count: 0`, `Entry count: 0` |
| 8 | Admin → "Book Now" | `frames visited: ['Services', 'Login']` |
| 9 | Existing test suite | `37 passed in 5.36s` (all against the Flask app) |
| 10 | AST dead-code scan | 12 unused imports across 11 files; 3 unused `theme.py` helpers; 0 bare `except:`; 0 `print()` in runtime paths |

---

**Phase 0 ends here. No application code has been changed. Awaiting approval to begin Phase 1.**


## 2026-10-22 Updates
- Migrated inclusions column; added to forms and service details.
- UI harness extended and passing.
- Credentials scrubbed; first-run uses Create Admin Account screen.

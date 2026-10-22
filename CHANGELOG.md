# Changelog

All notable changes to CleanHome PH are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] — 22 October 2026: UI cleanup and verification

### Changed

* Every page now draws its spacing, widths, wraps, and table columns from
  `theme.py`; business numbers come from `config.py`. The only remaining
  literal in the UI path is the toast height animation origin.
* `FormMixin` (`clear_form_errors`, `show_form_error`, `show_field_error`)
  lives in `components.py` and is shared by the auth pages and the new
  `FormDialog`. `AddAdminDialog`, `PromoForm`, and `ServiceForm` are now
  `FormDialog` subclasses instead of hand-built dialogs.
* `CancelDialog` and `RescheduleDialog` are `tk.Toplevel` subclasses with a
  consistent body/actions layout; rescheduling calls the shared
  `available_slots(...)` helper.
* `contact.py` opens the support mail client through `webbrowser` and falls
  back to an in-app message; it no longer spawns `os`/`subprocess` calls.
* `home.py` and `promotions.py` wire each `PromoCard` to the Book page through
  `on_book`, so every promotion button navigates.
* `admin_bookings` uses one `_refresh` path (the duplicate `_reload` is
  gone); the dashboard and reports use `DASHBOARD_COLUMNS`,
  `REPORT_COLUMNS`, `UPCOMING_BOOKINGS_LIMIT`, and
  `config.REPORT_WINDOW_DAYS`.
* First-run documentation now matches the app: the **Create Admin Account**
  screen creates the first administrator, customers self-register, and no
  password is seeded, printed, or written to the repository.

### Fixed

* `PageTemplate` crashed with `TclError` because
  `grid_columnconfigure` has no `maxsize` option; content width is now
  centred by a `<Configure>` handler on the scroll canvas.
* **Reschedule** raised `AttributeError` (`booking_service` was not in scope)
  and its confirm button did nothing; both are fixed and covered by the
  harness.
* The UI harness cancelled a booking inside the 24-hour cutoff, so the
  expected refusal masked the rest of the flow; scenarios now book at least
  four days ahead and drive the real dialogs.
* `format_discount()` is shared by the promo cards, promotion list, and
  service details page so the “10% off” wording cannot drift.

### Verification

* `python -m unittest discover -s cleanhome/tests -t .` — 101 tests, OK.
* `python -m cleanhome.tests.ui.harness` — every scenario passes.
* Credential literals were removed from `README.md`, `PHASE1_REPORT.md`, and
  `AUDIT.md`; `cleanhome.db` is explicitly ignored.

## [Unreleased] — Phase 1: restructure and rebuild

The application was rewritten as a single Tkinter/ttk desktop app with a
standard-library-only stack. The old Flask + SQLAlchemy web app and the
first Tkinter prototype were removed after their data was migrated.

### Added

* `cleanhome/` package with `config.py`, `utils.py`, `theme.py`, `db.py`,
  `security.py`, a `services/` logic layer, and a `ui/` layer.
* Database schema, migrations, and seed data for users, services,
  promotions, and bookings; the live file is `cleanhome.db` in the project
  root.
* PBKDF2-HMAC-SHA256 password hashing (200 000 iterations, per-user salt),
  a password policy, random first-run passwords, and a 5-attempt lockout.
* Component library (`ui/components.py`): label, button, input, badge, table,
  card, navigation, footer, and dialog atoms, molecules, and organisms.
* Three page templates (public, admin, auth) and a router with role gates
  (`ui/app.py`).
* All 18 screens: Home, Services, Service details, Promotions, About,
  Contact, Login, Sign-up, Book, My bookings, Profile, Change password, and
  six admin screens (Dashboard, Bookings, Services, Promotions, Customers,
  Reports).
* `ui/pages/service_details.py` — a full view of one service with its
  running promotion.
* `ui/pages/admin_customers.py` — an **Add Admin** dialog for creating
  another administrator.
* Sorting on the Services page (name, price low→high, price high→low,
  duration).
* Date and time pickers that are dropdown lists — the customer never types a
  date by hand (`components.DateCombo`).
* `Enter` submits the sign-in, sign-up, profile, password, and booking
  forms; `Esc` closes every dialog.
* The admin Bookings table now shows the customer's phone number.
* A fixed discount must be smaller than the price of the service it
  applies to.
* An "Add Admin" button on the admin Customers screen.
* `cleanhome/reset_password.py` — a command-line tool that resets a
  locked-out administrator's password, clears the failed-attempt lockout, and
  re-activates the account. It works without a desktop session
  (`python -m cleanhome.reset_password --list`, then
  `--email admin@cleanhome.ph`, with `--generate` for a random password).
* `cleanhome/tests/` — 101 unit tests covering hashing, lockout, sign-up
  validation, the booking rules, price and promotion maths, the status
  flow, permissions, the archive rule, the shared formatting helpers, and
  the command-line password reset.
* `cleanhome/tests/ui/harness.py` — a manual harness that opens a real
  window and walks every screen and every button: sign-up, sign-in,
  profile, password change, booking, cancelling, rescheduling, the admin
  status flow, the filters, and the three admin dialogs.
  Run it with `python -m cleanhome.tests.ui.harness`.
* `REMAINING_WORK.md` — the section-by-section audit of what the spec still
  asks for, with the measurements taken from the reference image
  `ui that i like.webp`.
* `README.md` (how to run, first-run accounts, folder map, known
  limitations), `AGENTS.md` (rules for future work), and `AUDIT.md`
  (the Phase 0 audit, 112 findings), plus `PHASE1_REPORT.md`.

### Changed

* The service catalogue was rebuilt: service id 8 was renamed to
  **Window Deep Wash** and service id 1 (**Basic Home Cleaning**) was left
  archived and inactive. Seven services are active.
* The `cleaner` role and the Cleaners screen were dropped; cleaner and
  test accounts were removed from the database.
* Promotions have no code any more — they match a service and a date range.
  Exactly one promotion applies to a booking (the best one); promotions
  never stack.
* The admin navigation bar gained **My Profile** and **Change Password**;
  the page registry now takes a set of roles instead of a single role.
* Database errors are turned into a readable message and written to
  `app.log` with the full traceback.
* Every screen was rebuilt on the component library: no page creates a
  one-off styled widget any more.
* First-run accounts print their random passwords to the console once
  instead of using a "Create Admin Account" screen.
* The promotion form and the report screen now use date and time pickers
  (`components.DateCombo` and `components.Dropdown`) instead of typed
  `YYYY-MM-DD HH:MM` text.
* The dialogs receive the signed-in administrator as an argument instead of
  walking up the widget tree with `master.master.master`.
* Colours, sizes, and spacing live only in `theme.py`; the white used by
  the toast and the navigation bar height are theme tokens now.

### Fixed

| Bug | Where | Fix |
|-----|-------|-----|
| `report_service.dashboard_stats` used `b.` aliases with no `FROM bookings b`, so every dashboard query failed with "no such column: b.price_at_booking" | `cleanhome/services/report_service.py` | Added the missing `FROM` clause |
| The best promotion was picked by comparing discounts against a fake price of 1 000 000, so a 10 % promo always beat a larger fixed discount | `cleanhome/services/catalog_service.py` | The comparison now uses the real service price |
| A guest could open the **Book** page because the registry entry had no role | `cleanhome/ui/pages/__init__.py` | The page is now registered for the `customer` role |
| `tk.Label(..., style="Caption.TLabel")` raised a TclError — plain `tk.Label` does not take a `style` | `cleanhome/ui/pages/my_bookings.py` | Switched to the `CaptionLabel` component |
| The admin Bookings screen raised `NameError: name 'body' is not defined` and duplicated its action buttons on every refresh | `cleanhome/ui/pages/admin_bookings.py` | The screen was rewritten around a persistent table and a `_reload()` method |
| The `ChangePassword` page was missing as its own module (the class was inside `profile.py`) | `cleanhome/ui/pages/change_password.py` | The page was given its own file, as the spec requires |
| `cleanhome/__init__.py` and `cleanhome/ui/__init__.py` were missing, so the package could not be imported | `cleanhome/` | Both were created |
| `from cleanhome.ui import components, templates` had been dropped from three pages, breaking them at import time | `admin_promotions.py`, `admin_reports.py`, `my_bookings.py` | The import was restored |
| `Signup._register` shadowed `tkinter.Misc._register`, so pressing Enter crashed the sign-up page | `cleanhome/ui/pages/signup.py` | The method was renamed to `_create_account` |
| `FormField.focus` shadowed `tkinter.Misc.focus` | `cleanhome/ui/components.py` | Renamed to `focus_field` |
| `users.email` was case-sensitive, so `Juan@Example.com` and `juan@example.com` could both register | `cleanhome/db.py` | The column is now `COLLATE NOCASE UNIQUE` |
| A promotion was matched against `datetime('now')` instead of the date being booked, so a promotion could not be quoted for a future date | `cleanhome/services/catalog_service.py` | The caller now passes the date in |
| A wrong price was silently turned into `0` instead of an error | `cleanhome/services/catalog_service.py` | `utils.parse_decimal` now raises, and the field error is shown |
| The footer left a large blank strip at the bottom of short pages | `cleanhome/ui/components.py` | The footer was compacted from 251 px to 153 px and the scroll region now matches the content exactly |
| The long "Data (users, services, bookings, promotions)" table on the home page overflowed the window | `cleanhome/ui/pages/home.py` | Replaced with summary cards |
| Several background processes kept the old `instance/app.db` open after the rewrite | project root | The legacy processes were stopped and `instance/` was removed |
| `PromoForm._save` reached the app with `self.master.master.master`, so saving a promotion crashed with `AttributeError: 'NoneType' object has no attribute 'master'` | `cleanhome/ui/pages/admin_promotions.py` | The administrator is passed into the dialog and the app is reached through `self.master.app` |
| `ServiceForm._save` used the same fragile `master.master.master` chain | `cleanhome/ui/pages/admin_services.py` | The administrator is passed into the dialog |
| The report date pickers could not reach today — the list ended yesterday, so a report of the current day was impossible | `cleanhome/ui/pages/admin_reports.py` | The list now runs from 30 days ago to today, and today is the default end |
| The admin promo form asked for a date and time as typed text, which the spec forbids | `cleanhome/ui/pages/admin_promotions.py` | Date and time dropdowns; the start defaults to today and the end to a month out |
| A white colour (`#FFFFFF`) was hard-coded in the toast instead of a theme token | `cleanhome/ui/components.py` | `theme.TEXT_ON_ACCENT` |
| **Pressing "Confirm Booking" always crashed** — `Book._submit` called `self._clear_error()` and `self._show_error()`, and neither method existed | `cleanhome/ui/pages/book.py` | Both methods were written; the whole customer booking flow was walked through the real widgets afterwards |
| `PasswordInput` had no `set` method, so `FormField.set` crashed on every password field | `cleanhome/ui/components.py` | `PasswordInput.set` and `PasswordInput.get` were added |
| The **My Bookings** item in the navigation bar was never highlighted — the page name was `MyBookings` but the label is `My Bookings` | `cleanhome/ui/pages/my_bookings.py` | The page name now matches the label |
| The **Change Password** page was called "Profile", so the navigation bar highlighted the wrong item | `cleanhome/ui/pages/change_password.py` | The page name is now "Change Password" |
| A SQL syntax error was reported to the user as "The database is busy right now" | `cleanhome/db.py` | The message now depends on the actual SQLite error |

### Removed

* The Flask web app (`app/`), the legacy scripts (`run.py`, `gui_app.py`,
  `init_db.py`, `seed_data.py`, `seed_demo_data.py`, `create_admin.py`), the
  old pytest suite (`tests/`), the first Tkinter prototype (`gui/`),
  `requirements.txt`, `.env.example`, and the legacy `.env` (it held a
  Flask secret key and PayMongo placeholders that nothing uses now).
* `requirements.txt` — the app now needs no third-party packages at all.
* The `cleaner` role, the Cleaners screen, add-ons, reviews, payments, and
  the separate addresses table (the address lives on `users`).

### Known gaps

* No email or SMS notifications; confirmations are shown in the app only.
* No online payment; prices are quoted and recorded, not charged.
* A locked-out administrator must be re-activated by another administrator.
* The reference screenshot (`ui_that_i_like.webp`) was never available, so
  the visual match to the reference design is approximate.
* The admin tables have no pagination; a few hundred bookings will make
  them slow to scroll.
* There is no bulk cancel and no per-booking team assignment.

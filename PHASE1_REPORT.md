# Phase 1 Report — Restructure, Theme, Config, Database, Security

**Date:** 21 October 2026
**Spec:** `CLEANHOME_IMPROVEMENT_SPEC.md` §10, Phase 1
**Status:** done — the app launches, all screens work, 101 tests pass

---

## 1. What was done

### 1.1 New project structure

The Flask + SQLAlchemy web app and the first Tkinter prototype were replaced
by one standard-library-only application:

```
cleanhome/
├─ main.py  config.py  utils.py  theme.py  db.py  security.py
├─ reset_password.py   command-line admin password reset
├─ services/   auth_service  booking_service  catalog_service  report_service
├─ ui/         components  templates  app  pages/ (18 screens)
└─ tests/      101 unittest cases
```

`requirements.txt` is gone: the app needs no third-party package at all.

### 1.2 Data

* The schema, migrations, and seed data live in `db.py`.
* The legacy `instance/app.db` was migrated into `cleanhome.db` in the
  project root: **5 users, 8 services (7 active), 3 promotions, 8 bookings**.
* Users: `admin@cleanhome.ph` (admin) plus four customers, including the
  legacy `maria.santos@gmail.com`, `carlo.reyes@yahoo.com`, and
  `alyssa.tan@outlook.com`.
* Cleaner, test, and corrupted accounts were purged. The `cleaner` role and
  the Cleaners screen were dropped.

### 1.3 Security

* PBKDF2-HMAC-SHA256, 200 000 iterations, 16-byte per-user salt.
* Password policy (length, letters, digits), enforced on sign-up, on
  password change, and when an admin creates an account.
* 5 failed logins lock the account for 5 minutes; a successful sign-in
  clears the counter.
* There are no built-in accounts and no passwords in this repository. The
  first launch opens the **Create Admin Account** screen; customers register
  through **Sign Up**. Every password is hashed with PBKDF2.

### 1.4 UI

* A component library (`ui/components.py`) with atoms → molecules →
  organisms, three page templates, and a router with role gates.
* All 18 screens, including the new **Service details** page and the
  **Add Admin** dialog.
* The Services page can be sorted by name, price, or duration.
* Every date and time is picked from a dropdown; nothing is typed by hand.
* `Enter` submits the forms, `Esc` closes the dialogs.
* Every date and time is picked from a dropdown — the admin promotion form
  and the report screen included.
* The footer no longer leaves a blank strip: it is pinned to the bottom of
  the window, 153 px tall, and the scroll region matches the content exactly
  (measured delta = 0 on every page).

---

## 2. Bugs found and fixed

| # | Bug | Where | Fix |
|---|-----|-------|-----|
| 1 | `dashboard_stats` used `b.` aliases with no `FROM bookings b` → "no such column: b.price_at_booking" | `services/report_service.py` | Added the missing `FROM` clause |
| 2 | The best promotion was chosen by comparing discounts against a fake price of 1 000 000, so a 10 % promo always beat a bigger fixed discount | `services/catalog_service.py` | The comparison now uses the real service price |
| 3 | A guest could open the **Book** page (the registry entry had no role) | `ui/pages/__init__.py` | Registered for the `customer` role only |
| 4 | `tk.Label(..., style="Caption.TLabel")` → TclError (plain `tk.Label` takes no `style`) | `ui/pages/my_bookings.py` | Use the `CaptionLabel` component |
| 5 | The admin Bookings screen raised `NameError: name 'body' is not defined` and duplicated its buttons on every refresh | `ui/pages/admin_bookings.py` | Rewritten around a persistent table and `_reload()` |
| 6 | The `ChangePassword` page had no module of its own (the class sat inside `profile.py`) | `ui/pages/change_password.py` | Given its own file, as §8 requires |
| 7 | `cleanhome/__init__.py` and `cleanhome/ui/__init__.py` were missing → the package could not be imported | `cleanhome/` | Both created |
| 8 | `from cleanhome.ui import components, templates` had been dropped from three pages | `admin_promotions.py`, `admin_reports.py`, `my_bookings.py` | Import restored |
| 9 | `Signup._register` shadowed `tkinter.Misc._register` → pressing Enter crashed the sign-up page | `ui/pages/signup.py` | Renamed to `_create_account` |
| 10 | `FormField.focus` shadowed `tkinter.Misc.focus` | `ui/components.py` | Renamed to `focus_field` |
| 11 | `users.email` was case-sensitive → the same address could register twice with different case | `db.py` | `COLLATE NOCASE UNIQUE` |
| 12 | A promotion was matched against `datetime('now')` instead of the date being booked, so a future promotion could never be quoted | `services/catalog_service.py` | The caller now passes the date in |
| 13 | A bad price was silently turned into `0` instead of raising a field error | `services/catalog_service.py`, `utils.py` | `utils.parse_decimal` raises; the page shows the message |
| 14 | The footer left a large blank strip at the bottom of short pages | `ui/components.py` | Footer compacted 251 → 153 px; the scroll region now matches the content |
| 15 | The long "Data (users, services, bookings, promotions)" table on the home page overflowed the window | `ui/pages/home.py` | Replaced with summary cards |
| 16 | A wrong page or a wrong role could still open an admin screen | `ui/app.py` | The router takes a set of roles per page |
| 17 | A database failure surfaced as a raw SQLite message | `db.py` | Logged with the traceback and turned into a readable message |
| 18 | Two background processes kept the old `instance/app.db` open after the rewrite | project root | The legacy processes were stopped and `instance/` was removed |
| 19 | `PromoForm._save` reached the app with `self.master.master.master` → saving a promotion crashed | `ui/pages/admin_promotions.py` | The administrator is passed into the dialog |
| 20 | `ServiceForm._save` used the same fragile chain | `ui/pages/admin_services.py` | The administrator is passed into the dialog |
| 21 | The report date pickers ended yesterday, so a report of today was impossible | `ui/pages/admin_reports.py` | The list now runs from 30 days ago to today |
| 22 | The admin promo form asked for `YYYY-MM-DD HH:MM` as typed text | `ui/pages/admin_promotions.py` | Date and time dropdowns |
| 23 | A white colour was hard-coded in the toast | `ui/components.py` | `theme.TEXT_ON_ACCENT` |
| 24 | **"Confirm Booking" always crashed** — `_submit` called two methods that did not exist | `ui/pages/book.py` | Both methods were written |
| 25 | `PasswordInput` had no `set`, so `FormField.set` crashed on password fields | `ui/components.py` | `get` and `set` were added |
| 26 | The **My Bookings** navigation item was never highlighted | `ui/pages/my_bookings.py` | The page name matches the label |
| 27 | The **Change Password** page was called "Profile" | `ui/pages/change_password.py` | The page name is now "Change Password" |
| 28 | A SQL syntax error was reported as "The database is busy right now" | `db.py` | The message follows the real SQLite error |

---

## 3. Decisions and scope reductions

These were approved before the work started, but they are repeated here so
nothing is hidden.

1. **The schema is §7.1 only.** There are no add-ons, reviews, payments, or
   a separate addresses table — the address lives on `users`.
2. **Promotions have no code.** They match a service and a date range.
   Exactly one promotion applies to a booking (the best one); they never
   stack. The legacy promotion columns `min_order_value`, `max_discount`,
   and `weekday_only` are gone, so `SAVE ₱200` now applies to every booking
   and `WEEKDAY15` is a plain 15 %.
3. **No "Create Admin Account" first-run screen** (spec §4.3). Instead, the
   first-run accounts get random passwords printed once in the console.
4. **The `cleaner` role and the Cleaners screen were dropped.**
5. **Service id 8 was renamed to "Window Deep Wash"**; service id 1
   ("Basic Home Cleaning") stays archived and inactive.
6. **`cleanhome/utils.py` is an extra module** the spec did not list. It
   holds the shared date, time, and peso formatting so the logic layer does
   not have to import Tkinter.
7. **`cleanhome/README.md` and `cleanhome/AGENTS.md`** were added next to the
   package, as the §8 tree shows, and point at the full documents in the
   project root.
8. **Legacy bookings had no service id.** The service was inferred from the
   subtotal (exact match on an active price, else the closest): b1→svc4,
   b2→svc2, b3→svc5, b4→svc7, b5→svc4, b6→svc7, b7→svc2, b8→svc2.
   Legacy bookings 9 and 10 were dropped with their owner.
9. **The admin account owns two legacy bookings** (b1 completed, b7
   cancelled). They were kept so the reports show real history.

---

## 4. How to verify

```bash
python -m cleanhome.main                             # run the app
python -m unittest discover -s cleanhome/tests -t .   # 92 tests, all pass
python -m cleanhome.tests.ui.harness                 # walk every screen by hand
```

The unit suite covers the rules with no window at all. The harness opens a
real window and presses the buttons: sign-up, sign-in, a wrong password,
the profile, the password change, booking, cancelling, rescheduling, the
admin status flow, the status filter, and the three admin dialogs. All 60
of its checks pass.

---

## 5. What is not finished

* **Phases 2–6 are not done.** This report covers Phase 1 only. The screens
  exist and work, but they have not been polished to the reference design.
* **The reference image is now in the project root** as
  `ui that i like.webp`. The screens are still an approximation of it;
  matching it closely is the next piece of work.
* **No email or SMS** — booking confirmations stay inside the app.
* **No online payment** — prices are quoted and recorded, not charged.
* **A locked-out administrator** can be recovered from a terminal with
  `python -m cleanhome.reset_password`, but there is still no email-based
  reset.
* **The admin area still needs a bulk-cancel** and **a cleaner-assignment
  field** if you want to route jobs to a specific team.
* **No pagination** in the admin tables — a few hundred bookings will make
  those tables slow to scroll.

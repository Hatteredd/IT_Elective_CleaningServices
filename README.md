# CleanHome PH — Home Cleaning Service Desktop Application

A desktop application for managing a home-cleaning business in the Philippines:
customers browse the catalogue and book a cleaning, and administrators manage
services, promotions, bookings, customers, and revenue.

The app is written in **Python 3.11+** with **Tkinter/ttk** and uses only the
**Python standard library** — no Flask, no SQLAlchemy, no third-party packages.

---

## Running the app

```bash
python -m cleanhome.main
```

or, from the project root:

```bash
python cleanhome/main.py
```

There is nothing to install. If `tkinter` is missing, re-run the Python
installer and tick **"tcl/tk and IDLE"**.

### First run

The first time the app starts it creates the database file `cleanhome.db` in
the project root and seeds the service catalogue and the starter promotions.

There are no built-in accounts and no default passwords. The app opens on the
**Create Admin Account** screen so the owner can create the first
administrator. After that, customers create their own accounts from the
**Sign Up** page, and an administrator can add more administrators from
**Customers → Add Admin**.

Every password is hashed with PBKDF2 before it is written to the database; the
app never stores or logs a plain-text password. If the only administrator is
locked out, use the reset tool described below.

### Locked out? Reset the admin password

If the only administrator is locked out, reset the password from a terminal —
no desktop session and no second administrator needed:

```bash
python -m cleanhome.reset_password --list                      # show the admin accounts
python -m cleanhome.reset_password --email admin@cleanhome.ph  # type a new password
python -m cleanhome.reset_password --email admin@cleanhome.ph --generate
```

The tool sets the new password, clears the five-failed-attempts lockout, and
re-activates the account. It refuses a password that breaks the policy
(8 characters, at least one letter and one number), and it never prints a
password you typed yourself.

---

## What is still to do

[`REMAINING_WORK.md`](REMAINING_WORK.md) lists every spec item that is not
finished yet — the audit was done against `CLEANHOME_IMPROVEMENT_SPEC.md`
section by section, and anything that was already built and tested is not
repeated there.

---

## Folder map

```
cleanhome/
├─ main.py                  # entry point: logging, database setup, first-run check
├─ config.py                # business rules, company details, paths
├─ utils.py                 # formatting helpers (peso, dates, times)
├─ theme.py                 # design tokens, fonts, ttk styles, ScrollableFrame
├─ db.py                    # connection, schema, migrations, seed data
├─ security.py              # PBKDF2 hashing, password policy, random passwords
├─ reset_password.py        # command-line admin password reset
├─ services/                # logic layer — never imports tkinter
│   ├─ auth_service.py      # register, login, lockout, profile, customers
│   ├─ booking_service.py   # scheduling, capacity, pricing, booking lifecycle
│   ├─ catalog_service.py   # services and promotions
│   └─ report_service.py    # dashboard figures, revenue report, CSV export
├─ ui/
│   ├─ components.py        # atoms → molecules → organisms (the whole UI kit)
│   ├─ templates.py         # page shells: public, admin, auth
│   ├─ app.py               # window, session, router, role gates
│   └─ pages/               # one page class per file
│       ├─ home.py  services.py  service_details.py  promotions.py
│       ├─ about.py  contact.py  login.py  signup.py
│       ├─ book.py  my_bookings.py  profile.py  change_password.py
│       └─ admin_dashboard.py  admin_bookings.py  admin_services.py
│           admin_promotions.py  admin_customers.py  admin_reports.py
├─ tests/                   # unittest suite for the logic layer
│   └─ ui/harness.py        # manual checks that open a real window
├─ AGENTS.md                # the rules for working on this package
└─ README.md                # a map of the package
```

Rules the code follows:

* the logic layer never imports Tkinter, so it can be unit-tested without a screen;
* the UI calls the services, the services call the database;
* every page class is in its own file and only receives `app` and `session`;
* one `Session` object holds the signed-in user and is cleared on logout.

---

## Business rules

All of these live in `cleanhome/config.py`:

| Rule | Value |
|------|-------|
| Cleaning hours | 8:00 AM – 6:00 PM, every day |
| Start-time step | 30 minutes |
| Team capacity | 3 concurrent cleanings |
| Minimum notice | 3 hours before the start time |
| Cancellation cutoff | 24 hours before the start time |
| Booking window | 30 days ahead |
| Service duration | 15 – 480 minutes |
| Notes | 300 characters maximum |
| Percentage discount | 1 – 90 % |
| Failed logins | 5, then locked for 5 minutes |
| Password hashing | PBKDF2-HMAC-SHA256, 200 000 iterations, 16-byte salt |

---

## Running the tests

```bash
python -m unittest discover -s cleanhome/tests -t .
```

The suite covers password hashing, the lockout, sign-up validation, the
booking rules (past date, business hours, capacity, price and promotion
maths), the booking status flow, the permission checks, the
archive-instead-of-delete rule, the shared formatting helpers, and the
command-line password reset. Each test
runs against its own throw-away database file, so your real `cleanhome.db`
is never touched.

There is a second, manual harness for the interface. It opens a real
window and presses the buttons: first-run setup, every screen for each role,
the components, sign-up, sign-in, booking, rescheduling, cancelling, the admin
status flow, the admin forms, reports, and logout:

```bash
python -m cleanhome.tests.ui.harness
```

---

## Where the data lives

| File | What it is |
|------|------------|
| `cleanhome.db` | the live SQLite database |
| `app.log` | the application log |
| `backup_original/` | a copy of the original project taken before the rewrite |

Delete `cleanhome.db` to start over from a fresh database.

---

## Known limitations

* **Tkinter is a desktop toolkit.** There is no web version, no multi-user
  server, and no live sync between two computers.
* **The date and time pickers are dropdown lists.** They are limited to the
  booking window (30 days ahead) and to the 30-day report range.
* **No email or SMS.** Booking confirmations and cancellation notices are
  only shown inside the app; there is no mail server integration.
* **No online payment.** Prices are quoted and recorded, but money is
  collected outside the app.
* **One admin password reset.** A locked-out administrator has to be
  re-activated from another administrator; there is no email-based reset.
  There is a command-line tool for the case where the locked-out account is
  the only administrator: `python -m cleanhome.reset_password`.
* **The text is English only**, and the interface is not translated.
* **The admin tables have no pagination.** A few hundred bookings will make
  them slow to scroll.
* **There is no bulk cancel** and no per-booking team assignment.
* **The screens are an approximation of the reference design.** The reference
  image `ui that i like.webp` is in the project root, and matching it more
  closely is the next piece of work.

# CleanHome PH

A desktop booking system for a home-cleaning business. It is built with
Python's standard library and Tkinter only — no web server, no database
server, and no third-party runtime packages.

## What it does

* Guests can browse services, promotions, the about page, and contact details.
* Customers can register, sign in, book a cleaning, reschedule or cancel it
  (at least 24 hours ahead), and edit their profile and password.
* Administrators can confirm, start, and complete bookings, manage the
  service catalogue and promotions, manage customer accounts, print revenue
  reports, and copy the database.

## Requirements

* Python 3.11 or newer for running from source.
* Windows for the packaged build. The source also runs on Linux and macOS
  wherever Tkinter is installed.
* PyInstaller is needed only to build the executables. It is not a runtime
  dependency.

## Run from source

```
python -m cleanhome.main
```

or

```
python main.py
```

## First run

1. Start the app.
2. The **Create Admin Account** screen appears because no administrator
   exists yet. Choose a strong password (at least 8 characters, with letters
   and a number).
3. Sign in as that administrator and add services or promotions if needed.
4. Customers create their own accounts from the **Sign up** link.

No passwords are seeded, printed, or stored in the repository. Passwords use
PBKDF2-HMAC-SHA256 with a per-user salt. Five failed sign-ins lock the account
for five minutes.

## Where the data lives

| How the app runs | Database | Log | Backups |
|---|---|---|---|
| From source | `cleanhome.db` in the project folder | `app.log` in the project folder | `backups/` in the project folder |
| Installed `.exe` | `%LOCALAPPDATA%\CleanHomePH\cleanhome.db` | `%LOCALAPPDATA%\CleanHomePH\app.log` | `%LOCALAPPDATA%\CleanHomePH\backups\` |

The packaged app never writes next to the executable, so it works when
installed under `Program Files` or on a read-only drive.

## Backups

Run `CleanHomeTools.exe backup`, or from source `python -m cleanhome.backup`.
A copy is written to the backup folder, named
`cleanhome-YYYYMMDD-HHMMSS.db`.

```
python -m cleanhome.backup
python -m cleanhome.backup --output D:\CleanHomeBackups
```

To restore a backup, close the app, replace `cleanhome.db` with the backup
file (keep a copy of the current file first), then start the app again.

## Password reset and lockout recovery

A locked-out administrator can wait five minutes, or another administrator
can reset the password from **Admin → Customers**. If nobody can sign in,
use the console tool while the app is closed:

```
python -m cleanhome.reset_password --list
python -m cleanhome.reset_password --email admin@example.com
python -m cleanhome.reset_password --email admin@example.com --generate
```

The reset clears the failed-attempt counter and reactivates the account. A
generated password is shown once and must be changed at the next sign-in.

## Customising company details

Open `cleanhome/config.py` and edit the **Company details** block near the
top. Every value marked `REPLACE BEFORE RELEASE` is a placeholder:

* company name, tagline, region
* support email, phone, address
* business hours and service areas
* cancellation window and maximum concurrent bookings
* currency symbol

The Home, About, Contact, navigation, and footer screens read these values,
so the text only needs to change in one place. Colours, spacing, and fonts
live in `cleanhome/theme.py`.

## Tests

```
python -m unittest discover -s cleanhome/tests -t .
python -m cleanhome.tests.ui.harness
```

The first command runs the logic tests. The second opens a real window and
walks every screen, dialog, booking flow, admin flow, report,
and 100/125/150% scaling; it needs a desktop session.

## Build the Windows executables

Install PyInstaller once on the build machine:

```
python -m pip install pyinstaller
```

Then run:

```
build_exe.bat
```

The build produces:

* `dist\CleanHomePH.exe` — the windowed application.
* `dist\CleanHomeTools.exe` — a console tool with `backup` and
  `reset-password` commands.

`CleanHomeTools.exe` is required because the windowed app has no console for
the reset prompt or the backup confirmation.

```
CleanHomeTools.exe backup
CleanHomeTools.exe reset-password --list
CleanHomeTools.exe reset-password --email admin@example.com --generate
```

## Release folder

Create a `release` folder containing:

```
CleanHomePH.exe
CleanHomeTools.exe
README.txt            (this file, or a short version of it)
```

Do not include `cleanhome.db`, `app.log`, `backups/`, `backup_original/`,
or development files in the release. The app creates its data folder on
first launch.

## Project layout

```
main.py                     launcher
cleanhome/
  config.py                 business rules, paths, company details
  theme.py                  colours, spacing, fonts
  db.py                     SQLite connection, schema, migrations, backup
  security.py               password hashing and policy
  utils.py                  formatting and date helpers
  services/                 business logic (no Tkinter)
  ui/                       Tkinter widgets, pages, router
  tests/                    unit tests and the manual UI harness
  backup.py                 console backup command
  reset_password.py         console password-reset command
  tools.py                  console dispatcher used by CleanHomeTools.exe
```

## Known limitations

* No email or SMS notifications; confirmations appear in the app only.
* No online payment; prices are quoted and recorded, not charged.
* Reports cover the last 30 days by default; there is no custom date typing
  because the pickers are dropdowns.
* The admin tables are not paginated, so very large booking histories scroll
  slowly.
* There is no per-booking cleaner assignment or bulk cancellation.

# AGENTS.md — rules for opencode working on CleanHome

## What this project is

A Tkinter desktop application for a home-cleaning business. The rules below
come from `CLEANHOME_IMPROVEMENT_SPEC.md` and apply to every change.

## Hard rules

1. **Python 3.11+ and the standard library only.** No Flask, SQLAlchemy,
   Werkzeug, CustomTkinter, Pillow, ttkbootstrap, or any other runtime
   dependency. Do not add a `requirements.txt` with third-party packages.
2. **The logic layer must never import tkinter.** `cleanhome/services/*.py`
   works with plain dictionaries; `cleanhome/ui/*` may import tkinter.
3. **The UI calls the services; the services call the database.** Pages never
   write SQL, and services never touch widgets.
4. **Every statement uses parameter placeholders.** Never build SQL by
   concatenating strings.
5. **No magic numbers or colours outside `theme.py` and `config.py`.**
   Business rules live in `config.py`; colours, spacing, and fonts live in
   `theme.py`.
6. **No bare `except:` and no `except Exception:`** unless the handler logs
   the traceback and turns it into a user-readable message.
7. **Pages assemble components, they do not invent widgets.** Use
   `cleanhome/ui/components.py` (atoms → molecules → organisms). A page may
   only create plain `tk.Frame` containers to lay components out.
8. **No placeholder text, no fake data, no commented-out code, no debug
   `print()` in the app path.**
9. **No hardcoded credentials.** Passwords are hashed with PBKDF2 and the
   first-run passwords are random and printed once.
10. **Every button does something.** No dead buttons.
11. **Logout clears the session completely** and rebuilds the navigation bar.
    The database connection is closed when the window closes.

## Adding a page

1. Create `cleanhome/ui/pages/<name>.py` with one page class that extends
   `templates.PageTemplate`, `templates.AdminTemplate`, or
   `templates.AuthTemplate`.
2. Register it in `cleanhome/ui/pages/__init__.py` under `PAGES` with the
   roles that may open it (`()` for a public page, `("customer",)`,
   `("admin",)`, or both).
3. The router in `cleanhome/ui/app.py` handles authentication and role
   checks — the page does not need to re-check them.

## Before you finish

* Run the app: `python -m cleanhome.main`.
* Run the tests: `python -m unittest discover -s cleanhome/tests -t .`.
* Update `CHANGELOG.md` with what changed and every bug fixed.
* Report anything you could not finish, and never hide a scope reduction.

# AGENTS.md — rules for working inside the `cleanhome` package

The project-wide rules are in [`../AGENTS.md`](../AGENTS.md). The ones below
are the ones that only apply to the code in this folder.

## The layers

```
cleanhome/
├─ config.py  utils.py  theme.py  db.py  security.py   plain Python
├─ services/  the rules — plain dictionaries, no tkinter
├─ ui/        widgets — may import tkinter
└─ tests/     unit tests, plus a manual UI harness
```

1. **`services/` must never import tkinter.** If a service needs to show
   something, it raises `ServiceError` and the page turns it into a message.
2. **`ui/pages/` must never write SQL.** It calls a service and shows what
   comes back.
3. **`db.py` is the only place that talks to SQLite.** Every statement uses
   `?` placeholders. The only exceptions are the migration statements, and
   their identifiers are checked against `IDENTIFIER` first.
4. **`config.py` holds the business rules** (hours, capacity, window sizes,
   company details) and **`theme.py` holds the look** (colours, spacing,
   fonts). A number that decides *how the business works* does not belong in
   a page.
5. **One page class per file** in `ui/pages/`, and it is registered in
   `ui/pages/__init__.py` with the roles that may open it.
6. **Pages assemble components.** They may create plain `tk.Frame` containers
   to lay components out, but a styled widget belongs in `ui/components.py`.

## Before you finish

```bash
python -m unittest discover -s cleanhome/tests -t .   # the rules
python -m cleanhome.tests.ui.harness                   # the screens
```

The second one opens a real window, so it needs a desktop. It is the only
way to catch the kind of bug where a page calls a method that does not
exist — the unit tests never touch the widgets.

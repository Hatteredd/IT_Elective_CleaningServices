# cleanhome — the CleanHome application package

This folder holds the whole application. The full documentation — how to run
it, the folder map, the business rules, and the known limitations — is in
[`../README.md`](../README.md).

| File | What it is |
|------|------------|
| `main.py` | the entry point: logging, database setup, first-run accounts |
| `config.py` | business rules, company details, file paths |
| `utils.py` | formatting helpers for pesos, dates, and times |
| `theme.py` | design tokens, fonts, ttk styles |
| `db.py` | the connection, the schema, the migrations, and the seed data |
| `security.py` | PBKDF2 hashing, the password policy, random passwords |
| `reset_password.py` | the command-line tool that resets a locked-out admin password |
| `services/` | the logic layer — it never imports tkinter |
| `ui/` | the interface: components, templates, the router, and the pages |
| `tests/` | the unit tests, plus a manual UI harness |

Run the application from the project root:

```bash
python -m cleanhome.main
```

Run the tests from the project root:

```bash
python -m unittest discover -s cleanhome/tests -t .
```

Reset an administrator password that is locked out:

```bash
python -m cleanhome.reset_password --list
python -m cleanhome.reset_password --email admin@cleanhome.ph
```

The rules for working on this package are in [`../AGENTS.md`](../AGENTS.md)
and in [`AGENTS.md`](AGENTS.md) next to this file.

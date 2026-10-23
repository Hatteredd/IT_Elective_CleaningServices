"""Command-line password reset for an administrator who cannot sign in.

Run it from the project root::

    python -m cleanhome.reset_password --list
    python -m cleanhome.reset_password --email admin@cleanhome.ph
    python -m cleanhome.reset_password --email admin@cleanhome.ph --generate

The script sets a new password, clears the failed-attempt lockout, and
re-activates the account. It never imports tkinter, so it works on a
machine with no desktop session, and it never prints the password unless it
generated one itself (in which case the password is shown once).
"""

from __future__ import annotations

import argparse
import getpass
import sqlite3
import sys
from datetime import datetime

from cleanhome import config, db, security


def _admins() -> list[dict]:
    """Return every administrator account with its current state."""
    rows = db.query(
        "SELECT id, full_name, email, is_active, failed_attempts, locked_until "
        "FROM users WHERE role = ? ORDER BY email",
        ("admin",),
    )
    return db.rows_to_dicts(rows)


def _state(account: dict) -> str:
    """Describe the account state in one short word."""
    if not account["is_active"]:
        return "deactivated"
    locked_until = account.get("locked_until")
    if locked_until:
        try:
            moment = datetime.strptime(str(locked_until), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return "unknown"
        if moment > datetime.now():
            return "locked"
    if account.get("failed_attempts"):
        return f"{account['failed_attempts']} failed attempt(s)"
    return "ok"


def list_admins() -> int:
    """Print the administrator accounts and their state."""
    accounts = _admins()
    if not accounts:
        print("There is no administrator account in the database yet.")
        print("Start CleanHome once and use the Create Admin Account screen.")
        return 1
    print("Administrator accounts:")
    for account in accounts:
        print(f"  {account['email']:<40} {account['full_name']:<24} {_state(account)}")
    return 0


def _ask(prompt: str) -> str:
    """Read a line, hiding it when the terminal allows it."""
    if sys.stdin.isatty():
        return getpass.getpass(prompt)
    return input(prompt).strip()


def _ask_password() -> str | None:
    """Ask for a new password twice, without echoing it."""
    first = _ask("New password: ")
    if not first:
        print("No password entered. Nothing was changed.")
        return None
    second = _ask("Confirm new password: ")
    if first != second:
        print("The two passwords did not match. Nothing was changed.")
        return None
    return first


def reset(email: str, password: str, force_change: bool = False) -> int:
    """Set a new password for ``email`` and clear the lockout.

    ``force_change`` marks the account so the next sign-in must set a new
    password; it is used for generated passwords so they are not kept.
    """
    account = db.query_one(
        "SELECT id, full_name, role, is_active FROM users WHERE email = ?",
        (email.strip().lower(),),
    )
    if account is None:
        print(f"No account uses the email {email!r}.")
        print("Run this script with --list to see the administrator accounts.")
        return 1
    if account["role"] != "admin":
        print(f"{email} is not an administrator account.")
        print("Only an administrator password can be reset here.")
        return 1

    problems = security.password_problems(password)
    if problems:
        for problem in problems:
            print(problem)
        return 1

    salt, password_hash = security.hash_password(password)
    db.execute(
        "UPDATE users SET pw_salt = ?, pw_hash = ?, failed_attempts = 0, "
        "locked_until = NULL, is_active = 1, must_change_password = ? WHERE id = ?",
        (salt, password_hash, 1 if force_change else 0, account["id"]),
    )
    print(f"Password reset for {email}.")
    print("The lockout was cleared and the account is active again.")
    if force_change:
        print("A new password must be chosen at the next sign-in.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the reset tool from the command line."""
    parser = argparse.ArgumentParser(
        prog="python -m cleanhome.reset_password",
        description="Reset an administrator password and clear a login lockout.",
    )
    parser.add_argument("--list", action="store_true",
                        help="list the administrator accounts and exit")
    parser.add_argument("--email", help="the email address of the administrator")
    parser.add_argument("--generate", action="store_true",
                        help="generate a random password and print it once")
    args = parser.parse_args(argv)

    if not config.DB_PATH.exists():
        print(f"No database found at {config.DB_PATH}.")
        print("Start CleanHome once first so it can create the database.")
        return 1

    try:
        if args.list:
            return list_admins()
        if not args.email:
            parser.print_help()
            print("\nGive --email to reset an account, or --list to see them.")
            return 2
        if args.generate:
            password = security.generate_password()
            printed = True
        else:
            password = _ask_password()
            printed = False
        if password is None:
            return 1
        result = reset(args.email, password, force_change=printed)
        if result == 0 and printed:
            print()
            print("New password: " + password)
            print("Write it down now. It is not shown again.")
        return result
    except sqlite3.Error as error:
        print(f"The database could not be updated: {error}")
        return 1
    finally:
        db.close_connection()


if __name__ == "__main__":
    sys.exit(main())

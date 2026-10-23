"""Console entry point for the packaged maintenance tools.

The windowed ``CleanHomePH.exe`` has no console, so the installed build
ships a second console executable that wraps the same commands::

    CleanHomeTools.exe backup
    CleanHomeTools.exe reset-password --list
    CleanHomeTools.exe reset-password --email admin@example.com --generate

From source the same commands are available as ``python -m cleanhome.backup``
and ``python -m cleanhome.reset_password``.
"""

from __future__ import annotations

import sys

from cleanhome import backup, reset_password

COMMANDS = {
    "backup": (backup.main, "copy the database to a timestamped backup file"),
    "reset-password": (reset_password.main, "reset an administrator password"),
}


def main(argv: list[str] | None = None) -> int:
    """Dispatch to one of the maintenance commands."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print("CleanHome maintenance tools")
        print()
        for name, (_, help_text) in COMMANDS.items():
            print(f"  {name:<16} {help_text}")
        print()
        print("Run a command with --help for its options.")
        return 0 if args else 2
    command, rest = args[0], args[1:]
    action = COMMANDS.get(command)
    if action is None:
        print(f"Unknown command: {command}")
        print("Available commands: " + ", ".join(COMMANDS))
        return 2
    return action[0](rest)


if __name__ == "__main__":
    sys.exit(main())

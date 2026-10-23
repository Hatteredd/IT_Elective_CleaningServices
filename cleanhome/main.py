"""Application entry point."""

from __future__ import annotations

import logging
import os

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from cleanhome import config, db
from cleanhome.ui.app import CleanHomeApp


def setup_logging() -> None:
    """Write logs to disk without breaking the Tkinter loop."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=config.LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    """Bootstrap the database and launch the UI."""
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    import tkinter as tk

    try:
        root_probe = tk.Tk()
        root_probe.withdraw()
        try:
            root_probe.tk.call("tk", "scaling", 1.0)
        finally:
            root_probe.destroy()
    except tk.TclError:
        pass
    setup_logging()
    logging.info("Starting CleanHome from %s", config.DATA_DIR)
    db.init_db()
    db.migrate()
    db.seed()
    app = CleanHomeApp()
    app.go("CreateAdmin" if app.first_run_required() else "Home")
    app.mainloop()


if __name__ == "__main__":
    main()

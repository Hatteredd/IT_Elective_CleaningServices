"""Application configuration.

Every business rule constant, path, and company detail used anywhere in the
app lives here. The logic layer and the UI must import from this module
instead of hard-coding numbers of their own.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent


def resolve_data_dir(frozen: bool, local_app_data: str | None) -> Path:
    """Return the writable folder that holds the database, log, and backups.

    A packaged executable must never write next to the program: the program
    folder may be read-only or under ``Program Files``. When frozen it uses
    ``%LOCALAPPDATA%\\CleanHomePH``; when running from source it keeps the
    database in the project root so development and tests stay simple.
    """
    if frozen:
        base = local_app_data or str(Path.home() / "AppData" / "Local")
        return Path(base) / "CleanHomePH"
    return Path(__file__).resolve().parent.parent


DATA_DIR = resolve_data_dir(bool(getattr(sys, "frozen", False)),
                            os.environ.get("LOCALAPPDATA"))
DB_PATH = DATA_DIR / "cleanhome.db"
LOG_PATH = DATA_DIR / "app.log"
BACKUP_DIR = DATA_DIR / "backups"

# ── Company details ───────────────────────────────────────────────────────────
# Edit this block only. The Home, About, Contact, navigation, and footer read
# every company detail from here.
COMPANY_NAME = "CleanHome PH"  # REPLACE BEFORE RELEASE
COMPANY_TAGLINE = "Metro Manila's trusted home cleaning service."  # REPLACE BEFORE RELEASE
COMPANY_REGION = "Metro Manila"  # REPLACE BEFORE RELEASE
COMPANY_EMAIL = "support@cleanhome.ph"  # REPLACE BEFORE RELEASE
COMPANY_PHONE = "+63 (02) 8123-4567"  # REPLACE BEFORE RELEASE
COMPANY_ADDRESS = "Makati City, Metro Manila"  # REPLACE BEFORE RELEASE
COMPANY_HOURS = "8:00 AM - 6:00 PM (Monday to Sunday)"  # REPLACE BEFORE RELEASE
SERVICE_AREAS = "Makati, Taguig (BGC), Pasig, Mandaluyong, San Juan, Quezon City, Manila"  # REPLACE BEFORE RELEASE
CURRENCY_SYMBOL = "₱"

# A customer may cancel only this many hours before the scheduled start.
CANCEL_CUTOFF_HOURS = 24  # REPLACE BEFORE RELEASE if the policy changes

# How many bookings may overlap at the same moment (team capacity).
MAX_CONCURRENT_BOOKINGS = 3  # REPLACE BEFORE RELEASE if the team size changes

# ── Business rules ────────────────────────────────────────────────────────────
# Cleaning runs between 8:00 AM and 6:00 PM Philippine Standard Time.
BUSINESS_OPEN_HOUR = 8
BUSINESS_CLOSE_HOUR = 18
SLOT_INTERVAL_MINUTES = 30

# A booking must be made at least this many hours in advance.
MIN_LEAD_TIME_HOURS = 3

# How far ahead a customer may schedule a cleaning.
BOOKING_WINDOW_DAYS = 30

# How many days the date pickers offer (the window plus some slack).
DATE_PICKER_DAYS = 60

# How many days back and forward the report date pickers reach.
REPORT_WINDOW_DAYS = 30

# How many services the revenue chart on the report screen shows.
REPORT_CHART_SERVICES = 8

# Service duration limits, in minutes.
MIN_DURATION_MINUTES = 15
MAX_DURATION_MINUTES = 480

# Booking notes are optional but capped.
MAX_NOTES_LENGTH = 300

# Promotion value limits.
MIN_PERCENT_DISCOUNT = 1
MAX_PERCENT_DISCOUNT = 90

# ── Field limits ──────────────────────────────────────────────────────────────
MAX_NAME_LENGTH = 120
MAX_ADDRESS_LENGTH = 255
MAX_SERVICE_NAME_LENGTH = 100

# How many services the home page shows, and how many bookings the admin
# dashboard lists under "Upcoming bookings".
FEATURED_SERVICE_COUNT = 3
UPCOMING_BOOKINGS_LIMIT = 10

DASHBOARD_TREND_MONTHS = 6
DASHBOARD_TOP_SERVICES = 5

# Minutes in an hour, used to turn the opening and closing hours into times.
MINUTES_PER_HOUR = 60

# Length of a password made by the command-line reset tool.
GENERATED_PASSWORD_LENGTH = 14

# How long SQLite waits for a locked database (in milliseconds).
DB_BUSY_TIMEOUT_MS = 5000

# ── Security ─────────────────────────────────────────────────────────────────
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 5
PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16
MIN_PASSWORD_LENGTH = 8

# ── Window ───────────────────────────────────────────────────────────────────
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 650
WINDOW_DEFAULT_WIDTH = 1180
WINDOW_DEFAULT_HEIGHT = 760

# ── Seed catalogue ────────────────────────────────────────────────────────────
# The service catalogue the app starts with: (name, description, price, minutes).
SEED_SERVICES: tuple[tuple[str, str, float, int], ...] = (
    ("Standard Home Cleaning", "A complete clean for living rooms, bedrooms, kitchens and bathrooms.", 1299.00, 90),
    ("Deep Cleaning", "Detailed top-to-bottom clean including buildup, degreasing and sanitising.", 2499.00, 180),
    ("Move-in/Move-out Cleaning", "Empty-home deep clean ready for handover or a fresh tenant.", 2999.00, 240),
    ("Kitchen Deep Cleaning", "Degreasing, descaling and polishing for all kitchen surfaces.", 999.00, 90),
    ("Bathroom Deep Cleaning", "Scrubbing, descaling and sanitising for bathrooms and toilets.", 699.00, 60),
    ("Sofa Cleaning", "Fabric sofa shampooing and stain treatment.", 799.00, 60),
    ("Window Deep Wash", "Interior and exterior glass cleaning for a streak-free finish.", 899.00, 90),
)

# The starter promotions: (title, discount type, value).
SEED_PROMOTIONS: tuple[tuple[str, str, float], ...] = (
    ("Welcome 10% Off", "percent", 10.0),
    ("Save ₱200", "fixed", 200.0),
)

# How long the starter promotions stay valid (in days).
PROMO_DEFAULT_DAYS = 30
SEED_PROMOTION_SPAN_DAYS = 730

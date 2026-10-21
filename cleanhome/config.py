"""Application configuration.

Every business rule constant, path, and company detail used anywhere in the
app lives here. The logic layer and the UI must import from this module
instead of hard-coding numbers of their own.
"""

from __future__ import annotations

from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent

DB_PATH = PROJECT_DIR / "cleanhome.db"
LOG_PATH = PROJECT_DIR / "app.log"

# ── Business rules ────────────────────────────────────────────────────────────
# Cleaning runs between 8:00 AM and 6:00 PM Philippine Standard Time.
BUSINESS_OPEN_HOUR = 8
BUSINESS_CLOSE_HOUR = 18
SLOT_INTERVAL_MINUTES = 30

# How many bookings may overlap at the same moment (team capacity).
MAX_CONCURRENT_BOOKINGS = 3

# A booking must be made at least this many hours in advance.
MIN_LEAD_TIME_HOURS = 3

# How far ahead a customer may schedule a cleaning.
BOOKING_WINDOW_DAYS = 30

# How many days back and forward the report date pickers reach.
REPORT_WINDOW_DAYS = 30

# A customer may cancel only this many hours before the scheduled start.
CANCEL_CUTOFF_HOURS = 24

# Service duration limits, in minutes.
MIN_DURATION_MINUTES = 15
MAX_DURATION_MINUTES = 480

# Booking notes are optional but capped.
MAX_NOTES_LENGTH = 300

# Promotion value limits.
MIN_PERCENT_DISCOUNT = 1
MAX_PERCENT_DISCOUNT = 90

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

# ── Company details (edit these to match your own business) ─────────────────
COMPANY_NAME = "CleanHome PH"
COMPANY_TAGLINE = "Metro Manila's trusted home cleaning service."
COMPANY_EMAIL = "support@cleanhome.ph"
COMPANY_PHONE = "+63 (02) 8123-4567"
COMPANY_ADDRESS = "Makati City, Metro Manila"
COMPANY_HOURS = "8:00 AM - 6:00 PM (Monday to Sunday)"
SERVICE_AREAS = "Makati, Taguig (BGC), Pasig, Mandaluyong, San Juan, Quezon City, Manila"
CURRENCY_SYMBOL = "₱"

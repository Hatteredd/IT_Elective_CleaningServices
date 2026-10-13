# CleanHome PH — Home Cleaning Service Desktop Application

A complete Tkinter desktop GUI application for managing home cleaning services in the Philippines.

## Technology Stack

- **UI / Frontend**: Python standard library Tkinter + ttk (multi-frame desktop GUI)
- **Database & ORM**: SQLite with SQLAlchemy
- **Authentication**: Password hashing with Werkzeug
- **Payment**: Sandbox/mock payment (PayMongo-ready)

---

## Installation

### 1. Clone and enter the project

```bash
cd IT_Service
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```
SECRET_KEY=change-this-to-a-long-random-string
DATABASE_URL=sqlite:///instance/app.db
```

For PayMongo (optional, sandbox payments work without it):

```
PAYMONGO_PUBLIC_KEY=pk_test_...
PAYMONGO_SECRET_KEY=sk_test_...
PAYMONGO_WEBHOOK_SECRET=whsec_...
```

### 5. Initialise the database

```bash
python init_db.py
```

This creates all tables and handles schema migrations for existing databases.

### 6. Seed sample data (services, add-ons, promo codes)

```bash
python seed_data.py
```

### 7. Create an admin account

```bash
python create_admin.py
```

---

## Running the Application
 
```bash
python run.py
```
 
This launches the Tkinter desktop GUI window.
 
You can also run:
```bash
python gui_app.py
```

---

## Running Tests

```bash
pytest
```

Or with verbose output:

```bash
pytest -v
```

Test files cover:

| File | Coverage |
|---|---|
| `tests/test_models.py` | User auth, registration, bookings, cleaners |
| `tests/test_auth_permissions.py` | Role access control, password reset flow |
| `tests/test_pricing.py` | Server-side price calculation, promo validation |
| `tests/test_availability.py` | Double-booking and cleaner conflict detection |
| `tests/test_payment.py` | Payment creation, status updates, uniqueness |

---

## Project Structure

```
IT_Service/
├── app/
│   ├── __init__.py           # App factory + context processor
│   ├── models.py             # All SQLAlchemy models
│   ├── forms.py              # WTForms (CSRF-protected)
│   ├── utils.py              # Shared helpers (notifications)
│   ├── routes/
│   │   ├── auth.py           # Login, register, forgot/reset password
│   │   ├── public.py         # Home, services, promotions, about, contact, FAQ
│   │   ├── customer.py       # Dashboard, booking, payment, reviews, reschedule
│   │   └── admin.py          # Full admin panel with audit logging
│   ├── static/css/style.css  # Responsive stylesheet
│   └── templates/            # Jinja2 templates (base + per-blueprint)
├── tests/                    # Pytest test suite
├── instance/app.db           # SQLite database (git-ignored)
├── init_db.py                # DB initialisation + migrations
├── seed_data.py              # Sample services, add-ons, promo codes
├── create_admin.py           # Interactive admin account creation
├── .env.example              # Environment variable template
├── requirements.txt          # Pinned dependencies
└── run.py                    # Development entry point
```

---

## Key Features

**Public**
- Service catalogue with pricing and add-ons
- Active promotions listing
- Contact form (stored as inquiries)
- About and FAQ pages
- Mobile-friendly navigation

**Customer accounts**
- Register, log in, log out, forgot/reset password
- Manage profile and multiple addresses
- Book services with add-ons and promo codes
- Reschedule or cancel pending/confirmed bookings
- Mock/sandbox payment flow
- View booking history, payment status, receipts
- Submit reviews after completed bookings
- In-app notification centre

**Admin panel**
- Dashboard with live stats (revenue, bookings, customers)
- Create, edit, archive, restore services and add-ons
- Manage promotions (percentage/fixed, expiry, usage limits)
- View all bookings; update status; assign cleaners
- Customer list with account activate/deactivate
- Cleaner list with availability toggle
- Sales reports (last 30 days)
- Audit log of admin actions

---

## Security Notes

- Passwords hashed with Werkzeug (`scrypt` / `pbkdf2`)
- CSRF protection on every form via Flask-WTF
- Role-based access control on all routes
- Prices and discounts always calculated server-side
- Payment references include a random token — never trust client-submitted totals
- Inactive accounts cannot log in
- Password reset tokens expire after 1 hour and are single-use
- Do **not** commit `.env` to version control
- Use a strong `SECRET_KEY` in production
- Enable HTTPS in production

---

## Implementation Status

| Phase | Description | Status |
|---|---|---|
| 1 | Project setup, Flask app, database, base layout | ✅ |
| 2 | Registration, login, roles, password reset | ✅ |
| 3 | Public pages, services, pricing, promotions | ✅ |
| 4 | Customer booking, scheduling, availability | ✅ |
| 5 | Payment integration (sandbox mode) | ✅ |
| 6 | Admin dashboard and management features | ✅ |
| 7 | Cleaner assignment, notifications, reviews, audit logs | ✅ |
| 8 | Automated tests, security hardening, README | ✅ |

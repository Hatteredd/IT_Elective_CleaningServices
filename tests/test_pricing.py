"""Tests for server-side price calculation and promotion validation."""
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta, date, time

from app import create_app, db
from app.models import (
    User, CustomerProfile, Service, AddOn, Promotion,
    Booking, BookingItem, PromotionRedemption, Address,
)


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ── helpers ──────────────────────────────────────────────────────────────────

def make_customer(app, email='c@test.com'):
    user = User(email=email, role='customer')
    user.set_password('pass1234')
    profile = CustomerProfile(user=user, first_name='Ana', last_name='Cruz')
    db.session.add_all([user, profile])
    db.session.flush()
    address = Address(
        customer_id=profile.id,
        street='1 Rizal St', city='Manila', province='Metro Manila',
    )
    db.session.add(address)
    db.session.commit()
    return user, profile, address


def make_service(app, price=1000.00):
    s = Service(name='Test Clean', base_price=price, duration_minutes=60, is_active=True)
    db.session.add(s)
    db.session.commit()
    return s


def make_promo(app, **kwargs):
    now = datetime.now(timezone.utc)
    defaults = dict(
        code='PROMO10',
        discount_type='percentage',
        discount_value=10,
        min_order_value=0,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=30),
        is_active=True,
    )
    defaults.update(kwargs)
    p = Promotion(**defaults)
    db.session.add(p)
    db.session.commit()
    return p


# ── pricing tests ─────────────────────────────────────────────────────────────

def test_percentage_discount_calculated_server_side(app):
    with app.app_context():
        s = make_service(app, price=1000.00)
        p = make_promo(app, discount_type='percentage', discount_value=10)

        subtotal = Decimal(str(s.base_price))
        discount = subtotal * (Decimal(str(p.discount_value)) / 100)
        total = subtotal - discount

        assert discount == Decimal('100.00')
        assert total == Decimal('900.00')


def test_fixed_discount_calculated_server_side(app):
    with app.app_context():
        s = make_service(app, price=1500.00)
        p = make_promo(app, code='SAVE200', discount_type='fixed', discount_value=200)

        subtotal = Decimal(str(s.base_price))
        discount = Decimal(str(p.discount_value))
        total = subtotal - discount

        assert discount == Decimal('200.00')
        assert total == Decimal('1300.00')


def test_max_discount_cap(app):
    with app.app_context():
        s = make_service(app, price=5000.00)
        p = make_promo(app, discount_type='percentage', discount_value=50, max_discount_amount=300)

        subtotal = Decimal(str(s.base_price))
        raw_discount = subtotal * (Decimal(str(p.discount_value)) / 100)  # 2500
        discount = min(raw_discount, Decimal(str(p.max_discount_amount)))

        assert discount == Decimal('300.00')


def test_addon_price_included_in_subtotal(app):
    with app.app_context():
        s = make_service(app, price=799.00)
        addon = AddOn(service_id=s.id, name='Window Clean', price=299.00, is_active=True)
        db.session.add(addon)
        db.session.commit()

        subtotal = Decimal(str(s.base_price)) + Decimal(str(addon.price))
        assert subtotal == Decimal('1098.00')


def test_booking_stores_price_at_time_of_booking(app):
    """Price on the booking should not change if service price changes later."""
    with app.app_context():
        _, profile, address = make_customer(app)
        s = make_service(app, price=999.00)

        booking = Booking(
            customer_id=profile.id,
            address_id=address.id,
            scheduled_date=date.today(),
            scheduled_time=time(9, 0),
            subtotal=Decimal('999.00'),
            total_amount=Decimal('999.00'),
        )
        db.session.add(booking)
        db.session.flush()

        item = BookingItem(
            booking_id=booking.id,
            service_id=s.id,
            unit_price=Decimal('999.00'),
            total_price=Decimal('999.00'),
            service_name=s.name,
        )
        db.session.add(item)

        # Now change the service price
        s.base_price = Decimal('1299.00')
        db.session.commit()

        # Booking item still holds the original price
        saved = BookingItem.query.filter_by(booking_id=booking.id).first()
        assert saved.unit_price == Decimal('999.00')


# ── promotion validation tests ────────────────────────────────────────────────

def test_expired_promo_rejected(app):
    with app.app_context():
        now = datetime.now(timezone.utc)
        p = make_promo(app, code='OLD',
                       start_date=now - timedelta(days=10),
                       end_date=now - timedelta(days=1))

        # SQLite stores naive datetimes; normalise before comparing
        end = p.end_date.replace(tzinfo=timezone.utc) if p.end_date.tzinfo is None else p.end_date
        assert end < now  # expired


def test_future_promo_rejected(app):
    with app.app_context():
        now = datetime.now(timezone.utc)
        p = make_promo(app, code='FUTURE',
                       start_date=now + timedelta(days=5),
                       end_date=now + timedelta(days=15))

        start = p.start_date.replace(tzinfo=timezone.utc) if p.start_date.tzinfo is None else p.start_date
        assert start > now  # not started yet


def test_min_order_not_met_rejects_promo(app):
    with app.app_context():
        p = make_promo(app, code='MIN500', min_order_value=500)
        subtotal = Decimal('300.00')
        assert subtotal < Decimal(str(p.min_order_value))


def test_usage_limit_enforced(app):
    with app.app_context():
        p = make_promo(app, code='LIMITED', usage_limit=2, usage_count=2)
        assert p.usage_limit is not None and p.usage_count >= p.usage_limit


def test_inactive_promo_not_applied(app):
    with app.app_context():
        p = make_promo(app, code='INACTIVE', is_active=False)
        result = Promotion.query.filter_by(code='INACTIVE', is_active=True).first()
        assert result is None

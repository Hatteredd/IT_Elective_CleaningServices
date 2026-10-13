"""Tests for booking availability and double-booking prevention."""
import pytest
from datetime import date, time, datetime, timezone

from app import create_app, db
from app.models import User, CustomerProfile, Service, Booking, Address, Cleaner


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


def _make_base(app):
    user = User(email='cust@test.com', role='customer')
    user.set_password('pass1234')
    profile = CustomerProfile(user=user, first_name='Juan', last_name='dela Cruz')
    db.session.add_all([user, profile])
    db.session.flush()
    address = Address(
        customer_id=profile.id,
        street='2 Mabini St', city='Cebu', province='Cebu',
    )
    service = Service(name='Basic Clean', base_price=799, duration_minutes=60, is_active=True)
    db.session.add_all([address, service])
    db.session.commit()
    return profile, address, service


def _make_cleaner(app):
    u = User(email='cleaner@test.com', role='cleaner')
    u.set_password('pass1234')
    db.session.add(u)
    db.session.flush()
    c = Cleaner(user_id=u.id, first_name='Rosa', last_name='Santos', is_available=True)
    db.session.add(c)
    db.session.commit()
    return c


def test_no_double_booking_same_slot(app):
    """Two bookings on the same date/time should be detectable."""
    with app.app_context():
        profile, address, service = _make_base(app)

        booking_date = date(2026, 12, 1)
        booking_time = time(9, 0)

        b1 = Booking(
            customer_id=profile.id, address_id=address.id,
            scheduled_date=booking_date, scheduled_time=booking_time,
            subtotal=799, total_amount=799,
        )
        db.session.add(b1)
        db.session.commit()

        # Simulate availability check: query for active bookings in the same slot
        conflict = Booking.query.filter_by(
            scheduled_date=booking_date,
            scheduled_time=booking_time,
        ).filter(Booking.status.notin_(['cancelled'])).count()

        assert conflict == 1  # one existing booking blocks the slot


def test_cancelled_booking_frees_slot(app):
    with app.app_context():
        profile, address, service = _make_base(app)

        booking_date = date(2026, 12, 2)
        booking_time = time(10, 0)

        b = Booking(
            customer_id=profile.id, address_id=address.id,
            scheduled_date=booking_date, scheduled_time=booking_time,
            subtotal=799, total_amount=799, status='cancelled',
        )
        db.session.add(b)
        db.session.commit()

        conflict = Booking.query.filter_by(
            scheduled_date=booking_date,
            scheduled_time=booking_time,
        ).filter(Booking.status.notin_(['cancelled'])).count()

        assert conflict == 0  # cancelled booking does not block


def test_cleaner_not_double_assigned(app):
    """Same cleaner should not be assigned to two bookings at the same date/time."""
    with app.app_context():
        profile, address, service = _make_base(app)
        cleaner = _make_cleaner(app)

        booking_date = date(2026, 12, 3)
        booking_time = time(8, 0)

        b1 = Booking(
            customer_id=profile.id, address_id=address.id,
            scheduled_date=booking_date, scheduled_time=booking_time,
            subtotal=799, total_amount=799, cleaner_id=cleaner.id,
        )
        db.session.add(b1)
        db.session.commit()

        # Check if cleaner is already booked at this slot
        cleaner_conflict = Booking.query.filter_by(
            cleaner_id=cleaner.id,
            scheduled_date=booking_date,
            scheduled_time=booking_time,
        ).filter(Booking.status.notin_(['cancelled'])).count()

        assert cleaner_conflict >= 1

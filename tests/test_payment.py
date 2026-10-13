"""Tests for payment status verification and mock payment flow."""
import pytest
from decimal import Decimal
from datetime import date, time, datetime, timezone

from app import create_app, db
from app.models import User, CustomerProfile, Booking, Payment, Address, Service

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


def _register_and_login(client):
    client.post('/auth/register', data={
        'email': 'pay@test.com', 'password': 'pass1234',
        'confirm_password': 'pass1234', 'first_name': 'Pay', 'last_name': 'Test',
    })
    client.post('/auth/login', data={'email': 'pay@test.com', 'password': 'pass1234'})


def _make_booking(app, client):
    """Create the minimum DB fixtures and return a booking that can be paid."""
    with app.app_context():
        user = User.query.filter_by(email='pay@test.com').first()
        profile = user.customer_profile
        address = Address(
            customer_id=profile.id, street='3 Luna St',
            city='Quezon City', province='Metro Manila',
        )
        db.session.add(address)
        db.session.flush()
        booking = Booking(
            customer_id=profile.id, address_id=address.id,
            scheduled_date=date(2027, 1, 10), scheduled_time=time(9, 0),
            subtotal=Decimal('799.00'), total_amount=Decimal('799.00'),
        )
        db.session.add(booking)
        db.session.commit()
        return booking.id


def test_payment_creates_payment_record(app, client):
    _register_and_login(client)
    booking_id = _make_booking(app, client)

    resp = client.post(
        f'/customer/bookings/{booking_id}/pay',
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        payment = Payment.query.filter_by(booking_id=booking_id).first()
        assert payment is not None
        assert payment.status == 'completed'


def test_payment_updates_booking_status(app, client):
    _register_and_login(client)
    booking_id = _make_booking(app, client)

    client.post(f'/customer/bookings/{booking_id}/pay', follow_redirects=True)

    with app.app_context():
        booking = db.session.get(Booking, booking_id)
        assert booking.payment_status == 'paid'
        assert booking.status == 'confirmed'


def test_cannot_pay_cancelled_booking(app, client):
    _register_and_login(client)
    booking_id = _make_booking(app, client)

    with app.app_context():
        booking = db.session.get(Booking, booking_id)
        booking.status = 'cancelled'
        db.session.commit()

    resp = client.post(f'/customer/bookings/{booking_id}/pay', follow_redirects=True)
    assert b'Cannot pay for cancelled bookings' in resp.data


def test_cannot_pay_already_paid_booking(app, client):
    _register_and_login(client)
    booking_id = _make_booking(app, client)

    # Pay once
    client.post(f'/customer/bookings/{booking_id}/pay', follow_redirects=True)
    # Try again
    resp = client.post(f'/customer/bookings/{booking_id}/pay', follow_redirects=True)
    assert b'already paid' in resp.data


def test_payment_amount_matches_booking_total(app, client):
    _register_and_login(client)
    booking_id = _make_booking(app, client)

    client.post(f'/customer/bookings/{booking_id}/pay', follow_redirects=True)

    with app.app_context():
        booking = db.session.get(Booking, booking_id)
        payment = Payment.query.filter_by(booking_id=booking_id).first()
        assert payment.amount == booking.total_amount


def test_payment_reference_is_unique(app, client):
    _register_and_login(client)
    bid1 = _make_booking(app, client)

    # Create a second booking
    with app.app_context():
        user = User.query.filter_by(email='pay@test.com').first()
        profile = user.customer_profile
        address = Address.query.filter_by(customer_id=profile.id).first()
        b2 = Booking(
            customer_id=profile.id, address_id=address.id,
            scheduled_date=date(2027, 1, 11), scheduled_time=time(10, 0),
            subtotal=Decimal('1299.00'), total_amount=Decimal('1299.00'),
        )
        db.session.add(b2)
        db.session.commit()
        bid2 = b2.id

    client.post(f'/customer/bookings/{bid1}/pay', follow_redirects=True)
    client.post(f'/customer/bookings/{bid2}/pay', follow_redirects=True)

    with app.app_context():
        refs = [p.payment_reference for p in Payment.query.all()]
        assert len(refs) == len(set(refs))  # all unique

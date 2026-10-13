import pytest
from app import create_app, db
from app.models import User, CustomerProfile, Service, Booking, Promotion, Cleaner
from datetime import datetime, date, time, timezone

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

def test_user_password_hashing(app):
    with app.app_context():
        user = User(email='test@example.com', role='customer')
        user.set_password('password123')
        assert user.check_password('password123') is True
        assert user.check_password('wrongpassword') is False

def test_service_creation(app):
    with app.app_context():
        service = Service(
            name='Test Service',
            description='A test service',
            base_price=999.00,
            duration_minutes=60
        )
        db.session.add(service)
        db.session.commit()
        
        assert service.id is not None
        assert service.name == 'Test Service'
        assert float(service.base_price) == 999.00

def test_user_registration(client):
    response = client.post('/auth/register', data={
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'first_name': 'John',
        'last_name': 'Doe',
        'phone': '09123456789'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Registration successful' in response.data

def test_duplicate_email_registration(client):
    # Register first user
    client.post('/auth/register', data={
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'first_name': 'John',
        'last_name': 'Doe'
    })
    
    # Try to register with same email
    response = client.post('/auth/register', data={
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'first_name': 'Jane',
        'last_name': 'Smith'
    })
    assert b'Email already registered' in response.data

def test_login(client):
    # Register a user first
    client.post('/auth/register', data={
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'first_name': 'John',
        'last_name': 'Doe'
    })
    
    # Login
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Customer Dashboard' in response.data

def test_invalid_login(client):
    response = client.post('/auth/login', data={
        'email': 'nonexistent@example.com',
        'password': 'wrongpassword'
    })
    assert b'Invalid email or password' in response.data

def test_password_mismatch_registration(client):
    response = client.post('/auth/register', data={
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'different',
        'first_name': 'John',
        'last_name': 'Doe'
    })
    assert b'Field must be equal to password' in response.data

def test_promotion_validation(app):
    with app.app_context():
        # Create a promotion with minimum order value
        promo = Promotion(
            code='TEST20',
            description='Test promotion',
            discount_type='percentage',
            discount_value=20.00,
            min_order_value=1000.00,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            is_active=True
        )
        db.session.add(promo)
        db.session.commit()
        
        assert promo.code == 'TEST20'
        assert float(promo.min_order_value) == 1000.00

def test_booking_creation(app):
    with app.app_context():
        # Create user and profile
        user = User(email='test@example.com', role='customer')
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        
        profile = CustomerProfile(
            user_id=user.id,
            first_name='John',
            last_name='Doe'
        )
        db.session.add(profile)
        db.session.flush()
        
        # Create service
        service = Service(
            name='Test Service',
            description='A test service',
            base_price=999.00,
            duration_minutes=60
        )
        db.session.add(service)
        db.session.flush()
        
        # Create address
        from app.models import Address
        address = Address(
            customer_id=profile.id,
            street='123 Test St',
            city='Test City',
            province='Test Province'
        )
        db.session.add(address)
        db.session.flush()
        
        # Create booking
        booking = Booking(
            customer_id=profile.id,
            address_id=address.id,
            scheduled_date=date.today(),
            scheduled_time=time(10, 0),
            subtotal=999.00,
            total_amount=999.00,
            status='pending',
            payment_status='unpaid'
        )
        db.session.add(booking)
        db.session.commit()
        
        assert booking.id is not None
        assert booking.status == 'pending'
        assert float(booking.total_amount) == 999.00

def test_cleaner_creation(app):
    with app.app_context():
        user = User(email='cleaner@example.com', role='cleaner')
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        
        cleaner = Cleaner(
            user_id=user.id,
            first_name='Jane',
            last_name='Smith',
            phone='09876543210',
            is_available=True
        )
        db.session.add(cleaner)
        db.session.commit()
        
        assert cleaner.id is not None
        assert cleaner.is_available is True

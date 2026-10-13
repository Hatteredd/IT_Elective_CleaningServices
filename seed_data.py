from app import create_app, db
from app.models import Service, AddOn, Promotion
from datetime import datetime, timedelta, timezone

app = create_app()

with app.app_context():
    # Clear existing data
    Service.query.delete()
    AddOn.query.delete()
    Promotion.query.delete()
    db.session.commit()
    
    # Create sample services
    services_data = [
        {
            'name': 'Basic Home Cleaning',
            'description': 'Essential cleaning for a tidy home. Includes dusting, vacuuming, mopping, and bathroom cleaning.',
            'base_price': 799.00,
            'duration_minutes': 60,
            'is_active': True
        },
        {
            'name': 'Standard Home Cleaning',
            'description': 'Comprehensive cleaning service. Includes all basic cleaning plus kitchen deep cleaning and window cleaning.',
            'base_price': 1299.00,
            'duration_minutes': 90,
            'is_active': True
        },
        {
            'name': 'Deep Cleaning',
            'description': 'Thorough cleaning for every corner. Perfect for spring cleaning or move-in/move-out situations.',
            'base_price': 2499.00,
            'duration_minutes': 180,
            'is_active': True
        },
        {
            'name': 'Move-in/Move-out Cleaning',
            'description': 'Complete cleaning for empty homes before or after moving. Includes inside cabinets and appliances.',
            'base_price': 2999.00,
            'duration_minutes': 240,
            'is_active': True
        },
        {
            'name': 'Kitchen Deep Cleaning',
            'description': 'Intensive kitchen cleaning including appliances, cabinets, and backsplashes.',
            'base_price': 999.00,
            'duration_minutes': 90,
            'is_active': True
        },
        {
            'name': 'Bathroom Deep Cleaning',
            'description': 'Thorough bathroom cleaning including tiles, grout, fixtures, and sanitization.',
            'base_price': 699.00,
            'duration_minutes': 60,
            'is_active': True
        },
        {
            'name': 'Sofa Cleaning',
            'description': 'Professional sofa cleaning and sanitization for upholstered furniture.',
            'base_price': 799.00,
            'duration_minutes': 60,
            'is_active': True
        }
    ]
    
    services = []
    for data in services_data:
        service = Service(**data)
        db.session.add(service)
        services.append(service)
    
    db.session.commit()
    
    # Create sample add-ons for Basic Home Cleaning
    basic_service = services[0]
    add_ons_data = [
        {
            'service_id': basic_service.id,
            'name': 'Interior Window Cleaning',
            'description': 'Clean all interior windows in your home',
            'price': 299.00,
            'is_active': True
        },
        {
            'service_id': basic_service.id,
            'name': 'Refrigerator Interior Cleaning',
            'description': 'Deep clean inside your refrigerator',
            'price': 299.00,
            'is_active': True
        },
        {
            'service_id': basic_service.id,
            'name': 'Extra Room',
            'description': 'Additional bedroom or living area',
            'price': 250.00,
            'is_active': True
        }
    ]
    
    for data in add_ons_data:
        add_on = AddOn(**data)
        db.session.add(add_on)
    
    db.session.commit()
    
    # Create sample promotions
    today = datetime.now(timezone.utc)
    promotions_data = [
        {
            'code': 'WELCOME10',
            'description': 'Welcome discount for new customers',
            'discount_type': 'percentage',
            'discount_value': 10.00,
            'min_order_value': 500.00,
            'max_discount_amount': 200.00,
            'start_date': today,
            'end_date': today + timedelta(days=365),
            'usage_limit': 100,
            'is_stackable': False,
            'is_active': True
        },
        {
            'code': 'WEEKDAY15',
            'description': '15% off on weekday bookings (Monday-Thursday)',
            'discount_type': 'percentage',
            'discount_value': 15.00,
            'min_order_value': 1000.00,
            'max_discount_amount': 300.00,
            'start_date': today,
            'end_date': today + timedelta(days=90),
            'usage_limit': None,
            'is_stackable': False,
            'is_active': True
        },
        {
            'code': 'SAVE200',
            'description': 'Flat ₱200 discount on orders over ₱1500',
            'discount_type': 'fixed',
            'discount_value': 200.00,
            'min_order_value': 1500.00,
            'max_discount_amount': None,
            'start_date': today,
            'end_date': today + timedelta(days=30),
            'usage_limit': 50,
            'is_stackable': True,
            'is_active': True
        }
    ]
    
    for data in promotions_data:
        promotion = Promotion(**data)
        db.session.add(promotion)
    
    db.session.commit()
    
    print('Sample data seeded successfully!')
    print(f'Created {len(services)} services')
    print(f'Created {len(add_ons_data)} add-ons')
    print(f'Created {len(promotions_data)} promotions')

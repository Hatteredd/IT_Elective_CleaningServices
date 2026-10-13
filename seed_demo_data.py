"""Comprehensive demo data seed script for CleanHome PH.
Seeds:
- Admin user (admin@cleanhome.ph / Admin123!)
- Multiple Customers with realistic addresses and phone numbers
- Professional Cleaners with active statuses
- Services & Add-ons as per specifications
- Active & scheduled Promotions
- Diverse Bookings across pending, confirmed, in_progress, completed, and cancelled statuses
- Associated BookingItems, Payments (cash, paymongo), and Promotion Redemptions
- Customer Reviews & Ratings
- Customer Inquiries / Contact messages
- Admin Audit Logs
"""
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal
import json

from app import create_app, db
from app.models import (
    User, CustomerProfile, Cleaner, Address,
    Service, AddOn, Promotion, PromotionRedemption,
    Booking, BookingItem, Payment, Review,
    Inquiry, Notification, AuditLog, BusinessSettings
)

app = create_app()

with app.app_context():
    print("Beginning database seeding with comprehensive demo data...")
    db.create_all()

    # 1. ADMIN USER
    admin = User.query.filter_by(email='admin@cleanhome.ph').first()
    if not admin:
        admin = User(email='admin@cleanhome.ph', role='admin', is_active=True)
        admin.set_password('Admin123!')
        db.session.add(admin)
        print("Created admin account: admin@cleanhome.ph")
    else:
        admin.set_password('Admin123!')
        admin.role = 'admin'
        admin.is_active = True
        print("Ensured admin account: admin@cleanhome.ph")

    db.session.flush()

    # 2. CUSTOMERS
    customer_defs = [
        {
            'email': 'customer@cleanhome.ph',
            'password': 'Customer123!',
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'phone': '09171234567',
            'addresses': [
                {'label': 'Home', 'street': 'Unit 1204, Tower 1, The Columns Legazpi', 'city': 'Makati City', 'province': 'Metro Manila', 'postal_code': '1229', 'is_default': True},
                {'label': 'Office', 'street': '18F PBCom Tower, 6795 Ayala Avenue', 'city': 'Makati City', 'province': 'Metro Manila', 'postal_code': '1226', 'is_default': False}
            ]
        },
        {
            'email': 'maria.santos@gmail.com',
            'password': 'Password123!',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'phone': '09189876543',
            'addresses': [
                {'label': 'Condo', 'street': '24B Fairways Tower, 5th Avenue, BGC', 'city': 'Taguig City', 'province': 'Metro Manila', 'postal_code': '1634', 'is_default': True}
            ]
        },
        {
            'email': 'carlo.reyes@yahoo.com',
            'password': 'Password123!',
            'first_name': 'Carlo',
            'last_name': 'Reyes',
            'phone': '09223456789',
            'addresses': [
                {'label': 'Townhouse', 'street': 'Blk 4 Lot 12 Mahogany Place 3, Acacia Estates', 'city': 'Taguig City', 'province': 'Metro Manila', 'postal_code': '1630', 'is_default': True}
            ]
        },
        {
            'email': 'alyssa.tan@outlook.com',
            'password': 'Password123!',
            'first_name': 'Alyssa',
            'last_name': 'Tan',
            'phone': '09154321098',
            'addresses': [
                {'label': 'Home', 'street': '88 Annapolis Street, Greenhills', 'city': 'San Juan City', 'province': 'Metro Manila', 'postal_code': '1504', 'is_default': True}
            ]
        }
    ]

    customers = []
    for c_def in customer_defs:
        user = User.query.filter_by(email=c_def['email']).first()
        if not user:
            user = User(email=c_def['email'], role='customer', is_active=True)
            user.set_password(c_def['password'])
            db.session.add(user)
            db.session.flush()

        profile = CustomerProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = CustomerProfile(
                user_id=user.id,
                first_name=c_def['first_name'],
                last_name=c_def['last_name'],
                phone=c_def['phone']
            )
            db.session.add(profile)
            db.session.flush()

            for a_def in c_def['addresses']:
                addr = Address(
                    customer_id=profile.id,
                    label=a_def['label'],
                    street=a_def['street'],
                    city=a_def['city'],
                    province=a_def['province'],
                    postal_code=a_def['postal_code'],
                    is_default=a_def['is_default']
                )
                db.session.add(addr)
        customers.append(profile)

    db.session.flush()

    # 3. CLEANERS
    cleaner_defs = [
        {'email': 'elena.bautista@cleanhome.ph', 'first_name': 'Elena', 'last_name': 'Bautista', 'phone': '09175550101', 'is_available': True},
        {'email': 'ricardo.mendoza@cleanhome.ph', 'first_name': 'Ricardo', 'last_name': 'Mendoza', 'phone': '09175550202', 'is_available': True},
        {'email': 'analyn.ramos@cleanhome.ph', 'first_name': 'Analyn', 'last_name': 'Ramos', 'phone': '09175550303', 'is_available': True},
        {'email': 'jovito.garcia@cleanhome.ph', 'first_name': 'Jovito', 'last_name': 'Garcia', 'phone': '09175550404', 'is_available': False}
    ]

    cleaners = []
    for cl_def in cleaner_defs:
        user = User.query.filter_by(email=cl_def['email']).first()
        if not user:
            user = User(email=cl_def['email'], role='cleaner', is_active=True)
            user.set_password('Cleaner123!')
            db.session.add(user)
            db.session.flush()

        cleaner = Cleaner.query.filter_by(user_id=user.id).first()
        if not cleaner:
            cleaner = Cleaner(
                user_id=user.id,
                first_name=cl_def['first_name'],
                last_name=cl_def['last_name'],
                phone=cl_def['phone'],
                is_available=cl_def['is_available']
            )
            db.session.add(cleaner)
        cleaners.append(cleaner)

    db.session.flush()

    # 4. SERVICES
    services_data = [
        {
            'name': 'Basic Home Cleaning',
            'description': 'Essential cleaning for a tidy home. Includes dusting, vacuuming, mopping, trash removal, and bathroom surface disinfection.',
            'base_price': Decimal('799.00'),
            'duration_minutes': 60,
            'is_active': True
        },
        {
            'name': 'Standard Home Cleaning',
            'description': 'Comprehensive routine cleaning. Covers thorough bedroom, living area, kitchen surface cleaning, and sanitized bathrooms.',
            'base_price': Decimal('1299.00'),
            'duration_minutes': 90,
            'is_active': True
        },
        {
            'name': 'Deep Cleaning',
            'description': 'Intensive, corner-to-corner sanitization. Perfect for seasonal resets, grime removal, and post-gathering recovery.',
            'base_price': Decimal('2499.00'),
            'duration_minutes': 180,
            'is_active': True
        },
        {
            'name': 'Move-in/Move-out Cleaning',
            'description': 'Complete turnkey detailing for empty homes and condos before occupancy or handover inspection.',
            'base_price': Decimal('2999.00'),
            'duration_minutes': 240,
            'is_active': True
        },
        {
            'name': 'Kitchen Deep Cleaning',
            'description': 'Heavy degreasing of stovetops, range hoods, exterior cabinetry, countertops, tile walls, and sinks.',
            'base_price': Decimal('999.00'),
            'duration_minutes': 90,
            'is_active': True
        },
        {
            'name': 'Bathroom Deep Cleaning',
            'description': 'Vigorous tile scrubbing, grout descaling, glass shower enclosure treatment, and fixture polish.',
            'base_price': Decimal('699.00'),
            'duration_minutes': 60,
            'is_active': True
        },
        {
            'name': 'Sofa Cleaning',
            'description': 'Professional fabric/leather upholstery deep vacuuming, stain spot-treatment, and anti-bacterial steaming.',
            'base_price': Decimal('799.00'),
            'duration_minutes': 60,
            'is_active': True
        }
    ]

    services_map = {}
    for s_item in services_data:
        existing_srv = Service.query.filter_by(name=s_item['name']).first()
        if not existing_srv:
            existing_srv = Service(**s_item)
            db.session.add(existing_srv)
            db.session.flush()
        services_map[existing_srv.name] = existing_srv

    # 5. ADD-ONS
    add_ons_data = [
        {'service_name': 'Basic Home Cleaning', 'name': 'Interior Window Cleaning', 'description': 'Streak-free window glass and frame wipe down', 'price': Decimal('299.00')},
        {'service_name': 'Basic Home Cleaning', 'name': 'Refrigerator Interior Cleaning', 'description': 'Empty shelves, disinfect interior, deodorize', 'price': Decimal('299.00')},
        {'service_name': 'Basic Home Cleaning', 'name': 'Extra Room Cleaning', 'description': 'Additional bedroom or study area cleaning', 'price': Decimal('250.00')},
        {'service_name': 'Standard Home Cleaning', 'name': 'Oven Interior Degrease', 'description': 'Deep baked-on residue removal inside oven', 'price': Decimal('349.00')},
        {'service_name': 'Deep Cleaning', 'name': 'Balcony Wash & Scrub', 'description': 'Floor scrub and railing sanitization', 'price': Decimal('399.00')},
    ]

    add_ons_map = {}
    for ao in add_ons_data:
        srv = services_map.get(ao['service_name'])
        if srv:
            existing_ao = AddOn.query.filter_by(service_id=srv.id, name=ao['name']).first()
            if not existing_ao:
                existing_ao = AddOn(
                    service_id=srv.id,
                    name=ao['name'],
                    description=ao['description'],
                    price=ao['price'],
                    is_active=True
                )
                db.session.add(existing_ao)
                db.session.flush()
            add_ons_map[existing_ao.name] = existing_ao

    # 6. PROMOTIONS
    now = datetime.now(timezone.utc)
    promotions_data = [
        {
            'code': 'WELCOME10',
            'description': '10% discount on your first booking',
            'discount_type': 'percentage',
            'discount_value': Decimal('10.00'),
            'min_order_value': Decimal('500.00'),
            'max_discount_amount': Decimal('200.00'),
            'start_date': now - timedelta(days=30),
            'end_date': now + timedelta(days=365),
            'usage_limit': 500,
            'is_stackable': False,
            'is_active': True
        },
        {
            'code': 'WEEKDAY15',
            'description': '15% off Monday to Thursday appointments',
            'discount_type': 'percentage',
            'discount_value': Decimal('15.00'),
            'min_order_value': Decimal('1000.00'),
            'max_discount_amount': Decimal('300.00'),
            'start_date': now - timedelta(days=30),
            'end_date': now + timedelta(days=120),
            'usage_limit': 200,
            'is_stackable': False,
            'is_active': True
        },
        {
            'code': 'SAVE200',
            'description': '₱200 flat voucher for orders over ₱1,500',
            'discount_type': 'fixed',
            'discount_value': Decimal('200.00'),
            'min_order_value': Decimal('1500.00'),
            'max_discount_amount': None,
            'start_date': now - timedelta(days=15),
            'end_date': now + timedelta(days=60),
            'usage_limit': 100,
            'is_stackable': True,
            'is_active': True
        }
    ]

    promos_map = {}
    for promo in promotions_data:
        p_obj = Promotion.query.filter_by(code=promo['code']).first()
        if not p_obj:
            p_obj = Promotion(**promo)
            db.session.add(p_obj)
            db.session.flush()
        promos_map[p_obj.code] = p_obj

    db.session.commit()

    # 7. BOOKINGS & OPERATIONAL DATA (If not already present)
    existing_bookings_count = Booking.query.count()
    if existing_bookings_count == 0:
        print("Generating realistic demo bookings...")
        today = date.today()

        c_juan = customers[0]
        c_maria = customers[1]
        c_carlo = customers[2]
        c_alyssa = customers[3]

        addr_juan = c_juan.addresses[0]
        addr_maria = c_maria.addresses[0]
        addr_carlo = c_carlo.addresses[0]
        addr_alyssa = c_alyssa.addresses[0]

        cl_elena = cleaners[0]
        cl_ricardo = cleaners[1]
        cl_analyn = cleaners[2]

        srv_deep = services_map['Deep Cleaning']
        srv_basic = services_map['Basic Home Cleaning']
        srv_standard = services_map['Standard Home Cleaning']
        srv_sofa = services_map['Sofa Cleaning']

        ao_window = add_ons_map.get('Interior Window Cleaning')
        ao_fridge = add_ons_map.get('Refrigerator Interior Cleaning')
        ao_balcony = add_ons_map.get('Balcony Wash & Scrub')

        # Booking 1: Completed Deep Clean with Review (Last week)
        b1_date = today - timedelta(days=7)
        b1_subtotal = srv_deep.base_price + (ao_balcony.price if ao_balcony else Decimal('0'))
        b1_discount = Decimal('200.00') # SAVE200
        b1_total = b1_subtotal - b1_discount

        b1 = Booking(
            customer_id=c_juan.id,
            address_id=addr_juan.id,
            cleaner_id=cl_elena.id,
            scheduled_date=b1_date,
            scheduled_time=time(9, 0),
            status='completed',
            payment_status='paid',
            subtotal=b1_subtotal,
            discount_amount=b1_discount,
            total_amount=b1_total,
            notes='Please focus on the balcony tiles and master bathroom.',
            created_at=datetime.combine(b1_date - timedelta(days=3), time(14, 20), tzinfo=timezone.utc)
        )
        db.session.add(b1)
        db.session.flush()

        db.session.add(BookingItem(
            booking_id=b1.id,
            service_id=srv_deep.id,
            quantity=1,
            unit_price=srv_deep.base_price,
            total_price=srv_deep.base_price,
            service_name=srv_deep.name,
            service_description=srv_deep.description
        ))
        if ao_balcony:
            db.session.add(BookingItem(
                booking_id=b1.id,
                add_on_id=ao_balcony.id,
                quantity=1,
                unit_price=ao_balcony.price,
                total_price=ao_balcony.price,
                service_name=ao_balcony.name,
                service_description=ao_balcony.description
            ))

        db.session.add(Payment(
            booking_id=b1.id,
            payment_method='paymongo',
            payment_reference='pay_mock_live_001_juan',
            amount=b1_total,
            status='completed',
            paid_at=datetime.combine(b1_date - timedelta(days=3), time(14, 25), tzinfo=timezone.utc),
            payment_metadata=json.dumps({'channel': 'gcash', 'fee': '0.00'})
        ))

        db.session.add(Review(
            booking_id=b1.id,
            customer_id=c_juan.id,
            rating=5,
            comment='Elena did a phenomenal job! Our condo feels completely brand new and the balcony tiles are immaculate. Will definitely book every month!',
            created_at=datetime.combine(b1_date, time(16, 0), tzinfo=timezone.utc)
        ))

        p_save200 = promos_map.get('SAVE200')
        if p_save200:
            db.session.add(PromotionRedemption(
                promotion_id=p_save200.id,
                booking_id=b1.id,
                discount_amount=b1_discount
            ))
            p_save200.usage_count = (p_save200.usage_count or 0) + 1

        # Booking 2: In-Progress Standard Clean (Today)
        b2_subtotal = srv_standard.base_price
        b2_total = b2_subtotal
        b2 = Booking(
            customer_id=c_maria.id,
            address_id=addr_maria.id,
            cleaner_id=cl_ricardo.id,
            scheduled_date=today,
            scheduled_time=time(13, 0),
            status='in_progress',
            payment_status='paid',
            subtotal=b2_subtotal,
            discount_amount=Decimal('0'),
            total_amount=b2_total,
            notes='Buzz unit 24B at the front desk.',
            created_at=datetime.combine(today - timedelta(days=1), time(10, 15), tzinfo=timezone.utc)
        )
        db.session.add(b2)
        db.session.flush()

        db.session.add(BookingItem(
            booking_id=b2.id,
            service_id=srv_standard.id,
            quantity=1,
            unit_price=srv_standard.base_price,
            total_price=srv_standard.base_price,
            service_name=srv_standard.name,
            service_description=srv_standard.description
        ))
        db.session.add(Payment(
            booking_id=b2.id,
            payment_method='paymongo',
            payment_reference='pay_mock_live_002_maria',
            amount=b2_total,
            status='completed',
            paid_at=datetime.combine(today - timedelta(days=1), time(10, 18), tzinfo=timezone.utc),
            payment_metadata=json.dumps({'channel': 'card', 'last4': '4242'})
        ))

        # Booking 3: Confirmed Upcoming Basic Clean with Add-on (Tomorrow)
        b3_date = today + timedelta(days=1)
        b3_subtotal = srv_basic.base_price + (ao_fridge.price if ao_fridge else Decimal('0'))
        b3_discount = Decimal('79.90') # WELCOME10 10%
        b3_total = b3_subtotal - b3_discount

        b3 = Booking(
            customer_id=c_carlo.id,
            address_id=addr_carlo.id,
            cleaner_id=cl_analyn.id,
            scheduled_date=b3_date,
            scheduled_time=time(10, 0),
            status='confirmed',
            payment_status='paid',
            subtotal=b3_subtotal,
            discount_amount=b3_discount,
            total_amount=b3_total,
            notes='Gate code is #4412. We have a friendly golden retriever.',
            created_at=datetime.combine(today, time(8, 30), tzinfo=timezone.utc)
        )
        db.session.add(b3)
        db.session.flush()

        db.session.add(BookingItem(
            booking_id=b3.id,
            service_id=srv_basic.id,
            quantity=1,
            unit_price=srv_basic.base_price,
            total_price=srv_basic.base_price,
            service_name=srv_basic.name,
            service_description=srv_basic.description
        ))
        if ao_fridge:
            db.session.add(BookingItem(
                booking_id=b3.id,
                add_on_id=ao_fridge.id,
                quantity=1,
                unit_price=ao_fridge.price,
                total_price=ao_fridge.price,
                service_name=ao_fridge.name,
                service_description=ao_fridge.description
            ))

        db.session.add(Payment(
            booking_id=b3.id,
            payment_method='cash',
            payment_reference='CASH-PENDING-CARLO',
            amount=b3_total,
            status='completed',
            paid_at=datetime.combine(today, time(8, 35), tzinfo=timezone.utc),
            payment_metadata=json.dumps({'channel': 'cash_on_delivery'})
        ))

        # Booking 4: Pending Booking awaiting Cleaner Assignment (3 days from now)
        b4_date = today + timedelta(days=3)
        b4_subtotal = srv_sofa.base_price
        b4_total = b4_subtotal

        b4 = Booking(
            customer_id=c_alyssa.id,
            address_id=addr_alyssa.id,
            cleaner_id=None,
            scheduled_date=b4_date,
            scheduled_time=time(14, 0),
            status='pending',
            payment_status='paid',
            subtotal=b4_subtotal,
            discount_amount=Decimal('0'),
            total_amount=b4_total,
            notes='L-shaped sectional couch, light beige fabric.',
            created_at=datetime.combine(today, time(11, 0), tzinfo=timezone.utc)
        )
        db.session.add(b4)
        db.session.flush()

        db.session.add(BookingItem(
            booking_id=b4.id,
            service_id=srv_sofa.id,
            quantity=1,
            unit_price=srv_sofa.base_price,
            total_price=srv_sofa.base_price,
            service_name=srv_sofa.name,
            service_description=srv_sofa.description
        ))
        db.session.add(Payment(
            booking_id=b4.id,
            payment_method='paymongo',
            payment_reference='pay_mock_live_004_alyssa',
            amount=b4_total,
            status='completed',
            paid_at=datetime.combine(today, time(11, 5), tzinfo=timezone.utc),
            payment_metadata=json.dumps({'channel': 'maya'})
        ))

        # Booking 5: Completed Move-out Clean with Review (2 weeks ago)
        b5_date = today - timedelta(days=14)
        srv_move = services_map['Move-in/Move-out Cleaning']
        b5_subtotal = srv_move.base_price
        b5_total = b5_subtotal

        b5 = Booking(
            customer_id=c_maria.id,
            address_id=addr_maria.id,
            cleaner_id=cl_ricardo.id,
            scheduled_date=b5_date,
            scheduled_time=time(9, 0),
            status='completed',
            payment_status='paid',
            subtotal=b5_subtotal,
            discount_amount=Decimal('0'),
            total_amount=b5_total,
            notes='End-of-lease inspection turnover clean.',
            created_at=datetime.combine(b5_date - timedelta(days=5), time(9, 0), tzinfo=timezone.utc)
        )
        db.session.add(b5)
        db.session.flush()

        db.session.add(BookingItem(
            booking_id=b5.id,
            service_id=srv_move.id,
            quantity=1,
            unit_price=srv_move.base_price,
            total_price=srv_move.base_price,
            service_name=srv_move.name,
            service_description=srv_move.description
        ))
        db.session.add(Payment(
            booking_id=b5.id,
            payment_method='paymongo',
            payment_reference='pay_mock_live_005_maria',
            amount=b5_total,
            status='completed',
            paid_at=datetime.combine(b5_date - timedelta(days=5), time(9, 5), tzinfo=timezone.utc)
        ))
        db.session.add(Review(
            booking_id=b5.id,
            customer_id=c_maria.id,
            rating=5,
            comment='Super reliable! The landlord gave back 100% of my security deposit because the unit was spotless.',
            created_at=datetime.combine(b5_date, time(18, 0), tzinfo=timezone.utc)
        ))

        # Booking 6: Cancelled booking (customer reschedule requested)
        b6_date = today - timedelta(days=2)
        b6 = Booking(
            customer_id=c_carlo.id,
            address_id=addr_carlo.id,
            cleaner_id=None,
            scheduled_date=b6_date,
            scheduled_time=time(15, 0),
            status='cancelled',
            payment_status='unpaid',
            subtotal=srv_basic.base_price,
            discount_amount=Decimal('0'),
            total_amount=srv_basic.base_price,
            notes='Customer had emergency family travel.',
            created_at=datetime.combine(b6_date - timedelta(days=2), time(14, 0), tzinfo=timezone.utc)
        )
        db.session.add(b6)
        db.session.flush()
        db.session.add(BookingItem(
            booking_id=b6.id,
            service_id=srv_basic.id,
            quantity=1,
            unit_price=srv_basic.base_price,
            total_price=srv_basic.base_price,
            service_name=srv_basic.name,
            service_description=srv_basic.description
        ))

    # 8. INQUIRIES
    if Inquiry.query.count() == 0:
        print("Adding sample inquiries...")
        inquiries_data = [
            {
                'name': 'Patricia Lim',
                'email': 'patricia.lim@gmail.com',
                'phone': '09178889900',
                'subject': 'Commercial Office Cleaning Quote',
                'message': 'Good day! Do you provide weekly recurring cleaning for a 150sqm office space in Ortigas Center?',
                'status': 'new',
                'created_at': now - timedelta(hours=3)
            },
            {
                'name': 'Mark Andrew Villanueva',
                'email': 'mark.villanueva@corporate.ph',
                'phone': '09201112233',
                'subject': 'Post-Renovation Cleaning Inquiry',
                'message': 'Hi CleanHome PH team. We just finished renovating our 3-bedroom home in Quezon City. Do you supply industrial vacuums for heavy dust removal?',
                'status': 'in_progress',
                'created_at': now - timedelta(days=1, hours=4)
            },
            {
                'name': 'Grace Fernandez',
                'email': 'grace.f@yahoo.com',
                'phone': '09334445566',
                'subject': 'Special Pet-Safe Cleaning Products',
                'message': 'Inquiring if your cleaning solutions and detergents are safe for households with newborn cats and dogs.',
                'status': 'resolved',
                'created_at': now - timedelta(days=4)
            }
        ]
        for inq in inquiries_data:
            db.session.add(Inquiry(**inq))

    # 9. AUDIT LOGS
    if AuditLog.query.count() == 0 and admin:
        print("Generating admin audit trail...")
        audit_records = [
            {
                'user_id': admin.id,
                'action': 'create_service',
                'entity_type': 'service',
                'entity_id': 1,
                'changes': json.dumps({'name': 'Basic Home Cleaning', 'base_price': '799.00'}),
                'ip_address': '127.0.0.1',
                'created_at': now - timedelta(days=10)
            },
            {
                'user_id': admin.id,
                'action': 'create_promotion',
                'entity_type': 'promotion',
                'entity_id': 1,
                'changes': json.dumps({'code': 'WELCOME10', 'discount': '10%'}),
                'ip_address': '127.0.0.1',
                'created_at': now - timedelta(days=8)
            },
            {
                'user_id': admin.id,
                'action': 'assign_cleaner',
                'entity_type': 'booking',
                'entity_id': 1,
                'changes': json.dumps({'cleaner': 'Elena Bautista'}),
                'ip_address': '127.0.0.1',
                'created_at': now - timedelta(days=5)
            },
            {
                'user_id': admin.id,
                'action': 'update_status',
                'entity_type': 'booking',
                'entity_id': 1,
                'changes': json.dumps({'old': 'in_progress', 'new': 'completed'}),
                'ip_address': '127.0.0.1',
                'created_at': now - timedelta(days=7)
            }
        ]
        for al in audit_records:
            db.session.add(AuditLog(**al))

    # 10. BUSINESS SETTINGS
    default_settings = [
        ('business_name', 'CleanHome Philippines', 'Official registered trade name'),
        ('contact_email', 'support@cleanhome.ph', 'Customer support email address'),
        ('contact_phone', '+63 (02) 8123-4567', 'Customer hotline telephone number'),
        ('operating_hours', '8:00 AM - 6:00 PM (Monday to Sunday)', 'Operating service window'),
        ('service_areas', 'Makati, Taguig (BGC), Pasig, Mandaluyong, San Juan, Quezon City, Manila', 'Covered Metro Manila cities')
    ]
    for key, val, desc in default_settings:
        if not BusinessSettings.query.filter_by(key=key).first():
            db.session.add(BusinessSettings(key=key, value=val, description=desc))

    db.session.commit()
    print("Demo data successfully populated and committed to the database!")

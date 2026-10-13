from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import CustomerProfile, Address, Service, AddOn, Booking, BookingItem, Promotion, PromotionRedemption, Review, Payment
from app.forms import ProfileForm, AddressForm, BookingForm, PromoCodeForm, ReviewForm
from functools import wraps
from datetime import datetime, timedelta, date, time, timezone
from decimal import Decimal
import json
import secrets

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'customer':
            flash('Access denied. Customer access required.', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function

bp = Blueprint('customer', __name__, url_prefix='/customer')

@bp.route('/dashboard')
@login_required
@customer_required
def dashboard():
    profile = current_user.customer_profile
    bookings = Booking.query.filter_by(customer_id=profile.id).order_by(Booking.created_at.desc()).limit(5).all()
    return render_template('customer/dashboard.html', profile=profile, bookings=bookings)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
@customer_required
def profile():
    profile = current_user.customer_profile
    form = ProfileForm(obj=profile)
    
    if form.validate_on_submit():
        profile.first_name = form.first_name.data
        profile.last_name = form.last_name.data
        profile.phone = form.phone.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('customer.profile'))
    
    return render_template('customer/profile.html', form=form, profile=profile)

@bp.route('/addresses')
@login_required
@customer_required
def addresses():
    profile = current_user.customer_profile
    addresses = Address.query.filter_by(customer_id=profile.id).all()
    return render_template('customer/addresses.html', addresses=addresses)

@bp.route('/addresses/add', methods=['GET', 'POST'])
@login_required
@customer_required
def add_address():
    profile = current_user.customer_profile
    form = AddressForm()
    
    if form.validate_on_submit():
        # If setting as default, unset other defaults
        if form.is_default.data == 'True':
            Address.query.filter_by(customer_id=profile.id).update({'is_default': False})
        
        address = Address(
            customer_id=profile.id,
            label=form.label.data,
            street=form.street.data,
            city=form.city.data,
            province=form.province.data,
            postal_code=form.postal_code.data,
            is_default=form.is_default.data == 'True'
        )
        db.session.add(address)
        db.session.commit()
        flash('Address added successfully!', 'success')
        return redirect(url_for('customer.addresses'))
    
    return render_template('customer/address_form.html', form=form, title='Add Address')

@bp.route('/addresses/<int:address_id>/edit', methods=['GET', 'POST'])
@login_required
@customer_required
def edit_address(address_id):
    profile = current_user.customer_profile
    address = Address.query.filter_by(id=address_id, customer_id=profile.id).first_or_404()
    form = AddressForm(obj=address)
    
    if form.validate_on_submit():
        # If setting as default, unset other defaults
        if form.is_default.data == 'True':
            Address.query.filter_by(customer_id=profile.id).update({'is_default': False})
        
        address.label = form.label.data
        address.street = form.street.data
        address.city = form.city.data
        address.province = form.province.data
        address.postal_code = form.postal_code.data
        address.is_default = form.is_default.data == 'True'
        db.session.commit()
        flash('Address updated successfully!', 'success')
        return redirect(url_for('customer.addresses'))
    
    return render_template('customer/address_form.html', form=form, address=address, title='Edit Address')

@bp.route('/addresses/<int:address_id>/delete', methods=['POST'])
@login_required
@customer_required
def delete_address(address_id):
    profile = current_user.customer_profile
    address = Address.query.filter_by(id=address_id, customer_id=profile.id).first_or_404()
    if Booking.query.filter_by(address_id=address.id).first():
        flash('This address is linked to existing bookings and cannot be deleted.', 'error')
        return redirect(url_for('customer.addresses'))
    db.session.delete(address)
    db.session.commit()
    flash('Address deleted successfully!', 'success')
    return redirect(url_for('customer.addresses'))

# Booking routes
@bp.route('/book', methods=['GET', 'POST'])
@login_required
@customer_required
def book():
    profile = current_user.customer_profile
    addresses = Address.query.filter_by(customer_id=profile.id).all()
    services = Service.query.filter_by(is_active=True, is_archived=False).all()
    
    if not addresses:
        flash('Please add an address before booking.', 'error')
        return redirect(url_for('customer.add_address'))
    
    form = BookingForm()
    form.service_id.choices = [
        (s.id, f"{s.name} - ₱{s.discounted_price if (s.discounted_price and s.discounted_price < s.base_price) else s.base_price}")
        for s in services
    ]
    form.address_id.choices = [(a.id, f"{a.label or 'Address'}: {a.street}, {a.city}") for a in addresses]

    req_service_id = request.args.get('service_id', type=int) if request.method == 'GET' else None
    selected_service_id = form.service_id.data or req_service_id
    if selected_service_id:
        service_add_ons = AddOn.query.filter_by(service_id=selected_service_id, is_active=True).all()
    else:
        service_add_ons = AddOn.query.filter_by(is_active=True).all()
    form.add_ons.choices = [(a.id, f"{a.name} - ₱{a.price}") for a in service_add_ons]

    if request.method == 'GET':
        form.address_id.data = next((a.id for a in addresses if a.is_default), addresses[0].id if addresses else None)
        if req_service_id and any(s.id == req_service_id for s in services):
            form.service_id.data = req_service_id
        req_promo = request.args.get('promo')
        if req_promo:
            form.promo_code.data = req_promo.strip().upper()
    
    if form.validate_on_submit():
        # Check slot availability to prevent double-booking
        conflict = Booking.query.filter_by(
            scheduled_date=form.date.data,
            scheduled_time=form.time.data
        ).filter(Booking.status.notin_(['cancelled'])).first()
        if conflict:
            flash('The selected date and time slot is already booked. Please choose a different appointment time.', 'error')
            return render_template('customer/book.html', form=form, services=services, addresses=addresses)

        # Calculate total (use discounted price if available and lower than base)
        service = Service.query.get(form.service_id.data)
        service_price = service.discounted_price if (service.discounted_price and Decimal(str(service.discounted_price)) < Decimal(str(service.base_price))) else service.base_price
        subtotal = Decimal(str(service_price))
        
        # Add add-ons (only those belonging to the selected service)
        selected_add_ons = []
        if form.add_ons.data:
            for add_on_id in form.add_ons.data:
                add_on = AddOn.query.get(add_on_id)
                if add_on and add_on.is_active and add_on.service_id == service.id:
                    subtotal += Decimal(str(add_on.price))
                    selected_add_ons.append(add_on)
        
        # Apply promotions
        discount_amount = Decimal('0')
        applied_promotions = []
        promo_error = None

        if form.promo_code.data:
            code = form.promo_code.data.upper().strip()
            promo = Promotion.query.filter_by(code=code, is_active=True).first()
            now = datetime.now(timezone.utc)
            if not promo:
                promo_error = f'Promo code "{code}" is not valid.'
            else:
                p_start = promo.start_date.replace(tzinfo=timezone.utc) if promo.start_date.tzinfo is None else promo.start_date.astimezone(timezone.utc)
                p_end = promo.end_date.replace(tzinfo=timezone.utc) if promo.end_date.tzinfo is None else promo.end_date.astimezone(timezone.utc)
                if not (p_start <= now <= p_end):
                    promo_error = f'Promo code "{code}" has expired or is not yet active.'
                elif promo.usage_limit is not None and promo.usage_count >= promo.usage_limit:
                    promo_error = f'Promo code "{code}" has reached its usage limit.'
                elif subtotal < Decimal(str(promo.min_order_value)):
                    promo_error = (
                        f'Minimum order of ₱{promo.min_order_value:,.2f} required for "{code}".'
                    )
                elif promo.eligible_services:
                    try:
                        eligible_ids = json.loads(promo.eligible_services)
                    except (ValueError, TypeError):
                        eligible_ids = []
                    if service.id not in eligible_ids:
                        promo_error = f'Promo code "{code}" is not valid for this service.'
                else:
                    if promo.discount_type == 'percentage':
                        discount = subtotal * (Decimal(str(promo.discount_value)) / Decimal('100'))
                    else:
                        discount = Decimal(str(promo.discount_value))
                    if promo.max_discount_amount:
                        discount = min(discount, Decimal(str(promo.max_discount_amount)))
                    discount_amount = discount
                    applied_promotions.append(promo)

        if promo_error:
            flash(promo_error, 'error')
            return render_template('customer/book.html', form=form, services=services, addresses=addresses)
        
        total = max(Decimal('0.00'), subtotal - discount_amount)
        
        # Create booking
        booking = Booking(
            customer_id=profile.id,
            address_id=form.address_id.data,
            scheduled_date=form.date.data,
            scheduled_time=form.time.data,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total,
            notes=form.notes.data,
            status='pending',
            payment_status='unpaid'
        )
        db.session.add(booking)
        db.session.flush()
        
        # Add service item
        booking_item = BookingItem(
            booking_id=booking.id,
            service_id=service.id,
            quantity=1,
            unit_price=Decimal(str(service_price)),
            total_price=Decimal(str(service_price)),
            service_name=service.name,
            service_description=service.description
        )
        db.session.add(booking_item)
        
        # Add add-on items
        for add_on in selected_add_ons:
            booking_item = BookingItem(
                booking_id=booking.id,
                add_on_id=add_on.id,
                quantity=1,
                unit_price=Decimal(str(add_on.price)),
                total_price=Decimal(str(add_on.price)),
                service_name=add_on.name,
                service_description=add_on.description
            )
            db.session.add(booking_item)
        
        # Record promotion redemptions
        for promo in applied_promotions:
            redemption = PromotionRedemption(
                promotion_id=promo.id,
                booking_id=booking.id,
                discount_amount=discount_amount / len(applied_promotions) if len(applied_promotions) > 1 else discount_amount
            )
            db.session.add(redemption)
            promo.usage_count += 1
        
        db.session.commit()

        # Notify customer
        from app.utils import create_notification
        create_notification(
            current_user.id,
            'Booking Created',
            f'Booking #{booking.id} has been created. Please complete your payment.'
        )
        db.session.commit()

        flash('Booking created successfully! Please complete payment.', 'success')
        return redirect(url_for('customer.booking_detail', booking_id=booking.id))

    return render_template('customer/book.html', form=form, services=services, addresses=addresses)

@bp.route('/book/add-ons/<int:service_id>')
@login_required
@customer_required
def get_add_ons(service_id):
    service = Service.query.get_or_404(service_id)
    add_ons = [{'id': a.id, 'name': a.name, 'price': float(a.price), 'description': a.description or ''} for a in service.add_ons if a.is_active]
    return jsonify(add_ons)

@bp.route('/book/validate-promo')
@login_required
@customer_required
def validate_promo():
    code = request.args.get('code', '').upper().strip()
    service_id = request.args.get('service_id', type=int)
    subtotal_arg = request.args.get('subtotal', type=float) or 0.0
    subtotal = Decimal(str(subtotal_arg))
    
    if not code:
        return jsonify({'valid': False, 'message': 'Please enter a promo code.'})
        
    promo = Promotion.query.filter_by(code=code, is_active=True).first()
    if not promo:
        return jsonify({'valid': False, 'message': f'Promo code "{code}" is not valid or does not exist.'})
        
    now = datetime.now(timezone.utc)
    p_start = promo.start_date.replace(tzinfo=timezone.utc) if promo.start_date.tzinfo is None else promo.start_date.astimezone(timezone.utc)
    p_end = promo.end_date.replace(tzinfo=timezone.utc) if promo.end_date.tzinfo is None else promo.end_date.astimezone(timezone.utc)
    
    if not (p_start <= now <= p_end):
        return jsonify({'valid': False, 'message': f'Promo code "{code}" has expired or is not yet active.'})
        
    if promo.usage_limit is not None and promo.usage_count >= promo.usage_limit:
        return jsonify({'valid': False, 'message': f'Promo code "{code}" has reached its usage limit.'})
        
    if subtotal < Decimal(str(promo.min_order_value)):
        return jsonify({'valid': False, 'message': f'Minimum order of ₱{promo.min_order_value:,.2f} required for "{code}".'})
        
    if promo.eligible_services and service_id:
        try:
            eligible_ids = json.loads(promo.eligible_services)
            if service_id not in eligible_ids:
                return jsonify({'valid': False, 'message': f'Promo code "{code}" is not valid for this service.'})
        except Exception:
            pass
            
    if promo.discount_type == 'percentage':
        discount = subtotal * (Decimal(str(promo.discount_value)) / Decimal('100'))
    else:
        discount = Decimal(str(promo.discount_value))
        
    if promo.max_discount_amount:
        discount = min(discount, Decimal(str(promo.max_discount_amount)))
        
    discount = min(discount, subtotal)
    
    return jsonify({
        'valid': True,
        'code': promo.code,
        'discount_amount': float(discount),
        'discount_formatted': f"₱{discount:,.2f}",
        'description': promo.description,
        'message': f'Coupon "{promo.code}" applied: You save ₱{discount:,.2f}!'
    })


@bp.route('/bookings')
@login_required
@customer_required
def bookings():
    profile = current_user.customer_profile
    bookings = Booking.query.filter_by(customer_id=profile.id).order_by(Booking.created_at.desc()).all()
    return render_template('customer/bookings.html', bookings=bookings)

@bp.route('/bookings/<int:booking_id>')
@login_required
@customer_required
def booking_detail(booking_id):
    profile = current_user.customer_profile
    booking = Booking.query.filter_by(id=booking_id, customer_id=profile.id).first_or_404()
    return render_template('customer/booking_detail.html', booking=booking)

@bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@customer_required
def cancel_booking(booking_id):
    profile = current_user.customer_profile
    booking = Booking.query.filter_by(id=booking_id, customer_id=profile.id).first_or_404()
    
    if booking.status in ['pending', 'confirmed']:
        booking.status = 'cancelled'
        db.session.commit()
        flash('Booking cancelled successfully.', 'success')
    else:
        flash('Cannot cancel this booking.', 'error')
    
    return redirect(url_for('customer.booking_detail', booking_id=booking_id))

@bp.route('/bookings/<int:booking_id>/review', methods=['GET', 'POST'])
@login_required
@customer_required
def add_review(booking_id):
    profile = current_user.customer_profile
    booking = Booking.query.filter_by(id=booking_id, customer_id=profile.id).first_or_404()
    
    if booking.status != 'completed':
        flash('You can only review completed bookings.', 'error')
        return redirect(url_for('customer.booking_detail', booking_id=booking_id))
    
    if booking.review:
        flash('You have already reviewed this booking.', 'error')
        return redirect(url_for('customer.booking_detail', booking_id=booking_id))
    
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            booking_id=booking.id,
            customer_id=profile.id,
            rating=int(form.rating.data),
            comment=form.comment.data
        )
        db.session.add(review)
        db.session.commit()
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('customer.booking_detail', booking_id=booking_id))
    
    return render_template('customer/review_form.html', form=form, booking=booking)

# Payment routes (sandbox/mock implementation)
@bp.route('/bookings/<int:booking_id>/pay', methods=['GET', 'POST'])
@login_required
@customer_required
def pay_booking(booking_id):
    profile = current_user.customer_profile
    booking = Booking.query.filter_by(id=booking_id, customer_id=profile.id).first_or_404()
    
    if booking.payment_status == 'paid':
        flash('This booking is already paid.', 'info')
        return redirect(url_for('customer.booking_detail', booking_id=booking_id))
    
    if booking.status == 'cancelled':
        flash('Cannot pay for cancelled bookings.', 'error')
        return redirect(url_for('customer.booking_detail', booking_id=booking_id))
    
    if request.method == 'POST':
        chosen_method = request.form.get('payment_method', 'paymongo_mock')
        is_cash = chosen_method == 'cash'
        
        payment = Payment(
            booking_id=booking.id,
            payment_method=chosen_method,
            payment_reference=f'{chosen_method.upper()}-{datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")}-{secrets.token_hex(4)}',
            amount=booking.total_amount,
            status='pending' if is_cash else 'completed',
            paid_at=None if is_cash else datetime.now(timezone.utc),
            payment_metadata=json.dumps({"mode": "sandbox", "channel": chosen_method})
        )
        db.session.add(payment)
        
        booking.payment_status = 'unpaid' if is_cash else 'paid'
        booking.status = 'confirmed'
        db.session.commit()

        from app.utils import create_notification
        create_notification(
            current_user.id,
            'Payment Confirmed',
            f'Payment for Booking #{booking.id} was successful. Your booking is confirmed!'
        )
        db.session.commit()

        flash('Payment successful! Your booking is confirmed.', 'success')
        return redirect(url_for('customer.booking_detail', booking_id=booking_id))
    
    return render_template('customer/payment.html', booking=booking)


# ── Reschedule ────────────────────────────────────────────────────────────────

@bp.route('/bookings/<int:booking_id>/reschedule', methods=['GET', 'POST'])
@login_required
@customer_required
def reschedule_booking(booking_id):
    from app.forms import RescheduleForm
    profile = current_user.customer_profile
    booking = Booking.query.filter_by(id=booking_id, customer_id=profile.id).first_or_404()

    if booking.status not in ['pending', 'confirmed']:
        flash('Only pending or confirmed bookings can be rescheduled.', 'error')
        return redirect(url_for('customer.booking_detail', booking_id=booking_id))

    form = RescheduleForm()
    if form.validate_on_submit():
        conflict = Booking.query.filter_by(
            scheduled_date=form.date.data,
            scheduled_time=form.time.data
        ).filter(Booking.id != booking.id, Booking.status.notin_(['cancelled'])).first()
        if conflict:
            flash('The selected appointment slot is already booked. Please choose a different date or time.', 'error')
            return render_template('customer/reschedule_form.html', form=form, booking=booking)

        booking.scheduled_date = form.date.data
        booking.scheduled_time = form.time.data
        booking.status = 'pending'  # back to pending for admin re-confirmation
        booking.cleaner_id = None   # Unassign cleaner so schedule doesn't conflict
        db.session.commit()

        from app.utils import create_notification
        create_notification(
            current_user.id,
            'Booking Rescheduled',
            f'Booking #{booking.id} rescheduled to '
            f'{form.date.data.strftime("%B %d, %Y")} at {form.time.data.strftime("%I:%M %p")}.'
        )
        db.session.commit()

        flash('Booking rescheduled successfully.', 'success')
        return redirect(url_for('customer.booking_detail', booking_id=booking_id))

    return render_template('customer/reschedule_form.html', form=form, booking=booking)


# ── Notifications ─────────────────────────────────────────────────────────────

@bp.route('/notifications')
@login_required
@customer_required
def notifications():
    from app.models import Notification
    notifs = (Notification.query
              .filter_by(user_id=current_user.id)
              .order_by(Notification.created_at.desc())
              .all())
    # Mark all as read
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return render_template('customer/notifications.html', notifications=notifs)

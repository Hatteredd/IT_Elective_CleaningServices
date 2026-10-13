from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import (Service, AddOn, Promotion, Booking, CustomerProfile, User,
                        Cleaner, Payment, AuditLog, Inquiry, BusinessSettings, Review)
from app.forms import (ServiceForm, AddOnForm, PromotionForm, SettingsForm,
                       AdminProfileForm, PasswordChangeForm, CleanerEditForm)
from functools import wraps
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
import json


def log_action(action, entity_type, entity_id=None, changes=None):
    entry = AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=json.dumps(changes) if changes else None,
        ip_address=request.remote_addr,
    )
    db.session.add(entry)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


bp = Blueprint('admin', __name__, url_prefix='/admin')


# ─────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────
@bp.route('/')
@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    today = date.today()
    now = datetime.now(timezone.utc)

    total_bookings = Booking.query.count()
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter_by(status='completed').scalar() or Decimal('0')
    total_customers = CustomerProfile.query.filter_by(is_archived=False).count()
    active_services = Service.query.filter_by(is_active=True, is_archived=False).count()
    pending_bookings = Booking.query.filter_by(status='pending').count()
    completed_services = Booking.query.filter_by(status='completed').count()

    # Revenue trend data (last 30 days, aggregated by day)
    chart_period = request.args.get('period', 'daily')
    if chart_period == 'weekly':
        days = 84  # ~12 weeks
    elif chart_period == 'monthly':
        days = 180  # ~6 months
    else:
        days = 30

    start_date = today - timedelta(days=days)
    payments = Payment.query.filter(
        Payment.status == 'completed',
        Payment.paid_at.isnot(None),
        Payment.paid_at >= datetime.combine(start_date, datetime.min.time())
    ).all()

    revenue_by_day = {}
    for p in payments:
        if p.paid_at:
            d = p.paid_at.date()
            revenue_by_day[d] = revenue_by_day.get(d, Decimal('0')) + p.amount

    if chart_period == 'weekly':
        chart_labels = []
        chart_data = []
        for i in range(12):
            week_start = today - timedelta(days=(11 - i) * 7)
            week_end = week_start + timedelta(days=6)
            week_total = sum(v for k, v in revenue_by_day.items() if week_start <= k <= week_end)
            chart_labels.append(week_start.strftime('%b %d'))
            chart_data.append(float(week_total))
    elif chart_period == 'monthly':
        from collections import defaultdict
        month_totals = defaultdict(Decimal)
        for d, amt in revenue_by_day.items():
            key = (d.year, d.month)
            month_totals[key] += amt
        chart_labels = []
        chart_data = []
        for i in range(6):
            m_date = today.replace(day=1) - timedelta(days=i * 30)
            key = (m_date.year, m_date.month)
            chart_labels.append(m_date.strftime('%b %Y'))
            chart_data.append(float(month_totals.get(key, Decimal('0'))))
        chart_labels.reverse()
        chart_data.reverse()
    else:
        chart_labels = []
        chart_data = []
        for i in range(days):
            d = today - timedelta(days=(days - 1 - i))
            chart_labels.append(d.strftime('%b %d'))
            chart_data.append(float(revenue_by_day.get(d, Decimal('0'))))

    # Booking status distribution
    statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
    status_counts = {}
    for s in statuses:
        status_counts[s] = Booking.query.filter_by(status=s).count()

    # Recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()

    # Upcoming appointments (confirmed/in_progress, today or future)
    upcoming = Booking.query.filter(
        Booking.status.in_(['confirmed', 'in_progress']),
        Booking.scheduled_date >= today
    ).order_by(Booking.scheduled_date, Booking.scheduled_time).limit(8).all()

    # Recent activity
    recent_activity = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                         total_bookings=total_bookings,
                         total_revenue=total_revenue,
                         total_customers=total_customers,
                         active_services=active_services,
                         pending_bookings=pending_bookings,
                         completed_services=completed_services,
                         chart_labels=json.dumps(chart_labels),
                         chart_data=json.dumps(chart_data),
                         chart_period=chart_period,
                         status_counts=status_counts,
                         recent_bookings=recent_bookings,
                         upcoming=upcoming,
                         recent_activity=recent_activity)


# ─────────────────────────────────────────────────────────────
# SERVICES
# ─────────────────────────────────────────────────────────────
@bp.route('/services')
@login_required
@admin_required
def services():
    search = request.args.get('search', '').strip()
    q = Service.query.filter_by(is_archived=False)
    if search:
        q = q.filter(Service.name.ilike(f'%{search}%'))
    services = q.order_by(Service.name).all()
    archived = Service.query.filter_by(is_archived=True).order_by(Service.name).all()
    return render_template('admin/services.html', services=services, archived=archived, search=search, active_page='services')


@bp.route('/services/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_service():
    form = ServiceForm()
    if form.validate_on_submit():
        service = Service(
            name=form.name.data,
            description=form.description.data,
            base_price=form.base_price.data,
            discounted_price=form.discounted_price.data,
            duration_minutes=form.duration_minutes.data,
            image_url=form.image_url.data,
            is_active=form.is_active.data
        )
        db.session.add(service)
        db.session.flush()
        log_action('create', 'service', service.id, {'name': service.name})
        db.session.commit()
        flash('Service added successfully!', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/service_form.html', form=form, title='Add Service', active_page='services')


@bp.route('/services/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    form = ServiceForm(obj=service)
    if form.validate_on_submit():
        service.name = form.name.data
        service.description = form.description.data
        service.base_price = form.base_price.data
        service.discounted_price = form.discounted_price.data
        service.duration_minutes = form.duration_minutes.data
        service.image_url = form.image_url.data
        service.is_active = form.is_active.data
        log_action('update', 'service', service.id, {'name': service.name})
        db.session.commit()
        flash('Service updated successfully!', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/service_form.html', form=form, service=service, title='Edit Service', active_page='services')


@bp.route('/services/<int:service_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.is_archived = True
    service.is_active = False
    log_action('archive', 'service', service_id, {'name': service.name})
    db.session.commit()
    flash('Service archived successfully!', 'success')
    return redirect(url_for('admin.services'))


@bp.route('/services/<int:service_id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.is_archived = False
    log_action('restore', 'service', service_id, {'name': service.name})
    db.session.commit()
    flash('Service restored successfully!', 'success')
    return redirect(url_for('admin.archived'))


@bp.route('/services/<int:service_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    if not service.is_archived:
        flash('Service must be archived before permanent deletion.', 'error')
        return redirect(url_for('admin.services'))
    log_action('delete', 'service', service_id, {'name': service.name})
    db.session.delete(service)
    db.session.commit()
    flash('Service permanently deleted.', 'success')
    return redirect(url_for('admin.archived'))


# ─────────────────────────────────────────────────────────────
# ADD-ONS
# ─────────────────────────────────────────────────────────────
@bp.route('/services/<int:service_id>/add-ons')
@login_required
@admin_required
def service_add_ons(service_id):
    service = Service.query.get_or_404(service_id)
    add_ons = AddOn.query.filter_by(service_id=service_id).all()
    return render_template('admin/add_ons.html', service=service, add_ons=add_ons, active_page='services')


@bp.route('/services/<int:service_id>/add-ons/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_add_on(service_id):
    service = Service.query.get_or_404(service_id)
    form = AddOnForm()
    if form.validate_on_submit():
        add_on = AddOn(
            service_id=service_id,
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            is_active=form.is_active.data
        )
        db.session.add(add_on)
        db.session.commit()
        flash('Add-on added successfully!', 'success')
        return redirect(url_for('admin.service_add_ons', service_id=service_id))
    return render_template('admin/add_on_form.html', form=form, service=service, title='Add Add-on', active_page='services')


@bp.route('/add-ons/<int:add_on_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_add_on(add_on_id):
    add_on = AddOn.query.get_or_404(add_on_id)
    form = AddOnForm(obj=add_on)
    if form.validate_on_submit():
        add_on.name = form.name.data
        add_on.description = form.description.data
        add_on.price = form.price.data
        add_on.is_active = form.is_active.data
        db.session.commit()
        flash('Add-on updated successfully!', 'success')
        return redirect(url_for('admin.service_add_ons', service_id=add_on.service_id))
    return render_template('admin/add_on_form.html', form=form, add_on=add_on, title='Edit Add-on', active_page='services')


@bp.route('/add-ons/<int:add_on_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_add_on(add_on_id):
    add_on = AddOn.query.get_or_404(add_on_id)
    service_id = add_on.service_id
    db.session.delete(add_on)
    db.session.commit()
    flash('Add-on deleted successfully!', 'success')
    return redirect(url_for('admin.service_add_ons', service_id=service_id))


# ─────────────────────────────────────────────────────────────
# PROMOTIONS
# ─────────────────────────────────────────────────────────────
@bp.route('/promotions')
@login_required
@admin_required
def promotions():
    search = request.args.get('search', '').strip()
    q = Promotion.query.filter_by(is_archived=False)
    if search:
        q = q.filter(Promotion.code.ilike(f'%{search}%'))
    promotions = q.order_by(Promotion.end_date.desc()).all()
    return render_template('admin/promotions.html', promotions=promotions, search=search, active_page='promotions')


@bp.route('/promotions/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_promotion():
    form = PromotionForm()
    if form.validate_on_submit():
        promotion = Promotion(
            code=form.code.data.upper(),
            description=form.description.data,
            discount_type=form.discount_type.data,
            discount_value=form.discount_value.data,
            min_order_value=form.min_order_value.data or 0,
            max_discount_amount=form.max_discount_amount.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            usage_limit=form.usage_limit.data,
            is_stackable=form.is_stackable.data,
            is_active=form.is_active.data
        )
        db.session.add(promotion)
        db.session.flush()
        log_action('create', 'promotion', promotion.id, {'code': promotion.code})
        db.session.commit()
        flash('Promotion added successfully!', 'success')
        return redirect(url_for('admin.promotions'))
    return render_template('admin/promotion_form.html', form=form, title='Add Promotion', active_page='promotions')


@bp.route('/promotions/<int:promotion_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_promotion(promotion_id):
    promotion = Promotion.query.get_or_404(promotion_id)
    form = PromotionForm(obj=promotion)
    if form.validate_on_submit():
        promotion.code = form.code.data.upper()
        promotion.description = form.description.data
        promotion.discount_type = form.discount_type.data
        promotion.discount_value = form.discount_value.data
        promotion.min_order_value = form.min_order_value.data or 0
        promotion.max_discount_amount = form.max_discount_amount.data
        promotion.start_date = form.start_date.data
        promotion.end_date = form.end_date.data
        promotion.usage_limit = form.usage_limit.data
        promotion.is_stackable = form.is_stackable.data
        promotion.is_active = form.is_active.data
        log_action('update', 'promotion', promotion_id, {'code': promotion.code})
        db.session.commit()
        flash('Promotion updated successfully!', 'success')
        return redirect(url_for('admin.promotions'))
    return render_template('admin/promotion_form.html', form=form, promotion=promotion, title='Edit Promotion', active_page='promotions')


@bp.route('/promotions/<int:promotion_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_promotion(promotion_id):
    promotion = Promotion.query.get_or_404(promotion_id)
    promotion.is_active = not promotion.is_active
    log_action('toggle', 'promotion', promotion_id, {'is_active': promotion.is_active})
    db.session.commit()
    status = 'activated' if promotion.is_active else 'deactivated'
    flash(f'Promotion {status} successfully!', 'success')
    return redirect(url_for('admin.promotions'))


@bp.route('/promotions/<int:promotion_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive_promotion(promotion_id):
    promotion = Promotion.query.get_or_404(promotion_id)
    promotion.is_archived = True
    promotion.is_active = False
    log_action('archive', 'promotion', promotion_id, {'code': promotion.code})
    db.session.commit()
    flash('Promotion archived successfully!', 'success')
    return redirect(url_for('admin.promotions'))


@bp.route('/promotions/<int:promotion_id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_promotion(promotion_id):
    promotion = Promotion.query.get_or_404(promotion_id)
    promotion.is_archived = False
    log_action('restore', 'promotion', promotion_id, {'code': promotion.code})
    db.session.commit()
    flash('Promotion restored successfully!', 'success')
    return redirect(url_for('admin.archived'))


@bp.route('/promotions/<int:promotion_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_promotion(promotion_id):
    promotion = Promotion.query.get_or_404(promotion_id)
    if not promotion.is_archived:
        flash('Promotion must be archived before deletion.', 'error')
        return redirect(url_for('admin.promotions'))
    log_action('delete', 'promotion', promotion_id, {'code': promotion.code})
    db.session.delete(promotion)
    db.session.commit()
    flash('Promotion permanently deleted.', 'success')
    return redirect(url_for('admin.archived'))


# ─────────────────────────────────────────────────────────────
# BOOKINGS
# ─────────────────────────────────────────────────────────────
@bp.route('/bookings')
@login_required
@admin_required
def bookings():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    sort_by = request.args.get('sort', 'created_desc')

    q = Booking.query
    if search:
        q = q.join(CustomerProfile).filter(
            db.or_(
                CustomerProfile.first_name.ilike(f'%{search}%'),
                CustomerProfile.last_name.ilike(f'%{search}%'),
                Booking.id == int(search) if search.isdigit() else False
            )
        )
    if status_filter:
        q = q.filter(Booking.status == status_filter)

    if sort_by == 'date_asc':
        q = q.order_by(Booking.scheduled_date.asc(), Booking.scheduled_time.asc())
    elif sort_by == 'date_desc':
        q = q.order_by(Booking.scheduled_date.desc(), Booking.scheduled_time.desc())
    elif sort_by == 'price_asc':
        q = q.order_by(Booking.total_amount.asc())
    elif sort_by == 'price_desc':
        q = q.order_by(Booking.total_amount.desc())
    else:
        q = q.order_by(Booking.created_at.desc())

    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    bookings = pagination.items

    statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
    return render_template('admin/bookings.html',
                         bookings=bookings,
                         pagination=pagination,
                         search=search,
                         status_filter=status_filter,
                         sort_by=sort_by,
                         statuses=statuses,
                         active_page='bookings')


@bp.route('/bookings/<int:booking_id>')
@login_required
@admin_required
def booking_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    cleaners = Cleaner.query.order_by(Cleaner.first_name).all()
    return render_template('admin/booking_detail.html', booking=booking, cleaners=cleaners, active_page='bookings')


@bp.route('/bookings/<int:booking_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    valid_statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
    if new_status in valid_statuses:
        old_status = booking.status
        booking.status = new_status
        log_action('update_status', 'booking', booking_id, {'old': old_status, 'new': new_status})
        db.session.commit()
        flash(f'Booking status updated to {new_status.replace("_", " ")}.', 'success')
    else:
        flash('Invalid status.', 'error')
    return redirect(url_for('admin.booking_detail', booking_id=booking_id))


@bp.route('/bookings/<int:booking_id>/assign-cleaner', methods=['POST'])
@login_required
@admin_required
def assign_cleaner(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    cleaner_id = request.form.get('cleaner_id', type=int)

    if cleaner_id:
        cleaner = Cleaner.query.get_or_404(cleaner_id)
        if not cleaner.is_available:
            flash(f'Cleaner {cleaner.first_name} {cleaner.last_name} is currently marked as unavailable.', 'error')
            return redirect(url_for('admin.booking_detail', booking_id=booking_id))

        conflict = Booking.query.filter_by(
            cleaner_id=cleaner.id,
            scheduled_date=booking.scheduled_date,
            scheduled_time=booking.scheduled_time
        ).filter(Booking.id != booking.id, Booking.status.notin_(['cancelled'])).first()
        if conflict:
            flash(f'Cleaner {cleaner.first_name} is already assigned to Booking #{conflict.id} on {booking.scheduled_date} at {booking.scheduled_time.strftime("%I:%M %p")}.', 'error')
            return redirect(url_for('admin.booking_detail', booking_id=booking_id))

        booking.cleaner_id = cleaner.id
        log_action('assign_cleaner', 'booking', booking_id,
                   {'cleaner': f'{cleaner.first_name} {cleaner.last_name}'})
        db.session.commit()
        flash(f'Cleaner {cleaner.first_name} {cleaner.last_name} assigned.', 'success')
    else:
        booking.cleaner_id = None
        log_action('unassign_cleaner', 'booking', booking_id)
        db.session.commit()
        flash('Cleaner unassigned.', 'info')

    return redirect(url_for('admin.booking_detail', booking_id=booking_id))


@bp.route('/bookings/<int:booking_id>/reschedule', methods=['POST'])
@login_required
@admin_required
def reschedule_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_date_str = request.form.get('scheduled_date')
    new_time_str = request.form.get('scheduled_time')
    try:
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
        new_time = datetime.strptime(new_time_str, '%H:%M').time()
    except (ValueError, TypeError):
        flash('Invalid date or time format.', 'error')
        return redirect(url_for('admin.booking_detail', booking_id=booking_id))

    if new_date < date.today():
        flash('Rescheduled date cannot be in the past.', 'error')
        return redirect(url_for('admin.booking_detail', booking_id=booking_id))

    conflict = Booking.query.filter_by(
        scheduled_date=new_date,
        scheduled_time=new_time
    ).filter(Booking.id != booking_id, Booking.status.notin_(['cancelled'])).first()
    if conflict:
        flash('The selected appointment slot is already booked. Please choose a different date or time.', 'error')
        return redirect(url_for('admin.booking_detail', booking_id=booking_id))

    old_date = booking.scheduled_date
    old_time = booking.scheduled_time
    booking.scheduled_date = new_date
    booking.scheduled_time = new_time
    if booking.status not in ['cancelled']:
        booking.status = 'pending'
        booking.cleaner_id = None
    log_action('reschedule', 'booking', booking_id, {'old_date': str(old_date), 'new_date': str(new_date)})
    db.session.commit()
    flash('Booking rescheduled successfully.', 'success')
    return redirect(url_for('admin.booking_detail', booking_id=booking_id))


# ─────────────────────────────────────────────────────────────
# CUSTOMERS
# ─────────────────────────────────────────────────────────────
@bp.route('/customers')
@login_required
@admin_required
def customers():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    search = request.args.get('search', '').strip()

    q = CustomerProfile.query.filter_by(is_archived=False)
    if search:
        q = q.join(User).filter(
            db.or_(
                CustomerProfile.first_name.ilike(f'%{search}%'),
                CustomerProfile.last_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    q = q.order_by(CustomerProfile.created_at.desc())
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    customers = pagination.items

    # Compute total spending per customer
    customer_spending = {}
    for c in customers:
        total = db.session.query(db.func.sum(Booking.total_amount)).filter_by(
            customer_id=c.id, payment_status='paid'
        ).scalar() or Decimal('0')
        customer_spending[c.id] = total

    return render_template('admin/customers.html',
                         customers=customers,
                         pagination=pagination,
                         search=search,
                         customer_spending=customer_spending,
                         active_page='customers')


@bp.route('/customers/<int:customer_id>')
@login_required
@admin_required
def customer_detail(customer_id):
    customer = CustomerProfile.query.get_or_404(customer_id)
    total_spending = db.session.query(db.func.sum(Booking.total_amount)).filter_by(
        customer_id=customer.id, payment_status='paid'
    ).scalar() or Decimal('0')
    return render_template('admin/customer_detail.html', customer=customer,
                         total_spending=total_spending, active_page='customers')


@bp.route('/customers/<int:customer_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_customer_active(customer_id):
    customer = CustomerProfile.query.get_or_404(customer_id)
    customer.user.is_active = not customer.user.is_active
    status = 'activated' if customer.user.is_active else 'deactivated'
    log_action(f'customer_{status}', 'user', customer.user_id)
    db.session.commit()
    flash(f'Customer account {status}.', 'success')
    return redirect(url_for('admin.customer_detail', customer_id=customer_id))


@bp.route('/customers/<int:customer_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive_customer(customer_id):
    customer = CustomerProfile.query.get_or_404(customer_id)
    customer.is_archived = True
    customer.user.is_active = False
    log_action('archive', 'customer', customer_id, {'name': f'{customer.first_name} {customer.last_name}'})
    db.session.commit()
    flash('Customer archived successfully!', 'success')
    return redirect(url_for('admin.customers'))


@bp.route('/customers/<int:customer_id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_customer(customer_id):
    customer = CustomerProfile.query.get_or_404(customer_id)
    customer.is_archived = False
    customer.user.is_active = True
    log_action('restore', 'customer', customer_id, {'name': f'{customer.first_name} {customer.last_name}'})
    db.session.commit()
    flash('Customer restored successfully!', 'success')
    return redirect(url_for('admin.archived'))


# ─────────────────────────────────────────────────────────────
# STAFF / CLEANERS
# ─────────────────────────────────────────────────────────────
@bp.route('/cleaners')
@login_required
@admin_required
def cleaners():
    cleaners = Cleaner.query.order_by(Cleaner.first_name).all()
    return render_template('admin/cleaners.html', cleaners=cleaners, active_page='cleaners')


@bp.route('/cleaners/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_cleaner():
    from app.forms import RegistrationForm
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, role='cleaner')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        cleaner = Cleaner(
            user_id=user.id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            is_available=True
        )
        db.session.add(cleaner)
        db.session.flush()
        log_action('create', 'cleaner', cleaner.id, {'name': f'{cleaner.first_name} {cleaner.last_name}'})
        db.session.commit()
        flash('Cleaner added successfully!', 'success')
        return redirect(url_for('admin.cleaners'))
    return render_template('admin/cleaner_form.html', form=form, title='Add Cleaner', active_page='cleaners')


@bp.route('/cleaners/<int:cleaner_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_cleaner(cleaner_id):
    cleaner = Cleaner.query.get_or_404(cleaner_id)
    form = CleanerEditForm(obj=cleaner)
    if form.validate_on_submit():
        cleaner.first_name = form.first_name.data
        cleaner.last_name = form.last_name.data
        cleaner.phone = form.phone.data
        cleaner.is_available = form.is_available.data
        log_action('update', 'cleaner', cleaner_id, {'name': f'{cleaner.first_name} {cleaner.last_name}'})
        db.session.commit()
        flash('Cleaner updated successfully!', 'success')
        return redirect(url_for('admin.cleaners'))
    assigned = Booking.query.filter_by(cleaner_id=cleaner.id).filter(
        Booking.status.notin_(['cancelled'])
    ).order_by(Booking.scheduled_date.desc()).all()
    return render_template('admin/cleaner_form.html', form=form, cleaner=cleaner,
                         assigned=assigned, title='Edit Cleaner', active_page='cleaners')


@bp.route('/cleaners/<int:cleaner_id>/toggle-availability', methods=['POST'])
@login_required
@admin_required
def toggle_cleaner_availability(cleaner_id):
    cleaner = Cleaner.query.get_or_404(cleaner_id)
    cleaner.is_available = not cleaner.is_available
    log_action('toggle_availability', 'cleaner', cleaner_id, {'is_available': cleaner.is_available})
    db.session.commit()
    status = 'available' if cleaner.is_available else 'unavailable'
    flash(f'Cleaner marked as {status}.', 'success')
    return redirect(url_for('admin.cleaners'))


# ─────────────────────────────────────────────────────────────
# SALES & PAYMENTS
# ─────────────────────────────────────────────────────────────
@bp.route('/sales')
@login_required
@admin_required
def sales():
    today = date.today()
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('payment_status', '')
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')

    q = Payment.query.join(Booking)
    if search:
        q = q.filter(
            db.or_(
                Booking.id == int(search) if search.isdigit() else False,
                Payment.payment_reference.ilike(f'%{search}%')
            )
        )
    if status_filter:
        q = q.filter(Payment.status == status_filter)
    if start_date_str:
        try:
            sd = datetime.strptime(start_date_str, '%Y-%m-%d')
            q = q.filter(Payment.paid_at >= sd)
        except ValueError:
            pass
    if end_date_str:
        try:
            ed = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            q = q.filter(Payment.paid_at < ed)
        except ValueError:
            pass

    q = q.order_by(Payment.id.desc())
    payments = q.all()

    total_revenue = sum(p.amount for p in payments if p.status == 'completed')
    pending_payments = sum(p.amount for p in payments if p.status == 'pending')
    completed_count = len([p for p in payments if p.status == 'completed'])
    total_count = len(payments)

    # Payment method breakdown
    method_breakdown = {}
    for p in payments:
        if p.status == 'completed':
            method_breakdown[p.payment_method] = method_breakdown.get(p.payment_method, Decimal('0')) + p.amount

    return render_template('admin/sales.html',
                         payments=payments,
                         total_revenue=total_revenue,
                         pending_payments=pending_payments,
                         completed_count=completed_count,
                         total_count=total_count,
                         method_breakdown=method_breakdown,
                         search=search,
                         status_filter=status_filter,
                         start_date=start_date_str,
                         end_date=end_date_str,
                         active_page='sales')


# ─────────────────────────────────────────────────────────────
# ARCHIVED RECORDS
# ─────────────────────────────────────────────────────────────
@bp.route('/archived')
@login_required
@admin_required
def archived():
    tab = request.args.get('tab', 'services')
    archived_services = Service.query.filter_by(is_archived=True).all()
    archived_promotions = Promotion.query.filter_by(is_archived=True).all()
    archived_customers = CustomerProfile.query.filter_by(is_archived=True).all()
    archived_bookings = Booking.query.filter_by(status='cancelled').all()
    return render_template('admin/archived.html',
                         tab=tab,
                         archived_services=archived_services,
                         archived_promotions=archived_promotions,
                         archived_customers=archived_customers,
                         archived_bookings=archived_bookings,
                         active_page='archived')


# ─────────────────────────────────────────────────────────────
# AUDIT LOGS
# ─────────────────────────────────────────────────────────────
@bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 25
    search = request.args.get('search', '').strip()
    q = AuditLog.query
    if search:
        q = q.join(User).filter(
            db.or_(
                AuditLog.action.ilike(f'%{search}%'),
                AuditLog.entity_type.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    q = q.order_by(AuditLog.created_at.desc())
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items
    return render_template('admin/audit_logs.html', logs=logs, pagination=pagination,
                         search=search, active_page='audit_logs')


# ─────────────────────────────────────────────────────────────
# INQUIRIES
# ─────────────────────────────────────────────────────────────
@bp.route('/inquiries')
@login_required
@admin_required
def inquiries():
    inquiries_list = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template('admin/inquiries.html', inquiries=inquiries_list, active_page='inquiries')


@bp.route('/inquiries/<int:inquiry_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_inquiry_status(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    new_status = request.form.get('status')
    if new_status in ['new', 'in_progress', 'resolved']:
        inquiry.status = new_status
        log_action('update_status', 'inquiry', inquiry_id, {'status': new_status})
        db.session.commit()
        flash(f'Inquiry status updated to {new_status}.', 'success')
    else:
        flash('Invalid status.', 'error')
    return redirect(url_for('admin.inquiries'))


# ─────────────────────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────────────────────
@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    settings_form = SettingsForm()
    profile_form = AdminProfileForm(obj=current_user)
    password_form = PasswordChangeForm()

    # Load existing settings
    settings_map = {s.key: s.value for s in BusinessSettings.query.all()}
    if request.method == 'GET':
        settings_form.business_name.data = settings_map.get('business_name', '')
        settings_form.contact_email.data = settings_map.get('contact_email', '')
        settings_form.contact_phone.data = settings_map.get('contact_phone', '')
        settings_form.address.data = settings_map.get('address', '')
        settings_form.operating_hours.data = settings_map.get('operating_hours', '')
        settings_form.service_areas.data = settings_map.get('service_areas', '')
        settings_form.booking_lead_time_hours.data = int(settings_map.get('booking_lead_time_hours', 2))
        settings_form.max_advance_days.data = int(settings_map.get('max_advance_days', 30))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'settings' and settings_form.validate():
            settings_to_save = {
                'business_name': settings_form.business_name.data,
                'contact_email': settings_form.contact_email.data,
                'contact_phone': settings_form.contact_phone.data,
                'address': settings_form.address.data,
                'operating_hours': settings_form.operating_hours.data,
                'service_areas': settings_form.service_areas.data,
                'booking_lead_time_hours': str(settings_form.booking_lead_time_hours.data),
                'max_advance_days': str(settings_form.max_advance_days.data),
            }
            for key, value in settings_to_save.items():
                setting = BusinessSettings.query.filter_by(key=key).first()
                if setting:
                    setting.value = value
                else:
                    db.session.add(BusinessSettings(key=key, value=value))
            log_action('update', 'settings')
            db.session.commit()
            flash('Business settings saved successfully!', 'success')
            return redirect(url_for('admin.settings'))

        elif action == 'profile' and profile_form.validate():
            existing = User.query.filter_by(email=profile_form.email.data).first()
            if existing and existing.id != current_user.id:
                flash('Email already in use.', 'error')
            else:
                current_user.email = profile_form.email.data
                log_action('update_profile', 'user', current_user.id)
                db.session.commit()
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('admin.settings'))

        elif action == 'password':
            if password_form.validate():
                if current_user.check_password(password_form.current_password.data):
                    current_user.set_password(password_form.new_password.data)
                    log_action('change_password', 'user', current_user.id)
                    db.session.commit()
                    flash('Password changed successfully!', 'success')
                    return redirect(url_for('admin.settings'))
                else:
                    flash('Current password is incorrect.', 'error')

    return render_template('admin/settings.html',
                         settings_form=settings_form,
                         profile_form=profile_form,
                         password_form=password_form,
                         active_page='settings')


# ─────────────────────────────────────────────────────────────
# REPORTS (kept for compatibility)
# ─────────────────────────────────────────────────────────────
@bp.route('/reports')
@login_required
@admin_required
def reports():
    from datetime import timedelta
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    bookings = Booking.query.filter(
        Booking.created_at >= start_date,
        Booking.created_at <= end_date
    ).all()
    total_revenue = sum([b.total_amount for b in bookings if b.payment_status == 'paid'])
    completed_bookings = len([b for b in bookings if b.status == 'completed'])
    cancelled_bookings = len([b for b in bookings if b.status == 'cancelled'])
    service_counts = {}
    for booking in bookings:
        for item in booking.items:
            if item.service_name:
                service_counts[item.service_name] = service_counts.get(item.service_name, 0) + 1
    return render_template('admin/reports.html',
                         start_date=start_date, end_date=end_date, bookings=bookings,
                         total_revenue=total_revenue, completed_bookings=completed_bookings,
                         cancelled_bookings=cancelled_bookings, service_counts=service_counts,
                         active_page='reports')

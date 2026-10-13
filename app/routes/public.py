from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from app import db
from app.models import Service, Promotion, Inquiry
from app.forms import ContactForm
from datetime import datetime, timezone

bp = Blueprint('public', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    services = Service.query.filter_by(is_active=True, is_archived=False).limit(3).all()
    now = datetime.now(timezone.utc)
    promotions = Promotion.query.filter_by(is_active=True).filter(
        Promotion.end_date >= now
    ).limit(3).all()
    return render_template('index.html', services=services, promotions=promotions)

@bp.route('/services')
def services():
    services = Service.query.filter_by(is_active=True, is_archived=False).order_by(Service.base_price).all()
    return render_template('public/services.html', services=services)

@bp.route('/services/<int:service_id>')
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    if not service.is_active or service.is_archived:
        flash('This service is not available.', 'error')
        return redirect(url_for('public.services'))
    return render_template('public/service_detail.html', service=service)

@bp.route('/promotions')
def promotions():
    now = datetime.now(timezone.utc)
    promotions = Promotion.query.filter_by(is_active=True).filter(
        Promotion.end_date >= now
    ).order_by(Promotion.end_date).all()
    return render_template('public/promotions.html', promotions=promotions)

@bp.route('/about')
def about():
    return render_template('public/about.html')

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        inquiry = Inquiry(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(inquiry)
        db.session.commit()
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('public.contact'))
    return render_template('public/contact.html', form=form)

@bp.route('/faq')
def faq():
    return render_template('public/faq.html')

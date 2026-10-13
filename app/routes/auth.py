import secrets
from datetime import datetime, timezone, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User, CustomerProfile, PasswordResetToken
from app.forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                return _redirect_by_role(user)
            return redirect(next_page)
        flash('Invalid email or password.', 'error')

    return render_template('login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data.lower().strip(), role='customer')
        user.set_password(form.password.data)

        profile = CustomerProfile(
            user=user,
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            phone=form.phone.data,
        )

        db.session.add(user)
        db.session.add(profile)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('public.index'))


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = ForgotPasswordForm()
    reset_token_value = None  # shown in dev instead of emailing

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            # Invalidate old tokens
            PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({'used': True})

            token_value = secrets.token_urlsafe(32)
            token = PasswordResetToken(
                user_id=user.id,
                token=token_value,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
            db.session.add(token)
            db.session.commit()

            import os
            from flask import current_app
            is_dev = bool(current_app.config.get('TESTING') or current_app.debug or current_app.config.get('ENV') == 'development' or os.getenv('FLASK_ENV') == 'development')
            if is_dev:
                reset_token_value = token_value
                flash(
                    'Password reset link generated. In production this would be emailed. '
                    'For development/testing, use the link shown below.',
                    'info',
                )
            else:
                flash(
                    'If that email is registered you will receive a reset link shortly.',
                    'info',
                )
        else:
            # Don't reveal whether email exists
            flash(
                'If that email is registered you will receive a reset link shortly.',
                'info',
            )

    return render_template('auth/forgot_password.html', form=form, reset_token=reset_token_value)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    record = PasswordResetToken.query.filter_by(token=token, used=False).first()
    now = datetime.now(timezone.utc)

    if not record or record.expires_at.replace(tzinfo=timezone.utc) < now:
        flash('This reset link is invalid or has expired.', 'error')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        record.user.set_password(form.password.data)
        record.used = True
        db.session.commit()
        flash('Password updated successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)


# ── helpers ──────────────────────────────────────────────────────────────────

def _redirect_by_role(user):
    if user.role == 'customer':
        return redirect(url_for('customer.dashboard'))
    if user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('public.index'))

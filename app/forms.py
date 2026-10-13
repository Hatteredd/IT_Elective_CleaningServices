from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, TimeField, IntegerField, DecimalField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from app.models import User, Promotion, Service

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])

class AddressForm(FlaskForm):
    label = StringField('Label (e.g., Home, Office)', validators=[Optional(), Length(max=50)])
    street = StringField('Street Address', validators=[DataRequired(), Length(max=255)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    province = StringField('Province', validators=[DataRequired(), Length(max=100)])
    postal_code = StringField('Postal Code', validators=[Optional(), Length(max=20)])
    is_default = SelectField('Set as Default', choices=[('False', 'No'), ('True', 'Yes')], default='False')

class ServiceForm(FlaskForm):
    name = StringField('Service Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    base_price = DecimalField('Base Price (₱)', validators=[DataRequired(), NumberRange(min=0)])
    discounted_price = DecimalField('Discounted Price (₱)', validators=[Optional(), NumberRange(min=0)])
    duration_minutes = IntegerField('Duration (minutes)', validators=[DataRequired(), NumberRange(min=1)])
    image_url = StringField('Image URL', validators=[Optional(), Length(max=500)])
    is_active = BooleanField('Active')

class AddOnForm(FlaskForm):
    name = StringField('Add-on Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    price = DecimalField('Price (₱)', validators=[DataRequired(), NumberRange(min=0)])
    is_active = BooleanField('Active')

class PromotionForm(FlaskForm):
    code = StringField('Promo Code', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional()])
    discount_type = SelectField('Discount Type', choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')])
    discount_value = DecimalField('Discount Value', validators=[DataRequired(), NumberRange(min=0)])
    min_order_value = DecimalField('Minimum Order Value (₱)', validators=[Optional(), NumberRange(min=0)], default=0)
    max_discount_amount = DecimalField('Maximum Discount (₱)', validators=[Optional(), NumberRange(min=0)])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    usage_limit = IntegerField('Usage Limit (blank for unlimited)', validators=[Optional(), NumberRange(min=1)])
    is_stackable = BooleanField('Allow Stacking')
    is_active = BooleanField('Active')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired()])

class BookingForm(FlaskForm):
    service_id = SelectField('Service', coerce=int, validators=[DataRequired()])
    date = DateField('Preferred Date', validators=[DataRequired()])
    time = TimeField('Preferred Time', validators=[DataRequired()])
    address_id = SelectField('Address', coerce=int, validators=[DataRequired()])
    add_ons = SelectMultipleField('Add-ons', coerce=int)
    promo_code = StringField('Promo Code', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Special Instructions', validators=[Optional()])

    def validate_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError('Booking date cannot be in the past.')

class PromoCodeForm(FlaskForm):
    code = StringField('Promo Code', validators=[DataRequired(), Length(max=50)])

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[('5', '5 - Excellent'), ('4', '4 - Good'), ('3', '3 - Average'), ('2', '2 - Fair'), ('1', '1 - Poor')], validators=[DataRequired()])
    comment = TextAreaField('Your Review', validators=[Optional()])


class RescheduleForm(FlaskForm):
    date = DateField('New Date', validators=[DataRequired()])
    time = TimeField('New Time', validators=[DataRequired()])

    def validate_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError('Rescheduled date cannot be in the past.')


class SettingsForm(FlaskForm):
    business_name = StringField('Business Name', validators=[DataRequired(), Length(max=200)])
    contact_email = StringField('Contact Email', validators=[DataRequired(), Email()])
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=50)])
    address = StringField('Business Address', validators=[Optional(), Length(max=300)])
    operating_hours = StringField('Operating Hours', validators=[Optional(), Length(max=200)])
    service_areas = TextAreaField('Service Coverage Areas', validators=[Optional()])
    booking_lead_time_hours = IntegerField('Booking Lead Time (hours)', validators=[Optional(), NumberRange(min=0)], default=2)
    max_advance_days = IntegerField('Max Advance Booking Days', validators=[Optional(), NumberRange(min=1)], default=30)


class AdminProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])


class CleanerEditForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    is_available = BooleanField('Available')

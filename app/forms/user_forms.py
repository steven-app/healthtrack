from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, DateField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from app.models.user import User
from flask_login import current_user

class ProfileForm(FlaskForm):
    """Form for user profile editing"""
    first_name = StringField('First Name', validators=[Length(max=64)])
    last_name = StringField('Last Name', validators=[Length(max=64)])
    gender = SelectField('Gender', choices=[
        ('', 'Select Gender'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say')
    ], validators=[Optional()])
    birth_date = DateField('Birth Date', format='%Y-%m-%d', validators=[Optional()])
    height = FloatField('Height (cm)', validators=[Optional()])
    weight = FloatField('Weight (kg)', validators=[Optional()])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Changes')

class ChangePasswordForm(FlaskForm):
    """Form for changing user password"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')
    
    def validate_current_password(self, field):
        """Validate current password"""
        if not current_user.check_password(field.data):
            raise ValidationError('Current password is incorrect')

class AccountSettingsForm(FlaskForm):
    """Form for account settings"""
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    confirm_email = BooleanField('I confirm that I want to update my email address')
    
    delete_account = BooleanField('I understand that deleting my account is permanent and cannot be undone')
    delete_confirmation = StringField('Type "DELETE" to confirm account deletion', validators=[Optional()])
    
    submit_email = SubmitField('Update Email')
    submit_delete = SubmitField('Delete Account')
    
    def validate_email(self, field):
        """Validate email is not already taken"""
        if field.data != current_user.email:
            user = User.query.filter_by(email=field.data).first()
            if user:
                raise ValidationError('Email already registered. Please use a different one.')
    
    def validate_delete_confirmation(self, field):
        """Validate deletion confirmation"""
        if self.delete_account.data and field.data != "DELETE":
            raise ValidationError('Please type "DELETE" to confirm account deletion')

class ExportConsentForm(FlaskForm):
    """Form for data export consent"""
    confirm_export = BooleanField('I consent to exporting my personal health data', validators=[DataRequired(message='You must consent to export your data')])
    submit = SubmitField('Export Data') 
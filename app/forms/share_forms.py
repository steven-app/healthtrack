from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField, DateField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError, Optional
from datetime import datetime, date, timedelta

class CreateShareLinkForm(FlaskForm):
    """Form for creating a new share link"""
    name = StringField('Share Name', validators=[
        DataRequired(),
        Length(min=3, max=100, message='Name must be between 3 and 100 characters')
    ])
    
    template_type = SelectField('Template Type', choices=[
        ('social', 'Social (For friends & family)'),
        ('medical', 'Medical (For healthcare providers)')
    ], validators=[DataRequired()])
    
    date_range_start = DateField('Start Date', format='%Y-%m-%d', 
                                default=lambda: date.today() - timedelta(days=30),
                                validators=[DataRequired()])
    
    date_range_end = DateField('End Date', format='%Y-%m-%d',
                              default=date.today,
                              validators=[DataRequired()])
    
    never_expire = BooleanField('Never Expire', default=False)
    
    expiry_days = IntegerField('Link Expiry (Days)', 
                              default=30,
                              validators=[
                                  DataRequired(),
                                  NumberRange(min=1, max=365, message='Expiry must be between 1 and 365 days')
                              ])
    
    # Password protection
    password_protect = BooleanField('Password Protect This Link', default=False)
    one_time_password = BooleanField('One-time Password (expires after one use)', default=False)
    password = PasswordField('Password', validators=[Optional(), Length(min=6, max=50)])
    
    # Privacy settings
    show_weight = BooleanField('Include Weight Data', default=True)
    show_heart_rate = BooleanField('Include Heart Rate Data', default=True)
    show_activity = BooleanField('Include Activity Data', default=True)
    show_sleep = BooleanField('Include Sleep Data', default=True)
    show_goals = BooleanField('Include Goals', default=True)
    show_achievements = BooleanField('Include Achievements', default=True)
    
    submit = SubmitField('Create Share Link')
    
    def validate_date_range_end(self, field):
        if field.data < self.date_range_start.data:
            raise ValidationError("End date must be after the start date")
        
        if (field.data - self.date_range_start.data).days > 365:
            raise ValidationError("Date range cannot exceed 1 year")
    
    def validate_expiry_days(self, field):
        if not self.never_expire.data and field.data < 1:
            raise ValidationError("Expiry must be at least 1 day if not set to never expire")
    
    def validate_password(self, field):
        if self.password_protect.data and not field.data:
            raise ValidationError("Password is required when password protection is enabled")


class ManageShareLinkForm(FlaskForm):
    """Form for managing existing share links"""
    name = StringField('Share Name', validators=[
        DataRequired(),
        Length(min=3, max=100, message='Name must be between 3 and 100 characters')
    ])
    
    never_expire = BooleanField('Never Expire', default=False)
    
    expiry_days = IntegerField('Extend Expiry By (Days)', 
                              default=30,
                              validators=[
                                  DataRequired(),
                                  NumberRange(min=1, max=365, message='Extension must be between 1 and 365 days')
                              ])
    
    # Password protection
    password_protect = BooleanField('Password Protect This Link')
    change_password = BooleanField('Change Password')
    one_time_password = BooleanField('One-time Password (expires after one use)', default=False)
    password = PasswordField('New Password', validators=[Optional(), Length(min=6, max=50)])
    
    # Privacy settings
    show_weight = BooleanField('Include Weight Data')
    show_heart_rate = BooleanField('Include Heart Rate Data')
    show_activity = BooleanField('Include Activity Data')
    show_sleep = BooleanField('Include Sleep Data')
    show_goals = BooleanField('Include Goals')
    show_achievements = BooleanField('Include Achievements')
    
    submit = SubmitField('Update Share Link')
    delete = SubmitField('Delete Share Link')
    
    def validate_expiry_days(self, field):
        if not self.never_expire.data and field.data < 1:
            raise ValidationError("Extension must be at least 1 day if not set to never expire")
    
    def validate_password(self, field):
        if self.password_protect.data and self.change_password.data and not field.data:
            raise ValidationError("Password is required when changing password") 
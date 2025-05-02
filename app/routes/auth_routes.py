from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db
from datetime import datetime
from app.forms.auth_forms import ResetPasswordRequestForm, ResetPasswordForm
from app.utils.email_utils import send_password_reset_email, send_email
from flask import current_app

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.get_dashboard_data'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.update_last_login()
            flash('Login successful!', 'success')
            
            # Redirect to the page the user was trying to access or to dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.get_dashboard_data'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.get_dashboard_data'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Simple validation
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('auth/register.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html')
        
        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('auth/register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            created_at=datetime.utcnow()
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """Handle password reset requests"""
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.get_dashboard_data'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        email = form.email.data.strip()
        current_app.logger.info(f"Password reset requested for email: {email}")
        
        user = User.query.filter_by(email=email).first()
        if user:
            current_app.logger.info(f"User found with ID: {user.id}, sending reset email")
            try:
                send_password_reset_email(user)
                current_app.logger.info(f"Password reset email sent to user {user.id}")
                flash('Check your email for instructions to reset your password.', 'info')
            except Exception as e:
                current_app.logger.error(f"Failed to send password reset email: {str(e)}")
                flash('An error occurred while sending the password reset email. Please try again later.', 'danger')
        else:
            # Log that no user was found but still show the same message to prevent user enumeration
            current_app.logger.warning(f"No user found with email: {email}")
            flash('Check your email for instructions to reset your password.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Verify token and handle password reset form"""
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.get_dashboard_data'))
    
    # Verify token and get user
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.reset_password_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset successfully.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, token=token)

# ... other auth routes like password reset etc. ...
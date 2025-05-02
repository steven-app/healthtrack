from flask import Blueprint, redirect, url_for, render_template
from flask_login import current_user

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.get_dashboard_data'))
    return redirect(url_for('auth.login')) 
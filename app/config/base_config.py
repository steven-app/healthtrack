import os
from datetime import timedelta

def init_base_config(app):
    """
    Initialize base configuration for the application
    
    This sets up core Flask settings, security settings, and other
    fundamental configurations.
    """
    # Basic Flask config
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret')
    
    # Base URL for external links - will be determined dynamically when possible
    app.config['BASE_URL'] = os.environ.get('BASE_URL', None)
    
    # Security settings
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    app.config['REMEMBER_COOKIE_SECURE'] = os.environ.get('REMEMBER_COOKIE_SECURE', 'False').lower() == 'true'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    
    # CSRF protection
    app.config['WTF_CSRF_ENABLED'] = True
    
    # Bootstrap configuration
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    
    # Development/Debug settings - override in production
    if app.debug:
        app.config['SESSION_COOKIE_SECURE'] = False
        app.config['REMEMBER_COOKIE_SECURE'] = False
    
    # Add a request hook to set BASE_URL dynamically if not set
    @app.before_request
    def set_dynamic_base_url():
        from flask import request, current_app
        if not current_app.config.get('BASE_URL'):
            current_app.config['BASE_URL'] = f"{request.scheme}://{request.host}"
    
    return app 
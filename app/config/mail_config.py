import os

def init_mail_config(app):
    """
    Initialize mail configuration for the application
    
    This function sets up all the mail-related configuration options.
    Values are loaded from environment variables with fallbacks to defaults.
    """
    # Basic mail server settings
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'sandbox.smtp.mailtrap.io')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 2525))
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '1907efbe7055e2')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'e7daa1a61f2ff8')
    
    # Connection security
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    
    # Sender identity
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@healthtrack.com')
    
    # Additional settings
    app.config['MAIL_MAX_EMAILS'] = int(os.environ.get('MAIL_MAX_EMAILS', 100))  # Max emails to send in a single connection
    app.config['MAIL_ASCII_ATTACHMENTS'] = os.environ.get('MAIL_ASCII_ATTACHMENTS', 'False').lower() == 'true'
    
    # Enable debug mode when app is in debug mode
    if app.debug:
        app.config['MAIL_DEBUG'] = True
        
    return app 
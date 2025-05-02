import os
from datetime import timedelta

def init_cache_session_config(app):
    """
    Initialize cache and session configuration for the application
    
    This sets up caching and session handling settings.
    """
    # Caching configuration
    app.config['CACHE_TYPE'] = os.environ.get('CACHE_TYPE', 'simple')
    app.config['CACHE_DEFAULT_TIMEOUT'] = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))  # Default 5 minutes
    
    # Session configuration
    app.config['SESSION_TYPE'] = os.environ.get('SESSION_TYPE', 'filesystem')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=int(os.environ.get('SESSION_LIFETIME_DAYS', 7)))
    app.config['SESSION_USE_SIGNER'] = os.environ.get('SESSION_USE_SIGNER', 'True').lower() == 'true'
    
    return app 
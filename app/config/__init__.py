"""
Configuration package for HealthTrack application.
This package contains various configuration modules for different parts of the application.
"""
import os

from .base_config import init_base_config
from .db_config import init_db_config
from .mail_config import init_mail_config
from .cache_session_config import init_cache_session_config
from .upload_config import init_upload_config
from .logging_config import init_logging_config

class Config:
    """Base configuration for the application."""
    DEBUG = False
    TESTING = False
    
    @classmethod
    def init_app(cls, app):
        """Initialize the application with all configuration modules"""
        # Apply all configuration modules
        app = init_base_config(app)
        app = init_db_config(app)
        app = init_mail_config(app)
        app = init_cache_session_config(app)
        app = init_upload_config(app)
        app = init_logging_config(app)
        
        return app

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost.localdomain'

class ProductionConfig(Config):
    """Production configuration."""
    pass

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 
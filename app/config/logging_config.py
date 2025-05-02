import os
import logging
from logging.handlers import RotatingFileHandler

def init_logging_config(app):
    """
    Initialize logging configuration for the application
    
    This sets up logging handlers, formatters, and log levels.
    """
    # Base configuration
    log_level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    
    # Default to just console logging
    app.logger.setLevel(log_level)
    
    # Production settings add file logging
    if not app.debug and not app.testing:
        # Ensure logs directory exists
        logs_dir = os.environ.get('LOG_DIR', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        log_file = os.environ.get('LOG_FILE', os.path.join(logs_dir, 'healthtrack.log'))
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=int(os.environ.get('LOG_MAX_BYTES', 10240)), 
            backupCount=int(os.environ.get('LOG_BACKUP_COUNT', 10))
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
        app.logger.info('HealthTrack startup')
    
    return app 
import os

def init_db_config(app):
    """
    Initialize database configuration for the application
    
    This sets up database connection and related settings.
    """
    # Base path for database files - use environment variable if available
    instance_path = os.environ.get('INSTANCE_PATH') or \
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'instance')
    
    # Ensure the directory exists
    os.makedirs(instance_path, exist_ok=True)
    
    app.config['INSTANCE_PATH'] = instance_path
    
    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(instance_path, 'healthtrack.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Testing override
    if app.config.get('TESTING', False):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    return app 
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_caching import Cache
from flask_mail import Mail
from app.config import config as config_mapping
from datetime import timedelta

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
cache = Cache()
mail = Mail()

def create_app(config_name=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Determine which configuration to use
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    # Load configuration
    config = config_mapping.get(config_name, config_mapping['default'])
    app.config.from_object(config)
    app = config.init_app(app)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    mail.init_app(app)
    
    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # User loader
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.main_routes import bp as main_bp
    from app.routes.auth_routes import bp as auth_bp
    from app.routes.upload_routes import bp as upload_bp
    from app.routes.dashboard_routes import bp as dashboard_bp
    from app.routes.activities_routes import bp as activities_bp
    from app.routes.heartbeats_routes import bp as heartbeats_bp
    from app.routes.sleep_routes import bp as sleep_bp
    from app.routes.weight_routes import bp as weight_bp
    from app.routes.user_routes import bp as user_bp
    from app.routes.goal_routes import bp as goal_bp
    from app.routes.achievement_routes import bp as achievement_bp
    from app.routes.share_routes import bp as share_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(activities_bp)
    app.register_blueprint(heartbeats_bp)
    app.register_blueprint(sleep_bp)
    app.register_blueprint(weight_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(goal_bp)
    app.register_blueprint(achievement_bp)
    app.register_blueprint(share_bp)
    
    # Register CLI commands
    from app.cli import register_commands
    register_commands(app)
    
    # Auto-create database tables if they don't exist (for SQLite on render)
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        with app.app_context():
            from app.models import User
            app.logger.info("Creating database tables if they don't exist...")
            db.create_all()
            app.logger.info("Database tables created successfully.")
            
            # Create admin user if not exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                app.logger.info("Creating admin user...")
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    is_admin=True
                )
                admin.set_password('admin@123')
                db.session.add(admin)
                db.session.commit()
                app.logger.info("Admin user created successfully.")
    
    return app
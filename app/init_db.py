import os
import sys
import argparse
import logging

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Weight, HeartRate, Activity, Sleep, Goal, Progress, Achievement, ImportLog

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_tables():
    """Create tables without dropping existing data"""
    app = create_app()
    with app.app_context():
        try:
            # Create all tables if they don't exist
            db.create_all()
            logger.info('Database tables created successfully')
            
            # Create admin user if not exists
            create_admin_user()
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise

def create_admin_user():
    """Create admin user if it doesn't exist"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        try:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin@123')
            db.session.add(admin)
            db.session.commit()
            logger.info('Admin user created successfully')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating admin user: {str(e)}")
            raise

def init_db(drop_tables=True):
    """Initialize database with options to drop tables or just create them"""
    app = create_app()
    with app.app_context():
        try:
            if drop_tables:
                # Drop all tables first
                db.drop_all()
                logger.info('All existing tables dropped')
            
            # Create all tables
            db.create_all()
            logger.info('Database tables created successfully')
            
            # Create admin user
            create_admin_user()
            
            logger.info('Database initialized successfully')
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

def ensure_instance_dir_exists():
    """Ensure the instance directory exists"""
    app = create_app()
    instance_path = app.config['INSTANCE_PATH']
    try:
        os.makedirs(instance_path, exist_ok=True)
        logger.info(f"Ensured instance directory exists at: {instance_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating instance directory: {str(e)}")
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Initialize or update the database')
    parser.add_argument('--create-only', action='store_true', help='Only create tables without dropping existing data')
    parser.add_argument('--ensure-dirs', action='store_true', help='Ensure instance directories exist')
    args = parser.parse_args()
    
    if args.ensure_dirs:
        ensure_instance_dir_exists()
    elif args.create_only:
        create_tables()
    else:
        init_db(drop_tables=True) 
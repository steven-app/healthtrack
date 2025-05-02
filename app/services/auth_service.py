from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app import db

class AuthService:
    @staticmethod
    def get_user_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def update_user(user, **kwargs):
        for key, value in kwargs.items():
            setattr(user, key, value)
        db.session.commit()
        return user

    @staticmethod
    def register_user(username, email, password_hash):
        """Register a new user"""
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            raise ValueError('Username already exists')
        if User.query.filter_by(email=email).first():
            raise ValueError('Email already exists')
        
        # Create new user
        user = User(
            username=username,
            email=email
        )
        user.set_password(password_hash)
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        return user

    @staticmethod
    def login_user(email, password):
        """Login a user"""
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def refresh_token(user_id):
        """Refresh user's access token"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError('User not found')
        return user.generate_token()
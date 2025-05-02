from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
import jwt
from time import time
from flask import current_app

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Personal information
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    gender = db.Column(db.String(20))
    birth_date = db.Column(db.Date)
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    
    # Privacy settings
    default_share_privacy = db.Column(db.String(20), default='overview')  # complete, overview, achievements
    default_share_modules = db.Column(db.Text, default='["dashboard","heartrate","activity","weight","sleep","goals","achievements"]')
    default_share_template = db.Column(db.String(20), default='social')  # medical, social
    default_share_expiry = db.Column(db.Integer, default=7)  # days
    
    # Relationships
    weights = db.relationship('Weight', backref='user', lazy='dynamic')
    heart_rates = db.relationship('HeartRate', backref='user', lazy='dynamic')
    activities = db.relationship('Activity', backref='user', lazy='dynamic')
    sleeps = db.relationship('Sleep', backref='user', lazy='dynamic')
    goals = db.relationship('Goal', backref='user', lazy='dynamic')
    progress = db.relationship('Progress', backref='user', lazy='dynamic')
    user_achievements = db.relationship('UserAchievement', backref='user', lazy='dynamic')
    import_logs = db.relationship('ImportLog', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check user password"""
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=3600):
        """Generate password reset token, expires in 1 hour by default"""
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        """Verify password reset token and return user"""
        try:
            id = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )['reset_password']
        except:
            return None
        return User.query.get(id)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'gender': self.gender,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'height': self.height,
            'weight': self.weight,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'default_share_privacy': self.default_share_privacy,
            'default_share_modules': self.default_share_modules,
            'default_share_template': self.default_share_template,
            'default_share_expiry': self.default_share_expiry
        }
        
    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
        
    def export_data(self):
        """Export user data as a dictionary"""
        data = {
            'profile': self.to_dict(),
            'weights': [w.to_dict() for w in self.weights],
            'heart_rates': [hr.to_dict() for hr in self.heart_rates],
            'activities': [a.to_dict() for a in self.activities],
            'sleeps': [s.to_dict() for s in self.sleeps],
        }
        return data
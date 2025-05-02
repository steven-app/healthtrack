from datetime import datetime, timedelta
import secrets
from app import db
from app.models.user import User
from flask import url_for, current_app

class SharedLink(db.Model):
    __tablename__ = 'shared_links'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    share_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)
    privacy_level = db.Column(db.String(20), nullable=False, default='overview')  # complete, overview, achievements
    modules = db.Column(db.Text, nullable=False)  # JSON array of modules to share
    date_range_start = db.Column(db.DateTime, nullable=False)
    date_range_end = db.Column(db.DateTime, nullable=False)
    template_type = db.Column(db.String(20), nullable=False, default='social')  # medical, social
    personal_message = db.Column(db.String(255), nullable=True)
    theme = db.Column(db.String(20), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, nullable=True)
    access_count = db.Column(db.Integer, default=0)
    
    # 添加兼容旧版UI的隐式属性
    show_weight = db.Column(db.Boolean, default=True)
    show_heart_rate = db.Column(db.Boolean, default=True)
    show_activity = db.Column(db.Boolean, default=True)
    show_sleep = db.Column(db.Boolean, default=True)
    show_goals = db.Column(db.Boolean, default=True)
    show_achievements = db.Column(db.Boolean, default=True)
    
    # 一次性密码相关
    one_time_password = db.Column(db.Boolean, default=False)
    password_used = db.Column(db.Boolean, default=False)
    
    # Define relationship with User
    user = db.relationship('User', backref=db.backref('shared_links', lazy='dynamic'))
    
    def __repr__(self):
        return f'<SharedLink {self.share_token}>'
    
    @staticmethod
    def generate_share_token():
        """Generate a unique share token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_one_time_password():
        """Generate a random 4-digit one-time password"""
        return ''.join(secrets.choice('0123456789') for _ in range(4))
    
    @classmethod
    def create_shared_link(cls, user_id, date_range_start, date_range_end, template_type, 
                          name=None, privacy_level=None, modules=None, expiry_days=7, 
                          password=None, personal_message=None, theme='default', 
                          privacy_settings=None, one_time_password=False):
        """Create a new shared link with flexible parameters to support both UIs"""
        share_token = cls.generate_share_token()
        
        # Handle expiration
        if expiry_days == 0:
            expires_at = None  # Never expires
        else:
            expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        
        # 设置默认值
        if privacy_level is None:
            privacy_level = 'overview'
            
        if modules is None:
            modules = '["dashboard","heartrate","activity","weight","sleep","goals","achievements"]'
            
        if privacy_settings is None:
            privacy_settings = {}
            
        # 创建基本的共享链接
        shared_link = cls(
            user_id=user_id,
            share_token=share_token,
            name=name,
            expires_at=expires_at,
            privacy_level=privacy_level,
            modules=modules,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            template_type=template_type,
            personal_message=personal_message,
            theme=theme,
            one_time_password=one_time_password,
            password_used=False
        )
        
        # 如果提供了隐私设置，更新链接属性
        for key, value in privacy_settings.items():
            if hasattr(shared_link, key):
                setattr(shared_link, key, value)
        
        if password:
            shared_link.set_password(password)
        
        db.session.add(shared_link)
        db.session.commit()
        
        return shared_link
    
    def set_password(self, password, is_one_time=False):
        """Set password for shared link"""
        if is_one_time:
            # Generate a random 4-digit password for one-time use
            password = self.generate_one_time_password()
            from werkzeug.security import generate_password_hash
            self.password_hash = generate_password_hash(password)
            self.one_time_password = True
            self.password_used = False  # Ensure password_used is set to False
            db.session.commit()  # Commit changes immediately
            return password  # Return the generated password to display to user
        elif password:
            from werkzeug.security import generate_password_hash
            self.password_hash = generate_password_hash(password)
            self.one_time_password = False
            self.password_used = False
            db.session.commit()  # Commit changes immediately
            return None
        else:
            self.password_hash = None
            self.one_time_password = False
            self.password_used = False
            db.session.commit()  # Commit changes immediately
            return None
    
    def check_password(self, password):
        """Check password for shared link"""
        if not self.password_hash:
            return True
        from werkzeug.security import check_password_hash
        
        # First refresh from database to get the latest password_used status
        try:
            db.session.refresh(self)
        except Exception as e:
            print(f"Error refreshing from database: {e}")
        
        # Check if password is correct
        is_valid = check_password_hash(self.password_hash, password)
        
        # If one-time password and not used yet, mark as used
        if is_valid and self.one_time_password and not self.password_used:
            self.password_used = True
            try:
                db.session.commit()
                print(f"Password for share_token {self.share_token} marked as used")
            except Exception as e:
                db.session.rollback()
                print(f"Error updating password_used: {e}")
            return True
        # If one-time password already used, deny access
        elif is_valid and self.one_time_password and self.password_used:
            print(f"One-time password for share_token {self.share_token} was already used")
            return False
        # Regular password check
        else:
            return is_valid
    
    @property
    def is_password_protected(self):
        """Check if this share link is password protected."""
        return self.password_hash is not None
    
    @property
    def is_expired(self):
        """Check if this share link is expired."""
        if self.expires_at is None:  # Never expires
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def days_until_expiry(self):
        """Calculate days until this share link expires."""
        if self.expires_at is None:
            return -1  # Special value indicates never expires
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def share_url(self):
        """Generate the complete URL for this share link."""
        try:
            return url_for('share.view_shared_content', share_token=self.share_token, _external=True)
        except:
            # Fallback if outside request context
            try:
                from flask import request
                base_url = f"{request.scheme}://{request.host}"
            except:
                # Final fallback if no request context
                base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
            return f"{base_url}/share/view/{self.share_token}"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'share_token': self.share_token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'has_password': bool(self.password_hash),
            'privacy_level': self.privacy_level,
            'modules': self.modules,
            'date_range_start': self.date_range_start.isoformat() if self.date_range_start else None,
            'date_range_end': self.date_range_end.isoformat() if self.date_range_end else None,
            'template_type': self.template_type,
            'personal_message': self.personal_message,
            'theme': self.theme,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def update_access_stats(self):
        """Update access statistics when link is viewed"""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
        db.session.commit() 
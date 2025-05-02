from app import db
from app.utils.date_utils import get_current_time

class ShareAccessLog(db.Model):
    """
    Model for logging access to shared links
    """
    __tablename__ = 'share_access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    share_link_id = db.Column(db.Integer, db.ForeignKey('shared_links.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    accessed_at = db.Column(db.DateTime, default=get_current_time, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 can be up to 45 chars
    user_agent = db.Column(db.String(255), nullable=True)
    successful = db.Column(db.Boolean, default=True)  # Whether access was successful (e.g., correct password)
    access_type = db.Column(db.String(20), nullable=False, default='view')  # 'view', 'pdf', etc.
    
    # Relationships - use string to avoid circular import
    share_link = db.relationship(
        'SharedLink', 
        backref=db.backref(
            'access_logs', 
            lazy='dynamic', 
            cascade='save-update, merge, refresh-expire',
            passive_deletes=True,
            passive_updates=True
        )
    )
    
    @classmethod
    def log_access(cls, share_link, request=None, successful=True, access_type='view'):
        """
        Create a log entry for share link access
        
        Args:
            share_link: The ShareLink object being accessed
            request: Flask request object (optional)
            successful: Whether access was successful
            access_type: Type of access ('view', 'pdf', etc.)
            
        Returns:
            The created log entry
        """
        ip_address = None
        user_agent = None
        
        # Extract IP and user agent from request if available
        if request:
            ip_address = request.remote_addr
            user_agent = request.user_agent.string if request.user_agent else None
        
        log_entry = cls(
            share_link_id=share_link.id,
            ip_address=ip_address,
            user_agent=user_agent,
            successful=successful,
            access_type=access_type
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return log_entry 
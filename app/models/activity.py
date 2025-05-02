from app import db

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    import_log_id = db.Column(db.Integer, db.ForeignKey('import_logs.id'), nullable=True)
    activity_type = db.Column(db.String(50))
    value = db.Column(db.Float)
    unit = db.Column(db.String(10))
    timestamp = db.Column(db.DateTime, nullable=False)
    total_steps = db.Column(db.Integer)
    total_distance = db.Column(db.Float)
    calories = db.Column(db.Integer)
    data_source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Add relationship
    import_log = db.relationship('ImportLog', backref=db.backref('activities', lazy=True))
    
    def __repr__(self):
        return f'<Activity {self.id} {self.timestamp}>'
        
    def to_dict(self):
        """Convert activity record to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'import_log_id': self.import_log_id,
            'activity_type': self.activity_type,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'total_steps': self.total_steps,
            'total_distance': self.total_distance,
            'calories': self.calories,
            'data_source': self.data_source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
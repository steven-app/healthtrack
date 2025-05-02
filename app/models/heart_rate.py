from app import db

class HeartRate(db.Model):
    __tablename__ = 'heart_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    import_log_id = db.Column(db.Integer, db.ForeignKey('import_logs.id'), nullable=True)
    value = db.Column(db.Integer, nullable=False)  # beats per minute
    unit = db.Column(db.String(10), nullable=False, default='bpm')  # Add unit field
    timestamp = db.Column(db.DateTime, nullable=False)
    data_source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Add relationship
    import_log = db.relationship('ImportLog', backref=db.backref('heart_rates', lazy=True))
    
    def __repr__(self):
        return f'<HeartRate {self.id} {self.timestamp}>'
        
    def to_dict(self):
        """Convert heart rate record to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'import_log_id': self.import_log_id,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'data_source': self.data_source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
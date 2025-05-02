from app import db

class Weight(db.Model):
    __tablename__ = 'weights'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    import_log_id = db.Column(db.Integer, db.ForeignKey('import_logs.id'), nullable=True)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    unit = db.Column(db.String(10))
    data_source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Add relationship
    import_log = db.relationship('ImportLog', backref=db.backref('weights', lazy=True))
    
    def __repr__(self):
        return f'<Weight {self.id} {self.timestamp}>'
        
    def to_dict(self):
        """Convert weight record to dictionary"""
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
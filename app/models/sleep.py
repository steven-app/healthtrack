from datetime import datetime
from app import db

class Sleep(db.Model):
    __tablename__ = 'sleeps'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    import_log_id = db.Column(db.Integer, db.ForeignKey('import_logs.id'), nullable=True)
    duration = db.Column(db.Float, nullable=False)  # Total sleep duration in minutes
    deep_sleep = db.Column(db.Float, nullable=True)  # Deep sleep duration in minutes
    light_sleep = db.Column(db.Float, nullable=True)  # Light sleep duration in minutes
    rem_sleep = db.Column(db.Float, nullable=True)  # REM sleep duration in minutes
    awake = db.Column(db.Float, nullable=True)  # Awake time during sleep period in minutes
    unit = db.Column(db.String(10), default='minutes')
    quality = db.Column(db.String(20))  # good, fair, poor
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Add relationship
    import_log = db.relationship('ImportLog', backref=db.backref('sleeps', lazy=True))
    
    def __repr__(self):
        return f'<Sleep {self.duration} minutes>'
    
    def to_dict(self):
        """Convert sleep record to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'import_log_id': self.import_log_id,
            'duration': self.duration,
            'deep_sleep': self.deep_sleep,
            'light_sleep': self.light_sleep,
            'rem_sleep': self.rem_sleep,
            'awake': self.awake,
            'unit': self.unit,
            'quality': self.quality,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'notes': self.notes
        }
    
    @staticmethod
    def create_sleep_record(user_id, duration, start_time, end_time, deep_sleep=None, 
                          light_sleep=None, rem_sleep=None, awake=None, quality=None, 
                          notes=None, import_log_id=None, unit='minutes'):
        """Create a new sleep record"""
        sleep = Sleep(
            user_id=user_id,
            duration=duration,
            deep_sleep=deep_sleep,
            light_sleep=light_sleep,
            rem_sleep=rem_sleep,
            awake=awake,
            start_time=start_time,
            end_time=end_time,
            quality=quality,
            notes=notes,
            import_log_id=import_log_id,
            unit=unit
        )
        db.session.add(sleep)
        db.session.commit()
        return sleep
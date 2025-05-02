from datetime import datetime
from app import db

class Progress(db.Model):
    __tablename__ = 'progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Progress {self.value} {self.unit}>'
    
    def to_dict(self):
        """Convert progress to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'notes': self.notes
        }
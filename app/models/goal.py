from datetime import datetime
from app import db

class Goal(db.Model):
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'steps', 'weight', 'sleep', 'heart_rate'
    target_value = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, default=0)
    unit = db.Column(db.String(20), nullable=False)
    timeframe = db.Column(db.String(20), nullable=False)  # 'daily', 'weekly', 'monthly'
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    progress_related = db.Column(db.Boolean, default=False)
    progress_baseline = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_progress(self):
        """Calculate progress as percentage"""
        if self.current_value is None:
            return 0
            
        if self.progress_related and self.progress_baseline is not None:
            # For weight loss goal
            if self.target_value < self.progress_baseline:
                if self.progress_baseline == self.current_value:
                    return 0
                progress = (self.progress_baseline - self.current_value) / (self.progress_baseline - self.target_value) * 100
            else:  # weight gain goal
                if self.target_value == self.progress_baseline:
                    return 100
                progress = (self.current_value - self.progress_baseline) / (self.target_value - self.progress_baseline) * 100
        else:
            progress = (self.current_value / self.target_value) * 100
            
        return min(round(progress, 1), 100)
        
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'unit': self.unit,
            'timeframe': self.timeframe,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'completed': self.completed,
            'progress': self.calculate_progress(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
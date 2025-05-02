from datetime import datetime
from app import db

class Achievement(db.Model):
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'steps', 'weight', 'sleep', 'heart_rate', 'general'
    icon = db.Column(db.String(100))
    level = db.Column(db.String(20), default='bronze')  # bronze, silver, gold
    condition_type = db.Column(db.String(50))  # streak, milestone, improvement
    condition_value = db.Column(db.Float)
    trigger_type = db.Column(db.String(20))  # 'progress', 'goal', 'combined'
    progress_related = db.Column(db.Boolean, default=False)
    goal_related = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_achievements = db.relationship('UserAchievement', back_populates='achievement')
    
    def __repr__(self):
        return f'<Achievement {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'icon': self.icon,
            'level': self.level,
            'condition_type': self.condition_type,
            'condition_value': self.condition_value
        }


class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    achievement = db.relationship('Achievement', back_populates='user_achievements')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'achievement': self.achievement.to_dict(),
            'earned_at': self.earned_at.strftime('%Y-%m-%d %H:%M:%S')
        }
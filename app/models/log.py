from app import db

class Log(db.Model):
    __tablename__ = 'logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<Log {self.action} {self.created_at}>'
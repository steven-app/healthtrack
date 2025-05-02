from datetime import datetime
from app import db

class ImportLog(db.Model):
    __tablename__ = 'import_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_source = db.Column(db.String(50), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, failed, processing
    error_message = db.Column(db.Text)
    records_processed = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<ImportLog {self.file_name} {self.status}>'
    
    def to_dict(self):
        """Convert import log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'data_source': self.data_source,
            'file_name': self.file_name,
            'status': self.status,
            'error_message': self.error_message,
            'records_processed': self.records_processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        } 
import os
import tempfile
from datetime import datetime
import json
from flask import current_app, render_template
from weasyprint import HTML, CSS
from app.models import User, SharedLink, Weight, HeartRate, Activity, Sleep, Goal, Achievement, UserAchievement

class PDFService:
    """Service for generating PDF reports from shared health data"""
    
    @staticmethod
    def generate_shared_pdf(share_token):
        """Generate a PDF report from a shared link"""
        try:
            # Get shared link
            share_link = SharedLink.query.filter_by(share_token=share_token).first()
            if not share_link or share_link.is_expired():
                raise ValueError("Share link not found or expired")
            
            # Get user
            user = User.query.get(share_link.user_id)
            if not user:
                raise ValueError("User not found")
            
            # Get health data
            data = PDFService._get_shared_data(share_link)
            
            # Determine template based on template_type
            template = f'share/pdf/{share_link.template_type}.html'
            
            # Render HTML template with data
            html_content = render_template(
                template,
                share_link=share_link,
                user=user,
                name=user.get_full_name(),
                data=data,
                generated_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            )
            
            # Create temporary file to save PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp:
                temp_path = temp.name
            
            # Generate PDF from HTML
            HTML(string=html_content).write_pdf(
                temp_path,
                stylesheets=[
                    CSS(string='@page { size: A4; margin: 1cm; }')
                ]
            )
            
            return temp_path
        except Exception as e:
            current_app.logger.error(f"Error generating PDF: {str(e)}")
            raise
    
    @staticmethod
    def _get_shared_data(share_link):
        """Get data for PDF based on shared link settings"""
        # Get user
        user = User.query.get(share_link.user_id)
        
        # Parse modules
        try:
            modules = json.loads(share_link.modules)
        except:
            modules = ["dashboard", "heartrate", "activity", "weight", "sleep", "goals", "achievements"]
        
        # Initialize data dict
        data = {}
        
        # Add data based on modules and privacy level
        if "dashboard" in modules:
            data['dashboard'] = PDFService._get_dashboard_data(user.id, share_link)
        
        if "heartrate" in modules:
            data['heartrate'] = PDFService._get_heartrate_data(user.id, share_link)
            
        if "activity" in modules:
            data['activity'] = PDFService._get_activity_data(user.id, share_link)
            
        if "weight" in modules:
            data['weight'] = PDFService._get_weight_data(user.id, share_link)
            
        if "sleep" in modules:
            data['sleep'] = PDFService._get_sleep_data(user.id, share_link)
            
        if "goals" in modules and share_link.privacy_level != 'achievements':
            data['goals'] = PDFService._get_goals_data(user.id, share_link)
            
        if "achievements" in modules:
            data['achievements'] = PDFService._get_achievements_data(user.id, share_link)
        
        return data
    
    @staticmethod
    def _get_dashboard_data(user_id, share_link):
        """Get dashboard data for PDF"""
        # Get data
        weights = Weight.query.filter(
            Weight.user_id == user_id,
            Weight.timestamp >= share_link.date_range_start,
            Weight.timestamp <= share_link.date_range_end
        ).order_by(Weight.timestamp.desc()).all()
        
        heart_rates = HeartRate.query.filter(
            HeartRate.user_id == user_id,
            HeartRate.timestamp >= share_link.date_range_start,
            HeartRate.timestamp <= share_link.date_range_end
        ).order_by(HeartRate.timestamp.desc()).all()
        
        activities = Activity.query.filter(
            Activity.user_id == user_id,
            Activity.timestamp >= share_link.date_range_start,
            Activity.timestamp <= share_link.date_range_end
        ).order_by(Activity.timestamp.desc()).all()
        
        sleeps = Sleep.query.filter(
            Sleep.user_id == user_id,
            Sleep.timestamp >= share_link.date_range_start,
            Sleep.timestamp <= share_link.date_range_end
        ).order_by(Sleep.timestamp.desc()).all()
        
        # Process data based on privacy level
        if share_link.privacy_level == 'overview':
            # Return only aggregated data
            data = {
                'weights': [{'date': w.timestamp.strftime('%Y-%m-%d'), 'value': w.value, 'unit': w.unit} for w in weights[:7]],
                'heart_rates': [{'date': hr.timestamp.strftime('%Y-%m-%d'), 'value': hr.value, 'unit': hr.unit} for hr in heart_rates[:7]],
                'activities': [{'date': a.timestamp.strftime('%Y-%m-%d'), 'steps': a.value} for a in activities[:7]],
                'sleeps': [{'date': s.timestamp.strftime('%Y-%m-%d'), 'duration': s.duration / 60} for s in sleeps[:7]],
                'summary': {
                    'weight': {'latest': weights[0].value if weights else 0},
                    'heart_rate': {
                        'min': min([hr.value for hr in heart_rates]) if heart_rates else 0,
                        'max': max([hr.value for hr in heart_rates]) if heart_rates else 0,
                        'avg': sum([hr.value for hr in heart_rates]) / len(heart_rates) if heart_rates else 0
                    },
                    'activity': {
                        'avg_steps': sum([a.value for a in activities]) / len(activities) if activities else 0,
                        'total_steps': sum([a.value for a in activities]) if activities else 0
                    },
                    'sleep': {
                        'avg_duration_hours': sum([s.duration for s in sleeps]) / len(sleeps) / 60 if sleeps else 0
                    }
                }
            }
        else:  # complete
            # Return all data
            data = {
                'weights': [w.to_dict() for w in weights],
                'heart_rates': [hr.to_dict() for hr in heart_rates],
                'activities': [a.to_dict() for a in activities],
                'sleeps': [s.to_dict() for s in sleeps],
                'summary': {
                    'weight': {'latest': weights[0].value if weights else 0},
                    'heart_rate': {
                        'min': min([hr.value for hr in heart_rates]) if heart_rates else 0,
                        'max': max([hr.value for hr in heart_rates]) if heart_rates else 0,
                        'avg': sum([hr.value for hr in heart_rates]) / len(heart_rates) if heart_rates else 0
                    },
                    'activity': {
                        'avg_steps': sum([a.value for a in activities]) / len(activities) if activities else 0,
                        'total_steps': sum([a.value for a in activities]) if activities else 0
                    },
                    'sleep': {
                        'avg_duration_hours': sum([s.duration for s in sleeps]) / len(sleeps) / 60 if sleeps else 0
                    }
                }
            }
        
        return data
    
    # Helper methods for other data types (similar to the API endpoints)
    @staticmethod
    def _get_heartrate_data(user_id, share_link):
        heart_rates = HeartRate.query.filter(
            HeartRate.user_id == user_id,
            HeartRate.timestamp >= share_link.date_range_start,
            HeartRate.timestamp <= share_link.date_range_end
        ).order_by(HeartRate.timestamp.desc()).all()
        
        if share_link.privacy_level == 'overview':
            return [{'date': hr.timestamp.strftime('%Y-%m-%d'), 'value': hr.value, 'unit': hr.unit} for hr in heart_rates[:14]]
        else:  # complete
            return [hr.to_dict() for hr in heart_rates]
    
    @staticmethod
    def _get_activity_data(user_id, share_link):
        activities = Activity.query.filter(
            Activity.user_id == user_id,
            Activity.timestamp >= share_link.date_range_start,
            Activity.timestamp <= share_link.date_range_end
        ).order_by(Activity.timestamp.desc()).all()
        
        if share_link.privacy_level == 'overview':
            return [{'date': a.timestamp.strftime('%Y-%m-%d'), 'steps': a.value} for a in activities[:14]]
        else:  # complete
            return [a.to_dict() for a in activities]
    
    @staticmethod
    def _get_weight_data(user_id, share_link):
        weights = Weight.query.filter(
            Weight.user_id == user_id,
            Weight.timestamp >= share_link.date_range_start,
            Weight.timestamp <= share_link.date_range_end
        ).order_by(Weight.timestamp.desc()).all()
        
        if share_link.privacy_level == 'overview':
            return [{'date': w.timestamp.strftime('%Y-%m-%d'), 'value': w.value, 'unit': w.unit} for w in weights[:14]]
        else:  # complete
            return [w.to_dict() for w in weights]
    
    @staticmethod
    def _get_sleep_data(user_id, share_link):
        sleeps = Sleep.query.filter(
            Sleep.user_id == user_id,
            Sleep.timestamp >= share_link.date_range_start,
            Sleep.timestamp <= share_link.date_range_end
        ).order_by(Sleep.timestamp.desc()).all()
        
        if share_link.privacy_level == 'overview':
            return [{'date': s.timestamp.strftime('%Y-%m-%d'), 'duration': s.duration / 60} for s in sleeps[:14]]
        else:  # complete
            return [s.to_dict() for s in sleeps]
    
    @staticmethod
    def _get_goals_data(user_id, share_link):
        goals = Goal.query.filter(
            Goal.user_id == user_id,
            Goal.created_at >= share_link.date_range_start,
            Goal.created_at <= share_link.date_range_end
        ).order_by(Goal.created_at.desc()).all()
        
        return [g.to_dict() for g in goals]
    
    @staticmethod
    def _get_achievements_data(user_id, share_link):
        user_achievements = UserAchievement.query.filter(
            UserAchievement.user_id == user_id,
            UserAchievement.earned_at >= share_link.date_range_start,
            UserAchievement.earned_at <= share_link.date_range_end
        ).order_by(UserAchievement.earned_at.desc()).all()
        
        achievements = []
        for ua in user_achievements:
            achievement = Achievement.query.get(ua.achievement_id)
            if achievement:
                achievement_dict = achievement.to_dict()
                achievement_dict['earned_at'] = ua.earned_at.isoformat()
                achievements.append(achievement_dict)
        
        return achievements 
from datetime import datetime, timedelta
from app import db
from app.models.goal import Goal
from app.models.user import User
from app.models.activity import Activity
from app.models.weight import Weight
from app.models.sleep import Sleep
from app.models.heart_rate import HeartRate

class GoalService:
    @staticmethod
    def create_goal(user_id, category, target_value, unit, timeframe, start_date, end_date=None, 
                    progress_related=False, progress_baseline=None):
        """Create a new goal for the user"""
        goal = Goal(
            user_id=user_id,
            category=category,
            target_value=target_value,
            unit=unit,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            progress_related=progress_related,
            progress_baseline=progress_baseline
        )
        
        # Set initial current value
        GoalService.update_goal_progress(goal)
        
        db.session.add(goal)
        db.session.commit()
        
        return goal
    
    @staticmethod
    def update_goal_progress(goal):
        """Update the current progress of a goal"""
        user = User.query.get(goal.user_id)
        if not user:
            return
        
        # Calculate current value based on category and timeframe
        if goal.category == 'steps':
            GoalService._update_steps_goal(goal)
        elif goal.category == 'weight':
            GoalService._update_weight_goal(goal)
        elif goal.category == 'sleep':
            GoalService._update_sleep_goal(goal)
        elif goal.category == 'heart_rate':
            GoalService._update_heart_rate_goal(goal)
        
        # Check if goal is completed
        progress = goal.calculate_progress()
        if progress >= 100 and not goal.completed:
            goal.completed = True
            db.session.commit()
    
    @staticmethod
    def _update_steps_goal(goal):
        # Get timeframe dates
        start_date, end_date = GoalService._get_timeframe_dates(goal)
        
        # Query activities in timeframe
        activities = Activity.query.filter(
            Activity.user_id == goal.user_id,
            Activity.timestamp >= start_date,
            Activity.timestamp <= end_date
        ).all()
        
        # Sum steps
        total_steps = sum(activity.total_steps or 0 for activity in activities)
        
        # Update goal current value
        goal.current_value = total_steps
        db.session.commit()
    
    @staticmethod
    def _update_weight_goal(goal):
        # For weight, we take the latest weight record
        latest_weight = Weight.query.filter_by(user_id=goal.user_id).order_by(Weight.timestamp.desc()).first()
        
        if latest_weight:
            goal.current_value = latest_weight.value
            db.session.commit()
    
    @staticmethod
    def _update_sleep_goal(goal):
        # Get timeframe dates
        start_date, end_date = GoalService._get_timeframe_dates(goal)
        
        # Query sleep records in timeframe
        sleeps = Sleep.query.filter(
            Sleep.user_id == goal.user_id,
            Sleep.timestamp >= start_date,
            Sleep.timestamp <= end_date
        ).all()
        
        if goal.timeframe == 'daily':
            # Calculate average daily sleep
            if sleeps:
                avg_sleep = sum(sleep.duration or 0 for sleep in sleeps) / len(sleeps)
                goal.current_value = avg_sleep
        else:
            # Sum total sleep over period
            total_sleep = sum(sleep.duration or 0 for sleep in sleeps)
            goal.current_value = total_sleep
        
        db.session.commit()
    
    @staticmethod
    def _update_heart_rate_goal(goal):
        # Get timeframe dates
        start_date, end_date = GoalService._get_timeframe_dates(goal)
        
        # Query heart rate records in timeframe
        heart_rates = HeartRate.query.filter(
            HeartRate.user_id == goal.user_id,
            HeartRate.timestamp >= start_date,
            HeartRate.timestamp <= end_date
        ).all()
        
        if heart_rates:
            # Calculate average heart rate
            avg_hr = sum(hr.value for hr in heart_rates) / len(heart_rates)
            goal.current_value = avg_hr
            db.session.commit()
    
    @staticmethod
    def _get_timeframe_dates(goal):
        """Get the start and end dates based on goal timeframe"""
        today = datetime.utcnow().date()
        
        if goal.timeframe == 'daily':
            start_date = datetime.combine(today, datetime.min.time())
            end_date = datetime.combine(today, datetime.max.time())
        elif goal.timeframe == 'weekly':
            # Start from Monday of current week
            monday = today - timedelta(days=today.weekday())
            start_date = datetime.combine(monday, datetime.min.time())
            end_date = start_date + timedelta(days=7) - timedelta(microseconds=1)
        elif goal.timeframe == 'monthly':
            # Start from first day of current month
            start_date = datetime.combine(today.replace(day=1), datetime.min.time())
            # Get last day of month
            if today.month == 12:
                next_month = today.replace(year=today.year+1, month=1, day=1)
            else:
                next_month = today.replace(month=today.month+1, day=1)
            end_date = datetime.combine(next_month - timedelta(days=1), datetime.max.time())
        
        return start_date, end_date 
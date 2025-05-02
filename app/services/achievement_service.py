from datetime import datetime, timedelta
from app import db
from app.models.achievement import Achievement, UserAchievement
from app.models.user import User
from app.models.activity import Activity
from app.models.weight import Weight
from app.models.sleep import Sleep
from app.models.heart_rate import HeartRate
from app.models.goal import Goal
from flask import flash

def check_achievements_for_user(user_id):
    """Check all achievements for a user"""
    user = User.query.get(user_id)
    if not user:
        return []
    
    earned_achievements = []
    
    # Get all achievements
    achievements = Achievement.query.all()
    
    # Get user's already earned achievements
    earned_ids = [ua.achievement_id for ua in UserAchievement.query.filter_by(user_id=user_id).all()]
    
    # Check each achievement
    for achievement in achievements:
        # Skip if already earned
        if achievement.id in earned_ids:
            continue
        
        # Check achievement based on type
        earned = False
        
        if achievement.category == 'steps':
            earned = check_steps_achievement(user, achievement)
        elif achievement.category == 'weight':
            earned = check_weight_achievement(user, achievement)
        elif achievement.category == 'sleep':
            earned = check_sleep_achievement(user, achievement)
        elif achievement.category == 'heart_rate':
            earned = check_heart_rate_achievement(user, achievement)
        elif achievement.category == 'general':
            earned = check_general_achievement(user, achievement)
        
        # If earned, add to database
        if earned:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id
            )
            db.session.add(user_achievement)
            earned_achievements.append(achievement)
    
    if earned_achievements:
        db.session.commit()
    
    return earned_achievements

def check_achievements_for_goal(user_id, goal):
    """Check achievements related to goal completion"""
    user = User.query.get(user_id)
    if not user:
        return []
    
    earned_achievements = []
    
    # Get goal-related achievements for this category
    achievements = Achievement.query.filter_by(
        goal_related=True,
        category=goal.category
    ).all()
    
    # Get user's already earned achievements
    earned_ids = [ua.achievement_id for ua in UserAchievement.query.filter_by(user_id=user_id).all()]
    
    # Check each achievement
    for achievement in achievements:
        # Skip if already earned
        if achievement.id in earned_ids:
            continue
        
        # Check if goal completion triggers this achievement
        earned = False
        
        # Example: Milestone achievement for completing a goal
        if achievement.condition_type == 'milestone' and goal.completed:
            # Check if the goal's target meets the achievement condition
            if goal.target_value >= achievement.condition_value:
                earned = True
        
        # Example: Streak achievement for completing multiple goals
        elif achievement.condition_type == 'streak':
            # Count completed goals in category
            completed_count = Goal.query.filter_by(
                user_id=user_id,
                category=goal.category,
                completed=True
            ).count()
            
            if completed_count >= achievement.condition_value:
                earned = True
        
        # If earned, add to database
        if earned:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id
            )
            db.session.add(user_achievement)
            earned_achievements.append(achievement)
    
    if earned_achievements:
        db.session.commit()
        
        # Flash messages for earned achievements
        for achievement in earned_achievements:
            flash(f'Achievement unlocked: {achievement.name}', 'success')
    
    return earned_achievements

def check_steps_achievement(user, achievement):
    """Check if user has earned a steps-related achievement"""
    if achievement.condition_type == 'milestone':
        # Check for total steps milestone
        activities = Activity.query.filter_by(user_id=user.id).all()
        total_steps = sum(activity.total_steps or 0 for activity in activities)
        return total_steps >= achievement.condition_value
    
    elif achievement.condition_type == 'streak':
        # Check for daily steps streak
        streak_days = int(achievement.condition_value)
        streak = 0
        current_date = datetime.utcnow().date()
        
        for i in range(streak_days):
            check_date = current_date - timedelta(days=i)
            start_of_day = datetime.combine(check_date, datetime.min.time())
            end_of_day = datetime.combine(check_date, datetime.max.time())
            
            # Get activities for this day
            day_activities = Activity.query.filter(
                Activity.user_id == user.id,
                Activity.timestamp >= start_of_day,
                Activity.timestamp <= end_of_day
            ).all()
            
            day_steps = sum(activity.total_steps or 0 for activity in day_activities)
            
            # 5000 steps is considered active day for this example
            if day_steps >= 5000:
                streak += 1
            else:
                break
        
        return streak >= streak_days
    
    return False

def check_weight_achievement(user, achievement):
    """Check if user has earned a weight-related achievement"""
    weights = Weight.query.filter_by(user_id=user.id).order_by(Weight.timestamp).all()
    
    if not weights or len(weights) < 2:
        return False
    
    if achievement.condition_type == 'improvement':
        # Check for weight loss/gain achievement
        first_weight = weights[0].value
        latest_weight = weights[-1].value
        difference = abs(latest_weight - first_weight)
        
        return difference >= achievement.condition_value
    
    elif achievement.condition_type == 'streak':
        # Check for consistent weight tracking
        streak_days = int(achievement.condition_value)
        streak = 0
        current_date = datetime.utcnow().date()
        
        for i in range(streak_days):
            check_date = current_date - timedelta(days=i)
            start_of_day = datetime.combine(check_date, datetime.min.time())
            end_of_day = datetime.combine(check_date, datetime.max.time())
            
            # Check if there's a weight record for this day
            day_weight = Weight.query.filter(
                Weight.user_id == user.id,
                Weight.timestamp >= start_of_day,
                Weight.timestamp <= end_of_day
            ).first()
            
            if day_weight:
                streak += 1
            else:
                break
        
        return streak >= streak_days
    
    return False

def check_sleep_achievement(user, achievement):
    """Check if user has earned a sleep-related achievement"""
    sleeps = Sleep.query.filter_by(user_id=user.id).all()
    
    if not sleeps:
        return False
    
    if achievement.condition_type == 'milestone':
        # Check for sleep quality milestone
        good_sleep_count = sum(1 for sleep in sleeps if sleep.quality and sleep.quality >= 8)
        return good_sleep_count >= achievement.condition_value
    
    elif achievement.condition_type == 'streak':
        # Check for sleep tracking streak
        streak_days = int(achievement.condition_value)
        streak = 0
        current_date = datetime.utcnow().date()
        
        for i in range(streak_days):
            check_date = current_date - timedelta(days=i)
            start_of_day = datetime.combine(check_date, datetime.min.time())
            end_of_day = datetime.combine(check_date, datetime.max.time())
            
            # Check if there's a sleep record for this day
            day_sleep = Sleep.query.filter(
                Sleep.user_id == user.id,
                Sleep.timestamp >= start_of_day,
                Sleep.timestamp <= end_of_day
            ).first()
            
            if day_sleep:
                streak += 1
            else:
                break
        
        return streak >= streak_days
    
    return False

def check_heart_rate_achievement(user, achievement):
    """Check if user has earned a heart-rate-related achievement"""
    heart_rates = HeartRate.query.filter_by(user_id=user.id).all()
    
    if not heart_rates:
        return False
    
    if achievement.condition_type == 'improvement':
        # Get heart rates from last month
        one_month_ago = datetime.utcnow() - timedelta(days=30)
        old_heart_rates = HeartRate.query.filter(
            HeartRate.user_id == user.id,
            HeartRate.timestamp <= one_month_ago
        ).all()
        
        recent_heart_rates = HeartRate.query.filter(
            HeartRate.user_id == user.id,
            HeartRate.timestamp > one_month_ago
        ).all()
        
        if not old_heart_rates or not recent_heart_rates:
            return False
        
        # Calculate averages
        old_avg = sum(hr.value for hr in old_heart_rates) / len(old_heart_rates)
        recent_avg = sum(hr.value for hr in recent_heart_rates) / len(recent_heart_rates)
        
        # Check for improvement (lower resting heart rate is generally better)
        improvement = old_avg - recent_avg
        return improvement >= achievement.condition_value
    
    return False

def check_general_achievement(user, achievement):
    """Check general achievements like app usage"""
    if achievement.condition_type == 'milestone':
        # Example: Total data points milestone
        if achievement.name == 'Data Collector':
            steps_count = Activity.query.filter_by(user_id=user.id).count()
            weight_count = Weight.query.filter_by(user_id=user.id).count()
            sleep_count = Sleep.query.filter_by(user_id=user.id).count()
            heart_rate_count = HeartRate.query.filter_by(user_id=user.id).count()
            
            total_data_points = steps_count + weight_count + sleep_count + heart_rate_count
            return total_data_points >= achievement.condition_value
    
    return False 
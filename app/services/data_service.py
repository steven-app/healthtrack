from app import db
from app.models.weight import Weight
from app.models.heart_rate import HeartRate
from app.models.activity import Activity
from app.models.sleep import Sleep
from app.models.goal import Goal
from app.models.achievement import Achievement, UserAchievement
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from collections import defaultdict

def get_user_data_in_range(user_id, start_date, end_date, 
                          include_weight=True, include_heart_rate=True,
                          include_activity=True, include_sleep=True,
                          include_goals=True, include_achievements=True,
                          limit_to_week=False, group_by='day'):
    """
    Get all user data within the specified date range.
    
    Args:
        user_id: The user ID
        start_date: The start date (inclusive)
        end_date: The end date (inclusive)
        include_weight: Whether to include weight data
        include_heart_rate: Whether to include heart rate data
        include_activity: Whether to include activity data
        include_sleep: Whether to include sleep data
        include_goals: Whether to include goals data
        include_achievements: Whether to include achievements data
        limit_to_week: Whether to limit the data to the most recent 7 days
        group_by: 'day' or 'hour' - determines aggregation granularity.
        
    Returns:
        A dictionary containing the requested data
    """
    data = {}
    
    # Include weight data if requested
    if include_weight:
        weights = Weight.query.filter(
            and_(
                Weight.user_id == user_id,
                Weight.timestamp >= start_date,
                Weight.timestamp <= end_date
            )
        ).order_by(Weight.timestamp.desc()).all()
        
        grouped_weights = defaultdict(list)
        for w in weights:
            if group_by == 'hour':
                key = w.timestamp.strftime('%Y-%m-%d %H:00')
            else:
                key = w.timestamp.strftime('%Y-%m-%d')
            grouped_weights[key].append(w)
        
        weight_data = []
        for key, ws in grouped_weights.items():
            # Use the latest weight in the group
            latest = max(ws, key=lambda x: x.timestamp)
            weight_data.append({
                'date': key,
                'weight': latest.value,
                'unit': latest.unit
            })
        
        weight_data = sorted(weight_data, key=lambda x: x['date'], reverse=True)
        data['weights'] = weight_data[:7] if limit_to_week else weight_data
        
        # Calculate weight statistics
        if weights:
            data['weight_stats'] = {
                'current': weights[-1].value,
                'min': min(w.value for w in weights),
                'max': max(w.value for w in weights),
                'avg': sum(w.value for w in weights) / len(weights),
                'change': weights[-1].value - weights[0].value if len(weights) > 1 else 0
            }
        else:
            data['weight_stats'] = None
    
    # Include heart rate data if requested
    if include_heart_rate:
        heart_rates = HeartRate.query.filter(
            and_(
                HeartRate.user_id == user_id,
                HeartRate.timestamp >= start_date,
                HeartRate.timestamp <= end_date
            )
        ).order_by(HeartRate.timestamp.desc()).all()
        
        grouped_heart = defaultdict(list)
        for h in heart_rates:
            if group_by == 'hour':
                key = h.timestamp.strftime('%Y-%m-%d %H:00')
            else:
                key = h.timestamp.strftime('%Y-%m-%d')
            grouped_heart[key].append(h)
        
        heart_data = []
        for key, hs in grouped_heart.items():
            avg_hr = sum(h.value for h in hs if h.value) / len(hs) if hs else 0
            min_hr = min((h.value for h in hs if h.value), default=None)
            max_hr = max((h.value for h in hs if h.value), default=None)
            heart_data.append({
                'date': key,
                'avg_heart_rate': avg_hr,
                'min_heart_rate': min_hr,
                'max_heart_rate': max_hr
            })
        
        heart_data = sorted(heart_data, key=lambda x: x['date'], reverse=True)
        data['heart_rates'] = heart_data[:7] if limit_to_week else heart_data
        
        # Calculate heart rate statistics
        if heart_rates:
            data['heart_rate_stats'] = {
                'min': min(hr.value for hr in heart_rates if hr.value is not None),
                'max': max(hr.value for hr in heart_rates if hr.value is not None),
                'avg': sum(hr.value for hr in heart_rates if hr.value is not None) / len([hr for hr in heart_rates if hr.value is not None]),
                'resting': None
            }
        else:
            data['heart_rate_stats'] = None
    
    # Include activity data if requested
    if include_activity:
        activities = Activity.query.filter(
            and_(
                Activity.user_id == user_id,
                Activity.timestamp >= start_date,
                Activity.timestamp <= end_date
            )
        ).order_by(Activity.timestamp.desc()).all()
        
        grouped_activities = defaultdict(list)
        for a in activities:
            if group_by == 'hour':
                key = a.timestamp.strftime('%Y-%m-%d %H:00')
            else:
                key = a.timestamp.strftime('%Y-%m-%d')
            grouped_activities[key].append(a)
        
        activity_data = []
        for key, acts in grouped_activities.items():
            total_steps = sum(a.total_steps or 0 for a in acts)
            total_distance = sum(a.total_distance or 0 for a in acts)
            calories = sum(a.calories or 0 for a in acts)
            activity_data.append({
                'date': key,
                'steps': total_steps,
                'distance': total_distance,
                'calories': calories
            })
        
        activity_data = sorted(activity_data, key=lambda x: x['date'], reverse=True)
        data['activities'] = activity_data[:7] if limit_to_week else activity_data
        
        # Calculate activity statistics
        if activities:
            total_steps = sum(a.total_steps for a in activities if a.total_steps is not None)
            total_distance = sum(a.total_distance for a in activities if a.total_distance is not None)
            total_calories = sum(a.calories for a in activities if a.calories is not None)
            
            avg_steps = total_steps / len([a for a in activities if a.total_steps is not None]) if any(a.total_steps is not None for a in activities) else 0
            max_steps = max((a.total_steps for a in activities if a.total_steps is not None), default=0)
            
            data['activity_stats'] = {
                'total_steps': total_steps,
                'total_distance': total_distance,
                'total_calories': total_calories,
                'avg_steps': avg_steps,
                'max_steps': max_steps
            }
        else:
            data['activity_stats'] = None
    
    # Include sleep data if requested
    if include_sleep:
        sleeps = Sleep.query.filter(
            and_(
                Sleep.user_id == user_id,
                Sleep.timestamp >= start_date,
                Sleep.timestamp <= end_date
            )
        ).order_by(Sleep.timestamp.desc()).all()
        
        grouped_sleep = defaultdict(list)
        for s in sleeps:
            if group_by == 'hour':
                key = s.timestamp.strftime('%Y-%m-%d %H:00')
            else:
                key = s.timestamp.strftime('%Y-%m-%d')
            grouped_sleep[key].append(s)
        
        sleep_data = []
        for key, ss in grouped_sleep.items():
            total_duration = sum(s.duration or 0 for s in ss)
            avg_quality = sum(s.quality or 0 for s in ss) / len(ss) if ss else 0
            sleep_data.append({
                'date': key,
                'duration': total_duration,
                'avg_quality': avg_quality
            })
        
        sleep_data = sorted(sleep_data, key=lambda x: x['date'], reverse=True)
        data['sleeps'] = sleep_data[:7] if limit_to_week else sleep_data
        
        # Calculate sleep statistics
        if sleeps:
            # Convert all durations to hours
            sleep_hours = []
            for s in sleeps:
                if s.duration is not None:
                    # If duration exceeds 24 hours, it might be in minutes
                    duration_hour = s.duration / 60 if s.duration > 24 else s.duration
                    sleep_hours.append(duration_hour)
            
            if sleep_hours:
                data['sleep_stats'] = {
                    'avg_duration': sum(sleep_hours) / len(sleep_hours),
                    'min_duration': min(sleep_hours),
                    'max_duration': max(sleep_hours),
                    'quality_distribution': {
                        'poor': len([s for s in sleeps if s.quality == 'poor']),
                        'fair': len([s for s in sleeps if s.quality == 'fair']),
                        'good': len([s for s in sleeps if s.quality == 'good']),
                        'excellent': len([s for s in sleeps if s.quality == 'excellent'])
                    }
                }
            else:
                data['sleep_stats'] = None
        else:
            data['sleep_stats'] = None
    
    # Include goals if requested
    if include_goals:
        # Include both active goals and goals completed within the date range
        goals = Goal.query.filter(
            and_(
                Goal.user_id == user_id,
                (
                    # Either the goal is not completed
                    (Goal.completed == False) |
                    # Or it was completed within our date range
                    (and_(
                        Goal.completed == True,
                        Goal.updated_at >= start_date,
                        Goal.updated_at <= end_date
                    ))
                )
            )
        ).all()
        
        data['goals'] = [g.to_dict() for g in goals]
        
        # Calculate goal statistics
        if goals:
            completed_goals = [g for g in goals if g.completed]
            active_goals = [g for g in goals if not g.completed]
            
            data['goal_stats'] = {
                'total': len(goals),
                'completed': len(completed_goals),
                'active': len(active_goals),
                'by_category': {}
            }
            
            # Count goals by category
            categories = set(g.category for g in goals)
            for category in categories:
                category_goals = [g for g in goals if g.category == category]
                completed = len([g for g in category_goals if g.completed])
                
                data['goal_stats']['by_category'][category] = {
                    'total': len(category_goals),
                    'completed': completed,
                    'active': len(category_goals) - completed
                }
        else:
            data['goal_stats'] = None
    
    # Include achievements if requested
    if include_achievements:
        # Get user achievements earned within the date range
        user_achievements = UserAchievement.query.join(
            Achievement, Achievement.id == UserAchievement.achievement_id
        ).filter(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.earned_at >= start_date,
                UserAchievement.earned_at <= end_date
            )
        ).all()
        
        # Include the achievements themselves
        achievements = []
        for ua in user_achievements:
            achievement_dict = ua.achievement.to_dict()
            achievement_dict['earned_at'] = ua.earned_at.isoformat() if ua.earned_at else None
            achievements.append(achievement_dict)
        
        data['achievements'] = achievements
        
        # Calculate achievement statistics
        if achievements:
            # Count achievements by category
            data['achievement_stats'] = {
                'total': len(achievements),
                'by_category': {}
            }
            
            categories = set(a['category'] for a in achievements)
            for category in categories:
                category_achievements = [a for a in achievements if a['category'] == category]
                data['achievement_stats']['by_category'][category] = len(category_achievements)
                
        else:
            data['achievement_stats'] = None
    
    # Prepare a consolidated summary that is sent to templates
    summary = {}
    
    if include_weight and 'weight_stats' in data and data['weight_stats']:
        summary['weight'] = data['weight_stats']
    else:
        summary['weight'] = {'latest': 0, 'min': 0, 'max': 0, 'avg': 0, 'change': 0}
    
    if include_heart_rate and 'heart_rate_stats' in data and data['heart_rate_stats']:
        summary['heart_rate'] = data['heart_rate_stats']
    else:
        summary['heart_rate'] = {'min': 0, 'max': 0, 'avg': 0, 'resting': 0}
    
    if include_activity and 'activity_stats' in data and data['activity_stats']:
        summary['activity'] = data['activity_stats']
    else:
        summary['activity'] = {'total_steps': 0, 'total_distance': 0, 'total_calories': 0, 'avg_steps': 0, 'max_steps': 0}
    
    if include_sleep and 'sleep_stats' in data and data['sleep_stats']:
        summary['sleep'] = data['sleep_stats']
        # 添加avg_duration_hours字段作为更直观的别名
        summary['sleep']['avg_duration_hours'] = summary['sleep']['avg_duration']
    else:
        summary['sleep'] = {'avg_duration': 0, 'min_duration': 0, 'max_duration': 0, 'avg_duration_hours': 0,
                           'quality_distribution': {'poor': 0, 'fair': 0, 'good': 0, 'excellent': 0}}
    
    data['summary'] = summary
    
    return data 
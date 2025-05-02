from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import Weight, HeartRate, Activity, Sleep

def get_data_time_range(user_id):
    """Get the time range of available data for a user"""
    # Get the earliest and latest records for each data type
    weight_range = Weight.query.filter_by(user_id=user_id).with_entities(
        func.min(Weight.timestamp),
        func.max(Weight.timestamp)
    ).first()
    
    heart_rate_range = HeartRate.query.filter_by(user_id=user_id).with_entities(
        func.min(HeartRate.timestamp),
        func.max(HeartRate.timestamp)
    ).first()
    
    activity_range = Activity.query.filter_by(user_id=user_id).with_entities(
        func.min(Activity.timestamp),
        func.max(Activity.timestamp)
    ).first()
    
    sleep_range = Sleep.query.filter_by(user_id=user_id).with_entities(
        func.min(Sleep.start_time),
        func.max(Sleep.end_time)
    ).first()
    
    # Find the overall earliest and latest dates
    dates = [
        (weight_range[0], weight_range[1]) if weight_range[0] else None,
        (heart_rate_range[0], heart_rate_range[1]) if heart_rate_range[0] else None,
        (activity_range[0], activity_range[1]) if activity_range[0] else None,
        (sleep_range[0], sleep_range[1]) if sleep_range[0] else None
    ]
    
    # Filter out None values
    dates = [d for d in dates if d is not None]
    
    if not dates:
        return None, None
    
    earliest = min(d[0] for d in dates)
    latest = max(d[1] for d in dates)
    
    return earliest, latest

def get_smart_date_range(user_id):
    """Get a smart date range for displaying data"""
    earliest, latest = get_data_time_range(user_id)
    
    if not earliest or not latest:
        return None, None
    
    now = datetime.utcnow()
    
    # If we have data within the last 7 days, use that
    if latest >= now - timedelta(days=7):
        return now - timedelta(days=7), now
    
    # If we have data within the last 30 days, use that
    if latest >= now - timedelta(days=30):
        return now - timedelta(days=30), now
    
    # Otherwise, use the last 30 days of available data
    return latest - timedelta(days=30), latest

def get_data_freshness(user_id):
    """Get the freshness of the data"""
    _, latest = get_data_time_range(user_id)
    
    if not latest:
        return 'no_data'
    
    now = datetime.utcnow()
    age = now - latest
    
    if age.days == 0:
        return 'today'
    elif age.days == 1:
        return 'yesterday'
    elif age.days <= 7:
        return 'recent'
    elif age.days <= 30:
        return 'old'
    else:
        return 'very_old' 
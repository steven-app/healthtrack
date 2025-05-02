from datetime import datetime, timedelta
import calendar

def get_current_time():
    """Get current UTC time"""
    return datetime.utcnow()

def get_date_n_days_ago(days=0):
    """Get date n days ago"""
    return get_current_time() - timedelta(days=days)

def format_date(date_obj, format_str="%Y-%m-%d"):
    """Format a date object to string"""
    if not date_obj:
        return None
    return date_obj.strftime(format_str)

def format_datetime(datetime_obj, format_str="%Y-%m-%d %H:%M:%S"):
    """Format a datetime object to string"""
    if not datetime_obj:
        return None
    return datetime_obj.strftime(format_str)

def parse_date(date_str, format_str="%Y-%m-%d"):
    """Parse a date string to a date object"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, format_str).date()
    except ValueError:
        return None

def parse_datetime(datetime_str, format_str="%Y-%m-%d %H:%M:%S"):
    """Parse a datetime string to a datetime object"""
    if not datetime_str:
        return None
    try:
        return datetime.strptime(datetime_str, format_str)
    except ValueError:
        return None

def get_start_of_day(date_obj=None):
    """Get the start of the day (00:00:00)"""
    if date_obj is None:
        date_obj = get_current_time()
    return date_obj.replace(hour=0, minute=0, second=0, microsecond=0)

def get_end_of_day(date_obj=None):
    """Get the end of the day (23:59:59)"""
    if date_obj is None:
        date_obj = get_current_time()
    return date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)

def get_start_of_week(date_obj=None):
    """Get the start of the week (Monday)"""
    if date_obj is None:
        date_obj = get_current_time()
    start_of_day = get_start_of_day(date_obj)
    return start_of_day - timedelta(days=start_of_day.weekday())

def get_end_of_week(date_obj=None):
    """Get the end of the week (Sunday)"""
    start_of_week = get_start_of_week(date_obj)
    return get_end_of_day(start_of_week + timedelta(days=6))

def get_start_of_month(date_obj=None):
    """Get the start of the month"""
    if date_obj is None:
        date_obj = get_current_time()
    return date_obj.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def get_end_of_month(date_obj=None):
    """Get the end of the month"""
    if date_obj is None:
        date_obj = get_current_time()
    last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
    return date_obj.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

def is_date_in_range(date_obj, start_date, end_date):
    """Check if a date is within a date range"""
    return start_date <= date_obj <= end_date

def get_date_difference(date1, date2):
    """Get the difference between two dates in days"""
    return abs((date1 - date2).days)

def humanize_datetime(dt):
    """Convert a datetime to a human-readable format"""
    now = get_current_time()
    diff = now - dt
    
    if diff.days == 0:
        seconds = diff.seconds
        if seconds < 60:
            return f"{seconds} seconds ago"
        elif seconds < 3600:
            return f"{seconds // 60} minutes ago"
        else:
            return f"{seconds // 3600} hours ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days} days ago"
    elif diff.days < 30:
        return f"{diff.days // 7} weeks ago"
    elif diff.days < 365:
        return f"{diff.days // 30} months ago"
    else:
        return f"{diff.days // 365} years ago"

def get_date_str(date_obj=None, format_str="%Y-%m-%d"):
    """Get a formatted date string for the given date or current date"""
    if date_obj is None:
        date_obj = get_current_time()
    return format_date(date_obj, format_str) 
import os
from flask import Blueprint, jsonify, render_template, request, current_app, session
from flask_login import login_required, current_user
from app import db, cache
from app.models import Weight, HeartRate, Activity, Sleep
from app.models.goal import Goal
from app.models.achievement import Achievement, UserAchievement
from datetime import datetime, timedelta
import json
from collections import defaultdict
from sqlalchemy import func, text
from app.utils.data_utils import get_smart_date_range, get_data_freshness
from app.models.import_log import ImportLog
from flask import flash, url_for
from sqlalchemy.orm import load_only
import math  # Add math import

bp = Blueprint('dashboard', __name__)

# Function to invalidate dashboard cache for a user
def invalidate_dashboard_cache(user_id):
    """Invalidate all dashboard-related caches for a user"""
    # Get the days parameter or default to both 7 and 30 days views
    days_param = request.args.get('days', None)
    
    # If days parameter is provided, only invalidate that specific view
    if days_param:
        cache_keys = [
            f'dashboard_data_{user_id}_days_{days_param}',
            f'dashboard_summary_{user_id}_days_{days_param}',
            f'dashboard_goals_achievements_{user_id}_days_{days_param}'
        ]
    else:
        # Otherwise invalidate both 7 and 30 days views
        cache_keys = []
        for days in ['7', '30']:
            cache_keys.extend([
                f'dashboard_data_{user_id}_days_{days}',
                f'dashboard_summary_{user_id}_days_{days}',
                f'dashboard_goals_achievements_{user_id}_days_{days}'
            ])
    
    for key in cache_keys:
        current_app.logger.info(f"Invalidating cache for key: {key}")
        cache.delete(key)

# Move SafeJSONEncoder to the top level for reuse
class SafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            # Check for NaN and Infinity values
            if math.isnan(obj) or math.isinf(obj):
                current_app.logger.warning(f"Found invalid numeric value: {obj}")
                return None
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
    
    def iterencode(self, obj, _one_shot=False):
        for chunk in super().iterencode(obj, _one_shot):
            # Replace NaN and Infinity with null in JSON
            chunk = chunk.replace('NaN', 'null').replace('Infinity', 'null').replace('-Infinity', 'null')
            yield chunk

def sanitize_for_json(obj):
    """Recursively sanitize a data structure for JSON serialization.
    Replaces NaN and Infinity values with None."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            current_app.logger.warning(f"Sanitized invalid float: {obj}")
            return None
        return obj
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

def process_weight_data(weights):
    """Process weight data for time-series display"""
    weight_by_date = []
    
    # Use a dictionary for faster lookups when grouping by date
    weight_dict = {}
    
    for weight in weights:
        date_str = weight.timestamp.strftime('%Y-%m-%d')
        
        # If we already have a weight for this date, only keep the latest one
        if date_str in weight_dict:
            # Compare timestamps and only keep the newer one
            if weight.timestamp > weight_dict[date_str]['timestamp']:
                weight_dict[date_str] = {
                    'date': date_str,
                    'value': float(weight.value),  # Ensure it's a float
                    'unit': weight.unit or 'kg',  # Provide default
                    'timestamp': weight.timestamp
                }
        else:
            weight_dict[date_str] = {
                'date': date_str,
                'value': float(weight.value),  # Ensure it's a float
                'unit': weight.unit or 'kg',  # Provide default
                'timestamp': weight.timestamp
            }
    
    # Convert dictionary to list and sort
    weight_by_date = list(weight_dict.values())
    weight_by_date.sort(key=lambda x: x['date'])
    
    # Only return the last 30 days of data for dashboard display
    result = weight_by_date[-30:] if len(weight_by_date) > 30 else weight_by_date
    
    # Remove timestamp (we don't need it on the frontend)
    for item in result:
        if 'timestamp' in item:
            del item['timestamp']
    
    return result

def process_heart_rate_data(heart_rates):
    """Process heart rate data for time-series display"""
    # Group by date more efficiently with a dictionary
    heart_rate_by_date_dict = defaultdict(list)
    
    for hr in heart_rates:
        date_str = hr.timestamp.strftime('%Y-%m-%d')
        heart_rate_by_date_dict[date_str].append(hr.value)
    
    # Calculate daily min, max, avg more efficiently
    heart_rate_by_date = []
    for date_str, values in heart_rate_by_date_dict.items():
        if values:
            heart_rate_by_date.append({
                'date': date_str,
                'min': min(values),
                'max': max(values),
                'avg': round(sum(values) / len(values)),
                'unit': heart_rates[0].unit if heart_rates else 'bpm'
            })
    
    # Sort by date and limit to most recent 30 days
    heart_rate_by_date.sort(key=lambda x: x['date'])
    return heart_rate_by_date[-30:] if len(heart_rate_by_date) > 30 else heart_rate_by_date

def process_activity_data(activities):
    """Process activity data for time-series display"""
    # Group steps by date efficiently with dictionary
    steps_by_date_dict = defaultdict(int)
    
    for activity in activities:
        if activity.activity_type in ('steps', 'walking'):
            date_str = activity.timestamp.strftime('%Y-%m-%d')
            steps_by_date_dict[date_str] += activity.value
    
    # Convert to list format
    activity_by_date = [
        {'date': date_str, 'steps': steps} 
        for date_str, steps in steps_by_date_dict.items()
    ]
    
    # Sort by date and limit to most recent 30 days
    activity_by_date.sort(key=lambda x: x['date'])
    return activity_by_date[-30:] if len(activity_by_date) > 30 else activity_by_date

def process_sleep_data(sleeps):
    """Process sleep data for time-series display"""
    # Use a dictionary for faster lookups
    sleep_dict = {}
    
    for sleep in sleeps:
        date_str = sleep.timestamp.strftime('%Y-%m-%d')
        
        # For each date, keep the record with longest duration
        if date_str in sleep_dict:
            if sleep.duration > sleep_dict[date_str]['duration']:
                sleep_dict[date_str] = {
                    'date': date_str,
                    'duration': float(sleep.duration),  # Ensure it's a float
                    'durationHours': round(float(sleep.duration) / 60, 1),  # Ensure it's a float
                    'quality': sleep.quality or ''  # Ensure it's not None
                }
        else:
            sleep_dict[date_str] = {
                'date': date_str,
                'duration': float(sleep.duration),  # Ensure it's a float
                'durationHours': round(float(sleep.duration) / 60, 1),  # Ensure it's a float
                'quality': sleep.quality or ''  # Ensure it's not None
            }
    
    # Convert to list and sort
    sleep_by_date = list(sleep_dict.values())
    sleep_by_date.sort(key=lambda x: x['date'])
    
    # Only return the most recent 30 days
    return sleep_by_date[-30:] if len(sleep_by_date) > 30 else sleep_by_date

def calculate_summary(weights, heart_rates, activities, sleeps):
    """Calculate summary statistics for the dashboard."""
    summary = {}
    
    # Weight summary
    if weights:
        try:
            latest_weight = weights[0].value if hasattr(weights[0], 'value') else 0
            
            # Check for at least 2 weights to calculate change
            if len(weights) >= 2:
                first_weight = weights[-1].value if hasattr(weights[-1], 'value') else 0
                weight_change = latest_weight - first_weight
                
                # Avoid division by zero
                if first_weight != 0:
                    weight_change_percent = (weight_change / first_weight) * 100
                else:
                    weight_change_percent = 0
                    current_app.logger.warning("Avoided division by zero in weight change percent calculation")
            else:
                weight_change = 0
                weight_change_percent = 0
                
            summary['weight'] = {
                'latest': safe_number(latest_weight),
                'change': safe_number(weight_change),
                'change_percent': safe_number(weight_change_percent)
            }
        except Exception as e:
            current_app.logger.error(f"Error calculating weight summary: {str(e)}")
            summary['weight'] = {'latest': 0, 'change': 0, 'change_percent': 0}
    
    # Heart Rate summary
    if heart_rates:
        try:
            heart_values = [hr.value for hr in heart_rates if hasattr(hr, 'value') and hr.value is not None]
            if heart_values:
                min_hr = min(heart_values)
                max_hr = max(heart_values)
                avg_hr = sum(heart_values) / len(heart_values)
            else:
                min_hr = max_hr = avg_hr = 0
                
            summary['heart_rate'] = {
                'min': safe_number(min_hr),
                'max': safe_number(max_hr),
                'avg': safe_number(avg_hr)
            }
        except Exception as e:
            current_app.logger.error(f"Error calculating heart rate summary: {str(e)}")
            summary['heart_rate'] = {'min': 0, 'max': 0, 'avg': 0}
    
    # Activity summary
    if activities:
        try:
            # Group activities by day
            daily_activities = defaultdict(list)
            for activity in activities:
                if hasattr(activity, 'timestamp') and hasattr(activity, 'value'):
                    day = activity.timestamp.date()
                    daily_activities[day].append(activity.value)
            
            # Calculate daily totals
            daily_totals = {}
            for day, values in daily_activities.items():
                daily_totals[day] = sum(values)
            
            if daily_totals:
                days = len(daily_totals)
                total_steps = sum(daily_totals.values())
                
                # Avoid division by zero
                if days > 0:
                    avg_steps = total_steps / days
                else:
                    avg_steps = 0
                    current_app.logger.warning("Avoided division by zero in avg steps calculation")
                    
                best_day = max(daily_totals.values()) if daily_totals else 0
            else:
                total_steps = avg_steps = best_day = 0
                
            summary['activity'] = {
                'total_steps': safe_number(total_steps),
                'avg_steps': safe_number(avg_steps),
                'best_day': safe_number(best_day)
            }
        except Exception as e:
            current_app.logger.error(f"Error calculating activity summary: {str(e)}")
            summary['activity'] = {'total_steps': 0, 'avg_steps': 0, 'best_day': 0}
    
    # Sleep summary
    if sleeps:
        try:
            # Calculate average and best sleep duration
            durations = [sleep.duration for sleep in sleeps if hasattr(sleep, 'duration') and sleep.duration is not None]
            
            if durations:
                avg_duration = sum(durations) / len(durations)
                best_duration = max(durations)
                
                # Convert to hours
                avg_duration_hours = avg_duration / 60
                best_duration_hours = best_duration / 60
            else:
                avg_duration = best_duration = 0
                avg_duration_hours = best_duration_hours = 0
                
            summary['sleep'] = {
                'avg_duration': safe_number(avg_duration),
                'avg_duration_hours': safe_number(avg_duration_hours),
                'best_duration': safe_number(best_duration),
                'best_duration_hours': safe_number(best_duration_hours)
            }
            
            # Count sleep quality distribution
            if hasattr(sleeps[0], 'quality'):
                quality_count = {'poor': 0, 'fair': 0, 'good': 0, 'excellent': 0}
                for sleep in sleeps:
                    if sleep.quality in quality_count:
                        quality_count[sleep.quality] += 1
                
                # Add quality distribution to summary
                summary['sleep']['quality'] = quality_count
        except Exception as e:
            current_app.logger.error(f"Error calculating sleep summary: {str(e)}")
            summary['sleep'] = {
                'avg_duration': 0, 
                'avg_duration_hours': 0,
                'best_duration': 0,
                'best_duration_hours': 0,
                'quality': {'poor': 0, 'fair': 0, 'good': 0, 'excellent': 0}
            }
    
    current_app.logger.debug(f"Calculated summary: {summary}")
    return summary

# Helper function to safely convert numeric values
def safe_number(value, default=0):
    """Convert value to float, handling NaN and Infinity by returning default"""
    if value is None:
        return default
    try:
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            current_app.logger.warning(f"Converting invalid numeric value to default: {value} -> {default}")
            return default
        return float_val
    except (ValueError, TypeError) as e:
        current_app.logger.warning(f"Error converting value '{value}' to float: {str(e)}")
        return default

def json_response(data, status=200):
    """Create a standardized JSON response that handles NaN/Infinity values"""
    # First sanitize the data
    sanitized_data = sanitize_for_json(data)
    
    # Use our custom JSON encoder
    json_text = json.dumps(sanitized_data, cls=SafeJSONEncoder)
    
    # Validate JSON (debug only)
    try:
        json.loads(json_text)
    except Exception as e:
        current_app.logger.error(f"Generated invalid JSON despite sanitization: {str(e)}")
        # Last resort fallback - return empty object
        json_text = "{}"
    
    return current_app.response_class(
        json_text,
        mimetype='application/json',
        status=status
    )

@bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard_data():
    """Get dashboard data for the current user."""
    # Clear any flash messages if directly accessing dashboard (not coming from login page)
    # This helps prevent "Login successful!" message appearing repeatedly
    if '_flashes' in session:
        # Only keep flashes if we're redirecting directly from login page
        if not request.referrer or 'login' not in request.referrer:
            session.pop('_flashes', None)
    
    user_id = current_user.id
    
    # Get days parameter first so we can preserve it during refresh
    days_ago = int(request.args.get('days', 7))  # Default to 7 days, but allow URL parameter override
    
    # 检查是否需要强制刷新缓存
    force_refresh = request.args.get('refresh') == '1'
    
    # Only try cache if not forcing refresh
    if not force_refresh:
        cache_key = f'dashboard_data_{user_id}_days_{days_ago}'
        cached_data = cache.get(cache_key)
        if cached_data:
            current_app.logger.info(f"Using cached dashboard data for user_id: {user_id}, days: {days_ago}")
            return cached_data
    else:
        current_app.logger.info(f"Forcing cache refresh for dashboard data, user_id: {user_id}, days: {days_ago}")
    
    try:
        # Use the days parameter we got earlier
        thirty_days_ago = datetime.now() - timedelta(days=days_ago)
        
        # Debug output
        current_app.logger.info(f"Starting dashboard data fetch for user_id: {user_id}, last {days_ago} days")
        
        # First, check if we have any data for this user at all
        total_records = db.session.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM weights WHERE user_id = :user_id) as weight_count,
                (SELECT COUNT(*) FROM heart_rates WHERE user_id = :user_id) as heart_rate_count,
                (SELECT COUNT(*) FROM activities WHERE user_id = :user_id) as activity_count,
                (SELECT COUNT(*) FROM sleeps WHERE user_id = :user_id) as sleep_count
        """), {'user_id': user_id}).fetchone()
        
        current_app.logger.info(f"Total records for user {user_id}: weights={total_records.weight_count}, "
                              f"heart_rates={total_records.heart_rate_count}, "
                              f"activities={total_records.activity_count}, "
                              f"sleeps={total_records.sleep_count}")
        
        # Optimize queries: select only needed columns and use indexing
        # For weights, only need recent data with timestamp, value, unit
        weights = db.session.query(Weight).filter(
            Weight.user_id == user_id,
            Weight.timestamp >= thirty_days_ago
        ).options(
            load_only(Weight.id, Weight.timestamp, Weight.value, Weight.unit)
        ).order_by(Weight.timestamp.desc()).limit(100).all()
        
        current_app.logger.info(f"Retrieved {len(weights)} weight records")
        
        # Process weights data
        weight_by_date = process_weight_data(weights)
        current_app.logger.info(f"Processed {len(weight_by_date)} weight data points")
        
        # Use native SQL for heart rate aggregation for better performance
        # This pre-aggregates data by day directly in the database
        try:
            heart_rate_stats = db.session.execute(text("""
                SELECT 
                    DATE(timestamp) as date,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    AVG(value) as avg_value,
                    unit
                FROM heart_rates
                WHERE user_id = :user_id AND timestamp >= :start_date
                GROUP BY DATE(timestamp), unit
                ORDER BY date DESC
                LIMIT 100
            """), {
                'user_id': user_id,
                'start_date': thirty_days_ago
            }).fetchall()
            
            current_app.logger.info(f"Retrieved {len(heart_rate_stats) if heart_rate_stats else 0} heart rate stats")
            
            # Convert SQL results to expected format
            heart_rate_by_date = [
                {
                    'date': str(row.date) if hasattr(row, 'date') else '',
                    'min': float(row.min_value) if hasattr(row, 'min_value') and row.min_value is not None else 0,
                    'max': float(row.max_value) if hasattr(row, 'max_value') and row.max_value is not None else 0,
                    'avg': round(float(row.avg_value)) if hasattr(row, 'avg_value') and row.avg_value is not None else 0,
                    'unit': row.unit if hasattr(row, 'unit') else 'bpm'
                }
                for row in heart_rate_stats
            ]
            current_app.logger.info(f"Processed {len(heart_rate_by_date)} heart rate data points")
            
            # Debug output of data format
            if heart_rate_by_date:
                current_app.logger.info(f"Sample heart rate data point: {heart_rate_by_date[0]}")
        except Exception as e:
            current_app.logger.error(f"Error processing heart rate data: {str(e)}")
            heart_rate_by_date = []
        
        # Pre-aggregate activity data by day in the database
        try:
            # First check all activity types in the database for this user
            activity_types = db.session.execute(text("""
                SELECT DISTINCT activity_type 
                FROM activities 
                WHERE user_id = :user_id
            """), {'user_id': user_id}).fetchall()
            
            activity_type_list = [row[0] for row in activity_types]
            current_app.logger.info(f"Activity types for user {user_id}: {activity_type_list}")
            
            # Use more inclusive filter if we don't have steps or walking activities
            if not any(a_type in ['steps', 'walking'] for a_type in activity_type_list) and activity_type_list:
                activity_type_filter = f"activity_type IN ({', '.join(['?']*len(activity_type_list))})"
                params = {
                    'user_id': user_id,
                    'start_date': thirty_days_ago
                }
                # Add activity types as parameters
                for i, a_type in enumerate(activity_type_list):
                    params[f'type_{i}'] = a_type
                
                current_app.logger.info(f"Using all activity types: {activity_type_list}")
            else:
                activity_type_filter = "activity_type IN ('steps', 'walking')"
                params = {
                    'user_id': user_id,
                    'start_date': thirty_days_ago
                }
                current_app.logger.info("Using default 'steps' and 'walking' activity types")
            
            # Query with more lenient activity type filter
            activity_query = f"""
                SELECT 
                    DATE(timestamp) as date,
                    SUM(value) as total_steps
                FROM activities
                WHERE 
                    user_id = :user_id AND 
                    timestamp >= :start_date
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                LIMIT 100
            """
            
            current_app.logger.info(f"Activity query: {activity_query}")
            activity_stats = db.session.execute(text(activity_query), params).fetchall()
            
            current_app.logger.info(f"Retrieved {len(activity_stats) if activity_stats else 0} activity stats")
            
            activity_by_date = [
                {
                    'date': str(row.date) if hasattr(row, 'date') else '',
                    'steps': float(row.total_steps) if hasattr(row, 'total_steps') and row.total_steps is not None else 0
                }
                for row in activity_stats
            ]
            
            # Debug output of data format
            if activity_by_date:
                current_app.logger.info(f"Sample activity data point: {activity_by_date[0]}")
        except Exception as e:
            current_app.logger.error(f"Error processing activity data: {str(e)}")
            activity_by_date = []
        
        # Get sleep data with optimized query
        # Only select necessary columns
        sleeps = db.session.query(Sleep).filter(
            Sleep.user_id == user_id,
            Sleep.timestamp >= thirty_days_ago
        ).options(
            load_only(Sleep.id, Sleep.timestamp, Sleep.duration, Sleep.quality)
        ).order_by(Sleep.timestamp.desc()).limit(100).all()
        
        current_app.logger.info(f"Retrieved {len(sleeps)} sleep records")
        
        sleep_by_date = process_sleep_data(sleeps)
        current_app.logger.info(f"Processed {len(sleep_by_date)} sleep data points")
        
        # Get 5 most recent import logs (reduced from 10)
        import_logs = db.session.query(ImportLog).filter(
            ImportLog.user_id == user_id
        ).options(
            load_only(ImportLog.id, ImportLog.created_at, ImportLog.file_name, ImportLog.status)
        ).order_by(ImportLog.created_at.desc()).limit(5).all()
        
        current_app.logger.info(f"Retrieved {len(import_logs)} import logs")
        
        # Calculate summary with limited data
        heart_rates = db.session.query(HeartRate).filter(
            HeartRate.user_id == user_id,
            HeartRate.timestamp >= thirty_days_ago
        ).options(
            load_only(HeartRate.id, HeartRate.timestamp, HeartRate.value, HeartRate.unit)
        ).order_by(HeartRate.timestamp.desc()).limit(100).all()
        
        activities = db.session.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.activity_type.in_(['steps', 'walking']),
            Activity.timestamp >= thirty_days_ago
        ).options(
            load_only(Activity.id, Activity.timestamp, Activity.value, Activity.activity_type)
        ).order_by(Activity.timestamp.desc()).limit(100).all()
        
        # Calculate summary with our already fetched data
        summary = calculate_summary(weights, heart_rates, activities, sleeps)
        
        # Ensure summary values are all JSON serializable
        if 'weight' in summary:
            if 'latest' in summary['weight']:
                summary['weight']['latest'] = float(summary['weight']['latest'])
            if 'change' in summary['weight']:
                summary['weight']['change'] = float(summary['weight']['change']) 
            if 'change_percent' in summary['weight']:
                summary['weight']['change_percent'] = float(summary['weight']['change_percent'])
                
        if 'heart_rate' in summary:
            if 'avg' in summary['heart_rate']:
                summary['heart_rate']['avg'] = float(summary['heart_rate']['avg'])
            if 'min' in summary['heart_rate']:
                summary['heart_rate']['min'] = float(summary['heart_rate']['min'])
            if 'max' in summary['heart_rate']:
                summary['heart_rate']['max'] = float(summary['heart_rate']['max'])
                
        if 'activity' in summary:
            if 'avg_steps' in summary['activity']:
                summary['activity']['avg_steps'] = float(summary['activity']['avg_steps'])
            if 'total_steps' in summary['activity']:
                summary['activity']['total_steps'] = float(summary['activity']['total_steps'])
            if 'best_day' in summary['activity']:
                summary['activity']['best_day'] = float(summary['activity']['best_day'])
                
        if 'sleep' in summary:
            if 'avg_duration' in summary['sleep']:
                summary['sleep']['avg_duration'] = float(summary['sleep']['avg_duration'])
            if 'avg_duration_hours' in summary['sleep']:
                summary['sleep']['avg_duration_hours'] = float(summary['sleep']['avg_duration_hours'])
            if 'best_duration' in summary['sleep']:
                summary['sleep']['best_duration'] = float(summary['sleep']['best_duration'])
            if 'best_duration_hours' in summary['sleep']:
                summary['sleep']['best_duration_hours'] = float(summary['sleep']['best_duration_hours'])
        
        # Safe import logs conversion - handles possible non-serializable values
        recent_imports = []
        for log in import_logs:
            try:
                log_dict = log.to_dict()
                recent_imports.append(log_dict)
            except Exception as e:
                current_app.logger.error(f"Error converting import log to dict: {str(e)}")
                # Add a simplified version
                recent_imports.append({
                    'id': log.id,
                    'file_name': log.file_name,
                    'status': log.status,
                    'created_at': log.created_at.isoformat() if log.created_at else None
                })
                
        # Create response data
        data = {
            'weights': weight_by_date,
            'heartRates': heart_rate_by_date,
            'activities': activity_by_date,
            'sleeps': sleep_by_date,
            'summary': summary,
            'recentImports': recent_imports
        }
        
        # Debug data structure
        current_app.logger.info(f"Dashboard data structure: weights={len(data['weights'])}, "
                               f"heartRates={len(data['heartRates'])}, "
                               f"activities={len(data['activities'])}, "
                               f"sleeps={len(data['sleeps'])}")
        
        # Check if we have any data to display
        has_data = True  # 强制设置为True，因为我们已经确认有数据
        
        # Return JSON for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return json_response(data)
        
        # Render template for regular requests
        # 添加JSON数据直接传递给模板
        data_json = json.dumps(data, cls=SafeJSONEncoder)
        current_app.logger.info(f"Passing JSON data to template: {len(data_json)} bytes")
        
        # Create the response
        response = render_template('dashboard/index.html', 
                             data=data, 
                             has_data=has_data,
                             data_json=data_json)
                             
        # Cache the response if not forcing refresh
        if not force_refresh:
            cache_key = f'dashboard_data_{user_id}_days_{days_ago}'
            current_app.logger.info(f"Caching dashboard data with key: {cache_key}")
            cache.set(cache_key, response, timeout=900)
            
        return response
        
    except Exception as e:
        error_msg = f"Error fetching dashboard data: {str(e)}"
        current_app.logger.error(error_msg)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return json_response({'error': error_msg}, 500)
        
        flash('Error loading dashboard data. Please try again later.', 'danger')
        empty_data = {
            'weights': [],
            'heartRates': [],
            'activities': [],
            'sleeps': [],
            'summary': {
                'weight': {'latest': 0},
                'heart_rate': {'min': 0, 'max': 0, 'avg': 0},
                'activity': {'total_steps': 0, 'avg_steps': 0},
                'sleep': {'avg_duration_hours': 0}
            }
        }
        empty_json = json.dumps(empty_data)
        return render_template('dashboard/index.html', data=empty_data, has_data=True, data_json=empty_json)

@bp.route('/dashboard/summary', methods=['GET'])
@login_required
def get_dashboard_summary():
    """Get summary data for dashboard."""
    user_id = current_user.id
    
    # Get days parameter to preserve in the cache key
    days_param = request.args.get('days', '7')
    
    # 检查是否需要强制刷新缓存
    force_refresh = request.args.get('refresh') == '1'
    
    # Only try cache if not forcing refresh
    if not force_refresh:
        cache_key = f'dashboard_summary_{user_id}_days_{days_param}'
        cached_data = cache.get(cache_key)
        if cached_data:
            current_app.logger.info(f"Using cached dashboard summary for user_id: {user_id}, days: {days_param}")
            return cached_data
    else:
        current_app.logger.info(f"Forcing cache refresh for dashboard summary, user_id: {user_id}, days: {days_param}")
    
    try:
        # Use the provided days parameter or default to 7
        days = int(days_param)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Calculate multiple metrics in a single query for efficiency
        summary_stats = db.session.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM weights WHERE user_id = :user_id AND timestamp >= :start_date) as weight_count,
                (SELECT COUNT(*) FROM heart_rates WHERE user_id = :user_id AND timestamp >= :start_date) as heart_rate_count,
                (SELECT COUNT(*) FROM activities WHERE user_id = :user_id AND timestamp >= :start_date) as activity_count,
                (SELECT COUNT(*) FROM sleeps WHERE user_id = :user_id AND timestamp >= :start_date) as sleep_count,
                (SELECT AVG(value) FROM activities 
                 WHERE user_id = :user_id AND timestamp >= :start_date 
                 AND activity_type IN ('steps', 'walking')
                 LIMIT 1000) as avg_steps,
                (SELECT COUNT(*) FROM goals WHERE user_id = :user_id AND completed = 0) as active_goals
        """), {
            'user_id': current_user.id,
            'start_date': start_date
        }).fetchone()
        
        # Calculate summary statistics
        summary = {
            'total_records': safe_number(
                (summary_stats.weight_count or 0) + 
                (summary_stats.heart_rate_count or 0) + 
                (summary_stats.activity_count or 0) + 
                (summary_stats.sleep_count or 0)
            ),
            'data_types': 4,  # weight, heart_rate, activity, sleep
            'latest_update': end_date.isoformat(),
            'avg_steps': safe_number(summary_stats.avg_steps or 0),
            'active_goals': safe_number(summary_stats.active_goals or 0)
        }
        
        # Debug the summary before returning
        current_app.logger.debug(f"Dashboard summary before JSON encoding: {summary}")
        
        # Create response
        response = json_response({'success': True, 'summary': summary})
        
        # Cache response if not forcing refresh
        if not force_refresh:
            cache_key = f'dashboard_summary_{user_id}_days_{days_param}'
            current_app.logger.info(f"Caching dashboard summary with key: {cache_key}")
            cache.set(cache_key, response, timeout=300)
            
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error in dashboard summary: {str(e)}")
        return json_response({
            'success': False,
            'message': str(e)
        }, 500)

@bp.route('/dashboard/goals-achievements', methods=['GET'])
@login_required
def get_dashboard_goals_achievements():
    """Get goals and achievements data for dashboard"""
    
    # Get days parameter to preserve in the cache key
    days_param = request.args.get('days', '7')
    
    # 检查是否需要强制刷新缓存
    force_refresh = request.args.get('refresh') == '1'
    
    # Only try cache if not forcing refresh
    if not force_refresh:
        cache_key = f'dashboard_goals_achievements_{current_user.id}_days_{days_param}'
        cached_data = cache.get(cache_key)
        if cached_data:
            current_app.logger.info(f"Using cached dashboard goals/achievements for user_id: {current_user.id}, days: {days_param}")
            return cached_data
    else:
        current_app.logger.info(f"Forcing cache refresh for dashboard goals/achievements, user_id: {current_user.id}, days: {days_param}")
    
    try:
        user_id = current_user.id
        
        # Get active goals for the user
        active_goals = db.session.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.completed == False
        ).order_by(Goal.updated_at.desc()).limit(5).all()
        
        # Get recent achievements for the user
        recent_achievements_query = db.session.query(
            UserAchievement,
            Achievement
        ).join(
            Achievement, UserAchievement.achievement_id == Achievement.id
        ).filter(
            UserAchievement.user_id == user_id
        ).order_by(
            UserAchievement.earned_at.desc()
        ).limit(6)
        
        recent_achievements = []
        for ua, achievement in recent_achievements_query:
            recent_achievements.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon or 'medal',
                'level': achievement.level or 'bronze',
                'earned_at': ua.earned_at
            })
        
        # Convert goals to dicts for serialization
        goals_data = [goal.to_dict() for goal in active_goals]
        
        # Create response
        response = render_template('dashboard/_goals_achievements.html',
                             active_goals=active_goals,
                             recent_achievements=recent_achievements)
        
        # Cache response if not forcing refresh
        if not force_refresh:
            cache_key = f'dashboard_goals_achievements_{user_id}_days_{days_param}'
            current_app.logger.info(f"Caching dashboard goals/achievements with key: {cache_key}")
            cache.set(cache_key, response, timeout=300)
            
        return response
                             
    except Exception as e:
        current_app.logger.error(f"Error fetching goals and achievements: {str(e)}")
        return render_template('dashboard/_goals_achievements.html',
                             active_goals=[],
                             recent_achievements=[]) 
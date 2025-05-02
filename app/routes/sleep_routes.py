from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Sleep
from datetime import datetime, timedelta
from sqlalchemy import func
import calendar
from app.utils.chart_utils import get_time_range, generate_time_slots, format_empty_data_structure, prepare_chart_data

bp = Blueprint('sleep', __name__)

from app import db # Import db instance

def get_sleep_data(user_id, start_date, end_date):
    """
    Get sleep data for the specified date range.
    Prioritizes Connect device data and returns a single record per day in MINUTES.
    Also converts unreasonably long sleep durations (>12 hours) to more realistic values.
    """
    # Query all sleep records, including notes field to check data source
    sleep_records = db.session.query(
        Sleep.timestamp,
        Sleep.duration,
        Sleep.deep_sleep,
        Sleep.light_sleep,
        Sleep.rem_sleep,
        Sleep.awake,
        Sleep.notes
    ).filter(
        Sleep.user_id == user_id,
        Sleep.timestamp >= start_date,
        Sleep.timestamp < end_date
    ).order_by(Sleep.timestamp).all()
    
    # Group by date, prioritizing data from Connect devices
    daily_data = {}
    
    for record in sleep_records:
        date = record.timestamp.date()
        is_connect = record.notes and "Connect" in record.notes
        
        # Skip unreasonably long sleep records (over 12 hours)
        if record.duration > 720:  # 720 minutes = 12 hours
            continue
            
        # If the date doesn't exist in the dictionary, or current record is from Connect device (prioritize)
        if date not in daily_data or is_connect:
            # Ensure all fields are populated, even if they are None
            daily_data[date] = {
                'total_duration': record.duration or 0,
                'deep_sleep': record.deep_sleep or 0,
                'light_sleep': record.light_sleep or 0,
                'rem_sleep': record.rem_sleep or 0,
                'awake': record.awake or 0
            }
    
    return daily_data  # Return daily sleep data (in minutes)

@bp.route('/sleep/daily')
@login_required
def daily():
    """Show daily sleep data in hours"""
    # Get today's time range
    start_date, end_date = get_time_range('daily')
    
    # Query today's sleep data
    sleep_records = db.session.query(
        Sleep.timestamp,
        Sleep.duration,
        Sleep.deep_sleep,
        Sleep.light_sleep,
        Sleep.rem_sleep,
        Sleep.awake,
        Sleep.notes
    ).filter(
        Sleep.user_id == current_user.id,
        Sleep.timestamp >= start_date,
        Sleep.timestamp < end_date
    ).order_by(Sleep.timestamp).all()
    
    # Generate time slots (hourly)
    time_slots = generate_time_slots('daily', start_date, end_date)
    
    # Initialize data structure
    hourly_data = {}
    for slot in time_slots:
        slot_key = slot['label']
        hourly_data[slot_key] = {
            'total_duration': 0,
            'deep_sleep': 0,
            'light_sleep': 0,
            'rem_sleep': 0,
            'awake': 0,
            'count': 0
        }
    
    # Aggregate sleep data by hour, keeping only valid records
    for record in sleep_records:
        # Skip unreasonably long sleep records (over 12 hours)
        if record.duration > 720:  # 720 minutes = 12 hours
            continue
        
        # Determine which time slot the record belongs to
        for slot in time_slots:
            if slot['start'] <= record.timestamp < slot['end']:
                slot_key = slot['label']
                is_connect = record.notes and "Connect" in record.notes
                
                # If the time slot has no data yet, or current record is from Connect device (prioritize)
                if hourly_data[slot_key]['count'] == 0 or is_connect:
                    hourly_data[slot_key]['total_duration'] = record.duration or 0
                    hourly_data[slot_key]['deep_sleep'] = record.deep_sleep or 0
                    hourly_data[slot_key]['light_sleep'] = record.light_sleep or 0
                    hourly_data[slot_key]['rem_sleep'] = record.rem_sleep or 0
                    hourly_data[slot_key]['awake'] = record.awake or 0
                    hourly_data[slot_key]['count'] += 1
                break
    
    # Convert minutes to hours
    for hour_key in hourly_data:
        hourly_data[hour_key]['total_duration'] = round(hourly_data[hour_key]['total_duration'] / 60, 1)
        hourly_data[hour_key]['deep_sleep'] = round(hourly_data[hour_key]['deep_sleep'] / 60, 1)
        hourly_data[hour_key]['light_sleep'] = round(hourly_data[hour_key]['light_sleep'] / 60, 1)
        hourly_data[hour_key]['rem_sleep'] = round(hourly_data[hour_key]['rem_sleep'] / 60, 1)
        hourly_data[hour_key]['awake'] = round(hourly_data[hour_key]['awake'] / 60, 1)
    
    # 准备图表数据
    labels = [slot['label'] for slot in time_slots]
    
    datasets_config = [
        {
            'metric': 'total_duration',
            'label': 'Total Sleep (hours)',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'deep_sleep',
            'label': 'Deep Sleep (hours)',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'light_sleep',
            'label': 'Light Sleep (hours)',
            'backgroundColor': 'rgba(255, 206, 86, 0.5)',
            'borderColor': 'rgba(255, 206, 86, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'rem_sleep',
            'label': 'REM Sleep (hours)',
            'backgroundColor': 'rgba(153, 102, 255, 0.5)',
            'borderColor': 'rgba(153, 102, 255, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'awake',
            'label': 'Awake (hours)',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(hourly_data, labels, datasets_config)
    
    return render_template('charts/base.html',
                         title='Daily Sleep (Hours)',
                         endpoint='sleep',
                         period='daily',
                         data=chart_data)

@bp.route('/sleep/weekly')
@login_required
def weekly():
    """Show sleep data for the past week"""
    # Get time range for the past week
    start_date, end_date = get_time_range('weekly')

    # Query sleep data
    sleep_records = db.session.query(
        Sleep.timestamp, 
        Sleep.duration,
        Sleep.deep_sleep,
        Sleep.light_sleep,
        Sleep.rem_sleep,
        Sleep.awake,
        Sleep.notes
    ).filter(
        Sleep.user_id == current_user.id,
        Sleep.timestamp >= start_date,
        Sleep.timestamp < end_date
    ).order_by(Sleep.timestamp).all()

    # Initialize empty data structure with metric keys
    metric_keys = ['total_duration', 'deep_sleep', 'light_sleep', 'rem_sleep', 'awake']
    daily_data, labels = format_empty_data_structure('weekly', metric_keys)
    
    # Aggregate sleep data by day
    for record in sleep_records:
        # Skip unreasonably long sleep records (over 12 hours)
        if record.duration > 720:  # 720 minutes = 12 hours
            continue
            
        # Determine which time slot this record belongs to
        for slot_label in daily_data:
            # Find the corresponding time slot
            slot = next((s for s in generate_time_slots('weekly', start_date, end_date) 
                       if s['label'] == slot_label), None)
            
            if slot and slot['start'] <= record.timestamp < slot['end']:
                # For each day, we take either the only record or the one from Connect device
                is_connect = record.notes and "Connect" in record.notes
                
                # Update values if this is the first record for this day or if it's from Connect
                if daily_data[slot_label]['count'] == 0 or is_connect:
                    daily_data[slot_label]['total_duration'] = record.duration or 0
                    daily_data[slot_label]['deep_sleep'] = record.deep_sleep or 0
                    daily_data[slot_label]['light_sleep'] = record.light_sleep or 0
                    daily_data[slot_label]['rem_sleep'] = record.rem_sleep or 0
                    daily_data[slot_label]['awake'] = record.awake or 0
                    daily_data[slot_label]['count'] = 1
                break
    
    # Convert minutes to hours for display
    for day_key in daily_data:
        if daily_data[day_key]['count'] > 0:
            daily_data[day_key]['total_duration'] = round(daily_data[day_key]['total_duration'] / 60, 1)
            daily_data[day_key]['deep_sleep'] = round(daily_data[day_key]['deep_sleep'] / 60, 1)
            daily_data[day_key]['light_sleep'] = round(daily_data[day_key]['light_sleep'] / 60, 1)
            daily_data[day_key]['rem_sleep'] = round(daily_data[day_key]['rem_sleep'] / 60, 1)
            daily_data[day_key]['awake'] = round(daily_data[day_key]['awake'] / 60, 1)
    
    # Prepare chart data configuration
    datasets_config = [
        {
            'metric': 'total_duration',
            'label': 'Total Sleep (hours)',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'deep_sleep',
            'label': 'Deep Sleep (hours)',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'light_sleep',
            'label': 'Light Sleep (hours)',
            'backgroundColor': 'rgba(255, 206, 86, 0.5)',
            'borderColor': 'rgba(255, 206, 86, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'rem_sleep',
            'label': 'REM Sleep (hours)',
            'backgroundColor': 'rgba(153, 102, 255, 0.5)',
            'borderColor': 'rgba(153, 102, 255, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'awake',
            'label': 'Awake (hours)',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(daily_data, labels, datasets_config)
    
    return render_template('charts/base.html',
                         title='Weekly Sleep (Hours)',
                         endpoint='sleep',
                         period='weekly',
                         data=chart_data)

@bp.route('/sleep/monthly')
@login_required
def monthly():
    """Show monthly sleep data"""
    # Get time range for the past month
    start_date, end_date = get_time_range('monthly')
    
    # Query sleep data
    sleep_records = db.session.query(
        Sleep.timestamp, 
        Sleep.duration,
        Sleep.deep_sleep,
        Sleep.light_sleep,
        Sleep.rem_sleep,
        Sleep.awake,
        Sleep.notes
    ).filter(
        Sleep.user_id == current_user.id,
        Sleep.timestamp >= start_date,
        Sleep.timestamp < end_date
    ).order_by(Sleep.timestamp).all()
    
    # Initialize empty data structure with metric keys
    metric_keys = ['total_duration', 'deep_sleep', 'light_sleep', 'rem_sleep', 'awake']
    daily_data, labels = format_empty_data_structure('monthly', metric_keys)
    
    # Aggregate sleep data by day
    for record in sleep_records:
        # Skip unreasonably long sleep records (over 12 hours)
        if record.duration > 720:  # 720 minutes = 12 hours
            continue
            
        # Determine which time slot this record belongs to
        for slot_label in daily_data:
            # Find the corresponding time slot
            slot = next((s for s in generate_time_slots('monthly', start_date, end_date) 
                       if s['label'] == slot_label), None)
            
            if slot and slot['start'] <= record.timestamp < slot['end']:
                # For each day, we take either the only record or the one from Connect device
                is_connect = record.notes and "Connect" in record.notes
                
                # Update values if this is the first record for this day or if it's from Connect
                if daily_data[slot_label]['count'] == 0 or is_connect:
                    daily_data[slot_label]['total_duration'] = record.duration or 0
                    daily_data[slot_label]['deep_sleep'] = record.deep_sleep or 0
                    daily_data[slot_label]['light_sleep'] = record.light_sleep or 0
                    daily_data[slot_label]['rem_sleep'] = record.rem_sleep or 0
                    daily_data[slot_label]['awake'] = record.awake or 0
                    daily_data[slot_label]['count'] = 1
                break
    
    # Convert minutes to hours for display
    for day_key in daily_data:
        if daily_data[day_key]['count'] > 0:
            daily_data[day_key]['total_duration'] = round(daily_data[day_key]['total_duration'] / 60, 1)
            daily_data[day_key]['deep_sleep'] = round(daily_data[day_key]['deep_sleep'] / 60, 1)
            daily_data[day_key]['light_sleep'] = round(daily_data[day_key]['light_sleep'] / 60, 1)
            daily_data[day_key]['rem_sleep'] = round(daily_data[day_key]['rem_sleep'] / 60, 1)
            daily_data[day_key]['awake'] = round(daily_data[day_key]['awake'] / 60, 1)
    
    # Prepare chart data configuration
    datasets_config = [
        {
            'metric': 'total_duration',
            'label': 'Total Sleep (hours)',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'deep_sleep',
            'label': 'Deep Sleep (hours)',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'light_sleep',
            'label': 'Light Sleep (hours)',
            'backgroundColor': 'rgba(255, 206, 86, 0.5)',
            'borderColor': 'rgba(255, 206, 86, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'rem_sleep',
            'label': 'REM Sleep (hours)',
            'backgroundColor': 'rgba(153, 102, 255, 0.5)',
            'borderColor': 'rgba(153, 102, 255, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'awake',
            'label': 'Awake (hours)',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(daily_data, labels, datasets_config)
    
    return render_template('charts/base.html',
                         title='Monthly Sleep (Hours)',
                         endpoint='sleep',
                         period='monthly',
                         data=chart_data)

@bp.route('/sleep/six_months')
@login_required
def six_months():
    """Show six months sleep data"""
    # Get time range for the past six months
    start_date, end_date = get_time_range('six_months')
    
    # Query sleep data
    sleep_records = db.session.query(
        Sleep.timestamp, 
        Sleep.duration,
        Sleep.deep_sleep,
        Sleep.light_sleep,
        Sleep.rem_sleep,
        Sleep.awake,
        Sleep.notes
    ).filter(
        Sleep.user_id == current_user.id,
        Sleep.timestamp >= start_date,
        Sleep.timestamp < end_date
    ).order_by(Sleep.timestamp).all()
    
    # Initialize empty data structure with metric keys
    metric_keys = ['total_duration', 'deep_sleep', 'light_sleep', 'rem_sleep', 'awake']
    weekly_data, labels = format_empty_data_structure('six_months', metric_keys)
    
    # Aggregate sleep data by week
    for record in sleep_records:
        # Skip unreasonably long sleep records (over 12 hours)
        if record.duration > 720:  # 720 minutes = 12 hours
            continue
            
        # Determine which time slot this record belongs to
        for slot_label in weekly_data:
            # Find the corresponding time slot
            slot = next((s for s in generate_time_slots('six_months', start_date, end_date) 
                       if s['label'] == slot_label), None)
            
            if slot and slot['start'] <= record.timestamp < slot['end']:
                # For each week, we aggregate data
                is_connect = record.notes and "Connect" in record.notes
                
                # For weekly aggregation, sum values and count records
                weekly_data[slot_label]['total_duration'] += record.duration or 0
                weekly_data[slot_label]['deep_sleep'] += record.deep_sleep or 0
                weekly_data[slot_label]['light_sleep'] += record.light_sleep or 0
                weekly_data[slot_label]['rem_sleep'] += record.rem_sleep or 0
                weekly_data[slot_label]['awake'] += record.awake or 0
                weekly_data[slot_label]['count'] += 1
                break
    
    # Calculate weekly averages and convert minutes to hours
    for week_key in weekly_data:
        if weekly_data[week_key]['count'] > 0:
            # Calculate average per day within each week
            weekly_data[week_key]['total_duration'] = round(weekly_data[week_key]['total_duration'] / weekly_data[week_key]['count'] / 60, 1)
            weekly_data[week_key]['deep_sleep'] = round(weekly_data[week_key]['deep_sleep'] / weekly_data[week_key]['count'] / 60, 1)
            weekly_data[week_key]['light_sleep'] = round(weekly_data[week_key]['light_sleep'] / weekly_data[week_key]['count'] / 60, 1)
            weekly_data[week_key]['rem_sleep'] = round(weekly_data[week_key]['rem_sleep'] / weekly_data[week_key]['count'] / 60, 1)
            weekly_data[week_key]['awake'] = round(weekly_data[week_key]['awake'] / weekly_data[week_key]['count'] / 60, 1)
    
    # Prepare chart data configuration
    datasets_config = [
        {
            'metric': 'total_duration',
            'label': 'Daily Avg Sleep (hours)',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'deep_sleep',
            'label': 'Daily Avg Deep Sleep (hours)',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'light_sleep',
            'label': 'Daily Avg Light Sleep (hours)',
            'backgroundColor': 'rgba(255, 206, 86, 0.5)',
            'borderColor': 'rgba(255, 206, 86, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'rem_sleep',
            'label': 'Daily Avg REM Sleep (hours)',
            'backgroundColor': 'rgba(153, 102, 255, 0.5)',
            'borderColor': 'rgba(153, 102, 255, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'awake',
            'label': 'Daily Avg Awake (hours)',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        }
    ]
    
    # Use sparse labels for better readability (show every 3rd label)
    chart_data = prepare_chart_data(weekly_data, labels, datasets_config, sparse_labels=True, label_interval=3)
    
    return render_template('charts/base.html',
                         title='Six Months Sleep (Daily Average)',
                         endpoint='sleep',
                         period='six_months',
                         data=chart_data)

@bp.route('/sleep/yearly')
@login_required
def yearly():
    """Show yearly sleep data"""
    # Get time range for the past year
    start_date, end_date = get_time_range('yearly')
    
    # Query sleep data
    sleep_records = db.session.query(
        Sleep.timestamp, 
        Sleep.duration,
        Sleep.deep_sleep,
        Sleep.light_sleep,
        Sleep.rem_sleep,
        Sleep.awake,
        Sleep.notes
    ).filter(
        Sleep.user_id == current_user.id,
        Sleep.timestamp >= start_date,
        Sleep.timestamp < end_date
    ).order_by(Sleep.timestamp).all()
    
    # Initialize empty data structure with metric keys
    metric_keys = ['total_duration', 'deep_sleep', 'light_sleep', 'rem_sleep', 'awake']
    monthly_data, labels = format_empty_data_structure('yearly', metric_keys)
    
    # Aggregate sleep data by month
    for record in sleep_records:
        # Skip unreasonably long sleep records (over 12 hours)
        if record.duration > 720:  # 720 minutes = 12 hours
            continue
            
        # Determine which time slot this record belongs to
        for slot_label in monthly_data:
            # Find the corresponding time slot
            slot = next((s for s in generate_time_slots('yearly', start_date, end_date) 
                       if s['label'] == slot_label), None)
            
            if slot and slot['start'] <= record.timestamp < slot['end']:
                # For each month, we aggregate data
                is_connect = record.notes and "Connect" in record.notes
                
                # For monthly aggregation, sum values and count records
                monthly_data[slot_label]['total_duration'] += record.duration or 0
                monthly_data[slot_label]['deep_sleep'] += record.deep_sleep or 0
                monthly_data[slot_label]['light_sleep'] += record.light_sleep or 0
                monthly_data[slot_label]['rem_sleep'] += record.rem_sleep or 0
                monthly_data[slot_label]['awake'] += record.awake or 0
                monthly_data[slot_label]['count'] += 1
                break
    
    # Calculate monthly averages and convert minutes to hours
    for month_key in monthly_data:
        if monthly_data[month_key]['count'] > 0:
            # Calculate average per day within each month
            monthly_data[month_key]['total_duration'] = round(monthly_data[month_key]['total_duration'] / monthly_data[month_key]['count'] / 60, 1)
            monthly_data[month_key]['deep_sleep'] = round(monthly_data[month_key]['deep_sleep'] / monthly_data[month_key]['count'] / 60, 1)
            monthly_data[month_key]['light_sleep'] = round(monthly_data[month_key]['light_sleep'] / monthly_data[month_key]['count'] / 60, 1)
            monthly_data[month_key]['rem_sleep'] = round(monthly_data[month_key]['rem_sleep'] / monthly_data[month_key]['count'] / 60, 1)
            monthly_data[month_key]['awake'] = round(monthly_data[month_key]['awake'] / monthly_data[month_key]['count'] / 60, 1)
    
    # Prepare chart data configuration
    datasets_config = [
        {
            'metric': 'total_duration',
            'label': 'Daily Avg Sleep (hours)',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'deep_sleep',
            'label': 'Daily Avg Deep Sleep (hours)',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'light_sleep',
            'label': 'Daily Avg Light Sleep (hours)',
            'backgroundColor': 'rgba(255, 206, 86, 0.5)',
            'borderColor': 'rgba(255, 206, 86, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'rem_sleep',
            'label': 'Daily Avg REM Sleep (hours)',
            'backgroundColor': 'rgba(153, 102, 255, 0.5)',
            'borderColor': 'rgba(153, 102, 255, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'awake',
            'label': 'Daily Avg Awake (hours)',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(monthly_data, labels, datasets_config)
    
    return render_template('charts/base.html',
                         title='Yearly Sleep (Daily Average)',
                         endpoint='sleep',
                         period='yearly',
                         data=chart_data)
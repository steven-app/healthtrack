from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Weight
from app.utils.date_utils import get_date_str
from app.utils.cache_utils import invalidate_dashboard_cache
from datetime import datetime, timedelta
from sqlalchemy import func
import calendar
from app.utils.chart_utils import get_time_range, generate_time_slots, format_empty_data_structure, prepare_chart_data

bp = Blueprint('weight', __name__, url_prefix='/weight')

def get_weight_data(user_id, start_date, end_date):
    """Get weight data for the specified date range"""
    weight_records = Weight.query.filter(
        Weight.user_id == user_id,
        Weight.timestamp >= start_date,
        Weight.timestamp <= end_date
    ).order_by(Weight.timestamp).all()
    
    # Group data by date
    data = {}
    for weight in weight_records:
        date = weight.timestamp.date()
        if date not in data:
            data[date] = {
                'value': weight.value,
                'count': 1
            }
        else:
            # If multiple records for same day, take average
            data[date]['value'] = (data[date]['value'] * data[date]['count'] + weight.value) / (data[date]['count'] + 1)
            data[date]['count'] += 1
    
    return data

@bp.route('/daily')
@login_required
def daily():
    """Show daily weight data"""
    # Get today's time range
    start_date, end_date = get_time_range('daily')
    
    # Query today's weight data
    weight_records = Weight.query.filter(
        Weight.user_id == current_user.id,
        Weight.timestamp >= start_date,
        Weight.timestamp < end_date
    ).order_by(Weight.timestamp).all()
    
    # Generate time slots (hourly)
    time_slots = generate_time_slots('daily', start_date, end_date)
    
    # Initialize data structure
    hourly_data = {}
    for slot in time_slots:
        slot_key = slot['label']
        hourly_data[slot_key] = {
            'weight': 0,
            'count': 0
        }
    
    # Aggregate weight data by hour
    for record in weight_records:
        # Find which time slot this record belongs to
        for slot in time_slots:
            if slot['start'] <= record.timestamp < slot['end']:
                slot_key = slot['label']
                
                # If the time slot already has data, calculate average
                if hourly_data[slot_key]['count'] > 0:
                    hourly_data[slot_key]['weight'] = (hourly_data[slot_key]['weight'] * hourly_data[slot_key]['count'] + record.value) / (hourly_data[slot_key]['count'] + 1)
                else:
                    hourly_data[slot_key]['weight'] = record.value
                
                hourly_data[slot_key]['count'] += 1
                break
    
    # Prepare chart data
    labels = [slot['label'] for slot in time_slots]
    
    datasets_config = [
        {
            'metric': 'weight',
            'label': 'Weight (kg)',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(hourly_data, labels, datasets_config)
    
    return render_template('charts/base.html',
                         title='Daily Weight',
                         endpoint='weight',
                         period='daily',
                         data=chart_data)

@bp.route('/weekly')
@login_required
def weekly():
    """Show weekly weight data"""
    # Get time range for the past week
    start_date, end_date = get_time_range('weekly')
    
    # Query weight data
    weight_records = Weight.query.filter(
        Weight.user_id == current_user.id,
        Weight.timestamp >= start_date,
        Weight.timestamp < end_date
    ).order_by(Weight.timestamp).all()
    
    # Initialize empty data structure with metric keys
    metric_keys = ['weight']
    daily_data, labels = format_empty_data_structure('weekly', metric_keys)
    
    # Aggregate weight data by day
    for record in weight_records:
        # Determine which time slot this record belongs to
        for slot_label in daily_data:
            # Find the corresponding time slot
            slot = next((s for s in generate_time_slots('weekly', start_date, end_date) 
                       if s['label'] == slot_label), None)
            
            if slot and slot['start'] <= record.timestamp < slot['end']:
                # For each day, aggregate data (calculate average if multiple records)
                if daily_data[slot_label]['count'] > 0:
                    # Calculate running average
                    daily_data[slot_label]['weight'] = (daily_data[slot_label]['weight'] * daily_data[slot_label]['count'] + record.value) / (daily_data[slot_label]['count'] + 1)
                else:
                    daily_data[slot_label]['weight'] = record.value
                
                daily_data[slot_label]['count'] += 1
                break
    
    # Round values for display
    for day_key in daily_data:
        if daily_data[day_key]['count'] > 0:
            daily_data[day_key]['weight'] = round(daily_data[day_key]['weight'], 1)
    
    # Prepare chart data configuration
    datasets_config = [
        {
            'metric': 'weight',
            'label': 'Weight (kg)',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(daily_data, labels, datasets_config)
    
    return render_template('charts/base.html',
                         title='Weekly Weight',
                         endpoint='weight',
                         period='weekly',
                         data=chart_data)

@bp.route('/monthly')
@login_required
def monthly():
    """Show monthly weight data"""
    # Get time range for the past month
    start_date, end_date = get_time_range('monthly')
    
    # Query weight data
    weight_records = Weight.query.filter(
        Weight.user_id == current_user.id,
        Weight.timestamp >= start_date,
        Weight.timestamp < end_date
    ).order_by(Weight.timestamp).all()
    
    # Initialize empty data structure with metric keys
    metric_keys = ['weight']
    daily_data, labels = format_empty_data_structure('monthly', metric_keys)
    
    # Aggregate weight data by day
    for record in weight_records:
        # Determine which time slot this record belongs to
        for slot_label in daily_data:
            # Find the corresponding time slot
            slot = next((s for s in generate_time_slots('monthly', start_date, end_date) 
                       if s['label'] == slot_label), None)
            
            if slot and slot['start'] <= record.timestamp < slot['end']:
                # For each day, aggregate data (calculate average if multiple records)
                if daily_data[slot_label]['count'] > 0:
                    # Calculate running average
                    daily_data[slot_label]['weight'] = (daily_data[slot_label]['weight'] * daily_data[slot_label]['count'] + record.value) / (daily_data[slot_label]['count'] + 1)
                else:
                    daily_data[slot_label]['weight'] = record.value
                
                daily_data[slot_label]['count'] += 1
                break
    
    # Round values for display
    for day_key in daily_data:
        if daily_data[day_key]['count'] > 0:
            daily_data[day_key]['weight'] = round(daily_data[day_key]['weight'], 1)
    
    # Prepare chart data configuration
    datasets_config = [
        {
            'metric': 'weight',
            'label': 'Weight (kg)',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(daily_data, labels, datasets_config)
    
    return render_template('charts/base.html',
                         title='Monthly Weight',
                         endpoint='weight',
                         period='monthly',
                         data=chart_data)

@bp.route('/six_months')
@login_required
def six_months():
    """Show six months weight data"""
    # Get time range for the past six months
    start_date, end_date = get_time_range('six_months')
    
    # Query weight data
    weight_records = Weight.query.filter(
        Weight.user_id == current_user.id,
        Weight.timestamp >= start_date,
        Weight.timestamp < end_date
    ).order_by(Weight.timestamp).all()
    
    # Initialize empty data structure with metric keys
    metric_keys = ['weight']
    weekly_data, labels = format_empty_data_structure('six_months', metric_keys)
    
    # Aggregate weight data by week
    for record in weight_records:
        # Determine which time slot this record belongs to
        for slot_label in weekly_data:
            # Find the corresponding time slot
            slot = next((s for s in generate_time_slots('six_months', start_date, end_date) 
                       if s['label'] == slot_label), None)
            
            if slot and slot['start'] <= record.timestamp < slot['end']:
                # For each week, aggregate data (calculate average if multiple records)
                if weekly_data[slot_label]['count'] > 0:
                    # Calculate running average
                    weekly_data[slot_label]['weight'] = (weekly_data[slot_label]['weight'] * weekly_data[slot_label]['count'] + record.value) / (weekly_data[slot_label]['count'] + 1)
                else:
                    weekly_data[slot_label]['weight'] = record.value
                
                weekly_data[slot_label]['count'] += 1
                break
    
    # Round values for display
    for week_key in weekly_data:
        if weekly_data[week_key]['count'] > 0:
            weekly_data[week_key]['weight'] = round(weekly_data[week_key]['weight'], 1)
    
    # Prepare chart data configuration
    datasets_config = [
        {
            'metric': 'weight',
            'label': 'Weight (kg)',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    # Use sparse labels for better readability (show every 3rd label)
    chart_data = prepare_chart_data(weekly_data, labels, datasets_config, sparse_labels=True, label_interval=3)
    
    return render_template('charts/base.html',
                         title='Six Months Weight',
                         endpoint='weight',
                         period='six_months',
                         data=chart_data)

@bp.route('/yearly')
@login_required
def yearly():
    """Show yearly weight data"""
    # Get time range for the past year
    start_date, end_date = get_time_range('yearly')
    
    # Query weight data
    weight_records = Weight.query.filter(
        Weight.user_id == current_user.id,
        Weight.timestamp >= start_date,
        Weight.timestamp < end_date
    ).order_by(Weight.timestamp).all()
    
    # Initialize empty data structure with metric keys
    metric_keys = ['weight']
    monthly_data, labels = format_empty_data_structure('yearly', metric_keys)
    
    # Aggregate weight data by month
    for record in weight_records:
        # Determine which time slot this record belongs to
        for slot_label in monthly_data:
            # Find the corresponding time slot
            slot = next((s for s in generate_time_slots('yearly', start_date, end_date) 
                       if s['label'] == slot_label), None)
            
            if slot and slot['start'] <= record.timestamp < slot['end']:
                # For each month, aggregate data (calculate average if multiple records)
                if monthly_data[slot_label]['count'] > 0:
                    # Calculate running average
                    monthly_data[slot_label]['weight'] = (monthly_data[slot_label]['weight'] * monthly_data[slot_label]['count'] + record.value) / (monthly_data[slot_label]['count'] + 1)
                else:
                    monthly_data[slot_label]['weight'] = record.value
                
                monthly_data[slot_label]['count'] += 1
                break
    
    # Round values for display
    for month_key in monthly_data:
        if monthly_data[month_key]['count'] > 0:
            monthly_data[month_key]['weight'] = round(monthly_data[month_key]['weight'], 1)
    
    # Prepare chart data configuration
    datasets_config = [
        {
            'metric': 'weight',
            'label': 'Weight (kg)',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(monthly_data, labels, datasets_config)
    
    return render_template('charts/base.html',
                         title='Yearly Weight',
                         endpoint='weight',
                         period='yearly',
                         data=chart_data) 
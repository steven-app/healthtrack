from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import HeartRate
from datetime import datetime, timedelta
from sqlalchemy import func
import calendar
from app.utils.chart_utils import get_time_range, generate_time_slots, format_empty_data_structure, prepare_chart_data

bp = Blueprint('heartbeats', __name__)

def get_heart_rate_data(user_id, start_date, end_date):
    """Get heart rate data for the specified date range"""
    heart_rates = HeartRate.query.filter(
        HeartRate.user_id == user_id,
        HeartRate.timestamp >= start_date,
        HeartRate.timestamp <= end_date
    ).order_by(HeartRate.timestamp).all()
    
    # Group data by date
    data = {}
    for hr in heart_rates:
        date = hr.timestamp.date()
        if date not in data:
            data[date] = {
                'min': float('inf'),
                'max': float('-inf'),
                'avg': 0,
                'count': 0,
                'total': 0
            }
        
        data[date]['min'] = min(data[date]['min'], hr.value)
        data[date]['max'] = max(data[date]['max'], hr.value)
        data[date]['total'] += hr.value
        data[date]['count'] += 1
    
    # Calculate averages
    for date in data:
        if data[date]['count'] > 0:
            data[date]['avg'] = round(data[date]['total'] / data[date]['count'], 1)
        if data[date]['min'] == float('inf'):
            data[date]['min'] = 0
        if data[date]['max'] == float('-inf'):
            data[date]['max'] = 0
    
    return data

@bp.route('/heartbeats/daily')
@login_required
def daily():
    """Show daily heart rate data"""
    # 获取今天的时间范围
    start_date, end_date = get_time_range('daily')
    
    # 获取心率数据
    heart_rates = HeartRate.query.filter(
        HeartRate.user_id == current_user.id,
        HeartRate.timestamp >= start_date,
        HeartRate.timestamp < end_date
    ).order_by(HeartRate.timestamp).all()
    
    # 生成时间槽（每小时）
    time_slots = generate_time_slots('daily', start_date, end_date)
    
    # 初始化数据结构
    hourly_data = {}
    for slot in time_slots:
        slot_key = slot['label']
        hourly_data[slot_key] = {
            'min': float('inf'),
            'max': float('-inf'),
            'avg': 0,
            'count': 0,
            'total': 0
        }
    
    # 将心率数据按小时聚合
    for hr in heart_rates:
        # 找到心率所属的时间槽
        for slot in time_slots:
            if slot['start'] <= hr.timestamp < slot['end']:
                slot_key = slot['label']
                
                hourly_data[slot_key]['min'] = min(hourly_data[slot_key]['min'], hr.value)
                hourly_data[slot_key]['max'] = max(hourly_data[slot_key]['max'], hr.value)
                hourly_data[slot_key]['total'] += hr.value
                hourly_data[slot_key]['count'] += 1
                break
    
    # 计算每小时的平均值
    for hour_key in hourly_data:
        if hourly_data[hour_key]['count'] > 0:
            hourly_data[hour_key]['avg'] = round(hourly_data[hour_key]['total'] / hourly_data[hour_key]['count'], 1)
        if hourly_data[hour_key]['min'] == float('inf'):
            hourly_data[hour_key]['min'] = 0
        if hourly_data[hour_key]['max'] == float('-inf'):
            hourly_data[hour_key]['max'] = 0
    
    # 准备图表数据
    labels = [slot['label'] for slot in time_slots]
    
    datasets_config = [
        {
            'metric': 'min',
            'label': 'Min Heart Rate',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'max',
            'label': 'Max Heart Rate',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'avg',
            'label': 'Average Heart Rate',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(hourly_data, labels, datasets_config)
    
    return render_template('charts/base.html',
                         title='Daily Heart Rate',
                         endpoint='heartbeats',
                         period='daily',
                         data=chart_data)

@bp.route('/heartbeats/weekly')
@login_required
def weekly():
    """Show weekly heart rate data"""
    # 获取过去7天的时间范围
    start_date, end_date = get_time_range('weekly')
    
    # 获取心率数据
    heart_rates = HeartRate.query.filter(
        HeartRate.user_id == current_user.id,
        HeartRate.timestamp >= start_date,
        HeartRate.timestamp < end_date
    ).order_by(HeartRate.timestamp).all()
    
    # 生成时间槽（每天）
    time_slots = generate_time_slots('weekly', start_date, end_date)
    
    # 初始化数据结构
    daily_data = {}
    for slot in time_slots:
        slot_key = slot['label']
        daily_data[slot_key] = {
            'min': float('inf'),
            'max': float('-inf'),
            'avg': 0,
            'count': 0,
            'total': 0
        }
    
    # 将心率数据按天聚合
    for hr in heart_rates:
        # 找到心率所属的时间槽
        for slot in time_slots:
            if slot['start'] <= hr.timestamp < slot['end']:
                slot_key = slot['label']
                
                daily_data[slot_key]['min'] = min(daily_data[slot_key]['min'], hr.value)
                daily_data[slot_key]['max'] = max(daily_data[slot_key]['max'], hr.value)
                daily_data[slot_key]['total'] += hr.value
                daily_data[slot_key]['count'] += 1
                break
    
    # 计算每天的平均值
    for day_key in daily_data:
        if daily_data[day_key]['count'] > 0:
            daily_data[day_key]['avg'] = round(daily_data[day_key]['total'] / daily_data[day_key]['count'], 1)
        if daily_data[day_key]['min'] == float('inf'):
            daily_data[day_key]['min'] = 0
        if daily_data[day_key]['max'] == float('-inf'):
            daily_data[day_key]['max'] = 0
    
    # 准备图表数据
    labels = [slot['label'] for slot in time_slots]
    
    datasets_config = [
        {
            'metric': 'min',
            'label': 'Min Heart Rate',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'max',
            'label': 'Max Heart Rate',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'avg',
            'label': 'Average Heart Rate',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(daily_data, labels, datasets_config)
    
    return render_template('charts/base.html',
                         title='Weekly Heart Rate',
                         endpoint='heartbeats',
                         period='weekly',
                         data=chart_data)

@bp.route('/heartbeats/monthly')
@login_required
def monthly():
    """Show monthly heart rate data"""
    # 获取过去30天的时间范围
    start_date, end_date = get_time_range('monthly')
    
    # 获取心率数据
    heart_rates = HeartRate.query.filter(
        HeartRate.user_id == current_user.id,
        HeartRate.timestamp >= start_date,
        HeartRate.timestamp < end_date
    ).order_by(HeartRate.timestamp).all()
    
    # 生成时间槽（每天）
    time_slots = generate_time_slots('monthly', start_date, end_date)
    
    # 初始化数据结构
    daily_data = {}
    for slot in time_slots:
        slot_key = slot['label']
        daily_data[slot_key] = {
            'min': float('inf'),
            'max': float('-inf'),
            'avg': 0,
            'count': 0,
            'total': 0
        }
    
    # 将心率数据按天聚合
    for hr in heart_rates:
        # 找到心率所属的时间槽
        for slot in time_slots:
            if slot['start'] <= hr.timestamp < slot['end']:
                slot_key = slot['label']
                
                daily_data[slot_key]['min'] = min(daily_data[slot_key]['min'], hr.value)
                daily_data[slot_key]['max'] = max(daily_data[slot_key]['max'], hr.value)
                daily_data[slot_key]['total'] += hr.value
                daily_data[slot_key]['count'] += 1
                break
    
    # 计算每天的平均值
    for day_key in daily_data:
        if daily_data[day_key]['count'] > 0:
            daily_data[day_key]['avg'] = round(daily_data[day_key]['total'] / daily_data[day_key]['count'], 1)
        if daily_data[day_key]['min'] == float('inf'):
            daily_data[day_key]['min'] = 0
        if daily_data[day_key]['max'] == float('-inf'):
            daily_data[day_key]['max'] = 0
    
    # 准备图表数据
    labels = [slot['label'] for slot in time_slots]
    
    datasets_config = [
        {
            'metric': 'min',
            'label': 'Min Heart Rate',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'max',
            'label': 'Max Heart Rate',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'avg',
            'label': 'Average Heart Rate',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(daily_data, labels, datasets_config)
    
    return render_template('charts/base.html',
                         title='Monthly Heart Rate',
                         endpoint='heartbeats',
                         period='monthly',
                         data=chart_data)

@bp.route('/heartbeats/six_months')
@login_required
def six_months():
    """Show six months heart rate data"""
    # 获取过去180天的时间范围
    start_date, end_date = get_time_range('six_months')
    
    # 获取心率数据
    heart_rates = HeartRate.query.filter(
        HeartRate.user_id == current_user.id,
        HeartRate.timestamp >= start_date,
        HeartRate.timestamp < end_date
    ).order_by(HeartRate.timestamp).all()
    
    # 生成时间槽（每周）
    time_slots = generate_time_slots('six_months', start_date, end_date)
    
    # 初始化数据结构
    weekly_data = {}
    for slot in time_slots:
        slot_key = slot['label']
        weekly_data[slot_key] = {
            'min': float('inf'),
            'max': float('-inf'),
            'avg': 0,
            'count': 0,
            'total': 0
        }
    
    # 将心率数据按周聚合
    for hr in heart_rates:
        # 找到心率所属的时间槽
        for slot in time_slots:
            if slot['start'] <= hr.timestamp < slot['end']:
                slot_key = slot['label']
                
                weekly_data[slot_key]['min'] = min(weekly_data[slot_key]['min'], hr.value)
                weekly_data[slot_key]['max'] = max(weekly_data[slot_key]['max'], hr.value)
                weekly_data[slot_key]['total'] += hr.value
                weekly_data[slot_key]['count'] += 1
                break
    
    # 计算每周的平均值
    for week_key in weekly_data:
        if weekly_data[week_key]['count'] > 0:
            weekly_data[week_key]['avg'] = round(weekly_data[week_key]['total'] / weekly_data[week_key]['count'], 1)
        if weekly_data[week_key]['min'] == float('inf'):
            weekly_data[week_key]['min'] = 0
        if weekly_data[week_key]['max'] == float('-inf'):
            weekly_data[week_key]['max'] = 0
    
    # 准备图表数据
    labels = [slot['label'] for slot in time_slots]
    
    datasets_config = [
        {
            'metric': 'min',
            'label': 'Min Heart Rate',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'max',
            'label': 'Max Heart Rate',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'avg',
            'label': 'Average Heart Rate',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    # Use sparse labels for better readability (show every 3rd label)
    chart_data = prepare_chart_data(weekly_data, labels, datasets_config, sparse_labels=True, label_interval=3)
    
    return render_template('charts/base.html',
                         title='Six Months Heart Rate',
                         endpoint='heartbeats',
                         period='six_months',
                         data=chart_data)

@bp.route('/heartbeats/yearly')
@login_required
def yearly():
    """Show yearly heart rate data"""
    # 获取过去365天的时间范围
    start_date, end_date = get_time_range('yearly')
    
    # 获取心率数据
    heart_rates = HeartRate.query.filter(
        HeartRate.user_id == current_user.id,
        HeartRate.timestamp >= start_date,
        HeartRate.timestamp < end_date
    ).order_by(HeartRate.timestamp).all()
    
    # 生成时间槽（每月）
    time_slots = generate_time_slots('yearly', start_date, end_date)
    
    # 初始化数据结构
    monthly_data = {}
    for slot in time_slots:
        slot_key = slot['label']
        monthly_data[slot_key] = {
            'min': float('inf'),
            'max': float('-inf'),
            'avg': 0,
            'count': 0,
            'total': 0
        }
    
    # 将心率数据按月聚合
    for hr in heart_rates:
        # 找到心率所属的时间槽
        for slot in time_slots:
            if slot['start'] <= hr.timestamp < slot['end']:
                slot_key = slot['label']
                
                monthly_data[slot_key]['min'] = min(monthly_data[slot_key]['min'], hr.value)
                monthly_data[slot_key]['max'] = max(monthly_data[slot_key]['max'], hr.value)
                monthly_data[slot_key]['total'] += hr.value
                monthly_data[slot_key]['count'] += 1
                break
    
    # 计算每月的平均值
    for month_key in monthly_data:
        if monthly_data[month_key]['count'] > 0:
            monthly_data[month_key]['avg'] = round(monthly_data[month_key]['total'] / monthly_data[month_key]['count'], 1)
        if monthly_data[month_key]['min'] == float('inf'):
            monthly_data[month_key]['min'] = 0
        if monthly_data[month_key]['max'] == float('-inf'):
            monthly_data[month_key]['max'] = 0
    
    # 准备图表数据
    labels = [slot['label'] for slot in time_slots]
    
    datasets_config = [
        {
            'metric': 'min',
            'label': 'Min Heart Rate',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'max',
            'label': 'Max Heart Rate',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'avg',
            'label': 'Average Heart Rate',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(monthly_data, labels, datasets_config)
    
    return render_template('charts/base.html',
                         title='Yearly Heart Rate',
                         endpoint='heartbeats',
                         period='yearly',
                         data=chart_data) 
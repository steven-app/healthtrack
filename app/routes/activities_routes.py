from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Activity
from datetime import datetime, timedelta
from sqlalchemy import func
import calendar
from app.utils.chart_utils import get_time_range, generate_time_slots, format_empty_data_structure, prepare_chart_data

bp = Blueprint('activities', __name__)

def get_activity_data(user_id, start_date, end_date):
    """Get activity data for the specified date range"""
    activities = Activity.query.filter(
        Activity.user_id == user_id,
        Activity.timestamp >= start_date,
        Activity.timestamp <= end_date
    ).order_by(Activity.timestamp).all()
    
    # Group data by date
    data = {}
    for activity in activities:
        date = activity.timestamp.date()
        if date not in data:
            data[date] = {
                'steps': 0,
                'distance': 0,
                'calories': 0,
                'count': 0
            }
        
        # If the activity has specific fields set, use them directly
        if activity.total_steps is not None:
            data[date]['steps'] = max(data[date]['steps'], activity.total_steps)
        
        if activity.total_distance is not None:
            data[date]['distance'] = max(data[date]['distance'], activity.total_distance)
            
        if activity.calories is not None:
            data[date]['calories'] = max(data[date]['calories'], activity.calories)
        
        # Otherwise process by activity_type
        elif activity.activity_type == 'steps':
            data[date]['steps'] += activity.value
        elif activity.activity_type == 'distance':
            data[date]['distance'] += activity.value
        elif activity.activity_type == 'calories':
            data[date]['calories'] += activity.value
        
        data[date]['count'] += 1
    
    return data

@bp.route('/activities/daily')
@login_required
def daily():
    """Show daily activity data"""
    # 获取今天的时间范围
    start_date, end_date = get_time_range('daily')
    
    # 查询今天的活动数据
    activities = Activity.query.filter(
        Activity.user_id == current_user.id,
        Activity.timestamp >= start_date,
        Activity.timestamp < end_date
    ).order_by(Activity.timestamp).all()
    
    # 生成时间槽（每小时）
    time_slots = generate_time_slots('daily', start_date, end_date)
    
    # 初始化数据结构
    hourly_data = {}
    for slot in time_slots:
        slot_key = slot['label']
        hourly_data[slot_key] = {
            'steps': 0,
            'distance': 0,
            'calories': 0,
            'count': 0
        }
    
    # 将活动数据按小时聚合
    for activity in activities:
        # 找到活动所属的时间槽
        for slot in time_slots:
            if slot['start'] <= activity.timestamp < slot['end']:
                slot_key = slot['label']
                
                # 如果活动有特定字段，直接使用
                if activity.total_steps is not None:
                    hourly_data[slot_key]['steps'] = max(hourly_data[slot_key]['steps'], activity.total_steps)
                
                if activity.total_distance is not None:
                    hourly_data[slot_key]['distance'] = max(hourly_data[slot_key]['distance'], activity.total_distance)
                    
                if activity.calories is not None:
                    hourly_data[slot_key]['calories'] = max(hourly_data[slot_key]['calories'], activity.calories)
                
                # 否则按活动类型处理
                elif activity.activity_type == 'steps':
                    hourly_data[slot_key]['steps'] += activity.value
                elif activity.activity_type == 'distance':
                    hourly_data[slot_key]['distance'] += activity.value
                elif activity.activity_type == 'calories':
                    hourly_data[slot_key]['calories'] += activity.value
                
                hourly_data[slot_key]['count'] += 1
                break
    
    # 准备图表数据
    labels = [slot['label'] for slot in time_slots]
    
    datasets_config = [
        {
            'metric': 'steps',
            'label': 'Steps',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'distance',
            'label': 'Distance (km)',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'calories',
            'label': 'Calories',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(hourly_data, labels, datasets_config)
    
    return render_template('charts/activity.html',
                         title='Daily Activities',
                         endpoint='activities',
                         period='daily',
                         data=chart_data)

@bp.route('/activities/weekly')
@login_required
def weekly():
    """Show weekly activity data"""
    # 获取过去7天的时间范围
    start_date, end_date = get_time_range('weekly')
    
    # 获取活动数据
    activities = Activity.query.filter(
        Activity.user_id == current_user.id,
        Activity.timestamp >= start_date,
        Activity.timestamp < end_date
    ).order_by(Activity.timestamp).all()
    
    # 生成时间槽（每天）
    time_slots = generate_time_slots('weekly', start_date, end_date)
    
    # 初始化数据结构
    daily_data = {}
    for slot in time_slots:
        slot_key = slot['label']
        daily_data[slot_key] = {
            'steps': 0,
            'distance': 0,
            'calories': 0,
            'count': 0
        }
    
    # 将活动数据按天聚合
    for activity in activities:
        # 找到活动所属的时间槽
        for slot in time_slots:
            if slot['start'] <= activity.timestamp < slot['end']:
                slot_key = slot['label']
                
                # 如果活动有特定字段，直接使用
                if activity.total_steps is not None:
                    daily_data[slot_key]['steps'] = max(daily_data[slot_key]['steps'], activity.total_steps)
                
                if activity.total_distance is not None:
                    daily_data[slot_key]['distance'] = max(daily_data[slot_key]['distance'], activity.total_distance)
                    
                if activity.calories is not None:
                    daily_data[slot_key]['calories'] = max(daily_data[slot_key]['calories'], activity.calories)
                
                # 否则按活动类型处理
                elif activity.activity_type == 'steps':
                    daily_data[slot_key]['steps'] += activity.value
                elif activity.activity_type == 'distance':
                    daily_data[slot_key]['distance'] += activity.value
                elif activity.activity_type == 'calories':
                    daily_data[slot_key]['calories'] += activity.value
                
                daily_data[slot_key]['count'] += 1
                break
    
    # 准备图表数据
    labels = [slot['label'] for slot in time_slots]
    
    datasets_config = [
        {
            'metric': 'steps',
            'label': 'Steps',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'distance',
            'label': 'Distance (km)',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'calories',
            'label': 'Calories',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(daily_data, labels, datasets_config)
    
    return render_template('charts/activity.html',
                         title='Weekly Activities',
                         endpoint='activities',
                         period='weekly',
                         data=chart_data)

@bp.route('/activities/monthly')
@login_required
def monthly():
    """Show monthly activity data"""
    # 获取过去30天的时间范围
    start_date, end_date = get_time_range('monthly')
    
    # 获取活动数据
    activities = Activity.query.filter(
        Activity.user_id == current_user.id,
        Activity.timestamp >= start_date,
        Activity.timestamp < end_date
    ).order_by(Activity.timestamp).all()
    
    # 生成时间槽（每天）
    time_slots = generate_time_slots('monthly', start_date, end_date)
    
    # 初始化数据结构
    daily_data = {}
    for slot in time_slots:
        slot_key = slot['label']
        daily_data[slot_key] = {
            'steps': 0,
            'distance': 0,
            'calories': 0,
            'count': 0
        }
    
    # 将活动数据按天聚合
    for activity in activities:
        # 找到活动所属的时间槽
        for slot in time_slots:
            if slot['start'] <= activity.timestamp < slot['end']:
                slot_key = slot['label']
                
                # 如果活动有特定字段，直接使用
                if activity.total_steps is not None:
                    daily_data[slot_key]['steps'] = max(daily_data[slot_key]['steps'], activity.total_steps)
                
                if activity.total_distance is not None:
                    daily_data[slot_key]['distance'] = max(daily_data[slot_key]['distance'], activity.total_distance)
                    
                if activity.calories is not None:
                    daily_data[slot_key]['calories'] = max(daily_data[slot_key]['calories'], activity.calories)
                
                # 否则按活动类型处理
                elif activity.activity_type == 'steps':
                    daily_data[slot_key]['steps'] += activity.value
                elif activity.activity_type == 'distance':
                    daily_data[slot_key]['distance'] += activity.value
                elif activity.activity_type == 'calories':
                    daily_data[slot_key]['calories'] += activity.value
                
                daily_data[slot_key]['count'] += 1
                break
    
    # 准备图表数据
    labels = [slot['label'] for slot in time_slots]
    
    datasets_config = [
        {
            'metric': 'steps',
            'label': 'Steps',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'distance',
            'label': 'Distance (km)',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'calories',
            'label': 'Calories',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(daily_data, labels, datasets_config)
    
    return render_template('charts/activity.html',
                         title='Monthly Activities',
                         endpoint='activities',
                         period='monthly',
                         data=chart_data)

@bp.route('/activities/six_months')
@login_required
def six_months():
    """Show six months activity data"""
    # 获取过去180天的时间范围
    start_date, end_date = get_time_range('six_months')
    
    # 获取活动数据
    activities = Activity.query.filter(
        Activity.user_id == current_user.id,
        Activity.timestamp >= start_date,
        Activity.timestamp < end_date
    ).order_by(Activity.timestamp).all()
    
    # 生成时间槽（每周）
    time_slots = generate_time_slots('six_months', start_date, end_date)
    
    # 初始化数据结构
    weekly_data = {}
    for slot in time_slots:
        slot_key = slot['label']
        weekly_data[slot_key] = {
            'steps': 0,
            'distance': 0,
            'calories': 0,
            'count': 0,
            'days': 0  # 跟踪该周有数据的天数
        }
    
    # 将活动数据按周聚合
    daily_values = {}  # 用于按天聚合，然后再按周聚合
    
    for activity in activities:
        date_key = activity.timestamp.date()
        
        if date_key not in daily_values:
            daily_values[date_key] = {
                'steps': 0,
                'distance': 0,
                'calories': 0,
                'count': 0
            }
        
        # 如果活动有特定字段，直接使用
        if activity.total_steps is not None:
            daily_values[date_key]['steps'] = max(daily_values[date_key]['steps'], activity.total_steps)
        
        if activity.total_distance is not None:
            daily_values[date_key]['distance'] = max(daily_values[date_key]['distance'], activity.total_distance)
            
        if activity.calories is not None:
            daily_values[date_key]['calories'] = max(daily_values[date_key]['calories'], activity.calories)
        
        # 否则按活动类型处理
        elif activity.activity_type == 'steps':
            daily_values[date_key]['steps'] += activity.value
        elif activity.activity_type == 'distance':
            daily_values[date_key]['distance'] += activity.value
        elif activity.activity_type == 'calories':
            daily_values[date_key]['calories'] += activity.value
        
        daily_values[date_key]['count'] += 1
    
    # 将每日数据聚合到周
    for date, values in daily_values.items():
        # 找到日期所属的时间槽
        for slot in time_slots:
            date_time = datetime.combine(date, datetime.min.time())
            if slot['start'] <= date_time < slot['end']:
                slot_key = slot['label']
                
                weekly_data[slot_key]['steps'] += values['steps']
                weekly_data[slot_key]['distance'] += values['distance']
                weekly_data[slot_key]['calories'] += values['calories']
                weekly_data[slot_key]['days'] += 1
                break
    
    # 计算每周的平均值
    for week_key in weekly_data:
        if weekly_data[week_key]['days'] > 0:
            weekly_data[week_key]['steps'] = round(weekly_data[week_key]['steps'] / weekly_data[week_key]['days'])
            weekly_data[week_key]['distance'] = round(weekly_data[week_key]['distance'] / weekly_data[week_key]['days'], 2)
            weekly_data[week_key]['calories'] = round(weekly_data[week_key]['calories'] / weekly_data[week_key]['days'])
    
    # 准备图表数据
    labels = [slot['label'] for slot in time_slots]
    
    datasets_config = [
        {
            'metric': 'steps',
            'label': 'Avg. Steps/Day',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'distance',
            'label': 'Avg. Distance (km)/Day',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'calories',
            'label': 'Avg. Calories/Day',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    # Use sparse labels for better readability (show every 3rd label)
    chart_data = prepare_chart_data(weekly_data, labels, datasets_config, sparse_labels=True, label_interval=3)
    
    return render_template('charts/activity.html',
                         title='Six Months Activities',
                         endpoint='activities',
                         period='six_months',
                         data=chart_data)

@bp.route('/activities/yearly')
@login_required
def yearly():
    """Show yearly activity data"""
    # 获取过去365天的时间范围
    start_date, end_date = get_time_range('yearly')
    
    # 获取活动数据
    activities = Activity.query.filter(
        Activity.user_id == current_user.id,
        Activity.timestamp >= start_date,
        Activity.timestamp < end_date
    ).order_by(Activity.timestamp).all()
    
    # 生成时间槽（每月）
    time_slots = generate_time_slots('yearly', start_date, end_date)
    
    # 初始化数据结构
    monthly_data = {}
    for slot in time_slots:
        slot_key = slot['label']
        monthly_data[slot_key] = {
            'steps': 0,
            'distance': 0,
            'calories': 0,
            'count': 0,
            'days': 0  # 跟踪该月有数据的天数
        }
    
    # 将活动数据按月聚合
    daily_values = {}  # 用于按天聚合，然后再按月聚合
    
    for activity in activities:
        date_key = activity.timestamp.date()
        
        if date_key not in daily_values:
            daily_values[date_key] = {
                'steps': 0,
                'distance': 0,
                'calories': 0,
                'count': 0
            }
        
        # 如果活动有特定字段，直接使用
        if activity.total_steps is not None:
            daily_values[date_key]['steps'] = max(daily_values[date_key]['steps'], activity.total_steps)
        
        if activity.total_distance is not None:
            daily_values[date_key]['distance'] = max(daily_values[date_key]['distance'], activity.total_distance)
            
        if activity.calories is not None:
            daily_values[date_key]['calories'] = max(daily_values[date_key]['calories'], activity.calories)
        
        # 否则按活动类型处理
        elif activity.activity_type == 'steps':
            daily_values[date_key]['steps'] += activity.value
        elif activity.activity_type == 'distance':
            daily_values[date_key]['distance'] += activity.value
        elif activity.activity_type == 'calories':
            daily_values[date_key]['calories'] += activity.value
        
        daily_values[date_key]['count'] += 1
    
    # 将每日数据聚合到月
    for date, values in daily_values.items():
        # 找到日期所属的时间槽
        for slot in time_slots:
            date_time = datetime.combine(date, datetime.min.time())
            if slot['start'] <= date_time < slot['end']:
                slot_key = slot['label']
                
                monthly_data[slot_key]['steps'] += values['steps']
                monthly_data[slot_key]['distance'] += values['distance']
                monthly_data[slot_key]['calories'] += values['calories']
                monthly_data[slot_key]['days'] += 1
                break
    
    # 计算每月的平均值
    for month_key in monthly_data:
        if monthly_data[month_key]['days'] > 0:
            monthly_data[month_key]['steps'] = round(monthly_data[month_key]['steps'] / monthly_data[month_key]['days'])
            monthly_data[month_key]['distance'] = round(monthly_data[month_key]['distance'] / monthly_data[month_key]['days'], 2)
            monthly_data[month_key]['calories'] = round(monthly_data[month_key]['calories'] / monthly_data[month_key]['days'])
    
    # 准备图表数据
    labels = [slot['label'] for slot in time_slots]
    
    datasets_config = [
        {
            'metric': 'steps',
            'label': 'Avg. Steps/Day',
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'distance',
            'label': 'Avg. Distance (km)/Day',
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        },
        {
            'metric': 'calories',
            'label': 'Avg. Calories/Day',
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }
    ]
    
    chart_data = prepare_chart_data(monthly_data, labels, datasets_config)
    
    return render_template('charts/activity.html',
                         title='Yearly Activities',
                         endpoint='activities',
                         period='yearly',
                         data=chart_data) 
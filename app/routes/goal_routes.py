from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.goal import Goal
from app.forms.goal_forms import GoalForm
from app.services.goal_service import GoalService
from datetime import datetime, timedelta
from app.models.weight import Weight
from app.models.activity import Activity
from app.models.sleep import Sleep
from app.models.heart_rate import HeartRate
from app.utils.cache_utils import invalidate_dashboard_cache

bp = Blueprint('goals', __name__, url_prefix='/goals')

@bp.route('/')
@login_required
def index():
    """Show all goals for current user and progress overview"""
    # Get existing goals
    active_goals = Goal.query.filter_by(user_id=current_user.id, completed=False).all()
    completed_goals = Goal.query.filter_by(user_id=current_user.id, completed=True).all()
    
    # Get progress overview data (from previous progress.index)
    latest_weight = Weight.query.filter_by(user_id=current_user.id).order_by(Weight.timestamp.desc()).first()
    
    # Calculate step trends
    now = datetime.utcnow()
    this_week_start = now - timedelta(days=now.weekday())
    last_week_start = this_week_start - timedelta(days=7)
    
    this_week_steps = Activity.query.filter(
        Activity.user_id == current_user.id,
        Activity.timestamp >= this_week_start,
        Activity.timestamp <= now
    ).all()
    
    last_week_steps = Activity.query.filter(
        Activity.user_id == current_user.id,
        Activity.timestamp >= last_week_start,
        Activity.timestamp < this_week_start
    ).all()
    
    this_week_total = sum(a.total_steps or 0 for a in this_week_steps)
    last_week_total = sum(a.total_steps or 0 for a in last_week_steps)
    
    steps_change = 0
    if last_week_total > 0:
        steps_change = ((this_week_total - last_week_total) / last_week_total) * 100
    
    # Add similar calculations for sleep and heart rate if needed
    sleep_change = 0
    heart_rate_change = 0
    
    return render_template('goals/index.html', 
                          active_goals=active_goals, 
                          completed_goals=completed_goals,
                          latest_weight=latest_weight,
                          steps_change=steps_change,
                          sleep_change=sleep_change,
                          heart_rate_change=heart_rate_change)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new goal"""
    form = GoalForm()
    
    # Set units based on category
    if request.method == 'GET':
        category = request.args.get('category', 'steps')
        if category == 'steps':
            form.unit.data = 'steps'
        elif category == 'weight':
            form.unit.data = 'kg'
        elif category == 'sleep':
            form.unit.data = 'hours'
        elif category == 'heart_rate':
            form.unit.data = 'bpm'
    
    if form.validate_on_submit():
        # Get baseline if weight goal
        progress_baseline = None
        if form.category.data == 'weight':
            from app.models.weight import Weight
            latest_weight = Weight.query.filter_by(user_id=current_user.id).order_by(Weight.timestamp.desc()).first()
            if latest_weight:
                progress_baseline = latest_weight.value
        
        # Create goal
        goal = GoalService.create_goal(
            user_id=current_user.id,
            category=form.category.data,
            target_value=form.target_value.data,
            unit=form.unit.data,
            timeframe=form.timeframe.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            progress_related=False,
            progress_baseline=progress_baseline
        )
        
        # Invalidate dashboard cache
        invalidate_dashboard_cache(current_user.id)
        
        flash('Goal created successfully!', 'success')
        return redirect(url_for('goals.index'))
    
    return render_template('goals/create.html', form=form)

@bp.route('/<int:goal_id>')
@login_required
def view(goal_id):
    """View a specific goal"""
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    return render_template('goals/view.html', goal=goal)

@bp.route('/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete(goal_id):
    """Delete a goal"""
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    invalidate_dashboard_cache(current_user.id)
    flash('Goal deleted successfully!', 'success')
    return redirect(url_for('goals.index'))

@bp.route('/from_progress', methods=['GET', 'POST'])
@login_required
def from_progress():
    """Create a goal from progress data"""
    form = GoalForm()
    
    # Pre-fill form based on progress data
    if request.method == 'GET':
        category = request.args.get('category')
        baseline = request.args.get('baseline')
        suggested_target = request.args.get('target')
        
        if category:
            form.category.data = category
        if suggested_target:
            form.target_value.data = float(suggested_target)
        
        # Set appropriate unit
        if category == 'steps':
            form.unit.data = 'steps'
        elif category == 'weight':
            form.unit.data = 'kg'
        elif category == 'sleep':
            form.unit.data = 'hours'
        elif category == 'heart_rate':
            form.unit.data = 'bpm'
    
    if form.validate_on_submit():
        # Get baseline from form or request
        progress_baseline = None
        if form.category.data == 'weight':
            progress_baseline = float(request.form.get('baseline', 0))
        elif request.form.get('baseline'):
            progress_baseline = float(request.form.get('baseline'))
        
        # Create goal
        goal = GoalService.create_goal(
            user_id=current_user.id,
            category=form.category.data,
            target_value=form.target_value.data,
            unit=form.unit.data,
            timeframe=form.timeframe.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            progress_related=True,
            progress_baseline=progress_baseline
        )
        
        # Invalidate dashboard cache
        invalidate_dashboard_cache(current_user.id)
        
        flash('Goal created from progress data!', 'success')
        return redirect(url_for('goals.index'))
    
    return render_template('goals/create_from_progress.html', 
                           form=form, 
                           baseline=request.args.get('baseline'))

@bp.route('/update_progress/<int:goal_id>', methods=['POST'])
@login_required
def update_progress(goal_id):
    """Manually update a goal's progress"""
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    
    try:
        current_value = float(request.form.get('current_value', 0))
        goal.current_value = current_value
        
        # Check if completed
        if goal.calculate_progress() >= 100:
            goal.completed = True
        
        db.session.commit()
        invalidate_dashboard_cache(current_user.id)
        
        # If completed, check for achievements
        if goal.completed:
            from app.services.achievement_service import check_achievements_for_goal
            check_achievements_for_goal(current_user.id, goal)
        
        flash('Progress updated successfully!', 'success')
    except ValueError:
        flash('Invalid value provided!', 'danger')
    
    return redirect(url_for('goals.view', goal_id=goal_id))

# Add the progress routes from progress_routes.py
@bp.route('/progress/steps')
@login_required
def steps_progress():
    """Show detailed steps progress"""
    # Calculate daily steps for last 30 days
    days = 30
    steps_data = []
    
    for i in range(days):
        date = datetime.utcnow().date() - timedelta(days=i)
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        
        day_activities = Activity.query.filter(
            Activity.user_id == current_user.id,
            Activity.timestamp >= start_of_day,
            Activity.timestamp <= end_of_day
        ).all()
        
        day_steps = sum(activity.total_steps or 0 for activity in day_activities)
        
        steps_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'steps': day_steps
        })
    
    # Calculate suggested goal
    average_steps = sum(day['steps'] for day in steps_data) / len(steps_data) if steps_data else 0
    suggested_goal = round(average_steps * 1.1)  # 10% increase
    
    return render_template('goals/progress/steps.html',
                          steps_data=steps_data,
                          average_steps=average_steps,
                          suggested_goal=suggested_goal)

@bp.route('/progress/weight')
@login_required
def weight_progress():
    """Show weight progress"""
    weights = Weight.query.filter_by(user_id=current_user.id).order_by(Weight.timestamp).all()
    
    if not weights:
        return render_template('goals/progress/weight.html', weights=[])
    
    # Calculate weight change over time
    first_weight = weights[0].value
    latest_weight = weights[-1].value
    weight_change = latest_weight - first_weight
    percent_change = (weight_change / first_weight) * 100 if first_weight > 0 else 0
    
    # Suggest goal based on BMI
    height = current_user.height or 170  # Default height if not set
    height_m = height / 100  # Convert to meters
    current_bmi = latest_weight / (height_m * height_m)
    
    suggested_goal = None
    if current_bmi > 25:  # Overweight
        # Suggest weight loss goal
        ideal_weight = 22 * (height_m * height_m)  # Target BMI of 22
        suggested_goal = round(ideal_weight, 1)
    
    return render_template('goals/progress/weight.html',
                          weights=weights,
                          weight_change=weight_change,
                          percent_change=percent_change,
                          current_bmi=current_bmi,
                          suggested_goal=suggested_goal)

@bp.route('/progress/sleep')
@login_required
def sleep_progress():
    """Show sleep progress"""
    # Get sleep data for last 30 days
    sleeps = Sleep.query.filter(
        Sleep.user_id == current_user.id,
        Sleep.timestamp >= (datetime.utcnow() - timedelta(days=30))
    ).order_by(Sleep.timestamp).all()
    
    if not sleeps:
        return render_template('goals/progress/sleep.html', sleeps=[])
    
    # Calculate average sleep duration
    avg_duration = sum(sleep.duration or 0 for sleep in sleeps) / len(sleeps)
    avg_quality = sum(sleep.quality or 0 for sleep in sleeps if sleep.quality) / sum(1 for sleep in sleeps if sleep.quality) if any(sleep.quality for sleep in sleeps) else 0
    
    # Suggest goal based on average sleep
    suggested_goal = None
    if avg_duration < 420:  # Less than 7 hours (420 minutes)
        suggested_goal = 420  # Target 7 hours
    elif avg_duration < 480:  # Less than 8 hours
        suggested_goal = 480  # Target 8 hours
    
    return render_template('goals/progress/sleep.html',
                          sleeps=sleeps,
                          avg_duration=avg_duration,
                          avg_quality=avg_quality,
                          suggested_goal=suggested_goal)

@bp.route('/progress/heart_rate')
@login_required
def heart_rate_progress():
    """Show heart rate progress"""
    # Get heart rate data for last 30 days
    heart_rates = HeartRate.query.filter(
        HeartRate.user_id == current_user.id,
        HeartRate.timestamp >= (datetime.utcnow() - timedelta(days=30))
    ).order_by(HeartRate.timestamp).all()
    
    if not heart_rates:
        return render_template('goals/progress/heart_rate.html', heart_rates=[])
    
    # Calculate averages
    avg_heart_rate = sum(hr.value for hr in heart_rates) / len(heart_rates)
    # Consider heart rates below 100 bpm as resting heart rates
    resting_heart_rates = [hr.value for hr in heart_rates if hr.value < 100]
    avg_resting_hr = sum(resting_heart_rates) / len(resting_heart_rates) if resting_heart_rates else avg_heart_rate
    
    # Suggest goal based on resting heart rate
    suggested_goal = None
    if avg_resting_hr > 70:
        suggested_goal = 70  # Target lower resting heart rate
    
    return render_template('goals/progress/heart_rate.html',
                          heart_rates=heart_rates,
                          avg_heart_rate=avg_heart_rate,
                          avg_resting_hr=avg_resting_hr,
                          suggested_goal=suggested_goal) 
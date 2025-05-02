from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.achievement import Achievement, UserAchievement
from app.services.achievement_service import check_achievements_for_user
from app.forms.achievement_forms import AchievementForm
from app.utils.decorators import admin_required
from app.utils.cache_utils import invalidate_dashboard_cache

bp = Blueprint('achievements', __name__, url_prefix='/achievements')

@bp.route('/')
@login_required
def index():
    """Show all achievements for current user"""
    # Get all achievements
    all_achievements = Achievement.query.all()
    
    # Get user's earned achievements
    user_achievement_objs = UserAchievement.query.filter_by(user_id=current_user.id).all()
    earned_achievements = {ua.achievement_id: ua for ua in user_achievement_objs}
    
    # Sort into categories
    categories = {}
    for achievement in all_achievements:
        if achievement.category not in categories:
            categories[achievement.category] = {
                'name': achievement.category.capitalize(),
                'achievements': []
            }
        
        # Check if earned
        earned = achievement.id in earned_achievements
        earned_date = None
        if earned:
            earned_date = earned_achievements[achievement.id].earned_at
        
        categories[achievement.category]['achievements'].append({
            'achievement': achievement,
            'earned': earned,
            'earned_date': earned_date
        })
    
    return render_template('achievements/index.html', categories=categories)

@bp.route('/check')
@login_required
def check():
    """Manually check for new achievements"""
    new_achievements = check_achievements_for_user(current_user.id)
    
    if new_achievements:
        for achievement in new_achievements:
            flash(f'Achievement unlocked: {achievement.name}', 'success')
        # Invalidate dashboard cache since achievements changed
        invalidate_dashboard_cache(current_user.id)
    else:
        flash('No new achievements unlocked', 'info')
    
    return redirect(url_for('achievements.index'))

@bp.route('/<int:achievement_id>')
@login_required
def view(achievement_id):
    """View a specific achievement"""
    achievement = Achievement.query.get_or_404(achievement_id)
    
    # Check if user has earned this achievement
    user_achievement = UserAchievement.query.filter_by(
        user_id=current_user.id,
        achievement_id=achievement_id
    ).first()
    
    earned = user_achievement is not None
    earned_date = user_achievement.earned_at if earned else None
    
    return render_template('achievements/view.html', 
                           achievement=achievement,
                           earned=earned,
                           earned_date=earned_date)

# Admin-only routes for managing achievements
@bp.route('/admin')
@login_required
@admin_required
def admin_index():
    """Admin interface for managing achievements"""
    achievements = Achievement.query.order_by(Achievement.category, Achievement.level).all()
    return render_template('achievements/admin/index.html', achievements=achievements)

@bp.route('/admin/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Create a new achievement"""
    form = AchievementForm()
    
    if form.validate_on_submit():
        achievement = Achievement(
            name=form.name.data,
            description=form.description.data,
            category=form.category.data,
            icon=form.icon.data,
            level=form.level.data,
            condition_type=form.condition_type.data,
            condition_value=form.condition_value.data,
            progress_related=form.progress_related.data,
            goal_related=form.goal_related.data
        )
        
        db.session.add(achievement)
        db.session.commit()
        
        # Note: No need to invalidate any specific user's cache here since
        # creating an achievement doesn't affect existing dashboards until earned
        
        flash('Achievement created successfully!', 'success')
        return redirect(url_for('achievements.admin_index'))
    
    return render_template('achievements/admin/create.html', form=form)

@bp.route('/admin/edit/<int:achievement_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(achievement_id):
    """Edit an existing achievement"""
    achievement = Achievement.query.get_or_404(achievement_id)
    form = AchievementForm(obj=achievement)
    
    if form.validate_on_submit():
        achievement.name = form.name.data
        achievement.description = form.description.data
        achievement.category = form.category.data
        achievement.icon = form.icon.data
        achievement.level = form.level.data
        achievement.condition_type = form.condition_type.data
        achievement.condition_value = form.condition_value.data
        achievement.progress_related = form.progress_related.data
        achievement.goal_related = form.goal_related.data
        
        db.session.commit()
        
        # Invalidate cache for all users who have earned this achievement
        # In a real-world application, we might want to optimize this to avoid
        # invalidating too many caches at once
        user_achievements = UserAchievement.query.filter_by(achievement_id=achievement_id).all()
        for ua in user_achievements:
            invalidate_dashboard_cache(ua.user_id)
        
        flash('Achievement updated successfully!', 'success')
        return redirect(url_for('achievements.admin_index'))
    
    return render_template('achievements/admin/edit.html', form=form, achievement=achievement)

@bp.route('/admin/delete/<int:achievement_id>', methods=['POST'])
@login_required
@admin_required
def delete(achievement_id):
    """Delete an achievement"""
    achievement = Achievement.query.get_or_404(achievement_id)
    
    # Check if any users have earned this achievement
    user_achievements = UserAchievement.query.filter_by(achievement_id=achievement_id).all()
    if user_achievements:
        flash(f'Cannot delete achievement "{achievement.name}" because it has been earned by {len(user_achievements)} users.', 'danger')
        return redirect(url_for('achievements.admin_index'))
    
    db.session.delete(achievement)
    db.session.commit()
    
    flash('Achievement deleted successfully!', 'success')
    return redirect(url_for('achievements.admin_index')) 
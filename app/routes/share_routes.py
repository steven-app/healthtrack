from flask import Blueprint, jsonify, request, current_app, render_template, abort, g, redirect, url_for, flash, session, make_response
from flask_login import login_required, current_user
from app import db, cache
from app.models import User, SharedLink, Weight, HeartRate, Activity, Sleep, Goal, Achievement, UserAchievement
from sqlalchemy import and_
from app.models.share_access_log import ShareAccessLog
import json
import os
import csv
from datetime import datetime, timedelta
import logging
from app.forms.share_forms import CreateShareLinkForm, ManageShareLinkForm
from werkzeug.utils import secure_filename
from app.utils.date_utils import get_current_time
from app.services.data_service import get_user_data_in_range

# For PDF export
try:
    from weasyprint import HTML
except ImportError:
    HTML = None
from app.utils.cache_utils import invalidate_shared_dashboard_cache

bp = Blueprint('share', __name__, url_prefix='/share')
logger = logging.getLogger(__name__)

@bp.route('/links', methods=['GET'])
@login_required
def get_share_links():
    """Get all share links for the current user"""
    try:
        share_links = SharedLink.query.filter_by(user_id=current_user.id).order_by(SharedLink.created_at.desc()).all()
        return jsonify({
            'success': True,
            'share_links': [link.to_dict() for link in share_links]
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching share links: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching share links'
        }), 500

@bp.route('/links', methods=['POST'])
@login_required
def create_share_link():
    """Create a new share link"""
    try:
        data = request.get_json()
        
        # Get parameters with defaults from user settings
        privacy_level = data.get('privacy_level', current_user.default_share_privacy)
        modules = data.get('modules', current_user.default_share_modules)
        template_type = data.get('template_type', current_user.default_share_template)
        expiration_days = data.get('expiration_days', current_user.default_share_expiry)
        password = data.get('password')
        personal_message = data.get('personal_message', '')
        theme = data.get('theme', 'default')
        
        # Convert modules to string if it's a list
        if isinstance(modules, list):
            modules = json.dumps(modules)
        
        # Date range (default to last 30 days)
        end_date = datetime.utcnow()
        days = data.get('days', 30)
        start_date = end_date - timedelta(days=days)
        
        # Create share link
        shared_link = SharedLink.create_shared_link(
            user_id=current_user.id,
            privacy_level=privacy_level,
            modules=modules,
            template_type=template_type,
            date_range_start=start_date,
            date_range_end=end_date,
            expiration_days=expiration_days,
            password=password,
            personal_message=personal_message,
            theme=theme,
            one_time_password=data.get('one_time_password', False)
        )
        
        # No need to invalidate cache for new share links as they haven't been cached yet
        
        return jsonify({
            'success': True,
            'share_link': shared_link.to_dict(),
            'url': f"/share/view/{shared_link.share_token}"
        })
    except Exception as e:
        current_app.logger.error(f"Error creating share link: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error creating share link'
        }), 500

@bp.route('/links/<share_token>', methods=['DELETE'])
@login_required
def delete_share_link(share_token):
    """Delete a share link"""
    try:
        share_link = SharedLink.query.filter_by(share_token=share_token, user_id=current_user.id).first()
        if not share_link:
            return jsonify({
                'success': False,
                'message': 'Share link not found'
            }), 404
        
        db.session.delete(share_link)
        db.session.commit()
        
        # Invalidate shared dashboard cache
        invalidate_shared_dashboard_cache(share_token)
        
        return jsonify({
            'success': True,
            'message': 'Share link deleted successfully'
        })
    except Exception as e:
        current_app.logger.error(f"Error deleting share link: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error deleting share link'
        }), 500

@bp.route('/links/<share_token>', methods=['GET'])
@login_required
def get_share_link(share_token):
    """Get details for a specific share link"""
    try:
        share_link = SharedLink.query.filter_by(share_token=share_token, user_id=current_user.id).first()
        if not share_link:
            return jsonify({
                'success': False,
                'message': 'Share link not found'
            }), 404
        
        return jsonify({
            'success': True,
            'share_link': share_link.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching share link: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching share link'
        }), 500

@bp.route('/view/<share_token>', methods=['GET'])
def view_shared_content(share_token):
    """View shared content - directly call the main view handler"""
    # Get share link by token
    share_link = SharedLink.query.filter_by(share_token=share_token).first_or_404()
    
    # Check if share link is expired
    if share_link.is_expired:
        # Log access attempt to expired link
        ShareAccessLog.log_access(share_link, request, successful=False, access_type='expired')
        return render_template('share/expired.html', share_link=share_link)
    
    # Debug output for session data
    print(f"Session data for {share_token}: authenticated_links={session.get('authenticated_share_links', [])}")

    # Check if password protected and not authenticated
    if share_link.is_password_protected:
        authenticated_links = session.get('authenticated_share_links', [])
        # Temporarily bypass one-time password check if just authenticated
        if share_token not in authenticated_links:
            # Log access attempt that requires password
            ShareAccessLog.log_access(share_link, request, successful=False, access_type='password_required')
            return render_template('share/password.html', token=share_token)
    
    # At this point, user is authenticated or password not required
    # Update access statistics
    share_link.update_access_stats()
    
    # Log successful access
    ShareAccessLog.log_access(share_link, request, successful=True, access_type='view')
    
    # Get user
    user = User.query.get_or_404(share_link.user_id)
    
    # Get data in the specified date range
    # Determine group_by granularity
    date_diff = share_link.date_range_end - share_link.date_range_start
    group_by = 'hour' if date_diff.days < 1 else 'day'
    data = get_user_data_in_range(
        user_id=share_link.user_id,
        start_date=share_link.date_range_start,
        end_date=share_link.date_range_end,
        include_weight=share_link.show_weight,
        include_heart_rate=share_link.show_heart_rate,
        include_activity=share_link.show_activity,
        include_sleep=share_link.show_sleep,
        include_goals=share_link.show_goals,
        include_achievements=share_link.show_achievements,
        group_by=group_by
    )
    
    # Render appropriate template
    template = f'share/{share_link.template_type}.html'
    
    return render_template(template, 
                         user=user,
                         share_link=share_link,
                         data=data,
                         title=f'Health Data Shared by {user.get_full_name()}')

@bp.route('/password/<share_token>', methods=['POST'])
def check_password(share_token):
    """Check password for shared content"""
    try:
        password = request.form.get('password')
        share_link = SharedLink.query.filter_by(share_token=share_token).first()
        
        if not share_link:
            return jsonify({
                'success': False,
                'message': 'Share link not found'
            }), 404
        
        if not share_link.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Incorrect password'
            }), 401
        
        # Store authentication in session
        authenticated_links = session.get('authenticated_share_links', [])
        if share_token not in authenticated_links:
            authenticated_links.append(share_token)
            session['authenticated_share_links'] = authenticated_links
        
        # Return full URL for JavaScript redirection
        return jsonify({
            'success': True,
            'redirect': url_for('share.view_shared_content', share_token=share_token, _external=True)
        })
    except Exception as e:
        current_app.logger.error(f"Error checking password: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error checking password: {str(e)}'
        }), 500

@bp.route('/check-password/<token>', methods=['POST'])
def validate_password(token):
    """Validate password for shared content"""
    try:
        password = request.form.get('password')
        if not password:
            flash('Please enter a password', 'error')
            return redirect(url_for('share.view_shared_content', share_token=token))
        
        share_link = SharedLink.query.filter_by(share_token=token).first()
        if not share_link:
            flash('Invalid share link', 'error')
            return redirect(url_for('main.index'))
        
        is_valid = share_link.check_password(password)
        if not is_valid:
            # Password incorrect or one-time password already used
            if share_link.one_time_password and share_link.password_used:
                flash('This one-time password has been used. Please contact the owner for a new password.', 'error')
            else:
                flash('Invalid password', 'error')
            return redirect(url_for('share.view_shared_content', share_token=token))
        
        # Password validation successful, store session authentication
        authenticated_links = session.get('authenticated_share_links', [])
        if token not in authenticated_links:
            authenticated_links.append(token)
            session['authenticated_share_links'] = authenticated_links
            session.modified = True  # Mark session as modified
            print(f"Added {token} to authenticated_links. Session: {session.get('authenticated_share_links', [])}")
        
        # Force session save
        session.permanent = True
        
        return redirect(url_for('share.view_shared_content', share_token=token))
    except Exception as e:
        flash('An error occurred', 'error')
        current_app.logger.error(f"Error in validate_password: {str(e)}")
        return redirect(url_for('share.view_shared_content', share_token=token))

# Data access API endpoints
@bp.route('/data/<share_token>/dashboard', methods=['GET'])
@cache.cached(timeout=900, key_prefix=lambda: f'shared_dashboard_{request.view_args["share_token"]}')
def get_shared_dashboard(share_token):
    """Get shared dashboard data"""
    try:
        share_link = SharedLink.query.filter_by(share_token=share_token).first()
        
        if not share_link or share_link.is_expired:
            return jsonify({
                'success': False,
                'message': 'Share link not found or expired'
            }), 404
        
        # Check if dashboard module is included
        modules = json.loads(share_link.modules)
        if 'dashboard' not in modules:
            return jsonify({
                'success': False,
                'message': 'Dashboard module not shared'
            }), 403
        
        # Get user
        user = User.query.get(share_link.user_id)
        
        # Get data based on privacy level
        weights = Weight.query.filter(
            Weight.user_id == user.id,
            Weight.timestamp >= share_link.date_range_start,
            Weight.timestamp <= share_link.date_range_end
        ).order_by(Weight.timestamp.desc()).all()
        
        heart_rates = HeartRate.query.filter(
            HeartRate.user_id == user.id,
            HeartRate.timestamp >= share_link.date_range_start,
            HeartRate.timestamp <= share_link.date_range_end
        ).order_by(HeartRate.timestamp.desc()).all()
        
        activities = Activity.query.filter(
            Activity.user_id == user.id,
            Activity.timestamp >= share_link.date_range_start,
            Activity.timestamp <= share_link.date_range_end
        ).order_by(Activity.timestamp.desc()).all()
        
        sleeps = Sleep.query.filter(
            Sleep.user_id == user.id,
            Sleep.timestamp >= share_link.date_range_start,
            Sleep.timestamp <= share_link.date_range_end
        ).order_by(Sleep.timestamp.desc()).all()
        
        # Process data based on privacy level
        if share_link.privacy_level == 'overview':
            # Return only aggregated data
            data = {
                'weights': [{'date': w.timestamp.strftime('%Y-%m-%d'), 'value': w.value, 'unit': w.unit} for w in weights[:7]],
                'heart_rates': [{'date': hr.timestamp.strftime('%Y-%m-%d'), 'value': hr.value, 'unit': hr.unit} for hr in heart_rates[:7]],
                'activities': [{'date': a.timestamp.strftime('%Y-%m-%d'), 'steps': a.value} for a in activities[:7]],
                'sleeps': [{'date': s.timestamp.strftime('%Y-%m-%d'), 'duration': s.duration / 60} for s in sleeps[:7]],
                'summary': {
                    'weight': {'latest': weights[0].value if weights else 0},
                    'heart_rate': {
                        'min': min([hr.value for hr in heart_rates]) if heart_rates else 0,
                        'max': max([hr.value for hr in heart_rates]) if heart_rates else 0,
                        'avg': sum([hr.value for hr in heart_rates]) / len(heart_rates) if heart_rates else 0
                    },
                    'activity': {
                        'avg_steps': sum([a.value for a in activities]) / len(activities) if activities else 0,
                        'total_steps': sum([a.value for a in activities]) if activities else 0
                    },
                    'sleep': {
                        'avg_duration_hours': sum([s.duration for s in sleeps]) / len(sleeps) / 60 if sleeps else 0
                    }
                }
            }
        elif share_link.privacy_level == 'achievements':
            # Return only achievements data
            data = {
                'message': 'Only achievements are shared in this view'
            }
        else:  # complete
            # Return all data
            data = {
                'weights': [w.to_dict() for w in weights],
                'heart_rates': [hr.to_dict() for hr in heart_rates],
                'activities': [a.to_dict() for a in activities],
                'sleeps': [s.to_dict() for s in sleeps],
                'summary': {
                    'weight': {'latest': weights[0].value if weights else 0},
                    'heart_rate': {
                        'min': min([hr.value for hr in heart_rates]) if heart_rates else 0,
                        'max': max([hr.value for hr in heart_rates]) if heart_rates else 0,
                        'avg': sum([hr.value for hr in heart_rates]) / len(heart_rates) if heart_rates else 0
                    },
                    'activity': {
                        'avg_steps': sum([a.value for a in activities]) / len(activities) if activities else 0,
                        'total_steps': sum([a.value for a in activities]) if activities else 0
                    },
                    'sleep': {
                        'avg_duration_hours': sum([s.duration for s in sleeps]) / len(sleeps) / 60 if sleeps else 0
                    }
                }
            }
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        current_app.logger.error(f"Error getting shared dashboard data: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error getting shared dashboard data'
        }), 500

# Similar data access endpoints for other modules
@bp.route('/data/<share_token>/<module>', methods=['GET'])
def get_shared_module_data(share_token, module):
    """Get shared module data"""
    try:
        valid_modules = ['heartrate', 'activity', 'weight', 'sleep', 'goals', 'achievements']
        if module not in valid_modules:
            return jsonify({
                'success': False,
                'message': f'Invalid module: {module}'
            }), 400
            
        share_link = SharedLink.query.filter_by(share_token=share_token).first()
        
        if not share_link or share_link.is_expired:
            return jsonify({
                'success': False,
                'message': 'Share link not found or expired'
            }), 404
        
        # Check if module is included
        modules = json.loads(share_link.modules)
        if module not in modules:
            return jsonify({
                'success': False,
                'message': f'{module} module not shared'
            }), 403
        
        # Get user
        user = User.query.get(share_link.user_id)
        
        # Get and process data based on module and privacy level
        if module == 'heartrate':
            data = get_heartrate_data(user.id, share_link)
        elif module == 'activity':
            data = get_activity_data(user.id, share_link)
        elif module == 'weight':
            data = get_weight_data(user.id, share_link)
        elif module == 'sleep':
            data = get_sleep_data(user.id, share_link)
        elif module == 'goals':
            data = get_goals_data(user.id, share_link)
        elif module == 'achievements':
            data = get_achievements_data(user.id, share_link)
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        current_app.logger.error(f"Error getting shared {module} data: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting shared {module} data'
        }), 500

# Helper functions for module data
def get_heartrate_data(user_id, share_link):
    heart_rates = HeartRate.query.filter(
        HeartRate.user_id == user_id,
        HeartRate.timestamp >= share_link.date_range_start,
        HeartRate.timestamp <= share_link.date_range_end
    ).order_by(HeartRate.timestamp.desc()).all()
    
    if share_link.privacy_level == 'overview':
        return [{'date': hr.timestamp.strftime('%Y-%m-%d'), 'value': hr.value, 'unit': hr.unit} for hr in heart_rates[:14]]
    elif share_link.privacy_level == 'achievements':
        return {'message': 'Only achievements are shared in this view'}
    else:  # complete
        return [hr.to_dict() for hr in heart_rates]

def get_activity_data(user_id, share_link):
    activities = Activity.query.filter(
        Activity.user_id == user_id,
        Activity.timestamp >= share_link.date_range_start,
        Activity.timestamp <= share_link.date_range_end
    ).order_by(Activity.timestamp.desc()).all()
    
    if share_link.privacy_level == 'overview':
        return [{'date': a.timestamp.strftime('%Y-%m-%d'), 'steps': a.value} for a in activities[:14]]
    elif share_link.privacy_level == 'achievements':
        return {'message': 'Only achievements are shared in this view'}
    else:  # complete
        return [a.to_dict() for a in activities]

def get_weight_data(user_id, share_link):
    weights = Weight.query.filter(
        Weight.user_id == user_id,
        Weight.timestamp >= share_link.date_range_start,
        Weight.timestamp <= share_link.date_range_end
    ).order_by(Weight.timestamp.desc()).all()
    
    if share_link.privacy_level == 'overview':
        return [{'date': w.timestamp.strftime('%Y-%m-%d'), 'value': w.value, 'unit': w.unit} for w in weights[:14]]
    elif share_link.privacy_level == 'achievements':
        return {'message': 'Only achievements are shared in this view'}
    else:  # complete
        return [w.to_dict() for w in weights]

def get_sleep_data(user_id, share_link):
    sleeps = Sleep.query.filter(
        Sleep.user_id == user_id,
        Sleep.timestamp >= share_link.date_range_start,
        Sleep.timestamp <= share_link.date_range_end
    ).order_by(Sleep.timestamp.desc()).all()
    
    if share_link.privacy_level == 'overview':
        return [{'date': s.timestamp.strftime('%Y-%m-%d'), 'duration': s.duration / 60} for s in sleeps[:14]]
    elif share_link.privacy_level == 'achievements':
        return {'message': 'Only achievements are shared in this view'}
    else:  # complete
        return [s.to_dict() for s in sleeps]

def get_goals_data(user_id, share_link):
    if share_link.privacy_level == 'achievements':
        return {'message': 'Only achievements are shared in this view'}
    
    goals = Goal.query.filter(
        Goal.user_id == user_id,
        Goal.created_at >= share_link.date_range_start,
        Goal.created_at <= share_link.date_range_end
    ).order_by(Goal.created_at.desc()).all()
    
    return [g.to_dict() for g in goals]

def get_achievements_data(user_id, share_link):
    user_achievements = UserAchievement.query.filter(
        UserAchievement.user_id == user_id,
        UserAchievement.earned_at >= share_link.date_range_start,
        UserAchievement.earned_at <= share_link.date_range_end
    ).order_by(UserAchievement.earned_at.desc()).all()
    
    achievements = []
    for ua in user_achievements:
        achievement = Achievement.query.get(ua.achievement_id)
        if achievement:
            achievement_dict = achievement.to_dict()
            achievement_dict['earned_at'] = ua.earned_at.isoformat()
            achievements.append(achievement_dict)
    
    return achievements

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_share():
    """Create a new share link"""
    form = CreateShareLinkForm()
    
    if form.validate_on_submit():
        try:
            # Create a new share link
            expiry_days = form.expiry_days.data
            if form.never_expire.data:
                expiry_days = 0  # Special value for never expires
                
            # Handle password protection
            password = None
            one_time_password = False
            if form.password_protect.data:
                if form.one_time_password.data:
                    one_time_password = True
                else:
                    password = form.password.data
                    
            # Create the shared link
            privacy_settings = {
                'show_weight': form.show_weight.data,
                'show_heart_rate': form.show_heart_rate.data,
                'show_activity': form.show_activity.data,
                'show_sleep': form.show_sleep.data,
                'show_goals': form.show_goals.data,
                'show_achievements': form.show_achievements.data
            }
            
            # Create the share link
            share_link = SharedLink.create_shared_link(
                user_id=current_user.id,
                name=form.name.data,
                template_type=form.template_type.data,
                date_range_start=form.date_range_start.data,
                date_range_end=form.date_range_end.data,
                expiry_days=expiry_days,
                privacy_settings=privacy_settings,
                password=password,
                one_time_password=False  # 先设置为False，然后在需要时通过set_password设置
            )
            
            # If one-time password was generated, get it and show it to the user
            if one_time_password:
                generated_password = share_link.set_password(None, is_one_time=True)
                flash(f'One-time password generated: {generated_password}', 'success')
            
            # No need to invalidate cache for new share links as they haven't been cached yet
            
            flash(f'Share link "{share_link.name}" created successfully!', 'success')
            return redirect(url_for('share.manage', created=True, share_token=share_link.share_token))
            
        except Exception as e:
            logger.error(f"Error creating share link: {str(e)}", exc_info=True)
            db.session.rollback()
            flash(f'An error occurred while creating the share link: {str(e)}', 'danger')
    
    return render_template('share/create.html', form=form, title='Create Share Link')

@bp.route('/manage', methods=['GET'])
@login_required
def manage():
    """Manage existing share links"""
    # Get user's share links
    share_links = SharedLink.query.filter_by(user_id=current_user.id).order_by(SharedLink.created_at.desc()).all()
    
    return render_template('share/manage.html', 
                         share_links=share_links, 
                         title='Manage Share Links')

@bp.route('/edit/<int:share_id>', methods=['GET', 'POST'])
@login_required
def edit_share(share_id):
    """Edit an existing share link"""
    # Get share link
    share_link = SharedLink.query.filter_by(id=share_id, user_id=current_user.id).first_or_404()
    
    form = ManageShareLinkForm()
    
    if request.method == 'GET':
        # Pre-populate form
        form.name.data = share_link.name
        form.password_protect.data = share_link.is_password_protected
        form.show_weight.data = share_link.show_weight
        form.show_heart_rate.data = share_link.show_heart_rate
        form.show_activity.data = share_link.show_activity
        form.show_sleep.data = share_link.show_sleep
        form.show_goals.data = share_link.show_goals
        form.show_achievements.data = share_link.show_achievements
    
    if form.validate_on_submit():
        try:
            if form.delete.data:
                # Store the share token before deletion for cache invalidation
                share_token = share_link.share_token
                
                # Delete share link
                db.session.delete(share_link)
                db.session.commit()
                
                # Invalidate shared dashboard cache
                invalidate_shared_dashboard_cache(share_token)
                
                flash(f'Share link "{share_link.name}" deleted successfully!', 'success')
                return redirect(url_for('share.manage'))
            
            if form.submit.data:
                try:
                    # Detach any existing access logs to avoid foreign key issues
                    for log in share_link.access_logs.all():
                        db.session.expunge(log)
                    
                    # Update share link
                    share_link.name = form.name.data
                    
                    # Handle expiration settings
                    if form.never_expire.data:
                        share_link.expires_at = None  # Set to None for never expire
                    else:
                        share_link.expires_at = get_current_time() + timedelta(days=form.expiry_days.data)
                    
                    share_link.show_weight = form.show_weight.data
                    share_link.show_heart_rate = form.show_heart_rate.data
                    share_link.show_activity = form.show_activity.data
                    share_link.show_sleep = form.show_sleep.data
                    share_link.show_goals = form.show_goals.data
                    share_link.show_achievements = form.show_achievements.data
                    
                    # Update password if needed
                    if form.password_protect.data:
                        if form.one_time_password.data:
                            # Generate and get one-time password
                            generated_password = share_link.set_password(None, is_one_time=True)
                            flash(f'One-time password generated: {generated_password}', 'success')
                        elif form.change_password.data and form.password.data:
                            share_link.set_password(form.password.data)
                    else:
                        share_link.set_password(None)  # Remove password protection
                    
                    # Try to commit changes
                    try:
                        db.session.commit()
                        
                        # Invalidate shared dashboard cache
                        invalidate_shared_dashboard_cache(share_link.share_token)
                        
                        flash(f'Share link "{share_link.name}" updated successfully!', 'success')
                        return redirect(url_for('share.manage'))
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Database error during commit: {str(e)}", exc_info=True)
                        
                        # 完全重置会话
                        db.session.close()
                        db.session = db.create_scoped_session()
                        
                        # 使用直接SQL更新
                        db.session.execute(
                            """UPDATE shared_links SET 
                            name = :name, 
                            expires_at = :expires_at,
                            show_weight = :show_weight,
                            show_heart_rate = :show_heart_rate,
                            show_activity = :show_activity,
                            show_sleep = :show_sleep,
                            show_goals = :show_goals,
                            show_achievements = :show_achievements,
                            password_hash = :password_hash
                            WHERE id = :id""",
                            {
                                "name": form.name.data,
                                "expires_at": get_current_time() + timedelta(days=form.expiry_days.data),
                                "show_weight": form.show_weight.data,
                                "show_heart_rate": form.show_heart_rate.data,
                                "show_activity": form.show_activity.data,
                                "show_sleep": form.show_sleep.data,
                                "show_goals": form.show_goals.data,
                                "show_achievements": form.show_achievements.data,
                                "password_hash": share_link.password_hash,
                                "id": share_id
                            }
                        )
                        db.session.commit()
                        
                        # Invalidate shared dashboard cache
                        invalidate_shared_dashboard_cache(share_link.share_token)
                        
                        flash(f'Share link "{form.name.data}" updated successfully (with fallback method)!', 'success')
                        return redirect(url_for('share.manage'))
                except Exception as e:
                    logger.error(f"Error updating share link: {str(e)}", exc_info=True)
                    db.session.rollback()
                    flash(f'An error occurred while updating the share link: {str(e)}', 'danger')
                
        except Exception as e:
            logger.error(f"Error updating share link: {str(e)}", exc_info=True)
            db.session.rollback()
            flash(f'An error occurred while updating the share link: {str(e)}', 'danger')
    
    return render_template('share/edit.html', 
                         form=form, 
                         share_link=share_link,
                         title=f'Edit Share: {share_link.name}')

@bp.route('/export-pdf/<token>', methods=['GET'])
def export_pdf(token):
    """Export the social health report as a PDF."""
    if HTML is None:
        return "WeasyPrint is not installed. Please install it to enable PDF export.", 500
    share_link = SharedLink.query.filter_by(share_token=token).first_or_404()
    user = User.query.get_or_404(share_link.user_id)
    data = get_user_data_in_range(
        user_id=share_link.user_id,
        start_date=share_link.date_range_start,
        end_date=share_link.date_range_end,
        include_weight=share_link.show_weight,
        include_heart_rate=share_link.show_heart_rate,
        include_activity=share_link.show_activity,
        include_sleep=share_link.show_sleep,
        include_goals=share_link.show_goals,
        include_achievements=share_link.show_achievements,
        group_by='day'
    )
    # Render the PDF-specific template
    html = render_template('share/pdf/social.html', user=user, share_link=share_link, data=data)
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=health_report_{token}.pdf'
    return response

@bp.route('/access-logs/<int:share_id>', methods=['GET'])
@login_required
def access_logs(share_id):
    """View access logs for a specific share link"""
    # Get share link
    share_link = SharedLink.query.filter_by(id=share_id, user_id=current_user.id).first_or_404()
    
    # Get access logs
    logs = ShareAccessLog.query.filter_by(share_link_id=share_id).order_by(ShareAccessLog.accessed_at.desc()).all()
    
    return render_template('share/access_logs.html',
                         share_link=share_link,
                         logs=logs,
                         title=f'Access Logs: {share_link.name}')

@bp.route('/feedback', methods=['GET'])
@login_required
def feedback():
    """Display the feedback form for the share feature"""
    return render_template('share/feedback.html', title='Share Feature Feedback')

@bp.route('/feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Process the feedback form submission"""
    try:
        # Get form data
        satisfaction = request.form.get('satisfaction')
        ease_of_use = request.form.get('ease_of_use')
        features_used = request.form.getlist('features_used')
        most_important_feature = request.form.get('most_important_feature')
        missing_features = request.form.get('missing_features')
        issues = request.form.get('issues')
        suggestions = request.form.get('suggestions')
        contact_email = request.form.get('contact_email')
        
        # Prepare feedback data
        feedback_data = {
            'user_id': current_user.id,
            'username': current_user.username,
            'email': contact_email or current_user.email,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'satisfaction': satisfaction,
            'ease_of_use': ease_of_use,
            'features_used': ','.join(features_used),
            'most_important_feature': most_important_feature,
            'missing_features': missing_features,
            'issues': issues,
            'suggestions': suggestions
        }
        
        # Log feedback in the application log
        logger.info(f"Feedback received from user {current_user.username}: satisfaction={satisfaction}, ease_of_use={ease_of_use}")
        
        # Save feedback to CSV file
        feedback_dir = os.path.join(current_app.config['INSTANCE_PATH'], 'feedback')
        os.makedirs(feedback_dir, exist_ok=True)
        
        feedback_file = os.path.join(feedback_dir, 'share_feedback.csv')
        file_exists = os.path.exists(feedback_file)
        
        with open(feedback_file, 'a', newline='') as csvfile:
            fieldnames = feedback_data.keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            writer.writerow(feedback_data)
        
        # Thank the user
        flash('Thank you for your feedback! We appreciate your help in improving HealthTrack.', 'success')
        return redirect(url_for('share.manage'))
        
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
        flash('An error occurred while processing your feedback. Please try again.', 'danger')
        return redirect(url_for('share.feedback'))
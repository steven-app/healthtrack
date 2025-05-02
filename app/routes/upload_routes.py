from flask import Blueprint, request, jsonify, current_app, render_template, redirect, url_for, flash
from app.services.upload_service import UploadService
from app.models import ImportLog, Weight, HeartRate, Activity, Sleep, User
from app.utils.error_handlers import handle_upload_errors, FileValidationError, DataImportError
from flask_login import current_user, login_required
from app.utils.decorators import admin_required
from werkzeug.utils import secure_filename
import os
import logging
from app import db

logger = logging.getLogger(__name__)
bp = Blueprint('upload', __name__)

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'GET':
        try:
            # Get import history for the current user
            import_logs = ImportLog.query.filter_by(user_id=current_user.id).order_by(ImportLog.created_at.desc()).all()
            
            # Get sample data for each import log
            for log in import_logs:
                # Get sample data from each table
                log.weight_data = [w.to_dict() for w in Weight.query.filter_by(user_id=current_user.id).limit(5).all()]
                log.heart_rate_data = [h.to_dict() for h in HeartRate.query.filter_by(user_id=current_user.id).limit(5).all()]
                log.activity_data = [a.to_dict() for a in Activity.query.filter_by(user_id=current_user.id).limit(5).all()]
                log.sleep_data = [s.to_dict() for s in Sleep.query.filter_by(user_id=current_user.id).limit(5).all()]
            
            return render_template('upload/index.html', import_logs=import_logs)
        except Exception as e:
            logger.error(f"Error loading upload page: {str(e)}", exc_info=True)
            flash('Error loading upload page', 'error')
            return redirect(url_for('upload.upload_file'))
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
              request.headers.get('Accept') == 'application/json'
    
    try:
        logger.info(f"Processing file upload for user {current_user.id}")
        
        # Validate file presence
        if 'file' not in request.files:
            logger.warning("No file part in request")
            if is_ajax:
                return jsonify({'success': False, 'message': 'No file uploaded'}), 400
            flash('No file uploaded', 'error')
            return redirect(url_for('upload.upload_file'))
        
        file = request.files['file']
        if file.filename == '':
            logger.warning("No selected file")
            if is_ajax:
                return jsonify({'success': False, 'message': 'No file selected'}), 400
            flash('No file selected', 'error')
            return redirect(url_for('upload.upload_file'))
        
        # Validate file type
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            error_msg = f'File type not allowed. Allowed types are: {", ".join(current_app.config["ALLOWED_EXTENSIONS"])}'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('upload.upload_file'))
        
        # Validate data source
        data_source = request.form.get('dataSource')
        if not data_source:
            logger.warning("No data source specified")
            if is_ajax:
                return jsonify({'success': False, 'message': 'Data source not specified'}), 400
            flash('Data source not specified', 'error')
            return redirect(url_for('upload.upload_file'))
        
        # Process file
        import_service = UploadService(current_user.id)
        import_log = import_service.process_file(file, data_source)
        
        logger.info(f"File {file.filename} processed successfully for user {current_user.id}")
        
        if is_ajax:
            return jsonify({
                'success': True, 
                'message': 'File uploaded and processed successfully',
                'import_log_id': import_log.id if import_log else None
            })
        
        flash('File uploaded and processed successfully', 'success')
        return redirect(url_for('dashboard.get_dashboard_data'))
        
    except FileValidationError as e:
        logger.warning(f"File validation error: {str(e)}")
        if is_ajax:
            return jsonify({'success': False, 'message': str(e)}), 400
        flash(str(e), 'error')
        return redirect(url_for('upload.upload_file'))
    except DataImportError as e:
        logger.error(f"Data import error: {str(e)}")
        if is_ajax:
            return jsonify({'success': False, 'message': str(e)}), 500
        flash(str(e), 'error')
        return redirect(url_for('upload.upload_file'))
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}", exc_info=True)
        if is_ajax:
            return jsonify({'success': False, 'message': f'An unexpected error occurred: {str(e)}'}), 500
        flash(f'An unexpected error occurred: {str(e)}', 'error')
        return redirect(url_for('upload.upload_file'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/import', methods=['POST'])
@login_required
def import_data():
    try:
        logger.info(f"Starting data import for user {current_user.id}")
        import_log_id = request.form['import_log_id']
        import_log = ImportLog.query.get(import_log_id)
        
        if not import_log:
            logger.warning(f"Import log {import_log_id} not found")
            flash('Import log not found', 'error')
            return redirect(url_for('upload.upload_file'))

        def progress_callback(message, progress):
            logger.info(f"Import progress: {progress}% - {message}")
            sse.publish({
                'message': message,
                'progress': progress,
                'import_log_id': import_log_id
            }, type='import_progress')

        UploadService.import_data(
            import_log.file_path,
            import_log.data_source,
            import_log.user_id,
            import_log.id,
            progress_callback
        )

        logger.info(f"Data import completed successfully for import log {import_log_id}")
        flash('Data imported successfully', 'success')
        return redirect(url_for('dashboard.get_dashboard_data'))

    except Exception as e:
        logger.error(f"Error during data import: {str(e)}", exc_info=True)
        flash(f'Error importing data: {str(e)}', 'error')
        return redirect(url_for('upload.upload_file'))

@bp.route('/import_history', methods=['GET'])
@login_required
def import_history():
    try:
        logger.info(f"Fetching import history for user {current_user.id}")
        import_logs = ImportLog.query.filter_by(user_id=current_user.id).order_by(ImportLog.created_at.desc()).all()
        
        # Get sample data for each import log
        for log in import_logs:
            # Get sample data from each table
            log.weight_data = [w.to_dict() for w in Weight.query.filter_by(user_id=current_user.id).limit(5).all()]
            log.heart_rate_data = [h.to_dict() for h in HeartRate.query.filter_by(user_id=current_user.id).limit(5).all()]
            log.activity_data = [a.to_dict() for a in Activity.query.filter_by(user_id=current_user.id).limit(5).all()]
            log.sleep_data = [s.to_dict() for s in Sleep.query.filter_by(user_id=current_user.id).limit(5).all()]
        
        logger.info(f"Found {len(import_logs)} import logs")
        return render_template('upload/index.html', import_logs=import_logs)

    except Exception as e:
        logger.error(f"Error fetching import history: {str(e)}", exc_info=True)
        flash(f'Error fetching import history: {str(e)}', 'error')
        return redirect(url_for('upload.upload_file'))

@bp.route('/admin/import_logs', methods=['GET'])
@login_required
@admin_required
def admin_import_logs():
    """Admin interface for managing import logs"""
    try:
        logger.info(f"Admin {current_user.id} accessing all import logs")
        
        # Get query parameters for filtering
        user_id = request.args.get('user_id', type=int)
        status = request.args.get('status')
        data_source = request.args.get('data_source')
        
        # Build the query
        query = ImportLog.query
        
        if user_id:
            query = query.filter(ImportLog.user_id == user_id)
        if status:
            query = query.filter(ImportLog.status == status)
        if data_source:
            query = query.filter(ImportLog.data_source == data_source)
        
        # Get import logs with pagination
        page = request.args.get('page', 1, type=int)
        per_page = 20
        pagination = query.order_by(ImportLog.created_at.desc()).paginate(page=page, per_page=per_page)
        import_logs = pagination.items
        
        # Get all users for the filter dropdown
        users = User.query.all()
        
        # Get unique data sources and statuses for filter dropdowns
        data_sources = db.session.query(ImportLog.data_source).distinct().all()
        data_sources = [source[0] for source in data_sources]
        
        statuses = db.session.query(ImportLog.status).distinct().all()
        statuses = [status[0] for status in statuses]
        
        return render_template('upload/admin/index.html', 
                            import_logs=import_logs, 
                            pagination=pagination,
                            users=users,
                            data_sources=data_sources,
                            statuses=statuses,
                            current_filters={
                                'user_id': user_id,
                                'status': status,
                                'data_source': data_source
                            })
    
    except Exception as e:
        logger.error(f"Error in admin import logs: {str(e)}", exc_info=True)
        flash(f'Error accessing import logs: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@bp.route('/admin/import_logs/<int:import_log_id>', methods=['GET'])
@login_required
@admin_required
def admin_view_import_log(import_log_id):
    """Admin view for a specific import log"""
    try:
        logger.info(f"Admin {current_user.id} viewing import log {import_log_id}")
        
        import_log = ImportLog.query.get_or_404(import_log_id)
        user = User.query.get(import_log.user_id)
        
        # Get sample data for this import
        weights = Weight.query.filter_by(import_log_id=import_log_id).limit(10).all()
        heart_rates = HeartRate.query.filter_by(import_log_id=import_log_id).limit(10).all()
        activities = Activity.query.filter_by(import_log_id=import_log_id).limit(10).all()
        sleeps = Sleep.query.filter_by(import_log_id=import_log_id).limit(10).all()
        
        # Get counts
        weight_count = Weight.query.filter_by(import_log_id=import_log_id).count()
        heart_rate_count = HeartRate.query.filter_by(import_log_id=import_log_id).count()
        activity_count = Activity.query.filter_by(import_log_id=import_log_id).count()
        sleep_count = Sleep.query.filter_by(import_log_id=import_log_id).count()
        
        return render_template('upload/admin/view.html',
                            import_log=import_log,
                            user=user,
                            weights=weights,
                            heart_rates=heart_rates,
                            activities=activities,
                            sleeps=sleeps,
                            counts={
                                'weight': weight_count,
                                'heart_rate': heart_rate_count,
                                'activity': activity_count,
                                'sleep': sleep_count
                            })
    
    except Exception as e:
        logger.error(f"Error viewing import log: {str(e)}", exc_info=True)
        flash(f'Error viewing import log: {str(e)}', 'error')
        return redirect(url_for('upload.admin_import_logs'))

@bp.route('/admin/import_logs/<int:import_log_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_import_log(import_log_id):
    """Admin delete a specific import log and its associated data"""
    try:
        logger.info(f"Admin {current_user.id} deleting import log {import_log_id}")
        
        import_log = ImportLog.query.get_or_404(import_log_id)
        
        # Begin transaction
        db.session.begin_nested()
        
        # Delete associated data
        weight_count = Weight.query.filter_by(import_log_id=import_log_id).delete()
        heart_rate_count = HeartRate.query.filter_by(import_log_id=import_log_id).delete()
        activity_count = Activity.query.filter_by(import_log_id=import_log_id).delete()
        sleep_count = Sleep.query.filter_by(import_log_id=import_log_id).delete()
        
        # Delete the import log
        db.session.delete(import_log)
        
        # Commit transaction
        db.session.commit()
        
        total_deleted = weight_count + heart_rate_count + activity_count + sleep_count
        logger.info(f"Deleted import log {import_log_id} and {total_deleted} associated records")
        
        flash(f'Successfully deleted import log and {total_deleted} associated records', 'success')
        return redirect(url_for('upload.admin_import_logs'))
    
    except Exception as e:
        # Rollback transaction
        db.session.rollback()
        logger.error(f"Error deleting import log: {str(e)}", exc_info=True)
        flash(f'Error deleting import log: {str(e)}', 'error')
        return redirect(url_for('upload.admin_import_logs'))
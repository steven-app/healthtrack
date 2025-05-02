import os

def init_upload_config(app):
    """
    Initialize file upload configuration for the application
    
    This sets up file upload paths, size limits, and allowed file types.
    """
    # Base path for uploads
    instance_path = app.config.get('INSTANCE_PATH') or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
        'instance'
    )
    
    # Upload configuration
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER') or os.path.join(instance_path, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # Default 16MB
    app.config['ALLOWED_EXTENSIONS'] = {'zip', 'xml', 'csv'}
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app 
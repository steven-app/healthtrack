from functools import wraps
from flask import jsonify
from werkzeug.exceptions import RequestEntityTooLarge

class UploadError(Exception):
    """Base exception for upload related errors"""
    pass

class FileValidationError(UploadError):
    """Exception for file validation errors"""
    pass

class DataImportError(UploadError):
    """Exception for data import errors"""
    pass

def handle_upload_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except FileValidationError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except DataImportError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
        except RequestEntityTooLarge:
            return jsonify({
                'success': False,
                'message': 'File size exceeds the maximum allowed size'
            }), 413
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred'
            }), 500
    return decorated_function 
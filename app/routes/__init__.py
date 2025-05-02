from flask import Blueprint

api = Blueprint('api', __name__, url_prefix='/api')

# Remove or comment out the line below to break the circular import
# from . import auth_routes, data_routes, goal_routes, progress_routes, achievement_routes, share_routes, upload_routes, dashboard_routes
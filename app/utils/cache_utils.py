from app import cache
from flask import current_app

def invalidate_dashboard_cache(user_id):
    """
    Invalidate all dashboard-related caches for a specific user.
    
    This should be called whenever a user's data is updated to ensure
    they see the latest information.
    
    Args:
        user_id (int): The ID of the user whose cache should be invalidated
    """
    # Clear main dashboard data cache
    dashboard_key = f'dashboard_data_{user_id}'
    dashboard_summary_key = f'dashboard_summary_{user_id}'
    dashboard_goals_achievements_key = f'dashboard_goals_achievements_{user_id}'
    
    try:
        # Track which keys were successfully invalidated
        invalidated_keys = []
        
        # Try to delete each key
        if cache.delete(dashboard_key):
            invalidated_keys.append(dashboard_key)
            
        if cache.delete(dashboard_summary_key):
            invalidated_keys.append(dashboard_summary_key)
            
        if cache.delete(dashboard_goals_achievements_key):
            invalidated_keys.append(dashboard_goals_achievements_key)
        
        if invalidated_keys:
            current_app.logger.info(f"Cache invalidated for user {user_id}: {', '.join(invalidated_keys)}")
        else:
            current_app.logger.info(f"No cache entries found to invalidate for user {user_id}")
    except Exception as e:
        current_app.logger.error(f"Error invalidating dashboard cache for user {user_id}: {str(e)}")

def invalidate_shared_dashboard_cache(share_token):
    """
    Invalidate cache for a shared dashboard.
    
    This should be called when a share link is updated or when 
    the underlying data changes.
    
    Args:
        share_token (str): The token of the shared link
    """
    # Clear shared dashboard cache
    shared_dashboard_key = f'shared_dashboard_{share_token}'
    
    try:
        # Attempt to delete the key and check if it was actually in the cache
        if cache.delete(shared_dashboard_key):
            current_app.logger.info(f"Successfully invalidated shared dashboard cache for token {share_token}")
        else:
            current_app.logger.info(f"No cache entry found to invalidate for token {share_token}")
    except Exception as e:
        current_app.logger.error(f"Error invalidating shared dashboard cache for token {share_token}: {str(e)}") 
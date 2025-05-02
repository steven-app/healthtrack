from .user import User
from .weight import Weight
from .heart_rate import HeartRate
from .activity import Activity
from .sleep import Sleep
from .goal import Goal
from .progress import Progress
from .achievement import Achievement, UserAchievement
from .import_log import ImportLog
from .shared_link import SharedLink
# Import the models that depend on other models last
from .share_access_log import ShareAccessLog

__all__ = [
    'User',
    'Weight',
    'HeartRate',
    'Activity',
    'Sleep',
    'Goal',
    'Progress',
    'Achievement',
    'UserAchievement',
    'ImportLog',
    'SharedLink',
    'ShareAccessLog'
]

# This file imports all models to make them available when importing from the models package
# It also ensures all model relationships are properly set up when the application starts
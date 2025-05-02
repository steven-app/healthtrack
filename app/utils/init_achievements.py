from app import db
from app.models.achievement import Achievement

def init_achievements():
    """Initialize default achievements in the database"""
    # First check if achievements already exist
    if Achievement.query.count() > 0:
        print("Achievements already initialized")
        return
    
    # Steps achievements
    steps_achievements = [
        {
            'name': 'First Steps',
            'description': 'Record your first 10,000 steps in a day',
            'category': 'steps',
            'icon': 'walking',
            'level': 'bronze',
            'condition_type': 'milestone',
            'condition_value': 10000,
            'goal_related': False
        },
        {
            'name': 'Step Master',
            'description': 'Record over 20,000 steps in a day',
            'category': 'steps',
            'icon': 'running',
            'level': 'silver',
            'condition_type': 'milestone',
            'condition_value': 20000,
            'goal_related': False
        },
        {
            'name': 'Step Legend',
            'description': 'Complete a 7-day streak of at least 10,000 steps daily',
            'category': 'steps',
            'icon': 'award',
            'level': 'gold',
            'condition_type': 'streak',
            'condition_value': 7,
            'goal_related': False
        },
        {
            'name': 'Goal Achiever: Steps',
            'description': 'Complete your first steps goal',
            'category': 'steps',
            'icon': 'flag-checkered',
            'level': 'bronze',
            'condition_type': 'milestone',
            'condition_value': 1,
            'goal_related': True
        }
    ]
    
    # Weight achievements
    weight_achievements = [
        {
            'name': 'Weight Tracker',
            'description': 'Record your weight consistently for 7 days',
            'category': 'weight',
            'icon': 'weight',
            'level': 'bronze',
            'condition_type': 'streak',
            'condition_value': 7,
            'goal_related': False
        },
        {
            'name': 'Weight Goal Milestone',
            'description': 'Achieve your first weight goal',
            'category': 'weight',
            'icon': 'bullseye',
            'level': 'silver',
            'condition_type': 'milestone',
            'condition_value': 1,
            'goal_related': True
        },
        {
            'name': 'Weight Transformation',
            'description': 'Change your weight by 5 kg towards your goal',
            'category': 'weight',
            'icon': 'star',
            'level': 'gold',
            'condition_type': 'improvement',
            'condition_value': 5,
            'goal_related': False
        }
    ]
    
    # Sleep achievements
    sleep_achievements = [
        {
            'name': 'Good Night',
            'description': 'Record 8 hours of sleep with good quality',
            'category': 'sleep',
            'icon': 'bed',
            'level': 'bronze',
            'condition_type': 'milestone',
            'condition_value': 8,
            'goal_related': False
        },
        {
            'name': 'Sleep Routine',
            'description': 'Track your sleep for 10 consecutive days',
            'category': 'sleep',
            'icon': 'moon',
            'level': 'silver',
            'condition_type': 'streak',
            'condition_value': 10,
            'goal_related': False
        },
        {
            'name': 'Sleep Goal Master',
            'description': 'Complete 3 sleep goals',
            'category': 'sleep',
            'icon': 'star',
            'level': 'gold',
            'condition_type': 'streak',
            'condition_value': 3,
            'goal_related': True
        }
    ]
    
    # Heart rate achievements
    heart_rate_achievements = [
        {
            'name': 'Heart Monitor',
            'description': 'Start tracking your heart rate consistently',
            'category': 'heart_rate',
            'icon': 'heartbeat',
            'level': 'bronze',
            'condition_type': 'streak',
            'condition_value': 5,
            'goal_related': False
        },
        {
            'name': 'Heart Health',
            'description': 'Improve your resting heart rate by 5 bpm',
            'category': 'heart_rate',
            'icon': 'heart',
            'level': 'silver',
            'condition_type': 'improvement',
            'condition_value': 5,
            'goal_related': False
        },
        {
            'name': 'Heart Goal Champion',
            'description': 'Complete a heart rate goal',
            'category': 'heart_rate',
            'icon': 'medal',
            'level': 'gold',
            'condition_type': 'milestone',
            'condition_value': 1,
            'goal_related': True
        }
    ]
    
    # General achievements
    general_achievements = [
        {
            'name': 'Data Collector',
            'description': 'Record a total of 100 health data points',
            'category': 'general',
            'icon': 'database',
            'level': 'bronze',
            'condition_type': 'milestone',
            'condition_value': 100,
            'goal_related': False
        },
        {
            'name': 'Goal Setter',
            'description': 'Create goals in all categories',
            'category': 'general',
            'icon': 'tasks',
            'level': 'silver',
            'condition_type': 'milestone',
            'condition_value': 4,  # One for each category
            'goal_related': True
        },
        {
            'name': 'Health Champion',
            'description': 'Complete 10 health goals across all categories',
            'category': 'general',
            'icon': 'trophy',
            'level': 'gold',
            'condition_type': 'milestone',
            'condition_value': 10,
            'goal_related': True
        }
    ]
    
    # Combine all achievements
    all_achievements = (
        steps_achievements + 
        weight_achievements + 
        sleep_achievements + 
        heart_rate_achievements + 
        general_achievements
    )
    
    # Add to database
    for achievement_data in all_achievements:
        achievement = Achievement(**achievement_data)
        db.session.add(achievement)
    
    db.session.commit()
    print(f"Initialized {len(all_achievements)} achievements") 
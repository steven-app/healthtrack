import csv
import io
import json
from datetime import datetime
import zipfile

def export_data_to_csv(user):
    """
    Export user data to CSV files (one per data type)
    
    Args:
        user: User object with data to export
        
    Returns:
        BytesIO object containing a zip file with CSVs
    """
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w') as zf:
        # Export profile data
        if user:
            profile_data = io.StringIO()
            profile_writer = csv.writer(profile_data)
            
            # Write headers
            profile_writer.writerow([
                'Username', 'Email', 'First Name', 'Last Name', 'Gender', 
                'Birth Date', 'Height (cm)', 'Weight (kg)', 'Created At'
            ])
            
            # Write data
            profile_writer.writerow([
                user.username, 
                user.email,
                user.first_name or '',
                user.last_name or '',
                user.gender or '',
                user.birth_date.strftime('%Y-%m-%d') if user.birth_date else '',
                user.height or '',
                user.weight or '',
                user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ''
            ])
            
            zf.writestr('profile.csv', profile_data.getvalue())
        
        # Export weight data
        if user.weights.count() > 0:
            weights_data = io.StringIO()
            weights_writer = csv.writer(weights_data)
            
            # Write headers
            weights_writer.writerow(['Date', 'Weight', 'Unit'])
            
            # Write data
            for weight in user.weights:
                weights_writer.writerow([
                    weight.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    weight.value,
                    weight.unit or 'kg'
                ])
            
            zf.writestr('weights.csv', weights_data.getvalue())
        
        # Export heart rate data
        if user.heart_rates.count() > 0:
            hr_data = io.StringIO()
            hr_writer = csv.writer(hr_data)
            
            # Write headers
            hr_writer.writerow(['Date', 'Heart Rate (bpm)'])
            
            # Write data
            for hr in user.heart_rates:
                hr_writer.writerow([
                    hr.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    hr.value
                ])
            
            zf.writestr('heart_rates.csv', hr_data.getvalue())
        
        # Export activity data
        if user.activities.count() > 0:
            activity_data = io.StringIO()
            activity_writer = csv.writer(activity_data)
            
            # Write headers
            activity_writer.writerow([
                'Date', 'Steps', 'Distance (km)', 'Calories', 'Activity Type'
            ])
            
            # Write data
            for activity in user.activities:
                activity_writer.writerow([
                    activity.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    activity.total_steps or '',
                    activity.total_distance or '',
                    activity.calories or '',
                    activity.activity_type or ''
                ])
            
            zf.writestr('activities.csv', activity_data.getvalue())
        
        # Export sleep data
        if user.sleeps.count() > 0:
            sleep_data = io.StringIO()
            sleep_writer = csv.writer(sleep_data)
            
            # Write headers
            sleep_writer.writerow([
                'Date', 'Duration (min)', 'Deep Sleep (min)', 'Light Sleep (min)', 
                'REM Sleep (min)', 'Awake (min)', 'Quality', 'Start Time', 'End Time'
            ])
            
            # Write data
            for sleep in user.sleeps:
                sleep_writer.writerow([
                    sleep.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    sleep.duration,
                    sleep.deep_sleep or '',
                    sleep.light_sleep or '',
                    sleep.rem_sleep or '',
                    sleep.awake or '',
                    sleep.quality or '',
                    sleep.start_time.strftime('%Y-%m-%d %H:%M:%S') if sleep.start_time else '',
                    sleep.end_time.strftime('%Y-%m-%d %H:%M:%S') if sleep.end_time else ''
                ])
            
            zf.writestr('sleep.csv', sleep_data.getvalue())
    
    memory_file.seek(0)
    return memory_file 
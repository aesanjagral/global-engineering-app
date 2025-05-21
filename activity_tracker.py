import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class ActivityTracker:
    def __init__(self):
        self.user_data_folder = os.path.join(str(Path.home()), '.my_app_data')
        self.activities_file = os.path.join(self.user_data_folder, 'activities.json')
        
        # Create user data folder if it doesn't exist
        os.makedirs(self.user_data_folder, exist_ok=True)
        
        # Create activities file if it doesn't exist
        if not os.path.exists(self.activities_file):
            with open(self.activities_file, 'w') as f:
                json.dump([], f)
        
        # Clean old activities on startup
        self.clean_old_activities()

    def clean_old_activities(self):
        """Remove activities older than 30 days"""
        try:
            with open(self.activities_file, 'r') as f:
                activities = json.load(f)
            
            current_date = datetime.now()
            filtered_activities = []
            
            for activity in activities:
                try:
                    activity_date = datetime.strptime(activity['datetime'], '%Y-%m-%d %H:%M:%S')
                    if (current_date - activity_date).days <= 30:
                        filtered_activities.append(activity)
                except:
                    continue
            
            with open(self.activities_file, 'w') as f:
                json.dump(filtered_activities, f, indent=2)
                
        except Exception as e:
            print(f"Error cleaning old activities: {str(e)}")

    def log_activity(self, module: str, action: str, details: str) -> bool:
        """
        Log a new activity
        :param module: Module name (e.g., 'Payment', 'Report', etc.)
        :param action: Action performed (e.g., 'Added', 'Modified', etc.)
        :param details: Additional details about the activity
        """
        try:
            # Clean old activities first
            self.clean_old_activities()
            
            # Read existing activities
            with open(self.activities_file, 'r') as f:
                activities = json.load(f)
            
            # Add new activity
            new_activity = {
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'module': module,
                'action': action,
                'details': details
            }
            activities.append(new_activity)
            
            # Write back to file
            with open(self.activities_file, 'w') as f:
                json.dump(activities, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
            return False

    def get_activities(self, limit: int = None) -> list:
        """
        Retrieve activities
        :param limit: Optional limit on number of activities to return (None for all activities)
        :return: List of activities
        """
        try:
            # Clean old activities first
            self.clean_old_activities()
            
            with open(self.activities_file, 'r') as f:
                activities = json.load(f)
            
            # Return all activities if limit is None, otherwise return limited activities
            if limit is None:
                return activities
            return activities[-limit:]
        except Exception as e:
            print(f"Error reading activities: {str(e)}")
            return []

    def clear_activities(self):
        """Clear all activities"""
        try:
            with open(self.activities_file, 'w') as f:
                json.dump([], f)
            return True
        except Exception as e:
            print(f"Error clearing activities: {str(e)}")
            return False 
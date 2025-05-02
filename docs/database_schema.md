# HealthTrack Database Schema

This document describes the database schema for the HealthTrack application. The schema is organized around various health metrics and user data.

## Tables

### 1. users

This table stores user account information and preferences.

| Field Name            | Type         | Description                                                  |
| --------------------- | ------------ | ------------------------------------------------------------ |
| `id`                  | INTEGER      | Primary key, auto-incremented, unique identifier for each user. |
| `username`            | VARCHAR(64)  | User's chosen username, must be unique.                      |
| `email`               | VARCHAR(120) | User's email address, must be unique.                        |
| `password_hash`       | VARCHAR(128) | Hashed password for secure authentication.                   |
| `created_at`          | DATETIME     | Timestamp when the user account was created.                 |
| `last_login`          | DATETIME     | Timestamp of the user's last login.                          |
| `is_active`           | BOOLEAN      | Indicates if the user account is active or deactivated.      |
| `is_admin`            | BOOLEAN      | Indicates if the user has admin privileges.                  |
| `updated_at`          | DATETIME     | Timestamp when the user account was last updated.            |
| `first_name`          | VARCHAR(64)  | User's first name.                                           |
| `last_name`           | VARCHAR(64)  | User's last name.                                            |
| `gender`              | VARCHAR(20)  | User's gender.                                               |
| `birth_date`          | DATE         | User's birth date.                                           |
| `height`              | FLOAT        | User's height (in cm).                                       |
| `weight`              | FLOAT        | User's weight (in kg).                                       |
| `default_share_privacy` | VARCHAR(20) | Default privacy level for sharing: 'complete', 'overview', or 'achievements'. |
| `default_share_modules` | TEXT        | JSON array of modules to share by default.                   |
| `default_share_template` | VARCHAR(20) | Default template for sharing: 'medical' or 'social'.        |
| `default_share_expiry` | INTEGER      | Default expiry time in days for share links.                 |

------

### 2. activities

This table stores activity data like steps, distance, and calories.

| Field Name       | Type        | Description                                                  |
| ---------------- | ----------- | ------------------------------------------------------------ |
| `id`             | INTEGER     | Primary key, auto-incremented, unique identifier for each activity entry. |
| `user_id`        | INTEGER     | Foreign key referencing `users(id)`, links activity data to a specific user. |
| `import_log_id`  | INTEGER     | Foreign key referencing `import_logs(id)`, indicates which import added this data. |
| `activity_type`  | VARCHAR(50) | Type of activity (e.g., walking, running, cycling).          |
| `value`          | FLOAT       | Numerical value for the activity.                            |
| `unit`           | VARCHAR(10) | Unit of measurement for the value.                           |
| `timestamp`      | DATETIME    | The timestamp when the activity data was recorded.           |
| `total_steps`    | INTEGER     | The total number of steps taken during the activity.         |
| `total_distance` | FLOAT       | The total distance covered in the activity.                  |
| `calories`       | INTEGER     | The total calories burned during the activity.               |
| `data_source`    | VARCHAR(50) | The source from which the data was imported (e.g., Fitbit, Google Fit). |
| `created_at`     | DATETIME    | Timestamp when the record was created.                       |
| `updated_at`     | DATETIME    | Timestamp when the record was last updated.                  |

------

### 3. heart_rates

This table stores heart rate measurements.

| Field Name      | Type        | Description                                                  |
| --------------- | ----------- | ------------------------------------------------------------ |
| `id`            | INTEGER     | Primary key, auto-incremented, unique identifier for each heart rate entry. |
| `user_id`       | INTEGER     | Foreign key referencing `users(id)`, links heart rate data to a specific user. |
| `import_log_id` | INTEGER     | Foreign key referencing `import_logs(id)`, indicates which import added this data. |
| `value`         | INTEGER     | Heart rate value in beats per minute (BPM).                  |
| `unit`          | VARCHAR(10) | Unit of measurement (default: 'bpm').                        |
| `timestamp`     | DATETIME    | The timestamp when the heart rate was measured.              |
| `data_source`   | VARCHAR(50) | The source from which the data was imported.                 |
| `created_at`    | DATETIME    | Timestamp when the record was created.                       |
| `updated_at`    | DATETIME    | Timestamp when the record was last updated.                  |

------

### 4. weights

This table stores weight measurements.

| Field Name      | Type        | Description                                                  |
| --------------- | ----------- | ------------------------------------------------------------ |
| `id`            | INTEGER     | Primary key, auto-incremented, unique identifier for each weight entry. |
| `user_id`       | INTEGER     | Foreign key referencing `users(id)`, links weight data to a specific user. |
| `import_log_id` | INTEGER     | Foreign key referencing `import_logs(id)`, indicates which import added this data. |
| `value`         | FLOAT       | Weight value.                                                |
| `unit`          | VARCHAR(10) | Unit of measurement (e.g., 'kg', 'lb').                      |
| `timestamp`     | DATETIME    | The timestamp when the weight was measured.                  |
| `data_source`   | VARCHAR(50) | The source from which the data was imported.                 |
| `created_at`    | DATETIME    | Timestamp when the record was created.                       |
| `updated_at`    | DATETIME    | Timestamp when the record was last updated.                  |

------

### 5. sleeps

This table stores sleep data.

| Field Name      | Type        | Description                                                  |
| --------------- | ----------- | ------------------------------------------------------------ |
| `id`            | INTEGER     | Primary key, auto-incremented, unique identifier for each sleep entry. |
| `user_id`       | INTEGER     | Foreign key referencing `users(id)`, links sleep data to a specific user. |
| `import_log_id` | INTEGER     | Foreign key referencing `import_logs(id)`, indicates which import added this data. |
| `duration`      | FLOAT       | Total sleep duration in minutes.                             |
| `deep_sleep`    | FLOAT       | Deep sleep duration in minutes.                              |
| `light_sleep`   | FLOAT       | Light sleep duration in minutes.                             |
| `rem_sleep`     | FLOAT       | REM sleep duration in minutes.                               |
| `awake`         | FLOAT       | Awake time during sleep period in minutes.                   |
| `unit`          | VARCHAR(10) | Unit of measurement (default: 'minutes').                    |
| `quality`       | VARCHAR(20) | Sleep quality (e.g., 'good', 'fair', 'poor').               |
| `start_time`    | DATETIME    | The start time of the sleep session.                         |
| `end_time`      | DATETIME    | The end time of the sleep session.                           |
| `timestamp`     | DATETIME    | The timestamp when the sleep data was recorded.              |
| `notes`         | TEXT        | Additional notes about the sleep session.                    |

------

### 6. goals

This table stores user goals for health metrics.

| Field Name          | Type        | Description                                                  |
| ------------------- | ----------- | ------------------------------------------------------------ |
| `id`                | INTEGER     | Primary key, auto-incremented, unique identifier for each goal. |
| `user_id`           | INTEGER     | Foreign key referencing `users(id)`, links the goal to a specific user. |
| `category`          | VARCHAR(50) | Category of the goal (e.g., 'steps', 'weight', 'sleep', 'heart_rate'). |
| `target_value`      | FLOAT       | The target value to achieve.                                 |
| `current_value`     | FLOAT       | The current progress towards the goal.                       |
| `unit`              | VARCHAR(20) | Unit of measurement for the goal.                            |
| `timeframe`         | VARCHAR(20) | Timeframe for achieving the goal (e.g., 'daily', 'weekly', 'monthly'). |
| `start_date`        | DATETIME    | The date when the goal begins.                               |
| `end_date`          | DATETIME    | The date by which the goal should be completed.              |
| `completed`         | BOOLEAN     | Indicates if the goal has been completed.                    |
| `progress_related`  | BOOLEAN     | Indicates if the goal is related to tracking progress over time. |
| `progress_baseline` | FLOAT       | Baseline value for progress calculations.                    |
| `created_at`        | DATETIME    | Timestamp when the goal was created.                         |
| `updated_at`        | DATETIME    | Timestamp when the goal was last updated.                    |

------

### 7. progress

This table tracks progress towards goals.

| Field Name  | Type        | Description                                                  |
| ----------- | ----------- | ------------------------------------------------------------ |
| `id`        | INTEGER     | Primary key, auto-incremented, unique identifier for each progress entry. |
| `user_id`   | INTEGER     | Foreign key referencing `users(id)`, links the progress to a specific user. |
| `goal_id`   | INTEGER     | Foreign key referencing `goals(id)`, links the progress to a specific goal. |
| `value`     | FLOAT       | The progress value.                                          |
| `unit`      | VARCHAR(20) | Unit of measurement for the progress value.                  |
| `timestamp` | DATETIME    | The timestamp when the progress was recorded.                |
| `notes`     | TEXT        | Additional notes about the progress.                         |

------

### 8. achievements

This table defines various achievements that users can earn.

| Field Name        | Type         | Description                                                  |
| ----------------- | ------------ | ------------------------------------------------------------ |
| `id`              | INTEGER      | Primary key, auto-incremented, unique identifier for each achievement. |
| `name`            | VARCHAR(100) | Name of the achievement.                                     |
| `description`     | VARCHAR(255) | Description of the achievement.                              |
| `category`        | VARCHAR(50)  | Category of the achievement (e.g., 'steps', 'weight', 'sleep', 'heart_rate', 'general'). |
| `icon`            | VARCHAR(100) | Icon or image associated with the achievement.               |
| `level`           | VARCHAR(20)  | Level of the achievement (e.g., 'bronze', 'silver', 'gold'). |
| `condition_type`  | VARCHAR(50)  | Type of condition for earning the achievement (e.g., 'streak', 'milestone', 'improvement'). |
| `condition_value` | FLOAT        | Value required to meet the condition.                        |
| `trigger_type`    | VARCHAR(20)  | What triggers the achievement (e.g., 'progress', 'goal', 'combined'). |
| `progress_related` | BOOLEAN     | Indicates if the achievement is related to tracking progress. |
| `goal_related`    | BOOLEAN      | Indicates if the achievement is related to completing goals. |
| `created_at`      | DATETIME     | Timestamp when the achievement was created.                  |

------

### 9. user_achievements

This table tracks which achievements have been earned by users.

| Field Name       | Type     | Description                                                  |
| ---------------- | -------- | ------------------------------------------------------------ |
| `id`             | INTEGER  | Primary key, auto-incremented, unique identifier for each user achievement. |
| `user_id`        | INTEGER  | Foreign key referencing `users(id)`, links the achievement to a specific user. |
| `achievement_id` | INTEGER  | Foreign key referencing `achievements(id)`, links to the specific achievement. |
| `earned_at`      | DATETIME | Timestamp when the achievement was earned.                   |

------

### 10. import_logs

This table logs data import operations.

| Field Name          | Type         | Description                                                  |
| ------------------- | ------------ | ------------------------------------------------------------ |
| `id`                | INTEGER      | Primary key, auto-incremented, unique identifier for each import log. |
| `user_id`           | INTEGER      | Foreign key referencing `users(id)`, links the import to a specific user. |
| `data_source`       | VARCHAR(50)  | The source of the imported data.                             |
| `file_name`         | VARCHAR(255) | Name of the imported file.                                   |
| `status`            | VARCHAR(20)  | Status of the import (e.g., 'success', 'failed', 'processing'). |
| `error_message`     | TEXT         | Error message if the import failed.                          |
| `records_processed` | INTEGER      | Number of records processed during the import.               |
| `created_at`        | DATETIME     | Timestamp when the import was initiated.                     |
| `completed_at`      | DATETIME     | Timestamp when the import was completed.                     |

------

### 11. shared_links

This table stores links for sharing health data with others.

| Field Name          | Type         | Description                                                  |
| ------------------- | ------------ | ------------------------------------------------------------ |
| `id`                | INTEGER      | Primary key, auto-incremented, unique identifier for each shared link. |
| `user_id`           | INTEGER      | Foreign key referencing `users(id)`, links the shared link to a specific user. |
| `share_token`       | VARCHAR(64)  | Unique token used in the share URL.                          |
| `name`              | VARCHAR(100) | Name of the shared link.                                     |
| `expires_at`        | DATETIME     | Expiration date and time for the shared link.                |
| `password_hash`     | VARCHAR(128) | Hash of the password for password-protected links.           |
| `privacy_level`     | VARCHAR(20)  | Privacy level for the shared data (e.g., 'complete', 'overview', 'achievements'). |
| `modules`           | TEXT         | JSON array of modules to include in the shared data.         |
| `date_range_start`  | DATETIME     | Start date for the data range to share.                      |
| `date_range_end`    | DATETIME     | End date for the data range to share.                        |
| `template_type`     | VARCHAR(20)  | Type of template to use for the shared data (e.g., 'medical', 'social'). |
| `personal_message`  | VARCHAR(255) | Personal message included with the shared data.              |
| `theme`             | VARCHAR(20)  | Visual theme for the shared data view.                       |
| `created_at`        | DATETIME     | Timestamp when the shared link was created.                  |
| `last_accessed`     | DATETIME     | Timestamp when the shared link was last accessed.            |
| `access_count`      | INTEGER      | Number of times the shared link has been accessed.           |
| `show_weight`       | BOOLEAN      | Whether to include weight data in the shared data.           |
| `show_heart_rate`   | BOOLEAN      | Whether to include heart rate data in the shared data.       |
| `show_activity`     | BOOLEAN      | Whether to include activity data in the shared data.         |
| `show_sleep`        | BOOLEAN      | Whether to include sleep data in the shared data.            |
| `show_goals`        | BOOLEAN      | Whether to include goals in the shared data.                 |
| `show_achievements` | BOOLEAN      | Whether to include achievements in the shared data.          |
| `one_time_password` | BOOLEAN      | Whether the shared link uses a one-time password.            |
| `password_used`     | BOOLEAN      | Whether the one-time password has been used.                 |

------

### 12. share_access_logs

This table logs access to shared links.

| Field Name      | Type         | Description                                                  |
| --------------- | ------------ | ------------------------------------------------------------ |
| `id`            | INTEGER      | Primary key, auto-incremented, unique identifier for each access log. |
| `share_link_id` | INTEGER      | Foreign key referencing `shared_links(id)`, links the access log to a specific shared link. |
| `accessed_at`   | DATETIME     | Timestamp when the shared link was accessed.                 |
| `ip_address`    | VARCHAR(45)  | IP address of the accessor.                                  |
| `user_agent`    | VARCHAR(255) | User agent of the accessor's browser.                        |
| `successful`    | BOOLEAN      | Whether the access was successful (e.g., correct password).  |
| `access_type`   | VARCHAR(20)  | Type of access (e.g., 'view', 'pdf').                        |

------

## Relationships

- **User** has many: Activities, Heart Rates, Weights, Sleeps, Goals, Progress records, User Achievements, Import Logs, and Shared Links
- **Goal** has many Progress records
- **Achievement** has many User Achievements
- **Import Log** has many: Activities, Heart Rates, Weights, and Sleeps
- **Shared Link** has many Share Access Logs 
# HealthTrack API Contract

- **Version:** `v1.0`
- **Base URL:** `http://localhost:5000/api`
- **Last Updated:** Apr 17, 2025

This RESTful API powers the HealthTrack Application, allowing users to track personal health data, visualize trends, track goals and achievements, and selectively share data with others. The API supports data from various health platforms including: **Apple Health**, **Google Fit**, **Fitbit**, **Garmin**, and **Samsung Health**.

------

## 1. Authentication

### POST `/auth/register`

Register a new user.

**Request Body (JSON):**

```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response:**

- `201 Created` on success
- `400 Bad Request` if validation fails

**Example Response:**

```json
{
  "success": true,
  "message": "Registration successful"
}
```

------

### POST `/auth/login`

Authenticate and receive a token.

**Request Body (JSON):**

```json
{
  "email": "string",
  "password": "string"
}
```

**Response:**

- `200 OK` on success
- `401 Unauthorized` if credentials are invalid

**Example Response:**

```json
{
  "success": true,
  "message": "Login successful",
  "token": "jwt-token-here"
}
```

------

### POST `/auth/logout`

Log out the current user (invalidate token).

**Request Headers:**
- `Authorization: Bearer <token>`

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

------

### POST `/auth/reset_password_request`

Request a password reset.

**Request Body (JSON):**

```json
{
  "email": "string"
}
```

**Response:**

- `200 OK` on success (regardless of whether email exists)

**Example Response:**

```json
{
  "success": true,
  "message": "Password reset instructions sent to email if it exists"
}
```

------

### POST `/auth/reset_password/<token>`

Reset password using a valid token.

**Request Body (JSON):**

```json
{
  "password": "string",
  "confirm_password": "string"
}
```

**Response:**

- `200 OK` on success
- `400 Bad Request` if passwords don't match
- `401 Unauthorized` if token is invalid

**Example Response:**

```json
{
  "success": true,
  "message": "Password reset successful"
}
```

------

## 2. Dashboard

### GET `/dashboard`

Get dashboard data for the current user.

**Request Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `days` (optional): Number of days of data to retrieve (default: 7)
- `refresh` (optional): Force refresh of cached data (values: 0 or 1)

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "data": {
    "weight_data": [
      {
        "date": "2024-05-10",
        "value": 70.5,
        "unit": "kg"
      }
    ],
    "heart_rate_data": [
      {
        "date": "2024-05-10",
        "min": 60,
        "max": 120,
        "avg": 75,
        "unit": "bpm"
      }
    ],
    "activity_data": [
      {
        "date": "2024-05-10",
        "steps": 8000
      }
    ],
    "sleep_data": [
      {
        "date": "2024-05-10",
        "duration": 480,
        "durationHours": 8.0,
        "quality": "good"
      }
    ]
  }
}
```

------

### GET `/dashboard/summary`

Get summary statistics for the current user.

**Request Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `days` (optional): Number of days of data to analyze (default: 7)

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "summary": {
    "weight": {
      "current": 70.5,
      "change": -0.5,
      "unit": "kg"
    },
    "heart_rate": {
      "avg": 72,
      "min": 58,
      "max": 155,
      "unit": "bpm"
    },
    "activity": {
      "avg_steps": 8500,
      "total_steps": 59500
    },
    "sleep": {
      "avg_duration": 7.5,
      "unit": "hours"
    }
  }
}
```

------

### GET `/dashboard/goals-achievements`

Get goals and achievements for the current user.

**Request Headers:**
- `Authorization: Bearer <token>`

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "goals": [
    {
      "id": 1,
      "category": "steps",
      "target_value": 10000,
      "current_value": 8500,
      "unit": "steps",
      "progress": 85
    }
  ],
  "achievements": [
    {
      "id": 2,
      "name": "Step Master",
      "description": "Walk 10,000 steps daily for a week",
      "earned_at": "2024-05-08T10:30:00"
    }
  ]
}
```

------

## 3. User Profile

### GET `/user/profile`

Get the current user's profile information.

**Request Headers:**
- `Authorization: Bearer <token>`

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "profile": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "gender": "male",
    "birth_date": "1990-01-01",
    "height": 180,
    "weight": 75.5
  }
}
```

------

### PUT `/user/profile`

Update the current user's profile information.

**Request Headers:**
- `Authorization: Bearer <token>`

**Request Body (JSON):**

```json
{
  "first_name": "string",
  "last_name": "string",
  "gender": "string",
  "birth_date": "YYYY-MM-DD",
  "height": 0.0,
  "weight": 0.0
}
```

**Response:**

- `200 OK` on success
- `400 Bad Request` if validation fails

**Example Response:**

```json
{
  "success": true,
  "message": "Profile updated successfully"
}
```

------

### PUT `/user/change_password`

Change the current user's password.

**Request Headers:**
- `Authorization: Bearer <token>`

**Request Body (JSON):**

```json
{
  "current_password": "string",
  "new_password": "string",
  "confirm_password": "string"
}
```

**Response:**

- `200 OK` on success
- `400 Bad Request` if validation fails
- `401 Unauthorized` if current password is incorrect

**Example Response:**

```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

------

### DELETE `/user/account`

Delete or deactivate the current user's account.

**Request Headers:**
- `Authorization: Bearer <token>`

**Request Body (JSON):**

```json
{
  "confirmation": "DELETE"
}
```

**Response:**

- `200 OK` on success
- `400 Bad Request` if confirmation is incorrect

**Example Response:**

```json
{
  "success": true,
  "message": "Account deactivated successfully"
}
```

------

## 4. Health Data

### GET `/weight`

Get weight data for the current user.

**Request Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `period` (optional): Time period (values: "daily", "weekly", "monthly", "six_months", "yearly", default: "weekly")
- `start_date` (optional): Start date in format YYYY-MM-DD
- `end_date` (optional): End date in format YYYY-MM-DD

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "timestamp": "2024-05-10T08:30:00",
      "value": 70.5,
      "unit": "kg"
    }
  ]
}
```

------

### POST `/weight`

Add a new weight record.

**Request Headers:**
- `Authorization: Bearer <token>`

**Request Body (JSON):**

```json
{
  "value": 0.0,
  "unit": "string",
  "timestamp": "YYYY-MM-DDTHH:MM:SS"
}
```

**Response:**

- `201 Created` on success
- `400 Bad Request` if validation fails

**Example Response:**

```json
{
  "success": true,
  "message": "Weight record added successfully",
  "record": {
    "id": 1,
    "timestamp": "2024-05-10T08:30:00",
    "value": 70.5,
    "unit": "kg"
  }
}
```

------

### GET `/heart-rate`

Get heart rate data for the current user.

**Request Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `period` (optional): Time period (values: "daily", "weekly", "monthly", "six_months", "yearly", default: "weekly")
- `start_date` (optional): Start date in format YYYY-MM-DD
- `end_date` (optional): End date in format YYYY-MM-DD

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "timestamp": "2024-05-10T08:30:00",
      "value": 72,
      "unit": "bpm"
    }
  ]
}
```

------

### POST `/heart-rate`

Add a new heart rate record.

**Request Headers:**
- `Authorization: Bearer <token>`

**Request Body (JSON):**

```json
{
  "value": 0,
  "unit": "string",
  "timestamp": "YYYY-MM-DDTHH:MM:SS"
}
```

**Response:**

- `201 Created` on success
- `400 Bad Request` if validation fails

**Example Response:**

```json
{
  "success": true,
  "message": "Heart rate record added successfully",
  "record": {
    "id": 1,
    "timestamp": "2024-05-10T08:30:00",
    "value": 72,
    "unit": "bpm"
  }
}
```

------

### GET `/activity`

Get activity data for the current user.

**Request Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `period` (optional): Time period (values: "daily", "weekly", "monthly", "six_months", "yearly", default: "weekly")
- `start_date` (optional): Start date in format YYYY-MM-DD
- `end_date` (optional): End date in format YYYY-MM-DD

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "timestamp": "2024-05-10T08:30:00",
      "activity_type": "walking",
      "total_steps": 8000,
      "total_distance": 6.2,
      "calories": 320
    }
  ]
}
```

------

### POST `/activity`

Add a new activity record.

**Request Headers:**
- `Authorization: Bearer <token>`

**Request Body (JSON):**

```json
{
  "activity_type": "string",
  "total_steps": 0,
  "total_distance": 0.0,
  "calories": 0,
  "timestamp": "YYYY-MM-DDTHH:MM:SS"
}
```

**Response:**

- `201 Created` on success
- `400 Bad Request` if validation fails

**Example Response:**

```json
{
  "success": true,
  "message": "Activity record added successfully",
  "record": {
    "id": 1,
    "timestamp": "2024-05-10T08:30:00",
    "activity_type": "walking",
    "total_steps": 8000,
    "total_distance": 6.2,
    "calories": 320
  }
}
```

------

### GET `/sleep`

Get sleep data for the current user.

**Request Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `period` (optional): Time period (values: "daily", "weekly", "monthly", "six_months", "yearly", default: "weekly")
- `start_date` (optional): Start date in format YYYY-MM-DD
- `end_date` (optional): End date in format YYYY-MM-DD

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "start_time": "2024-05-10T23:00:00",
      "end_time": "2024-05-11T07:00:00",
      "duration": 480,
      "deep_sleep": 120,
      "light_sleep": 240,
      "rem_sleep": 100,
      "awake": 20,
      "quality": "good"
    }
  ]
}
```

------

### POST `/sleep`

Add a new sleep record.

**Request Headers:**
- `Authorization: Bearer <token>`

**Request Body (JSON):**

```json
{
  "start_time": "YYYY-MM-DDTHH:MM:SS",
  "end_time": "YYYY-MM-DDTHH:MM:SS",
  "duration": 0,
  "deep_sleep": 0,
  "light_sleep": 0,
  "rem_sleep": 0,
  "awake": 0,
  "quality": "string"
}
```

**Response:**

- `201 Created` on success
- `400 Bad Request` if validation fails

**Example Response:**

```json
{
  "success": true,
  "message": "Sleep record added successfully",
  "record": {
    "id": 1,
    "start_time": "2024-05-10T23:00:00",
    "end_time": "2024-05-11T07:00:00",
    "duration": 480,
    "quality": "good"
  }
}
```

------

## 5. Goals and Achievements

### GET `/goals`

Get goals for the current user.

**Request Headers:**
- `Authorization: Bearer <token>`

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "goals": [
    {
      "id": 1,
      "category": "steps",
      "target_value": 10000,
      "current_value": 8500,
      "unit": "steps",
      "timeframe": "daily",
      "start_date": "2024-05-01",
      "end_date": "2024-05-31",
      "progress": 85,
      "completed": false
    }
  ]
}
```

------

### POST `/goals`

Create a new goal.

**Request Headers:**
- `Authorization: Bearer <token>`

**Request Body (JSON):**

```json
{
  "category": "string",
  "target_value": 0.0,
  "unit": "string",
  "timeframe": "string",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD"
}
```

**Response:**

- `201 Created` on success
- `400 Bad Request` if validation fails

**Example Response:**

```json
{
  "success": true,
  "message": "Goal created successfully",
  "goal": {
    "id": 1,
    "category": "steps",
    "target_value": 10000,
    "unit": "steps",
    "timeframe": "daily"
  }
}
```

------

### PUT `/goals/<goal_id>`

Update an existing goal.

**Request Headers:**
- `Authorization: Bearer <token>`

**Request Body (JSON):**

```json
{
  "target_value": 0.0,
  "current_value": 0.0,
  "end_date": "YYYY-MM-DD",
  "completed": false
}
```

**Response:**

- `200 OK` on success
- `400 Bad Request` if validation fails
- `404 Not Found` if goal doesn't exist

**Example Response:**

```json
{
  "success": true,
  "message": "Goal updated successfully",
  "goal": {
    "id": 1,
    "target_value": 12000,
    "current_value": 9000,
    "progress": 75
  }
}
```

------

### DELETE `/goals/<goal_id>`

Delete a goal.

**Request Headers:**
- `Authorization: Bearer <token>`

**Response:**

- `200 OK` on success
- `404 Not Found` if goal doesn't exist

**Example Response:**

```json
{
  "success": true,
  "message": "Goal deleted successfully"
}
```

------

### GET `/achievements`

Get achievements for the current user.

**Request Headers:**
- `Authorization: Bearer <token>`

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "achievements": [
    {
      "id": 1,
      "name": "Step Master",
      "description": "Walk 10,000 steps daily for a week",
      "category": "steps",
      "icon": "steps-icon",
      "level": "gold",
      "earned_at": "2024-05-10T18:30:00"
    }
  ]
}
```

------

## 6. Data Import/Export

### POST `/upload`

Upload health data from a file.

**Request Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Request Body:**
- `file`: File to upload
- `dataSource`: Source of the data (e.g., "fitbit", "apple_health", "google_fit")

**Response:**

- `200 OK` on success
- `400 Bad Request` if file validation fails

**Example Response:**

```json
{
  "success": true,
  "message": "File uploaded and processed successfully",
  "import_log_id": 123
}
```

------

### GET `/import_history`

Get import history for the current user.

**Request Headers:**
- `Authorization: Bearer <token>`

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "import_logs": [
    {
      "id": 123,
      "data_source": "fitbit",
      "file_name": "fitbit_export_2024-05-10.csv",
      "status": "success",
      "records_processed": 150,
      "created_at": "2024-05-10T15:30:00"
    }
  ]
}
```

------

### GET `/export_data`

Export user data in CSV/JSON format.

**Request Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `format` (optional): Export format (values: "csv", "json", default: "csv")
- `data_types` (optional): Comma-separated list of data types to export (default: all)

**Response:**

- `200 OK` on success with file download

------

## 7. Data Sharing

### GET `/share/links`

Get all share links for the current user.

**Request Headers:**
- `Authorization: Bearer <token>`

**Response:**

- `200 OK` on success

**Example Response:**

```json
{
  "success": true,
  "share_links": [
    {
      "id": 1,
      "share_token": "abc123def456",
      "name": "Doctor Visit",
      "expires_at": "2024-06-10T00:00:00",
      "has_password": true,
      "template_type": "medical",
      "created_at": "2024-05-10T15:30:00",
      "access_count": 3
    }
  ]
}
```

------

### POST `/share/links`

Create a new share link.

**Request Headers:**
- `Authorization: Bearer <token>`

**Request Body (JSON):**

```json
{
  "name": "string",
  "privacy_level": "string",
  "modules": ["dashboard", "heartrate", "activity", "weight", "sleep", "goals", "achievements"],
  "template_type": "string",
  "expiration_days": 0,
  "password": "string",
  "personal_message": "string",
  "days": 30
}
```

**Response:**

- `200 OK` on success
- `400 Bad Request` if validation fails

**Example Response:**

```json
{
  "success": true,
  "share_link": {
    "id": 1,
    "share_token": "abc123def456",
    "url": "/share/view/abc123def456"
  }
}
```

------

### DELETE `/share/links/<share_token>`

Delete a share link.

**Request Headers:**
- `Authorization: Bearer <token>`

**Response:**

- `200 OK` on success
- `404 Not Found` if share link doesn't exist

**Example Response:**

```json
{
  "success": true,
  "message": "Share link deleted successfully"
}
```

------

### GET `/share/links/<share_token>`

Get details for a specific share link.

**Request Headers:**
- `Authorization: Bearer <token>`

**Response:**

- `200 OK` on success
- `404 Not Found` if share link doesn't exist

**Example Response:**

```json
{
  "success": true,
  "share_link": {
    "id": 1,
    "share_token": "abc123def456",
    "name": "Doctor Visit",
    "expires_at": "2024-06-10T00:00:00",
    "has_password": true,
    "privacy_level": "overview",
    "modules": ["dashboard", "heartrate", "weight"],
    "template_type": "medical",
    "personal_message": "For my annual checkup",
    "created_at": "2024-05-10T15:30:00"
  }
}
```

------

## 8. Error Responses

All endpoints may return the following error responses:

### `400 Bad Request`

```json
{
  "success": false,
  "message": "Error message describing the problem",
  "errors": {
    "field_name": "Specific error for this field"
  }
}
```

### `401 Unauthorized`

```json
{
  "success": false,
  "message": "Authentication required"
}
```

### `403 Forbidden`

```json
{
  "success": false,
  "message": "You don't have permission to access this resource"
}
```

### `404 Not Found`

```json
{
  "success": false,
  "message": "Resource not found"
}
```

### `500 Internal Server Error`

```json
{
  "success": false,
  "message": "An unexpected error occurred"
}
``` 
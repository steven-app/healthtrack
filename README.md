# HealthTrack - Health and Fitness Tracking Application

A comprehensive health and fitness tracking application built with Flask, SQLite, and Bootstrap. Track your activities, monitor health metrics, set goals, and share achievements.

## Features

- **Dashboard**: Get a comprehensive overview of all your health metrics in one place
- **Activity Tracking**: Monitor steps, distance, and calories burned
- **Heart Rate Monitoring**: Track your heart rate patterns over time
- **Sleep Analysis**: Visualize your sleep duration and quality
- **Weight Management**: Keep track of your weight changes
- **Goal Setting**: Set and track personalized health goals
- **Achievements**: Earn achievements for reaching milestones
- **Data Sharing**: Securely share your health data with healthcare providers or family
- **Data Import**: Import health data from various sources
- **Dark Mode**: Toggle between light and dark themes for comfortable viewing

## Technology Stack

- Backend: Flask with SQLAlchemy
- Database: SQLite
- Frontend: Bootstrap, jQuery, AJAX
- Data Visualization: Plotly.js
- File Parsing: Pandas, xmltodict

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/healthtrack.git
cd healthtrack
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables (adjust as needed):
```bash
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
```

5. Initialize the database:
```bash
python -m app.init_db
```

   Or, if you just want to create tables without dropping existing data:
```bash
python -m app.init_db --create-only
```

6. Run the application:
```bash
flask run
```

7. Open your browser and navigate to `http://127.0.0.1:5000`

8. Default admin account:
   - Email: admin@example.com
   - Password: admin@123

## Project Structure

- `app/`: Main application package
  - `models/`: Database models
  - `routes/`: Route blueprints
  - `services/`: Business logic
  - `templates/`: HTML templates
  - `static/`: CSS, JavaScript, and images
  - `utils/`: Helper functions

## Database

The application is configured to use SQLite by default, with the database file stored in the `instance` folder. When deployed to render.com or similar platforms, the database tables will be automatically created on startup if they don't exist.

If you need to manually initialize or reset the database:
- Use `python -m app.init_db` to completely reset the database (drops all existing tables)
- Use `python -m app.init_db --create-only` to only create missing tables without losing data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
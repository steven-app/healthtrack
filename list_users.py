from app import create_app, db
from app.models.user import User

def list_users():
    """List all users in the database"""
    app = create_app()
    with app.app_context():
        users = User.query.all()
        print(f"Total users: {len(users)}")
        print("-" * 80)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Admin':<10}")
        print("-" * 80)
        for user in users:
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {'Yes' if user.is_admin else 'No':<10}")

if __name__ == "__main__":
    list_users() 
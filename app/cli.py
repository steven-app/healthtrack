import click
from flask.cli import with_appcontext
from app import db

@click.command('init-achievements')
@with_appcontext
def init_achievements_command():
    """Initialize achievements in the database."""
    from app.utils.init_achievements import init_achievements
    init_achievements()
    click.echo('Initialized achievements.')

@click.command('update-goals')
@with_appcontext
def update_goals_command():
    """Update progress for all active goals."""
    from app.models.goal import Goal
    from app.services.goal_service import GoalService
    
    goals = Goal.query.filter_by(completed=False).all()
    for goal in goals:
        GoalService.update_goal_progress(goal)
    
    click.echo(f'Updated progress for {len(goals)} goals.')

@click.command('check-achievements')
@click.argument('user_id', type=int)
@with_appcontext
def check_achievements_command(user_id):
    """Check and update achievements for a specific user."""
    from app.services.achievement_service import check_achievements_for_user
    
    achievements = check_achievements_for_user(user_id)
    if achievements:
        click.echo(f'User earned {len(achievements)} new achievements!')
        for a in achievements:
            click.echo(f' - {a.name}: {a.description}')
    else:
        click.echo('No new achievements earned.')

def register_commands(app):
    """Register custom CLI commands."""
    app.cli.add_command(init_achievements_command)
    app.cli.add_command(update_goals_command)
    app.cli.add_command(check_achievements_command) 
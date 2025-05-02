#!/usr/bin/env python
import os
import click
from flask.cli import FlaskGroup
from app import create_app, db
from app.models.goal import Goal
from app.models.achievement import Achievement, UserAchievement
from app.utils.init_achievements import init_achievements

app = create_app()
cli = FlaskGroup(create_app=create_app)

@app.cli.command('init-achievements')
def init_achievements_command():
    """Initialize achievements in database."""
    with app.app_context():
        init_achievements()
    click.echo('Initialized achievements.')

@app.cli.command('check-achievements')
@click.argument('user_id', type=int)
def check_user_achievements(user_id):
    """Check and update achievements for a specific user."""
    from app.services.achievement_service import check_achievements_for_user
    with app.app_context():
        achievements = check_achievements_for_user(user_id)
        if achievements:
            click.echo(f'User earned {len(achievements)} new achievements!')
            for a in achievements:
                click.echo(f' - {a.name}: {a.description}')
        else:
            click.echo('No new achievements earned.')

@app.cli.command('update-goals')
def update_all_goals():
    """Update progress on all active goals."""
    from app.models.goal import Goal
    from app.services.goal_service import GoalService
    with app.app_context():
        goals = Goal.query.filter_by(completed=False).all()
        for goal in goals:
            GoalService.update_goal_progress(goal)
        click.echo(f'Updated progress for {len(goals)} goals.')

@app.cli.command('create-database')
def create_database():
    """Create database tables."""
    with app.app_context():
        db.create_all()
    click.echo('Database tables created.')

@app.cli.command('drop-database')
@click.confirmation_option(prompt='Are you sure you want to drop all tables?')
def drop_database():
    """Drop all database tables."""
    with app.app_context():
        db.drop_all()
    click.echo('Database tables dropped.')

if __name__ == '__main__':
    cli() 
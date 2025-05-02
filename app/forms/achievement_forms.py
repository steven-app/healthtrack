from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, FloatField
from wtforms.validators import DataRequired, Length, Optional

class AchievementForm(FlaskForm):
    """Form for creating and editing achievements"""
    name = StringField('Achievement Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=255)])
    
    category = SelectField('Category', choices=[
        ('steps', 'Steps'),
        ('weight', 'Weight'),
        ('sleep', 'Sleep'),
        ('heart_rate', 'Heart Rate'),
        ('general', 'General')
    ], validators=[DataRequired()])
    
    icon = StringField('Icon (FontAwesome)', validators=[Length(max=100)], 
                     description="Font Awesome icon name (e.g., 'trophy', 'medal', 'walking')")
    
    level = SelectField('Level', choices=[
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold')
    ], validators=[DataRequired()])
    
    condition_type = SelectField('Condition Type', choices=[
        ('milestone', 'Milestone'),
        ('streak', 'Streak'),
        ('improvement', 'Improvement')
    ], validators=[DataRequired()], 
    description="The type of condition to check for this achievement")
    
    condition_value = FloatField('Condition Value', validators=[DataRequired()],
                                description="The numeric value for the condition (e.g., 10000 steps, 7 day streak)")
    
    progress_related = BooleanField('Progress Related', default=False,
                                  description="Is this achievement related to user progress?")
    
    goal_related = BooleanField('Goal Related', default=False,
                              description="Is this achievement related to completing goals?") 
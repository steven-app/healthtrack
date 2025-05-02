from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

class GoalForm(FlaskForm):
    category = SelectField('Category', choices=[
        ('steps', 'Steps'), 
        ('weight', 'Weight'), 
        ('sleep', 'Sleep Duration'), 
        ('heart_rate', 'Heart Rate')
    ], validators=[DataRequired()])
    
    target_value = FloatField('Target Value', validators=[DataRequired(), NumberRange(min=0)])
    
    unit = SelectField('Unit', choices=[
        ('steps', 'steps'),
        ('kg', 'kg'),
        ('min', 'minutes'),
        ('hours', 'hours'),
        ('bpm', 'beats per minute')
    ], validators=[DataRequired()])
    
    timeframe = SelectField('Timeframe', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], validators=[DataRequired()])
    
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date (Optional)', validators=[Optional()])
    
    submit = SubmitField('Create Goal') 
from datetime import datetime, timedelta, date
import calendar
from typing import Dict, List, Tuple, Any, Optional, Union

# Fitbit style chart color definitions
CHART_COLORS = {
    'primary': '#00B0B9',          # Blue-green (primary color)
    'sleep': '#7177F7',            # Light purple (for sleep data)
    'heart_rate': '#FF2D55',       # Coral red (for heart rate data)
    'activity': '#4CD964',         # Bright green (for activity data)
    'weight': '#5AC8FA',           # Sky blue (for weight data)
    'accent': '#FF4081',           # Bright pink (for accent)
    'warning': '#FFCC00'           # Yellow (for warnings)
}

def get_time_range(period: str) -> Tuple[datetime, datetime]:
    """
    Calculate time range based on current time for looking back
    
    Args:
        period: Type of time period ('daily', 'weekly', 'monthly', 'six_months', 'yearly')
        
    Returns:
        Tuple of start date and end date
    """
    end_date = datetime.utcnow()
    
    if period == 'daily':
        # Today from 00:00 to 23:59
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1) - timedelta(microseconds=1)
    elif period == 'weekly':
        # Past 7 days (including today)
        start_date = end_date - timedelta(days=6)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'monthly':
        # Past 30 days (including today)
        start_date = end_date - timedelta(days=29)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'six_months':
        # Past 180 days (including today)
        start_date = end_date - timedelta(days=179)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'yearly':
        # Past 12 complete months, including current month
        # First find the first day of current month
        current_month_start = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Then go back 11 months
        start_date = current_month_start
        for _ in range(11):
            # Calculate previous month
            if start_date.month == 1:
                start_date = start_date.replace(year=start_date.year-1, month=12)
            else:
                start_date = start_date.replace(month=start_date.month-1)
    else:
        # Default to past 7 days
        start_date = end_date - timedelta(days=6)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return start_date, end_date

def generate_time_slots(period: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """
    Generate time slots for the specified time range
    
    Args:
        period: Type of time period ('daily', 'weekly', 'monthly', 'six_months', 'yearly')
        start_date: Start time
        end_date: End time
        
    Returns:
        List of time slots, each with start time, end time and label
    """
    slots = []
    
    if period == 'daily':
        # Divide into hourly slots
        current = start_date
        while current < end_date:
            slot_end = min(current + timedelta(hours=1), end_date)
            slots.append({
                'start': current,
                'end': slot_end,
                'label': current.strftime('%I %p')  # 12-hour format, e.g. "01 AM"
            })
            current = slot_end
    
    elif period == 'weekly':
        # Divide into daily slots
        current = start_date
        while current < end_date:
            slot_end = min(current + timedelta(days=1), end_date)
            slots.append({
                'start': current,
                'end': slot_end,
                'label': current.strftime('%a, %d')  # e.g. "Mon, 15"
            })
            current = slot_end
    
    elif period == 'monthly':
        # Divide into daily slots
        current = start_date
        while current < end_date:
            slot_end = min(current + timedelta(days=1), end_date)
            slots.append({
                'start': current,
                'end': slot_end,
                'label': current.strftime('%d')  # date, e.g. "15"
            })
            current = slot_end
    
    elif period == 'six_months':
        # Divide into weekly slots
        current = start_date
        while current < end_date:
            # Calculate the end of this week (00:00 next Monday)
            days_to_next_monday = (7 - current.weekday()) % 7
            if days_to_next_monday == 0:
                days_to_next_monday = 7
            
            week_end = current + timedelta(days=days_to_next_monday)
            week_end = week_end.replace(hour=0, minute=0, second=0, microsecond=0)
            
            slot_end = min(week_end, end_date)
            
            # Only add if this week has at least one day
            if current < slot_end:
                slots.append({
                    'start': current,
                    'end': slot_end,
                    'label': f"{current.strftime('%b %d')}-{(slot_end - timedelta(microseconds=1)).strftime('%b %d')}"
                })
            
            current = slot_end
    
    elif period == 'yearly':
        # Divide into monthly slots
        current = start_date.replace(day=1)  # Ensure we start from the first of the month
        
        while current < end_date:
            # Calculate the first day of next month
            if current.month == 12:
                next_month = current.replace(year=current.year + 1, month=1)
            else:
                next_month = current.replace(month=current.month + 1)
            
            slot_end = min(next_month, end_date)
            
            slots.append({
                'start': current,
                'end': slot_end,
                'label': current.strftime('%b')  # Month abbreviation, e.g. "Jan"
            })
            
            current = next_month
    
    return slots

def format_empty_data_structure(period: str, metric_keys: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Create initial empty data structure for different time periods
    
    Args:
        period: Type of time period
        metric_keys: List of metric names to record
        
    Returns:
        Initialized data structure
    """
    result = {}
    
    # Get time range
    start_date, end_date = get_time_range(period)
    
    # Generate time slots
    slots = generate_time_slots(period, start_date, end_date)
    
    # Create data structure for each time slot
    for slot in slots:
        slot_key = slot['label']
        result[slot_key] = {key: 0 for key in metric_keys}
        result[slot_key]['count'] = 0
    
    return result, [slot['label'] for slot in slots]

def prepare_chart_data(
    data_points: Dict[str, Dict[str, float]], 
    labels: List[str],
    datasets_config: List[Dict[str, Any]],
    sparse_labels: bool = False,
    label_interval: int = 2
) -> Dict[str, Any]:
    """
    Prepare data in a format usable for charts
    
    Args:
        data_points: Dictionary of data points, keys are labels, values are dictionaries of metrics
        labels: List of chart labels
        datasets_config: List of dataset configurations
        sparse_labels: Whether to show only some labels to avoid crowding
        label_interval: If sparse_labels is True, show every nth label (n = label_interval)
        
    Returns:
        Chart data structure
    """
    # Create a display_labels list that has empty strings for labels we want to hide
    display_labels = labels.copy()
    if sparse_labels:
        for i in range(len(display_labels)):
            if i % label_interval != 0:
                display_labels[i] = ''
    
    chart_data = {
        'labels': display_labels,
        'datasets': []
    }
    
    for config in datasets_config:
        metric = config['metric']
        
        # Use predefined Fitbit style colors
        backgroundColor = config.get('backgroundColor', CHART_COLORS['primary'])
        borderColor = config.get('borderColor', CHART_COLORS['primary'])
        
        # Automatically select colors based on metric name
        if 'heart' in metric.lower() or 'pulse' in metric.lower():
            backgroundColor = CHART_COLORS['heart_rate']
            borderColor = CHART_COLORS['heart_rate']
        elif 'sleep' in metric.lower() or 'rest' in metric.lower():
            backgroundColor = CHART_COLORS['sleep']
            borderColor = CHART_COLORS['sleep']
        elif 'weight' in metric.lower() or 'mass' in metric.lower():
            backgroundColor = CHART_COLORS['weight']
            borderColor = CHART_COLORS['weight']
        elif 'step' in metric.lower() or 'activ' in metric.lower() or 'walk' in metric.lower():
            backgroundColor = CHART_COLORS['activity']
            borderColor = CHART_COLORS['activity']
        
        # Create custom version with transparency
        backgroundColor = add_alpha(backgroundColor, 0.5)
        
        dataset = {
            'label': config['label'],
            'backgroundColor': backgroundColor,
            'borderColor': borderColor,
            'borderWidth': config.get('borderWidth', 2),
            'data': []
        }
        
        for label in labels:
            if label in data_points:
                dataset['data'].append(data_points[label].get(metric, 0))
            else:
                dataset['data'].append(0)
        
        chart_data['datasets'].append(dataset)
    
    return chart_data

def add_alpha(hex_color: str, alpha: float) -> str:
    """Convert hex color to RGBA format with transparency
    
    Args:
        hex_color: Hexadecimal color code (e.g. #RRGGBB)
        alpha: Transparency value (0-1)
        
    Returns:
        RGBA formatted color string
    """
    # Ensure hex_color is a valid hexadecimal color
    if not hex_color.startswith('#') or len(hex_color) != 7:
        return hex_color
    
    # Extract RGB values from hexadecimal color
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    
    # Return RGBA format
    return f'rgba({r}, {g}, {b}, {alpha})' 
import json
from typing import Dict, List, Any
from datetime import datetime
from .base_parser import BaseParser

class GoogleFitParser(BaseParser):
    """Parser for Google Fit data"""
    
    def __init__(self):
        super().__init__()
        self.data_source = 'google_fit'
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse Google Fit data from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            records = []
            for point in data.get('point', []):
                record = self._parse_data_point(point)
                if record and self.validate_data(record):
                    records.append(self.format_record(record))
            
            return records
            
        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid JSON format: {str(e)}')
    
    def _parse_data_point(self, point: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual data point from Google Fit"""
        try:
            data_type = point.get('dataTypeName', '').lower()
            value = point.get('value', [{}])[0].get('fpVal')
            start_time = point.get('startTimeNanos')
            end_time = point.get('endTimeNanos')
            
            if not all([data_type, value, start_time]):
                return None
            
            # Convert nanoseconds to datetime
            timestamp = datetime.fromtimestamp(int(start_time) / 1e9)
            
            return {
                'data_type': data_type,
                'value': value,
                'unit': self._get_unit(data_type),
                'timestamp': timestamp
            }
            
        except (KeyError, ValueError) as e:
            raise ValueError(f'Error parsing data point: {str(e)}')
    
    def _get_unit(self, data_type: str) -> str:
        """Get unit for data type"""
        units = {
            'com.google.heart_rate.bpm': 'bpm',
            'com.google.step_count.delta': 'steps',
            'com.google.distance.delta': 'meters',
            'com.google.calories.expended': 'kcal',
            'com.google.weight': 'kg',
            'com.google.height': 'meters',
            'com.google.body.fat.percentage': 'percent',
            'com.google.blood_pressure.systolic': 'mmHg',
            'com.google.blood_pressure.diastolic': 'mmHg'
        }
        return units.get(data_type, '') 
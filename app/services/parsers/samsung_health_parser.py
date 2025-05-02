import json
import csv
from typing import Dict, List, Any
from datetime import datetime
from .base_parser import BaseParser

class SamsungHealthParser(BaseParser):
    """Parser for Samsung Health data"""
    
    def __init__(self):
        super().__init__()
        self.data_source = 'samsung_health'
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse Samsung Health data from JSON or CSV file"""
        if file_path.endswith('.json'):
            return self._parse_json(file_path)
        elif file_path.endswith('.csv'):
            return self._parse_csv(file_path)
        else:
            raise ValueError('Unsupported file format')
    
    def _parse_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse Samsung Health data from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            records = []
            for record in data.get('data', []):
                parsed_record = self._parse_record(record)
                if parsed_record and self.validate_data(parsed_record):
                    records.append(self.format_record(parsed_record))
            
            return records
            
        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid JSON format: {str(e)}')
    
    def _parse_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse Samsung Health data from CSV file"""
        try:
            records = []
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    record = self._parse_csv_row(row)
                    if record and self.validate_data(record):
                        records.append(self.format_record(record))
            
            return records
            
        except csv.Error as e:
            raise ValueError(f'Invalid CSV format: {str(e)}')
    
    def _parse_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual record from Samsung Health JSON"""
        try:
            data_type = record.get('type', '').lower()
            value = record.get('value')
            start_time = record.get('start_time')
            
            if not all([data_type, value, start_time]):
                return None
            
            return {
                'data_type': data_type,
                'value': value,
                'unit': self._get_unit(data_type),
                'timestamp': datetime.fromisoformat(start_time)
            }
            
        except (KeyError, ValueError) as e:
            raise ValueError(f'Error parsing record: {str(e)}')
    
    def _parse_csv_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual row from Samsung Health CSV"""
        try:
            data_type = row.get('type', '').lower()
            value = row.get('value')
            timestamp = row.get('timestamp')
            
            if not all([data_type, value, timestamp]):
                return None
            
            return {
                'data_type': data_type,
                'value': value,
                'unit': self._get_unit(data_type),
                'timestamp': datetime.fromisoformat(timestamp)
            }
            
        except (KeyError, ValueError) as e:
            raise ValueError(f'Error parsing CSV row: {str(e)}')
    
    def _get_unit(self, data_type: str) -> str:
        """Get unit for data type"""
        units = {
            'step_count': 'steps',
            'distance': 'meters',
            'calorie': 'kcal',
            'heart_rate': 'bpm',
            'weight': 'kg',
            'height': 'meters',
            'body_fat': 'percent',
            'blood_pressure_systolic': 'mmHg',
            'blood_pressure_diastolic': 'mmHg',
            'sleep': 'minutes',
            'exercise': 'minutes',
            'water': 'ml',
            'caffeine': 'mg'
        }
        return units.get(data_type, '') 
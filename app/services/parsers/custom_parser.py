import csv
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_parser import BaseParser

class CustomParser(BaseParser):
    """Parser for custom health data formats"""
    
    def __init__(self, data_source: str = 'custom', field_mapping: Optional[Dict[str, str]] = None):
        super().__init__()
        self.data_source = data_source
        self.field_mapping = field_mapping or {
            'type': 'data_type',
            'value': 'value',
            'timestamp': 'timestamp',
            'unit': 'unit'
        }
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse custom health data from JSON or CSV file"""
        if file_path.endswith('.json'):
            return self._parse_json(file_path)
        elif file_path.endswith('.csv'):
            return self._parse_csv(file_path)
        else:
            raise ValueError('Unsupported file format')
    
    def _parse_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse custom health data from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            records = []
            for record in data:
                parsed_record = self._parse_record(record)
                if parsed_record and self.validate_data(parsed_record):
                    records.append(self.format_record(parsed_record))
            
            return records
            
        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid JSON format: {str(e)}')
    
    def _parse_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse custom health data from CSV file"""
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
        """Parse individual record from custom JSON"""
        try:
            mapped_record = {}
            for source_field, target_field in self.field_mapping.items():
                if source_field in record:
                    mapped_record[target_field] = record[source_field]
            
            if not all(field in mapped_record for field in ['data_type', 'value', 'timestamp']):
                return None
            
            return mapped_record
            
        except (KeyError, ValueError) as e:
            raise ValueError(f'Error parsing record: {str(e)}')
    
    def _parse_csv_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual row from custom CSV"""
        try:
            mapped_record = {}
            for source_field, target_field in self.field_mapping.items():
                if source_field in row:
                    mapped_record[target_field] = row[source_field]
            
            if not all(field in mapped_record for field in ['data_type', 'value', 'timestamp']):
                return None
            
            return mapped_record
            
        except (KeyError, ValueError) as e:
            raise ValueError(f'Error parsing CSV row: {str(e)}')
    
    def set_field_mapping(self, field_mapping: Dict[str, str]):
        """Set custom field mapping"""
        self.field_mapping = field_mapping 
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import os

class BaseParser(ABC):
    """Base class for all health data parsers"""
    
    def __init__(self):
        self.data_source = self.__class__.__name__.replace('Parser', '').lower()
    
    @abstractmethod
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse health data from file and return list of records"""
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate health data record"""
        required_fields = ['data_type', 'value', 'timestamp']
        return all(field in data for field in required_fields)
    
    def convert_timestamp(self, timestamp: Any) -> datetime:
        """Convert various timestamp formats to datetime"""
        if isinstance(timestamp, datetime):
            return timestamp
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp)
            except ValueError:
                try:
                    return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    raise ValueError(f'Unsupported timestamp format: {timestamp}')
        raise ValueError(f'Unsupported timestamp type: {type(timestamp)}')
    
    def normalize_value(self, value: Any, unit: Optional[str] = None) -> float:
        """Convert value to float and handle unit conversions"""
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(f'Invalid value format: {value}')
    
    def format_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format health data record to standard format"""
        return {
            'data_source': self.data_source,
            'data_type': data.get('data_type'),
            'value': self.normalize_value(data.get('value')),
            'unit': data.get('unit'),
            'timestamp': self.convert_timestamp(data.get('timestamp'))
        }

    def save_to_csv(self, data, filename):
        df = pd.DataFrame(data)
        output_path = os.path.join(self.output_dir, filename)
        df.to_csv(output_path, index=False)
        return output_path 
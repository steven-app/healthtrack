import os
import zipfile
import xml.etree.ElementTree as ET
import csv
from datetime import datetime, timedelta
import logging
from app import db
from app.models import ImportLog, Weight, HeartRate, Activity, Sleep
from app.utils.error_handlers import FileValidationError, DataImportError
import pandas as pd
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_datetime(datetime_str):
    """
    Parse datetime string with timezone support.
    Handles formats like:
    - '2020-07-26 17:23:00 +0800'
    - '2020-07-26T17:23:00+08:00'
    """
    # Try direct parsing first
    try:
        return datetime.fromisoformat(datetime_str)
    except ValueError:
        pass
    
    # Try parsing with timezone fix
    try:
        # Handle format: '2020-07-26 17:23:00 +0800'
        if '+' in datetime_str:
            # Split into datetime and timezone
            dt_part, tz_part = datetime_str.split('+')
            dt_part = dt_part.strip()
            
            # Format timezone from +0800 to +08:00
            if len(tz_part) == 4:  # Format: 0800
                tz_part = f"{tz_part[:2]}:{tz_part[2:]}"
            
            # Combine and parse
            return datetime.fromisoformat(f"{dt_part}+{tz_part}")
        
        # Handle other formats or raise error
        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        raise ValueError(f"Unable to parse datetime: {datetime_str}. Error: {str(e)}")

class DataImportService:
    def __init__(self, user_id, import_log=None):
        self.user_id = user_id
        self.import_log = import_log
        self.logger = logging.getLogger(__name__)
        self.batch_size = 10000  

    def check_imported_data(self):
        """Check data in each table for the current user"""
        try:
            self.logger.info(f"Checking imported data for user {self.user_id}")
            data = {
                'weight': Weight.query.filter_by(user_id=self.user_id).count(),
                'heart_rate': HeartRate.query.filter_by(user_id=self.user_id).count(),
                'activity': Activity.query.filter_by(user_id=self.user_id).count(),
                'sleep': Sleep.query.filter_by(user_id=self.user_id).count()
            }
            self.logger.info(f"Found existing data: {data}")
            return data
        except Exception as e:
            self.logger.error(f"Error checking imported data: {str(e)}")
            raise DataImportError(f'Error checking imported data: {str(e)}')

    def _validate_csv_files(self, output_dir):
        """Validate the existence and basic format of CSV files"""
        required_files = ['weight.csv', 'heart_rate.csv', 'activity.csv', 'sleep.csv']
        missing_files = []
        invalid_files = []
        
        for file_name in required_files:
            file_path = os.path.join(output_dir, file_name)
            if not os.path.exists(file_path):
                missing_files.append(file_name)
                continue
            
            try:
                # Try to read the CSV file to validate format
                with open(file_path, 'r') as f:
                    # Check if file is empty or only has header
                    first_line = f.readline()
                    if not first_line.strip():
                        invalid_files.append(f"{file_name}: Empty file")
                        continue
                        
                    # If file has at least a header, consider it valid
                    # We'll handle empty data (just headers) during import
            except Exception as e:
                invalid_files.append(f"{file_name}: {str(e)}")
        
        if missing_files or invalid_files:
            error_msg = []
            if missing_files:
                error_msg.append(f"Missing files: {', '.join(missing_files)}")
            if invalid_files:
                error_msg.append(f"Invalid files: {', '.join(invalid_files)}")
            
            # Just log warnings instead of raising exception
            self.logger.warning('\n'.join(error_msg))

    def process_file(self, file, data_source, output_dir):
        """Process uploaded file and import data"""
        try:
            self.logger.info(f"Starting file processing for user {self.user_id}")
            
            # Validate CSV files
            try:
                self._validate_csv_files(output_dir)
                self.logger.info("CSV files validation successful")
            except FileValidationError as e:
                self.logger.warning(f"CSV validation failed: {str(e)}")
                # Continue processing even if some files are missing
            
            if not self.import_log:
                self.import_log = ImportLog(
                    user_id=self.user_id,
                    data_source=data_source,
                    file_name=file.filename if file else 'unknown',
                    status='processing'
                )
                db.session.add(self.import_log)
                db.session.commit()
                self.logger.info(f"Created import log with ID: {self.import_log.id}")
            
            # Import data from CSV files
            self._import_csv_data(output_dir)

            # Update import log
            self.import_log.status = 'success'
            self.import_log.completed_at = datetime.utcnow()
            db.session.commit()
            self.logger.info(f"File processing completed successfully. Records processed: {self.import_log.records_processed}")

            return True

        except Exception as e:
            self.logger.error(f"Error processing file: {str(e)}", exc_info=True)
            if self.import_log:
                self.import_log.status = 'failed'
                self.import_log.error_message = str(e)
                self.import_log.completed_at = datetime.utcnow()
                db.session.commit()
            raise DataImportError(f'Error processing file: {str(e)}')

    def _import_csv_data(self, output_dir):
        """Import data from CSV files"""
        records_to_commit = []
        sample_data = []
        total_processed = 0  # 添加总记录计数器
        
        def commit_batch_local():
            nonlocal records_to_commit, total_processed
            if records_to_commit:
                self._save_health_data_batch(records_to_commit)
                total_processed += len(records_to_commit)  # 更新总记录数
                records_to_commit = []

        try:
            # Process sleep data
            sleep_csv = os.path.join(output_dir, 'sleep.csv')
            if os.path.exists(sleep_csv):
                self.logger.info(f"Processing sleep data from {sleep_csv}")
                try:
                    # Check if file has data beyond headers
                    with open(sleep_csv, 'r') as f:
                        header = f.readline().strip()
                        has_data = bool(f.readline().strip())
                    
                    if not has_data:
                        self.logger.info("Sleep CSV file has only headers, no data to import")
                    else:
                        df = pd.read_csv(sleep_csv)
                        if not df.empty:
                            # Group sleep records by date to combine different stages
                            sleep_records = {}
                            for _, row in df.iterrows():
                                try:
                                    start_time = parse_datetime(row['start_time'])
                                    end_time = parse_datetime(row['end_time'])
                                    duration = (end_time - start_time).total_seconds() / 60  # Convert to minutes
                                    
                                    date_key = start_time.date()
                                    if date_key not in sleep_records:
                                        sleep_records[date_key] = {
                                            'start_time': start_time,
                                            'end_time': end_time,
                                            'total_duration': 0,
                                            'deep_sleep': 0,
                                            'light_sleep': 0,
                                            'rem_sleep': 0,
                                            'awake': 0
                                        }
                                    
                                    # Update sleep stage durations based on the stage column
                                    stage = row.get('stage', '').lower()
                                    if 'deep' in stage:
                                        sleep_records[date_key]['deep_sleep'] += duration
                                    elif 'light' in stage or 'core' in stage:
                                        sleep_records[date_key]['light_sleep'] += duration
                                    elif 'rem' in stage:
                                        sleep_records[date_key]['rem_sleep'] += duration
                                    elif 'awake' in stage:
                                        sleep_records[date_key]['awake'] += duration
                                    else:
                                        # If no stage information, add to total duration only
                                        sleep_records[date_key]['total_duration'] += duration
                                    
                                    # Update time range
                                    if end_time > sleep_records[date_key]['end_time']:
                                        sleep_records[date_key]['end_time'] = end_time
                                    if start_time < sleep_records[date_key]['start_time']:
                                        sleep_records[date_key]['start_time'] = start_time
                                    
                                except Exception as e:
                                    self.logger.error(f"Error processing sleep record: {str(e)}")
                                    continue
                            
                            # Create Sleep records from the grouped data
                            for sleep_data in sleep_records.values():
                                # 如果CSV文件包含source_name字段，使用它来填充notes
                                source_name = df.loc[df['start_time'] == sleep_data['start_time'].strftime('%Y-%m-%d %H:%M:%S'), 'source_name'].values
                                source_note = f"Source: {source_name[0]}" if len(source_name) > 0 else ""
                                
                                record = Sleep(
                                    user_id=self.user_id,
                                    import_log_id=self.import_log.id,
                                    duration=sleep_data['total_duration'],
                                    deep_sleep=sleep_data['deep_sleep'],
                                    light_sleep=sleep_data['light_sleep'],
                                    rem_sleep=sleep_data['rem_sleep'],
                                    awake=sleep_data['awake'],
                                    unit='minutes',
                                    start_time=sleep_data['start_time'],
                                    end_time=sleep_data['end_time'],
                                    timestamp=sleep_data['start_time'],
                                    notes=source_note
                                )
                                records_to_commit.append(record)
                                
                                # Store sample data
                                if len(sample_data) < 5:
                                    sample_data.append({
                                        'type': 'sleep',
                                        'duration': sleep_data['total_duration'],
                                        'deep_sleep': sleep_data['deep_sleep'],
                                        'light_sleep': sleep_data['light_sleep'],
                                        'rem_sleep': sleep_data['rem_sleep'],
                                        'awake': sleep_data['awake'],
                                        'unit': 'minutes',
                                        'start_time': sleep_data['start_time'].isoformat(),
                                        'end_time': sleep_data['end_time'].isoformat()
                                    })
                                
                                # Commit batch if size threshold reached
                                if len(records_to_commit) >= self.batch_size:
                                    commit_batch_local() # Use the local helper function
                except pd.errors.EmptyDataError:
                    self.logger.info("Sleep CSV is empty or has invalid format, skipping")
                except Exception as e:
                    self.logger.warning(f"Error processing sleep data: {str(e)}, skipping this data type")

            # Import weight data
            weight_csv = os.path.join(output_dir, 'weight.csv')
            if os.path.exists(weight_csv):
                self.logger.info(f"Processing weight data from {weight_csv}")
                try:
                    # Check if file has data beyond headers
                    with open(weight_csv, 'r') as f:
                        header = f.readline().strip()
                        has_data = bool(f.readline().strip())
                    
                    if not has_data:
                        self.logger.info("Weight CSV file has only headers, no data to import")
                    else:
                        df = pd.read_csv(weight_csv)
                        if not df.empty:
                            for _, row in df.iterrows():
                                try:
                                    # Create Weight record - make sure we're only using valid parameters
                                    timestamp = parse_datetime(row['timestamp'])
                                    
                                    record = Weight(
                                        user_id=self.user_id,
                                        import_log_id=self.import_log.id,
                                        value=float(row.get('value', 0)),
                                        unit=row.get('unit', 'kg'),
                                        timestamp=timestamp
                                        # weight_type, source_name, source_version, device are in CSV but not in model
                                    )
                                    records_to_commit.append(record)
                                    
                                    # Store sample data
                                    if len(sample_data) < 5:
                                        sample_data.append({
                                            'type': 'weight',
                                            'value': float(row.get('value', 0)),
                                            'unit': row.get('unit', 'kg'),
                                            'timestamp': timestamp.isoformat()
                                        })
                                    
                                    # Commit batch if size threshold reached
                                    if len(records_to_commit) >= self.batch_size:
                                        commit_batch_local()
                                except Exception as e:
                                    self.logger.error(f"Error processing weight record: {str(e)}")
                                    continue
                except pd.errors.EmptyDataError:
                    self.logger.info("Weight CSV is empty or has invalid format, skipping")
                except Exception as e:
                    self.logger.warning(f"Error processing weight data: {str(e)}, skipping this data type")

            # Import heart rate data
            heart_rate_csv = os.path.join(output_dir, 'heart_rate.csv')
            if os.path.exists(heart_rate_csv):
                self.logger.info(f"Processing heart rate data from {heart_rate_csv}")
                try:
                    # Check if file has data beyond headers
                    with open(heart_rate_csv, 'r') as f:
                        header = f.readline().strip()
                        has_data = bool(f.readline().strip())
                    
                    if not has_data:
                        self.logger.info("Heart rate CSV file has only headers, no data to import")
                    else:
                        df = pd.read_csv(heart_rate_csv)
                        if not df.empty:
                            for _, row in df.iterrows():
                                try:
                                    # Create HeartRate record - make sure we're only using valid parameters
                                    timestamp = parse_datetime(row['timestamp'])
                                    
                                    record = HeartRate(
                                        user_id=self.user_id,
                                        import_log_id=self.import_log.id,
                                        value=float(row.get('value', 0)),
                                        unit=row.get('unit', 'count/min'),
                                        timestamp=timestamp
                                        # heart_type, source_name, source_version, device are in CSV but not in model
                                    )
                                    records_to_commit.append(record)
                                    
                                    # Store sample data
                                    if len(sample_data) < 5:
                                        sample_data.append({
                                            'type': 'heart_rate',
                                            'value': float(row.get('value', 0)),
                                            'unit': row.get('unit', 'count/min'),
                                            'timestamp': timestamp.isoformat()
                                        })
                                    
                                    # Commit batch if size threshold reached
                                    if len(records_to_commit) >= self.batch_size:
                                        commit_batch_local()
                                except Exception as e:
                                    self.logger.error(f"Error processing heart rate record: {str(e)}")
                                    continue
                except pd.errors.EmptyDataError:
                    self.logger.info("Heart rate CSV is empty or has invalid format, skipping")
                except Exception as e:
                    self.logger.warning(f"Error processing heart rate data: {str(e)}, skipping this data type")

            # Import activity data
            activity_csv = os.path.join(output_dir, 'activity.csv')
            if os.path.exists(activity_csv):
                self.logger.info(f"Processing activity data from {activity_csv}")
                try:
                    # Check if file has data beyond headers
                    with open(activity_csv, 'r') as f:
                        header = f.readline().strip()
                        has_data = bool(f.readline().strip())
                    
                    if not has_data:
                        self.logger.info("Activity CSV file has only headers, no data to import")
                    else:
                        df = pd.read_csv(activity_csv)
                        if not df.empty:
                            for _, row in df.iterrows():
                                try:
                                    # Create Activity record - make sure we're only using valid parameters
                                    start_time = parse_datetime(row['start_time'])
                                    # Build activity info string with information that doesn't map to model fields
                                    activity_info = f"Start: {start_time.isoformat()}"
                                    if pd.notna(row.get('end_time')):
                                        activity_info += f", End: {row['end_time']}"
                                    if row.get('source_name'):
                                        activity_info += f", Source: {row['source_name']}"
                                    if row.get('device'):
                                        activity_info += f", Device: {row['device']}"
                                    if row.get('subtype') and pd.notna(row.get('subtype')):
                                        activity_info += f", Subtype: {row['subtype']}"
                                    
                                    record = Activity(
                                        user_id=self.user_id,
                                        import_log_id=self.import_log.id,
                                        activity_type=row.get('activity_type', 'unknown'),
                                        value=float(row.get('value', 0)),
                                        unit=row.get('unit', 'unknown'),
                                        timestamp=start_time,
                                        data_source=row.get('source_name', '')  # Store source in the data_source field
                                    )
                                    records_to_commit.append(record)
                                    
                                    # Store sample data
                                    if len(sample_data) < 5:
                                        sample_data.append({
                                            'type': 'activity',
                                            'activity_type': row.get('activity_type', 'unknown'),
                                            'value': float(row.get('value', 0)),
                                            'unit': row.get('unit', 'unknown'),
                                            'start_time': start_time.isoformat(),
                                            'end_time': row['end_time'] if pd.notna(row['end_time']) else None
                                        })
                                    
                                    # Commit batch if size threshold reached
                                    if len(records_to_commit) >= self.batch_size:
                                        commit_batch_local()
                                except Exception as e:
                                    self.logger.error(f"Error processing activity record: {str(e)}")
                                    continue
                except pd.errors.EmptyDataError:
                    self.logger.info("Activity CSV is empty or has invalid format, skipping")
                except Exception as e:
                    self.logger.warning(f"Error processing activity data: {str(e)}, skipping this data type")

            # Final commit for any remaining records
            commit_batch_local()
            
            # Update import log with record count
            if self.import_log:
                self.import_log.records_processed = total_processed  # 使用实际处理的记录总数
                self.import_log.sample_data = str(sample_data[:5]) if sample_data else "[]"
                db.session.commit()
                
            # Return success even if no data was imported
            return True
                
        except Exception as e:
            self.logger.error(f"Error importing CSV data: {str(e)}", exc_info=True)
            # Handle empty CSV files gracefully
            if "No columns to parse from file" in str(e):
                self.logger.warning(f"Empty CSV file detected. This is normal if no data of this type was found.")
                if self.import_log:
                    self.import_log.status = 'partial'
                    self.import_log.error_message = "Some data types had no records to import"
                    db.session.commit()
                return True
            raise DataImportError(f'Error importing CSV data: {str(e)}')

    def _process_zip(self, file):
        """Process ZIP file containing health data"""
        self.logger.info(f"Processing ZIP file: {file}")
        try:
            with zipfile.ZipFile(file) as zip_ref:
                for filename in zip_ref.namelist():
                    self.logger.info(f"Processing file from ZIP: {filename}")
                    if filename.endswith('.xml'):
                        with zip_ref.open(filename) as xml_file:
                            self._process_xml(xml_file)
                    elif filename.endswith('.csv'):
                        with zip_ref.open(filename) as csv_file:
                            self._process_csv(csv_file)
        except zipfile.BadZipFile as e:
            self.logger.error(f"Invalid ZIP file: {str(e)}")
            raise FileValidationError(f'Invalid ZIP file: {str(e)}')
        except Exception as e:
            self.logger.error(f"Error processing ZIP file: {str(e)}", exc_info=True)
            raise DataImportError(f'Error processing ZIP file: {str(e)}')

    def _process_xml(self, file):
        """Process XML file containing health data"""
        try:
            self.logger.info("Processing XML file")
            tree = ET.parse(file)
            root = tree.getroot()
            
            records_to_commit = []
            total_records = 0
            
            # Process sleep records
            sleep_records = {}  # Dictionary to group sleep records by start time
            for record in root.findall('.//Record[@type="HKCategoryTypeIdentifierSleepAnalysis"]'):
                try:
                    start_time = datetime.fromisoformat(record.get('startDate'))
                    end_time = datetime.fromisoformat(record.get('endDate', record.get('startDate')))
                    value = record.get('value')
                    source_name = record.get('sourceName', '')
                    duration = (end_time - start_time).total_seconds() / 60  # Convert to minutes
                    
                    # Group sleep records by start_time to combine different stages
                    date_key = start_time.date()
                    if date_key not in sleep_records:
                        sleep_records[date_key] = {
                            'start_time': start_time,
                            'end_time': end_time,
                            'total_duration': 0,
                            'deep_sleep': 0,
                            'light_sleep': 0,
                            'rem_sleep': 0,
                            'awake': 0,
                            'source_name': source_name  # 保存来源信息
                        }
                    elif 'Connect' in source_name:  # 如果是Connect设备，优先使用它的记录
                        sleep_records[date_key]['source_name'] = source_name
                    
                    # Update sleep stage durations based on the value
                    if 'Deep' in value or 'DeepSleep' in value:
                        sleep_records[date_key]['deep_sleep'] += duration
                    elif 'Light' in value or 'CoreSleep' in value:
                        sleep_records[date_key]['light_sleep'] += duration
                    elif 'REM' in value:
                        sleep_records[date_key]['rem_sleep'] += duration
                    elif 'Awake' in value:
                        sleep_records[date_key]['awake'] += duration
                    
                    # Update total duration and time range
                    sleep_records[date_key]['total_duration'] += duration
                    if end_time > sleep_records[date_key]['end_time']:
                        sleep_records[date_key]['end_time'] = end_time
                    if start_time < sleep_records[date_key]['start_time']:
                        sleep_records[date_key]['start_time'] = start_time
                    
                    total_records += 1
                    
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Skipping invalid sleep record: {str(e)}")
                    continue
            
            # Create Sleep records from the grouped data
            for sleep_data in sleep_records.values():
                record = Sleep(
                    user_id=self.user_id,
                    import_log_id=self.import_log.id,
                    duration=sleep_data['total_duration'],
                    deep_sleep=sleep_data['deep_sleep'],
                    light_sleep=sleep_data['light_sleep'],
                    rem_sleep=sleep_data['rem_sleep'],
                    awake=sleep_data['awake'],
                    unit='minutes',
                    start_time=sleep_data['start_time'],
                    end_time=sleep_data['end_time'],
                    timestamp=sleep_data['start_time'],
                    notes=f"Source: {sleep_data.get('source_name', '')}"  # 记录数据来源
                )
                records_to_commit.append(record)
                
                if len(records_to_commit) >= self.batch_size:
                    self._save_health_data_batch(records_to_commit)
                    records_to_commit = []
            
            # Process other health records
            daily_activities = {}  # Dictionary to group activity records by date

            # Process steps, distance and calories data
            activity_types = {
                'HKQuantityTypeIdentifierStepCount': {'type': 'steps', 'field': 'steps'},
                'HKQuantityTypeIdentifierDistanceWalkingRunning': {'type': 'distance', 'field': 'distance'},
                'HKQuantityTypeIdentifierActiveEnergyBurned': {'type': 'calories', 'field': 'calories'}
            }

            for record in root.findall('.//Record'):
                try:
                    record_type = record.get('type', '')
                    if record_type in activity_types:
                        value = float(record.get('value', 0))
                        unit = record.get('unit', '')
                        start_time = datetime.fromisoformat(record.get('startDate'))
                        date_key = start_time.date()
                        
                        # Initialize daily activity record if not exists
                        if date_key not in daily_activities:
                            daily_activities[date_key] = {
                                'timestamp': start_time,
                                'steps': 0,
                                'distance': 0,
                                'calories': 0,
                                'activity_records': []
                            }
                        
                        # Add to appropriate total based on activity type
                        field = activity_types[record_type]['field']
                        daily_activities[date_key][field] += value
                        
                        # Store the individual activity record
                        activity_type = activity_types[record_type]['type']
                        daily_activities[date_key]['activity_records'].append({
                            'activity_type': activity_type,
                            'value': value,
                            'unit': unit,
                            'timestamp': start_time
                        })
                        
                        total_records += 1
                        
                    elif 'weight' in record_type.lower():
                        value = float(record.get('value', 0))
                        unit = record.get('unit', '')
                        timestamp = datetime.fromisoformat(record.get('startDate'))
                        
                        weight_record = Weight(
                            user_id=self.user_id,
                            import_log_id=self.import_log.id,
                            value=value,
                            unit=unit,
                            timestamp=timestamp
                        )
                        records_to_commit.append(weight_record)
                        total_records += 1
                        
                    elif 'heart' in record_type.lower() or 'bpm' in record_type.lower():
                        value = float(record.get('value', 0))
                        unit = record.get('unit', '')
                        timestamp = datetime.fromisoformat(record.get('startDate'))
                        
                        heart_rate_record = HeartRate(
                            user_id=self.user_id,
                            import_log_id=self.import_log.id,
                            value=value,
                            unit=unit,
                            timestamp=timestamp
                        )
                        records_to_commit.append(heart_rate_record)
                        total_records += 1
                    
                    # Commit batch if size threshold reached
                    if len(records_to_commit) >= self.batch_size:
                        self._save_health_data_batch(records_to_commit)
                        records_to_commit = []
                
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Skipping invalid record: {str(e)}")
                    continue

            # Create Activity records from the grouped data
            for date_key, daily_data in daily_activities.items():
                try:
                    # Create the main daily activity record with totals
                    main_record = Activity(
                        user_id=self.user_id,
                        import_log_id=self.import_log.id,
                        activity_type='daily_summary',
                        value=daily_data['steps'] + daily_data['distance'] + daily_data['calories'],
                        unit='mixed',
                        timestamp=daily_data['timestamp'],
                        total_steps=daily_data['steps'] if daily_data['steps'] > 0 else None,
                        total_distance=daily_data['distance'] if daily_data['distance'] > 0 else None,
                        calories=daily_data['calories'] if daily_data['calories'] > 0 else None
                    )
                    records_to_commit.append(main_record)
                    
                    # Also store individual activity records
                    for activity_record in daily_data['activity_records']:
                        record = Activity(
                            user_id=self.user_id,
                            import_log_id=self.import_log.id,
                            activity_type=activity_record['activity_type'],
                            value=activity_record['value'],
                            unit=activity_record['unit'],
                            timestamp=activity_record['timestamp'],
                            data_source=activity_record.get('source_name', '')  # Store source in data_source field
                        )
                        records_to_commit.append(record)
                    
                    # Commit batch if size threshold reached
                    if len(records_to_commit) >= self.batch_size:
                        self._save_health_data_batch(records_to_commit)
                        records_to_commit = []
                except Exception as e:
                    self.logger.error(f"Error creating consolidated activity record: {str(e)}")
                    continue

            # Process remaining records
            if records_to_commit:
                self._save_health_data_batch(records_to_commit)

            self.logger.info(f"XML processing completed. Total records: {total_records}")

        except ET.ParseError as e:
            self.logger.error(f"Invalid XML format: {str(e)}")
            raise FileValidationError(f'Invalid XML format: {str(e)}')
        except Exception as e:
            self.logger.error(f"Error processing XML file: {str(e)}", exc_info=True)
            raise DataImportError(f'Error processing XML file: {str(e)}')

    # In class DataImportService
    def _save_health_data_batch(self, records):
        """Save a batch of health data records"""
        try:
            if not records:
                return

            batch_count = len(records) # Get the number of records in the batch

            db.session.add_all(records)
            db.session.commit()

            # Update import log count correctly
            if self.import_log:
                if self.import_log.records_processed is None:
                    self.import_log.records_processed = 0
                self.import_log.records_processed += batch_count # Increment by the number of records in the batch
                db.session.commit() # Commit the log update

            self.logger.info(f"Successfully saved batch of {batch_count} records.")

        except Exception as e:
            # Log the specific error and rollback
            self.logger.warning(f"Error saving batch: {str(e)}", exc_info=True) # Log full traceback for debugging
            db.session.rollback()
            # Optionally re-raise or handle differently if needed
            # raise DataImportError(f"Failed to save batch: {str(e)}")

        # Ensure records list is cleared by the caller function (commit_batch_local)
"""
Apple Health Data Parser

This module parses Apple Health export XML files into structured data.
It uses an incremental/streaming approach to handle large XML files efficiently
with batch processing to prevent worker timeouts.
"""
import xml.etree.ElementTree as ET
from datetime import datetime
import csv
import os
import zipfile
import tempfile
import shutil
import gc
import time
import signal
from app.utils.error_handlers import FileValidationError

# Constants for optimization
BATCH_SIZE = 20000  # Increased batch size for faster processing
CHECKPOINT_INTERVAL = 20  # More frequent checkpoints
GC_FREQUENCY = 5  # Collect garbage after every 5 batches to reduce overhead

class TimeoutHandler:
    """Handler for managing timeouts during long-running operations"""
    def __init__(self, timeout=280):  # Default 280s (slightly under 300s worker timeout)
        self.timeout = timeout
        self.start_time = time.time()
        self.checkpoint_time = self.start_time
        self.processed_items = {}
        
    def check_timeout(self, record_type=None, count=None):
        """Check if operation is close to timing out"""
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        # Update processed items count if provided
        if record_type and count is not None:
            self.processed_items[record_type] = count
        
        # Log checkpoint every CHECKPOINT_INTERVAL seconds
        if current_time - self.checkpoint_time > CHECKPOINT_INTERVAL:
            print(f"Processing... Elapsed time: {int(elapsed_time)}s")
            if self.processed_items:
                status = ", ".join([f"{k}: {v}" for k, v in self.processed_items.items()])
                print(f"Status: {status}")
            self.checkpoint_time = current_time
        
        # If we're approaching the timeout, raise exception to allow graceful handling
        if elapsed_time > self.timeout:
            raise TimeoutError(f"Operation exceeded maximum allowed time ({self.timeout}s)")

class AppleHealthParser:
    """
    Parser for Apple Health export data (export.xml)
    Uses incremental parsing and batch processing to handle large files efficiently
    """
    
    def __init__(self, file_path):
        """
        Initialize parser with file path
        
        Args:
            file_path (str): Path to Apple Health export file (ZIP or XML)
        """
        self.file_path = file_path
        self.xml_path = None
        self.timeout_handler = TimeoutHandler()
        self._prepare_file()
    
    def _prepare_file(self):
        """Prepare the file for parsing (extract if ZIP)"""
        try:
            if self.file_path.endswith('.zip'):
                # Create a temporary directory for extracted files
                temp_dir = os.path.join(os.path.dirname(self.file_path), 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                
                # Extract the ZIP file
                try:
                    with zipfile.ZipFile(self.file_path) as zip_ref:
                        # Only extract apple_health_export/export.xml to save space and time
                        xml_paths = [info for info in zip_ref.infolist() 
                                    if info.filename.endswith('.xml') and 
                                       ('export.xml' in info.filename or 'apple_health_export' in info.filename)]
                        
                        # Extract only the smallest XML file to save time
                        if xml_paths:
                            xml_paths.sort(key=lambda x: x.file_size)
                            target_xml = xml_paths[0]
                            extracted_path = os.path.join(temp_dir, os.path.basename(target_xml.filename))
                            with zip_ref.open(target_xml) as source, open(extracted_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
                            self.xml_path = extracted_path
                        else:
                            # Fall back to extracting all XML files if targeted approach fails
                            for item in zip_ref.infolist():
                                if item.filename.endswith('.xml'):
                                    zip_ref.extract(item, temp_dir)
                        
                        # Look for XML files in the extracted directory
                        xml_files = []
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                if file.endswith('.xml'):
                                    xml_files.append(os.path.join(root, file))
                        
                        if not xml_files:
                            raise FileValidationError('No XML files found in the ZIP archive')
                        
                        # Use the first XML file found
                            self.xml_path = xml_files[0]
                        
                except zipfile.BadZipFile:
                    raise FileValidationError('Invalid ZIP file format')
            else:
                # Use the XML file directly
                self.xml_path = self.file_path
                
            # Validate that the XML file exists and is readable
            if not os.path.exists(self.xml_path):
                raise FileValidationError(f'XML file not found: {self.xml_path}')
                
            # Try to open and validate the XML file
            try:
                with open(self.xml_path, 'r', encoding='utf-8') as test_file:
                    first_line = test_file.readline()
                    if '<?xml' not in first_line and '<HealthData' not in first_line:
                        raise FileValidationError('The file does not appear to be a valid Apple Health export XML file')
            except UnicodeDecodeError:
                # Try again with a different encoding
                try:
                    with open(self.xml_path, 'r', encoding='latin-1') as test_file:
                        first_line = test_file.readline()
                        if '<?xml' not in first_line and '<HealthData' not in first_line:
                            raise FileValidationError('The file does not appear to be a valid Apple Health export XML file')
                except Exception as e:
                    raise FileValidationError(f'Error reading XML file: {str(e)}')
            
        except Exception as e:
            if not isinstance(e, FileValidationError):
                raise FileValidationError(f'Error processing file: {str(e)}')
            raise
    
    def _safe_iterparse(self, tag_type=None, attribute_type=None):
        """
        Safer iterparse implementation that doesn't rely on getchildren()
        
        Args:
            tag_type (str): Tag name to filter elements (e.g., 'Record', 'Workout')
            attribute_type (str): Attribute type to filter (e.g., 'HKQuantityTypeIdentifierStepCount')
            
        Yields:
            dict: Parsed element attributes
        """
        try:
            # We'll use a simpler approach to parse the XML
            with open(self.xml_path, 'rb') as xml_file:
                for event, elem in ET.iterparse(xml_file, events=('end',)):
                    # Apply filters if specified
                    if (tag_type is None or elem.tag == tag_type) and \
                       (attribute_type is None or elem.get('type') == attribute_type):
                        # Extract attributes
                        attributes = {k: v for k, v in elem.attrib.items()}
                        yield attributes
                    
                    # Clear element to free memory
                    elem.clear()
        except Exception as e:
            raise FileValidationError(f'Error in safe XML parsing: {str(e)}')
    
    def _iterparse_records_batched(self, record_type, batch_size=BATCH_SIZE):
        """
        Incrementally parse records of specified type from XML in batches
        
        Args:
            record_type (str): Type of records to parse
            batch_size: Number of records to process in one batch
            
        Yields:
            list: Batch of parsed record data
        """
        try:
            batch = []
            record_count = 0
            batch_count = 0
            
            try:
                # Try the standard approach first
                # Use iterparse to process the XML file in chunks
                context = ET.iterparse(self.xml_path, events=('end',))
                
                # Process elements as they are parsed
                for event, elem in context:
                    # Check for timeout periodically
                    if record_count % 1000 == 0:
                        self.timeout_handler.check_timeout(record_type, record_count)
                    
                    if elem.tag == 'Record' and elem.get('type') == record_type:
                        # Extract the record data
                        record_data = {k: elem.get(k) for k in elem.attrib}
                        batch.append(record_data)
                        record_count += 1
                        
                        # When batch is full, yield it and start a new one
                        if len(batch) >= batch_size:
                            yield batch
                            batch = []
                            batch_count += 1
                            # Force garbage collection periodically to prevent memory buildup
                            if batch_count % GC_FREQUENCY == 0:
                                gc.collect()
                    
                    # Clear element to free memory
                    elem.clear()
                    
                    # Remove reference to element - safely check if root exists and has children
                    if event == 'end' and context.root is not None:
                        try:
                            while context.root.getchildren():
                                context.root.remove(context.root.getchildren()[0])
                        except (AttributeError, TypeError):
                            # Handle potential AttributeError if getchildren is not available
                            # or TypeError if root becomes None
                            pass
                
                # Clear the root element if it exists
                if hasattr(context, 'root') and context.root is not None:
                    context.root.clear()
            
            except (AttributeError, TypeError) as e:
                # If we got an attribute error, use the safer implementation
                print(f"Warning: Standard XML parsing failed, using fallback method: {str(e)}")
                if batch:
                    yield batch
                    batch = []
                    batch_count += 1
                
                # Fallback to the safer implementation
                for attributes in self._safe_iterparse('Record', record_type):
                    # Check for timeout periodically
                    if record_count % 1000 == 0:
                        self.timeout_handler.check_timeout(record_type, record_count)
                    
                    batch.append(attributes)
                    record_count += 1
                    
                    # When batch is full, yield it and start a new one
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                        batch_count += 1
                        # Force garbage collection periodically
                        if batch_count % GC_FREQUENCY == 0:
                            gc.collect()
            
            # Yield any remaining records
            if batch:
                yield batch
                
        except ET.ParseError as e:
            raise FileValidationError(f'Invalid XML format: {str(e)}')
        except TimeoutError as e:
            # If we hit a timeout, return what we've processed so far
            if batch:
                yield batch
            print(f"Warning: Timeout during parsing {record_type}. {record_count} records processed.")
        except Exception as e:
            raise FileValidationError(f'Error parsing file: {str(e)}')
    
    def _iterparse_workouts_batched(self, batch_size=BATCH_SIZE):
        """
        Incrementally parse workout records from XML in batches
        
        Args:
            batch_size: Number of records to process in one batch
            
        Yields:
            list: Batch of parsed workout data
        """
        try:
            batch = []
            record_count = 0
            batch_count = 0
            
            try:
                # Try the standard approach first
                # Use iterparse to process the XML file in chunks
                context = ET.iterparse(self.xml_path, events=('end',))
                
                # Process elements as they are parsed
                for event, elem in context:
                    # Check for timeout periodically
                    if record_count % 1000 == 0:
                        self.timeout_handler.check_timeout(None, record_count)
                    
                    if elem.tag == 'Workout':
                        # Extract the workout data
                        workout_data = {k: elem.get(k) for k in elem.attrib}
                        batch.append(workout_data)
                        record_count += 1
                        
                        # When batch is full, yield it and start a new one
                        if len(batch) >= batch_size:
                            yield batch
                            batch = []
                            batch_count += 1
                            # Force garbage collection periodically
                            if batch_count % GC_FREQUENCY == 0:
                                gc.collect()
                    
                    # Clear element to free memory
                    elem.clear()
                    
                    # Remove reference to element - safely check if root exists and has children
                    if event == 'end' and context.root is not None:
                        try:
                            while context.root.getchildren():
                                context.root.remove(context.root.getchildren()[0])
                        except (AttributeError, TypeError):
                            # Handle potential AttributeError if getchildren is not available
                            # or TypeError if root becomes None
                            pass
                
                # Clear the root element if it exists
                if hasattr(context, 'root') and context.root is not None:
                    context.root.clear()
                    
            except (AttributeError, TypeError) as e:
                # If we got an attribute error, use the safer implementation
                print(f"Warning: Standard XML parsing failed, using fallback method: {str(e)}")
                if batch:
                    yield batch
                    batch = []
                    batch_count += 1
                
                # Fallback to the safer implementation
                for attributes in self._safe_iterparse('Workout'):
                    # Check for timeout periodically
                    if record_count % 1000 == 0:
                        self.timeout_handler.check_timeout(None, record_count)
                    
                    batch.append(attributes)
                    record_count += 1
                    
                    # When batch is full, yield it and start a new one
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                        batch_count += 1
                        # Force garbage collection periodically
                        if batch_count % GC_FREQUENCY == 0:
                            gc.collect()
            
            # Yield any remaining records
            if batch:
                yield batch
                
        except ET.ParseError as e:
            raise FileValidationError(f'Invalid XML format: {str(e)}')
        except TimeoutError as e:
            # If we hit a timeout, return what we've processed so far
            if batch:
                yield batch
            print(f"Warning: Timeout during parsing workouts. {record_count} records processed.")
        except Exception as e:
            raise FileValidationError(f'Error parsing file: {str(e)}')
    
    def _stream_generate_csv_batched(self, batch_generator, output_path, transform_func):
        """
        Stream-generate a CSV file from batched parsed data to minimize memory usage
        
        Args:
            batch_generator: Generator that yields batches of records
            output_path: Path to output CSV file
            transform_func: Function to transform record to CSV row
        """
        if isinstance(batch_generator, list):
            # If we passed a list of batches (after checking first batch)
            batches = batch_generator
        else:
            # Original generator
            batches = batch_generator
            
        with open(output_path, 'w', newline='') as csvfile:
            writer = None
            records_processed = 0
            batch_count = 0
            
            try:
                # Process each batch
                for batch in batches:
                    if not batch:  # Skip empty batches
                        continue
                        
                    # Process each record in the batch
                    for item in batch:
                        try:
                            row = transform_func(item)
                            
                            # Initialize writer with the first row's keys
                            if writer is None:
                                writer = csv.DictWriter(csvfile, fieldnames=row.keys())
                                writer.writeheader()
                            
                            writer.writerow(row)
                            records_processed += 1
                            
                            # Periodically flush to disk (every 5000 records)
                            if records_processed % 5000 == 0:
                                csvfile.flush()
                        except Exception as e:
                            print(f"Error processing record: {str(e)}, skipping")
                            continue
                    
                    # Force garbage collection periodically
                    batch_count += 1
                    if batch_count % GC_FREQUENCY == 0:
                        gc.collect()
                
                # If no records were processed, ensure the file has headers
                if records_processed == 0 and writer is None:
                    # Create a sample row to get field names
                    sample_item = {'type': 'sample'}  # Minimal sample
                    try:
                        row = transform_func(sample_item)
                        writer = csv.DictWriter(csvfile, fieldnames=row.keys())
                        writer.writeheader()
                    except Exception:
                        # If transform fails on sample, create generic headers
                        print("Could not determine headers from transform function, using generic headers")
                        writer = csv.DictWriter(csvfile, fieldnames=['record_type', 'value', 'timestamp'])
                        writer.writeheader()
                
                return records_processed
            except Exception as e:
                print(f"Error in CSV generation: {str(e)}")
                
                # Ensure file has at least headers 
                if records_processed == 0 and writer is None:
                    # Try to write generic headers
                    try:
                        writer = csv.DictWriter(csvfile, fieldnames=['record_type', 'value', 'timestamp'])
                        writer.writeheader()
                    except Exception:
                        pass
                
                return records_processed
    
    def generate_activity_csv(self, output_dir):
        """Generate activity.csv file incrementally using batched processing"""
        steps_path = os.path.join(output_dir, 'activity_steps.csv')
        distance_path = os.path.join(output_dir, 'activity_distance.csv')
        calories_path = os.path.join(output_dir, 'activity_calories.csv')
        workout_path = os.path.join(output_dir, 'activity_workout.csv')
        csv_file_path = os.path.join(output_dir, 'activity.csv')
        
        total_records = 0
        print("Processing step count data...")
        
        # Generate individual CSVs
        steps_count = self._stream_generate_csv_batched(
            self._iterparse_records_batched('HKQuantityTypeIdentifierStepCount'),
            steps_path,
            lambda r: {
                'user_id': 'user_id',
                'activity_type': 'steps',
                'subtype': None,
                'start_time': r.get('startDate'),
                'end_time': r.get('endDate'),
                'value': float(r.get('value', 0)),
                'unit': r.get('unit', 'count'),
                'source_name': r.get('sourceName', ''),
                'source_version': None,
                'device': r.get('device', ''),
                'import_batch_id': 'import_batch_id'
            }
        )
        total_records += steps_count
        print(f"Processed {steps_count} step count records")
        
        print("Processing distance data...")
        distance_count = self._stream_generate_csv_batched(
            self._iterparse_records_batched('HKQuantityTypeIdentifierDistanceWalkingRunning'),
            distance_path,
            lambda r: {
                'user_id': 'user_id',
                'activity_type': 'distance',
                'subtype': None,
                'start_time': r.get('startDate'),
                'end_time': r.get('endDate'),
                'value': float(r.get('value', 0)),
                'unit': r.get('unit', 'km'),
                'source_name': r.get('sourceName', ''),
                'source_version': None,
                'device': r.get('device', ''),
                'import_batch_id': 'import_batch_id'
            }
        )
        total_records += distance_count
        print(f"Processed {distance_count} distance records")
        
        print("Processing calories data...")
        calories_count = self._stream_generate_csv_batched(
            self._iterparse_records_batched('HKQuantityTypeIdentifierActiveEnergyBurned'),
            calories_path,
            lambda r: {
                'user_id': 'user_id',
                'activity_type': 'calories',
                'subtype': None,
                'start_time': r.get('startDate'),
                'end_time': r.get('endDate'),
                'value': float(r.get('value', 0)),
                'unit': r.get('unit', 'kcal'),
                'source_name': r.get('sourceName', ''),
                'source_version': None,
                'device': r.get('device', ''),
                'import_batch_id': 'import_batch_id'
            }
        )
        total_records += calories_count
        print(f"Processed {calories_count} calories records")
        
        print("Processing workout data...")
        workout_count = self._stream_generate_csv_batched(
            self._iterparse_workouts_batched(),
            workout_path,
            lambda w: {
                'user_id': 'user_id',
                'activity_type': 'workout',
                'subtype': w.get('workoutActivityType', ''),
                'start_time': w.get('startDate'),
                'end_time': w.get('endDate'),
                'value': float(w.get('totalDistance', 0)) if w.get('totalDistance') else (float(w.get('totalEnergyBurned', 0)) if w.get('totalEnergyBurned') else 0),
                'unit': 'km' if w.get('totalDistance') else 'kcal',
                'source_name': w.get('sourceName', ''),
                'source_version': None,
                'device': w.get('device', ''),
                'import_batch_id': 'import_batch_id'
            }
        )
        total_records += workout_count
        print(f"Processed {workout_count} workout records")
        
        # Combine CSVs in batches to avoid memory issues
        print("Combining activity data...")
        batch_size = 5000
        total_combined = 0
        
        with open(csv_file_path, 'w', newline='') as outfile:
            fieldnames = ['user_id', 'activity_type', 'subtype', 'start_time', 'end_time', 'value', 'unit', 'source_name', 'source_version', 'device', 'import_batch_id']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for file_path in [steps_path, distance_path, calories_path, workout_path]:
                if os.path.exists(file_path):
                    with open(file_path, 'r', newline='') as infile:
                        reader = csv.DictReader(infile)
                        batch = []
                        
                        for row in reader:
                            batch.append(row)
                            
                            if len(batch) >= batch_size:
                                for record in batch:
                                    writer.writerow(record)
                                total_combined += len(batch)
                                batch = []
                                outfile.flush()
                                
                                # Check for timeout
                                self.timeout_handler.check_timeout(None, total_records)
                        
                        # Write any remaining records
                        for record in batch:
                            writer.writerow(record)
                        total_combined += len(batch)
                        outfile.flush()
                    
                    # Delete the temp file after combining
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Warning: Could not remove temporary file {file_path}: {str(e)}")
        
        print(f"Combined {total_combined} activity records")
        return csv_file_path

    def generate_heart_rate_csv(self, output_dir):
        """Generate heart_rate.csv file incrementally using batched processing"""
        csv_file_path = os.path.join(output_dir, 'heart_rate.csv')
        
        print("Processing heart rate data...")
        try:
            # Get a generator for heart rate records
            heart_rate_records_generator = self._iterparse_records_batched('HKQuantityTypeIdentifierHeartRate')
            
            # Check if there are any heart rate records by trying to get the first batch
            first_batch = next(heart_rate_records_generator, None)
            
            if first_batch is None or len(first_batch) == 0:
                # No heart rate records found, create a minimal valid CSV with headers only
                print("No heart rate records found in data. Creating empty CSV with headers.")
                with open(csv_file_path, 'w', newline='') as csvfile:
                    fieldnames = ['user_id', 'heart_type', 'timestamp', 'value', 'unit', 'source_name', 'source_version', 'device', 'import_batch_id']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                return csv_file_path
            
            # Process the first batch and any remaining batches
            count = self._stream_generate_csv_batched(
                # Chain the first batch with the remaining batches
                ([first_batch] if first_batch else []) + list(heart_rate_records_generator),
                csv_file_path,
                lambda r: {
                    'user_id': 'user_id',
                    'heart_type': 'active',
                    'timestamp': r.get('startDate'),
                    'value': float(r.get('value', 0)),
                    'unit': r.get('unit', 'count/min'),
                    'source_name': r.get('sourceName', ''),
                    'source_version': None,
                    'device': r.get('device', ''),
                    'import_batch_id': 'import_batch_id'
                }
            )
            
            print(f"Processed {count} heart rate records")
            return csv_file_path
        except Exception as e:
            # If error occurs, still create a valid empty CSV
            print(f"Error processing heart rate data: {str(e)}. Creating empty CSV with headers.")
            with open(csv_file_path, 'w', newline='') as csvfile:
                fieldnames = ['user_id', 'heart_type', 'timestamp', 'value', 'unit', 'source_name', 'source_version', 'device', 'import_batch_id']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            return csv_file_path

    def generate_sleep_csv(self, output_dir):
        """Generate sleep.csv file incrementally using batched processing"""
        csv_file_path = os.path.join(output_dir, 'sleep.csv')
        
        print("Processing sleep data...")
        try:
            # Get a generator for sleep records
            sleep_records_generator = self._iterparse_records_batched('HKCategoryTypeIdentifierSleepAnalysis')
            
            # Check if there are any sleep records by trying to get the first batch
            first_batch = next(sleep_records_generator, None)
            
            if first_batch is None or len(first_batch) == 0:
                # No sleep records found, create a minimal valid CSV with headers only
                print("No sleep records found in data. Creating empty CSV with headers.")
                with open(csv_file_path, 'w', newline='') as csvfile:
                    fieldnames = ['user_id', 'stage', 'start_time', 'end_time', 'source_name', 
                                 'source_version', 'device', 'import_batch_id']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                return csv_file_path
            
            # Process the first batch and any remaining batches
            count = self._stream_generate_csv_batched(
                # Chain the first batch with the remaining batches
                ([first_batch] if first_batch else []) + list(sleep_records_generator),
                csv_file_path,
                lambda r: {
                    'user_id': 'user_id',
                    'stage': r.get('value', ''),
                    'start_time': r.get('startDate'),
                    'end_time': r.get('endDate'),
                    'source_name': r.get('sourceName', ''),
                    'source_version': None,
                    'device': r.get('device', ''),
                    'import_batch_id': 'import_batch_id'
                }
            )
            
            print(f"Processed {count} sleep records")
            return csv_file_path
        except Exception as e:
            # If error occurs, still create a valid empty CSV
            print(f"Error processing sleep data: {str(e)}. Creating empty CSV with headers.")
            with open(csv_file_path, 'w', newline='') as csvfile:
                fieldnames = ['user_id', 'stage', 'start_time', 'end_time', 'source_name', 
                             'source_version', 'device', 'import_batch_id']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            return csv_file_path

    def generate_weight_csv(self, output_dir):
        """Generate weight.csv file incrementally using batched processing"""
        csv_file_path = os.path.join(output_dir, 'weight.csv')
        
        print("Processing weight data...")
        try:
            # Get a generator for weight records
            weight_records_generator = self._iterparse_records_batched('HKQuantityTypeIdentifierBodyMass')
            
            # Check if there are any weight records by trying to get the first batch
            first_batch = next(weight_records_generator, None)
            
            if first_batch is None or len(first_batch) == 0:
                # No weight records found, create a minimal valid CSV with headers only
                print("No weight records found in data. Creating empty CSV with headers.")
                with open(csv_file_path, 'w', newline='') as csvfile:
                    fieldnames = ['user_id', 'weight_type', 'timestamp', 'value', 'unit', 'source_name', 'source_version', 'device', 'import_batch_id']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                return csv_file_path
            
            # Process the first batch and any remaining batches
            count = self._stream_generate_csv_batched(
                # Chain the first batch with the remaining batches
                ([first_batch] if first_batch else []) + list(weight_records_generator),
                csv_file_path,
                lambda r: {
                    'user_id': 'user_id',
                    'weight_type': 'body_mass',
                    'timestamp': r.get('startDate'),
                    'value': float(r.get('value', 0)),
                    'unit': r.get('unit', 'kg'),
                    'source_name': r.get('sourceName', ''),
                    'source_version': None,
                    'device': r.get('device', ''),
                    'import_batch_id': 'import_batch_id'
                }
            )
            
            print(f"Processed {count} weight records")
            return csv_file_path
        except Exception as e:
            # If error occurs, still create a valid empty CSV
            print(f"Error processing weight data: {str(e)}. Creating empty CSV with headers.")
            with open(csv_file_path, 'w', newline='') as csvfile:
                fieldnames = ['user_id', 'weight_type', 'timestamp', 'value', 'unit', 'source_name', 'source_version', 'device', 'import_batch_id']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            return csv_file_path

    def parse_all(self, output_dir):
        """Parse all available health data and generate CSV files incrementally with batched processing"""
        try:
            start_time = time.time()
            print(f"Starting Apple Health data parsing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Track files successfully generated
            generated_files = []
            
            # Process activity data first (most important)
            try:
                activity_file = self.generate_activity_csv(output_dir)
                generated_files.append('activity.csv')
                print(f"Activity data processed in {int(time.time() - start_time)} seconds")
            except TimeoutError as e:
                print(f"Warning: Timeout during activity data processing: {str(e)}")
                if os.path.exists(os.path.join(output_dir, 'activity.csv')):
                    generated_files.append('activity.csv')
            
            # Try to process other data types if time permits
            remaining_time = 280 - (time.time() - start_time)
            if remaining_time > 30:  # Only try if we have at least 30 seconds left
                try:
                    # Set a shorter timeout for the remaining operations
                    self.timeout_handler.timeout = min(remaining_time - 10, 60)
                    heart_rate_file = self.generate_heart_rate_csv(output_dir)
                    generated_files.append('heart_rate.csv')
                    print(f"Heart rate data processed in {int(time.time() - start_time)} seconds")
                except TimeoutError as e:
                    print(f"Warning: Timeout during heart rate data processing: {str(e)}")
                    if os.path.exists(os.path.join(output_dir, 'heart_rate.csv')):
                        generated_files.append('heart_rate.csv')
            
            remaining_time = 280 - (time.time() - start_time)
            if remaining_time > 30:
                try:
                    self.timeout_handler.timeout = min(remaining_time - 10, 60)
                    sleep_file = self.generate_sleep_csv(output_dir)
                    generated_files.append('sleep.csv')
                    print(f"Sleep data processed in {int(time.time() - start_time)} seconds")
                except TimeoutError as e:
                    print(f"Warning: Timeout during sleep data processing: {str(e)}")
                    if os.path.exists(os.path.join(output_dir, 'sleep.csv')):
                        generated_files.append('sleep.csv')
            
            remaining_time = 280 - (time.time() - start_time)
            if remaining_time > 30:
                try:
                    self.timeout_handler.timeout = min(remaining_time - 10, 60)
                    weight_file = self.generate_weight_csv(output_dir)
                    generated_files.append('weight.csv')
                    print(f"Weight data processed in {int(time.time() - start_time)} seconds")
                except TimeoutError as e:
                    print(f"Warning: Timeout during weight data processing: {str(e)}")
                    if os.path.exists(os.path.join(output_dir, 'weight.csv')):
                        generated_files.append('weight.csv')
            
            # Return a reference to the output directory
            end_time = time.time()
            print(f"Apple Health data parsing completed in {int(end_time - start_time)} seconds")
            
            # If we have at least one file, consider it a success
            partial = len(generated_files) < 4
            
            return {
                'output_dir': output_dir,
                'files_generated': generated_files,
                'processing_time': int(end_time - start_time),
                'partial_results': partial,
                'error': "Some data types could not be processed in time" if partial else None
            }
        except TimeoutError as e:
            # If we hit a timeout, return what we've processed so far
            print(f"Warning: {str(e)}. Returning partial results.")
            generated_files = [f for f in ['activity.csv', 'heart_rate.csv', 'sleep.csv', 'weight.csv'] 
                              if os.path.exists(os.path.join(output_dir, f))]
            
            return {
                'output_dir': output_dir,
                'files_generated': generated_files,
                'partial_results': True,
                'error': str(e)
            }
        finally:
            # Clean up temp files to ensure we free memory
            try:
                temp_dir = os.path.join(os.path.dirname(self.file_path), 'temp')
                if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not remove temporary directory: {str(e)}")
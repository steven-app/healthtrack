from werkzeug.utils import secure_filename
import os
from datetime import datetime
import logging
from app import db
from app.models import ImportLog
from app.services.parsers.apple_health_parser import AppleHealthParser
from app.services.parsers.google_fit_parser import GoogleFitParser
from app.services.parsers.fitbit_parser import FitbitParser
from app.services.parsers.samsung_health_parser import SamsungHealthParser
from app.services.parsers.custom_parser import CustomParser
from app.services.data_import import DataImportService
from app.utils.error_handlers import FileValidationError, DataImportError
from flask import current_app

logger = logging.getLogger(__name__)

class UploadService:
    def __init__(self, user_id):
        self.user_id = user_id
        self.import_log = None
        self.logger = logging.getLogger(__name__)

    def process_file(self, file, data_source):
        """Process uploaded file and import data"""
        try:
            self.logger.info(f"Starting file processing for user {self.user_id}")
            self.logger.info(f"File: {file.filename}, Data source: {data_source}")
            
            # Ensure upload directory exists
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            self.logger.info(f"Upload directory: {current_app.config['UPLOAD_FOLDER']}")
            
            # Create import log
            self.import_log = ImportLog(
                user_id=self.user_id,
                data_source=data_source,
                file_name=file.filename,
                status='processing'
            )
            db.session.add(self.import_log)
            db.session.commit()
            self.logger.info(f"Created import log with ID: {self.import_log.id}")

            # Save file to upload directory
            try:
                file_path = self.upload_file(file)
                self.logger.info(f"File saved to: {file_path}")
            except Exception as e:
                self.logger.error(f"Error saving file: {str(e)}")
                raise FileValidationError(f"Error saving file: {str(e)}")
            
            # Get appropriate parser based on data source
            try:
                parser = self.get_parser(data_source, file_path)
                self.logger.info(f"Using parser {parser.__class__.__name__} for data source {data_source}")
            except Exception as e:
                self.logger.error(f"Error creating parser: {str(e)}")
                raise DataImportError(f"Error creating parser: {str(e)}")
            
            # Parse data using the selected parser
            try:
                output_dir = os.path.dirname(file_path)
                self.logger.info(f"Parsing data to directory: {output_dir}")
                parse_result = parser.parse_all(output_dir)
                self.logger.info("Data parsing completed")
                
                # Handle different parser return structures
                if isinstance(parse_result, dict):
                    parsed_output_dir = parse_result.get('output_dir', output_dir)
                    
                    # Check if we have partial results
                    if parse_result.get('partial_results', False):
                        self.logger.warning(f"Parser returned partial results: {parse_result.get('error', 'Unknown reason')}")
                        self.import_log.status = 'partial'
                        self.import_log.error_message = f"Partial import: {parse_result.get('error', 'Processing timed out')}"
                        db.session.commit()
                else:
                    # Original format from other parsers
                    parsed_output_dir = output_dir
            except Exception as e:
                self.logger.error(f"Error parsing data: {str(e)}")
                raise DataImportError(f"Error parsing data: {str(e)}")
            
            # Import data using DataImportService
            try:
                import_service = DataImportService(self.user_id, self.import_log)
                import_result = import_service.process_file(file, data_source, parsed_output_dir)
                self.logger.info("Data import completed")
                
                if import_result:
                    # Consider it a success even if partially successful
                    if self.import_log.status != 'partial':
                        self.import_log.status = 'success'
                else:
                    self.import_log.status = 'failed'
                    self.import_log.error_message = "Failed to import data, no records processed"
                
                self.import_log.completed_at = datetime.utcnow()
                db.session.commit()
            except DataImportError as e:
                self.logger.error(f"Error importing data: {str(e)}")
                # Check if the error is just about empty files
                if "No columns to parse from file" in str(e) or "Empty CSV file" in str(e):
                    self.import_log.status = 'partial'
                    self.import_log.error_message = "Some data types had no records to import"
                    self.import_log.completed_at = datetime.utcnow()
                    db.session.commit()
                    self.logger.warning("Completed with partial results - some data types had no records")
                else:
                    raise DataImportError(f"Error importing data: {str(e)}")
            except Exception as e:
                self.logger.error(f"Error importing data: {str(e)}")
                raise DataImportError(f"Error importing data: {str(e)}")

            # Log summary
            if isinstance(parse_result, dict) and 'processing_time' in parse_result:
                self.logger.info(f"File processing completed in {parse_result['processing_time']} seconds")
                if 'files_generated' in parse_result:
                    self.logger.info(f"Generated files: {', '.join(parse_result['files_generated'])}")
            else:
                self.logger.info("File processing completed successfully")

            # Clean up temporary files directory
            try:
                temp_dir = os.path.join(output_dir, 'temp')
                if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
                    self.logger.info(f"Removed temporary directory: {temp_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to remove temporary directory: {str(e)}")

            return self.import_log

        except Exception as e:
            self.logger.error(f"Error processing file: {str(e)}", exc_info=True)
            if self.import_log:
                self.import_log.status = 'failed'
                self.import_log.error_message = str(e)
                self.import_log.completed_at = datetime.utcnow()
                db.session.commit()
            
            # Try to clean up temporary files even in error cases
            try:
                output_dir = os.path.dirname(file_path) if 'file_path' in locals() else None
                if output_dir:
                    temp_dir = os.path.join(output_dir, 'temp')
                    if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
                        import shutil
                        shutil.rmtree(temp_dir)
                        self.logger.info(f"Removed temporary directory after error: {temp_dir}")
            except Exception as cleanup_error:
                self.logger.warning(f"Failed to remove temporary directory after error: {str(cleanup_error)}")
                
            raise DataImportError(f'Error processing file: {str(e)}')

    @staticmethod
    def upload_file(file):
        """Save uploaded file to upload directory"""
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save the file
            file.save(file_path)
            logger.info(f"File saved successfully to {file_path}")
            
            return file_path
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}", exc_info=True)
            raise FileValidationError(f"Error saving file: {str(e)}")

    @staticmethod
    def get_parser(data_source, file_path):
        """Get appropriate parser based on data source"""
        try:
            # Define parser mappings for different data sources
            parser_mappings = {
                'apple_health': AppleHealthParser,
                'google_fit': GoogleFitParser,
                'fitbit': FitbitParser,
                'samsung_health': SamsungHealthParser,
                'custom': CustomParser
            }
            
            # Get parser class for the data source
            parser_class = parser_mappings.get(data_source)
            if not parser_class:
                logger.error(f"Unsupported data source: {data_source}")
                raise ValueError(f'Unsupported data source: {data_source}')
            
            logger.info(f"Using parser {parser_class.__name__} for data source {data_source}")
            return parser_class(file_path)
        except Exception as e:
            logger.error(f"Error creating parser: {str(e)}", exc_info=True)
            raise DataImportError(f"Error creating parser: {str(e)}") 
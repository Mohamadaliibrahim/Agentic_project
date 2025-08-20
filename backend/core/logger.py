"""
Centralized Logging Configuration
Handles all application logging to file instead of terminal
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

class WatchfilesFilter(logging.Filter):
    """Filter to exclude watchfiles debug messages that create circular logging"""
    
    def filter(self, record):
        # Exclude watchfiles debug messages
        if record.name == "watchfiles.main" and record.levelno == logging.DEBUG:
            return False
        
        # Exclude httpcore debug messages (too verbose)
        if record.name.startswith("httpcore") and record.levelno == logging.DEBUG:
            return False
            
        return True

class Logger:
    """Centralized logger for the application"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Create log filename with current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"fastapi_backend_{current_date}.txt"
        self.error_log_file = self.log_dir / f"fastapi_errors_{current_date}.txt"
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        
        # Remove all existing handlers to avoid duplicates
        logging.getLogger().handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler for all logs
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        # Add filter to exclude watchfiles debug messages
        file_handler.addFilter(WatchfilesFilter())
        
        # Force immediate flushing for live logging
        class FlushingHandler(logging.handlers.RotatingFileHandler):
            def emit(self, record):
                super().emit(record)
                self.flush()  # Force flush after each log entry
        
        # Replace file handler with flushing version for live logging
        live_file_handler = FlushingHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        live_file_handler.setLevel(logging.DEBUG)
        live_file_handler.setFormatter(detailed_formatter)
        live_file_handler.addFilter(WatchfilesFilter())
        
        # Separate file handler for errors only
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        # No need for watchfiles filter on error handler since it's ERROR level only
        
        # Also make error handler flush immediately
        class FlushingErrorHandler(logging.handlers.RotatingFileHandler):
            def emit(self, record):
                super().emit(record)
                self.flush()  # Force flush after each error log entry
        
        live_error_handler = FlushingErrorHandler(
            self.error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        live_error_handler.setLevel(logging.ERROR)
        live_error_handler.setFormatter(detailed_formatter)
        
        # Console handler for minimal output (only critical errors)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.CRITICAL)
        console_handler.setFormatter(simple_formatter)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(live_file_handler)  # Use live flushing handler
        root_logger.addHandler(live_error_handler)  # Use live flushing error handler
        root_logger.addHandler(console_handler)
        
        # Configure specific loggers
        self._configure_fastapi_logging()
        self._configure_uvicorn_logging()
        self._configure_database_logging()
        self._configure_application_logging()
        
        # Log the start of logging session
        logging.info("=" * 60)
        logging.info("LOGGING SESSION STARTED")
        logging.info(f"Main log file: {self.log_file}")
        logging.info(f"Error log file: {self.error_log_file}")
        logging.info("=" * 60)
    
    def _configure_fastapi_logging(self):
        """Configure FastAPI specific logging"""
        fastapi_logger = logging.getLogger("fastapi")
        fastapi_logger.setLevel(logging.INFO)
        fastapi_logger.propagate = True
    
    def _configure_uvicorn_logging(self):
        """Configure Uvicorn logging"""
        # Uvicorn access logs
        uvicorn_access = logging.getLogger("uvicorn.access")
        uvicorn_access.setLevel(logging.INFO)
        uvicorn_access.propagate = True
        
        # Uvicorn error logs
        uvicorn_error = logging.getLogger("uvicorn.error")
        uvicorn_error.setLevel(logging.INFO)
        uvicorn_error.propagate = True
        
        # Main uvicorn logger
        uvicorn_logger = logging.getLogger("uvicorn")
        uvicorn_logger.setLevel(logging.INFO)
        uvicorn_logger.propagate = True
    
    def _configure_database_logging(self):
        """Configure database related logging"""
        # MongoDB/PyMongo logs
        pymongo_logger = logging.getLogger("pymongo")
        pymongo_logger.setLevel(logging.WARNING)
        pymongo_logger.propagate = True
        
        # Database operations
        db_logger = logging.getLogger("database")
        db_logger.setLevel(logging.DEBUG)
        db_logger.propagate = True
    
    def _configure_application_logging(self):
        """Configure application specific logging"""
        # Routes logging
        routes_logger = logging.getLogger("routes")
        routes_logger.setLevel(logging.DEBUG)
        routes_logger.propagate = True
        
        # CRUD operations
        crud_logger = logging.getLogger("crud")
        crud_logger.setLevel(logging.DEBUG)
        crud_logger.propagate = True
        
        # Services logging
        services_logger = logging.getLogger("services")
        services_logger.setLevel(logging.DEBUG)
        services_logger.propagate = True
        
        # AI/Mistral service
        ai_logger = logging.getLogger("mistral")
        ai_logger.setLevel(logging.DEBUG)
        ai_logger.propagate = True
        
        # Reduce noise from development tools
        watchfiles_logger = logging.getLogger("watchfiles")
        watchfiles_logger.setLevel(logging.WARNING)  # Only warnings and errors
        watchfiles_logger.propagate = True
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get a logger instance"""
        return logging.getLogger(name or __name__)
    
    def log_startup(self):
        """Log application startup information"""
        logger = self.get_logger("startup")
        logger.info("FastAPI Backend Application Starting...")
        logger.info(f"Python version: {os.sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Log directory: {self.log_dir.absolute()}")
    
    def log_shutdown(self):
        """Log application shutdown"""
        logger = self.get_logger("shutdown")
        logger.info("FastAPI Backend Application Shutting Down...")
        logger.info("=" * 60)

# Global logger instance
app_logger = Logger()

# Convenience functions
def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance"""
    return app_logger.get_logger(name)

def log_error(message: str, exception: Exception = None, logger_name: str = None):
    """Log an error with optional exception details"""
    logger = get_logger(logger_name or "error")
    if exception:
        logger.error(f"{message}: {str(exception)}", exc_info=True)
    else:
        logger.error(message)

def log_info(message: str, logger_name: str = None):
    """Log an info message"""
    logger = get_logger(logger_name or "info")
    logger.info(message)

def log_warning(message: str, logger_name: str = None):
    """Log a warning message"""
    logger = get_logger(logger_name or "warning")
    logger.warning(message)

def log_debug(message: str, logger_name: str = None):
    """Log a debug message"""
    logger = get_logger(logger_name or "debug")
    logger.debug(message)

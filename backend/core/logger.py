"""
Centralized Logging Configuration
Handles all application logging to file instead of terminal
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from core.config import settings

class ThirdPartyFilter(logging.Filter):
    """Filter to exclude verbose third-party library messages"""
    
    def filter(self, record):
        # Allow all messages if DEBUG_THIRD_PARTY is enabled
        if hasattr(settings, 'DEBUG_THIRD_PARTY') and settings.DEBUG_THIRD_PARTY:
            return True
            
        # List of third-party loggers to suppress at DEBUG level
        noisy_loggers = [
            "watchfiles",
            "httpcore", 
            "httpx",
            "pymongo",
            "faiss",
            "asyncio",
            "uvicorn.protocols",
            "uvicorn.server"
        ]
        
        # Suppress DEBUG and INFO level messages from noisy third-party libraries
        if any(record.name.startswith(logger) for logger in noisy_loggers):
            if record.levelno <= logging.INFO:
                return False
        
        # Allow our application logs (anything not starting with common third-party prefixes)
        if not any(record.name.startswith(prefix) for prefix in ["watchfiles", "httpcore", "httpx", "pymongo", "faiss", "asyncio", "uvicorn"]):
            return True
            
        # Allow WARNING and above from third-party libraries
        if record.levelno >= logging.WARNING:
            return True
            
        return False

class Logger:
    """Centralized logger for the application"""
    
    def __init__(self):
        # Use absolute path relative to this file's location
        current_file_dir = Path(__file__).parent.parent  # backend directory
        self.log_dir = current_file_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Session tracking to avoid duplicate prompts
        self.logged_sessions = set()
        
        # Create static log filenames (no date dependency)
        self.debug_log_file = self.log_dir / "debug.txt"
        self.error_log_file = self.log_dir / "error.txt"
        self.timing_log_file = self.log_dir / "timing.txt"
        self.prompt_log_file = self.log_dir / "prompt.txt"
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration with 4 separate log files"""
        
        # Remove all existing handlers to avoid duplicates
        logging.getLogger().handlers.clear()
        
        # Create formatters for different log types
        debug_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        error_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        timing_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        prompt_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
    def _setup_logging(self):
        """Setup logging configuration with 4 separate log files"""
        
        # Remove all existing handlers to avoid duplicates
        logging.getLogger().handlers.clear()
        
        # Create formatters for different log types
        debug_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        error_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        timing_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        prompt_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Force immediate flushing for live logging
        class FlushingHandler(logging.handlers.RotatingFileHandler):
            def emit(self, record):
                super().emit(record)
                self.flush()  # Force flush after each log entry
        
        # DEBUG LOG HANDLER - for debug and info messages
        debug_handler = FlushingHandler(
            self.debug_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(debug_formatter)
        debug_handler.addFilter(ThirdPartyFilter())
        
        # ERROR LOG HANDLER - for errors only
        error_handler = FlushingHandler(
            self.error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(error_formatter)
        
        # Console handler for minimal output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.CRITICAL)
        console_handler.setFormatter(error_formatter)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(debug_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)
        
        # Configure specific loggers
        self._configure_application_logging()
        
        # Log the start of logging session
        logging.info("=" * 60)
        logging.info("LOGGING SESSION STARTED")
        logging.info(f"Debug log file: {self.debug_log_file}")
        logging.info(f"Error log file: {self.error_log_file}")
        logging.info(f"Timing log file: {self.timing_log_file}")
        logging.info(f"Prompt log file: {self.prompt_log_file}")
        logging.info("=" * 60)
    
    def _configure_application_logging(self):
        """Configure application specific logging with reduced third-party noise"""
        
        # Check if we should enable minimal logging
        minimal_logging = getattr(settings, 'MINIMAL_LOGGING', True)
        debug_third_party = getattr(settings, 'DEBUG_THIRD_PARTY', False)
        
        # Third-party libraries - set to WARNING or higher to reduce noise
        if not debug_third_party:
            noisy_loggers = {
                "watchfiles": logging.ERROR,     # Only errors
                "httpcore": logging.ERROR,       # Only errors  
                "httpx": logging.INFO,           # Keep some httpx info for API calls
                "pymongo": logging.ERROR,        # Only errors from MongoDB
                "faiss": logging.ERROR,          # Only errors from FAISS
                "asyncio": logging.ERROR,        # Only errors from asyncio
                "uvicorn.protocols": logging.ERROR,
                "uvicorn.server": logging.ERROR,
                "uvicorn.access": logging.ERROR,  # Suppress access logs completely
            }
            
            for logger_name, level in noisy_loggers.items():
                logger = logging.getLogger(logger_name)
                logger.setLevel(level)
                logger.propagate = True
        
        # Keep uvicorn.error at INFO for important server messages
        uvicorn_error_logger = logging.getLogger("uvicorn.error")
        uvicorn_error_logger.setLevel(logging.INFO)
        uvicorn_error_logger.propagate = True
        
        # Our application loggers - adjust based on minimal_logging setting
        app_loggers = [
            "main", "startup", "mistral_service", "rag_service", 
            "document_processor", "embedding_service", "database",
            "routes", "core"
        ]
        
        app_level = logging.INFO if minimal_logging else logging.DEBUG
        for logger_name in app_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(app_level)
            logger.propagate = True
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get a logger instance"""
        return logging.getLogger(name or __name__)
    
    def log_timing(self, session_id: str, stage: str, duration: float, details: str = ""):
        """Log timing information to timing.txt"""
        timing_msg = f"TIMING | {session_id} | {stage} | {duration:.3f}s | {details}"
        
        with open(self.timing_log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} | {timing_msg}\n")
            f.flush()
    
    def log_prompt(self, session_id: str, prompt_content: str, response_content: str, prompt_type: str):
        """Log LLM prompts and responses to prompt.txt (with deduplication)"""
        
        # Create a unique key for this session and type
        session_key = f"{session_id}:{prompt_type}"
        
        # Skip if MINIMAL_LOGGING is enabled and this is a duplicate type for the session
        if hasattr(settings, 'MINIMAL_LOGGING') and settings.MINIMAL_LOGGING:
            # Only log the final result for each session to avoid duplicates
            skip_types = ["mistral_request", "rag_generation"]  # Skip intermediate steps
            if prompt_type in skip_types:
                return
                
            # For other types, check if we've already logged this session
            if session_key in self.logged_sessions:
                return
            self.logged_sessions.add(session_key)
        
        with open(self.prompt_log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Simplified logging format
            f.write(f"{timestamp} | SESSION: {session_id} | TYPE: {prompt_type}\n")
            
            # Extract just the user query from complex prompts
            if isinstance(prompt_content, str) and "User Question:" in prompt_content:
                # Extract the actual user question
                try:
                    user_question = prompt_content.split("User Question:")[-1].split("Instructions:")[0].strip()
                    f.write(f"USER_QUERY: {user_question}\n")
                except:
                    # Fallback to first 200 chars
                    f.write(f"QUERY: {prompt_content[:200]}...\n")
            else:
                # Only show first 200 chars of prompt if it's too long
                if len(str(prompt_content)) > 200:
                    prompt_preview = str(prompt_content)[:200] + "..."
                else:
                    prompt_preview = str(prompt_content)
                f.write(f"QUERY: {prompt_preview}\n")
                
            f.write(f"RESPONSE: {response_content}\n")
            f.write("-" * 80 + "\n")
            f.flush()
    
    def log_debug_session(self, session_id: str, filename: str, level: str, description: str):
        """Log debug information with session tracking"""
        debug_logger = self.get_logger(filename)
        if level.upper() == "DEBUG":
            debug_logger.debug(f"SESSION: {session_id} | {description}")
        else:
            debug_logger.info(f"SESSION: {session_id} | {description}")
    
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

# Convenience functions with session tracking
def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance"""
    return app_logger.get_logger(name)

def log_debug_session(session_id: str, filename: str, description: str):
    """Log debug information with session tracking"""
    app_logger.log_debug_session(session_id, filename, "DEBUG", description)

def log_info_session(session_id: str, filename: str, description: str):
    """Log info information with session tracking"""
    app_logger.log_debug_session(session_id, filename, "INFO", description)

def log_timing(session_id: str, stage: str, duration: float, details: str = ""):
    """Log timing information"""
    app_logger.log_timing(session_id, stage, duration, details)

def log_prompt(session_id: str, prompt_content: str, response_content: str, prompt_type: str):
    """Log LLM prompts and responses"""
    app_logger.log_prompt(session_id, prompt_content, response_content, prompt_type)

def log_error_session(session_id: str, message: str, exception: Exception = None):
    """Log an error with session tracking"""
    logger = get_logger("error")
    error_msg = f"SESSION: {session_id} | {message}"
    if exception:
        logger.error(error_msg + f" | EXCEPTION: {str(exception)}", exc_info=True)
    else:
        logger.error(error_msg)

# Legacy support functions (keeping for backward compatibility)
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

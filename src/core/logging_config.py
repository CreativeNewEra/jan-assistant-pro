"""
Logging configuration for Jan Assistant Pro
Provides structured logging with multiple outputs and levels
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional, Dict, Any
from datetime import datetime
import json

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, default=str)

class ContextFilter(logging.Filter):
    """Add context information to log records"""
    
    def __init__(self, context: Dict[str, Any] = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to record"""
        if not hasattr(record, 'extra_fields'):
            record.extra_fields = {}
        record.extra_fields.update(self.context)
        return True

def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    app_name: str = "jan_assistant_pro",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = False,
    max_bytes: int = 10_000_000,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up comprehensive logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        app_name: Application name for log files
        enable_console: Whether to log to console
        enable_file: Whether to log to files
        enable_json: Whether to use JSON formatting
        max_bytes: Maximum size of log files before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured root logger
    """
    
    # Create logs directory if it doesn't exist
    if enable_file and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if enable_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    if enable_file:
        # File handler for all logs
        all_logs_file = os.path.join(log_dir, f"{app_name}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            all_logs_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Error-only file handler
        error_file = os.path.join(log_dir, f"{app_name}_errors.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
    
    # Log startup
    root_logger.info(f"Logging initialized for {app_name}")
    root_logger.info(f"Log level: {log_level}")
    root_logger.info(f"Console logging: {enable_console}")
    root_logger.info(f"File logging: {enable_file}")
    
    return root_logger

def get_logger(name: str, context: Dict[str, Any] = None) -> logging.Logger:
    """
    Get a logger with optional context
    
    Args:
        name: Logger name
        context: Additional context to include in logs
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    if context:
        context_filter = ContextFilter(context)
        logger.addFilter(context_filter)
    
    return logger

def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {str(e)}")
            raise
    
    return wrapper

def log_performance(func):
    """Decorator to log function performance"""
    def wrapper(*args, **kwargs):
        import time
        logger = logging.getLogger(func.__module__)
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {str(e)}")
            raise
    
    return wrapper

class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self.logger.debug(message, extra={'extra_fields': kwargs})
    
    def log_info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, extra={'extra_fields': kwargs})
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.warning(message, extra={'extra_fields': kwargs})
    
    def log_error(self, message: str, **kwargs):
        """Log error message with context"""
        self.logger.error(message, extra={'extra_fields': kwargs})
    
    def log_exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra={'extra_fields': kwargs})

def configure_third_party_loggers():
    """Configure logging levels for third-party libraries"""
    # Reduce noise from common libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

def create_audit_logger(audit_file: str = "logs/audit.log") -> logging.Logger:
    """
    Create a dedicated audit logger for security events
    
    Args:
        audit_file: Path to audit log file
        
    Returns:
        Configured audit logger
    """
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    
    # Ensure audit directory exists
    os.makedirs(os.path.dirname(audit_file), exist_ok=True)
    
    # Create audit file handler
    handler = logging.handlers.RotatingFileHandler(
        audit_file,
        maxBytes=10_000_000,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    
    # Use JSON formatting for audit logs
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    
    audit_logger.addHandler(handler)
    audit_logger.propagate = False  # Don't propagate to root logger
    
    return audit_logger

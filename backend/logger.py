"""
Centralized Logging Service

Provides consistent, structured logging across the entire application.
All modules should import and use this logger instead of creating their own.
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

from pythonjsonlogger import jsonlogger


class LogConfig:
    """Logging configuration constants."""
    
    # Log levels
    DEFAULT_LEVEL = logging.INFO
    DEBUG_LEVEL = logging.DEBUG
    
    # File settings
    MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 5
    
    # Formats
    CONSOLE_FORMAT = "%(asctime)s │ %(levelname)-8s │ %(name)-20s │ %(message)s"
    FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
    JSON_FORMAT = "%(asctime)s %(levelname)s %(name)s %(funcName)s %(lineno)d %(message)s"
    
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    # ANSI color codes
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[41m",  # Red background
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    def __init__(self, fmt: str, datefmt: str, use_colors: bool = True):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        if self.use_colors:
            color = self.COLORS.get(record.levelno, self.RESET)
            record.levelname = f"{color}{record.levelname}{self.RESET}"
            
            # Highlight logger name
            record.name = f"{self.BOLD}{record.name}{self.RESET}"
        
        return super().format(record)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno
        
        # Add service identifier
        log_record["service"] = "resume-tailor"


class LoggerService:
    """
    Centralized logging service.
    
    Provides a singleton-like interface for consistent logging across
    all application modules.
    
    Usage:
        from logger import logger
        logger.info("Message here")
        
        # Or get a named logger for a specific module
        from logger import get_logger
        log = get_logger("my_module")
        log.info("Module-specific message")
    """
    
    _instance: Optional["LoggerService"] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if LoggerService._initialized:
            return
        
        self._loggers: dict[str, logging.Logger] = {}
        self._log_dir: Optional[Path] = None
        self._debug_mode: bool = False
        
        LoggerService._initialized = True
    
    def setup(
        self,
        log_dir: Path,
        debug: bool = False,
        enable_json: bool = False,
        app_name: str = "resume-tailor",
    ) -> None:
        """
        Initialize the logging system.
        
        Args:
            log_dir: Directory to store log files
            debug: Enable debug level logging
            enable_json: Enable JSON formatted logs (for production)
            app_name: Application name for log identification
        """
        self._log_dir = log_dir
        self._debug_mode = debug
        self._app_name = app_name
        
        # Ensure log directory exists
        self._log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(LogConfig.DEBUG_LEVEL if debug else LogConfig.DEFAULT_LEVEL)
        
        # Remove any existing handlers
        root_logger.handlers.clear()
        
        # Add handlers
        root_logger.addHandler(self._create_console_handler(debug))
        root_logger.addHandler(self._create_file_handler("app.log", debug))
        root_logger.addHandler(self._create_error_file_handler("error.log"))
        
        if enable_json:
            root_logger.addHandler(self._create_json_handler("app.json.log"))
        
        # Log initialization
        init_logger = self.get_logger("logger.setup")
        init_logger.info(f"Logging initialized | debug={debug} | log_dir={log_dir}")
    
    def _create_console_handler(self, debug: bool) -> logging.Handler:
        """Create console handler with colored output."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(LogConfig.DEBUG_LEVEL if debug else LogConfig.DEFAULT_LEVEL)
        
        # Use colors if outputting to a terminal
        use_colors = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        formatter = ColoredFormatter(
            LogConfig.CONSOLE_FORMAT,
            LogConfig.DATE_FORMAT,
            use_colors=use_colors,
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_file_handler(self, filename: str, debug: bool) -> logging.Handler:
        """Create rotating file handler for general logs."""
        log_path = self._log_dir / filename
        
        handler = RotatingFileHandler(
            log_path,
            maxBytes=LogConfig.MAX_BYTES,
            backupCount=LogConfig.BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setLevel(LogConfig.DEBUG_LEVEL if debug else LogConfig.DEFAULT_LEVEL)
        
        formatter = logging.Formatter(LogConfig.FILE_FORMAT, LogConfig.DATE_FORMAT)
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_error_file_handler(self, filename: str) -> logging.Handler:
        """Create file handler for errors only."""
        log_path = self._log_dir / filename
        
        handler = RotatingFileHandler(
            log_path,
            maxBytes=LogConfig.MAX_BYTES,
            backupCount=LogConfig.BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setLevel(logging.ERROR)
        
        formatter = logging.Formatter(LogConfig.FILE_FORMAT, LogConfig.DATE_FORMAT)
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_json_handler(self, filename: str) -> logging.Handler:
        """Create JSON formatted file handler for structured logging."""
        log_path = self._log_dir / filename
        
        handler = RotatingFileHandler(
            log_path,
            maxBytes=LogConfig.MAX_BYTES,
            backupCount=LogConfig.BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setLevel(LogConfig.DEFAULT_LEVEL)
        
        formatter = CustomJsonFormatter(LogConfig.JSON_FORMAT)
        handler.setFormatter(formatter)
        
        return handler
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a named logger instance.
        
        Args:
            name: Logger name (typically module name)
            
        Returns:
            logging.Logger: Configured logger instance
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        
        return self._loggers[name]
    
    def set_level(self, level: int, logger_name: Optional[str] = None) -> None:
        """
        Change log level at runtime.
        
        Args:
            level: New logging level
            logger_name: Specific logger to modify (None for root)
        """
        if logger_name:
            logging.getLogger(logger_name).setLevel(level)
        else:
            logging.getLogger().setLevel(level)


# Global logger service instance
_logger_service = LoggerService()


def setup_logging(
    log_dir: Path,
    debug: bool = False,
    enable_json: bool = False,
    app_name: str = "resume-tailor",
) -> None:
    """
    Initialize application logging.
    
    Call this once at application startup.
    
    Args:
        log_dir: Directory for log files
        debug: Enable debug mode
        enable_json: Enable JSON logs
        app_name: Application identifier
    """
    _logger_service.setup(log_dir, debug, enable_json, app_name)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name (use __name__ for module name)
        
    Returns:
        logging.Logger: Configured logger
        
    Example:
        from logger import get_logger
        logger = get_logger(__name__)
        logger.info("Hello from my module")
    """
    return _logger_service.get_logger(name)


# Convenience: Default application logger
logger = get_logger("app")

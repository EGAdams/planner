"""
Logging configuration for nonprofit finance database
"""

import logging
import logging.config
import os
from pathlib import Path
from datetime import datetime
import structlog
from typing import Dict, Any


def setup_logging(
    log_level: str = "INFO",
    log_file: str = None,
    enable_structured_logging: bool = True,
    enable_console_logging: bool = True
) -> None:
    """
    Setup logging configuration for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        enable_structured_logging: Enable structured logging with structlog
        enable_console_logging: Enable console logging
    """

    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Default log file if not provided
    if log_file is None:
        log_file = log_dir / f"nonprofit_finance_{datetime.now().strftime('%Y%m%d')}.log"

    # Configure standard logging
    logging_config = _get_logging_config(log_level, log_file, enable_console_logging)
    logging.config.dictConfig(logging_config)

    # Configure structured logging if enabled
    if enable_structured_logging:
        _setup_structured_logging()

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "log_file": str(log_file),
            "structured_logging": enable_structured_logging,
            "console_logging": enable_console_logging
        }
    )


def _get_logging_config(log_level: str, log_file: str, enable_console: bool) -> Dict[str, Any]:
    """Get logging configuration dictionary"""

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(lineno)d %(message)s"
            }
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": str(log_file),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(Path(log_file).parent / "errors.log"),
                "maxBytes": 10485760,
                "backupCount": 5,
                "encoding": "utf8"
            }
        },
        "loggers": {
            # Application loggers
            "parsers": {
                "level": log_level,
                "handlers": ["file"],
                "propagate": False
            },
            "detection": {
                "level": log_level,
                "handlers": ["file"],
                "propagate": False
            },
            "ingestion": {
                "level": log_level,
                "handlers": ["file"],
                "propagate": False
            },
            "app": {
                "level": log_level,
                "handlers": ["file"],
                "propagate": False
            },
            # Third-party loggers
            "mysql.connector": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False
            },
            "urllib3": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["file", "error_file"]
        }
    }

    # Add console handler if enabled
    if enable_console:
        config["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        }

        # Add console to all loggers
        for logger_name in config["loggers"]:
            config["loggers"][logger_name]["handlers"].append("console")

        config["root"]["handlers"].append("console")

    return config


def _setup_structured_logging():
    """Setup structured logging with structlog"""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class DatabaseLogHandler(logging.Handler):
    """Custom log handler that writes to database"""

    def __init__(self, db_connection=None):
        super().__init__()
        self.db_connection = db_connection

    def emit(self, record):
        """Emit log record to database"""
        if not self.db_connection:
            return

        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line_number': record.lineno,
                'thread_id': record.thread,
                'process_id': record.process
            }

            if record.exc_info:
                log_entry['exception'] = self.format(record)

            # TODO: Implement database logging when repositories are available
            # self._save_log_entry(log_entry)

        except Exception:
            self.handleError(record)


class ImportLoggerMixin:
    """Mixin class to provide logging functionality for import operations"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__class__.__module__)

    def log_import_start(self, file_path: str, org_id: int):
        """Log start of import operation"""
        self.logger.info(
            "Starting import operation",
            extra={
                "operation": "import_start",
                "file_path": file_path,
                "org_id": org_id
            }
        )

    def log_import_complete(self, file_path: str, org_id: int, result: Dict[str, Any]):
        """Log completion of import operation"""
        self.logger.info(
            "Import operation completed",
            extra={
                "operation": "import_complete",
                "file_path": file_path,
                "org_id": org_id,
                "total_transactions": result.get("total_transactions", 0),
                "successful_imports": result.get("successful_imports", 0),
                "failed_imports": result.get("failed_imports", 0),
                "duplicate_count": result.get("duplicate_count", 0),
                "success": result.get("success", False)
            }
        )

    def log_duplicate_detection(self, transaction_count: int, duplicate_count: int):
        """Log duplicate detection results"""
        self.logger.info(
            "Duplicate detection completed",
            extra={
                "operation": "duplicate_detection",
                "transaction_count": transaction_count,
                "duplicate_count": duplicate_count,
                "duplicate_rate": (duplicate_count / transaction_count * 100) if transaction_count > 0 else 0
            }
        )

    def log_validation_error(self, transaction_index: int, error: str):
        """Log validation error"""
        self.logger.warning(
            "Transaction validation failed",
            extra={
                "operation": "validation_error",
                "transaction_index": transaction_index,
                "error": error
            }
        )

    def log_parsing_error(self, file_path: str, error: str):
        """Log parsing error"""
        self.logger.error(
            "File parsing failed",
            extra={
                "operation": "parsing_error",
                "file_path": file_path,
                "error": error
            }
        )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)


def log_performance(func):
    """Decorator to log function performance"""
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.debug(
                f"Function {func.__name__} completed",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "success": True
                }
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            logger.error(
                f"Function {func.__name__} failed",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "success": False,
                    "error": str(e)
                }
            )
            raise

    return wrapper


# Environment-based logging configuration
def setup_environment_logging():
    """Setup logging based on environment variables"""

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE")
    enable_structured = os.getenv("ENABLE_STRUCTURED_LOGGING", "true").lower() == "true"
    enable_console = os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() == "true"

    setup_logging(
        log_level=log_level,
        log_file=log_file,
        enable_structured_logging=enable_structured,
        enable_console_logging=enable_console
    )


# Initialize logging when module is imported
if not logging.getLogger().handlers:
    setup_environment_logging()
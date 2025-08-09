"""
Logging configuration for the Task Management API.
"""

import logging
import sys
import json
from typing import Dict, Any
from datetime import datetime
from app.config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging in production.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, "duration"):
            log_entry["duration"] = record.duration
            
        # Add HTTP request fields
        if hasattr(record, "method"):
            log_entry["method"] = record.method
            
        if hasattr(record, "url"):
            log_entry["url"] = record.url
            
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
            
        if hasattr(record, "ip_address"):
            log_entry["ip_address"] = record.ip_address
            
        # Add service information
        log_entry["service"] = "task-api"
        log_entry["version"] = "1.0.0"
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry)


def setup_logging() -> None:
    """
    Configure logging for the application.
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.debug:
        # Development: Human-readable format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setLevel(logging.DEBUG)
    else:
        # Production: JSON format
        formatter = JSONFormatter()
        console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    configure_loggers()


def configure_loggers() -> None:
    """
    Configure specific loggers for different components.
    """
    loggers_config = {
        "app": settings.log_level.upper(),
        "uvicorn.access": "INFO",
        "uvicorn.error": "INFO",
        "sqlalchemy.engine": "WARNING" if not settings.debug else "INFO",
        "alembic": "INFO",
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level))


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name, typically __name__
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Request logging utilities
class RequestLogger:
    """
    Utility class for logging HTTP requests.
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(
        self, 
        method: str, 
        url: str, 
        status_code: int,
        duration: float,
        user_id: str = None,
        request_id: str = None
    ) -> None:
        """
        Log HTTP request information.
        
        Args:
            method: HTTP method
            url: Request URL
            status_code: HTTP status code
            duration: Request duration in seconds
            user_id: Optional user ID
            request_id: Optional request ID
        """
        extra = {
            "request_method": method,
            "request_url": url,
            "status_code": status_code,
            "duration": duration,
        }
        
        if user_id:
            extra["user_id"] = user_id
        
        if request_id:
            extra["request_id"] = request_id
        
        level = logging.INFO
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING
        
        self.logger.log(
            level,
            f"{method} {url} - {status_code} ({duration:.3f}s)",
            extra=extra
        )


# Security logging utilities
class SecurityLogger:
    """
    Utility class for logging security-related events.
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_auth_attempt(
        self, 
        username: str, 
        success: bool, 
        ip_address: str,
        user_agent: str = None
    ) -> None:
        """Log authentication attempt."""
        extra = {
            "event_type": "auth_attempt",
            "username": username,
            "success": success,
            "ip_address": ip_address,
        }
        
        if user_agent:
            extra["user_agent"] = user_agent
        
        level = logging.INFO if success else logging.WARNING
        message = f"Authentication {'successful' if success else 'failed'} for {username}"
        
        self.logger.log(level, message, extra=extra)
    
    def log_rate_limit_exceeded(self, ip_address: str, endpoint: str) -> None:
        """Log rate limit violation."""
        extra = {
            "event_type": "rate_limit_exceeded",
            "ip_address": ip_address,
            "endpoint": endpoint,
        }
        
        self.logger.warning(
            f"Rate limit exceeded for {ip_address} on {endpoint}",
            extra=extra
        )
    
    def log_suspicious_activity(
        self, 
        activity_type: str, 
        details: Dict[str, Any],
        ip_address: str = None
    ) -> None:
        """Log suspicious activity."""
        extra = {
            "event_type": "suspicious_activity",
            "activity_type": activity_type,
            "details": details,
        }
        
        if ip_address:
            extra["ip_address"] = ip_address
        
        self.logger.error(
            f"Suspicious activity detected: {activity_type}",
            extra=extra
        )
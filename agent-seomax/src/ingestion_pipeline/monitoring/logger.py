"""
Structured Logging Configuration

Provides centralized logging configuration with support for:
- Multiple log handlers (console, file, GCP Cloud Logging)
- Structured log formatting with context
- Log level management
- Performance and audit logging
"""

import os
import sys
import logging
import structlog
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from structlog.processors import (
    JSONRenderer,
    TimeStamper,
    StackInfoRenderer,
    format_exc_info,
    UnicodeDecoder,
)
from structlog.stdlib import (
    add_log_level,
    add_logger_name,
    BoundLogger,
    ProcessorFormatter,
)


# Log level mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class PipelineLogger:
    """
    Centralized logging configuration for the ingestion pipeline.
    
    Features:
    - Structured logging with context propagation
    - Multiple output handlers (console, file, GCP)
    - Performance logging with timing context
    - Audit logging for security events
    - Component-specific loggers with shared configuration
    
    Example:
        # Initialize logging
        logger_manager = PipelineLogger(
            log_level="INFO",
            log_file="pipeline.log",
            enable_gcp=True
        )
        
        # Get logger for component
        logger = logger_manager.get_logger("api_client")
        
        # Log with context
        logger.info("resource_fetched", resource_id="vm-123", duration_ms=45.2)
        
        # Audit logging
        logger_manager.audit_log("user_access", user="admin", resource="vm-123")
    """
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        log_dir: Optional[str] = None,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_gcp: bool = False,
        json_format: bool = False,
        include_timestamp: bool = True,
        include_caller: bool = True,
    ):
        """
        Initialize pipeline logger.
        
        Args:
            log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Log file name (default: pipeline_{timestamp}.log)
            log_dir: Directory for log files (default: ./logs)
            enable_console: Enable console output
            enable_file: Enable file output
            enable_gcp: Enable GCP Cloud Logging
            json_format: Use JSON format for logs
            include_timestamp: Include timestamps in logs
            include_caller: Include caller information in logs
        """
        self.log_level = LOG_LEVELS.get(log_level.upper(), logging.INFO)
        self.log_dir = log_dir or os.getenv("LOG_DIR", "./logs")
        self.log_file = log_file
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_gcp = enable_gcp
        self.json_format = json_format
        self.include_timestamp = include_timestamp
        self.include_caller = include_caller
        
        # Create log directory if needed
        if self.enable_file:
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)
            
            if not self.log_file:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                self.log_file = f"pipeline_{timestamp}.log"
        
        # Audit log file
        self.audit_file = os.path.join(self.log_dir, "audit.log") if enable_file else None
        
        # Initialize logging
        self._configure_structlog()
        self._configure_stdlib_logging()
        
        # Create root logger
        self.root_logger = structlog.get_logger("pipeline")
        self.root_logger.info(
            "logging_initialized",
            log_level=log_level,
            log_file=self.log_file,
            log_dir=self.log_dir,
            enable_console=enable_console,
            enable_file=enable_file,
            enable_gcp=enable_gcp,
        )
    
    def _configure_structlog(self) -> None:
        """Configure structlog with processors."""
        processors = [
            # Add log level to event dict
            add_log_level,
            # Add logger name to event dict
            add_logger_name,
            # Decode unicode
            UnicodeDecoder(),
        ]
        
        if self.include_timestamp:
            # Add ISO timestamp
            processors.append(TimeStamper(fmt="iso"))
        
        if self.include_caller:
            # Add caller information
            processors.append(
                structlog.processors.CallsiteParameterAdder(
                    [
                        structlog.processors.CallsiteParameter.FILENAME,
                        structlog.processors.CallsiteParameter.FUNC_NAME,
                        structlog.processors.CallsiteParameter.LINENO,
                    ]
                )
            )
        
        # Add stack info and exception formatting
        processors.extend([
            StackInfoRenderer(),
            format_exc_info,
        ])
        
        # Final renderer
        if self.json_format:
            processors.append(JSONRenderer())
        else:
            processors.append(
                structlog.dev.ConsoleRenderer(colors=self.enable_console)
            )
        
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    def _configure_stdlib_logging(self) -> None:
        """Configure standard library logging with handlers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create formatter
        if self.json_format:
            formatter = ProcessorFormatter(
                processor=JSONRenderer(),
            )
        else:
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        
        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if self.enable_file and self.log_file:
            file_path = os.path.join(self.log_dir, self.log_file)
            file_handler = logging.FileHandler(file_path, mode="a")
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        # GCP Cloud Logging handler
        if self.enable_gcp:
            try:
                from google.cloud import logging as gcp_logging
                
                client = gcp_logging.Client()
                gcp_handler = client.get_default_handler()
                gcp_handler.setLevel(self.log_level)
                root_logger.addHandler(gcp_handler)
            except Exception as e:
                # Fallback if GCP logging not available
                root_logger.warning(f"Failed to initialize GCP logging: {e}")
    
    def get_logger(
        self,
        name: str,
        **context: Any
    ) -> BoundLogger:
        """
        Get a logger for a specific component.
        
        Args:
            name: Logger name (typically component name)
            **context: Additional context to bind to logger
            
        Returns:
            BoundLogger instance with context
        """
        logger = structlog.get_logger(name)
        if context:
            logger = logger.bind(**context)
        return logger
    
    def audit_log(
        self,
        event: str,
        **context: Any
    ) -> None:
        """
        Log an audit event for security/compliance tracking.
        
        Args:
            event: Audit event name
            **context: Event context (user, resource, action, etc.)
        """
        audit_logger = self.get_logger("audit")
        
        # Add audit-specific context
        audit_context = {
            "event_type": "audit",
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            **context,
        }
        
        audit_logger.info("audit_event", **audit_context)
        
        # Write to dedicated audit log file
        if self.audit_file:
            try:
                with open(self.audit_file, "a") as f:
                    import json
                    f.write(json.dumps(audit_context) + "\n")
            except Exception as e:
                audit_logger.error("audit_log_write_failed", error=str(e))
    
    def set_log_level(self, level: str) -> None:
        """
        Change the log level at runtime.
        
        Args:
            level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        new_level = LOG_LEVELS.get(level.upper(), logging.INFO)
        
        # Update structlog
        self.log_level = new_level
        
        # Update all stdlib handlers
        root_logger = logging.getLogger()
        root_logger.setLevel(new_level)
        
        for handler in root_logger.handlers:
            handler.setLevel(new_level)
        
        self.root_logger.info("log_level_changed", new_level=level)
    
    def flush(self) -> None:
        """Flush all log handlers."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            handler.flush()
    
    def close(self) -> None:
        """Close all log handlers."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            handler.close()
        
        self.root_logger.info("logging_closed")


# Global logger instance (singleton)
_logger_instance: Optional[PipelineLogger] = None


def get_pipeline_logger() -> PipelineLogger:
    """
    Get the global pipeline logger instance.
    
    Returns:
        PipelineLogger singleton instance
    """
    global _logger_instance
    
    if _logger_instance is None:
        # Initialize with environment-based configuration
        _logger_instance = PipelineLogger(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_dir=os.getenv("LOG_DIR", "./logs"),
            enable_console=os.getenv("LOG_CONSOLE", "true").lower() == "true",
            enable_file=os.getenv("LOG_FILE", "true").lower() == "true",
            enable_gcp=os.getenv("LOG_GCP", "false").lower() == "true",
            json_format=os.getenv("LOG_JSON", "false").lower() == "true",
        )
    
    return _logger_instance


def initialize_logging(**kwargs: Any) -> PipelineLogger:
    """
    Initialize the global pipeline logger with custom configuration.
    
    Args:
        **kwargs: Configuration options for PipelineLogger
        
    Returns:
        Configured PipelineLogger instance
    """
    global _logger_instance
    _logger_instance = PipelineLogger(**kwargs)
    return _logger_instance


def get_logger(name: str, **context: Any) -> BoundLogger:
    """
    Convenience function to get a component logger.
    
    Args:
        name: Logger name
        **context: Additional context to bind
        
    Returns:
        BoundLogger instance
    """
    return get_pipeline_logger().get_logger(name, **context)

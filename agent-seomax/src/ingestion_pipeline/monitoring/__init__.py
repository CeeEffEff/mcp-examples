"""
Monitoring and Logging Module

Provides comprehensive monitoring, logging, and alerting for the ingestion pipeline.

Features:
- Structured logging with multiple output handlers
- Prometheus metrics collection and exposition
- Health monitoring for all components
- Rule-based alerting with multi-channel notifications
- Dashboard-ready data aggregation

Quick Start:
    ```python
    from ingestion_pipeline.monitoring import (
        initialize_monitoring,
        get_logger,
        get_metrics,
        get_health_monitor,
        get_alert_manager,
    )
    
    # Initialize all monitoring systems
    monitoring = initialize_monitoring(
        log_level="INFO",
        enable_prometheus=True,
        health_check_interval=60,
    )
    
    # Get component logger
    logger = get_logger("my_component")
    logger.info("component_started", version="1.0.0")
    
    # Track metrics
    metrics = get_metrics()
    with metrics.track_processing("compute"):
        # Process data
        pass
    
    # Register health check
    health = get_health_monitor()
    health.register_check("my_component", my_health_check)
    
    # Setup alerts
    alerts = get_alert_manager()
    alerts.register_rule(my_alert_rule)
    alerts.add_channel(AlertChannel.LOG)
    ```
"""

from typing import Dict, Any, Optional

# Logger
from .logger import (
    PipelineLogger,
    get_pipeline_logger,
    initialize_logging,
    get_logger,
)

# Metrics
from .metrics import (
    PipelineMetrics,
    MetricSnapshot,
    get_pipeline_metrics,
    initialize_metrics,
)

# Health
from .health import (
    HealthMonitor,
    HealthStatus,
    HealthCheck,
    SystemHealth,
    get_health_monitor,
    initialize_health_monitor,
    create_ping_check,
    create_connection_check,
    create_threshold_check,
)

# Alerts
from .alerts import (
    AlertManager,
    AlertSeverity,
    AlertStatus,
    Alert,
    AlertRule,
    AlertChannel,
    get_alert_manager,
    initialize_alert_manager,
)


__all__ = [
    # Main functions
    "initialize_monitoring",
    "get_monitoring_status",
    "shutdown_monitoring",
    # Logger
    "PipelineLogger",
    "get_pipeline_logger",
    "initialize_logging",
    "get_logger",
    # Metrics
    "PipelineMetrics",
    "MetricSnapshot",
    "get_pipeline_metrics",
    "initialize_metrics",
    "get_metrics",
    # Health
    "HealthMonitor",
    "HealthStatus",
    "HealthCheck",
    "SystemHealth",
    "get_health_monitor",
    "initialize_health_monitor",
    "create_ping_check",
    "create_connection_check",
    "create_threshold_check",
    # Alerts
    "AlertManager",
    "AlertSeverity",
    "AlertStatus",
    "Alert",
    "AlertRule",
    "AlertChannel",
    "get_alert_manager",
    "initialize_alert_manager",
]


# Monitoring state
_monitoring_initialized = False


def initialize_monitoring(
    # Logging configuration
    log_level: str = "INFO",
    log_dir: str = "./logs",
    enable_console_log: bool = True,
    enable_file_log: bool = True,
    enable_gcp_log: bool = False,
    json_format: bool = False,
    # Metrics configuration
    enable_prometheus: bool = True,
    metrics_namespace: str = "gcp_pipeline",
    # Health monitoring configuration
    enable_health_monitoring: bool = True,
    health_check_interval: int = 60,
    # Alert configuration
    enable_alerting: bool = True,
    alert_channels: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Initialize all monitoring systems with unified configuration.
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        enable_console_log: Enable console logging
        enable_file_log: Enable file logging
        enable_gcp_log: Enable GCP Cloud Logging
        json_format: Use JSON format for logs
        enable_prometheus: Enable Prometheus metrics
        metrics_namespace: Namespace prefix for metrics
        enable_health_monitoring: Enable health monitoring
        health_check_interval: Health check interval in seconds
        enable_alerting: Enable alert system
        alert_channels: List of AlertChannel values to enable
        
    Returns:
        Dictionary with monitoring component references
    """
    global _monitoring_initialized
    
    if _monitoring_initialized:
        logger = get_logger("monitoring")
        logger.warning("monitoring_already_initialized")
        return get_monitoring_status()
    
    # Initialize logging
    logger_instance = initialize_logging(
        log_level=log_level,
        log_dir=log_dir,
        enable_console=enable_console_log,
        enable_file=enable_file_log,
        enable_gcp=enable_gcp_log,
        json_format=json_format,
    )
    
    logger = get_logger("monitoring")
    logger.info("initializing_monitoring_systems")
    
    # Initialize metrics
    metrics_instance = None
    if enable_prometheus:
        metrics_instance = initialize_metrics(
            namespace=metrics_namespace,
            enable_prometheus=True,
        )
        logger.info("metrics_initialized", namespace=metrics_namespace)
    
    # Initialize health monitoring
    health_instance = None
    if enable_health_monitoring:
        health_instance = initialize_health_monitor(
            check_interval=health_check_interval,
        )
        # Start health monitoring in background
        health_instance.start()
        logger.info("health_monitoring_started", check_interval=health_check_interval)
    
    # Initialize alerting
    alert_instance = None
    if enable_alerting:
        alert_instance = initialize_alert_manager()
        
        # Configure default channels
        if alert_channels is None:
            alert_channels = [AlertChannel.LOG, AlertChannel.CONSOLE]
        
        for channel in alert_channels:
            if isinstance(channel, str):
                channel = AlertChannel(channel)
            alert_instance.add_channel(channel)
        
        logger.info("alerting_initialized", channels=[c.value for c in alert_channels])
    
    _monitoring_initialized = True
    
    logger.info("monitoring_systems_initialized")
    
    return {
        "logger": logger_instance,
        "metrics": metrics_instance,
        "health": health_instance,
        "alerts": alert_instance,
        "initialized": True,
    }


def get_metrics() -> PipelineMetrics:
    """
    Convenience function to get pipeline metrics instance.
    
    Returns:
        PipelineMetrics singleton
    """
    return get_pipeline_metrics()


def get_monitoring_status() -> Dict[str, Any]:
    """
    Get status of all monitoring systems.
    
    Returns:
        Dictionary with monitoring system status
    """
    status = {
        "initialized": _monitoring_initialized,
        "logger": None,
        "metrics": None,
        "health": None,
        "alerts": None,
    }
    
    try:
        logger_instance = get_pipeline_logger()
        status["logger"] = {
            "active": True,
            "log_level": logger_instance.log_level,
            "log_dir": logger_instance.log_dir,
        }
    except:
        pass
    
    try:
        metrics_instance = get_pipeline_metrics()
        snapshot = metrics_instance.get_snapshot()
        status["metrics"] = {
            "active": True,
            "namespace": metrics_instance.namespace,
            "snapshot": snapshot.to_dict(),
        }
    except:
        pass
    
    try:
        health_instance = get_health_monitor()
        current_health = health_instance.get_health()
        status["health"] = {
            "active": health_instance._is_running,
            "check_interval": health_instance.check_interval,
            "overall_status": current_health.overall_status.value,
            "healthy_components": current_health.healthy_components,
            "degraded_components": current_health.degraded_components,
            "unhealthy_components": current_health.unhealthy_components,
        }
    except:
        pass
    
    try:
        alert_instance = get_alert_manager()
        alert_stats = alert_instance.get_statistics()
        status["alerts"] = {
            "active": True,
            **alert_stats,
        }
    except:
        pass
    
    return status


def shutdown_monitoring(timeout: int = 10) -> None:
    """
    Gracefully shutdown all monitoring systems.
    
    Args:
        timeout: Maximum time to wait for shutdown in seconds
    """
    global _monitoring_initialized
    
    logger = get_logger("monitoring")
    logger.info("shutting_down_monitoring_systems")
    
    # Stop health monitoring
    try:
        health_instance = get_health_monitor()
        health_instance.stop(timeout=timeout)
        logger.info("health_monitoring_stopped")
    except Exception as e:
        logger.warning("health_monitoring_stop_failed", error=str(e))
    
    # Flush logs
    try:
        logger_instance = get_pipeline_logger()
        logger_instance.flush()
        logger_instance.close()
        logger.info("logging_stopped")
    except Exception as e:
        logger.warning("logging_stop_failed", error=str(e))
    
    _monitoring_initialized = False
    logger.info("monitoring_systems_shutdown_complete")

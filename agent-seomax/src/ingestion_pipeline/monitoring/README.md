# Monitoring and Logging System

Comprehensive monitoring, logging, and alerting system for the GCP ingestion pipeline.

## Features

- **Structured Logging**: Multi-output logging with console, file, and GCP Cloud Logging support
- **Prometheus Metrics**: Real-time metrics collection with Prometheus-compatible exposition
- **Health Monitoring**: Component health checks with automatic polling
- **Alert Management**: Rule-based alerting with multi-channel notifications
- **Dashboard Ready**: Metrics and health data formatted for visualization

## Quick Start

```python
from ingestion_pipeline.monitoring import (
    initialize_monitoring,
    get_logger,
    get_metrics,
    get_health_monitor,
    get_alert_manager,
    AlertSeverity,
    AlertRule,
    AlertChannel,
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
health.register_check("my_component", my_health_check_func)

# Configure alerts
alerts = get_alert_manager()
alerts.register_rule(AlertRule(
    name="high_error_rate",
    condition=lambda ctx: ctx.get("error_rate", 0) > 0.1,
    severity=AlertSeverity.ERROR,
    title="High Error Rate Detected",
    message_template="Error rate: {error_rate:.2%}",
    component="pipeline"
))
alerts.add_channel(AlertChannel.LOG)
```

## Architecture

```
monitoring/
├── logger.py          # Structured logging with multiple handlers
├── metrics.py         # Prometheus metrics collection
├── health.py          # Component health monitoring
├── alerts.py          # Rule-based alerting system
└── __init__.py        # Public API and initialization
```

## Components

### 1. Structured Logging (`logger.py`)

#### Features
- Multiple output handlers (console, file, GCP Cloud Logging)
- Structured log format with context propagation
- Runtime log level adjustment
- Audit logging for security events
- Component-specific loggers

#### Usage

```python
from ingestion_pipeline.monitoring import get_logger

# Get logger for component
logger = get_logger("api_client", project_id="my-project")

# Log with context
logger.info(
    "resource_fetched",
    resource_id="vm-123",
    duration_ms=45.2,
    status="success"
)

# Audit logging
from ingestion_pipeline.monitoring import get_pipeline_logger

logger_manager = get_pipeline_logger()
logger_manager.audit_log(
    "user_access",
    user="admin",
    resource="vm-123",
    action="read"
)
```

#### Configuration

Environment variables:
```bash
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=./logs                    # Log file directory
LOG_CONSOLE=true                  # Enable console output
LOG_FILE=true                     # Enable file output
LOG_GCP=false                     # Enable GCP Cloud Logging
LOG_JSON=false                    # Use JSON format
```

### 2. Metrics Collection (`metrics.py`)

#### Features
- Prometheus-compatible metrics exposition
- Counter, Gauge, and Histogram metrics
- Context managers for automatic timing
- Thread-safe metric updates
- Metric snapshots for reporting

#### Usage

```python
from ingestion_pipeline.monitoring import get_metrics

metrics = get_metrics()

# Track message processing
with metrics.track_processing("compute"):
    # Process message
    result = process_message(msg)

# Track API calls
with metrics.track_api_call("compute", "list_instances"):
    instances = api.list_instances()

# Track transformations
with metrics.track_transformation("VirtualMachine"):
    transformed = transform_vm(data)

# Track Neo4j operations
with metrics.track_neo4j_operation("batch_write"):
    writer.write_nodes(nodes)

# Manual metric updates
metrics.increment_messages_processed("compute", count=10)
metrics.record_processing_time("compute", duration_ms=125.5)

# Get metrics snapshot
snapshot = metrics.get_snapshot()
print(f"Processed: {snapshot.messages_processed}")
print(f"Failed: {snapshot.messages_failed}")
print(f"Avg processing time: {snapshot.avg_processing_time_ms}ms")

# Get Prometheus metrics
prometheus_data = metrics.get_prometheus_metrics()
```

#### Available Metrics

**Counters:**
- `{namespace}_messages_total{resource_type, status}` - Total messages processed
- `{namespace}_api_calls_total{service, method, status}` - Total API calls
- `{namespace}_transformations_total{resource_type, status}` - Total transformations
- `{namespace}_neo4j_operations_total{operation_type, status}` - Total Neo4j operations

**Gauges:**
- `{namespace}_active_subscriptions` - Active Pub/Sub subscriptions
- `{namespace}_active_workers` - Active processing workers
- `{namespace}_queue_size{queue_name}` - Message queue sizes
- `{namespace}_neo4j_connections` - Active Neo4j connections

**Histograms:**
- `{namespace}_processing_duration_seconds{resource_type}` - Processing duration
- `{namespace}_api_latency_seconds{service, method}` - API call latency
- `{namespace}_transformation_duration_seconds{resource_type}` - Transformation duration
- `{namespace}_neo4j_duration_seconds{operation_type}` - Neo4j operation duration

### 3. Health Monitoring (`health.py`)

#### Features
- Component health check registration
- Automatic health polling
- Health history tracking
- Aggregated system health status
- Utility functions for common health checks

#### Usage

```python
from ingestion_pipeline.monitoring import (
    get_health_monitor,
    HealthStatus,
    HealthCheck,
    create_ping_check,
    create_connection_check,
)
from datetime import datetime

# Get health monitor
health = get_health_monitor()

# Register health checks
def check_neo4j_health() -> HealthCheck:
    try:
        # Check Neo4j connection
        conn.check_health()
        return HealthCheck(
            component="neo4j",
            status=HealthStatus.HEALTHY,
            message="Neo4j connection healthy",
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        return HealthCheck(
            component="neo4j",
            status=HealthStatus.UNHEALTHY,
            message=f"Neo4j connection failed: {e}",
            timestamp=datetime.utcnow(),
        )

health.register_check("neo4j", check_neo4j_health)

# Or use utility functions
health.register_check(
    "pubsub",
    create_ping_check("pubsub", lambda: pubsub_client.check_health())
)

# Start health monitoring (automatic polling)
health.start()

# Get current health
system_health = health.get_health()
print(f"Overall: {system_health.overall_status.value}")
print(f"Healthy: {system_health.healthy_components}")
print(f"Degraded: {system_health.degraded_components}")
print(f"Unhealthy: {system_health.unhealthy_components}")

# Get specific component health
neo4j_health = health.get_component_health("neo4j")
if neo4j_health:
    print(f"Neo4j: {neo4j_health.status.value} - {neo4j_health.message}")

# Stop health monitoring
health.stop()
```

#### Health Status Levels

- `HEALTHY` - Component operating normally
- `DEGRADED` - Component operational but performance impacted
- `UNHEALTHY` - Component not operational
- `UNKNOWN` - Health status cannot be determined

### 4. Alert Management (`alerts.py`)

#### Features
- Rule-based alerting
- Multi-channel notifications (log, console, email, webhook, GCP)
- Alert deduplication
- Alert cooldown periods
- Alert history and acknowledgment

#### Usage

```python
from ingestion_pipeline.monitoring import (
    get_alert_manager,
    AlertRule,
    AlertSeverity,
    AlertChannel,
)

# Get alert manager
alerts = get_alert_manager()

# Register alert rules
alerts.register_rule(AlertRule(
    name="high_error_rate",
    condition=lambda ctx: ctx.get("error_rate", 0) > 0.1,
    severity=AlertSeverity.ERROR,
    title="High Error Rate Detected",
    message_template="Error rate: {error_rate:.2%}",
    component="pipeline",
    cooldown_seconds=300,  # 5 minutes
))

alerts.register_rule(AlertRule(
    name="neo4j_connection_lost",
    condition=lambda ctx: ctx.get("neo4j_connected") == False,
    severity=AlertSeverity.CRITICAL,
    title="Neo4j Connection Lost",
    message_template="Unable to connect to Neo4j database",
    component="neo4j",
))

# Configure notification channels
alerts.add_channel(AlertChannel.LOG)
alerts.add_channel(AlertChannel.CONSOLE)
alerts.add_channel(AlertChannel.EMAIL, config={
    "recipients": ["ops@example.com"]
})
alerts.add_channel(AlertChannel.WEBHOOK, config={
    "url": "https://hooks.example.com/alerts"
})

# Evaluate rules with context
context = {
    "error_rate": 0.15,
    "neo4j_connected": True,
}
triggered = alerts.evaluate_rules(context)

# Get active alerts
active = alerts.get_active_alerts()
for alert in active:
    print(f"[{alert.severity.value}] {alert.title}")

# Acknowledge alert
alerts.acknowledge_alert(alert_id)

# Resolve alert
alerts.resolve_alert(alert_id)

# Get alert statistics
stats = alerts.get_statistics()
print(f"Active alerts: {stats['active_alerts']}")
print(f"Total rules: {stats['total_rules']}")
```

#### Alert Severity Levels

- `CRITICAL` - Immediate attention required
- `ERROR` - Error requiring investigation
- `WARNING` - Warning condition
- `INFO` - Informational alert

#### Alert Channels

- `LOG` - Write to structured log
- `CONSOLE` - Print to console
- `EMAIL` - Send email notification (requires configuration)
- `WEBHOOK` - POST to webhook URL (requires configuration)
- `GCP_LOGGING` - Send to GCP Cloud Logging

## Configuration

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
LOG_CONSOLE=true
LOG_FILE=true
LOG_GCP=false
LOG_JSON=false

# Metrics
METRICS_ENABLED=true
METRICS_NAMESPACE=gcp_pipeline
METRICS_PORT=8000

# Health Monitoring
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL=60

# Alerts
ALERTS_ENABLED=true
ALERT_CHANNELS=log,console
ALERT_EMAIL_RECIPIENTS=ops@example.com
ALERT_WEBHOOK_URL=https://hooks.example.com/alerts
```

### Programmatic Configuration

```python
from ingestion_pipeline.monitoring import initialize_monitoring

monitoring = initialize_monitoring(
    # Logging
    log_level="INFO",
    log_dir="./logs",
    enable_console_log=True,
    enable_file_log=True,
    enable_gcp_log=False,
    json_format=False,
    # Metrics
    enable_prometheus=True,
    metrics_namespace="gcp_pipeline",
    # Health
    enable_health_monitoring=True,
    health_check_interval=60,
    # Alerts
    enable_alerting=True,
    alert_channels=["log", "console"],
)
```

## Integration Examples

### Pipeline Integration

```python
from ingestion_pipeline.monitoring import (
    initialize_monitoring,
    get_logger,
    get_metrics,
    get_health_monitor,
    get_alert_manager,
    AlertRule,
    AlertSeverity,
    AlertChannel,
    create_connection_check,
)

# Initialize monitoring
monitoring = initialize_monitoring(
    log_level="INFO",
    enable_prometheus=True,
    health_check_interval=30,
)

# Get monitoring instances
logger = get_logger("pipeline")
metrics = get_metrics()
health = get_health_monitor()
alerts = get_alert_manager()

# Register health checks
health.register_check(
    "neo4j",
    create_connection_check("neo4j", neo4j_conn.check_health)
)
health.register_check(
    "pubsub",
    create_connection_check("pubsub", pubsub_client.check_health)
)

# Register alert rules
alerts.register_rule(AlertRule(
    name="high_failure_rate",
    condition=lambda ctx: ctx.get("failure_rate", 0) > 0.2,
    severity=AlertSeverity.CRITICAL,
    title="Critical: High Failure Rate",
    message_template="Failure rate: {failure_rate:.2%}",
    component="pipeline",
))

alerts.add_channel(AlertChannel.LOG)
alerts.add_channel(AlertChannel.CONSOLE)

# Message processing with monitoring
async def process_message(message):
    logger.info("message_received", message_id=message.id)
    
    with metrics.track_processing(message.resource_type):
        try:
            # Process message
            result = await process_resource(message)
            
            logger.info(
                "message_processed",
                message_id=message.id,
                resource_type=message.resource_type,
                status="success"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "message_processing_failed",
                message_id=message.id,
                error=str(e),
                exc_info=True
            )
            raise

# Periodic monitoring tasks
async def monitor_pipeline():
    while True:
        # Get metrics snapshot
        snapshot = metrics.get_snapshot()
        
        # Calculate failure rate
        total = snapshot.messages_processed + snapshot.messages_failed
        failure_rate = snapshot.messages_failed / total if total > 0 else 0
        
        # Evaluate alert rules
        alerts.evaluate_rules({
            "failure_rate": failure_rate,
            "total_processed": snapshot.messages_processed,
        })
        
        # Log statistics
        logger.info(
            "pipeline_statistics",
            messages_processed=snapshot.messages_processed,
            messages_failed=snapshot.messages_failed,
            failure_rate=failure_rate,
        )
        
        await asyncio.sleep(60)
```

### Prometheus Metrics Server

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
from ingestion_pipeline.monitoring import get_metrics

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            metrics = get_metrics()
            prometheus_data = metrics.get_prometheus_metrics()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(prometheus_data)
        else:
            self.send_response(404)
            self.end_headers()

def start_metrics_server(port=8000):
    server = HTTPServer(('0.0.0.0', port), MetricsHandler)
    print(f"Metrics server listening on port {port}")
    server.serve_forever()

# Run in separate thread
import threading
metrics_thread = threading.Thread(target=start_metrics_server, daemon=True)
metrics_thread.start()
```

## Testing

```python
import pytest
from ingestion_pipeline.monitoring import (
    initialize_monitoring,
    get_logger,
    get_metrics,
    HealthStatus,
    HealthCheck,
)
from datetime import datetime

def test_logging():
    logger = get_logger("test")
    logger.info("test_message", key="value")
    # Verify log output

def test_metrics():
    metrics = get_metrics()
    
    # Track processing
    with metrics.track_processing("test"):
        pass
    
    # Get snapshot
    snapshot = metrics.get_snapshot()
    assert snapshot.messages_processed >= 1

def test_health_check():
    def check() -> HealthCheck:
        return HealthCheck(
            component="test",
            status=HealthStatus.HEALTHY,
            message="Test healthy",
            timestamp=datetime.utcnow(),
        )
    
    from ingestion_pipeline.monitoring import get_health_monitor
    health = get_health_monitor()
    health.register_check("test", check)
    
    result = health.check_component("test")
    assert result.status == HealthStatus.HEALTHY

def test_alerts():
    from ingestion_pipeline.monitoring import (
        get_alert_manager,
        AlertRule,
        AlertSeverity,
    )
    
    alerts = get_alert_manager()
    alerts.register_rule(AlertRule(
        name="test_alert",
        condition=lambda ctx: ctx.get("value", 0) > 10,
        severity=AlertSeverity.WARNING,
        title="Test Alert",
        message_template="Value: {value}",
        component="test",
    ))
    
    triggered = alerts.evaluate_rules({"value": 15})
    assert len(triggered) == 1
    assert triggered[0].severity == AlertSeverity.WARNING
```

## Best Practices

1. **Initialize Early**: Call `initialize_monitoring()` at application startup
2. **Use Context Managers**: Use `track_*()` context managers for automatic timing
3. **Structured Logging**: Use key-value pairs instead of string formatting
4. **Component Loggers**: Create separate loggers for each component
5. **Health Checks**: Register health checks for all critical dependencies
6. **Alert Thresholds**: Set appropriate thresholds to avoid alert fatigue
7. **Cooldown Periods**: Use cooldown periods to prevent alert spam
8. **Monitor Metrics**: Expose Prometheus metrics for external monitoring
9. **Audit Logging**: Use audit logging for security-sensitive operations
10. **Graceful Shutdown**: Call `shutdown_monitoring()` on application exit

## Troubleshooting

### Logs not appearing
- Check `LOG_LEVEL` environment variable
- Verify log directory permissions
- Check `LOG_CONSOLE` or `LOG_FILE` settings

### Metrics not updating
- Ensure `METRICS_ENABLED=true`
- Check Prometheus scrape configuration
- Verify metrics endpoint is accessible

### Health checks failing
- Check component connectivity
- Review health check implementation
- Verify health check interval is appropriate

### Alerts not firing
- Verify alert rules are registered
- Check alert channels are configured
- Review cooldown periods
- Check alert condition logic

## Performance Considerations

- **Logging**: Use appropriate log levels to reduce I/O
- **Metrics**: Metrics collection has minimal overhead (~1-2%)
- **Health Checks**: Set reasonable check intervals (60-300s)
- **Alerts**: Use cooldown periods to prevent resource exhaustion

## License

Part of the GCP Digital Twin Agent System project.

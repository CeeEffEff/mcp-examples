"""
Smoke test for monitoring system components.

Verifies basic functionality of logger, metrics, health, and alerts.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ingestion_pipeline.monitoring import (
    initialize_monitoring,
    get_logger,
    get_metrics,
    get_health_monitor,
    get_alert_manager,
    get_monitoring_status,
    shutdown_monitoring,
    HealthStatus,
    HealthCheck,
    AlertSeverity,
    AlertChannel,
    AlertRule,
)
from datetime import datetime


def test_logger():
    """Test basic logging functionality."""
    print("Testing logger...")
    
    logger = get_logger("test_component")
    logger.info("test_message", test_key="test_value")
    logger.debug("debug_message", detail="extra detail")
    logger.warning("warning_message", reason="test warning")
    
    print("✓ Logger test passed")


def test_metrics():
    """Test metrics collection."""
    print("Testing metrics...")
    
    metrics = get_metrics()
    
    # Test message processing counters
    metrics.increment_messages_processed("compute")
    metrics.increment_messages_processed("compute")
    metrics.increment_messages_failed("compute")
    
    # Test API counters
    metrics.increment_api_calls("compute", "list_instances", success=True)
    metrics.increment_api_calls("compute", "list_instances", success=False)
    
    # Test transformation counters
    metrics.increment_transformations("compute", success=True)
    
    # Test Neo4j counters
    metrics.increment_neo4j_operations("batch_write", success=True)
    
    # Test gauges
    metrics.set_active_subscriptions(3)
    metrics.set_active_workers(5)
    metrics.set_queue_size("compute", 10)
    metrics.set_neo4j_connections(2)
    
    # Test timing metrics
    metrics.record_processing_time("compute", 123.4)
    metrics.record_api_latency("compute", "list_instances", 45.2)
    metrics.record_transformation_time("compute", 12.3)
    metrics.record_neo4j_duration("batch_write", 78.9)
    
    # Get snapshot
    snapshot = metrics.get_snapshot()
    
    assert snapshot.messages_processed == 2
    assert snapshot.messages_failed == 1
    assert snapshot.api_calls == 1
    assert snapshot.api_errors == 1
    assert snapshot.transformations == 1
    assert snapshot.neo4j_writes == 1
    
    print("✓ Metrics test passed")


def test_health_monitor():
    """Test health monitoring."""
    print("Testing health monitor...")
    
    health = get_health_monitor()
    
    # Register test health checks with proper HealthCheck return types
    def healthy_check():
        return HealthCheck(
            component="healthy_component",
            status=HealthStatus.HEALTHY,
            message="All good",
            timestamp=datetime.utcnow(),
        )
    
    def unhealthy_check():
        return HealthCheck(
            component="unhealthy_component",
            status=HealthStatus.UNHEALTHY,
            message="Something wrong",
            timestamp=datetime.utcnow(),
        )
    
    health.register_check("healthy_component", healthy_check)
    health.register_check("unhealthy_component", unhealthy_check)
    
    # Manually trigger health checks
    health.check_all()
    
    # Get current health
    system_health = health.get_health()
    
    # With 1 healthy and 1 unhealthy, overall status is UNHEALTHY
    # (any unhealthy component makes the whole system unhealthy)
    assert system_health.overall_status == HealthStatus.UNHEALTHY
    assert system_health.healthy_components == 1
    assert system_health.unhealthy_components == 1
    
    print("✓ Health monitor test passed")


def test_alert_manager():
    """Test alert management."""
    print("Testing alert manager...")
    
    alerts = get_alert_manager()
    
    # Add channels
    alerts.add_channel(AlertChannel.LOG)
    alerts.add_channel(AlertChannel.CONSOLE)
    
    # Create and register test rule
    test_rule = AlertRule(
        name="test_rule",
        condition=lambda ctx: ctx.get("trigger", False),
        severity=AlertSeverity.WARNING,
        title="Test Alert",
        message_template="This is a test alert: {trigger}",
        component="test_component",
    )
    
    alerts.register_rule(test_rule)
    
    # Evaluate rules with context that triggers the alert
    triggered = alerts.evaluate_rules({"trigger": True})
    assert len(triggered) > 0
    
    # Check active alerts
    active_alerts = alerts.get_active_alerts()
    assert len(active_alerts) > 0
    
    # Get statistics
    stats = alerts.get_statistics()
    assert stats["active_alerts"] > 0
    
    print("✓ Alert manager test passed")


def test_monitoring_integration():
    """Test full monitoring system integration."""
    print("Testing monitoring integration...")
    
    # Get monitoring status
    status = get_monitoring_status()
    
    assert status["initialized"] == True
    assert status["logger"] is not None
    assert status["metrics"] is not None
    assert status["health"] is not None
    assert status["alerts"] is not None
    
    print("✓ Monitoring integration test passed")


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("Running monitoring system smoke tests")
    print("=" * 60)
    
    # Create temporary log directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize monitoring with test configuration
        initialize_monitoring(
            log_level="DEBUG",
            log_dir=temp_dir,
            enable_console_log=True,
            enable_file_log=True,
            enable_gcp_log=False,
            json_format=False,
            enable_prometheus=True,
            enable_health_monitoring=True,
            health_check_interval=60,
            enable_alerting=True,
            alert_channels=[AlertChannel.LOG, AlertChannel.CONSOLE],
        )
        
        # Run tests
        test_logger()
        test_metrics()
        test_health_monitor()
        test_alert_manager()
        test_monitoring_integration()
        
        print("\n" + "=" * 60)
        print("✓ All smoke tests passed!")
        print("=" * 60)
        
        # Display monitoring status
        print("\nMonitoring Status:")
        status = get_monitoring_status()
        print(f"  Initialized: {status['initialized']}")
        print(f"  Logger: {status['logger'] is not None}")
        print(f"  Metrics: {status['metrics'] is not None}")
        print(f"  Health: {status['health'] is not None}")
        print(f"  Alerts: {status['alerts'] is not None}")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Cleanup
        shutdown_monitoring(timeout=5)
        
        # Remove temp directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())

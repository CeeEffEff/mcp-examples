"""
Alert Management System

Provides alerting functionality for critical pipeline events:
- Alert rule configuration
- Multi-channel notification (log, email, webhook, GCP)
- Alert aggregation and deduplication
- Alert history and tracking
- Severity-based routing
"""

import time
import threading
import json
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

import structlog


logger = structlog.get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class AlertStatus(Enum):
    """Alert status."""
    
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """Alert instance."""
    
    id: str
    rule_name: str
    severity: AlertSeverity
    title: str
    message: str
    component: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "metadata": self.metadata,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
        }


@dataclass
class AlertRule:
    """Alert rule configuration."""
    
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    title: str
    message_template: str
    component: str
    cooldown_seconds: int = 300  # 5 minutes
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertChannel(Enum):
    """Alert notification channels."""
    
    LOG = "log"
    EMAIL = "email"
    WEBHOOK = "webhook"
    GCP_LOGGING = "gcp_logging"
    CONSOLE = "console"


class AlertManager:
    """
    Centralized alert management for the ingestion pipeline.
    
    Features:
    - Rule-based alerting
    - Multi-channel notifications
    - Alert deduplication
    - Alert history and tracking
    - Severity-based routing
    - Alert acknowledgment and resolution
    
    Example:
        # Initialize alert manager
        alert_mgr = AlertManager()
        
        # Register alert rules
        alert_mgr.register_rule(AlertRule(
            name="high_error_rate",
            condition=lambda ctx: ctx.get("error_rate", 0) > 0.1,
            severity=AlertSeverity.ERROR,
            title="High Error Rate Detected",
            message_template="Error rate: {error_rate:.2%}",
            component="pipeline"
        ))
        
        # Configure channels
        alert_mgr.add_channel(AlertChannel.LOG)
        alert_mgr.add_channel(AlertChannel.EMAIL, config={
            "recipients": ["ops@example.com"]
        })
        
        # Evaluate rules
        alert_mgr.evaluate_rules({"error_rate": 0.15})
        
        # Get active alerts
        alerts = alert_mgr.get_active_alerts()
    """
    
    def __init__(
        self,
        enable_deduplication: bool = True,
        deduplication_window: int = 300,  # 5 minutes
        max_history: int = 1000,
    ):
        """
        Initialize alert manager.
        
        Args:
            enable_deduplication: Enable alert deduplication
            deduplication_window: Deduplication window in seconds
            max_history: Maximum number of alerts to keep in history
        """
        self.enable_deduplication = enable_deduplication
        self.deduplication_window = deduplication_window
        self.max_history = max_history
        
        # Alert rules
        self._rules: Dict[str, AlertRule] = {}
        
        # Active alerts
        self._active_alerts: Dict[str, Alert] = {}
        
        # Alert history
        self._alert_history: List[Alert] = []
        
        # Notification channels
        self._channels: Dict[AlertChannel, Optional[Dict[str, Any]]] = {}
        
        # Cooldown tracking (rule_name -> last_alert_time)
        self._cooldowns: Dict[str, datetime] = {}
        
        # Deduplication tracking (alert_fingerprint -> alert_id)
        self._fingerprints: Dict[str, str] = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info(
            "alert_manager_initialized",
            enable_deduplication=enable_deduplication,
            deduplication_window=deduplication_window,
        )
    
    def register_rule(self, rule: AlertRule) -> None:
        """
        Register an alert rule.
        
        Args:
            rule: AlertRule to register
        """
        with self._lock:
            self._rules[rule.name] = rule
        
        logger.info("alert_rule_registered", rule_name=rule.name, severity=rule.severity.value)
    
    def unregister_rule(self, rule_name: str) -> bool:
        """
        Unregister an alert rule.
        
        Args:
            rule_name: Name of rule to remove
            
        Returns:
            True if rule was found and removed
        """
        with self._lock:
            if rule_name in self._rules:
                del self._rules[rule_name]
                logger.info("alert_rule_unregistered", rule_name=rule_name)
                return True
        return False
    
    def add_channel(
        self,
        channel: AlertChannel,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a notification channel.
        
        Args:
            channel: Channel type
            config: Channel-specific configuration
        """
        with self._lock:
            self._channels[channel] = config or {}
        
        logger.info("alert_channel_added", channel=channel.value)
    
    def remove_channel(self, channel: AlertChannel) -> bool:
        """
        Remove a notification channel.
        
        Args:
            channel: Channel type
            
        Returns:
            True if channel was found and removed
        """
        with self._lock:
            if channel in self._channels:
                del self._channels[channel]
                logger.info("alert_channel_removed", channel=channel.value)
                return True
        return False
    
    def evaluate_rules(self, context: Dict[str, Any]) -> List[Alert]:
        """
        Evaluate all alert rules against provided context.
        
        Args:
            context: Context dictionary for rule evaluation
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts: List[Alert] = []
        
        with self._lock:
            rules = list(self._rules.values())
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            # Check cooldown
            if rule.name in self._cooldowns:
                last_alert = self._cooldowns[rule.name]
                cooldown_until = last_alert + timedelta(seconds=rule.cooldown_seconds)
                
                if datetime.utcnow() < cooldown_until:
                    logger.debug(
                        "alert_rule_in_cooldown",
                        rule_name=rule.name,
                        cooldown_until=cooldown_until.isoformat(),
                    )
                    continue
            
            # Evaluate condition
            try:
                if rule.condition(context):
                    alert = self._create_alert(rule, context)
                    triggered_alerts.append(alert)
                    
                    # Update cooldown
                    with self._lock:
                        self._cooldowns[rule.name] = datetime.utcnow()
            except Exception as e:
                logger.error(
                    "alert_rule_evaluation_failed",
                    rule_name=rule.name,
                    error=str(e),
                    exc_info=True,
                )
        
        return triggered_alerts
    
    def _create_alert(self, rule: AlertRule, context: Dict[str, Any]) -> Alert:
        """Create an alert from a rule."""
        # Format message
        try:
            message = rule.message_template.format(**context)
        except KeyError:
            message = rule.message_template
        
        # Generate alert ID
        timestamp = datetime.utcnow()
        alert_id = f"{rule.name}_{timestamp.timestamp()}"
        
        # Check for duplicate
        if self.enable_deduplication:
            fingerprint = self._generate_fingerprint(rule, context)
            
            with self._lock:
                if fingerprint in self._fingerprints:
                    existing_id = self._fingerprints[fingerprint]
                    if existing_id in self._active_alerts:
                        logger.debug(
                            "alert_deduplicated",
                            rule_name=rule.name,
                            existing_id=existing_id,
                        )
                        return self._active_alerts[existing_id]
        
        # Create alert
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            severity=rule.severity,
            title=rule.title,
            message=message,
            component=rule.component,
            timestamp=timestamp,
            metadata={**rule.metadata, **context},
        )
        
        # Store alert
        with self._lock:
            self._active_alerts[alert_id] = alert
            self._alert_history.append(alert)
            
            if len(self._alert_history) > self.max_history:
                self._alert_history.pop(0)
            
            # Store fingerprint
            if self.enable_deduplication:
                fingerprint = self._generate_fingerprint(rule, context)
                self._fingerprints[fingerprint] = alert_id
        
        # Send notifications
        self._notify(alert)
        
        logger.info(
            "alert_created",
            alert_id=alert_id,
            rule_name=rule.name,
            severity=rule.severity.value,
        )
        
        return alert
    
    def _generate_fingerprint(self, rule: AlertRule, context: Dict[str, Any]) -> str:
        """Generate fingerprint for deduplication."""
        # Simple fingerprint: rule_name + component
        # Could be extended to include specific context values
        return f"{rule.name}:{rule.component}"
    
    def _notify(self, alert: Alert) -> None:
        """Send alert notifications to all configured channels."""
        with self._lock:
            channels = list(self._channels.items())
        
        for channel, config in channels:
            try:
                if channel == AlertChannel.LOG:
                    self._notify_log(alert)
                elif channel == AlertChannel.CONSOLE:
                    self._notify_console(alert)
                elif channel == AlertChannel.EMAIL:
                    self._notify_email(alert, config)
                elif channel == AlertChannel.WEBHOOK:
                    self._notify_webhook(alert, config)
                elif channel == AlertChannel.GCP_LOGGING:
                    self._notify_gcp_logging(alert)
            except Exception as e:
                logger.error(
                    "alert_notification_failed",
                    channel=channel.value,
                    alert_id=alert.id,
                    error=str(e),
                    exc_info=True,
                )
    
    def _notify_log(self, alert: Alert) -> None:
        """Send alert to structured log."""
        log_func = logger.critical
        if alert.severity == AlertSeverity.ERROR:
            log_func = logger.error
        elif alert.severity == AlertSeverity.WARNING:
            log_func = logger.warning
        elif alert.severity == AlertSeverity.INFO:
            log_func = logger.info
        
        log_func(
            "alert_triggered",
            alert_id=alert.id,
            rule_name=alert.rule_name,
            severity=alert.severity.value,
            title=alert.title,
            message=alert.message,
            component=alert.component,
        )
    
    def _notify_console(self, alert: Alert) -> None:
        """Print alert to console."""
        severity_emoji = {
            AlertSeverity.CRITICAL: "🔴",
            AlertSeverity.ERROR: "🟠",
            AlertSeverity.WARNING: "🟡",
            AlertSeverity.INFO: "🔵",
        }
        
        emoji = severity_emoji.get(alert.severity, "⚪")
        print(f"\n{emoji} ALERT [{alert.severity.value.upper()}] {emoji}")
        print(f"Title: {alert.title}")
        print(f"Component: {alert.component}")
        print(f"Message: {alert.message}")
        print(f"Time: {alert.timestamp.isoformat()}")
        print(f"Alert ID: {alert.id}\n")
    
    def _notify_email(self, alert: Alert, config: Dict[str, Any]) -> None:
        """Send alert via email (placeholder)."""
        # This would integrate with an email service
        # For now, just log the intent
        recipients = config.get("recipients", [])
        logger.info(
            "alert_email_sent",
            alert_id=alert.id,
            recipients=recipients,
            subject=f"[{alert.severity.value.upper()}] {alert.title}",
        )
    
    def _notify_webhook(self, alert: Alert, config: Dict[str, Any]) -> None:
        """Send alert to webhook (placeholder)."""
        # This would make an HTTP POST request
        webhook_url = config.get("url")
        logger.info(
            "alert_webhook_sent",
            alert_id=alert.id,
            webhook_url=webhook_url,
        )
    
    def _notify_gcp_logging(self, alert: Alert) -> None:
        """Send alert to GCP Cloud Logging."""
        try:
            from google.cloud import logging as gcp_logging
            
            client = gcp_logging.Client()
            log_logger = client.logger("pipeline-alerts")
            
            severity_map = {
                AlertSeverity.CRITICAL: "CRITICAL",
                AlertSeverity.ERROR: "ERROR",
                AlertSeverity.WARNING: "WARNING",
                AlertSeverity.INFO: "INFO",
            }
            
            log_logger.log_struct(
                alert.to_dict(),
                severity=severity_map.get(alert.severity, "DEFAULT"),
            )
        except Exception as e:
            logger.warning("gcp_logging_alert_failed", error=str(e))
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an active alert.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            True if alert was found and acknowledged
        """
        with self._lock:
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                
                logger.info("alert_acknowledged", alert_id=alert_id)
                return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an active alert.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            True if alert was found and resolved
        """
        with self._lock:
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                
                # Remove from active alerts
                del self._active_alerts[alert_id]
                
                # Remove fingerprint
                if self.enable_deduplication:
                    fingerprint = f"{alert.rule_name}:{alert.component}"
                    self._fingerprints.pop(fingerprint, None)
                
                logger.info("alert_resolved", alert_id=alert_id)
                return True
        return False
    
    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        component: Optional[str] = None,
    ) -> List[Alert]:
        """
        Get active alerts.
        
        Args:
            severity: Filter by severity
            component: Filter by component
            
        Returns:
            List of active alerts
        """
        with self._lock:
            alerts = list(self._active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if component:
            alerts = [a for a in alerts if a.component == component]
        
        return alerts
    
    def get_alert_history(
        self,
        since: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
        component: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Alert]:
        """
        Get alert history.
        
        Args:
            since: Only return alerts after this timestamp
            severity: Filter by severity
            component: Filter by component
            limit: Maximum number of alerts to return
            
        Returns:
            List of historical alerts
        """
        with self._lock:
            history = list(self._alert_history)
        
        if since:
            history = [a for a in history if a.timestamp >= since]
        
        if severity:
            history = [a for a in history if a.severity == severity]
        
        if component:
            history = [a for a in history if a.component == component]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        with self._lock:
            active = len(self._active_alerts)
            
            # Count by severity
            severity_counts = defaultdict(int)
            for alert in self._active_alerts.values():
                severity_counts[alert.severity.value] += 1
            
            # Count by component
            component_counts = defaultdict(int)
            for alert in self._active_alerts.values():
                component_counts[alert.component] += 1
        
        return {
            "active_alerts": active,
            "total_rules": len(self._rules),
            "active_channels": len(self._channels),
            "severity_breakdown": dict(severity_counts),
            "component_breakdown": dict(component_counts),
            "history_size": len(self._alert_history),
        }


# Global alert manager instance
_alert_manager_instance: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """
    Get the global alert manager instance.
    
    Returns:
        AlertManager singleton instance
    """
    global _alert_manager_instance
    
    if _alert_manager_instance is None:
        _alert_manager_instance = AlertManager()
    
    return _alert_manager_instance


def initialize_alert_manager(**kwargs: Any) -> AlertManager:
    """
    Initialize the global alert manager with custom configuration.
    
    Args:
        **kwargs: Configuration options for AlertManager
        
    Returns:
        Configured AlertManager instance
    """
    global _alert_manager_instance
    _alert_manager_instance = AlertManager(**kwargs)
    return _alert_manager_instance

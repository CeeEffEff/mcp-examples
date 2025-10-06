"""
Health Monitoring System

Provides health checking and status monitoring for pipeline components:
- Component health status tracking
- Dependency health checking
- System resource monitoring
- Health check endpoints
- Aggregated health status
"""

import time
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

import structlog


logger = structlog.get_logger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check result."""
    
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime
    latency_ms: float = 0.0
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "latency_ms": round(self.latency_ms, 2),
            "details": self.details or {},
        }


@dataclass
class SystemHealth:
    """Aggregated system health status."""
    
    overall_status: HealthStatus
    components: List[HealthCheck]
    timestamp: datetime
    
    @property
    def healthy_components(self) -> int:
        """Count of healthy components."""
        return sum(1 for c in self.components if c.status == HealthStatus.HEALTHY)
    
    @property
    def degraded_components(self) -> int:
        """Count of degraded components."""
        return sum(1 for c in self.components if c.status == HealthStatus.DEGRADED)
    
    @property
    def unhealthy_components(self) -> int:
        """Count of unhealthy components."""
        return sum(1 for c in self.components if c.status == HealthStatus.UNHEALTHY)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_status": self.overall_status.value,
            "timestamp": self.timestamp.isoformat(),
            "summary": {
                "total_components": len(self.components),
                "healthy": self.healthy_components,
                "degraded": self.degraded_components,
                "unhealthy": self.unhealthy_components,
            },
            "components": [c.to_dict() for c in self.components],
        }


class HealthMonitor:
    """
    Centralized health monitoring for pipeline components.
    
    Features:
    - Component health check registration
    - Automatic health polling
    - Aggregated health status
    - Configurable check intervals
    - Health history tracking
    
    Example:
        # Initialize monitor
        monitor = HealthMonitor(check_interval=30)
        
        # Register health checks
        monitor.register_check("pubsub", check_pubsub_health)
        monitor.register_check("neo4j", check_neo4j_health)
        monitor.register_check("api_client", check_api_health)
        
        # Start monitoring
        monitor.start()
        
        # Get current health
        health = monitor.get_health()
        
        # Stop monitoring
        monitor.stop()
    """
    
    def __init__(
        self,
        check_interval: int = 60,
        history_size: int = 100,
    ):
        """
        Initialize health monitor.
        
        Args:
            check_interval: Interval between health checks in seconds
            history_size: Number of health check results to retain
        """
        self.check_interval = check_interval
        self.history_size = history_size
        
        # Health check registry
        self._checks: Dict[str, Callable[[], HealthCheck]] = {}
        self._last_results: Dict[str, HealthCheck] = {}
        self._history: List[SystemHealth] = []
        
        # Monitoring thread
        self._is_running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        logger.info(
            "health_monitor_initialized",
            check_interval=check_interval,
            history_size=history_size,
        )
    
    def register_check(
        self,
        component: str,
        check_func: Callable[[], HealthCheck],
    ) -> None:
        """
        Register a health check for a component.
        
        Args:
            component: Component name
            check_func: Function that returns HealthCheck
        """
        with self._lock:
            self._checks[component] = check_func
        
        logger.info("health_check_registered", component=component)
    
    def unregister_check(self, component: str) -> bool:
        """
        Unregister a health check.
        
        Args:
            component: Component name
            
        Returns:
            True if check was found and removed
        """
        with self._lock:
            if component in self._checks:
                del self._checks[component]
                logger.info("health_check_unregistered", component=component)
                return True
        return False
    
    def check_component(self, component: str) -> Optional[HealthCheck]:
        """
        Run health check for a specific component.
        
        Args:
            component: Component name
            
        Returns:
            HealthCheck result or None if component not registered
        """
        with self._lock:
            check_func = self._checks.get(component)
        
        if not check_func:
            return None
        
        start_time = time.time()
        
        try:
            result = check_func()
            result.latency_ms = (time.time() - start_time) * 1000
            
            with self._lock:
                self._last_results[component] = result
            
            return result
            
        except Exception as e:
            logger.error(
                "health_check_failed",
                component=component,
                error=str(e),
                exc_info=True,
            )
            
            result = HealthCheck(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {e}",
                timestamp=datetime.utcnow(),
                latency_ms=(time.time() - start_time) * 1000,
            )
            
            with self._lock:
                self._last_results[component] = result
            
            return result
    
    def check_all(self) -> SystemHealth:
        """
        Run all registered health checks.
        
        Returns:
            SystemHealth with aggregated results
        """
        components: List[str] = []
        with self._lock:
            components = list(self._checks.keys())
        
        results: List[HealthCheck] = []
        
        for component in components:
            result = self.check_component(component)
            if result:
                results.append(result)
        
        # Determine overall status
        if not results:
            overall_status = HealthStatus.UNKNOWN
        elif all(r.status == HealthStatus.HEALTHY for r in results):
            overall_status = HealthStatus.HEALTHY
        elif any(r.status == HealthStatus.UNHEALTHY for r in results):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED
        
        system_health = SystemHealth(
            overall_status=overall_status,
            components=results,
            timestamp=datetime.utcnow(),
        )
        
        # Add to history
        with self._lock:
            self._history.append(system_health)
            if len(self._history) > self.history_size:
                self._history.pop(0)
        
        logger.info(
            "health_check_completed",
            overall_status=overall_status.value,
            healthy=system_health.healthy_components,
            degraded=system_health.degraded_components,
            unhealthy=system_health.unhealthy_components,
        )
        
        return system_health
    
    def get_health(self) -> SystemHealth:
        """
        Get current system health.
        
        Returns:
            Most recent SystemHealth or new check if none cached
        """
        with self._lock:
            if self._history:
                return self._history[-1]
        
        # No cached results, run checks now
        return self.check_all()
    
    def get_component_health(self, component: str) -> Optional[HealthCheck]:
        """
        Get health status for a specific component.
        
        Args:
            component: Component name
            
        Returns:
            HealthCheck result or None if not found
        """
        with self._lock:
            return self._last_results.get(component)
    
    def get_history(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[SystemHealth]:
        """
        Get health check history.
        
        Args:
            since: Only return results after this timestamp
            limit: Maximum number of results to return
            
        Returns:
            List of SystemHealth results
        """
        with self._lock:
            history = list(self._history)
        
        if since:
            history = [h for h in history if h.timestamp >= since]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        logger.info("health_monitor_started")
        
        while self._is_running:
            try:
                self.check_all()
            except Exception as e:
                logger.error(
                    "health_monitor_error",
                    error=str(e),
                    exc_info=True,
                )
            
            # Sleep in small intervals to allow quick shutdown
            for _ in range(self.check_interval):
                if not self._is_running:
                    break
                time.sleep(1)
        
        logger.info("health_monitor_stopped")
    
    def start(self) -> None:
        """Start background health monitoring."""
        if self._is_running:
            logger.warning("health_monitor_already_running")
            return
        
        self._is_running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="health-monitor",
        )
        self._monitor_thread.start()
        
        logger.info("health_monitor_thread_started")
    
    def stop(self, timeout: int = 10) -> None:
        """
        Stop background health monitoring.
        
        Args:
            timeout: Maximum time to wait for thread to stop
        """
        if not self._is_running:
            logger.warning("health_monitor_not_running")
            return
        
        logger.info("stopping_health_monitor")
        
        self._is_running = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=timeout)
            if self._monitor_thread.is_alive():
                logger.warning("health_monitor_thread_did_not_stop")
        
        logger.info("health_monitor_stopped")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


# Utility functions for creating health checks

def create_ping_check(
    component: str,
    ping_func: Callable[[], bool],
    timeout: float = 5.0,
) -> Callable[[], HealthCheck]:
    """
    Create a simple ping-style health check.
    
    Args:
        component: Component name
        ping_func: Function that returns True if healthy
        timeout: Timeout for ping in seconds
        
    Returns:
        Health check function
    """
    def check() -> HealthCheck:
        start_time = time.time()
        
        try:
            is_healthy = ping_func()
            latency_ms = (time.time() - start_time) * 1000
            
            if is_healthy:
                return HealthCheck(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    message=f"{component} is responding",
                    timestamp=datetime.utcnow(),
                    latency_ms=latency_ms,
                )
            else:
                return HealthCheck(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    message=f"{component} ping failed",
                    timestamp=datetime.utcnow(),
                    latency_ms=latency_ms,
                )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"{component} check error: {e}",
                timestamp=datetime.utcnow(),
                latency_ms=latency_ms,
            )
    
    return check


def create_connection_check(
    component: str,
    check_func: Callable[[], Dict[str, Any]],
) -> Callable[[], HealthCheck]:
    """
    Create a connection-based health check with details.
    
    Args:
        component: Component name
        check_func: Function that returns status dict with keys:
            - connected: bool
            - message: str
            - details: Optional[Dict]
            
    Returns:
        Health check function
    """
    def check() -> HealthCheck:
        start_time = time.time()
        
        try:
            result = check_func()
            latency_ms = (time.time() - start_time) * 1000
            
            connected = result.get("connected", False)
            message = result.get("message", "Unknown status")
            details = result.get("details")
            
            status = HealthStatus.HEALTHY if connected else HealthStatus.UNHEALTHY
            
            return HealthCheck(
                component=component,
                status=status,
                message=message,
                timestamp=datetime.utcnow(),
                latency_ms=latency_ms,
                details=details,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Connection check failed: {e}",
                timestamp=datetime.utcnow(),
                latency_ms=latency_ms,
            )
    
    return check


def create_threshold_check(
    component: str,
    metric_func: Callable[[], float],
    threshold: float,
    comparison: str = "less_than",
    metric_name: str = "metric",
) -> Callable[[], HealthCheck]:
    """
    Create a threshold-based health check.
    
    Args:
        component: Component name
        metric_func: Function that returns a numeric metric
        threshold: Threshold value
        comparison: Comparison type ('less_than', 'greater_than', 'equal_to')
        metric_name: Name of the metric for messages
        
    Returns:
        Health check function
    """
    def check() -> HealthCheck:
        start_time = time.time()
        
        try:
            value = metric_func()
            latency_ms = (time.time() - start_time) * 1000
            
            # Determine health based on comparison
            if comparison == "less_than":
                is_healthy = value < threshold
                op = "<"
            elif comparison == "greater_than":
                is_healthy = value > threshold
                op = ">"
            elif comparison == "equal_to":
                is_healthy = value == threshold
                op = "=="
            else:
                raise ValueError(f"Unknown comparison: {comparison}")
            
            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.DEGRADED
            message = f"{metric_name} = {value} {op} {threshold}"
            
            return HealthCheck(
                component=component,
                status=status,
                message=message,
                timestamp=datetime.utcnow(),
                latency_ms=latency_ms,
                details={
                    "metric_name": metric_name,
                    "value": value,
                    "threshold": threshold,
                    "comparison": comparison,
                },
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Threshold check failed: {e}",
                timestamp=datetime.utcnow(),
                latency_ms=latency_ms,
            )
    
    return check


# Global health monitor instance
_monitor_instance: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """
    Get the global health monitor instance.
    
    Returns:
        HealthMonitor singleton instance
    """
    global _monitor_instance
    
    if _monitor_instance is None:
        _monitor_instance = HealthMonitor()
    
    return _monitor_instance


def initialize_health_monitor(**kwargs: Any) -> HealthMonitor:
    """
    Initialize the global health monitor with custom configuration.
    
    Args:
        **kwargs: Configuration options for HealthMonitor
        
    Returns:
        Configured HealthMonitor instance
    """
    global _monitor_instance
    _monitor_instance = HealthMonitor(**kwargs)
    return _monitor_instance

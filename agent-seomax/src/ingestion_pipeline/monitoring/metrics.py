"""
Metrics Collection and Prometheus Integration

Provides comprehensive metrics collection for pipeline monitoring:
- Prometheus metrics exposition
- Counter, Gauge, Histogram, and Summary metrics
- Pipeline-specific metrics (throughput, latency, error rates)
- Component-level metrics tracking
- Health status metrics
"""

import time
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

import structlog


logger = structlog.get_logger(__name__)


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time."""
    
    timestamp: datetime
    messages_processed: int = 0
    messages_failed: int = 0
    api_calls: int = 0
    api_errors: int = 0
    transformations: int = 0
    transformation_errors: int = 0
    neo4j_writes: int = 0
    neo4j_errors: int = 0
    avg_processing_time_ms: float = 0.0
    avg_api_latency_ms: float = 0.0
    avg_transformation_time_ms: float = 0.0
    avg_neo4j_write_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "messages_processed": self.messages_processed,
            "messages_failed": self.messages_failed,
            "api_calls": self.api_calls,
            "api_errors": self.api_errors,
            "transformations": self.transformations,
            "transformation_errors": self.transformation_errors,
            "neo4j_writes": self.neo4j_writes,
            "neo4j_errors": self.neo4j_errors,
            "avg_processing_time_ms": round(self.avg_processing_time_ms, 2),
            "avg_api_latency_ms": round(self.avg_api_latency_ms, 2),
            "avg_transformation_time_ms": round(self.avg_transformation_time_ms, 2),
            "avg_neo4j_write_time_ms": round(self.avg_neo4j_write_time_ms, 2),
        }


class PipelineMetrics:
    """
    Centralized metrics collection for the ingestion pipeline.
    
    Features:
    - Prometheus-compatible metrics exposition
    - Pipeline throughput and latency tracking
    - Error rate monitoring
    - Component-specific metrics
    - Resource utilization tracking
    - Custom metric registration
    
    Example:
        # Initialize metrics
        metrics = PipelineMetrics(namespace="gcp_pipeline")
        
        # Track message processing
        with metrics.track_processing("compute"):
            # Process message
            pass
        
        # Increment counters
        metrics.increment_api_calls("compute", "list_instances")
        
        # Record latency
        metrics.record_api_latency("compute", "list_instances", 45.2)
        
        # Get Prometheus metrics
        metrics_text = metrics.get_prometheus_metrics()
    """
    
    def __init__(
        self,
        namespace: str = "pipeline",
        enable_prometheus: bool = True,
        registry: Optional[CollectorRegistry] = None,
    ):
        """
        Initialize pipeline metrics.
        
        Args:
            namespace: Namespace prefix for all metrics
            enable_prometheus: Enable Prometheus metrics exposition
            registry: Custom Prometheus registry (creates new if None)
        """
        self.namespace = namespace
        self.enable_prometheus = enable_prometheus
        self.registry = registry or CollectorRegistry()
        
        # Thread-safe counters
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._timings: Dict[str, List[float]] = defaultdict(list)
        
        # Initialize Prometheus metrics
        if self.enable_prometheus:
            self._init_prometheus_metrics()
        
        logger.info(
            "metrics_initialized",
            namespace=namespace,
            enable_prometheus=enable_prometheus,
        )
    
    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus metric collectors."""
        prefix = f"{self.namespace}_"
        
        # Counters
        self.prom_messages_total = Counter(
            f"{prefix}messages_total",
            "Total messages received",
            ["resource_type", "status"],
            registry=self.registry,
        )
        
        self.prom_api_calls_total = Counter(
            f"{prefix}api_calls_total",
            "Total GCP API calls",
            ["service", "method", "status"],
            registry=self.registry,
        )
        
        self.prom_transformations_total = Counter(
            f"{prefix}transformations_total",
            "Total resource transformations",
            ["resource_type", "status"],
            registry=self.registry,
        )
        
        self.prom_neo4j_operations_total = Counter(
            f"{prefix}neo4j_operations_total",
            "Total Neo4j operations",
            ["operation_type", "status"],
            registry=self.registry,
        )
        
        # Gauges
        self.prom_active_subscriptions = Gauge(
            f"{prefix}active_subscriptions",
            "Number of active Pub/Sub subscriptions",
            registry=self.registry,
        )
        
        self.prom_active_workers = Gauge(
            f"{prefix}active_workers",
            "Number of active processing workers",
            registry=self.registry,
        )
        
        self.prom_queue_size = Gauge(
            f"{prefix}queue_size",
            "Current message queue size",
            ["queue_name"],
            registry=self.registry,
        )
        
        self.prom_neo4j_connections = Gauge(
            f"{prefix}neo4j_connections",
            "Active Neo4j connections",
            registry=self.registry,
        )
        
        # Histograms (for latency distributions)
        self.prom_processing_duration = Histogram(
            f"{prefix}processing_duration_seconds",
            "Message processing duration",
            ["resource_type"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
            registry=self.registry,
        )
        
        self.prom_api_latency = Histogram(
            f"{prefix}api_latency_seconds",
            "GCP API call latency",
            ["service", "method"],
            buckets=[0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=self.registry,
        )
        
        self.prom_transformation_duration = Histogram(
            f"{prefix}transformation_duration_seconds",
            "Resource transformation duration",
            ["resource_type"],
            buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0],
            registry=self.registry,
        )
        
        self.prom_neo4j_duration = Histogram(
            f"{prefix}neo4j_duration_seconds",
            "Neo4j operation duration",
            ["operation_type"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry,
        )
        
        # Info metrics
        self.prom_pipeline_info = Info(
            f"{prefix}info",
            "Pipeline information",
            registry=self.registry,
        )
        
        # Set pipeline info
        self.prom_pipeline_info.info({
            "namespace": self.namespace,
            "version": "1.0.0",
        })
    
    # Message Processing Metrics
    
    def increment_messages_processed(
        self,
        resource_type: str,
        count: int = 1,
    ) -> None:
        """Increment messages processed counter."""
        with self._lock:
            self._counters[f"messages_processed_{resource_type}"] += count
        
        if self.enable_prometheus:
            self.prom_messages_total.labels(
                resource_type=resource_type,
                status="success"
            ).inc(count)
    
    def increment_messages_failed(
        self,
        resource_type: str,
        count: int = 1,
    ) -> None:
        """Increment messages failed counter."""
        with self._lock:
            self._counters[f"messages_failed_{resource_type}"] += count
        
        if self.enable_prometheus:
            self.prom_messages_total.labels(
                resource_type=resource_type,
                status="failed"
            ).inc(count)
    
    def record_processing_time(
        self,
        resource_type: str,
        duration_ms: float,
    ) -> None:
        """Record message processing time."""
        with self._lock:
            self._timings[f"processing_{resource_type}"].append(duration_ms)
        
        if self.enable_prometheus:
            self.prom_processing_duration.labels(
                resource_type=resource_type
            ).observe(duration_ms / 1000.0)
    
    def track_processing(self, resource_type: str):
        """Context manager for tracking processing time."""
        return _ProcessingTimer(self, resource_type)
    
    # API Call Metrics
    
    def increment_api_calls(
        self,
        service: str,
        method: str,
        success: bool = True,
    ) -> None:
        """Increment API calls counter."""
        status = "success" if success else "error"
        
        with self._lock:
            self._counters[f"api_calls_{service}_{method}_{status}"] += 1
        
        if self.enable_prometheus:
            self.prom_api_calls_total.labels(
                service=service,
                method=method,
                status=status
            ).inc()
    
    def record_api_latency(
        self,
        service: str,
        method: str,
        duration_ms: float,
    ) -> None:
        """Record API call latency."""
        with self._lock:
            self._timings[f"api_{service}_{method}"].append(duration_ms)
        
        if self.enable_prometheus:
            self.prom_api_latency.labels(
                service=service,
                method=method
            ).observe(duration_ms / 1000.0)
    
    def track_api_call(self, service: str, method: str):
        """Context manager for tracking API call time."""
        return _APICallTimer(self, service, method)
    
    # Transformation Metrics
    
    def increment_transformations(
        self,
        resource_type: str,
        success: bool = True,
    ) -> None:
        """Increment transformation counter."""
        status = "success" if success else "error"
        
        with self._lock:
            self._counters[f"transformations_{resource_type}_{status}"] += 1
        
        if self.enable_prometheus:
            self.prom_transformations_total.labels(
                resource_type=resource_type,
                status=status
            ).inc()
    
    def record_transformation_time(
        self,
        resource_type: str,
        duration_ms: float,
    ) -> None:
        """Record transformation time."""
        with self._lock:
            self._timings[f"transformation_{resource_type}"].append(duration_ms)
        
        if self.enable_prometheus:
            self.prom_transformation_duration.labels(
                resource_type=resource_type
            ).observe(duration_ms / 1000.0)
    
    def track_transformation(self, resource_type: str):
        """Context manager for tracking transformation time."""
        return _TransformationTimer(self, resource_type)
    
    # Neo4j Metrics
    
    def increment_neo4j_operations(
        self,
        operation_type: str,
        success: bool = True,
    ) -> None:
        """Increment Neo4j operations counter."""
        status = "success" if success else "error"
        
        with self._lock:
            self._counters[f"neo4j_{operation_type}_{status}"] += 1
        
        if self.enable_prometheus:
            self.prom_neo4j_operations_total.labels(
                operation_type=operation_type,
                status=status
            ).inc()
    
    def record_neo4j_duration(
        self,
        operation_type: str,
        duration_ms: float,
    ) -> None:
        """Record Neo4j operation duration."""
        with self._lock:
            self._timings[f"neo4j_{operation_type}"].append(duration_ms)
        
        if self.enable_prometheus:
            self.prom_neo4j_duration.labels(
                operation_type=operation_type
            ).observe(duration_ms / 1000.0)
    
    def track_neo4j_operation(self, operation_type: str):
        """Context manager for tracking Neo4j operation time."""
        return _Neo4jTimer(self, operation_type)
    
    def set_neo4j_connections(self, count: int) -> None:
        """Set number of active Neo4j connections."""
        with self._lock:
            self._gauges["neo4j_connections"] = count
        
        if self.enable_prometheus:
            self.prom_neo4j_connections.set(count)
    
    # Resource Metrics
    
    def set_active_subscriptions(self, count: int) -> None:
        """Set number of active subscriptions."""
        with self._lock:
            self._gauges["active_subscriptions"] = count
        
        if self.enable_prometheus:
            self.prom_active_subscriptions.set(count)
    
    def set_active_workers(self, count: int) -> None:
        """Set number of active workers."""
        with self._lock:
            self._gauges["active_workers"] = count
        
        if self.enable_prometheus:
            self.prom_active_workers.set(count)
    
    def set_queue_size(self, queue_name: str, size: int) -> None:
        """Set queue size."""
        with self._lock:
            self._gauges[f"queue_{queue_name}"] = size
        
        if self.enable_prometheus:
            self.prom_queue_size.labels(queue_name=queue_name).set(size)
    
    # Metrics Retrieval
    
    def get_snapshot(self) -> MetricSnapshot:
        """Get current metrics snapshot."""
        with self._lock:
            # Aggregate counts
            messages_processed = sum(
                v for k, v in self._counters.items()
                if k.startswith("messages_processed_")
            )
            messages_failed = sum(
                v for k, v in self._counters.items()
                if k.startswith("messages_failed_")
            )
            api_calls = sum(
                v for k, v in self._counters.items()
                if k.startswith("api_calls_") and k.endswith("_success")
            )
            api_errors = sum(
                v for k, v in self._counters.items()
                if k.startswith("api_calls_") and k.endswith("_error")
            )
            transformations = sum(
                v for k, v in self._counters.items()
                if k.startswith("transformations_") and k.endswith("_success")
            )
            transformation_errors = sum(
                v for k, v in self._counters.items()
                if k.startswith("transformations_") and k.endswith("_error")
            )
            neo4j_writes = sum(
                v for k, v in self._counters.items()
                if k.startswith("neo4j_") and k.endswith("_success")
            )
            neo4j_errors = sum(
                v for k, v in self._counters.items()
                if k.startswith("neo4j_") and k.endswith("_error")
            )
            
            # Calculate averages
            def avg(key_prefix: str) -> float:
                times = []
                for k, v in self._timings.items():
                    if k.startswith(key_prefix):
                        times.extend(v)
                return sum(times) / len(times) if times else 0.0
            
            return MetricSnapshot(
                timestamp=datetime.utcnow(),
                messages_processed=messages_processed,
                messages_failed=messages_failed,
                api_calls=api_calls,
                api_errors=api_errors,
                transformations=transformations,
                transformation_errors=transformation_errors,
                neo4j_writes=neo4j_writes,
                neo4j_errors=neo4j_errors,
                avg_processing_time_ms=avg("processing_"),
                avg_api_latency_ms=avg("api_"),
                avg_transformation_time_ms=avg("transformation_"),
                avg_neo4j_write_time_ms=avg("neo4j_"),
            )
    
    def get_prometheus_metrics(self) -> bytes:
        """
        Get Prometheus-formatted metrics.
        
        Returns:
            Prometheus metrics as bytes
        """
        if not self.enable_prometheus:
            return b""
        
        return generate_latest(self.registry)
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """Get all metrics as dictionary."""
        snapshot = self.get_snapshot()
        
        with self._lock:
            return {
                "snapshot": snapshot.to_dict(),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }
    
    def increment_counter(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
        count: int = 1,
    ) -> None:
        """
        Increment a generic counter metric.
        
        Args:
            name: Counter name
            labels: Optional labels for the counter
            count: Amount to increment
        """
        label_str = ""
        if labels:
            label_str = "_" + "_".join(f"{k}_{v}" for k, v in sorted(labels.items()))
        
        with self._lock:
            self._counters[f"{name}{label_str}"] += count
    
    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a value in a histogram metric.
        
        Args:
            name: Histogram name
            value: Value to record
            labels: Optional labels for the histogram
        """
        label_str = ""
        if labels:
            label_str = "_" + "_".join(f"{k}_{v}" for k, v in sorted(labels.items()))
        
        with self._lock:
            self._timings[f"{name}{label_str}"].append(value)
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._timings.clear()
        
        logger.info("metrics_reset")


# Context managers for timing

class _ProcessingTimer:
    """Context manager for tracking processing time."""
    
    def __init__(self, metrics: PipelineMetrics, resource_type: str):
        self.metrics = metrics
        self.resource_type = resource_type
        self.start_time = None
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        if exc_type is not None:
            self.success = False
            self.metrics.increment_messages_failed(self.resource_type)
        else:
            self.metrics.increment_messages_processed(self.resource_type)
        
        self.metrics.record_processing_time(self.resource_type, duration_ms)
        return False


class _APICallTimer:
    """Context manager for tracking API call time."""
    
    def __init__(self, metrics: PipelineMetrics, service: str, method: str):
        self.metrics = metrics
        self.service = service
        self.method = method
        self.start_time = None
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.success = exc_type is None
        
        self.metrics.increment_api_calls(self.service, self.method, self.success)
        self.metrics.record_api_latency(self.service, self.method, duration_ms)
        return False


class _TransformationTimer:
    """Context manager for tracking transformation time."""
    
    def __init__(self, metrics: PipelineMetrics, resource_type: str):
        self.metrics = metrics
        self.resource_type = resource_type
        self.start_time = None
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.success = exc_type is None
        
        self.metrics.increment_transformations(self.resource_type, self.success)
        self.metrics.record_transformation_time(self.resource_type, duration_ms)
        return False


class _Neo4jTimer:
    """Context manager for tracking Neo4j operation time."""
    
    def __init__(self, metrics: PipelineMetrics, operation_type: str):
        self.metrics = metrics
        self.operation_type = operation_type
        self.start_time = None
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.success = exc_type is None
        
        self.metrics.increment_neo4j_operations(self.operation_type, self.success)
        self.metrics.record_neo4j_duration(self.operation_type, duration_ms)
        return False


# Global metrics instance
_metrics_instance: Optional[PipelineMetrics] = None


def get_pipeline_metrics() -> PipelineMetrics:
    """
    Get the global pipeline metrics instance.
    
    Returns:
        PipelineMetrics singleton instance
    """
    global _metrics_instance
    
    if _metrics_instance is None:
        _metrics_instance = PipelineMetrics()
    
    return _metrics_instance


def initialize_metrics(**kwargs: Any) -> PipelineMetrics:
    """
    Initialize the global pipeline metrics with custom configuration.
    
    Args:
        **kwargs: Configuration options for PipelineMetrics
        
    Returns:
        Configured PipelineMetrics instance
    """
    global _metrics_instance
    _metrics_instance = PipelineMetrics(**kwargs)
    return _metrics_instance

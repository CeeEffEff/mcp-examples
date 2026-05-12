"""
GCP Digital Twin Ingestion Pipeline Orchestrator

This module provides the main orchestration layer that integrates all pipeline
components into a cohesive data ingestion system.

Components Integrated:
    1. Monitoring System - Logging, metrics, health checks, alerts
    2. GCP API Client - Resource fetching from GCP APIs
    3. Event System - Pub/Sub event subscription
    4. Transformation - Data conversion and validation
    5. Neo4j Operations - Graph database persistence

Architecture:
    GCP Events → Pub/Sub → Event Handler → Transformer → Neo4j Writer
         ↓
    Monitoring (metrics, logs, health, alerts)

Usage:
    ```python
    from ingestion_pipeline.pipeline import GCPIngestionPipeline
    
    # Create pipeline with configuration
    pipeline = GCPIngestionPipeline(
        gcp_project_id="my-project",
        gcp_service_account_path="key.json",
        neo4j_uri="bolt://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="password",
    )
    
    # Start pipeline
    await pipeline.start()
    
    # ... pipeline runs ...
    
    # Stop gracefully
    await pipeline.stop()
    ```
"""

import os
import asyncio
import signal
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field

# Monitoring
from .monitoring import (
    initialize_monitoring,
    get_logger,
    get_metrics,
    get_health_monitor,
    get_alert_manager,
    shutdown_monitoring,
    create_connection_check,
    create_threshold_check,
    AlertSeverity,
    AlertRule,
    AlertChannel,
)

# API Client
from .api_client import (
    GCPAuthManager,
    GCPClientManager,
    GCPAuthenticationError,
)

# Event System
from .event_system import (
    EventSubscriber,
    ResourceEvent,
    GCPResourceType,
    EventType,
)

# Transformation
from .transformation import (
    TransformerFactory,
    TransformationError,
    ResourceValidator,
)

# Neo4j Operations
from .neo4j_ops import (
    Neo4jConnectionManager,
    Neo4jBatchWriter,
    get_connection_manager,
    Neo4jConnectionError,
)


@dataclass
class PipelineConfig:
    """Configuration for the GCP ingestion pipeline."""
    
    # GCP Configuration
    gcp_project_id: str
    gcp_service_account_path: str
    gcp_region: str = "us-central1"
    
    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"
    
    # Pub/Sub Configuration
    pubsub_topic: str = "gcp-resource-events"
    pubsub_subscription: str = "pipeline-subscription"
    pubsub_create_subscription: bool = True
    
    # Pipeline Behavior
    batch_size: int = 100
    max_workers: int = 10
    poll_timeout: float = 10.0
    
    # Monitoring Configuration
    log_level: str = "INFO"
    log_dir: str = "./logs"
    enable_console_log: bool = True
    enable_file_log: bool = True
    enable_gcp_log: bool = False
    enable_prometheus: bool = True
    health_check_interval: int = 60
    
    # Alert Configuration
    alert_channels: List[str] = field(default_factory=lambda: ["log", "console"])
    
    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Create configuration from environment variables."""
        return cls(
            # GCP
            gcp_project_id=os.getenv("GCP_PROJECT_ID", ""),
            gcp_service_account_path=os.getenv("GCP_SERVICE_ACCOUNT_KEY_PATH", ""),
            gcp_region=os.getenv("GCP_REGION", "us-central1"),
            # Neo4j
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_username=os.getenv("NEO4J_USERNAME", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
            neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
            # Pub/Sub
            pubsub_topic=os.getenv("PUBSUB_TOPIC", "gcp-resource-events"),
            pubsub_subscription=os.getenv("PUBSUB_SUBSCRIPTION", "pipeline-subscription"),
            # Pipeline
            batch_size=int(os.getenv("BATCH_SIZE", "100")),
            max_workers=int(os.getenv("MAX_WORKERS", "10")),
            poll_timeout=float(os.getenv("POLL_TIMEOUT", "10.0")),
            # Monitoring
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_dir=os.getenv("LOG_DIR", "./logs"),
            enable_console_log=os.getenv("LOG_CONSOLE", "true").lower() == "true",
            enable_file_log=os.getenv("LOG_FILE", "true").lower() == "true",
            enable_gcp_log=os.getenv("LOG_GCP", "false").lower() == "true",
            enable_prometheus=os.getenv("METRICS_ENABLED", "true").lower() == "true",
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "60")),
            # Alerts
            alert_channels=os.getenv("ALERT_CHANNELS", "log,console").split(","),
        )
    
    def validate(self) -> None:
        """Validate configuration values."""
        if not self.gcp_project_id:
            raise ValueError("GCP_PROJECT_ID is required")
        if not self.gcp_service_account_path:
            raise ValueError("GCP_SERVICE_ACCOUNT_KEY_PATH is required")
        if not os.path.exists(self.gcp_service_account_path):
            raise ValueError(f"Service account key file not found: {self.gcp_service_account_path}")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.max_workers <= 0:
            raise ValueError("max_workers must be positive")


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class GCPIngestionPipeline:
    """
    Main orchestrator for the GCP Digital Twin ingestion pipeline.
    
    Integrates all components and manages their lifecycle.
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None, **kwargs):
        """
        Initialize the ingestion pipeline.
        
        Args:
            config: Pipeline configuration. If not provided, created from kwargs or env
            **kwargs: Individual configuration parameters (alternative to config)
        """
        if config is None:
            if kwargs:
                config = PipelineConfig(**kwargs)
            else:
                config = PipelineConfig.from_env()
        
        config.validate()
        self.config = config
        
        # Component instances
        self._monitoring_initialized = False
        self._auth_manager: Optional[GCPAuthManager] = None
        self._client_manager: Optional[GCPClientManager] = None
        self._neo4j_manager: Optional[Neo4jConnectionManager] = None
        self._batch_writer: Optional[Neo4jBatchWriter] = None
        self._event_subscriber: Optional[EventSubscriber] = None
        self._validator: Optional[ResourceValidator] = None
        
        # Runtime state
        self._is_running = False
        self._shutdown_event = asyncio.Event()
        self._logger = None
        self._metrics = None
        self._health = None
        self._alerts = None
        
    async def initialize(self) -> None:
        """Initialize all pipeline components."""
        # Step 1: Initialize monitoring
        await self._initialize_monitoring()
        
        self._logger.info("pipeline_initialization_started", config=self.config.__dict__)
        
        try:
            # Step 2: Initialize Neo4j
            await self._initialize_neo4j()
            
            # Step 3: Initialize GCP clients
            await self._initialize_gcp_clients()
            
            # Step 4: Initialize transformation
            await self._initialize_transformation()
            
            # Step 5: Initialize event subscriber
            await self._initialize_event_system()
            
            # Step 6: Register health checks
            await self._register_health_checks()
            
            # Step 7: Register alert rules
            await self._register_alert_rules()
            
            self._logger.info("pipeline_initialization_complete")
            
        except Exception as e:
            self._logger.error("pipeline_initialization_failed", error=str(e), exc_info=True)
            await self.shutdown()
            raise PipelineError(f"Failed to initialize pipeline: {e}") from e
    
    async def _initialize_monitoring(self) -> None:
        """Initialize monitoring systems."""
        monitoring = initialize_monitoring(
            log_level=self.config.log_level,
            log_dir=self.config.log_dir,
            enable_console_log=self.config.enable_console_log,
            enable_file_log=self.config.enable_file_log,
            enable_gcp_log=self.config.enable_gcp_log,
            enable_prometheus=self.config.enable_prometheus,
            health_check_interval=self.config.health_check_interval,
            alert_channels=[AlertChannel(c) for c in self.config.alert_channels],
        )
        
        self._monitoring_initialized = True
        self._logger = get_logger("pipeline")
        self._metrics = get_metrics()
        self._health = get_health_monitor()
        self._alerts = get_alert_manager()
        
        self._logger.info("monitoring_initialized")
    
    async def _initialize_neo4j(self) -> None:
        """Initialize Neo4j connection and batch writer."""
        self._logger.info("initializing_neo4j")
        
        try:
            self._neo4j_manager = get_connection_manager()
            self._neo4j_manager.connect(
                uri=self.config.neo4j_uri,
                username=self.config.neo4j_username,
                password=self.config.neo4j_password,
                database=self.config.neo4j_database,
            )
            
            # Test connection
            health = self._neo4j_manager.health_check()
            if not health["connected"]:
                raise Neo4jConnectionError("Neo4j connection health check failed")
            
            # Create batch writer
            self._batch_writer = Neo4jBatchWriter(
                connection_manager=self._neo4j_manager,
                batch_size=self.config.batch_size,
            )
            
            self._logger.info("neo4j_initialized", uri=self.config.neo4j_uri)
            self._metrics.increment_counter("pipeline_component_initialized", labels={"component": "neo4j"})
            
        except Exception as e:
            self._logger.error("neo4j_initialization_failed", error=str(e))
            raise
    
    async def _initialize_gcp_clients(self) -> None:
        """Initialize GCP authentication and API clients."""
        self._logger.info("initializing_gcp_clients")
        
        try:
            self._auth_manager = GCPAuthManager(
                service_account_path=self.config.gcp_service_account_path,
                project_id=self.config.gcp_project_id,
            )
            
            # Validate authentication
            if not self._auth_manager.project_id:
                raise GCPAuthenticationError("Failed to authenticate with GCP")
            
            self._client_manager = GCPClientManager(
                auth_manager=self._auth_manager,
            )
            
            self._logger.info(
                "gcp_clients_initialized",
                project_id=self._auth_manager.project_id,
            )
            self._metrics.increment_counter("pipeline_component_initialized", labels={"component": "gcp_client"})
            
        except Exception as e:
            self._logger.error("gcp_client_initialization_failed", error=str(e))
            raise
    
    async def _initialize_transformation(self) -> None:
        """Initialize transformation and validation components."""
        self._logger.info("initializing_transformation")
        
        try:
            self._validator = ResourceValidator()
            
            self._logger.info("transformation_initialized")
            self._metrics.increment_counter("pipeline_component_initialized", labels={"component": "transformation"})
            
        except Exception as e:
            self._logger.error("transformation_initialization_failed", error=str(e))
            raise
    
    async def _initialize_event_system(self) -> None:
        """Initialize event subscription system."""
        self._logger.info("initializing_event_system")
        
        try:
            self._event_subscriber = EventSubscriber(
                auth_manager=self._auth_manager,
                max_workers=self.config.max_workers,
            )
            
            # Register callback for all resource types
            self._event_subscriber.register_callback(
                self._handle_resource_event,
                resource_type=None,  # Handle all types
            )
            
            # Subscribe to Pub/Sub topic
            self._event_subscriber.subscribe(
                subscription_name=self.config.pubsub_subscription,
                topic_name=self.config.pubsub_topic,
                create_if_missing=self.config.pubsub_create_subscription,
            )
            
            self._logger.info(
                "event_system_initialized",
                subscription=self.config.pubsub_subscription,
                topic=self.config.pubsub_topic,
            )
            self._metrics.increment_counter("pipeline_component_initialized", labels={"component": "event_system"})
            
        except Exception as e:
            self._logger.error("event_system_initialization_failed", error=str(e))
            raise
    
    async def _register_health_checks(self) -> None:
        """Register health checks for all components."""
        self._logger.info("registering_health_checks")
        
        # Neo4j health check
        def neo4j_health() -> bool:
            try:
                health = self._neo4j_manager.health_check()
                return health["connected"]
            except:
                return False
        
        self._health.register_check("neo4j", neo4j_health)
        
        # GCP client health check
        def gcp_client_health() -> bool:
            try:
                return self._auth_manager.project_id is not None
            except:
                return False
        
        self._health.register_check("gcp_client", gcp_client_health)
        
        # Event subscriber health check
        def event_subscriber_health() -> bool:
            try:
                health = self._event_subscriber.get_health_status()
                return health.get("is_running", False)
            except:
                return False
        
        self._health.register_check("event_subscriber", event_subscriber_health)
        
        self._logger.info("health_checks_registered", count=3)
    
    async def _register_alert_rules(self) -> None:
        """Register alert rules for pipeline monitoring."""
        self._logger.info("registering_alert_rules")
        
        # Alert rule for high error rate
        def check_error_rate(metrics_snapshot) -> Optional[str]:
            error_count = metrics_snapshot.get("pipeline_errors_total", 0)
            processed_count = metrics_snapshot.get("pipeline_resources_processed", 0)
            
            if processed_count > 100:  # Only check after processing some resources
                error_rate = error_count / processed_count
                if error_rate > 0.1:  # 10% error rate
                    return f"High error rate: {error_rate:.2%} ({error_count}/{processed_count})"
            return None
        
        error_rate_rule = AlertRule(
            name="high_error_rate",
            severity=AlertSeverity.WARNING,
            check_function=lambda: check_error_rate(self._metrics.get_snapshot().to_dict()),
            cooldown_seconds=300,  # 5 minutes
        )
        self._alerts.register_rule(error_rate_rule)
        
        # Alert rule for unhealthy components
        def check_component_health() -> Optional[str]:
            health = self._health.get_health()
            if health.unhealthy_components:
                return f"Unhealthy components: {', '.join(health.unhealthy_components)}"
            return None
        
        health_rule = AlertRule(
            name="unhealthy_components",
            severity=AlertSeverity.ERROR,
            check_function=check_component_health,
            cooldown_seconds=60,
        )
        self._alerts.register_rule(health_rule)
        
        self._logger.info("alert_rules_registered", count=2)
    
    async def _handle_resource_event(self, event: ResourceEvent) -> None:
        """
        Handle incoming resource events from Pub/Sub.
        
        This is the main data processing callback that:
        1. Validates the event
        2. Transforms the resource data
        3. Writes to Neo4j
        4. Tracks metrics
        """
        resource_type = event.metadata.resource_type.value
        event_type = event.metadata.event_type.value
        
        self._logger.debug(
            "processing_resource_event",
            resource_type=resource_type,
            event_type=event_type,
            resource_name=event.metadata.resource_name,
        )
        
        with self._metrics.track_processing(resource_type):
            try:
                # Step 1: Validate event
                validation_result = self._validator.validate(event.data)
                if not validation_result.is_valid:
                    self._logger.warning(
                        "resource_validation_failed",
                        resource_type=resource_type,
                        errors=validation_result.errors,
                    )
                    self._metrics.increment_counter("pipeline_validation_errors", labels={"type": resource_type})
                    return
                
                # Step 2: Transform resource
                transformer = TransformerFactory.get_transformer(resource_type)
                transformation_result = transformer.transform(event.data)
                
                self._logger.debug(
                    "resource_transformed",
                    resource_type=resource_type,
                    node_labels=transformation_result.node.labels,
                    relationship_count=len(transformation_result.relationships),
                )
                
                # Step 3: Write to Neo4j
                write_metrics = self._batch_writer.write_transformation_results([transformation_result])
                
                self._logger.info(
                    "resource_processed",
                    resource_type=resource_type,
                    event_type=event_type,
                    nodes_created=write_metrics.nodes_created,
                    relationships_created=write_metrics.relationships_created,
                    duration_ms=write_metrics.duration_ms,
                )
                
                # Track success metrics
                self._metrics.increment_counter("pipeline_resources_processed", labels={"type": resource_type})
                self._metrics.record_histogram("pipeline_processing_duration", write_metrics.duration_ms / 1000.0)
                
            except TransformationError as e:
                self._logger.error(
                    "transformation_error",
                    resource_type=resource_type,
                    error=str(e),
                )
                self._metrics.increment_counter("pipeline_transformation_errors", labels={"type": resource_type})
                
            except Exception as e:
                self._logger.error(
                    "resource_processing_failed",
                    resource_type=resource_type,
                    error=str(e),
                    exc_info=True,
                )
                self._metrics.increment_counter("pipeline_errors_total", labels={"type": resource_type})
    
    async def start(self) -> None:
        """Start the pipeline and begin processing events."""
        if self._is_running:
            self._logger.warning("pipeline_already_running")
            return
        
        self._logger.info("starting_pipeline")
        
        try:
            # Initialize if not already done
            if not self._monitoring_initialized:
                await self.initialize()
            
            # Start event subscriber
            await self._event_subscriber.start()
            
            self._is_running = True
            self._logger.info("pipeline_started")
            self._metrics.increment_counter("pipeline_starts")
            
            # Setup signal handlers for graceful shutdown
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
            
            # Wait for shutdown event
            await self._shutdown_event.wait()
            
        except Exception as e:
            self._logger.error("pipeline_start_failed", error=str(e), exc_info=True)
            self._metrics.increment_counter("pipeline_start_errors")
            raise PipelineError(f"Failed to start pipeline: {e}") from e
    
    async def stop(self, timeout: int = 30) -> None:
        """Stop the pipeline gracefully."""
        if not self._is_running:
            return
        
        self._logger.info("stopping_pipeline", timeout=timeout)
        
        try:
            # Stop event subscriber
            if self._event_subscriber:
                await self._event_subscriber.stop()
            
            self._is_running = False
            self._shutdown_event.set()
            
            self._logger.info("pipeline_stopped")
            self._metrics.increment_counter("pipeline_stops")
            
        except Exception as e:
            self._logger.error("pipeline_stop_error", error=str(e), exc_info=True)
    
    async def shutdown(self, timeout: int = 30) -> None:
        """Shutdown the pipeline and cleanup all resources."""
        self._logger.info("shutting_down_pipeline") if self._logger else None
        
        # Stop if running
        if self._is_running:
            await self.stop(timeout)
        
        # Close Neo4j connection
        if self._neo4j_manager:
            try:
                self._neo4j_manager.close()
                self._logger.info("neo4j_connection_closed") if self._logger else None
            except Exception as e:
                self._logger.warning("neo4j_close_error", error=str(e)) if self._logger else None
        
        # Shutdown monitoring
        if self._monitoring_initialized:
            try:
                shutdown_monitoring(timeout=timeout)
            except Exception as e:
                print(f"Monitoring shutdown error: {e}")
        
        self._logger.info("pipeline_shutdown_complete") if self._logger else None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current pipeline status.
        
        Returns:
            Dictionary with pipeline status information
        """
        status = {
            "is_running": self._is_running,
            "config": self.config.__dict__,
        }
        
        if self._monitoring_initialized:
            # Add monitoring status
            if self._metrics:
                snapshot = self._metrics.get_snapshot()
                status["metrics"] = snapshot.to_dict()
            
            if self._health:
                health = self._health.get_health()
                status["health"] = {
                    "overall_status": health.overall_status.value,
                    "healthy_components": health.healthy_components,
                    "degraded_components": health.degraded_components,
                    "unhealthy_components": health.unhealthy_components,
                }
            
            if self._event_subscriber:
                status["event_subscriber"] = self._event_subscriber.get_health_status()
        
        return status


# Convenience function for running the pipeline
async def run_pipeline(config: Optional[PipelineConfig] = None, **kwargs) -> None:
    """
    Run the ingestion pipeline.
    
    This is a convenience function that creates, starts, and manages
    the pipeline lifecycle.
    
    Args:
        config: Pipeline configuration
        **kwargs: Individual configuration parameters
    """
    pipeline = GCPIngestionPipeline(config=config, **kwargs)
    
    try:
        await pipeline.initialize()
        await pipeline.start()
    except KeyboardInterrupt:
        print("\nShutting down pipeline...")
    finally:
        await pipeline.shutdown()


if __name__ == "__main__":
    """CLI entry point for running the pipeline."""
    # Load configuration from environment
    config = PipelineConfig.from_env()
    
    # Run pipeline
    asyncio.run(run_pipeline(config=config))

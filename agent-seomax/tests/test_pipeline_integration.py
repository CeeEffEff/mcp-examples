"""
Integration Tests for GCP Ingestion Pipeline

Tests the full pipeline integration with all components working together.
These tests use mocks for external services but test real integration logic.
"""

import asyncio
import pytest
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass

# Import pipeline components
from src.ingestion_pipeline.pipeline import (
    GCPIngestionPipeline,
    PipelineConfig,
    PipelineError,
)
from src.ingestion_pipeline.event_system import (
    ResourceEvent,
    EventMetadata,
    GCPResourceType,
    EventType,
)
from src.ingestion_pipeline.transformation import TransformationResult, ComputeInstanceSchema


# Test configuration
TEST_CONFIG = PipelineConfig(
    gcp_project_id="test-project",
    gcp_service_account_path="/tmp/test-key.json",
    gcp_region="us-central1",
    neo4j_uri="bolt://localhost:7687",
    neo4j_username="neo4j",
    neo4j_password="test-password",
    neo4j_database="neo4j",
    pubsub_topic="test-topic",
    pubsub_subscription="test-subscription",
    batch_size=10,
    max_workers=2,
    log_level="DEBUG",
    log_dir="/tmp/logs",
    enable_console_log=True,
    enable_file_log=False,
    enable_gcp_log=False,
    enable_prometheus=True,
    health_check_interval=5,
    alert_channels=["log"],
)


@pytest.fixture
def mock_service_account_file(tmp_path):
    """Create a mock service account JSON file."""
    key_file = tmp_path / "test-key.json"
    key_file.write_text('{"type": "service_account", "project_id": "test-project"}')
    return str(key_file)


@pytest.fixture
def test_config(mock_service_account_file):
    """Create test configuration with mock service account."""
    config = TEST_CONFIG
    config.gcp_service_account_path = mock_service_account_file
    return config


@pytest.fixture
def mock_neo4j_connection():
    """Mock Neo4j connection manager."""
    with patch('src.ingestion_pipeline.pipeline.get_connection_manager') as mock:
        connection = Mock()
        connection.connect = Mock()
        connection.health_check = Mock(return_value={"connected": True, "version": "5.0.0"})
        connection.close = Mock()
        mock.return_value = connection
        yield connection


@pytest.fixture
def mock_neo4j_writer():
    """Mock Neo4j batch writer."""
    with patch('src.ingestion_pipeline.pipeline.Neo4jBatchWriter') as mock:
        writer = Mock()
        writer.write_transformation_results = Mock(return_value=Mock(
            nodes_created=1,
            nodes_updated=0,
            relationships_created=2,
            relationships_updated=0,
            duration_ms=50.0,
        ))
        mock.return_value = writer
        yield writer


@pytest.fixture
def mock_gcp_auth():
    """Mock GCP authentication."""
    with patch('src.ingestion_pipeline.pipeline.GCPAuthManager') as mock:
        auth = Mock()
        auth.project_id = "test-project"
        auth.get_credentials = Mock(return_value=Mock())
        mock.return_value = auth
        yield auth


@pytest.fixture
def mock_gcp_client_manager():
    """Mock GCP client manager."""
    with patch('src.ingestion_pipeline.pipeline.GCPClientManager') as mock:
        manager = Mock()
        mock.return_value = manager
        yield manager


@pytest.fixture
def mock_event_subscriber():
    """Mock event subscriber."""
    with patch('src.ingestion_pipeline.pipeline.EventSubscriber') as mock:
        subscriber = Mock()
        subscriber.register_callback = Mock()
        subscriber.subscribe = Mock()
        subscriber.start = AsyncMock()
        subscriber.stop = AsyncMock()
        subscriber.get_health_status = Mock(return_value={
            "is_running": True,
            "callback_count": 1,
            "subscription_count": 1,
        })
        mock.return_value = subscriber
        yield subscriber


@pytest.fixture
def mock_transformer_factory():
    """Mock transformer factory."""
    with patch('src.ingestion_pipeline.pipeline.TransformerFactory') as mock:
        transformer = Mock()
        transformer.transform = Mock(return_value=TransformationResult(
            node=ComputeInstanceSchema(
                resourceId="instance-1",
                name="test-instance",
                labels=["ComputeInstance", "GCPResource"],
                properties={"status": "RUNNING"},
            ),
            relationships=[],
        ))
        mock.get_transformer = Mock(return_value=transformer)
        yield mock


@pytest.fixture
def mock_validator():
    """Mock resource validator."""
    with patch('src.ingestion_pipeline.pipeline.ResourceValidator') as mock:
        validator = Mock()
        validator.validate = Mock(return_value=Mock(is_valid=True, errors=[]))
        mock.return_value = validator
        yield validator


@pytest.mark.asyncio
class TestPipelineInitialization:
    """Test pipeline initialization."""
    
    async def test_pipeline_initialization_success(
        self,
        test_config,
        mock_neo4j_connection,
        mock_neo4j_writer,
        mock_gcp_auth,
        mock_gcp_client_manager,
        mock_event_subscriber,
        mock_validator,
    ):
        """Test successful pipeline initialization."""
        pipeline = GCPIngestionPipeline(config=test_config)
        
        await pipeline.initialize()
        
        # Verify all components initialized
        assert pipeline._monitoring_initialized is True
        assert pipeline._logger is not None
        assert pipeline._metrics is not None
        assert pipeline._health is not None
        assert pipeline._alerts is not None
        
        # Verify Neo4j connection
        mock_neo4j_connection.connect.assert_called_once()
        mock_neo4j_connection.health_check.assert_called()
        
        # Verify GCP client setup
        assert pipeline._auth_manager is not None
        assert pipeline._client_manager is not None
        
        # Verify event subscriber setup
        mock_event_subscriber.register_callback.assert_called_once()
        mock_event_subscriber.subscribe.assert_called_once()
        
        # Cleanup
        await pipeline.shutdown()
    
    async def test_pipeline_initialization_missing_config(self):
        """Test pipeline initialization with missing required config."""
        with pytest.raises(ValueError, match="GCP_PROJECT_ID is required"):
            config = PipelineConfig(
                gcp_project_id="",  # Empty
                gcp_service_account_path="/tmp/test-key.json",
            )
            pipeline = GCPIngestionPipeline(config=config)
    
    async def test_pipeline_initialization_neo4j_failure(
        self,
        test_config,
        mock_gcp_auth,
        mock_gcp_client_manager,
        mock_event_subscriber,
        mock_validator,
    ):
        """Test pipeline initialization when Neo4j connection fails."""
        with patch('src.ingestion_pipeline.pipeline.get_connection_manager') as mock:
            connection = Mock()
            connection.connect = Mock()
            connection.health_check = Mock(return_value={"connected": False})
            mock.return_value = connection
            
            pipeline = GCPIngestionPipeline(config=test_config)
            
            with pytest.raises(PipelineError, match="Failed to initialize pipeline"):
                await pipeline.initialize()


@pytest.mark.asyncio
class TestPipelineEventProcessing:
    """Test pipeline event processing."""
    
    async def test_handle_resource_event_success(
        self,
        test_config,
        mock_neo4j_connection,
        mock_neo4j_writer,
        mock_gcp_auth,
        mock_gcp_client_manager,
        mock_event_subscriber,
        mock_transformer_factory,
        mock_validator,
    ):
        """Test successful resource event handling."""
        pipeline = GCPIngestionPipeline(config=test_config)
        await pipeline.initialize()
        
        # Create test event
        event = ResourceEvent(
            metadata=EventMetadata(
                event_id="test-event-1",
                event_type=EventType.CREATED,
                resource_type=GCPResourceType.COMPUTE_INSTANCE,
                resource_name="instance-1",
                project_id="test-project",
                timestamp="2025-01-01T00:00:00Z",
            ),
            data={"name": "test-instance", "status": "RUNNING"},
        )
        
        # Process event
        await pipeline._handle_resource_event(event)
        
        # Verify validation called
        mock_validator.return_value.validate.assert_called_once()
        
        # Verify transformation called
        mock_transformer_factory.get_transformer.assert_called_once_with(
            GCPResourceType.COMPUTE_INSTANCE.value
        )
        
        # Verify Neo4j write called
        mock_neo4j_writer.write_transformation_results.assert_called_once()
        
        # Verify metrics tracked
        metrics = pipeline._metrics.get_snapshot()
        assert metrics.to_dict()["pipeline_resources_processed"] >= 1
        
        await pipeline.shutdown()
    
    async def test_handle_resource_event_validation_failure(
        self,
        test_config,
        mock_neo4j_connection,
        mock_neo4j_writer,
        mock_gcp_auth,
        mock_gcp_client_manager,
        mock_event_subscriber,
        mock_transformer_factory,
    ):
        """Test event handling when validation fails."""
        # Mock validator that fails
        with patch('src.ingestion_pipeline.pipeline.ResourceValidator') as mock:
            validator = Mock()
            validator.validate = Mock(return_value=Mock(
                is_valid=False,
                errors=["Invalid resource format"]
            ))
            mock.return_value = validator
            
            pipeline = GCPIngestionPipeline(config=test_config)
            await pipeline.initialize()
            
            # Create test event
            event = ResourceEvent(
                metadata=EventMetadata(
                    event_id="test-event-2",
                    event_type=EventType.CREATED,
                    resource_type=GCPResourceType.COMPUTE_INSTANCE,
                    resource_name="instance-2",
                    project_id="test-project",
                    timestamp="2025-01-01T00:00:00Z",
                ),
                data={"invalid": "data"},
            )
            
            # Process event
            await pipeline._handle_resource_event(event)
            
            # Verify Neo4j write NOT called
            mock_neo4j_writer.write_transformation_results.assert_not_called()
            
            # Verify validation error metrics
            metrics = pipeline._metrics.get_snapshot()
            assert metrics.to_dict()["pipeline_validation_errors"] >= 1
            
            await pipeline.shutdown()
    
    async def test_handle_resource_event_transformation_error(
        self,
        test_config,
        mock_neo4j_connection,
        mock_neo4j_writer,
        mock_gcp_auth,
        mock_gcp_client_manager,
        mock_event_subscriber,
        mock_validator,
    ):
        """Test event handling when transformation fails."""
        # Mock transformer that raises error
        with patch('src.ingestion_pipeline.pipeline.TransformerFactory') as mock:
            from src.ingestion_pipeline.transformation import TransformationError
            transformer = Mock()
            transformer.transform = Mock(side_effect=TransformationError("Transform failed"))
            mock.get_transformer = Mock(return_value=transformer)
            
            pipeline = GCPIngestionPipeline(config=test_config)
            await pipeline.initialize()
            
            # Create test event
            event = ResourceEvent(
                metadata=EventMetadata(
                    event_id="test-event-3",
                    event_type=EventType.CREATED,
                    resource_type=GCPResourceType.COMPUTE_INSTANCE,
                    resource_name="instance-3",
                    project_id="test-project",
                    timestamp="2025-01-01T00:00:00Z",
                ),
                data={"name": "test-instance"},
            )
            
            # Process event (should not raise)
            await pipeline._handle_resource_event(event)
            
            # Verify transformation error metrics
            metrics = pipeline._metrics.get_snapshot()
            assert metrics.to_dict()["pipeline_transformation_errors"] >= 1
            
            await pipeline.shutdown()


@pytest.mark.asyncio
class TestPipelineLifecycle:
    """Test pipeline lifecycle management."""
    
    async def test_pipeline_start_stop(
        self,
        test_config,
        mock_neo4j_connection,
        mock_neo4j_writer,
        mock_gcp_auth,
        mock_gcp_client_manager,
        mock_event_subscriber,
        mock_validator,
    ):
        """Test pipeline start and stop."""
        pipeline = GCPIngestionPipeline(config=test_config)
        await pipeline.initialize()
        
        # Start pipeline in background
        start_task = asyncio.create_task(pipeline.start())
        
        # Wait a bit for startup
        await asyncio.sleep(0.1)
        
        assert pipeline._is_running is True
        mock_event_subscriber.start.assert_called_once()
        
        # Stop pipeline
        await pipeline.stop()
        
        assert pipeline._is_running is False
        mock_event_subscriber.stop.assert_called_once()
        
        # Cleanup task
        start_task.cancel()
        try:
            await start_task
        except asyncio.CancelledError:
            pass
        
        await pipeline.shutdown()
    
    async def test_pipeline_shutdown_cleanup(
        self,
        test_config,
        mock_neo4j_connection,
        mock_neo4j_writer,
        mock_gcp_auth,
        mock_gcp_client_manager,
        mock_event_subscriber,
        mock_validator,
    ):
        """Test pipeline shutdown cleans up resources."""
        pipeline = GCPIngestionPipeline(config=test_config)
        await pipeline.initialize()
        
        await pipeline.shutdown()
        
        # Verify Neo4j connection closed
        mock_neo4j_connection.close.assert_called_once()
    
    async def test_pipeline_get_status(
        self,
        test_config,
        mock_neo4j_connection,
        mock_neo4j_writer,
        mock_gcp_auth,
        mock_gcp_client_manager,
        mock_event_subscriber,
        mock_validator,
    ):
        """Test getting pipeline status."""
        pipeline = GCPIngestionPipeline(config=test_config)
        await pipeline.initialize()
        
        status = pipeline.get_status()
        
        assert "is_running" in status
        assert "config" in status
        assert "metrics" in status
        assert "health" in status
        assert "event_subscriber" in status
        
        assert status["config"]["gcp_project_id"] == "test-project"
        assert status["config"]["batch_size"] == 10
        
        await pipeline.shutdown()


@pytest.mark.asyncio
class TestPipelineHealthMonitoring:
    """Test pipeline health monitoring."""
    
    async def test_health_checks_registered(
        self,
        test_config,
        mock_neo4j_connection,
        mock_neo4j_writer,
        mock_gcp_auth,
        mock_gcp_client_manager,
        mock_event_subscriber,
        mock_validator,
    ):
        """Test health checks are registered for all components."""
        pipeline = GCPIngestionPipeline(config=test_config)
        await pipeline.initialize()
        
        health = pipeline._health.get_health()
        
        # Verify health checks exist for key components
        assert "neo4j" in health.components
        assert "gcp_client" in health.components
        assert "event_subscriber" in health.components
        
        await pipeline.shutdown()
    
    async def test_alert_rules_registered(
        self,
        test_config,
        mock_neo4j_connection,
        mock_neo4j_writer,
        mock_gcp_auth,
        mock_gcp_client_manager,
        mock_event_subscriber,
        mock_validator,
    ):
        """Test alert rules are registered."""
        pipeline = GCPIngestionPipeline(config=test_config)
        await pipeline.initialize()
        
        # Verify alert rules exist
        alerts = pipeline._alerts
        assert alerts is not None
        
        # Get statistics
        stats = alerts.get_statistics()
        assert stats["rule_count"] >= 2  # Should have error rate and health rules
        
        await pipeline.shutdown()


@pytest.mark.asyncio
class TestPipelineConfiguration:
    """Test pipeline configuration."""
    
    def test_config_from_env(self, monkeypatch, mock_service_account_file):
        """Test loading configuration from environment variables."""
        # Set environment variables
        monkeypatch.setenv("GCP_PROJECT_ID", "env-project")
        monkeypatch.setenv("GCP_SERVICE_ACCOUNT_KEY_PATH", mock_service_account_file)
        monkeypatch.setenv("GCP_REGION", "us-west1")
        monkeypatch.setenv("NEO4J_URI", "bolt://neo4j:7687")
        monkeypatch.setenv("NEO4J_USERNAME", "admin")
        monkeypatch.setenv("NEO4J_PASSWORD", "secret")
        monkeypatch.setenv("BATCH_SIZE", "50")
        monkeypatch.setenv("MAX_WORKERS", "5")
        
        config = PipelineConfig.from_env()
        
        assert config.gcp_project_id == "env-project"
        assert config.gcp_region == "us-west1"
        assert config.neo4j_uri == "bolt://neo4j:7687"
        assert config.neo4j_username == "admin"
        assert config.batch_size == 50
        assert config.max_workers == 5
    
    def test_config_validation(self, mock_service_account_file):
        """Test configuration validation."""
        # Valid config
        config = PipelineConfig(
            gcp_project_id="test-project",
            gcp_service_account_path=mock_service_account_file,
        )
        config.validate()  # Should not raise
        
        # Invalid: missing project ID
        with pytest.raises(ValueError, match="GCP_PROJECT_ID is required"):
            config = PipelineConfig(
                gcp_project_id="",
                gcp_service_account_path=mock_service_account_file,
            )
            config.validate()
        
        # Invalid: missing service account path
        with pytest.raises(ValueError, match="GCP_SERVICE_ACCOUNT_KEY_PATH is required"):
            config = PipelineConfig(
                gcp_project_id="test-project",
                gcp_service_account_path="",
            )
            config.validate()
        
        # Invalid: negative batch size
        with pytest.raises(ValueError, match="batch_size must be positive"):
            config = PipelineConfig(
                gcp_project_id="test-project",
                gcp_service_account_path=mock_service_account_file,
                batch_size=-1,
            )
            config.validate()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

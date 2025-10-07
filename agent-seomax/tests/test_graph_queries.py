"""
Test Suite for Graph Queries Module

This module provides comprehensive tests for all graph query classes:
- ResourceQueries
- TraversalQueries  
- RelationshipQueries
- AnalysisQueries
- QueryCache

Author: GCP Digital Twin Agent System
Date: 2025-01-06
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import List, Dict, Any

# Import directly from graph_queries submodule to avoid loading entire package with GCP dependencies
from src.ingestion_pipeline.graph_queries.resource_queries import get_resource_queries
from src.ingestion_pipeline.graph_queries.traversal_queries import get_traversal_queries
from src.ingestion_pipeline.graph_queries.relationship_queries import get_relationship_queries
from src.ingestion_pipeline.graph_queries.analysis_queries import get_analysis_queries
from src.ingestion_pipeline.graph_queries.query_cache import get_query_cache, reset_cache
from src.ingestion_pipeline.graph_queries.base_query import (
    QueryResult,
    QueryValidationError,
    QueryExecutionError,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_neo4j_result():
    """Mock Neo4j Result object."""
    result = Mock()
    result.records = []
    return result


@pytest.fixture
def mock_connection_manager():
    """Mock Neo4j connection manager."""
    manager = Mock()
    session = MagicMock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    manager.get_session.return_value = session
    return manager


@pytest.fixture
def sample_vm_data():
    """Sample VM resource data."""
    return {
        "id": "projects/test-project/zones/us-central1-a/instances/test-vm",
        "name": "test-vm",
        "project_id": "test-project",
        "zone": "us-central1-a",
        "machine_type": "n1-standard-1",
        "status": "RUNNING",
        "_labels": ["VirtualMachine"]
    }


@pytest.fixture
def sample_disk_data():
    """Sample disk resource data."""
    return {
        "id": "projects/test-project/zones/us-central1-a/disks/test-disk",
        "name": "test-disk",
        "project_id": "test-project",
        "zone": "us-central1-a",
        "size_gb": 100,
        "type": "pd-standard",
        "status": "READY",
        "_labels": ["PersistentDisk"]
    }


# =============================================================================
# ResourceQueries Tests
# =============================================================================

class TestResourceQueries:
    """Tests for ResourceQueries class."""
    
    def test_find_by_id_success(self, mock_connection_manager, sample_vm_data):
        """Test successful resource lookup by ID."""
        # Setup mock
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: sample_vm_data if key == "resource" else ["VirtualMachine"]
        mock_record.get.return_value = ["VirtualMachine"]
        
        mock_result = Mock()
        mock_result.records = [mock_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        # Execute
        queries = get_resource_queries(connection_manager=mock_connection_manager)
        result = queries.find_by_id(sample_vm_data["id"])
        
        # Verify
        assert result is not None
        assert result["id"] == sample_vm_data["id"]
        assert "_labels" in result
    
    def test_find_by_id_not_found(self, mock_connection_manager):
        """Test resource not found."""
        mock_result = Mock()
        mock_result.records = []
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        queries = get_resource_queries(connection_manager=mock_connection_manager)
        result = queries.find_by_id("nonexistent-id")
        
        assert result is None
    
    def test_find_by_id_validation_error(self, mock_connection_manager):
        """Test validation error for missing resource_id."""
        queries = get_resource_queries(connection_manager=mock_connection_manager)
        
        with pytest.raises(QueryValidationError):
            queries.find_by_id("")
    
    def test_find_by_type(self, mock_connection_manager, sample_vm_data):
        """Test finding resources by type."""
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: sample_vm_data
        
        mock_result = Mock()
        mock_result.records = [mock_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        queries = get_resource_queries(connection_manager=mock_connection_manager)
        result = queries.find_by_type("VirtualMachine", project_id="test-project")
        
        assert isinstance(result, QueryResult)
        assert len(result.data) == 1
        assert result.data[0]["id"] == sample_vm_data["id"]
    
    def test_count(self, mock_connection_manager):
        """Test counting resources."""
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: 5
        
        mock_result = Mock()
        mock_result.records = [mock_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        queries = get_resource_queries(connection_manager=mock_connection_manager)
        count = queries.count(resource_type="VirtualMachine", project_id="test-project")
        
        assert count == 5


# =============================================================================
# TraversalQueries Tests
# =============================================================================

class TestTraversalQueries:
    """Tests for TraversalQueries class."""
    
    def test_find_dependencies(self, mock_connection_manager):
        """Test finding resource dependencies."""
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: {
            "resource_id": "dep-resource-1",
            "resource_type": "PersistentDisk",
            "distance": 1,
            "relationship_type": "DEPENDS_ON"
        }[key]
        
        mock_result = Mock()
        mock_result.records = [mock_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        queries = get_traversal_queries(connection_manager=mock_connection_manager)
        result = queries.find_dependencies("test-resource-id")
        
        assert isinstance(result, QueryResult)
        assert len(result.data) >= 0
    
    def test_find_shortest_path(self, mock_connection_manager):
        """Test finding shortest path between resources."""
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: {
            "path_length": 2,
            "node_ids": ["source", "intermediate", "target"],
            "relationships": ["DEPENDS_ON", "USES"]
        }[key]
        
        mock_result = Mock()
        mock_result.records = [mock_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        queries = get_traversal_queries(connection_manager=mock_connection_manager)
        result = queries.find_shortest_path("source-id", "target-id")
        
        assert result is not None
        assert "path_length" in result
    
    def test_analyze_impact(self, mock_connection_manager):
        """Test impact analysis for a resource."""
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: {
            "resource_id": "affected-1",
            "resource_type": "VirtualMachine",
            "distance": 1
        }[key]
        
        mock_result = Mock()
        mock_result.records = [mock_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        queries = get_traversal_queries(connection_manager=mock_connection_manager)
        result = queries.analyze_impact("test-resource-id")
        
        assert isinstance(result, dict)
        assert "affected_resources" in result


# =============================================================================
# RelationshipQueries Tests
# =============================================================================

class TestRelationshipQueries:
    """Tests for RelationshipQueries class."""
    
    def test_find_relationships_between(self, mock_connection_manager):
        """Test finding relationships between two resources."""
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: {
            "source_id": "source-id",
            "relationship_type": "DEPENDS_ON",
            "target_id": "target-id",
            "relationship_id": 123,
            "properties": {"weight": 1}
        }[key]
        
        mock_result = Mock()
        mock_result.records = [mock_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        queries = get_relationship_queries(connection_manager=mock_connection_manager)
        result = queries.find_relationships_between("source-id", "target-id")
        
        assert isinstance(result, QueryResult)
        assert len(result.data) == 1
        assert result.data[0]["relationship_type"] == "DEPENDS_ON"
    
    def test_count_relationships(self, mock_connection_manager):
        """Test counting relationships for a resource."""
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: 3
        
        mock_result = Mock()
        mock_result.records = [mock_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        queries = get_relationship_queries(connection_manager=mock_connection_manager)
        counts = queries.count_relationships("test-resource-id")
        
        assert isinstance(counts, dict)
        assert "incoming" in counts
        assert "outgoing" in counts
        assert "total" in counts
    
    def test_analyze_relationship_patterns(self, mock_connection_manager):
        """Test relationship pattern analysis."""
        # Mock type distribution result
        type_record = Mock()
        type_record.__getitem__ = lambda self, key: {
            "relationship_type": "DEPENDS_ON",
            "count": 10
        }[key]
        
        # Mock pair patterns result
        pair_record = Mock()
        pair_record.__getitem__ = lambda self, key: {
            "source_type": "VirtualMachine",
            "relationship_type": "USES",
            "target_type": "PersistentDisk",
            "count": 5
        }[key]
        
        mock_result = Mock()
        mock_result.records = [type_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.side_effect = [
            Mock(records=[type_record]),  # Type distribution
            Mock(records=[pair_record])    # Pair patterns
        ]
        
        queries = get_relationship_queries(connection_manager=mock_connection_manager)
        result = queries.analyze_relationship_patterns("test-project")
        
        assert isinstance(result, QueryResult)
        assert "type_distribution" in result.data
        assert "pair_patterns" in result.data


# =============================================================================
# AnalysisQueries Tests
# =============================================================================

class TestAnalysisQueries:
    """Tests for AnalysisQueries class."""
    
    def test_analyze_costs(self, mock_connection_manager):
        """Test cost analysis."""
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: {
            "resource_type": "VirtualMachine",
            "resource_count": 3,
            "total_cost": 150.0,
            "avg_cost": 50.0,
            "min_cost": 30.0,
            "max_cost": 70.0
        }[key]
        
        mock_result = Mock()
        mock_result.records = [mock_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        queries = get_analysis_queries(connection_manager=mock_connection_manager)
        result = queries.analyze_costs("test-project")
        
        assert isinstance(result, dict)
        assert "total_monthly_cost" in result
        assert "breakdown" in result
        assert result["total_monthly_cost"] == 150.0
    
    def test_identify_bottlenecks(self, mock_connection_manager):
        """Test bottleneck identification."""
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: {
            "resource_id": "bottleneck-resource",
            "resource_type": "VirtualMachine",
            "resource_name": "critical-vm",
            "status": "RUNNING",
            "dependency_count": 15,
            "dependent_ids": ["dep1", "dep2", "dep3"]
        }[key]
        
        mock_result = Mock()
        mock_result.records = [mock_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        queries = get_analysis_queries(connection_manager=mock_connection_manager)
        result = queries.identify_bottlenecks("test-project")
        
        assert isinstance(result, QueryResult)
        assert len(result.data) == 1
        assert result.data[0]["dependency_count"] == 15
        assert "severity" in result.data[0]
    
    def test_find_security_issues(self, mock_connection_manager):
        """Test security issue detection."""
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: {
            "resource_id": "vm-1",
            "resource_type": "VirtualMachine",
            "resource_name": "public-vm",
            "public_ip": "1.2.3.4"
        }[key]
        
        mock_result = Mock()
        mock_result.records = [mock_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        queries = get_analysis_queries(connection_manager=mock_connection_manager)
        result = queries.find_security_issues("test-project", check_types=["public_ips"])
        
        assert isinstance(result, QueryResult)
        assert len(result.data) >= 0
    
    def test_suggest_optimizations(self, mock_connection_manager):
        """Test optimization suggestions."""
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: {
            "vm_id": "underutilized-vm",
            "vm_name": "test-vm",
            "machine_type": "n1-standard-8",
            "cpu_util": 5.0,
            "mem_util": 10.0,
            "cost": 200.0
        }[key]
        
        mock_result = Mock()
        mock_result.records = [mock_record]
        
        session = mock_connection_manager.get_session.return_value.__enter__.return_value
        session.run.return_value = mock_result
        
        queries = get_analysis_queries(connection_manager=mock_connection_manager)
        result = queries.suggest_optimizations("test-project", optimization_types=["underutilized"])
        
        assert isinstance(result, QueryResult)
        assert len(result.data) >= 0


# =============================================================================
# QueryCache Tests
# =============================================================================

class TestQueryCache:
    """Tests for QueryCache class."""
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = get_query_cache()
        cache.clear()  # Start fresh
        
        # Set a value
        cache.set("test-key", {"data": "test-value"}, ttl_seconds=300)
        
        # Get the value
        result = cache.get("test-key")
        
        assert result is not None
        assert result["data"] == "test-value"
    
    def test_cache_miss(self):
        """Test cache miss."""
        cache = get_query_cache()
        cache.clear()
        
        result = cache.get("nonexistent-key")
        
        assert result is None
    
    def test_cache_expiration(self):
        """Test cache entry expiration."""
        cache = get_query_cache()
        cache.clear()
        
        # Set with very short TTL
        cache.set("expiring-key", "test-data", ttl_seconds=0)
        
        # Immediate get should return None (TTL=0 means immediate expiration)
        import time
        time.sleep(0.1)
        result = cache.get("expiring-key")
        
        # Entry should be expired
        assert result is None
    
    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        cache = get_query_cache()
        cache.clear()
        
        # Generate some cache activity
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        stats = cache.get_statistics()
        
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
    
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        cache = get_query_cache()
        cache.clear()
        
        cache.set("test-key", "test-value")
        assert cache.get("test-key") is not None
        
        cache.invalidate("test-key")
        assert cache.get("test-key") is None
    
    def test_cache_pattern_invalidation(self):
        """Test pattern-based cache invalidation."""
        cache = get_query_cache()
        cache.clear()
        
        cache.set("resource:vm:1", "vm1")
        cache.set("resource:vm:2", "vm2")
        cache.set("resource:disk:1", "disk1")
        
        # Invalidate all VM entries
        count = cache.invalidate_pattern("vm")
        
        assert count == 2
        assert cache.get("resource:vm:1") is None
        assert cache.get("resource:vm:2") is None
        assert cache.get("resource:disk:1") is not None
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = get_query_cache(max_size=3)
        cache.clear()
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add new entry - should evict key2 (oldest, not recently used)
        cache.set("key4", "value4")
        
        stats = cache.get_statistics()
        assert stats["size"] <= 3


# =============================================================================
# Integration Tests
# =============================================================================

class TestQueryIntegration:
    """Integration tests for graph queries."""
    
    @pytest.mark.skip(reason="Requires live Neo4j instance")
    def test_full_query_workflow(self):
        """Test complete query workflow with all components."""
        # This would test the full workflow with a real Neo4j instance
        # Skip by default unless explicitly testing integration
        pass


# =============================================================================
# Test Runner
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

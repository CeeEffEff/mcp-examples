"""
GCP Digital Twin Ingestion Pipeline

This package provides comprehensive functionality for ingesting GCP resource data
into a Neo4j graph database for digital twin representation.

Main Components:
- api_client: GCP API integration
- event_system: Pub/Sub event handling
- transformation: Resource data transformation
- neo4j_ops: Neo4j database operations
- graph_queries: Graph query interface
- monitoring: Logging, metrics, health checks
- pipeline: Main pipeline orchestration

Author: GCP Digital Twin Agent System
Date: 2025-01-06
"""

# Graph query functionality (primary interface)
from .graph_queries import (
    # Query classes
    get_resource_queries,
    get_traversal_queries,
    get_relationship_queries,
    get_analysis_queries,
    get_query_cache,
    
    # Base classes
    BaseQuery,
    QueryResult,
    
    # Exceptions
    QueryError,
    QueryValidationError,
    QueryExecutionError,
    QueryResultError,
    
    # Utilities
    reset_cache,
    generate_cache_key,
    cached_query,
)

# Neo4j operations
from .neo4j_ops import (
    get_connection_manager,
    CypherQueryBuilder,
    Neo4jBatchWriter,
)

# Monitoring
from .monitoring import (
    get_logger,
    get_metrics,
    get_health_monitor,
    get_alert_manager,
)

# Pipeline
from .pipeline import IngestionPipeline


__all__ = [
    # Graph queries
    "get_resource_queries",
    "get_traversal_queries",
    "get_relationship_queries",
    "get_analysis_queries",
    "get_query_cache",
    "BaseQuery",
    "QueryResult",
    "QueryError",
    "QueryValidationError",
    "QueryExecutionError",
    "QueryResultError",
    "reset_cache",
    "generate_cache_key",
    "cached_query",
    
    # Neo4j operations
    "get_connection_manager",
    "CypherQueryBuilder",
    "Neo4jBatchWriter",
    
    # Monitoring
    "get_logger",
    "get_metrics",
    "get_health_monitor",
    "get_alert_manager",
    
    # Pipeline
    "IngestionPipeline",
]

__version__ = "0.2.0"

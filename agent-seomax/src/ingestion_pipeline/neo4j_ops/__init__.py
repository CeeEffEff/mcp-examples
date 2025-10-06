"""
Neo4j Operations Module

Provides batch write operations, connection management, and query building
for Neo4j database operations in the GCP Digital Twin ingestion pipeline.

Usage Example:
    from ingestion_pipeline.neo4j_ops import (
        Neo4jConnectionManager,
        Neo4jBatchWriter,
        get_connection_manager,
    )
    
    # Connect to Neo4j
    manager = get_connection_manager()
    manager.connect()
    
    # Create batch writer
    writer = Neo4jBatchWriter(manager, batch_size=100)
    
    # Write transformation results
    metrics = writer.write_transformation_results(transformation_results)
    
    # Check health
    health = manager.health_check()
    
    # Close connection
    manager.close()
"""

from .connection import (
    Neo4jConnectionManager,
    Neo4jConnectionError,
    get_connection_manager,
    reset_connection_manager,
)

from .query_builder import (
    CypherQueryBuilder,
    QueryBuilderError,
    create_node_merge_query,
    create_relationship_merge_query,
)

from .batch_writer import (
    Neo4jBatchWriter,
    BatchWriterError,
    BatchWriteMetrics,
)

__all__ = [
    # Connection management
    'Neo4jConnectionManager',
    'Neo4jConnectionError',
    'get_connection_manager',
    'reset_connection_manager',
    
    # Query building
    'CypherQueryBuilder',
    'QueryBuilderError',
    'create_node_merge_query',
    'create_relationship_merge_query',
    
    # Batch writing
    'Neo4jBatchWriter',
    'BatchWriterError',
    'BatchWriteMetrics',
]

# Version information
__version__ = '0.1.0'
__author__ = 'Digital Twin Agent Team'

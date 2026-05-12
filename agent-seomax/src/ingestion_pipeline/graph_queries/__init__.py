"""
Neo4j Graph Queries Module

Provides comprehensive query capabilities for the GCP Digital Twin graph database.

Public API:
    - ResourceQueries: Resource lookup and search operations
    - TraversalQueries: Path finding and dependency analysis
    - RelationshipQueries: Relationship analysis and pattern detection
    - AnalysisQueries: Cost analysis, bottleneck identification, security checks
    - QueryCache: LRU caching with TTL for query optimization
    - get_resource_queries(): Get ResourceQueries singleton
    - get_traversal_queries(): Get TraversalQueries singleton
    - get_relationship_queries(): Get RelationshipQueries singleton
    - get_analysis_queries(): Get AnalysisQueries singleton
    - get_query_cache(): Get QueryCache singleton

Query Types:
    - Resource Queries: Find resources by ID, type, properties, search
    - Traversal Queries: Shortest paths, dependencies, impact analysis
    - Relationship Queries: Relationship analysis, pattern detection, statistics
    - Analysis Queries: Cost analysis, bottleneck identification, security checks, optimizations

Usage:
    from ingestion_pipeline.graph_queries import (
        get_resource_queries, 
        get_traversal_queries,
        get_relationship_queries,
        get_analysis_queries,
        get_query_cache
    )
    
    # Resource queries
    resource_queries = get_resource_queries()
    vm = resource_queries.find_by_id("projects/my-project/zones/us-central1-a/instances/vm-1")
    
    # Traversal queries
    traversal_queries = get_traversal_queries()
    deps = traversal_queries.find_dependencies(resource_id="...")
    impact = traversal_queries.analyze_impact(resource_id="...")
    
    # Relationship queries
    relationship_queries = get_relationship_queries()
    rels = relationship_queries.find_relationships_between(source_id="...", target_id="...")
    patterns = relationship_queries.analyze_relationship_patterns(project_id="...")
    
    # Analysis queries
    analysis_queries = get_analysis_queries()
    costs = analysis_queries.analyze_costs(project_id="...")
    bottlenecks = analysis_queries.identify_bottlenecks(project_id="...")
    security_issues = analysis_queries.find_security_issues(project_id="...")
    
    # Query caching
    cache = get_query_cache()
    stats = cache.get_statistics()
"""

from .base_query import (
    BaseQuery,
    QueryResult,
    QueryError,
    QueryValidationError,
    QueryExecutionError,
    QueryResultError,
    track_query_performance,
)

from .resource_queries import (
    ResourceQueries,
    get_resource_queries,
)

from .traversal_queries import (
    TraversalQueries,
    PathType,
    get_traversal_queries,
)

from .relationship_queries import (
    RelationshipQueries,
    get_relationship_queries,
)

from .analysis_queries import (
    AnalysisQueries,
    get_analysis_queries,
)

from .query_cache import (
    QueryCache,
    CacheEntry,
    get_query_cache,
    reset_cache,
    generate_cache_key,
    cached_query,
)


__all__ = [
    # Base classes
    "BaseQuery",
    "QueryResult",
    
    # Exceptions
    "QueryError",
    "QueryValidationError",
    "QueryExecutionError",
    "QueryResultError",
    
    # Resource queries
    "ResourceQueries",
    "get_resource_queries",
    
    # Traversal queries
    "TraversalQueries",
    "PathType",
    "get_traversal_queries",
    
    # Relationship queries
    "RelationshipQueries",
    "get_relationship_queries",
    
    # Analysis queries
    "AnalysisQueries",
    "get_analysis_queries",
    
    # Query caching
    "QueryCache",
    "CacheEntry",
    "get_query_cache",
    "reset_cache",
    "generate_cache_key",
    "cached_query",
    
    # Decorators
    "track_query_performance",
]


# Module version
__version__ = "0.2.0"

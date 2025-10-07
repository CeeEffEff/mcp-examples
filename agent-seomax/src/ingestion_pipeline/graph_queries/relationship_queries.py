"""
Relationship Queries Module

This module provides query methods for analyzing relationships between GCP resources
in the Neo4j graph database. It supports finding relationships by type, analyzing
relationship patterns, and identifying orphaned or unused relationships.

Author: GCP Digital Twin Agent System
Date: 2025-01-06
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime

from .base_query import BaseQuery, QueryResult, track_query_performance
from ..monitoring import get_logger, get_metrics

logger = get_logger("RelationshipQueries")
metrics = get_metrics()


class RelationshipQueries(BaseQuery):
    """
    Query class for relationship-focused operations in the GCP digital twin graph.
    
    This class provides methods for:
    - Finding relationships between specific resources
    - Querying relationships by type
    - Counting and analyzing relationship patterns
    - Identifying orphaned or unused relationships
    - Analyzing relationship distribution across projects
    
    Examples:
        >>> from ingestion_pipeline.graph_queries import get_relationship_queries
        >>> queries = get_relationship_queries()
        >>> 
        >>> # Find all relationships between two resources
        >>> rels = queries.find_relationships_between("vm-1", "disk-1")
        >>> 
        >>> # Count relationships for a resource
        >>> counts = queries.count_relationships("vm-1")
        >>> print(f"Incoming: {counts['incoming']}, Outgoing: {counts['outgoing']}")
        >>> 
        >>> # Find all DEPENDS_ON relationships
        >>> deps = queries.find_by_type("DEPENDS_ON", limit=100)
    """
    
    def __init__(self, connection_manager=None, monitoring_enabled: bool = True):
        """
        Initialize RelationshipQueries.
        
        Args:
            connection_manager: Optional connection manager instance
            monitoring_enabled: Whether to enable monitoring (default: True)
        """
        super().__init__(connection_manager, monitoring_enabled)
        logger.info("RelationshipQueries initialized")
    
    @track_query_performance("find_relationships_between")
    def find_relationships_between(
        self,
        source_id: str,
        target_id: str,
        relationship_types: Optional[List[str]] = None,
        include_properties: bool = True
    ) -> QueryResult:
        """
        Find all relationships between two specific resources.
        
        Args:
            source_id: ID of the source resource
            target_id: ID of the target resource
            relationship_types: Optional list of relationship types to filter by
            include_properties: Whether to include relationship properties
            
        Returns:
            QueryResult containing list of relationships with their properties
            
        Raises:
            QueryValidationError: If required parameters are missing
            QueryExecutionError: If query execution fails
        """
        self._validate_required_params(
            source_id=source_id,
            target_id=target_id
        )
        
        # Build relationship type filter
        rel_filter = ""
        if relationship_types:
            sanitized_types = [self._sanitize_label(rt) for rt in relationship_types]
            rel_filter = f":{':'.join(sanitized_types)}"
        
        query = f"""
        MATCH (source {{id: $source_id}})-[r{rel_filter}]->(target {{id: $target_id}})
        RETURN 
            source.id as source_id,
            type(r) as relationship_type,
            target.id as target_id,
            properties(r) as properties,
            id(r) as relationship_id
        """
        
        result = self._execute_query(
            query=query,
            parameters={
                "source_id": source_id,
                "target_id": target_id
            },
            query_type="find_relationships_between"
        )
        
        relationships = []
        for record in result.records:
            rel_data = {
                "source_id": record["source_id"],
                "relationship_type": record["relationship_type"],
                "target_id": record["target_id"],
                "relationship_id": record["relationship_id"]
            }
            
            if include_properties and record["properties"]:
                rel_data["properties"] = dict(record["properties"])
            
            relationships.append(rel_data)
        
        logger.info(
            f"Found {len(relationships)} relationships between {source_id} and {target_id}"
        )
        
        return QueryResult(
            data=relationships,
            query_type="find_relationships_between",
            record_count=len(relationships),
            execution_time=result.execution_time,
            timestamp=result.timestamp
        )
    
    @track_query_performance("find_by_type")
    def find_by_type(
        self,
        relationship_type: str,
        project_id: Optional[str] = None,
        include_nodes: bool = False,
        limit: int = 100,
        skip: int = 0
    ) -> QueryResult:
        """
        Find relationships by their type.
        
        Args:
            relationship_type: Type of relationship (e.g., "DEPENDS_ON", "USES")
            project_id: Optional filter by project ID
            include_nodes: Whether to include source and target node details
            limit: Maximum number of relationships to return
            skip: Number of relationships to skip (for pagination)
            
        Returns:
            QueryResult containing list of relationships
            
        Raises:
            QueryValidationError: If parameters are invalid
            QueryExecutionError: If query execution fails
        """
        self._validate_required_params(relationship_type=relationship_type)
        self._validate_positive_int(limit, "limit")
        self._validate_positive_int(skip, "skip", allow_zero=True)
        
        sanitized_type = self._sanitize_label(relationship_type)
        
        # Build query based on project filter
        if project_id:
            match_clause = f"""
            MATCH (source {{project_id: $project_id}})-[r:{sanitized_type}]->(target)
            """
        else:
            match_clause = f"""
            MATCH (source)-[r:{sanitized_type}]->(target)
            """
        
        if include_nodes:
            return_clause = """
            RETURN 
                source.id as source_id,
                labels(source) as source_labels,
                properties(source) as source_properties,
                type(r) as relationship_type,
                properties(r) as relationship_properties,
                target.id as target_id,
                labels(target) as target_labels,
                properties(target) as target_properties,
                id(r) as relationship_id
            """
        else:
            return_clause = """
            RETURN 
                source.id as source_id,
                type(r) as relationship_type,
                target.id as target_id,
                properties(r) as relationship_properties,
                id(r) as relationship_id
            """
        
        query = f"""
        {match_clause}
        {return_clause}
        SKIP $skip
        LIMIT $limit
        """
        
        parameters = {
            "limit": limit,
            "skip": skip
        }
        if project_id:
            parameters["project_id"] = project_id
        
        result = self._execute_query(
            query=query,
            parameters=parameters,
            query_type="find_by_type"
        )
        
        relationships = []
        for record in result.records:
            rel_data = {
                "source_id": record["source_id"],
                "relationship_type": record["relationship_type"],
                "target_id": record["target_id"],
                "relationship_id": record["relationship_id"]
            }
            
            if record.get("relationship_properties"):
                rel_data["properties"] = dict(record["relationship_properties"])
            
            if include_nodes:
                rel_data["source"] = {
                    "id": record["source_id"],
                    "labels": record.get("source_labels", []),
                    "properties": dict(record.get("source_properties", {}))
                }
                rel_data["target"] = {
                    "id": record["target_id"],
                    "labels": record.get("target_labels", []),
                    "properties": dict(record.get("target_properties", {}))
                }
        
            relationships.append(rel_data)
        
        logger.info(
            f"Found {len(relationships)} {relationship_type} relationships"
        )
        
        return QueryResult(
            data=relationships,
            query_type="find_by_type",
            record_count=len(relationships),
            execution_time=result.execution_time,
            timestamp=result.timestamp
        )
    
    @track_query_performance("count_relationships")
    def count_relationships(
        self,
        resource_id: str,
        relationship_type: Optional[str] = None,
        direction: str = "both"
    ) -> Dict[str, int]:
        """
        Count incoming and outgoing relationships for a resource.
        
        Args:
            resource_id: ID of the resource
            relationship_type: Optional filter by relationship type
            direction: "incoming", "outgoing", or "both" (default: "both")
            
        Returns:
            Dictionary with counts: {"incoming": int, "outgoing": int, "total": int}
            
        Raises:
            QueryValidationError: If parameters are invalid
            QueryExecutionError: If query execution fails
        """
        self._validate_required_params(resource_id=resource_id)
        
        if direction not in ["incoming", "outgoing", "both"]:
            raise ValueError(f"Invalid direction: {direction}. Must be 'incoming', 'outgoing', or 'both'")
        
        rel_filter = ""
        if relationship_type:
            sanitized_type = self._sanitize_label(relationship_type)
            rel_filter = f":{sanitized_type}"
        
        counts = {"incoming": 0, "outgoing": 0, "total": 0}
        
        # Count incoming relationships
        if direction in ["incoming", "both"]:
            query_incoming = f"""
            MATCH (n {{id: $resource_id}})<-[r{rel_filter}]-()
            RETURN count(r) as count
            """
            result = self._execute_query(
                query=query_incoming,
                parameters={"resource_id": resource_id},
                query_type="count_relationships_incoming"
            )
            counts["incoming"] = result.records[0]["count"] if result.records else 0
        
        # Count outgoing relationships
        if direction in ["outgoing", "both"]:
            query_outgoing = f"""
            MATCH (n {{id: $resource_id}})-[r{rel_filter}]->()
            RETURN count(r) as count
            """
            result = self._execute_query(
                query=query_outgoing,
                parameters={"resource_id": resource_id},
                query_type="count_relationships_outgoing"
            )
            counts["outgoing"] = result.records[0]["count"] if result.records else 0
        
        counts["total"] = counts["incoming"] + counts["outgoing"]
        
        logger.info(
            f"Resource {resource_id} has {counts['total']} relationships "
            f"(incoming: {counts['incoming']}, outgoing: {counts['outgoing']})"
        )
        
        return counts
    
    @track_query_performance("find_unused_relationships")
    def find_unused_relationships(
        self,
        project_id: Optional[str] = None,
        limit: int = 100
    ) -> QueryResult:
        """
        Find relationships that point to non-existent nodes (orphaned relationships).
        
        This can happen if nodes are deleted but relationships remain, or due to
        data inconsistencies during ingestion.
        
        Args:
            project_id: Optional filter by project ID
            limit: Maximum number of orphaned relationships to return
            
        Returns:
            QueryResult containing list of orphaned relationships
            
        Raises:
            QueryExecutionError: If query execution fails
        """
        self._validate_positive_int(limit, "limit")
        
        # Neo4j automatically removes relationships when nodes are deleted,
        # so we look for other indicators of "unused" relationships:
        # 1. Relationships with invalid/empty properties
        # 2. Relationships to deprecated resources (marked as deleted but not removed)
        
        project_filter = "WHERE source.project_id = $project_id" if project_id else ""
        
        query = f"""
        MATCH (source)-[r]->(target)
        {project_filter}
        WHERE target.status = 'DELETED' OR target.deleted = true
        RETURN 
            source.id as source_id,
            type(r) as relationship_type,
            target.id as target_id,
            target.status as target_status,
            properties(r) as relationship_properties,
            id(r) as relationship_id
        LIMIT $limit
        """
        
        parameters = {"limit": limit}
        if project_id:
            parameters["project_id"] = project_id
        
        result = self._execute_query(
            query=query,
            parameters=parameters,
            query_type="find_unused_relationships"
        )
        
        orphaned = []
        for record in result.records:
            orphaned.append({
                "source_id": record["source_id"],
                "relationship_type": record["relationship_type"],
                "target_id": record["target_id"],
                "target_status": record["target_status"],
                "relationship_id": record["relationship_id"],
                "properties": dict(record.get("relationship_properties", {}))
            })
        
        logger.warning(f"Found {len(orphaned)} unused/orphaned relationships")
        
        return QueryResult(
            data=orphaned,
            query_type="find_unused_relationships",
            record_count=len(orphaned),
            execution_time=result.execution_time,
            timestamp=result.timestamp
        )
    
    @track_query_performance("analyze_relationship_patterns")
    def analyze_relationship_patterns(
        self,
        project_id: Optional[str] = None,
        min_count: int = 2
    ) -> QueryResult:
        """
        Analyze common relationship patterns in the graph.
        
        Identifies frequently occurring relationship patterns such as:
        - Most common relationship types
        - Most connected resource pairs
        - Relationship type distribution by resource type
        
        Args:
            project_id: Optional filter by project ID
            min_count: Minimum count threshold for patterns (default: 2)
            
        Returns:
            QueryResult containing relationship pattern analysis
            
        Raises:
            QueryExecutionError: If query execution fails
        """
        self._validate_positive_int(min_count, "min_count")
        
        project_filter = "WHERE source.project_id = $project_id" if project_id else ""
        
        # Query 1: Relationship type distribution
        query_type_dist = f"""
        MATCH (source)-[r]->(target)
        {project_filter}
        RETURN 
            type(r) as relationship_type,
            count(r) as count
        ORDER BY count DESC
        """
        
        # Query 2: Resource type pair patterns
        query_pair_patterns = f"""
        MATCH (source)-[r]->(target)
        {project_filter}
        WITH 
            labels(source)[0] as source_type,
            type(r) as relationship_type,
            labels(target)[0] as target_type,
            count(*) as count
        WHERE count >= $min_count
        RETURN 
            source_type,
            relationship_type,
            target_type,
            count
        ORDER BY count DESC
        LIMIT 50
        """
        
        parameters = {"min_count": min_count}
        if project_id:
            parameters["project_id"] = project_id
        
        # Execute type distribution query
        result1 = self._execute_query(
            query=query_type_dist,
            parameters=parameters if project_id else {},
            query_type="analyze_type_distribution"
        )
        
        type_distribution = [
            {"relationship_type": r["relationship_type"], "count": r["count"]}
            for r in result1.records
        ]
        
        # Execute pair patterns query
        result2 = self._execute_query(
            query=query_pair_patterns,
            parameters=parameters,
            query_type="analyze_pair_patterns"
        )
        
        pair_patterns = [
            {
                "source_type": r["source_type"],
                "relationship_type": r["relationship_type"],
                "target_type": r["target_type"],
                "count": r["count"]
            }
            for r in result2.records
        ]
        
        analysis = {
            "type_distribution": type_distribution,
            "pair_patterns": pair_patterns,
            "total_types": len(type_distribution),
            "total_patterns": len(pair_patterns),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Analyzed relationship patterns: {len(type_distribution)} types, "
            f"{len(pair_patterns)} common patterns"
        )
        
        return QueryResult(
            data=analysis,
            query_type="analyze_relationship_patterns",
            record_count=len(type_distribution) + len(pair_patterns),
            execution_time=result1.execution_time + result2.execution_time,
            timestamp=datetime.utcnow()
        )
    
    @track_query_performance("get_relationship_statistics")
    def get_relationship_statistics(
        self,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get overall relationship statistics for the graph or a specific project.
        
        Args:
            project_id: Optional filter by project ID
            
        Returns:
            Dictionary containing relationship statistics
            
        Raises:
            QueryExecutionError: If query execution fails
        """
        project_filter = "WHERE source.project_id = $project_id" if project_id else ""
        
        query = f"""
        MATCH (source)-[r]->(target)
        {project_filter}
        RETURN 
            count(r) as total_relationships,
            count(DISTINCT type(r)) as unique_relationship_types,
            count(DISTINCT source) as resources_with_outgoing,
            count(DISTINCT target) as resources_with_incoming
        """
        
        parameters = {"project_id": project_id} if project_id else {}
        
        result = self._execute_query(
            query=query,
            parameters=parameters,
            query_type="get_relationship_statistics"
        )
        
        if not result.records:
            return {
                "total_relationships": 0,
                "unique_relationship_types": 0,
                "resources_with_outgoing": 0,
                "resources_with_incoming": 0
            }
        
        record = result.records[0]
        stats = {
            "total_relationships": record["total_relationships"],
            "unique_relationship_types": record["unique_relationship_types"],
            "resources_with_outgoing": record["resources_with_outgoing"],
            "resources_with_incoming": record["resources_with_incoming"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if project_id:
            stats["project_id"] = project_id
        
        logger.info(f"Retrieved relationship statistics: {stats['total_relationships']} total")
        
        return stats


# Module-level singleton accessor
_instance: Optional[RelationshipQueries] = None


def get_relationship_queries(
    connection_manager=None,
    monitoring_enabled: bool = True
) -> RelationshipQueries:
    """
    Get or create the singleton RelationshipQueries instance.
    
    Args:
        connection_manager: Optional connection manager instance
        monitoring_enabled: Whether to enable monitoring (default: True)
        
    Returns:
        RelationshipQueries singleton instance
    """
    global _instance
    
    if _instance is None:
        _instance = RelationshipQueries(
            connection_manager=connection_manager,
            monitoring_enabled=monitoring_enabled
        )
    
    return _instance

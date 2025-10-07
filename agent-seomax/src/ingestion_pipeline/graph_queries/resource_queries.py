"""
Resource Query Layer for GCP Digital Twin

Provides query operations for finding and searching GCP resources in the Neo4j graph.
Supports lookup by ID, type, properties, and complex filtering.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from .base_query import BaseQuery, QueryResult, track_query_performance, QueryValidationError


logger = logging.getLogger(__name__)


class ResourceQueries(BaseQuery):
    """
    Query layer for GCP resource operations.
    
    Provides methods for:
    - Finding resources by ID
    - Finding resources by type/label
    - Finding resources by project
    - Filtering resources by properties
    - Searching across multiple criteria
    - Counting resources
    """
    
    @track_query_performance("resource_by_id")
    def find_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a resource by its unique ID.
        
        Args:
            resource_id: Unique resource identifier (e.g., "projects/my-project/zones/us-central1-a/instances/vm-1")
            
        Returns:
            Resource properties dict or None if not found
            
        Example:
            resource = queries.find_by_id("projects/my-project/zones/us-central1-a/instances/vm-1")
            if resource:
                print(f"Found: {resource['name']}, Status: {resource['status']}")
        """
        self._validate_required_params(resource_id=resource_id)
        
        query = """
        MATCH (r {id: $resource_id})
        RETURN r, labels(r) AS labels
        """
        
        result = self._execute_single_result_query(
            query=query,
            parameters={"resource_id": resource_id},
            query_type="resource_by_id"
        )
        
        if result and 'r' in result:
            resource_data = dict(result['r'])
            resource_data['_labels'] = result.get('labels', [])
            return resource_data
        
        return None
    
    @track_query_performance("resources_by_type")
    def find_by_type(
        self,
        resource_type: str,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Find resources by their type (node label).
        
        Args:
            resource_type: Resource type label (e.g., "VirtualMachine", "StorageBucket")
            project_id: Optional filter by project ID
            status: Optional filter by status
            limit: Maximum number of results (default: 100)
            offset: Number of results to skip (default: 0)
            
        Returns:
            List of resource property dictionaries
            
        Example:
            vms = queries.find_by_type("VirtualMachine", project_id="my-project", status="RUNNING")
            for vm in vms:
                print(f"VM: {vm['name']}, Zone: {vm.get('zone', 'N/A')}")
        """
        self._validate_required_params(resource_type=resource_type)
        self._validate_positive_int(limit, "limit")
        
        # Sanitize label
        safe_label = self._sanitize_label(resource_type)
        
        # Build query with optional filters
        query_parts = [f"MATCH (r:{safe_label})"]
        where_clauses = []
        parameters = {"limit": limit, "offset": offset}
        
        if project_id:
            where_clauses.append("r.project_id = $project_id")
            parameters["project_id"] = project_id
        
        if status:
            where_clauses.append("r.status = $status")
            parameters["status"] = status
        
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
        
        query_parts.extend([
            "RETURN r",
            "ORDER BY r.name",
            "SKIP $offset",
            "LIMIT $limit"
        ])
        
        query = "\n".join(query_parts)
        
        result = self._execute_query(
            query=query,
            parameters=parameters,
            query_type="resources_by_type"
        )
        
        return [dict(record['r']) for record in result.data]
    
    @track_query_performance("resources_by_project")
    def find_by_project(
        self,
        project_id: str,
        resource_type: Optional[str] = None,
        include_counts: bool = False,
    ) -> Dict[str, Any]:
        """
        Find all resources in a project.
        
        Args:
            project_id: GCP project ID
            resource_type: Optional filter by resource type
            include_counts: If True, include count by resource type
            
        Returns:
            Dict with 'resources' list and optional 'counts' dict
            
        Example:
            result = queries.find_by_project("my-project", include_counts=True)
            print(f"Total resources: {len(result['resources'])}")
            print(f"Resource counts: {result['counts']}")
        """
        self._validate_required_params(project_id=project_id)
        
        if resource_type:
            # Find specific type in project
            return {
                "resources": self.find_by_type(resource_type, project_id=project_id, limit=1000),
                "counts": None
            }
        
        # Find all resources in project
        query = """
        MATCH (p:Project {project_id: $project_id})-[:CONTAINS]->(r)
        RETURN r, labels(r) AS labels
        ORDER BY r.name
        """
        
        result = self._execute_query(
            query=query,
            parameters={"project_id": project_id},
            query_type="resources_by_project"
        )
        
        resources = []
        type_counts = {}
        
        for record in result.data:
            resource = dict(record['r'])
            resource_labels = record.get('labels', [])
            resource['_labels'] = resource_labels
            resources.append(resource)
            
            # Count by type
            if include_counts and resource_labels:
                primary_label = resource_labels[0]
                type_counts[primary_label] = type_counts.get(primary_label, 0) + 1
        
        response = {"resources": resources}
        
        if include_counts:
            response["counts"] = type_counts
        
        return response
    
    @track_query_performance("resources_by_properties")
    def find_by_properties(
        self,
        properties: Dict[str, Any],
        resource_type: Optional[str] = None,
        match_all: bool = True,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Find resources by property values.
        
        Args:
            properties: Dict of property name/value pairs to match
            resource_type: Optional filter by resource type
            match_all: If True, match all properties (AND). If False, match any (OR)
            limit: Maximum number of results
            
        Returns:
            List of matching resources
            
        Example:
            # Find all running VMs in us-central1
            vms = queries.find_by_properties(
                properties={"status": "RUNNING", "region": "us-central1"},
                resource_type="VirtualMachine",
                match_all=True
            )
        """
        if not properties:
            raise QueryValidationError("properties dict cannot be empty")
        
        self._validate_positive_int(limit, "limit")
        
        # Build MATCH clause
        if resource_type:
            safe_label = self._sanitize_label(resource_type)
            match_clause = f"MATCH (r:{safe_label})"
        else:
            match_clause = "MATCH (r)"
        
        # Build WHERE clauses
        where_clauses = []
        parameters = {"limit": limit}
        
        for i, (key, value) in enumerate(properties.items()):
            param_name = f"prop_{i}"
            where_clauses.append(f"r.{key} = ${param_name}")
            parameters[param_name] = value
        
        operator = " AND " if match_all else " OR "
        where_clause = "WHERE " + operator.join(where_clauses)
        
        query = f"""
        {match_clause}
        {where_clause}
        RETURN r, labels(r) AS labels
        ORDER BY r.name
        LIMIT $limit
        """
        
        result = self._execute_query(
            query=query,
            parameters=parameters,
            query_type="resources_by_properties"
        )
        
        resources = []
        for record in result.data:
            resource = dict(record['r'])
            resource['_labels'] = record.get('labels', [])
            resources.append(resource)
        
        return resources
    
    @track_query_performance("resources_search")
    def search(
        self,
        search_term: str,
        resource_types: Optional[List[str]] = None,
        search_fields: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search resources by text across specified fields.
        
        Args:
            search_term: Text to search for
            resource_types: Optional list of resource types to search
            search_fields: Fields to search in (default: ["name", "description", "id"])
            limit: Maximum results
            
        Returns:
            List of matching resources with relevance scores
            
        Example:
            results = queries.search(
                search_term="production",
                resource_types=["VirtualMachine", "StorageBucket"],
                search_fields=["name", "tags"]
            )
        """
        self._validate_required_params(search_term=search_term)
        self._validate_positive_int(limit, "limit")
        
        if not search_fields:
            search_fields = ["name", "description", "id"]
        
        # Build MATCH clause with optional type filter
        if resource_types:
            safe_labels = [self._sanitize_label(rt) for rt in resource_types]
            label_filter = ":" + "|".join(safe_labels)
            match_clause = f"MATCH (r{label_filter})"
        else:
            match_clause = "MATCH (r)"
        
        # Build WHERE clause for text matching
        where_clauses = []
        for field in search_fields:
            where_clauses.append(f"r.{field} CONTAINS $search_term")
        
        where_clause = "WHERE " + " OR ".join(where_clauses)
        
        query = f"""
        {match_clause}
        {where_clause}
        RETURN r, labels(r) AS labels
        ORDER BY r.name
        LIMIT $limit
        """
        
        result = self._execute_query(
            query=query,
            parameters={"search_term": search_term, "limit": limit},
            query_type="resources_search"
        )
        
        resources = []
        for record in result.data:
            resource = dict(record['r'])
            resource['_labels'] = record.get('labels', [])
            resources.append(resource)
        
        return resources
    
    @track_query_performance("resource_with_relationships")
    def get_with_relationships(
        self,
        resource_id: str,
        include_incoming: bool = True,
        include_outgoing: bool = True,
        relationship_types: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a resource with its relationships.
        
        Args:
            resource_id: Resource ID
            include_incoming: Include incoming relationships
            include_outgoing: Include outgoing relationships
            relationship_types: Optional filter for specific relationship types
            
        Returns:
            Dict with resource data and relationships, or None if not found
            
        Example:
            result = queries.get_with_relationships(
                resource_id="projects/my-project/zones/us-central1-a/instances/vm-1",
                relationship_types=["USES", "ATTACHED_TO"]
            )
            if result:
                print(f"Resource: {result['resource']['name']}")
                print(f"Outgoing: {len(result['outgoing'])}")
                print(f"Incoming: {len(result['incoming'])}")
        """
        self._validate_required_params(resource_id=resource_id)
        
        # Find the resource first
        resource = self.find_by_id(resource_id)
        if not resource:
            return None
        
        result = {
            "resource": resource,
            "outgoing": [],
            "incoming": []
        }
        
        # Build relationship type filter
        rel_type_filter = ""
        if relationship_types:
            rel_type_filter = ":" + "|".join(relationship_types)
        
        # Get outgoing relationships
        if include_outgoing:
            outgoing_query = f"""
            MATCH (r {{id: $resource_id}})-[rel{rel_type_filter}]->(target)
            RETURN type(rel) AS rel_type, 
                   properties(rel) AS rel_props,
                   target,
                   labels(target) AS target_labels
            """
            
            outgoing_result = self._execute_query(
                query=outgoing_query,
                parameters={"resource_id": resource_id},
                query_type="resource_outgoing_rels"
            )
            
            for record in outgoing_result.data:
                result["outgoing"].append({
                    "relationship_type": record['rel_type'],
                    "properties": record.get('rel_props', {}),
                    "target": dict(record['target']),
                    "target_labels": record.get('target_labels', [])
                })
        
        # Get incoming relationships
        if include_incoming:
            incoming_query = f"""
            MATCH (source)-[rel{rel_type_filter}]->(r {{id: $resource_id}})
            RETURN type(rel) AS rel_type,
                   properties(rel) AS rel_props,
                   source,
                   labels(source) AS source_labels
            """
            
            incoming_result = self._execute_query(
                query=incoming_query,
                parameters={"resource_id": resource_id},
                query_type="resource_incoming_rels"
            )
            
            for record in incoming_result.data:
                result["incoming"].append({
                    "relationship_type": record['rel_type'],
                    "properties": record.get('rel_props', {}),
                    "source": dict(record['source']),
                    "source_labels": record.get('source_labels', [])
                })
        
        return result
    
    @track_query_performance("count_resources")
    def count(
        self,
        resource_type: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """
        Count resources with optional filters.
        
        Args:
            resource_type: Optional resource type filter
            project_id: Optional project ID filter
            status: Optional status filter
            
        Returns:
            Count of matching resources
            
        Example:
            running_vms = queries.count(
                resource_type="VirtualMachine",
                project_id="my-project",
                status="RUNNING"
            )
            print(f"Running VMs: {running_vms}")
        """
        # Build query
        if resource_type:
            safe_label = self._sanitize_label(resource_type)
            match_clause = f"MATCH (r:{safe_label})"
        else:
            match_clause = "MATCH (r)"
        
        where_clauses = []
        parameters = {}
        
        if project_id:
            where_clauses.append("r.project_id = $project_id")
            parameters["project_id"] = project_id
        
        if status:
            where_clauses.append("r.status = $status")
            parameters["status"] = status
        
        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)
        
        query = f"""
        {match_clause}
        {where_clause}
        RETURN count(r) AS count
        """
        
        result = self._execute_single_result_query(
            query=query,
            parameters=parameters,
            query_type="count_resources"
        )
        
        return result.get('count', 0) if result else 0
    
    @track_query_performance("count_by_type")
    def count_by_type(self, project_id: Optional[str] = None) -> Dict[str, int]:
        """
        Count resources grouped by type.
        
        Args:
            project_id: Optional filter by project
            
        Returns:
            Dict mapping resource type to count
            
        Example:
            counts = queries.count_by_type(project_id="my-project")
            for resource_type, count in counts.items():
                print(f"{resource_type}: {count}")
        """
        match_clause = "MATCH (r)"
        where_clause = ""
        parameters = {}
        
        if project_id:
            where_clause = "WHERE r.project_id = $project_id"
            parameters["project_id"] = project_id
        
        query = f"""
        {match_clause}
        {where_clause}
        WITH r, labels(r) AS resource_labels
        UNWIND resource_labels AS label
        RETURN label, count(r) AS count
        ORDER BY count DESC
        """
        
        result = self._execute_query(
            query=query,
            parameters=parameters,
            query_type="count_by_type"
        )
        
        return {record['label']: record['count'] for record in result.data}
    
    @track_query_performance("find_recently_created")
    def find_recently_created(
        self,
        hours: int = 24,
        resource_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Find resources created within the specified time window.
        
        Args:
            hours: Number of hours to look back (default: 24)
            resource_type: Optional resource type filter
            limit: Maximum results
            
        Returns:
            List of recently created resources
            
        Example:
            recent = queries.find_recently_created(hours=6, resource_type="VirtualMachine")
            for resource in recent:
                print(f"Created: {resource['name']} at {resource['createdAt']}")
        """
        self._validate_positive_int(hours, "hours")
        self._validate_positive_int(limit, "limit")
        
        if resource_type:
            safe_label = self._sanitize_label(resource_type)
            match_clause = f"MATCH (r:{safe_label})"
        else:
            match_clause = "MATCH (r)"
        
        query = f"""
        {match_clause}
        WHERE r.createdAt > datetime() - duration({{hours: $hours}})
        RETURN r, labels(r) AS labels
        ORDER BY r.createdAt DESC
        LIMIT $limit
        """
        
        result = self._execute_query(
            query=query,
            parameters={"hours": hours, "limit": limit},
            query_type="find_recently_created"
        )
        
        resources = []
        for record in result.data:
            resource = dict(record['r'])
            resource['_labels'] = record.get('labels', [])
            resources.append(resource)
        
        return resources
    
    @track_query_performance("find_recently_updated")
    def find_recently_updated(
        self,
        hours: int = 24,
        resource_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Find resources updated within the specified time window.
        
        Args:
            hours: Number of hours to look back (default: 24)
            resource_type: Optional resource type filter
            limit: Maximum results
            
        Returns:
            List of recently updated resources
            
        Example:
            updated = queries.find_recently_updated(hours=1, resource_type="StorageBucket")
        """
        self._validate_positive_int(hours, "hours")
        self._validate_positive_int(limit, "limit")
        
        if resource_type:
            safe_label = self._sanitize_label(resource_type)
            match_clause = f"MATCH (r:{safe_label})"
        else:
            match_clause = "MATCH (r)"
        
        query = f"""
        {match_clause}
        WHERE r.updatedAt IS NOT NULL 
          AND r.updatedAt > datetime() - duration({{hours: $hours}})
        RETURN r, labels(r) AS labels
        ORDER BY r.updatedAt DESC
        LIMIT $limit
        """
        
        result = self._execute_query(
            query=query,
            parameters={"hours": hours, "limit": limit},
            query_type="find_recently_updated"
        )
        
        resources = []
        for record in result.data:
            resource = dict(record['r'])
            resource['_labels'] = record.get('labels', [])
            resources.append(resource)
        
        return resources


# Singleton instance
_resource_queries_instance: Optional[ResourceQueries] = None


def get_resource_queries(
    connection_manager=None,
    enable_monitoring: bool = True,
) -> ResourceQueries:
    """
    Get or create singleton ResourceQueries instance.
    
    Args:
        connection_manager: Optional connection manager
        enable_monitoring: Whether to enable monitoring
        
    Returns:
        ResourceQueries instance
    """
    global _resource_queries_instance
    
    if _resource_queries_instance is None:
        _resource_queries_instance = ResourceQueries(
            connection_manager=connection_manager,
            enable_monitoring=enable_monitoring,
        )
    
    return _resource_queries_instance

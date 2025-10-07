"""
Graph Traversal Queries for GCP Digital Twin

Provides advanced graph traversal operations including:
- Path finding (shortest path, all paths)
- Dependency analysis
- Impact assessment
- Relationship traversal
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from .base_query import BaseQuery, QueryResult, track_query_performance, QueryValidationError


logger = logging.getLogger(__name__)


class PathType(Enum):
    """Types of paths to find between nodes."""
    SHORTEST = "shortest"
    ALL = "all"
    ALL_SIMPLE = "all_simple"  # No repeated nodes


class TraversalQueries(BaseQuery):
    """
    Query layer for graph traversal operations.
    
    Provides methods for:
    - Finding paths between resources
    - Analyzing dependencies
    - Identifying downstream/upstream resources
    - Calculating relationship distances
    - Finding connected components
    """
    
    @track_query_performance("shortest_path")
    def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        Find the shortest path between two resources.
        
        Args:
            source_id: Source resource ID
            target_id: Target resource ID
            relationship_types: Optional filter for relationship types
            max_depth: Maximum path length to search
            
        Returns:
            Dict with path information or None if no path exists:
            {
                'path': [list of nodes],
                'relationships': [list of relationship types],
                'length': path length,
                'nodes': list of node details,
                'relationships_detail': list of relationship details
            }
            
        Example:
            path = queries.find_shortest_path(
                source_id="projects/my-project/zones/us-central1-a/instances/vm-1",
                target_id="projects/my-project/global/networks/vpc-1"
            )
            if path:
                print(f"Path length: {path['length']}")
                for node in path['nodes']:
                    print(f"  -> {node['name']}")
        """
        self._validate_required_params(
            source_id=source_id, target_id=target_id
        )
        self._validate_positive_int(max_depth, "max_depth")
        
        # Build relationship type filter
        rel_filter = ""
        if relationship_types:
            rel_filter = ":" + "|".join(relationship_types)
        
        query = f"""
        MATCH (source {{id: $source_id}}),
              (target {{id: $target_id}}),
              path = shortestPath((source)-[{rel_filter}*..{max_depth}]-(target))
        RETURN path,
               [node IN nodes(path) | node] AS path_nodes,
               [rel IN relationships(path) | type(rel)] AS path_rels,
               length(path) AS path_length
        """
        
        result = self._execute_single_result_query(
            query=query,
            parameters={"source_id": source_id, "target_id": target_id},
            query_type="shortest_path"
        )
        
        if not result:
            return None
        
        # Extract path details
        nodes = []
        for node in result.get('path_nodes', []):
            nodes.append(dict(node))
        
        return {
            'path': result['path'],
            'relationships': result.get('path_rels', []),
            'length': result.get('path_length', 0),
            'nodes': nodes,
        }
    
    @track_query_performance("find_dependencies")
    def find_dependencies(
        self,
        resource_id: str,
        max_depth: int = 5,
        include_indirect: bool = True,
    ) -> Dict[str, Any]:
        """
        Find all dependencies for a resource.
        
        Args:
            resource_id: Resource ID to analyze
            max_depth: Maximum dependency depth to traverse
            include_indirect: Include indirect dependencies
            
        Returns:
            Dict with direct and indirect dependencies:
            {
                'resource': resource details,
                'direct_dependencies': [list of direct deps],
                'all_dependencies': [list of all deps with depth],
                'dependency_graph': hierarchical structure
            }
            
        Example:
            deps = queries.find_dependencies(
                resource_id="projects/my-project/zones/us-central1-a/instances/vm-1",
                max_depth=3
            )
            print(f"Direct dependencies: {len(deps['direct_dependencies'])}")
            print(f"Total dependencies: {len(deps['all_dependencies'])}")
        """
        self._validate_required_params(resource_id=resource_id)
        self._validate_positive_int(max_depth, "max_depth")
        
        # Get direct dependencies first
        direct_query = """
        MATCH (r {id: $resource_id})-[:DEPENDS_ON]->(dep)
        RETURN dep, labels(dep) AS labels
        ORDER BY dep.name
        """
        
        direct_result = self._execute_query(
            query=direct_query,
            parameters={"resource_id": resource_id},
            query_type="direct_dependencies"
        )
        
        direct_deps = []
        for record in direct_result.data:
            dep = dict(record['dep'])
            dep['_labels'] = record.get('labels', [])
            direct_deps.append(dep)
        
        result = {
            'resource_id': resource_id,
            'direct_dependencies': direct_deps,
        }
        
        # Get all dependencies if requested
        if include_indirect:
            all_deps_query = f"""
            MATCH (r {{id: $resource_id}})-[:DEPENDS_ON*1..{max_depth}]->(dep)
            WITH DISTINCT dep, 
                 shortestPath((r)-[:DEPENDS_ON*]->(dep)) AS path
            RETURN dep, 
                   labels(dep) AS labels,
                   length(path) AS depth
            ORDER BY depth, dep.name
            """
            
            all_result = self._execute_query(
                query=all_deps_query,
                parameters={"resource_id": resource_id},
                query_type="all_dependencies"
            )
            
            all_deps = []
            for record in all_result.data:
                dep = dict(record['dep'])
                dep['_labels'] = record.get('labels', [])
                dep['_depth'] = record.get('depth', 0)
                all_deps.append(dep)
            
            result['all_dependencies'] = all_deps
        
        return result
    
    @track_query_performance("find_dependents")
    def find_dependents(
        self,
        resource_id: str,
        max_depth: int = 5,
        include_indirect: bool = True,
    ) -> Dict[str, Any]:
        """
        Find all resources that depend on this resource.
        
        Args:
            resource_id: Resource ID to analyze
            max_depth: Maximum depth to traverse
            include_indirect: Include indirect dependents
            
        Returns:
            Dict with direct and indirect dependents
            
        Example:
            dependents = queries.find_dependents(
                resource_id="projects/my-project/regions/us-central1/subnetworks/subnet-1"
            )
            print(f"Resources depending on this: {len(dependents['all_dependents'])}")
        """
        self._validate_required_params(resource_id=resource_id)
        self._validate_positive_int(max_depth, "max_depth")
        
        # Get direct dependents
        direct_query = """
        MATCH (dependent)-[:DEPENDS_ON]->(r {id: $resource_id})
        RETURN dependent, labels(dependent) AS labels
        ORDER BY dependent.name
        """
        
        direct_result = self._execute_query(
            query=direct_query,
            parameters={"resource_id": resource_id},
            query_type="direct_dependents"
        )
        
        direct_dependents = []
        for record in direct_result.data:
            dep = dict(record['dependent'])
            dep['_labels'] = record.get('labels', [])
            direct_dependents.append(dep)
        
        result = {
            'resource_id': resource_id,
            'direct_dependents': direct_dependents,
        }
        
        # Get all dependents if requested
        if include_indirect:
            all_deps_query = f"""
            MATCH (dependent)-[:DEPENDS_ON*1..{max_depth}]->(r {{id: $resource_id}})
            WITH DISTINCT dependent,
                 shortestPath((dependent)-[:DEPENDS_ON*]->(r)) AS path
            RETURN dependent,
                   labels(dependent) AS labels,
                   length(path) AS depth
            ORDER BY depth, dependent.name
            """
            
            all_result = self._execute_query(
                query=all_deps_query,
                parameters={"resource_id": resource_id},
                query_type="all_dependents"
            )
            
            all_dependents = []
            for record in all_result.data:
                dep = dict(record['dependent'])
                dep['_labels'] = record.get('labels', [])
                dep['_depth'] = record.get('depth', 0)
                all_dependents.append(dep)
            
            result['all_dependents'] = all_dependents
        
        return result
    
    @track_query_performance("impact_analysis")
    def analyze_impact(
        self,
        resource_id: str,
        max_depth: int = 5,
    ) -> Dict[str, Any]:
        """
        Analyze the impact if a resource fails or is deleted.
        
        Args:
            resource_id: Resource to analyze
            max_depth: Maximum depth for impact analysis
            
        Returns:
            Dict with impact analysis:
            {
                'resource': resource details,
                'directly_affected': [resources with direct dependency],
                'indirectly_affected': [resources with indirect dependency],
                'total_affected': total count,
                'affected_by_type': count by resource type,
                'critical_dependencies': resources with no alternatives
            }
            
        Example:
            impact = queries.analyze_impact(
                resource_id="projects/my-project/regions/us-central1/subnetworks/subnet-1"
            )
            print(f"Total resources affected: {impact['total_affected']}")
            print(f"By type: {impact['affected_by_type']}")
        """
        self._validate_required_params(resource_id=resource_id)
        
        # Get all affected resources
        dependents = self.find_dependents(
            resource_id=resource_id,
            max_depth=max_depth,
            include_indirect=True
        )
        
        # Categorize by depth
        direct = dependents.get('direct_dependents', [])
        all_deps = dependents.get('all_dependents', [])
        indirect = [d for d in all_deps if d.get('_depth', 0) > 1]
        
        # Count by type
        type_counts = {}
        for dep in all_deps:
            labels = dep.get('_labels', [])
            if labels:
                label = labels[0]
                type_counts[label] = type_counts.get(label, 0) + 1
        
        return {
            'resource_id': resource_id,
            'directly_affected': direct,
            'indirectly_affected': indirect,
            'total_affected': len(all_deps),
            'affected_by_type': type_counts,
        }
    
    @track_query_performance("find_circular_dependencies")
    def find_circular_dependencies(
        self,
        project_id: Optional[str] = None,
        max_cycle_length: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Find circular dependency chains in the graph.
        
        Args:
            project_id: Optional filter by project
            max_cycle_length: Maximum cycle length to search
            
        Returns:
            List of circular dependency chains:
            [{
                'cycle': [list of node IDs in cycle],
                'length': cycle length,
                'nodes': [node details]
            }]
            
        Example:
            cycles = queries.find_circular_dependencies(project_id="my-project")
            for cycle in cycles:
                print(f"Found cycle of length {cycle['length']}")
                for node in cycle['nodes']:
                    print(f"  -> {node['name']}")
        """
        self._validate_positive_int(max_cycle_length, "max_cycle_length")
        
        # Build project filter
        where_clause = ""
        parameters = {"max_length": max_cycle_length}
        
        if project_id:
            where_clause = "WHERE r.project_id = $project_id"
            parameters["project_id"] = project_id
        
        query = f"""
        MATCH path = (r)-[:DEPENDS_ON*1..{max_cycle_length}]->(r)
        {where_clause}
        WITH path, nodes(path) AS cycle_nodes, length(path) AS cycle_length
        WHERE cycle_length > 1
        RETURN cycle_nodes, cycle_length
        ORDER BY cycle_length
        LIMIT 100
        """
        
        result = self._execute_query(
            query=query,
            parameters=parameters,
            query_type="circular_dependencies"
        )
        
        cycles = []
        for record in result.data:
            nodes = [dict(node) for node in record['cycle_nodes']]
            cycles.append({
                'cycle': [node.get('id') for node in nodes],
                'length': record['cycle_length'],
                'nodes': nodes
            })
        
        return cycles
    
    @track_query_performance("find_connected_resources")
    def find_connected_resources(
        self,
        resource_id: str,
        max_hops: int = 3,
        relationship_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find all resources connected within N hops.
        
        Args:
            resource_id: Starting resource
            max_hops: Maximum number of hops (default: 3)
            relationship_types: Optional filter for relationship types
            
        Returns:
            List of connected resources with distance:
            [{
                'resource': resource details,
                'distance': number of hops,
                'path_count': number of paths to this resource
            }]
            
        Example:
            connected = queries.find_connected_resources(
                resource_id="projects/my-project/zones/us-central1-a/instances/vm-1",
                max_hops=2
            )
            for resource in connected:
                print(f"{resource['resource']['name']} - distance: {resource['distance']}")
        """
        self._validate_required_params(resource_id=resource_id)
        self._validate_positive_int(max_hops, "max_hops")
        
        # Build relationship filter
        rel_filter = ""
        if relationship_types:
            rel_filter = ":" + "|".join(relationship_types)
        
        query = f"""
        MATCH (start {{id: $resource_id}}),
              path = (start)-[{rel_filter}*1..{max_hops}]-(connected)
        WHERE connected.id <> $resource_id
        WITH DISTINCT connected, 
             min(length(path)) AS distance,
             count(path) AS path_count,
             labels(connected) AS labels
        RETURN connected, distance, path_count, labels
        ORDER BY distance, connected.name
        """
        
        result = self._execute_query(
            query=query,
            parameters={"resource_id": resource_id},
            query_type="connected_resources"
        )
        
        resources = []
        for record in result.data:
            resource = dict(record['connected'])
            resource['_labels'] = record.get('labels', [])
            resources.append({
                'resource': resource,
                'distance': record['distance'],
                'path_count': record.get('path_count', 1)
            })
        
        return resources
    
    @track_query_performance("network_path_trace")
    def trace_network_path(
        self,
        source_id: str,
        target_id: str,
        max_hops: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        Trace network connectivity path between two resources.
        
        Follows network-specific relationships like USES, ROUTES_TO, FORWARDS_TO.
        
        Args:
            source_id: Source resource ID
            target_id: Target resource ID  
            max_hops: Maximum hops to search
            
        Returns:
            Dict with network path details or None if no path
            
        Example:
            path = queries.trace_network_path(
                source_id="projects/my-project/zones/us-central1-a/instances/vm-1",
                target_id="projects/my-project/global/networks/vpc-1"
            )
        """
        network_rels = ["USES", "ROUTES_TO", "PART_OF", "CONNECTS_TO", "FORWARDS_TO", "PEERED_WITH"]
        
        return self.find_shortest_path(
            source_id=source_id,
            target_id=target_id,
            relationship_types=network_rels,
            max_depth=max_hops
        )
    
    @track_query_performance("find_resource_clusters")
    def find_resource_clusters(
        self,
        project_id: Optional[str] = None,
        min_cluster_size: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Find clusters of highly connected resources.
        
        Args:
            project_id: Optional filter by project
            min_cluster_size: Minimum resources in a cluster
            
        Returns:
            List of resource clusters
            
        Example:
            clusters = queries.find_resource_clusters(project_id="my-project")
            for cluster in clusters:
                print(f"Cluster size: {cluster['size']}")
        """
        self._validate_positive_int(min_cluster_size, "min_cluster_size")
        
        where_clause = ""
        parameters = {"min_size": min_cluster_size}
        
        if project_id:
            where_clause = "WHERE r.project_id = $project_id"
            parameters["project_id"] = project_id
        
        # This is a simplified cluster finding algorithm
        # In production, consider using graph algorithms like Louvain or Label Propagation
        query = f"""
        MATCH (r)
        {where_clause}
        WITH r
        MATCH (r)-[]->(connected)
        WITH r, collect(DISTINCT connected) AS neighbors
        WHERE size(neighbors) >= $min_size
        RETURN r, neighbors, size(neighbors) AS neighbor_count
        ORDER BY neighbor_count DESC
        LIMIT 50
        """
        
        result = self._execute_query(
            query=query,
            parameters=parameters,
            query_type="resource_clusters"
        )
        
        clusters = []
        for record in result.data:
            center = dict(record['r'])
            neighbors = [dict(n) for n in record['neighbors']]
            
            clusters.append({
                'center': center,
                'members': neighbors,
                'size': record['neighbor_count']
            })
        
        return clusters
    
    @track_query_performance("dependency_depth")
    def calculate_dependency_depth(
        self,
        resource_id: str,
    ) -> Dict[str, Any]:
        """
        Calculate maximum dependency depth for a resource.
        
        Args:
            resource_id: Resource to analyze
            
        Returns:
            Dict with depth information:
            {
                'max_depth': maximum dependency chain length,
                'longest_chain': list of resources in longest chain,
                'leaf_dependencies': resources with no further deps
            }
            
        Example:
            depth_info = queries.calculate_dependency_depth(resource_id="...")
            print(f"Max dependency depth: {depth_info['max_depth']}")
        """
        self._validate_required_params(resource_id=resource_id)
        
        query = """
        MATCH path = (r {id: $resource_id})-[:DEPENDS_ON*]->(dep)
        WHERE NOT (dep)-[:DEPENDS_ON]->()
        WITH path, length(path) AS depth
        ORDER BY depth DESC
        LIMIT 1
        RETURN nodes(path) AS longest_chain, depth AS max_depth
        """
        
        result = self._execute_single_result_query(
            query=query,
            parameters={"resource_id": resource_id},
            query_type="dependency_depth"
        )
        
        if not result:
            return {
                'max_depth': 0,
                'longest_chain': [],
                'leaf_dependencies': []
            }
        
        chain = [dict(node) for node in result['longest_chain']]
        
        # Get leaf dependencies (resources with no further dependencies)
        leaf_query = """
        MATCH (r {id: $resource_id})-[:DEPENDS_ON*]->(leaf)
        WHERE NOT (leaf)-[:DEPENDS_ON]->()
        RETURN DISTINCT leaf
        """
        
        leaf_result = self._execute_query(
            query=leaf_query,
            parameters={"resource_id": resource_id},
            query_type="leaf_dependencies"
        )
        
        leaves = [dict(record['leaf']) for record in leaf_result.data]
        
        return {
            'max_depth': result['max_depth'],
            'longest_chain': chain,
            'leaf_dependencies': leaves
        }


# Singleton instance
_traversal_queries_instance: Optional[TraversalQueries] = None


def get_traversal_queries(
    connection_manager=None,
    enable_monitoring: bool = True,
) -> TraversalQueries:
    """
    Get or create singleton TraversalQueries instance.
    
    Args:
        connection_manager: Optional connection manager
        enable_monitoring: Whether to enable monitoring
        
    Returns:
        TraversalQueries instance
    """
    global _traversal_queries_instance
    
    if _traversal_queries_instance is None:
        _traversal_queries_instance = TraversalQueries(
            connection_manager=connection_manager,
            enable_monitoring=enable_monitoring,
        )
    
    return _traversal_queries_instance

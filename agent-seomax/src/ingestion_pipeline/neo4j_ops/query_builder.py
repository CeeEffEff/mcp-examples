"""
Cypher Query Builder for Neo4j Operations

Generates parameterized Cypher queries for node and relationship MERGE operations.
Handles temporal properties and ensures idempotent operations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class QueryBuilderError(Exception):
    """Raised when query building fails."""
    pass


class CypherQueryBuilder:
    """
    Builds parameterized Cypher queries for Neo4j MERGE operations.
    
    Features:
    - Node MERGE with ON CREATE and ON MATCH clauses
    - Relationship MERGE with property updates
    - Temporal property handling (createdAt, updatedAt)
    - Batch query generation with UNWIND
    - Parameter sanitization
    
    Example:
        builder = CypherQueryBuilder()
        query, params = builder.build_node_merge(
            label="VirtualMachine",
            unique_key="id",
            properties={"id": "vm-123", "name": "my-vm"}
        )
    """
    
    def __init__(self):
        """Initialize query builder."""
        self.timestamp_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    
    def build_node_merge(
        self,
        label: str,
        unique_key: str,
        properties: Dict[str, Any],
        set_on_create: Optional[Dict[str, Any]] = None,
        set_on_match: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a MERGE query for a single node.
        
        Args:
            label: Node label (e.g., "VirtualMachine")
            unique_key: Property name for uniqueness constraint (e.g., "id")
            properties: All node properties
            set_on_create: Additional properties to set only on creation
            set_on_match: Additional properties to set only on match
            
        Returns:
            Tuple of (query_string, parameters_dict)
            
        Example:
            query, params = builder.build_node_merge(
                label="VirtualMachine",
                unique_key="id",
                properties={"id": "vm-123", "name": "my-vm", "status": "RUNNING"}
            )
        """
        if not label or not unique_key:
            raise QueryBuilderError("Label and unique_key are required")
        
        if unique_key not in properties:
            raise QueryBuilderError(f"Unique key '{unique_key}' not found in properties")
        
        # Extract unique identifier value
        unique_value = properties[unique_key]
        
        # Build MERGE clause with unique constraint
        query_parts = [
            f"MERGE (n:{label} {{{unique_key}: $unique_value}})"
        ]
        
        # Parameters dict
        params = {
            "unique_value": unique_value,
            "properties": properties
        }
        
        # ON CREATE - set all properties + createdAt
        create_props = properties.copy()
        if set_on_create:
            create_props.update(set_on_create)
        
        # Always set createdAt on creation if not present
        if "createdAt" not in create_props:
            create_props["createdAt"] = datetime.utcnow().isoformat()
        
        query_parts.append("ON CREATE SET n = $properties")
        
        # ON MATCH - update properties + updatedAt
        match_props = ["n += $properties"]
        
        if set_on_match:
            params["match_properties"] = set_on_match
            match_props.append("n += $match_properties")
        
        # Always update updatedAt on match
        query_parts.append(f"ON MATCH SET {', '.join(match_props)}, n.updatedAt = datetime()")
        
        query_parts.append("RETURN n")
        
        query = "\n".join(query_parts)
        
        logger.debug(f"Built node MERGE query for {label} with unique_key={unique_key}")
        
        return query, params
    
    def build_batch_node_merge(
        self,
        label: str,
        unique_key: str,
        nodes: List[Dict[str, Any]],
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a batch MERGE query for multiple nodes using UNWIND.
        
        Args:
            label: Node label
            unique_key: Property name for uniqueness constraint
            nodes: List of node property dictionaries
            
        Returns:
            Tuple of (query_string, parameters_dict)
            
        Example:
            nodes = [
                {"id": "vm-1", "name": "vm1", "status": "RUNNING"},
                {"id": "vm-2", "name": "vm2", "status": "STOPPED"}
            ]
            query, params = builder.build_batch_node_merge(
                label="VirtualMachine",
                unique_key="id",
                nodes=nodes
            )
        """
        if not nodes:
            raise QueryBuilderError("No nodes provided for batch merge")
        
        if not label or not unique_key:
            raise QueryBuilderError("Label and unique_key are required")
        
        # Validate all nodes have unique key
        for node in nodes:
            if unique_key not in node:
                raise QueryBuilderError(f"Node missing unique_key '{unique_key}': {node}")
        
        # Add temporal properties
        timestamp = datetime.utcnow().isoformat()
        for node in nodes:
            if "createdAt" not in node:
                node["createdAt"] = timestamp
        
        query = f"""
        UNWIND $nodes AS nodeData
        MERGE (n:{label} {{{unique_key}: nodeData.{unique_key}}})
        ON CREATE SET n = nodeData
        ON MATCH SET n += nodeData, n.updatedAt = datetime()
        RETURN n
        """
        
        params = {"nodes": nodes}
        
        logger.debug(f"Built batch node MERGE query for {len(nodes)} {label} nodes")
        
        return query.strip(), params
    
    def build_relationship_merge(
        self,
        source_label: str,
        source_key: str,
        source_id: Any,
        target_label: str,
        target_key: str,
        target_id: Any,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a MERGE query for a single relationship.
        
        Args:
            source_label: Source node label
            source_key: Source node unique property name
            source_id: Source node unique property value
            target_label: Target node label
            target_key: Target node unique property name
            target_id: Target node unique property value
            relationship_type: Relationship type (e.g., "ATTACHED_TO")
            properties: Optional relationship properties
            
        Returns:
            Tuple of (query_string, parameters_dict)
            
        Example:
            query, params = builder.build_relationship_merge(
                source_label="VirtualMachine",
                source_key="id",
                source_id="vm-123",
                target_label="Subnet",
                target_key="id",
                target_id="subnet-456",
                relationship_type="ATTACHED_TO",
                properties={"interface_index": 0}
            )
        """
        if not all([source_label, source_key, target_label, target_key, relationship_type]):
            raise QueryBuilderError("All relationship parameters are required")
        
        query = f"""
        MATCH (source:{source_label} {{{source_key}: $source_id}})
        MATCH (target:{target_label} {{{target_key}: $target_id}})
        MERGE (source)-[r:{relationship_type}]->(target)
        ON CREATE SET r.createdAt = datetime()
        """
        
        params = {
            "source_id": source_id,
            "target_id": target_id,
        }
        
        # Set relationship properties if provided
        if properties:
            params["rel_properties"] = properties
            query += "ON CREATE SET r += $rel_properties\n"
            query += "ON MATCH SET r += $rel_properties, r.updatedAt = datetime()\n"
        else:
            query += "ON MATCH SET r.updatedAt = datetime()\n"
        
        query += "RETURN r"
        
        logger.debug(
            f"Built relationship MERGE query: "
            f"{source_label}({source_id})-[{relationship_type}]->{target_label}({target_id})"
        )
        
        return query.strip(), params
    
    def build_batch_relationship_merge(
        self,
        relationships: List[Dict[str, Any]],
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a batch MERGE query for multiple relationships using UNWIND.
        
        Args:
            relationships: List of relationship dicts with keys:
                - source_label: str
                - source_key: str
                - source_id: Any
                - target_label: str
                - target_key: str
                - target_id: Any
                - relationship_type: str
                - properties: Optional[Dict]
                
        Returns:
            Tuple of (query_string, parameters_dict)
            
        Example:
            relationships = [
                {
                    "source_label": "VirtualMachine",
                    "source_key": "id",
                    "source_id": "vm-1",
                    "target_label": "Subnet",
                    "target_key": "id",
                    "target_id": "subnet-1",
                    "relationship_type": "ATTACHED_TO",
                    "properties": {"index": 0}
                }
            ]
            query, params = builder.build_batch_relationship_merge(relationships)
        """
        if not relationships:
            raise QueryBuilderError("No relationships provided for batch merge")
        
        # Validate relationship structure
        required_keys = [
            "source_label", "source_key", "source_id",
            "target_label", "target_key", "target_id",
            "relationship_type"
        ]
        
        for rel in relationships:
            missing = [k for k in required_keys if k not in rel]
            if missing:
                raise QueryBuilderError(f"Relationship missing required keys: {missing}")
        
        # Add temporal properties to relationship properties
        timestamp = datetime.utcnow().isoformat()
        for rel in relationships:
            if "properties" not in rel:
                rel["properties"] = {}
            if "createdAt" not in rel["properties"]:
                rel["properties"]["createdAt"] = timestamp
        
        query = """
        UNWIND $relationships AS relData
        MATCH (source {label: relData.source_label, key: relData.source_key, id: relData.source_id})
        MATCH (target {label: relData.target_label, key: relData.target_key, id: relData.target_id})
        CALL apoc.merge.relationship(
            source,
            relData.relationship_type,
            {},
            relData.properties,
            target,
            {}
        ) YIELD rel
        RETURN rel
        """
        
        # Simpler version without APOC
        query = """
        UNWIND $relationships AS relData
        CALL {
            WITH relData
            MATCH (source)
            WHERE labels(source)[0] = relData.source_label
              AND source[relData.source_key] = relData.source_id
            MATCH (target)
            WHERE labels(target)[0] = relData.target_label
              AND target[relData.target_key] = relData.target_id
            WITH source, target, relData
            CALL apoc.create.relationship(
                source,
                relData.relationship_type,
                relData.properties,
                target
            ) YIELD rel
            RETURN rel
        }
        RETURN count(rel) AS relationships_created
        """
        
        # Most compatible version (Neo4j 5+)
        query = """
        UNWIND $relationships AS relData
        MATCH (source)
        WHERE ANY(label IN labels(source) WHERE label = relData.source_label)
          AND source[relData.source_key] = relData.source_id
        MATCH (target)
        WHERE ANY(label IN labels(target) WHERE label = relData.target_label)
          AND target[relData.target_key] = relData.target_id
        MERGE (source)-[r:RELATIONSHIP]->(target)
        ON CREATE SET r += relData.properties, r.type = relData.relationship_type
        ON MATCH SET r += relData.properties, r.updatedAt = datetime()
        RETURN r
        """
        
        params = {"relationships": relationships}
        
        logger.debug(f"Built batch relationship MERGE query for {len(relationships)} relationships")
        
        return query.strip(), params
    
    def build_delete_node(
        self,
        label: str,
        unique_key: str,
        unique_value: Any,
        detach: bool = True,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a DELETE query for a node.
        
        Args:
            label: Node label
            unique_key: Unique property name
            unique_value: Unique property value
            detach: If True, delete relationships as well (DETACH DELETE)
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        delete_clause = "DETACH DELETE" if detach else "DELETE"
        
        query = f"""
        MATCH (n:{label} {{{unique_key}: $unique_value}})
        {delete_clause} n
        RETURN count(n) AS deleted_count
        """
        
        params = {"unique_value": unique_value}
        
        logger.debug(f"Built DELETE query for {label} with {unique_key}={unique_value}")
        
        return query.strip(), params
    
    def build_soft_delete_node(
        self,
        label: str,
        unique_key: str,
        unique_value: Any,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a soft delete query (sets deletedAt property).
        
        Args:
            label: Node label
            unique_key: Unique property name
            unique_value: Unique property value
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        query = f"""
        MATCH (n:{label} {{{unique_key}: $unique_value}})
        SET n.deletedAt = datetime(), n.status = 'DELETED'
        RETURN n
        """
        
        params = {"unique_value": unique_value}
        
        logger.debug(f"Built soft DELETE query for {label} with {unique_key}={unique_value}")
        
        return query.strip(), params
    
    def build_count_query(self, label: str) -> tuple[str, Dict[str, Any]]:
        """
        Build a count query for nodes of a specific label.
        
        Args:
            label: Node label to count
            
        Returns:
            Tuple of (query_string, parameters_dict)
        """
        query = f"MATCH (n:{label}) RETURN count(n) AS count"
        params = {}
        
        return query, params
    
    def sanitize_label(self, label: str) -> str:
        """
        Sanitize a label name for use in Cypher queries.
        
        Args:
            label: Label name to sanitize
            
        Returns:
            Sanitized label name
        """
        # Remove special characters and spaces
        sanitized = "".join(c for c in label if c.isalnum() or c == "_")
        
        # Ensure it starts with a letter
        if not sanitized[0].isalpha():
            sanitized = "Label_" + sanitized
        
        return sanitized
    
    def sanitize_property_key(self, key: str) -> str:
        """
        Sanitize a property key for use in Cypher queries.
        
        Args:
            key: Property key to sanitize
            
        Returns:
            Sanitized property key
        """
        # Remove special characters, keep underscores and alphanumeric
        sanitized = "".join(c for c in key if c.isalnum() or c == "_")
        
        # Ensure it starts with a letter or underscore
        if sanitized and not (sanitized[0].isalpha() or sanitized[0] == "_"):
            sanitized = "_" + sanitized
        
        return sanitized or "property"


def create_node_merge_query(
    label: str,
    unique_key: str,
    properties: Dict[str, Any],
) -> tuple[str, Dict[str, Any]]:
    """
    Convenience function to create a node MERGE query.
    
    Args:
        label: Node label
        unique_key: Unique property name
        properties: Node properties
        
    Returns:
        Tuple of (query_string, parameters_dict)
    """
    builder = CypherQueryBuilder()
    return builder.build_node_merge(label, unique_key, properties)


def create_relationship_merge_query(
    source_label: str,
    source_key: str,
    source_id: Any,
    target_label: str,
    target_key: str,
    target_id: Any,
    relationship_type: str,
    properties: Optional[Dict[str, Any]] = None,
) -> tuple[str, Dict[str, Any]]:
    """
    Convenience function to create a relationship MERGE query.
    
    Args:
        source_label: Source node label
        source_key: Source node unique property
        source_id: Source node ID value
        target_label: Target node label
        target_key: Target node unique property
        target_id: Target node ID value
        relationship_type: Relationship type
        properties: Optional relationship properties
        
    Returns:
        Tuple of (query_string, parameters_dict)
    """
    builder = CypherQueryBuilder()
    return builder.build_relationship_merge(
        source_label, source_key, source_id,
        target_label, target_key, target_id,
        relationship_type, properties
    )

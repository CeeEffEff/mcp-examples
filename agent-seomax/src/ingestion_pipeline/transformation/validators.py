"""
Data validation utilities for GCP resource transformations.

Provides validation logic to ensure transformed data meets
Neo4j schema requirements before insertion.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

import structlog
from pydantic import ValidationError

from .schemas import (
    ComputeInstanceSchema,
    PersistentDiskSchema,
    VPCNetworkSchema,
    SubnetSchema,
    BaseRelationshipSchema,
    TransformationResult
)

logger = structlog.get_logger(__name__)


class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass


class ResourceValidator:
    """
    Validates transformed resource data against schemas.
    
    Ensures data integrity before Neo4j insertion.
    """
    
    def __init__(self):
        """Initialize the validator."""
        self.logger = logger.bind(component="ResourceValidator")
        
        # Schema mapping
        self._schemas = {
            'ComputeInstance': ComputeInstanceSchema,
            'PersistentDisk': PersistentDiskSchema,
            'VPCNetwork': VPCNetworkSchema,
            'Subnet': SubnetSchema,
        }
    
    def validate_node(
        self,
        node_data: Dict[str, Any],
        node_label: str
    ) -> bool:
        """
        Validate node data against its schema.
        
        Args:
            node_data: Node data dictionary
            node_label: Node label (e.g., "ComputeInstance")
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        schema_class = self._schemas.get(node_label)
        
        if not schema_class:
            self.logger.warning(
                "No schema found for node label",
                node_label=node_label
            )
            # Allow unknown labels to pass (for future expansion)
            return True
        
        try:
            # Validate using pydantic schema
            schema_class(**node_data)
            return True
            
        except ValidationError as e:
            self.logger.error(
                "Node validation failed",
                node_label=node_label,
                errors=e.errors()
            )
            raise ValidationError(f"Node validation failed: {e}")
    
    def validate_relationship(
        self,
        relationship: Dict[str, Any]
    ) -> bool:
        """
        Validate relationship data.
        
        Args:
            relationship: Relationship dictionary
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate using base relationship schema
            BaseRelationshipSchema(**relationship)
            return True
            
        except ValidationError as e:
            self.logger.error(
                "Relationship validation failed",
                errors=e.errors()
            )
            raise ValidationError(f"Relationship validation failed: {e}")
    
    def validate_transformation_result(
        self,
        result: TransformationResult
    ) -> bool:
        """
        Validate complete transformation result.
        
        Args:
            result: TransformationResult object
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate node
        self.validate_node(result.node, result.node_label)
        
        # Validate all relationships
        for relationship in result.relationships:
            self.validate_relationship(relationship)
        
        return True
    
    def validate_batch(
        self,
        results: List[TransformationResult]
    ) -> Dict[str, Any]:
        """
        Validate a batch of transformation results.
        
        Args:
            results: List of TransformationResult objects
            
        Returns:
            Validation summary dictionary
        """
        valid_count = 0
        invalid_count = 0
        errors = []
        
        for i, result in enumerate(results):
            try:
                self.validate_transformation_result(result)
                valid_count += 1
            except ValidationError as e:
                invalid_count += 1
                errors.append({
                    'index': i,
                    'resource_id': result.resource_id,
                    'error': str(e)
                })
                self.logger.error(
                    "Validation failed for result",
                    index=i,
                    resource_id=result.resource_id,
                    error=str(e)
                )
        
        return {
            'total': len(results),
            'valid': valid_count,
            'invalid': invalid_count,
            'errors': errors
        }


class SchemaComplianceChecker:
    """
    Checks data compliance with Neo4j schema requirements.
    """
    
    def __init__(self):
        """Initialize the compliance checker."""
        self.logger = logger.bind(component="SchemaComplianceChecker")
    
    def check_required_fields(
        self,
        node_data: Dict[str, Any],
        required_fields: List[str]
    ) -> List[str]:
        """
        Check for required fields in node data.
        
        Args:
            node_data: Node data dictionary
            required_fields: List of required field names
            
        Returns:
            List of missing field names
        """
        missing = []
        
        for field in required_fields:
            if field not in node_data or node_data[field] is None:
                missing.append(field)
        
        return missing
    
    def check_temporal_properties(
        self,
        node_data: Dict[str, Any]
    ) -> bool:
        """
        Check temporal properties are present and valid.
        
        Args:
            node_data: Node data dictionary
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If temporal properties are invalid
        """
        required_temporal = ['createdAt', 'updatedAt', 'snapshotTimestamp']
        missing = self.check_required_fields(node_data, required_temporal)
        
        if missing:
            raise ValidationError(f"Missing temporal properties: {missing}")
        
        # Validate datetime types
        for field in required_temporal:
            value = node_data[field]
            if not isinstance(value, datetime):
                raise ValidationError(
                    f"Temporal property '{field}' must be datetime, got {type(value)}"
                )
        
        # Check logical consistency
        created = node_data['createdAt']
        updated = node_data['updatedAt']
        
        if updated < created:
            raise ValidationError(
                f"updatedAt ({updated}) cannot be before createdAt ({created})"
            )
        
        return True
    
    def check_gcp_standard_properties(
        self,
        node_data: Dict[str, Any]
    ) -> bool:
        """
        Check GCP standard properties are present.
        
        Args:
            node_data: Node data dictionary
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If standard properties are invalid
        """
        required_gcp = ['gcpId', 'gcpSelfLink', 'resourceType', 'projectId']
        missing = self.check_required_fields(node_data, required_gcp)
        
        if missing:
            raise ValidationError(f"Missing GCP standard properties: {missing}")
        
        return True
    
    def check_relationship_integrity(
        self,
        relationship: Dict[str, Any]
    ) -> bool:
        """
        Check relationship integrity.
        
        Args:
            relationship: Relationship dictionary
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If relationship is invalid
        """
        required = ['sourceId', 'targetId', 'relationshipType']
        
        for field in required:
            if field not in relationship or not relationship[field]:
                raise ValidationError(f"Missing required relationship field: {field}")
        
        # Check source and target are different (no self-relationships for most types)
        if relationship['sourceId'] == relationship['targetId']:
            # Allow some relationship types to be self-referential
            allowed_self_ref = ['PART_OF', 'DEPENDS_ON']
            if relationship['relationshipType'] not in allowed_self_ref:
                self.logger.warning(
                    "Self-referential relationship detected",
                    relationship_type=relationship['relationshipType'],
                    resource_id=relationship['sourceId']
                )
        
        return True


class DataIntegrityValidator:
    """
    Validates data integrity across nodes and relationships.
    """
    
    def __init__(self):
        """Initialize the integrity validator."""
        self.logger = logger.bind(component="DataIntegrityValidator")
    
    def validate_reference_integrity(
        self,
        nodes: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate that all relationship references point to existing nodes.
        
        Args:
            nodes: List of node dictionaries
            relationships: List of relationship dictionaries
            
        Returns:
            Validation report dictionary
        """
        # Build set of node IDs
        node_ids = {node.get('gcpId') for node in nodes if node.get('gcpId')}
        
        # Check relationship references
        missing_sources = []
        missing_targets = []
        valid_count = 0
        
        for rel in relationships:
            source_id = rel.get('sourceId')
            target_id = rel.get('targetId')
            
            source_exists = source_id in node_ids
            target_exists = target_id in node_ids
            
            if not source_exists:
                missing_sources.append({
                    'relationship_type': rel.get('relationshipType'),
                    'source_id': source_id,
                    'target_id': target_id
                })
            
            if not target_exists:
                missing_targets.append({
                    'relationship_type': rel.get('relationshipType'),
                    'source_id': source_id,
                    'target_id': target_id
                })
            
            if source_exists and target_exists:
                valid_count += 1
        
        return {
            'total_relationships': len(relationships),
            'valid_relationships': valid_count,
            'missing_sources': len(missing_sources),
            'missing_targets': len(missing_targets),
            'missing_source_details': missing_sources[:10],  # Limit to first 10
            'missing_target_details': missing_targets[:10]
        }
    
    def check_duplicate_nodes(
        self,
        nodes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check for duplicate nodes based on gcpId.
        
        Args:
            nodes: List of node dictionaries
            
        Returns:
            Duplicate report dictionary
        """
        seen_ids = {}
        duplicates = []
        
        for i, node in enumerate(nodes):
            node_id = node.get('gcpId')
            
            if node_id in seen_ids:
                duplicates.append({
                    'node_id': node_id,
                    'first_index': seen_ids[node_id],
                    'duplicate_index': i
                })
            else:
                seen_ids[node_id] = i
        
        return {
            'total_nodes': len(nodes),
            'unique_nodes': len(seen_ids),
            'duplicates': len(duplicates),
            'duplicate_details': duplicates[:10]
        }
    
    def validate_data_types(
        self,
        node_data: Dict[str, Any]
    ) -> List[str]:
        """
        Validate data types of node properties.
        
        Args:
            node_data: Node data dictionary
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check string fields
        string_fields = ['gcpId', 'gcpSelfLink', 'resourceType', 'projectId', 'name']
        for field in string_fields:
            if field in node_data and node_data[field] is not None:
                if not isinstance(node_data[field], str):
                    errors.append(f"Field '{field}' must be string, got {type(node_data[field])}")
        
        # Check dict fields
        dict_fields = ['labels', 'metadata']
        for field in dict_fields:
            if field in node_data and node_data[field] is not None:
                if not isinstance(node_data[field], dict):
                    errors.append(f"Field '{field}' must be dict, got {type(node_data[field])}")
        
        # Check list fields
        list_fields = ['tags', 'disks', 'networkInterfaces']
        for field in list_fields:
            if field in node_data and node_data[field] is not None:
                if not isinstance(node_data[field], list):
                    errors.append(f"Field '{field}' must be list, got {type(node_data[field])}")
        
        # Check datetime fields
        datetime_fields = ['createdAt', 'updatedAt', 'snapshotTimestamp']
        for field in datetime_fields:
            if field in node_data and node_data[field] is not None:
                if not isinstance(node_data[field], datetime):
                    errors.append(f"Field '{field}' must be datetime, got {type(node_data[field])}")
        
        return errors

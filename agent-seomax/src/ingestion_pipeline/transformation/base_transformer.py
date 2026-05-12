"""
Base transformer abstract class for GCP resource transformations.

Defines the interface and common functionality for transforming
GCP API responses into Neo4j-compatible format.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

import structlog

from .schemas import TransformationResult

logger = structlog.get_logger(__name__)


class TransformationError(Exception):
    """Exception raised when transformation fails."""
    pass


class BaseTransformer(ABC):
    """
    Abstract base class for GCP resource transformers.
    
    All resource-specific transformers must inherit from this class
    and implement the required abstract methods.
    """
    
    def __init__(self):
        """Initialize the transformer."""
        self.logger = logger.bind(transformer=self.__class__.__name__)
    
    @abstractmethod
    def get_resource_type(self) -> str:
        """
        Get the GCP resource type this transformer handles.
        
        Returns:
            Resource type string (e.g., "compute.instances")
        """
        pass
    
    @abstractmethod
    def get_node_label(self) -> str:
        """
        Get the Neo4j node label for this resource type.
        
        Returns:
            Node label (e.g., "ComputeInstance")
        """
        pass
    
    @abstractmethod
    def transform(
        self,
        resource_data: Dict[str, Any],
        snapshot_timestamp: Optional[datetime] = None
    ) -> TransformationResult:
        """
        Transform GCP resource data into Neo4j format.
        
        Args:
            resource_data: Raw GCP resource data
            snapshot_timestamp: Optional timestamp for this snapshot
            
        Returns:
            TransformationResult containing node and relationships
            
        Raises:
            TransformationError: If transformation fails
        """
        pass
    
    def transform_batch(
        self,
        resources: List[Dict[str, Any]],
        snapshot_timestamp: Optional[datetime] = None
    ) -> List[TransformationResult]:
        """
        Transform a batch of resources.
        
        Args:
            resources: List of raw GCP resource data
            snapshot_timestamp: Optional timestamp for this snapshot
            
        Returns:
            List of TransformationResult objects
        """
        results = []
        errors = []
        
        for i, resource in enumerate(resources):
            try:
                result = self.transform(resource, snapshot_timestamp)
                results.append(result)
            except Exception as e:
                self.logger.error(
                    "Failed to transform resource",
                    resource_index=i,
                    error=str(e),
                    resource_id=resource.get('id', 'unknown')
                )
                errors.append({
                    'index': i,
                    'resource_id': resource.get('id', 'unknown'),
                    'error': str(e)
                })
        
        if errors:
            self.logger.warning(
                "Batch transformation completed with errors",
                total=len(resources),
                successful=len(results),
                failed=len(errors)
            )
        
        return results
    
    def _convert_snake_to_camel(self, snake_str: str) -> str:
        """
        Convert snake_case to camelCase.
        
        Args:
            snake_str: String in snake_case
            
        Returns:
            String in camelCase
        """
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def _transform_keys_to_camel_case(
        self,
        data: Dict[str, Any],
        exclude_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Transform dictionary keys from snake_case to camelCase.
        
        Args:
            data: Dictionary with snake_case keys
            exclude_keys: Keys to exclude from transformation
            
        Returns:
            Dictionary with camelCase keys
        """
        exclude_keys = exclude_keys or []
        result = {}
        
        for key, value in data.items():
            if key in exclude_keys:
                new_key = key
            else:
                new_key = self._convert_snake_to_camel(key)
            
            # Recursively transform nested dictionaries
            if isinstance(value, dict):
                result[new_key] = self._transform_keys_to_camel_case(value, exclude_keys)
            elif isinstance(value, list):
                result[new_key] = [
                    self._transform_keys_to_camel_case(item, exclude_keys)
                    if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[new_key] = value
        
        return result
    
    def _add_temporal_properties(
        self,
        node_data: Dict[str, Any],
        resource_data: Dict[str, Any],
        snapshot_timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Add temporal tracking properties to node data.
        
        Args:
            node_data: Node data dictionary
            resource_data: Original resource data
            snapshot_timestamp: Snapshot timestamp
            
        Returns:
            Node data with temporal properties
        """
        now = datetime.utcnow()
        snapshot_ts = snapshot_timestamp or now
        
        # Parse creation timestamp from resource data
        created_at = self._parse_timestamp(
            resource_data.get('creation_timestamp') or 
            resource_data.get('creationTimestamp')
        ) or now
        
        node_data['createdAt'] = created_at
        node_data['updatedAt'] = now
        node_data['deletedAt'] = None
        node_data['snapshotTimestamp'] = snapshot_ts
        
        return node_data
    
    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """
        Parse timestamp from various formats.
        
        Args:
            timestamp: Timestamp in various formats
            
        Returns:
            datetime object or None
        """
        if timestamp is None:
            return None
        
        if isinstance(timestamp, datetime):
            return timestamp
        
        if isinstance(timestamp, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try RFC3339 format
                    from dateutil import parser
                    return parser.isoparse(timestamp)
                except Exception:
                    self.logger.warning(
                        "Failed to parse timestamp",
                        timestamp=timestamp
                    )
                    return None
        
        return None
    
    def _extract_resource_id(self, resource_data: Dict[str, Any]) -> str:
        """
        Extract resource ID from resource data.
        
        Args:
            resource_data: Resource data dictionary
            
        Returns:
            Resource ID
            
        Raises:
            TransformationError: If ID cannot be extracted
        """
        # Try various ID fields
        for id_field in ['id', 'self_link', 'selfLink', 'name']:
            if id_field in resource_data:
                return str(resource_data[id_field])
        
        raise TransformationError("Cannot extract resource ID from data")
    
    def _extract_project_id(self, resource_data: Dict[str, Any]) -> str:
        """
        Extract project ID from resource data.
        
        Args:
            resource_data: Resource data dictionary
            
        Returns:
            Project ID
        """
        # Check explicit project_id field
        if 'project_id' in resource_data:
            return resource_data['project_id']
        
        if 'projectId' in resource_data:
            return resource_data['projectId']
        
        # Extract from self_link
        self_link = resource_data.get('self_link') or resource_data.get('selfLink', '')
        if 'projects/' in self_link:
            parts = self_link.split('projects/')
            if len(parts) > 1:
                project_part = parts[1].split('/')[0]
                return project_part
        
        # Extract from ID if it contains project
        resource_id = resource_data.get('id', '')
        if 'projects/' in resource_id:
            parts = resource_id.split('projects/')
            if len(parts) > 1:
                project_part = parts[1].split('/')[0]
                return project_part
        
        return "unknown"
    
    def _create_base_node_data(
        self,
        resource_data: Dict[str, Any],
        snapshot_timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create base node data with standard properties.
        
        Args:
            resource_data: Resource data dictionary
            snapshot_timestamp: Snapshot timestamp
            
        Returns:
            Base node data dictionary
        """
        node_data = {}
        
        # Add standard properties
        node_data['gcpId'] = self._extract_resource_id(resource_data)
        node_data['gcpSelfLink'] = (
            resource_data.get('self_link') or 
            resource_data.get('selfLink') or 
            node_data['gcpId']
        )
        node_data['resourceType'] = self.get_resource_type()
        node_data['projectId'] = self._extract_project_id(resource_data)
        
        # Add labels and description
        node_data['labels'] = resource_data.get('labels', {})
        node_data['description'] = resource_data.get('description')
        
        # Add temporal properties
        self._add_temporal_properties(node_data, resource_data, snapshot_timestamp)
        
        return node_data
    
    def _create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a relationship dictionary.
        
        Args:
            source_id: Source node gcpId
            target_id: Target node gcpId
            relationship_type: Relationship type (e.g., "ATTACHED_TO")
            properties: Additional relationship properties
            
        Returns:
            Relationship dictionary
        """
        now = datetime.utcnow()
        
        relationship = {
            'sourceId': source_id,
            'targetId': target_id,
            'relationshipType': relationship_type,
            'createdAt': now,
            'updatedAt': now,
            'deletedAt': None,
            'metadata': {}
        }
        
        if properties:
            relationship.update(properties)
        
        return relationship
    
    def validate_required_fields(
        self,
        resource_data: Dict[str, Any],
        required_fields: List[str]
    ) -> None:
        """
        Validate that required fields are present.
        
        Args:
            resource_data: Resource data dictionary
            required_fields: List of required field names
            
        Raises:
            TransformationError: If required fields are missing
        """
        missing_fields = []
        
        for field in required_fields:
            if field not in resource_data or resource_data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise TransformationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

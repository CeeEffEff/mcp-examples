"""
Relationship extraction utilities for GCP resources.

Provides centralized logic for extracting and managing relationships
between different GCP resources in the digital twin.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


class RelationshipExtractor:
    """
    Extracts relationships between GCP resources.
    
    Provides utilities for identifying and creating relationships
    based on resource references and dependencies.
    """
    
    def __init__(self):
        """Initialize the relationship extractor."""
        self.logger = logger.bind(component="RelationshipExtractor")
    
    def extract_network_relationships(
        self,
        resource_id: str,
        network_interfaces: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract network-related relationships.
        
        Args:
            resource_id: Source resource ID
            network_interfaces: List of network interface configurations
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        for idx, interface in enumerate(network_interfaces):
            # ATTACHED_TO Subnet
            subnetwork = interface.get('subnetwork') or interface.get('subnetworkRef')
            if subnetwork:
                rel = self._create_network_attachment_relationship(
                    source_id=resource_id,
                    subnet_id=subnetwork,
                    interface_index=idx,
                    interface_config=interface
                )
                relationships.append(rel)
            
            # Extract VPC network reference
            network = interface.get('network') or interface.get('networkRef')
            if network and not subnetwork:
                # Direct network attachment (legacy/auto-mode)
                rel = self._create_relationship(
                    source_id=resource_id,
                    target_id=network,
                    relationship_type='ATTACHED_TO',
                    properties={'interfaceIndex': idx}
                )
                relationships.append(rel)
        
        return relationships
    
    def extract_disk_relationships(
        self,
        resource_id: str,
        disks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract disk-related relationships.
        
        Args:
            resource_id: Source resource ID (instance)
            disks: List of disk configurations
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        for disk in disks:
            disk_source = disk.get('source') or disk.get('sourceRef')
            if disk_source:
                rel = self._create_disk_usage_relationship(
                    instance_id=resource_id,
                    disk_id=disk_source,
                    disk_config=disk
                )
                relationships.append(rel)
        
        return relationships
    
    def extract_hierarchy_relationships(
        self,
        child_id: str,
        parent_id: str,
        relationship_type: str = 'PART_OF'
    ) -> Dict[str, Any]:
        """
        Extract hierarchical parent-child relationships.
        
        Args:
            child_id: Child resource ID
            parent_id: Parent resource ID
            relationship_type: Type of hierarchy relationship
            
        Returns:
            Relationship dictionary
        """
        return self._create_relationship(
            source_id=child_id,
            target_id=parent_id,
            relationship_type=relationship_type
        )
    
    def extract_service_account_relationships(
        self,
        resource_id: str,
        service_accounts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract service account usage relationships.
        
        Args:
            resource_id: Source resource ID
            service_accounts: List of service account configurations
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        for sa in service_accounts:
            email = sa.get('email')
            if email:
                rel = self._create_relationship(
                    source_id=resource_id,
                    target_id=email,  # Use email as service account identifier
                    relationship_type='USES_SERVICE_ACCOUNT',
                    properties={
                        'scopes': sa.get('scopes', []),
                        'email': email
                    }
                )
                relationships.append(rel)
        
        return relationships
    
    def extract_encryption_relationships(
        self,
        resource_id: str,
        encryption_config: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract encryption key relationships.
        
        Args:
            resource_id: Source resource ID
            encryption_config: Encryption configuration
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        if not encryption_config:
            return relationships
        
        kms_key = encryption_config.get('kmsKeyName') or encryption_config.get('keyName')
        if kms_key:
            rel = self._create_relationship(
                source_id=resource_id,
                target_id=kms_key,
                relationship_type='ENCRYPTED_BY',
                properties={
                    'keyVersion': encryption_config.get('keyVersion')
                }
            )
            relationships.append(rel)
        
        return relationships
    
    def extract_source_relationships(
        self,
        resource_id: str,
        source_snapshot: Optional[str] = None,
        source_image: Optional[str] = None,
        source_disk: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract source/origin relationships.
        
        Args:
            resource_id: Target resource ID
            source_snapshot: Source snapshot reference
            source_image: Source image reference
            source_disk: Source disk reference
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        if source_snapshot:
            rel = self._create_relationship(
                source_id=resource_id,
                target_id=source_snapshot,
                relationship_type='CREATED_FROM',
                properties={'sourceType': 'SNAPSHOT'}
            )
            relationships.append(rel)
        
        if source_image:
            rel = self._create_relationship(
                source_id=resource_id,
                target_id=source_image,
                relationship_type='CREATED_FROM',
                properties={'sourceType': 'IMAGE'}
            )
            relationships.append(rel)
        
        if source_disk:
            rel = self._create_relationship(
                source_id=resource_id,
                target_id=source_disk,
                relationship_type='SNAPSHOT_OF',
                properties={'sourceType': 'DISK'}
            )
            relationships.append(rel)
        
        return relationships
    
    def deduplicate_relationships(
        self,
        relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate relationships.
        
        Args:
            relationships: List of relationship dictionaries
            
        Returns:
            Deduplicated list of relationships
        """
        seen: Set[tuple] = set()
        unique_relationships = []
        
        for rel in relationships:
            # Create unique key from source, target, and type
            key = (
                rel.get('sourceId'),
                rel.get('targetId'),
                rel.get('relationshipType')
            )
            
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)
            else:
                self.logger.debug(
                    "Skipping duplicate relationship",
                    source=rel.get('sourceId'),
                    target=rel.get('targetId'),
                    type=rel.get('relationshipType')
                )
        
        return unique_relationships
    
    def validate_relationship(
        self,
        relationship: Dict[str, Any]
    ) -> bool:
        """
        Validate relationship has required fields.
        
        Args:
            relationship: Relationship dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['sourceId', 'targetId', 'relationshipType']
        
        for field in required_fields:
            if field not in relationship or not relationship[field]:
                self.logger.warning(
                    "Invalid relationship missing required field",
                    field=field,
                    relationship=relationship
                )
                return False
        
        return True
    
    def filter_valid_relationships(
        self,
        relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter out invalid relationships.
        
        Args:
            relationships: List of relationship dictionaries
            
        Returns:
            List of valid relationships
        """
        return [rel for rel in relationships if self.validate_relationship(rel)]
    
    def _create_network_attachment_relationship(
        self,
        source_id: str,
        subnet_id: str,
        interface_index: int,
        interface_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create ATTACHED_TO relationship with network interface details."""
        return self._create_relationship(
            source_id=source_id,
            target_id=subnet_id,
            relationship_type='ATTACHED_TO',
            properties={
                'interfaceIndex': interface_index,
                'networkIP': interface_config.get('networkIP', ''),
                'accessConfigs': interface_config.get('accessConfigs', []),
                'aliasIpRanges': interface_config.get('aliasIpRanges', []),
                'nicType': interface_config.get('nicType')
            }
        )
    
    def _create_disk_usage_relationship(
        self,
        instance_id: str,
        disk_id: str,
        disk_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create USES_DISK relationship with disk attachment details."""
        return self._create_relationship(
            source_id=instance_id,
            target_id=disk_id,
            relationship_type='USES_DISK',
            properties={
                'deviceName': disk_config.get('deviceName', ''),
                'boot': disk_config.get('boot', False),
                'autoDelete': disk_config.get('autoDelete', False),
                'mode': disk_config.get('mode', 'READ_WRITE'),
                'interface': disk_config.get('interface')
            }
        )
    
    def _create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a relationship dictionary with standard properties.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            relationship_type: Relationship type
            properties: Additional properties
            
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


class RelationshipMerger:
    """
    Merges and consolidates relationships across multiple sources.
    """
    
    def __init__(self):
        """Initialize the relationship merger."""
        self.logger = logger.bind(component="RelationshipMerger")
    
    def merge_relationships(
        self,
        *relationship_lists: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge multiple lists of relationships.
        
        Args:
            relationship_lists: Variable number of relationship lists
            
        Returns:
            Merged and deduplicated relationship list
        """
        all_relationships = []
        
        for rel_list in relationship_lists:
            all_relationships.extend(rel_list)
        
        # Deduplicate
        extractor = RelationshipExtractor()
        return extractor.deduplicate_relationships(all_relationships)
    
    def group_by_type(
        self,
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group relationships by type.
        
        Args:
            relationships: List of relationship dictionaries
            
        Returns:
            Dictionary mapping relationship types to lists of relationships
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        
        for rel in relationships:
            rel_type = rel.get('relationshipType', 'UNKNOWN')
            if rel_type not in grouped:
                grouped[rel_type] = []
            grouped[rel_type].append(rel)
        
        return grouped
    
    def get_relationship_statistics(
        self,
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistics about relationships.
        
        Args:
            relationships: List of relationship dictionaries
            
        Returns:
            Dictionary with statistics
        """
        grouped = self.group_by_type(relationships)
        
        return {
            'total_relationships': len(relationships),
            'unique_types': len(grouped),
            'by_type': {
                rel_type: len(rels)
                for rel_type, rels in grouped.items()
            }
        }

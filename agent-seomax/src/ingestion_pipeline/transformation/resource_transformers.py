"""
Resource-specific transformers for GCP resources.

Implements concrete transformation logic for different GCP resource types,
converting API responses to Neo4j-compatible format with relationships.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

import structlog

from .base_transformer import BaseTransformer, TransformationError
from .schemas import (
    ComputeInstanceSchema,
    PersistentDiskSchema,
    VPCNetworkSchema,
    SubnetSchema,
    TransformationResult
)

logger = structlog.get_logger(__name__)


class ComputeInstanceTransformer(BaseTransformer):
    """Transformer for GCP Compute Engine VM instances."""
    
    def get_resource_type(self) -> str:
        return "compute.instances"
    
    def get_node_label(self) -> str:
        return "ComputeInstance"
    
    def transform(
        self,
        resource_data: Dict[str, Any],
        snapshot_timestamp: Optional[datetime] = None
    ) -> TransformationResult:
        """
        Transform VM instance data into Neo4j format.
        
        Args:
            resource_data: VM instance data from ComputeEngineClient
            snapshot_timestamp: Snapshot timestamp
            
        Returns:
            TransformationResult with node and relationships
        """
        # Validate required fields
        self.validate_required_fields(
            resource_data,
            ['name', 'zone', 'machine_type', 'status']
        )
        
        # Create base node data
        node_data = self._create_base_node_data(resource_data, snapshot_timestamp)
        
        # Add instance-specific properties
        node_data['name'] = resource_data['name']
        node_data['zone'] = resource_data['zone']
        node_data['machineType'] = resource_data['machine_type']
        node_data['cpuPlatform'] = resource_data.get('cpu_platform')
        node_data['status'] = resource_data['status']
        
        # Network configuration
        node_data['networkInterfaces'] = self._transform_keys_to_camel_case(
            {'items': resource_data.get('network_interfaces', [])}
        ).get('items', [])
        node_data['tags'] = resource_data.get('tags', [])
        node_data['canIpForward'] = resource_data.get('can_ip_forward', False)
        
        # Disk configuration
        node_data['disks'] = resource_data.get('disks', [])
        node_data['bootDiskSizeGb'] = self._extract_boot_disk_size(resource_data.get('disks', []))
        
        # Metadata
        node_data['metadata'] = resource_data.get('metadata', {})
        
        # Service accounts
        node_data['serviceAccounts'] = resource_data.get('service_accounts', [])
        
        # Scheduling
        node_data['preemptible'] = resource_data.get('preemptible', False)
        node_data['automaticRestart'] = resource_data.get('automatic_restart', True)
        node_data['onHostMaintenance'] = resource_data.get('on_host_maintenance')
        
        # Performance metrics (optional)
        node_data['cpuUtilization'] = resource_data.get('cpu_utilization')
        node_data['memoryUtilization'] = resource_data.get('memory_utilization')
        node_data['diskReadOpsPerSec'] = resource_data.get('disk_read_ops_per_sec')
        node_data['diskWriteOpsPerSec'] = resource_data.get('disk_write_ops_per_sec')
        node_data['networkSentBytesPerSec'] = resource_data.get('network_sent_bytes_per_sec')
        node_data['networkReceivedBytesPerSec'] = resource_data.get('network_received_bytes_per_sec')
        
        # Extract relationships
        relationships = self._extract_instance_relationships(
            node_data['gcpId'],
            resource_data
        )
        
        return TransformationResult(
            node=node_data,
            node_label=self.get_node_label(),
            relationships=relationships,
            resource_id=node_data['gcpId'],
            resource_type=self.get_resource_type()
        )
    
    def _extract_boot_disk_size(self, disks: List[Dict[str, Any]]) -> Optional[int]:
        """Extract boot disk size from disks list."""
        for disk in disks:
            if disk.get('boot'):
                # Size would need to be fetched from disk resource
                # For now, return None as it's not in the instance data
                return None
        return None
    
    def _extract_instance_relationships(
        self,
        instance_id: str,
        resource_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships from instance data.
        
        Creates:
        - ATTACHED_TO relationships for network interfaces
        - USES_DISK relationships for attached disks
        """
        relationships = []
        
        # Extract network relationships (ATTACHED_TO Subnet)
        network_interfaces = resource_data.get('network_interfaces', [])
        for idx, interface in enumerate(network_interfaces):
            subnetwork = interface.get('subnetwork')
            if subnetwork:
                # Extract subnet ID from subnetwork URL
                subnet_id = subnetwork
                
                rel = self._create_relationship(
                    source_id=instance_id,
                    target_id=subnet_id,
                    relationship_type='ATTACHED_TO',
                    properties={
                        'interfaceIndex': idx,
                        'networkIP': interface.get('networkIP', ''),
                        'accessConfigs': interface.get('accessConfigs', []),
                        'aliasIpRanges': interface.get('aliasIpRanges', []),
                        'nicType': interface.get('nicType')
                    }
                )
                relationships.append(rel)
        
        # Extract disk relationships (USES_DISK)
        disks = resource_data.get('disks', [])
        for disk in disks:
            disk_source = disk.get('source')
            if disk_source:
                rel = self._create_relationship(
                    source_id=instance_id,
                    target_id=disk_source,
                    relationship_type='USES_DISK',
                    properties={
                        'deviceName': disk.get('deviceName', ''),
                        'boot': disk.get('boot', False),
                        'autoDelete': disk.get('autoDelete', False),
                        'mode': disk.get('mode', 'READ_WRITE'),
                        'interface': disk.get('interface')
                    }
                )
                relationships.append(rel)
        
        return relationships


class PersistentDiskTransformer(BaseTransformer):
    """Transformer for GCP Persistent Disks."""
    
    def get_resource_type(self) -> str:
        return "compute.disks"
    
    def get_node_label(self) -> str:
        return "PersistentDisk"
    
    def transform(
        self,
        resource_data: Dict[str, Any],
        snapshot_timestamp: Optional[datetime] = None
    ) -> TransformationResult:
        """
        Transform persistent disk data into Neo4j format.
        
        Args:
            resource_data: Disk data from ComputeEngineClient
            snapshot_timestamp: Snapshot timestamp
            
        Returns:
            TransformationResult with node and relationships
        """
        # Validate required fields
        self.validate_required_fields(
            resource_data,
            ['name', 'zone', 'size_gb', 'type', 'status']
        )
        
        # Create base node data
        node_data = self._create_base_node_data(resource_data, snapshot_timestamp)
        
        # Add disk-specific properties
        node_data['name'] = resource_data['name']
        node_data['zone'] = resource_data['zone']
        node_data['sizeGb'] = resource_data['size_gb']
        node_data['type'] = resource_data['type']
        node_data['status'] = resource_data['status']
        
        # Parse timestamps
        node_data['lastAttachTimestamp'] = self._parse_timestamp(
            resource_data.get('last_attach_timestamp')
        )
        node_data['lastDetachTimestamp'] = self._parse_timestamp(
            resource_data.get('last_detach_timestamp')
        )
        
        # Source information
        node_data['sourceSnapshot'] = resource_data.get('source_snapshot')
        node_data['sourceImage'] = resource_data.get('source_image')
        
        # Users (attached instances)
        node_data['users'] = resource_data.get('users', [])
        
        # Optional properties
        node_data['provisionedIops'] = resource_data.get('provisioned_iops')
        node_data['diskEncryptionKey'] = resource_data.get('disk_encryption_key')
        node_data['replicaZones'] = resource_data.get('replica_zones', [])
        
        # Extract relationships
        relationships = self._extract_disk_relationships(
            node_data['gcpId'],
            resource_data
        )
        
        return TransformationResult(
            node=node_data,
            node_label=self.get_node_label(),
            relationships=relationships,
            resource_id=node_data['gcpId'],
            resource_type=self.get_resource_type()
        )
    
    def _extract_disk_relationships(
        self,
        disk_id: str,
        resource_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships from disk data.
        
        Creates:
        - CREATED_FROM relationships for snapshots/images
        """
        relationships = []
        
        # Snapshot source relationship
        source_snapshot = resource_data.get('source_snapshot')
        if source_snapshot:
            rel = self._create_relationship(
                source_id=disk_id,
                target_id=source_snapshot,
                relationship_type='CREATED_FROM',
                properties={'sourceType': 'SNAPSHOT'}
            )
            relationships.append(rel)
        
        # Image source relationship
        source_image = resource_data.get('source_image')
        if source_image:
            rel = self._create_relationship(
                source_id=disk_id,
                target_id=source_image,
                relationship_type='CREATED_FROM',
                properties={'sourceType': 'IMAGE'}
            )
            relationships.append(rel)
        
        return relationships


class VPCNetworkTransformer(BaseTransformer):
    """Transformer for GCP VPC Networks."""
    
    def get_resource_type(self) -> str:
        return "compute.networks"
    
    def get_node_label(self) -> str:
        return "VPCNetwork"
    
    def transform(
        self,
        resource_data: Dict[str, Any],
        snapshot_timestamp: Optional[datetime] = None
    ) -> TransformationResult:
        """
        Transform VPC network data into Neo4j format.
        
        Args:
            resource_data: VPC network data
            snapshot_timestamp: Snapshot timestamp
            
        Returns:
            TransformationResult with node and relationships
        """
        # Validate required fields
        self.validate_required_fields(
            resource_data,
            ['name', 'auto_create_subnetworks', 'routing_mode']
        )
        
        # Create base node data
        node_data = self._create_base_node_data(resource_data, snapshot_timestamp)
        
        # Add VPC-specific properties
        node_data['name'] = resource_data['name']
        node_data['autoCreateSubnetworks'] = resource_data['auto_create_subnetworks']
        node_data['routingMode'] = resource_data['routing_mode']
        node_data['mtu'] = resource_data.get('mtu', 1460)
        node_data['peerings'] = resource_data.get('peerings', [])
        
        # Extract relationships
        relationships = self._extract_vpc_relationships(
            node_data['gcpId'],
            resource_data
        )
        
        return TransformationResult(
            node=node_data,
            node_label=self.get_node_label(),
            relationships=relationships,
            resource_id=node_data['gcpId'],
            resource_type=self.get_resource_type()
        )
    
    def _extract_vpc_relationships(
        self,
        vpc_id: str,
        resource_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships from VPC data.
        
        Creates:
        - PEERS_WITH relationships for VPC peering
        """
        relationships = []
        
        # VPC peering relationships
        peerings = resource_data.get('peerings', [])
        for peering in peerings:
            peer_network = peering.get('network')
            if peer_network:
                rel = self._create_relationship(
                    source_id=vpc_id,
                    target_id=peer_network,
                    relationship_type='PEERS_WITH',
                    properties={
                        'peeringName': peering.get('name'),
                        'state': peering.get('state'),
                        'importCustomRoutes': peering.get('importCustomRoutes', False),
                        'exportCustomRoutes': peering.get('exportCustomRoutes', False)
                    }
                )
                relationships.append(rel)
        
        return relationships


class SubnetTransformer(BaseTransformer):
    """Transformer for GCP Subnets."""
    
    def get_resource_type(self) -> str:
        return "compute.subnetworks"
    
    def get_node_label(self) -> str:
        return "Subnet"
    
    def transform(
        self,
        resource_data: Dict[str, Any],
        snapshot_timestamp: Optional[datetime] = None
    ) -> TransformationResult:
        """
        Transform subnet data into Neo4j format.
        
        Args:
            resource_data: Subnet data
            snapshot_timestamp: Snapshot timestamp
            
        Returns:
            TransformationResult with node and relationships
        """
        # Validate required fields
        self.validate_required_fields(
            resource_data,
            ['name', 'region', 'network', 'ip_cidr_range', 'gateway_address']
        )
        
        # Create base node data
        node_data = self._create_base_node_data(resource_data, snapshot_timestamp)
        
        # Add subnet-specific properties
        node_data['name'] = resource_data['name']
        node_data['region'] = resource_data['region']
        node_data['network'] = resource_data['network']
        node_data['ipCidrRange'] = resource_data['ip_cidr_range']
        node_data['gatewayAddress'] = resource_data['gateway_address']
        node_data['secondaryIpRanges'] = resource_data.get('secondary_ip_ranges', [])
        
        # Access configuration
        node_data['privateIpGoogleAccess'] = resource_data.get('private_ip_google_access', False)
        node_data['enableFlowLogs'] = resource_data.get('enable_flow_logs', False)
        node_data['flowLogsConfig'] = resource_data.get('flow_logs_config')
        
        # Purpose and role
        node_data['purpose'] = resource_data.get('purpose')
        node_data['role'] = resource_data.get('role')
        
        # Extract relationships
        relationships = self._extract_subnet_relationships(
            node_data['gcpId'],
            resource_data
        )
        
        return TransformationResult(
            node=node_data,
            node_label=self.get_node_label(),
            relationships=relationships,
            resource_id=node_data['gcpId'],
            resource_type=self.get_resource_type()
        )
    
    def _extract_subnet_relationships(
        self,
        subnet_id: str,
        resource_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships from subnet data.
        
        Creates:
        - PART_OF relationship to parent VPC network
        """
        relationships = []
        
        # Parent VPC network relationship
        network = resource_data.get('network')
        if network:
            rel = self._create_relationship(
                source_id=subnet_id,
                target_id=network,
                relationship_type='PART_OF'
            )
            relationships.append(rel)
        
        return relationships


class TransformerFactory:
    """
    Factory for creating appropriate transformers based on resource type.
    """
    
    _transformers = {
        'compute.instances': ComputeInstanceTransformer,
        'compute.disks': PersistentDiskTransformer,
        'compute.networks': VPCNetworkTransformer,
        'compute.subnetworks': SubnetTransformer,
    }
    
    @classmethod
    def get_transformer(cls, resource_type: str) -> BaseTransformer:
        """
        Get transformer for a specific resource type.
        
        Args:
            resource_type: GCP resource type
            
        Returns:
            Transformer instance
            
        Raises:
            ValueError: If resource type is not supported
        """
        transformer_class = cls._transformers.get(resource_type)
        
        if not transformer_class:
            raise ValueError(f"No transformer available for resource type: {resource_type}")
        
        return transformer_class()
    
    @classmethod
    def register_transformer(
        cls,
        resource_type: str,
        transformer_class: type
    ) -> None:
        """
        Register a new transformer for a resource type.
        
        Args:
            resource_type: GCP resource type
            transformer_class: Transformer class
        """
        cls._transformers[resource_type] = transformer_class
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """
        Get list of supported resource types.
        
        Returns:
            List of resource type strings
        """
        return list(cls._transformers.keys())

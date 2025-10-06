"""
GCP Compute Engine API Client

Handles retrieval of Compute Engine resources including:
- Virtual Machine instances
- Persistent disks
- Instance templates
- Instance groups
- Machine types
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

import structlog
from google.cloud import compute_v1
from google.auth.credentials import Credentials

from .base_client import (
    BaseGCPClient,
    ResourceType,
    RateLimitConfig,
    RetryConfig,
    GCPAPIError
)

logger = structlog.get_logger(__name__)


class ComputeEngineClient(BaseGCPClient):
    """
    Client for GCP Compute Engine API.
    
    Provides methods to retrieve VM instances, disks, and related resources.
    """
    
    def __init__(
        self,
        credentials: Credentials,
        project_id: str,
        rate_limit_config: Optional[RateLimitConfig] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize Compute Engine client.
        
        Args:
            credentials: GCP credentials
            project_id: GCP project ID
            rate_limit_config: Rate limiting configuration
            retry_config: Retry logic configuration
        """
        super().__init__(credentials, project_id, rate_limit_config, retry_config)
        
        # Initialize Compute Engine API clients
        self._instances_client = compute_v1.InstancesClient(credentials=credentials)
        self._disks_client = compute_v1.DisksClient(credentials=credentials)
        self._instance_templates_client = compute_v1.InstanceTemplatesClient(credentials=credentials)
        self._instance_groups_client = compute_v1.InstanceGroupsClient(credentials=credentials)
        self._zones_client = compute_v1.ZonesClient(credentials=credentials)
        self._regions_client = compute_v1.RegionsClient(credentials=credentials)
        
        logger.info("Initialized Compute Engine client", project_id=project_id)
    
    def get_resource_type(self) -> ResourceType:
        """Get the resource type handled by this client."""
        return ResourceType.VIRTUAL_MACHINE
    
    def _extract_items_from_response(self, response: Any) -> List[Any]:
        """
        Extract items from Compute Engine API response.
        
        Args:
            response: API response object
            
        Returns:
            List of items from response
        """
        # Compute Engine responses are iterables
        return list(response)
    
    def _extract_next_page_token(self, response: Any) -> Optional[str]:
        """
        Extract next page token from Compute Engine API response.
        
        Args:
            response: API response object
            
        Returns:
            Next page token or None
        """
        # Compute Engine API handles pagination internally via iterators
        # The list() call in _extract_items_from_response exhausts the iterator
        return None
    
    def list_resources(
        self,
        region: Optional[str] = None,
        zone: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List all VM instances in the project.
        
        Args:
            region: GCP region to filter by
            zone: GCP zone to filter by (takes precedence over region)
            filters: Additional filters
            
        Returns:
            List of VM instance dictionaries
        """
        instances = []
        
        try:
            if zone:
                # List instances in specific zone
                logger.debug("Listing instances in zone", zone=zone)
                instances.extend(self._list_instances_in_zone(zone, filters))
            
            elif region:
                # List instances in all zones of the region
                logger.debug("Listing instances in region", region=region)
                zones = self._get_zones_in_region(region)
                for zone_name in zones:
                    instances.extend(self._list_instances_in_zone(zone_name, filters))
            
            else:
                # List instances in all zones of the project
                logger.debug("Listing instances in all zones")
                zones = self._get_all_zones()
                for zone_name in zones:
                    instances.extend(self._list_instances_in_zone(zone_name, filters))
            
            logger.info(
                "Retrieved VM instances",
                count=len(instances),
                zone=zone,
                region=region
            )
            
            return instances
            
        except Exception as e:
            logger.error("Failed to list VM instances", error=str(e))
            raise GCPAPIError(f"Failed to list VM instances: {str(e)}")
    
    def _list_instances_in_zone(
        self,
        zone: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List VM instances in a specific zone.
        
        Args:
            zone: Zone name
            filters: Optional filters
            
        Returns:
            List of VM instance dictionaries
        """
        request = compute_v1.ListInstancesRequest(
            project=self.project_id,
            zone=zone
        )
        
        # Add filters if provided
        if filters:
            filter_str = self._build_filter_string(filters)
            request.filter = filter_str
        
        # Execute request with retry and rate limiting
        instances_iterator = self._execute_with_retry(
            self._instances_client.list,
            request=request
        )
        
        # Convert instances to dictionaries
        instances = []
        for instance in instances_iterator:
            instance_dict = self._instance_to_dict(instance)
            instances.append(instance_dict)
        
        return instances
    
    def get_resource(self, resource_id: str) -> Dict[str, Any]:
        """
        Get a specific VM instance by ID.
        
        Args:
            resource_id: Full resource ID (projects/PROJECT/zones/ZONE/instances/NAME)
            
        Returns:
            VM instance dictionary
        """
        try:
            # Parse resource ID
            parts = resource_id.split('/')
            if len(parts) < 6:
                raise ValueError(f"Invalid resource ID format: {resource_id}")
            
            zone = parts[3]
            instance_name = parts[5]
            
            logger.debug(
                "Getting VM instance",
                instance_name=instance_name,
                zone=zone
            )
            
            request = compute_v1.GetInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            
            instance = self._execute_with_retry(
                self._instances_client.get,
                request=request
            )
            
            return self._instance_to_dict(instance)
            
        except Exception as e:
            logger.error(
                "Failed to get VM instance",
                resource_id=resource_id,
                error=str(e)
            )
            raise GCPAPIError(f"Failed to get VM instance: {str(e)}")
    
    def _instance_to_dict(self, instance: compute_v1.Instance) -> Dict[str, Any]:
        """
        Convert Compute Engine Instance to dictionary format.
        
        Args:
            instance: Compute Engine Instance object
            
        Returns:
            Dictionary representation matching Neo4j schema
        """
        # Extract zone from self-link
        zone = instance.zone.split('/')[-1] if instance.zone else None
        region = zone.rsplit('-', 1)[0] if zone else None
        
        # Extract network information
        network_interfaces = []
        for interface in instance.network_interfaces:
            network_interfaces.append({
                'network': interface.network,
                'subnetwork': interface.subnetwork,
                'networkIP': interface.network_i_p,
                'accessConfigs': [
                    {
                        'natIP': config.nat_i_p,
                        'type': config.type_
                    }
                    for config in interface.access_configs
                ] if interface.access_configs else []
            })
        
        # Extract disk information
        disks = []
        for disk in instance.disks:
            disks.append({
                'source': disk.source,
                'deviceName': disk.device_name,
                'mode': disk.mode,
                'boot': disk.boot,
                'autoDelete': disk.auto_delete
            })
        
        # Extract labels and metadata
        labels = dict(instance.labels) if instance.labels else {}
        metadata_items = {}
        if instance.metadata and instance.metadata.items:
            for item in instance.metadata.items:
                metadata_items[item.key] = item.value
        
        # Extract service accounts
        service_accounts = []
        for sa in instance.service_accounts:
            service_accounts.append({
                'email': sa.email,
                'scopes': list(sa.scopes) if sa.scopes else []
            })
        
        return {
            'id': instance.self_link,
            'name': instance.name,
            'project_id': self.project_id,
            'zone': zone,
            'region': region,
            'machine_type': instance.machine_type.split('/')[-1] if instance.machine_type else None,
            'status': instance.status,
            'status_message': instance.status_message if hasattr(instance, 'status_message') else None,
            'cpu_count': self._extract_cpu_count(instance.machine_type) if instance.machine_type else None,
            'memory_gb': self._extract_memory_gb(instance.machine_type) if instance.machine_type else None,
            'creation_timestamp': instance.creation_timestamp,
            'last_start_timestamp': instance.last_start_timestamp if hasattr(instance, 'last_start_timestamp') else None,
            'last_stop_timestamp': instance.last_stop_timestamp if hasattr(instance, 'last_stop_timestamp') else None,
            'network_interfaces': network_interfaces,
            'disks': disks,
            'labels': labels,
            'metadata': metadata_items,
            'tags': list(instance.tags.items) if instance.tags and instance.tags.items else [],
            'service_accounts': service_accounts,
            'can_ip_forward': instance.can_i_p_forward,
            'deletion_protection': instance.deletion_protection,
            'fingerprint': instance.fingerprint,
            'self_link': instance.self_link
        }
    
    def _extract_cpu_count(self, machine_type: str) -> Optional[int]:
        """
        Extract CPU count from machine type.
        
        Args:
            machine_type: Machine type string
            
        Returns:
            CPU count or None
        """
        # Machine types are in format: zones/ZONE/machineTypes/TYPE
        # Standard types: n1-standard-4, n2-standard-8, etc.
        # Custom types: custom-CPUS-MEMORY
        
        type_name = machine_type.split('/')[-1]
        
        if type_name.startswith('custom-'):
            parts = type_name.split('-')
            if len(parts) >= 2:
                try:
                    return int(parts[1])
                except ValueError:
                    pass
        else:
            # Extract from standard type name (e.g., n1-standard-4 -> 4 CPUs)
            parts = type_name.split('-')
            if len(parts) >= 3:
                try:
                    # For standard types, the last part is often the CPU count
                    return int(parts[-1])
                except ValueError:
                    pass
        
        return None
    
    def _extract_memory_gb(self, machine_type: str) -> Optional[float]:
        """
        Extract memory in GB from machine type.
        
        Args:
            machine_type: Machine type string
            
        Returns:
            Memory in GB or None
        """
        # For custom machine types: custom-CPUS-MEMORY
        type_name = machine_type.split('/')[-1]
        
        if type_name.startswith('custom-'):
            parts = type_name.split('-')
            if len(parts) >= 3:
                try:
                    memory_mb = int(parts[2])
                    return memory_mb / 1024.0
                except ValueError:
                    pass
        
        # For standard types, would need a lookup table
        # Return None for now - can be enriched later
        return None
    
    def _get_zones_in_region(self, region: str) -> List[str]:
        """
        Get all zones in a specific region.
        
        Args:
            region: Region name
            
        Returns:
            List of zone names
        """
        zones = []
        
        request = compute_v1.ListZonesRequest(project=self.project_id)
        zones_iterator = self._execute_with_retry(
            self._zones_client.list,
            request=request
        )
        
        for zone in zones_iterator:
            # Check if zone belongs to the specified region
            zone_region = zone.region.split('/')[-1] if zone.region else None
            if zone_region == region:
                zones.append(zone.name)
        
        return zones
    
    def _get_all_zones(self) -> List[str]:
        """
        Get all zones in the project.
        
        Returns:
            List of zone names
        """
        zones = []
        
        request = compute_v1.ListZonesRequest(project=self.project_id)
        zones_iterator = self._execute_with_retry(
            self._zones_client.list,
            request=request
        )
        
        for zone in zones_iterator:
            zones.append(zone.name)
        
        return zones
    
    def _build_filter_string(self, filters: Dict[str, Any]) -> str:
        """
        Build filter string for Compute Engine API.
        
        Args:
            filters: Dictionary of filter criteria
            
        Returns:
            Filter string
        """
        filter_parts = []
        
        for key, value in filters.items():
            if isinstance(value, str):
                filter_parts.append(f"{key}={value}")
            elif isinstance(value, list):
                # OR condition for multiple values
                or_parts = [f"{key}={v}" for v in value]
                filter_parts.append(f"({' OR '.join(or_parts)})")
        
        return " AND ".join(filter_parts)
    
    def list_disks(
        self,
        zone: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List persistent disks.
        
        Args:
            zone: Zone to filter by
            region: Region to filter by
            
        Returns:
            List of disk dictionaries
        """
        disks = []
        
        try:
            if zone:
                disks.extend(self._list_disks_in_zone(zone))
            elif region:
                zones = self._get_zones_in_region(region)
                for zone_name in zones:
                    disks.extend(self._list_disks_in_zone(zone_name))
            else:
                zones = self._get_all_zones()
                for zone_name in zones:
                    disks.extend(self._list_disks_in_zone(zone_name))
            
            logger.info("Retrieved disks", count=len(disks))
            return disks
            
        except Exception as e:
            logger.error("Failed to list disks", error=str(e))
            raise GCPAPIError(f"Failed to list disks: {str(e)}")
    
    def _list_disks_in_zone(self, zone: str) -> List[Dict[str, Any]]:
        """
        List disks in a specific zone.
        
        Args:
            zone: Zone name
            
        Returns:
            List of disk dictionaries
        """
        request = compute_v1.ListDisksRequest(
            project=self.project_id,
            zone=zone
        )
        
        disks_iterator = self._execute_with_retry(
            self._disks_client.list,
            request=request
        )
        
        disks = []
        for disk in disks_iterator:
            disk_dict = self._disk_to_dict(disk, zone)
            disks.append(disk_dict)
        
        return disks
    
    def _disk_to_dict(self, disk: compute_v1.Disk, zone: str) -> Dict[str, Any]:
        """
        Convert Compute Engine Disk to dictionary format.
        
        Args:
            disk: Compute Engine Disk object
            zone: Zone name
            
        Returns:
            Dictionary representation
        """
        region = zone.rsplit('-', 1)[0] if zone else None
        
        return {
            'id': disk.self_link,
            'name': disk.name,
            'project_id': self.project_id,
            'zone': zone,
            'region': region,
            'size_gb': disk.size_gb,
            'type': disk.type_.split('/')[-1] if disk.type_ else None,
            'status': disk.status,
            'source_image': disk.source_image if hasattr(disk, 'source_image') else None,
            'source_snapshot': disk.source_snapshot if hasattr(disk, 'source_snapshot') else None,
            'users': list(disk.users) if disk.users else [],
            'labels': dict(disk.labels) if disk.labels else {},
            'creation_timestamp': disk.creation_timestamp,
            'last_attach_timestamp': disk.last_attach_timestamp if hasattr(disk, 'last_attach_timestamp') else None,
            'last_detach_timestamp': disk.last_detach_timestamp if hasattr(disk, 'last_detach_timestamp') else None,
            'self_link': disk.self_link
        }

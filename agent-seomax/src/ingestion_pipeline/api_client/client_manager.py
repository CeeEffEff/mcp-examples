"""
GCP Client Manager

Provides unified interface for all GCP API clients.
Manages client lifecycle, authentication, and resource retrieval.
"""

from typing import Dict, List, Optional, Any
from enum import Enum

import structlog

from .auth import GCPAuthManager, GCPAuthenticationError
from .base_client import ResourceType, RateLimitConfig, RetryConfig
from .compute_client import ComputeEngineClient

logger = structlog.get_logger(__name__)


class GCPClientManager:
    """
    Manages all GCP API clients.
    
    Provides unified interface for retrieving resources across all GCP services.
    """
    
    def __init__(
        self,
        service_account_path: Optional[str] = None,
        project_id: Optional[str] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize GCP client manager.
        
        Args:
            service_account_path: Path to service account JSON key
            project_id: GCP project ID (optional, will be auto-detected)
            rate_limit_config: Rate limiting configuration for all clients
            retry_config: Retry configuration for all clients
        """
        self.rate_limit_config = rate_limit_config
        self.retry_config = retry_config
        
        # Initialize authentication
        self.auth_manager = GCPAuthManager(service_account_path=service_account_path)
        
        # Get credentials and project ID
        self.credentials = self.auth_manager.authenticate()
        self.project_id = project_id or self.auth_manager.get_project_id()
        
        # Initialize client registry
        self._clients: Dict[ResourceType, Any] = {}
        
        logger.info(
            "Initialized GCP client manager",
            project_id=self.project_id,
            service_account_path=service_account_path
        )
    
    def _get_or_create_client(self, resource_type: ResourceType) -> Any:
        """
        Get or create client for specific resource type.
        
        Args:
            resource_type: Type of resource
            
        Returns:
            GCP API client instance
        """
        if resource_type in self._clients:
            return self._clients[resource_type]
        
        # Create new client based on resource type
        if resource_type in [
            ResourceType.VIRTUAL_MACHINE,
            ResourceType.PERSISTENT_DISK,
            ResourceType.INSTANCE_GROUP
        ]:
            client = ComputeEngineClient(
                credentials=self.credentials,
                project_id=self.project_id,
                rate_limit_config=self.rate_limit_config,
                retry_config=self.retry_config
            )
            self._clients[resource_type] = client
            return client
        
        # Add more client types here as they are implemented
        # elif resource_type == ResourceType.STORAGE_BUCKET:
        #     client = StorageClient(...)
        # elif resource_type == ResourceType.VPC_NETWORK:
        #     client = NetworkingClient(...)
        
        raise NotImplementedError(
            f"Client for resource type {resource_type.value} not yet implemented"
        )
    
    def list_resources(
        self,
        resource_type: ResourceType,
        region: Optional[str] = None,
        zone: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List resources of specified type.
        
        Args:
            resource_type: Type of resources to list
            region: GCP region to filter by
            zone: GCP zone to filter by
            filters: Additional filters
            
        Returns:
            List of resource dictionaries
        """
        try:
            client = self._get_or_create_client(resource_type)
            resources = client.list_resources(
                region=region,
                zone=zone,
                filters=filters
            )
            
            logger.info(
                "Listed resources",
                resource_type=resource_type.value,
                count=len(resources),
                region=region,
                zone=zone
            )
            
            return resources
            
        except Exception as e:
            logger.error(
                "Failed to list resources",
                resource_type=resource_type.value,
                error=str(e)
            )
            raise
    
    def get_resource(
        self,
        resource_type: ResourceType,
        resource_id: str
    ) -> Dict[str, Any]:
        """
        Get specific resource by ID.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
            
        Returns:
            Resource dictionary
        """
        try:
            client = self._get_or_create_client(resource_type)
            resource = client.get_resource(resource_id)
            
            logger.info(
                "Retrieved resource",
                resource_type=resource_type.value,
                resource_id=resource_id
            )
            
            return resource
            
        except Exception as e:
            logger.error(
                "Failed to get resource",
                resource_type=resource_type.value,
                resource_id=resource_id,
                error=str(e)
            )
            raise
    
    def list_all_compute_resources(
        self,
        region: Optional[str] = None,
        zone: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        List all Compute Engine resources.
        
        Args:
            region: GCP region to filter by
            zone: GCP zone to filter by
            
        Returns:
            Dictionary mapping resource types to resource lists
        """
        results = {}
        
        # Get Compute Engine client
        compute_client = self._get_or_create_client(ResourceType.VIRTUAL_MACHINE)
        
        # List VMs
        try:
            results['instances'] = compute_client.list_resources(
                region=region,
                zone=zone
            )
        except Exception as e:
            logger.error("Failed to list VM instances", error=str(e))
            results['instances'] = []
        
        # List disks
        try:
            results['disks'] = compute_client.list_disks(
                region=region,
                zone=zone
            )
        except Exception as e:
            logger.error("Failed to list disks", error=str(e))
            results['disks'] = []
        
        logger.info(
            "Listed all compute resources",
            instances_count=len(results['instances']),
            disks_count=len(results['disks']),
            region=region,
            zone=zone
        )
        
        return results
    
    def validate_connection(self) -> bool:
        """
        Validate that GCP connection is working.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Validate credentials
            if not self.auth_manager.validate_credentials():
                return False
            
            # Try to list zones as a connectivity test
            compute_client = self._get_or_create_client(ResourceType.VIRTUAL_MACHINE)
            zones = compute_client._get_all_zones()
            
            logger.info(
                "Connection validation successful",
                zones_count=len(zones)
            )
            
            return True
            
        except Exception as e:
            logger.error("Connection validation failed", error=str(e))
            return False
    
    def get_project_info(self) -> Dict[str, Any]:
        """
        Get information about the GCP project.
        
        Returns:
            Dictionary with project information
        """
        return {
            'project_id': self.project_id,
            'authenticated': self.credentials is not None,
            'available_clients': list(self._clients.keys())
        }
    
    def close(self):
        """Close all clients and clean up resources."""
        logger.info("Closing GCP client manager")
        
        # Close all clients
        for client in self._clients.values():
            if hasattr(client, 'close'):
                client.close()
        
        self._clients.clear()

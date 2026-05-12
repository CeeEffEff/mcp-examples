"""
Pydantic schemas for GCP resources matching Neo4j node definitions.

These schemas define the data structure for Neo4j nodes, ensuring
type safety and validation before database insertion.
"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


class BaseNodeSchema(BaseModel):
    """Base schema for all Neo4j nodes with standard properties."""
    
    # Temporal Tracking (Required)
    createdAt: datetime = Field(..., description="Resource creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")
    deletedAt: Optional[datetime] = Field(None, description="Soft deletion timestamp")
    snapshotTimestamp: datetime = Field(..., description="Digital twin snapshot capture time")
    
    # GCP Resource Properties (Required)
    gcpId: str = Field(..., description="GCP unique identifier")
    gcpSelfLink: str = Field(..., description="Full GCP resource URL")
    resourceType: str = Field(..., description="GCP resource type")
    
    # Metadata (Optional but recommended)
    labels: Dict[str, str] = Field(default_factory=dict, description="GCP resource labels")
    description: Optional[str] = Field(None, description="Human-readable description")
    projectId: str = Field(..., description="Parent GCP project ID")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InstanceStatus(str, Enum):
    """VM instance status values."""
    PROVISIONING = "PROVISIONING"
    STAGING = "STAGING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    TERMINATED = "TERMINATED"
    SUSPENDING = "SUSPENDING"
    SUSPENDED = "SUSPENDED"


class ComputeInstanceSchema(BaseNodeSchema):
    """Schema for ComputeInstance Neo4j nodes."""
    
    # Identity
    name: str = Field(..., description="Instance name")
    zone: str = Field(..., description="Zone location")
    
    # Configuration
    machineType: str = Field(..., description="Machine type")
    cpuPlatform: Optional[str] = Field(None, description="CPU architecture")
    status: InstanceStatus = Field(..., description="Instance status")
    
    # Network Configuration
    networkInterfaces: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Array of network interface configs"
    )
    tags: List[str] = Field(default_factory=list, description="Network tags for firewall rules")
    canIpForward: bool = Field(False, description="IP forwarding enabled")
    
    # Disk Configuration
    disks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Array of attached disk configs"
    )
    bootDiskSizeGb: Optional[int] = Field(None, description="Boot disk size")
    
    # Metadata
    metadata: Dict[str, str] = Field(default_factory=dict, description="Custom metadata key-values")
    
    # Service Accounts
    serviceAccounts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Service account configurations"
    )
    
    # Scheduling
    preemptible: bool = Field(False, description="Preemptible instance flag")
    automaticRestart: bool = Field(True, description="Auto-restart on failure")
    onHostMaintenance: Optional[str] = Field(None, description="MIGRATE or TERMINATE")
    
    # Performance Metrics (optional, updated periodically)
    cpuUtilization: Optional[float] = Field(None, description="CPU utilization percentage (0-100)")
    memoryUtilization: Optional[float] = Field(None, description="Memory utilization percentage")
    diskReadOpsPerSec: Optional[float] = Field(None, description="Disk read ops per second")
    diskWriteOpsPerSec: Optional[float] = Field(None, description="Disk write ops per second")
    networkSentBytesPerSec: Optional[float] = Field(None, description="Network sent bytes per second")
    networkReceivedBytesPerSec: Optional[float] = Field(None, description="Network received bytes per second")


class PersistentDiskSchema(BaseNodeSchema):
    """Schema for PersistentDisk Neo4j nodes."""
    
    # Identity
    name: str = Field(..., description="Disk name")
    zone: str = Field(..., description="Zone location")
    
    # Configuration
    sizeGb: int = Field(..., description="Disk size in GB")
    type: str = Field(..., description="pd-standard, pd-balanced, pd-ssd, pd-extreme")
    physicalBlockSizeBytes: Optional[int] = Field(None, description="Physical block size")
    
    # Status
    status: str = Field(..., description="Disk status")
    lastAttachTimestamp: Optional[datetime] = Field(None, description="Last attach time")
    lastDetachTimestamp: Optional[datetime] = Field(None, description="Last detach time")
    
    # Source
    sourceSnapshot: Optional[str] = Field(None, description="Source snapshot reference")
    sourceImage: Optional[str] = Field(None, description="Source image reference")
    
    # Users
    users: List[str] = Field(default_factory=list, description="Attached instance references")
    
    # Performance (pd-extreme only)
    provisionedIops: Optional[int] = Field(None, description="Provisioned IOPS")
    
    # Encryption
    diskEncryptionKey: Optional[Dict[str, Any]] = Field(None, description="Encryption key config")
    
    # Replication (regional disks)
    replicaZones: List[str] = Field(default_factory=list, description="Replica zones")


class VPCNetworkSchema(BaseNodeSchema):
    """Schema for VPCNetwork Neo4j nodes."""
    
    # Identity
    name: str = Field(..., description="VPC network name")
    
    # Configuration
    autoCreateSubnetworks: bool = Field(..., description="Auto-create mode")
    routingMode: str = Field(..., description="REGIONAL or GLOBAL")
    mtu: int = Field(1460, description="Maximum transmission unit")
    
    # Peering
    peerings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="VPC peering configurations"
    )


class SubnetSchema(BaseNodeSchema):
    """Schema for Subnet Neo4j nodes."""
    
    # Identity
    name: str = Field(..., description="Subnet name")
    region: str = Field(..., description="Region location")
    
    # Network Reference
    network: str = Field(..., description="Parent VPC network reference")
    
    # IP Configuration
    ipCidrRange: str = Field(..., description="Primary IP range")
    gatewayAddress: str = Field(..., description="Gateway IP")
    secondaryIpRanges: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Secondary IP ranges"
    )
    
    # Access Configuration
    privateIpGoogleAccess: bool = Field(False, description="Private Google access")
    enableFlowLogs: bool = Field(False, description="VPC flow logs enabled")
    flowLogsConfig: Optional[Dict[str, Any]] = Field(None, description="Flow logs configuration")
    
    # Purpose
    purpose: Optional[str] = Field(None, description="PRIVATE, INTERNAL_HTTPS_LOAD_BALANCER, etc.")
    role: Optional[str] = Field(None, description="ACTIVE or BACKUP")


class StorageBucketSchema(BaseNodeSchema):
    """Schema for StorageBucket Neo4j nodes."""
    
    # Identity
    name: str = Field(..., description="Globally unique bucket name")
    
    # Location
    location: str = Field(..., description="Region or multi-region")
    locationType: str = Field(..., description="REGION or MULTI_REGION")
    
    # Storage Class
    storageClass: str = Field(..., description="STANDARD, NEARLINE, COLDLINE, ARCHIVE")
    
    # Versioning
    versioningEnabled: bool = Field(False, description="Object versioning")
    
    # Lifecycle
    lifecycleRules: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Lifecycle management rules"
    )
    
    # Access Control
    iamConfiguration: Optional[Dict[str, Any]] = Field(None, description="IAM config")
    publicAccessPrevention: str = Field("inherited", description="inherited or enforced")
    
    # Encryption
    encryption: Optional[Dict[str, Any]] = Field(None, description="Default encryption config")
    
    # Retention
    retentionPolicy: Optional[Dict[str, Any]] = Field(None, description="Data retention policy")
    
    # Logging
    logging: Optional[Dict[str, Any]] = Field(None, description="Access logging config")
    
    # Website
    website: Optional[Dict[str, Any]] = Field(None, description="Static website config")
    
    # CORS
    cors: List[Dict[str, Any]] = Field(default_factory=list, description="CORS configuration")


class ServiceAccountSchema(BaseNodeSchema):
    """Schema for ServiceAccount Neo4j nodes."""
    
    # Identity
    email: str = Field(..., description="Service account email")
    uniqueId: str = Field(..., description="Unique numeric ID")
    
    # Display
    displayName: Optional[str] = Field(None, description="Display name")
    
    # OAuth
    oauth2ClientId: Optional[str] = Field(None, description="OAuth2 client ID")
    
    # Status
    disabled: bool = Field(False, description="Disabled status")


class BaseRelationshipSchema(BaseModel):
    """Base schema for Neo4j relationships."""
    
    # Source and target node IDs
    sourceId: str = Field(..., description="Source node gcpId")
    targetId: str = Field(..., description="Target node gcpId")
    
    # Relationship type
    relationshipType: str = Field(..., description="Relationship type (e.g., ATTACHED_TO)")
    
    # Temporal Tracking
    createdAt: datetime = Field(..., description="Relationship creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")
    deletedAt: Optional[datetime] = Field(None, description="Soft deletion timestamp")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional relationship metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AttachedToRelationship(BaseRelationshipSchema):
    """Relationship for instance attached to network."""
    
    relationshipType: Literal["ATTACHED_TO"] = "ATTACHED_TO"
    
    # Network Interface Details
    interfaceIndex: int = Field(..., description="Interface number")
    networkIP: str = Field(..., description="Internal IP address")
    accessConfigs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="External IP configurations"
    )
    aliasIpRanges: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Alias IP ranges"
    )
    nicType: Optional[str] = Field(None, description="VIRTIO_NET or GVNIC")


class UsesDiskRelationship(BaseRelationshipSchema):
    """Relationship for instance using disk."""
    
    relationshipType: Literal["USES_DISK"] = "USES_DISK"
    
    # Disk Attachment Configuration
    deviceName: str = Field(..., description="Device name within instance")
    boot: bool = Field(..., description="Boot disk flag")
    autoDelete: bool = Field(..., description="Delete disk when instance deleted")
    mode: str = Field(..., description="READ_WRITE or READ_ONLY")
    interface: Optional[str] = Field(None, description="SCSI or NVME")


class PartOfRelationship(BaseRelationshipSchema):
    """Relationship for child being part of parent."""
    
    relationshipType: Literal["PART_OF"] = "PART_OF"


class TransformationResult(BaseModel):
    """Result of a transformation operation."""
    
    # Node data
    node: Dict[str, Any] = Field(..., description="Neo4j node dictionary")
    node_label: str = Field(..., description="Neo4j node label")
    
    # Relationships
    relationships: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Neo4j relationship dictionaries"
    )
    
    # Metadata
    resource_id: str = Field(..., description="Resource identifier")
    resource_type: str = Field(..., description="GCP resource type")
    transformation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When transformation occurred"
    )

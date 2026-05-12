"""
Event type definitions and enums for GCP resource change events.

This module defines the event types that the system can process from
GCP Pub/Sub subscriptions, along with their associated data structures.
"""

from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


class GCPResourceType(Enum):
    """Enumeration of GCP resource types that can trigger events."""
    
    COMPUTE_INSTANCE = "compute.googleapis.com/Instance"
    COMPUTE_DISK = "compute.googleapis.com/Disk"
    STORAGE_BUCKET = "storage.googleapis.com/Bucket"
    CLOUD_SQL_INSTANCE = "sqladmin.googleapis.com/Instance"
    CLOUD_FUNCTION = "cloudfunctions.googleapis.com/CloudFunction"
    PUBSUB_TOPIC = "pubsub.googleapis.com/Topic"
    PUBSUB_SUBSCRIPTION = "pubsub.googleapis.com/Subscription"
    IAM_POLICY = "cloudresourcemanager.googleapis.com/IamPolicy"
    SERVICE_ACCOUNT = "iam.googleapis.com/ServiceAccount"
    VPC_NETWORK = "compute.googleapis.com/Network"
    VPC_SUBNET = "compute.googleapis.com/Subnetwork"
    LOAD_BALANCER = "compute.googleapis.com/ForwardingRule"
    CLOUD_LOGGING_SINK = "logging.googleapis.com/LogSink"
    MONITORING_ALERT = "monitoring.googleapis.com/AlertPolicy"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, resource_type: str) -> "GCPResourceType":
        """Convert a string to a GCPResourceType enum value."""
        for member in cls:
            if member.value == resource_type:
                return member
        return cls.UNKNOWN


class EventType(Enum):
    """Enumeration of event types that can occur for GCP resources."""
    
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    STATE_CHANGED = "state_changed"
    CONFIGURATION_CHANGED = "configuration_changed"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, event_type: str) -> "EventType":
        """Convert a string to an EventType enum value."""
        event_type_lower = event_type.lower()
        for member in cls:
            if member.value == event_type_lower:
                return member
        return cls.UNKNOWN


@dataclass
class EventMetadata:
    """Metadata associated with a GCP resource event."""
    
    event_id: str
    event_type: EventType
    resource_type: GCPResourceType
    resource_name: str
    project_id: str
    timestamp: datetime
    region: Optional[str] = None
    zone: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary format."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "resource_type": self.resource_type.value,
            "resource_name": self.resource_name,
            "project_id": self.project_id,
            "timestamp": self.timestamp.isoformat(),
            "region": self.region,
            "zone": self.zone,
            "labels": self.labels,
            "attributes": self.attributes
        }

    @classmethod
    def from_pubsub_message(cls, message_data: Dict[str, Any], 
                           message_attributes: Dict[str, str]) -> "EventMetadata":
        """
        Create EventMetadata from a Pub/Sub message.
        
        Args:
            message_data: The decoded message data
            message_attributes: Message attributes from Pub/Sub
            
        Returns:
            EventMetadata instance
        """
        return cls(
            event_id=message_attributes.get("eventId", ""),
            event_type=EventType.from_string(
                message_attributes.get("eventType", "unknown")
            ),
            resource_type=GCPResourceType.from_string(
                message_data.get("protoPayload", {}).get("resourceName", "unknown")
            ),
            resource_name=message_data.get("resource", {}).get("labels", {}).get("resource_id", ""),
            project_id=message_data.get("resource", {}).get("labels", {}).get("project_id", ""),
            timestamp=datetime.fromisoformat(
                message_data.get("timestamp", datetime.utcnow().isoformat()).replace("Z", "+00:00")
            ),
            region=message_data.get("resource", {}).get("labels", {}).get("region"),
            zone=message_data.get("resource", {}).get("labels", {}).get("zone"),
            labels=message_data.get("resource", {}).get("labels", {}),
            attributes=message_attributes
        )


@dataclass
class ResourceEvent:
    """Complete event data for a GCP resource change."""
    
    metadata: EventMetadata
    resource_data: Dict[str, Any]
    previous_state: Optional[Dict[str, Any]] = None
    raw_message: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary format."""
        return {
            "metadata": self.metadata.to_dict(),
            "resource_data": self.resource_data,
            "previous_state": self.previous_state,
            "raw_message": self.raw_message
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_pubsub_message(cls, message_data: Dict[str, Any],
                           message_attributes: Dict[str, str]) -> "ResourceEvent":
        """
        Create ResourceEvent from a Pub/Sub message.
        
        Args:
            message_data: The decoded message data
            message_attributes: Message attributes from Pub/Sub
            
        Returns:
            ResourceEvent instance
        """
        metadata = EventMetadata.from_pubsub_message(message_data, message_attributes)
        
        # Extract resource data from the message
        resource_data = message_data.get("protoPayload", {}).get("response", {})
        if not resource_data:
            resource_data = message_data.get("jsonPayload", {})
        
        # Extract previous state if available (for update events)
        previous_state = None
        if metadata.event_type == EventType.UPDATED:
            previous_state = message_data.get("protoPayload", {}).get("request", {})
        
        return cls(
            metadata=metadata,
            resource_data=resource_data,
            previous_state=previous_state,
            raw_message=message_data
        )


class EventPriority(Enum):
    """Priority levels for event processing."""
    
    CRITICAL = 0  # Must be processed immediately (e.g., security events)
    HIGH = 1      # Should be processed quickly (e.g., deletions)
    NORMAL = 2    # Standard priority (e.g., updates)
    LOW = 3       # Can be processed with delay (e.g., metadata changes)

    @staticmethod
    def get_priority_for_event(event: ResourceEvent) -> "EventPriority":
        """
        Determine the priority level for a given event.
        
        Args:
            event: The resource event
            
        Returns:
            EventPriority enum value
        """
        # Security-related events are critical
        if "iam" in event.metadata.resource_type.value.lower():
            return EventPriority.CRITICAL
        
        # Deletions are high priority
        if event.metadata.event_type == EventType.DELETED:
            return EventPriority.HIGH
        
        # Creations and state changes are normal priority
        if event.metadata.event_type in [EventType.CREATED, EventType.STATE_CHANGED]:
            return EventPriority.NORMAL
        
        # Everything else is low priority
        return EventPriority.LOW

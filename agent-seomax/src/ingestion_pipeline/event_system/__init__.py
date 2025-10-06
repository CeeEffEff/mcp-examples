"""
Event subscription system for GCP resource change events.

This package provides a comprehensive event subscription system for monitoring
GCP resource changes via Pub/Sub, including event type definitions, message
handling, and subscription management.

Main Components:
    - EventSubscriber: Main orchestrator for subscription management
    - PubSubClient: Low-level Pub/Sub operations wrapper
    - MessageHandler: Message processing and callback execution
    - Event Types: Type definitions for GCP resource events

Example Usage:
    ```python
    from ingestion_pipeline.api_client import GCPAuthManager
    from ingestion_pipeline.event_system import EventSubscriber, GCPResourceType
    
    # Initialize authentication
    auth_manager = GCPAuthManager(service_account_path="key.json")
    
    # Create subscriber
    subscriber = EventSubscriber(
        auth_manager=auth_manager,
        max_workers=10
    )
    
    # Register callback for compute instances
    def handle_vm_event(event):
        print(f"VM Event: {event.metadata.event_type.value}")
        print(f"Resource: {event.metadata.resource_name}")
    
    subscriber.register_callback(
        handle_vm_event,
        resource_type=GCPResourceType.COMPUTE_INSTANCE
    )
    
    # Subscribe to topic
    subscriber.subscribe(
        subscription_name="vm-events-sub",
        topic_name="gcp-resource-events",
        create_if_missing=True
    )
    
    # Start processing
    await subscriber.start()
    
    # ... process events ...
    
    # Stop gracefully
    await subscriber.stop()
    ```
"""

from .event_types import (
    GCPResourceType,
    EventType,
    EventPriority,
    EventMetadata,
    ResourceEvent
)

from .pubsub_client import PubSubClient

from .message_handler import (
    MessageHandler,
    MessageProcessingResult
)

from .subscriber import EventSubscriber

__all__ = [
    # Main subscriber
    "EventSubscriber",
    
    # Client components
    "PubSubClient",
    "MessageHandler",
    "MessageProcessingResult",
    
    # Event types
    "GCPResourceType",
    "EventType",
    "EventPriority",
    "EventMetadata",
    "ResourceEvent",
]

__version__ = "0.1.0"

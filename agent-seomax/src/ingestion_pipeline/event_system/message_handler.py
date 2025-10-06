"""
Message handler for processing Pub/Sub messages.

This module handles the processing of individual Pub/Sub messages,
including parsing, validation, callback execution, and error handling.
"""

import asyncio
import json
import base64
from typing import Callable, Dict, Any, Optional, List, Awaitable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import structlog

from .event_types import (
    ResourceEvent,
    EventMetadata,
    GCPResourceType,
    EventType,
    EventPriority
)

logger = structlog.get_logger(__name__)


@dataclass
class MessageProcessingResult:
    """Result of processing a Pub/Sub message."""
    
    success: bool
    event: Optional[ResourceEvent] = None
    error: Optional[str] = None
    processing_time_ms: Optional[float] = None
    callbacks_executed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "success": self.success,
            "error": self.error,
            "processing_time_ms": self.processing_time_ms,
            "callbacks_executed": self.callbacks_executed,
            "event_id": self.event.metadata.event_id if self.event else None,
            "event_type": self.event.metadata.event_type.value if self.event else None
        }


class MessageHandler:
    """
    Handler for processing Pub/Sub messages.
    
    Manages message parsing, validation, callback execution,
    and error handling for GCP resource events.
    """
    
    def __init__(
        self,
        max_workers: int = 10,
        enable_async: bool = True
    ):
        """
        Initialize the message handler.
        
        Args:
            max_workers: Maximum number of worker threads for processing
            enable_async: Whether to enable async message processing
        """
        self.logger = logger.bind(component="message_handler")
        
        # Callback registry: resource_type -> list of callbacks
        self._callbacks: Dict[GCPResourceType, List[Callable]] = {}
        
        # Wildcard callbacks (executed for all events)
        self._wildcard_callbacks: List[Callable] = []
        
        # Thread pool for parallel processing
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._enable_async = enable_async
        
        # Processing statistics
        self._stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "callbacks_executed": 0
        }
        
        self.logger.info(
            "message_handler_initialized",
            max_workers=max_workers,
            enable_async=enable_async
        )
    
    def register_callback(
        self,
        callback: Callable[[ResourceEvent], Any],
        resource_type: Optional[GCPResourceType] = None
    ) -> None:
        """
        Register a callback for processing events.
        
        Args:
            callback: Function to call when event is received
            resource_type: Specific resource type to filter (None for all events)
        """
        if resource_type is None:
            self._wildcard_callbacks.append(callback)
            self.logger.info(
                "wildcard_callback_registered",
                callback_name=callback.__name__
            )
        else:
            if resource_type not in self._callbacks:
                self._callbacks[resource_type] = []
            self._callbacks[resource_type].append(callback)
            self.logger.info(
                "callback_registered",
                callback_name=callback.__name__,
                resource_type=resource_type.value
            )
    
    def unregister_callback(
        self,
        callback: Callable[[ResourceEvent], Any],
        resource_type: Optional[GCPResourceType] = None
    ) -> bool:
        """
        Unregister a previously registered callback.
        
        Args:
            callback: The callback function to unregister
            resource_type: The resource type it was registered for
            
        Returns:
            True if callback was found and removed, False otherwise
        """
        try:
            if resource_type is None:
                self._wildcard_callbacks.remove(callback)
            else:
                if resource_type in self._callbacks:
                    self._callbacks[resource_type].remove(callback)
            
            self.logger.info(
                "callback_unregistered",
                callback_name=callback.__name__,
                resource_type=resource_type.value if resource_type else "wildcard"
            )
            return True
        except ValueError:
            self.logger.warning(
                "callback_not_found",
                callback_name=callback.__name__,
                resource_type=resource_type.value if resource_type else "wildcard"
            )
            return False
    
    def get_callbacks_for_event(self, event: ResourceEvent) -> List[Callable]:
        """
        Get all callbacks that should be executed for an event.
        
        Args:
            event: The resource event
            
        Returns:
            List of callback functions
        """
        callbacks = list(self._wildcard_callbacks)
        
        # Add resource-specific callbacks
        if event.metadata.resource_type in self._callbacks:
            callbacks.extend(self._callbacks[event.metadata.resource_type])
        
        return callbacks
    
    async def _execute_callback_async(
        self,
        callback: Callable,
        event: ResourceEvent
    ) -> bool:
        """
        Execute a callback asynchronously.
        
        Args:
            callback: The callback function to execute
            event: The resource event
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if callback is async
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                # Run sync callback in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self._executor, callback, event)
            
            self.logger.debug(
                "callback_executed",
                callback_name=callback.__name__,
                event_id=event.metadata.event_id
            )
            return True
        except Exception as e:
            self.logger.error(
                "callback_execution_failed",
                callback_name=callback.__name__,
                event_id=event.metadata.event_id,
                error=str(e),
                exc_info=True
            )
            return False
    
    def _execute_callback_sync(
        self,
        callback: Callable,
        event: ResourceEvent
    ) -> bool:
        """
        Execute a callback synchronously.
        
        Args:
            callback: The callback function to execute
            event: The resource event
            
        Returns:
            True if successful, False otherwise
        """
        try:
            callback(event)
            self.logger.debug(
                "callback_executed",
                callback_name=callback.__name__,
                event_id=event.metadata.event_id
            )
            return True
        except Exception as e:
            self.logger.error(
                "callback_execution_failed",
                callback_name=callback.__name__,
                event_id=event.metadata.event_id,
                error=str(e),
                exc_info=True
            )
            return False
    
    def _parse_message_data(self, message_data: bytes) -> Dict[str, Any]:
        """
        Parse message data from bytes to dictionary.
        
        Args:
            message_data: Raw message data
            
        Returns:
            Parsed message data
            
        Raises:
            ValueError: If message data cannot be parsed
        """
        try:
            # Decode base64 if needed
            try:
                decoded = base64.b64decode(message_data)
            except Exception:
                decoded = message_data
            
            # Parse JSON
            if isinstance(decoded, bytes):
                decoded = decoded.decode('utf-8')
            
            return json.loads(decoded)
        except Exception as e:
            self.logger.error(
                "message_parsing_failed",
                error=str(e)
            )
            raise ValueError(f"Failed to parse message data: {e}")
    
    async def process_message_async(
        self,
        message_data: bytes,
        message_attributes: Dict[str, str]
    ) -> MessageProcessingResult:
        """
        Process a Pub/Sub message asynchronously.
        
        Args:
            message_data: Raw message data
            message_attributes: Message attributes
            
        Returns:
            MessageProcessingResult with processing details
        """
        import time
        start_time = time.time()
        
        try:
            # Parse message data
            parsed_data = self._parse_message_data(message_data)
            
            # Create resource event
            event = ResourceEvent.from_pubsub_message(parsed_data, message_attributes)
            
            # Log event details
            priority = EventPriority.get_priority_for_event(event)
            self.logger.info(
                "event_received",
                event_id=event.metadata.event_id,
                event_type=event.metadata.event_type.value,
                resource_type=event.metadata.resource_type.value,
                resource_name=event.metadata.resource_name,
                priority=priority.name
            )
            
            # Get callbacks for this event
            callbacks = self.get_callbacks_for_event(event)
            
            if not callbacks:
                self.logger.warning(
                    "no_callbacks_registered",
                    event_id=event.metadata.event_id,
                    resource_type=event.metadata.resource_type.value
                )
            
            # Execute callbacks
            callbacks_executed = 0
            for callback in callbacks:
                success = await self._execute_callback_async(callback, event)
                if success:
                    callbacks_executed += 1
            
            # Update statistics
            self._stats["total_processed"] += 1
            self._stats["successful"] += 1
            self._stats["callbacks_executed"] += callbacks_executed
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            self.logger.info(
                "message_processed",
                event_id=event.metadata.event_id,
                callbacks_executed=callbacks_executed,
                processing_time_ms=processing_time
            )
            
            return MessageProcessingResult(
                success=True,
                event=event,
                processing_time_ms=processing_time,
                callbacks_executed=callbacks_executed
            )
            
        except Exception as e:
            self._stats["total_processed"] += 1
            self._stats["failed"] += 1
            
            processing_time = (time.time() - start_time) * 1000
            
            self.logger.error(
                "message_processing_failed",
                error=str(e),
                processing_time_ms=processing_time,
                exc_info=True
            )
            
            return MessageProcessingResult(
                success=False,
                error=str(e),
                processing_time_ms=processing_time
            )
    
    def process_message_sync(
        self,
        message_data: bytes,
        message_attributes: Dict[str, str]
    ) -> MessageProcessingResult:
        """
        Process a Pub/Sub message synchronously.
        
        Args:
            message_data: Raw message data
            message_attributes: Message attributes
            
        Returns:
            MessageProcessingResult with processing details
        """
        import time
        start_time = time.time()
        
        try:
            # Parse message data
            parsed_data = self._parse_message_data(message_data)
            
            # Create resource event
            event = ResourceEvent.from_pubsub_message(parsed_data, message_attributes)
            
            # Log event details
            priority = EventPriority.get_priority_for_event(event)
            self.logger.info(
                "event_received",
                event_id=event.metadata.event_id,
                event_type=event.metadata.event_type.value,
                resource_type=event.metadata.resource_type.value,
                resource_name=event.metadata.resource_name,
                priority=priority.name
            )
            
            # Get callbacks for this event
            callbacks = self.get_callbacks_for_event(event)
            
            if not callbacks:
                self.logger.warning(
                    "no_callbacks_registered",
                    event_id=event.metadata.event_id,
                    resource_type=event.metadata.resource_type.value
                )
            
            # Execute callbacks
            callbacks_executed = 0
            for callback in callbacks:
                success = self._execute_callback_sync(callback, event)
                if success:
                    callbacks_executed += 1
            
            # Update statistics
            self._stats["total_processed"] += 1
            self._stats["successful"] += 1
            self._stats["callbacks_executed"] += callbacks_executed
            
            processing_time = (time.time() - start_time) * 1000
            
            self.logger.info(
                "message_processed",
                event_id=event.metadata.event_id,
                callbacks_executed=callbacks_executed,
                processing_time_ms=processing_time
            )
            
            return MessageProcessingResult(
                success=True,
                event=event,
                processing_time_ms=processing_time,
                callbacks_executed=callbacks_executed
            )
            
        except Exception as e:
            self._stats["total_processed"] += 1
            self._stats["failed"] += 1
            
            processing_time = (time.time() - start_time) * 1000
            
            self.logger.error(
                "message_processing_failed",
                error=str(e),
                processing_time_ms=processing_time,
                exc_info=True
            )
            
            return MessageProcessingResult(
                success=False,
                error=str(e),
                processing_time_ms=processing_time
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary containing statistics
        """
        return {
            **self._stats,
            "registered_callbacks": {
                resource_type.value: len(callbacks)
                for resource_type, callbacks in self._callbacks.items()
            },
            "wildcard_callbacks": len(self._wildcard_callbacks)
        }
    
    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self._stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "callbacks_executed": 0
        }
        self.logger.info("statistics_reset")
    
    def shutdown(self) -> None:
        """Shutdown the message handler and cleanup resources."""
        self.logger.info("shutting_down_message_handler")
        self._executor.shutdown(wait=True)
        self.logger.info("message_handler_shutdown_complete")

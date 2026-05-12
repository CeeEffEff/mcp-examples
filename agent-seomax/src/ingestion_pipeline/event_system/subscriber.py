"""
Event subscriber for managing Pub/Sub subscriptions and processing events.

This module provides the main orchestration for event subscription,
managing the subscription lifecycle, health monitoring, and coordinating
between the Pub/Sub client and message handler.
"""

import asyncio
import threading
from typing import Optional, Dict, Any, Callable, List
from concurrent.futures import TimeoutError
from google.cloud.pubsub_v1.subscriber.message import Message
import structlog

from .pubsub_client import PubSubClient
from .message_handler import MessageHandler, MessageProcessingResult
from .event_types import GCPResourceType, ResourceEvent
from ..api_client.auth import GCPAuthManager


logger = structlog.get_logger(__name__)


class EventSubscriber:
    """
    Main event subscriber for managing GCP Pub/Sub subscriptions.
    
    Coordinates subscription management, message processing, health monitoring,
    and graceful shutdown.
    """
    
    def __init__(
        self,
        auth_manager: GCPAuthManager,
        project_id: Optional[str] = None,
        max_workers: int = 10,
        max_messages: int = 100,
        ack_deadline: int = 60
    ):
        """
        Initialize the event subscriber.
        
        Args:
            auth_manager: GCPAuthManager for authentication
            project_id: GCP project ID
            max_workers: Maximum concurrent message processing workers
            max_messages: Maximum messages to pull at once
            ack_deadline: Message acknowledgment deadline in seconds
        """
        self.auth_manager = auth_manager
        self.project_id = project_id or auth_manager.get_project_id()
        
        self.logger = logger.bind(
            component="event_subscriber",
            project_id=self.project_id
        )
        
        # Initialize clients
        self.pubsub_client = PubSubClient(auth_manager, self.project_id)
        self.message_handler = MessageHandler(
            max_workers=max_workers,
            enable_async=True
        )
        
        # Subscription settings
        self.max_messages = max_messages
        self.ack_deadline = ack_deadline
        
        # Active subscriptions tracking
        self._subscriptions: Dict[str, Any] = {}
        self._subscription_futures: Dict[str, Any] = {}
        self._is_running = False
        self._shutdown_event = threading.Event()
        
        # Health monitoring
        self._health_check_interval = 60  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        
        self.logger.info(
            "event_subscriber_initialized",
            max_workers=max_workers,
            max_messages=max_messages,
            ack_deadline=ack_deadline
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
            resource_type: Specific resource type to filter (None for all)
        """
        self.message_handler.register_callback(callback, resource_type)
        self.logger.info(
            "callback_registered",
            callback_name=callback.__name__,
            resource_type=resource_type.value if resource_type else "all"
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
            True if callback was found and removed
        """
        return self.message_handler.unregister_callback(callback, resource_type)
    
    def _message_callback(self, message: Message) -> None:
        """
        Callback for handling incoming Pub/Sub messages.
        
        Args:
            message: The Pub/Sub message
        """
        try:
            # Extract message data and attributes
            message_data = message.data
            message_attributes = dict(message.attributes)
            
            # Process message synchronously (Pub/Sub callback must be sync)
            result = self.message_handler.process_message_sync(
                message_data,
                message_attributes
            )
            
            if result.success:
                # Acknowledge successful processing
                message.ack()
                self.logger.debug(
                    "message_acknowledged",
                    message_id=message.message_id,
                    event_id=result.event.metadata.event_id if result.event else None
                )
            else:
                # Negative acknowledgment - message will be redelivered
                message.nack()
                self.logger.warning(
                    "message_nacked",
                    message_id=message.message_id,
                    error=result.error
                )
        except Exception as e:
            self.logger.error(
                "message_callback_failed",
                message_id=message.message_id,
                error=str(e),
                exc_info=True
            )
            # Nack on unexpected errors
            message.nack()
    
    def subscribe(
        self,
        subscription_name: str,
        topic_name: Optional[str] = None,
        create_if_missing: bool = True,
        filter_expression: Optional[str] = None
    ) -> str:
        """
        Subscribe to a Pub/Sub topic.
        
        Args:
            subscription_name: Name of the subscription
            topic_name: Name of the topic (required if create_if_missing=True)
            create_if_missing: Create subscription if it doesn't exist
            filter_expression: Optional filter for messages
            
        Returns:
            Subscription path
            
        Raises:
            ValueError: If subscription is invalid or already active
        """
        if subscription_name in self._subscriptions:
            raise ValueError(f"Subscription '{subscription_name}' is already active")
        
        # Create subscription if requested
        if create_if_missing:
            if not topic_name:
                raise ValueError("topic_name is required when create_if_missing=True")
            
            subscription_path = self.pubsub_client.create_subscription(
                subscription_name=subscription_name,
                topic_name=topic_name,
                ack_deadline_seconds=self.ack_deadline,
                filter_expression=filter_expression
            )
        else:
            subscription_path = self.pubsub_client._get_subscription_path(subscription_name)
        
        # Create streaming pull future
        flow_control = {
            "max_messages": self.max_messages,
            "max_bytes": 100 * 1024 * 1024,  # 100 MB
        }
        
        streaming_pull_future = self.pubsub_client.subscriber.subscribe(
            subscription_path,
            callback=self._message_callback,
            flow_control=flow_control
        )
        
        # Store subscription info
        self._subscriptions[subscription_name] = {
            "path": subscription_path,
            "topic": topic_name,
            "future": streaming_pull_future,
            "filter": filter_expression
        }
        
        self.logger.info(
            "subscription_started",
            subscription_name=subscription_name,
            topic_name=topic_name,
            subscription_path=subscription_path
        )
        
        return subscription_path
    
    def unsubscribe(
        self,
        subscription_name: str,
        delete_subscription: bool = False
    ) -> None:
        """
        Unsubscribe from a subscription.
        
        Args:
            subscription_name: Name of the subscription to stop
            delete_subscription: Whether to delete the subscription
        """
        if subscription_name not in self._subscriptions:
            self.logger.warning(
                "subscription_not_found",
                subscription_name=subscription_name
            )
            return
        
        subscription_info = self._subscriptions[subscription_name]
        future = subscription_info["future"]
        
        try:
            # Cancel the streaming pull
            future.cancel()
            
            # Wait for cancellation with timeout
            try:
                future.result(timeout=30)
            except TimeoutError:
                self.logger.warning(
                    "subscription_cancellation_timeout",
                    subscription_name=subscription_name
                )
            except Exception as e:
                # Expected when canceling
                self.logger.debug(
                    "subscription_cancelled",
                    subscription_name=subscription_name,
                    error=str(e)
                )
            
            # Delete subscription if requested
            if delete_subscription:
                self.pubsub_client.delete_subscription(subscription_name)
            
            # Remove from tracking
            del self._subscriptions[subscription_name]
            
            self.logger.info(
                "subscription_stopped",
                subscription_name=subscription_name,
                deleted=delete_subscription
            )
        except Exception as e:
            self.logger.error(
                "unsubscribe_failed",
                subscription_name=subscription_name,
                error=str(e),
                exc_info=True
            )
            raise
    
    def list_active_subscriptions(self) -> List[str]:
        """
        List all active subscriptions.
        
        Returns:
            List of active subscription names
        """
        return list(self._subscriptions.keys())
    
    def get_subscription_info(self, subscription_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an active subscription.
        
        Args:
            subscription_name: Name of the subscription
            
        Returns:
            Subscription information dictionary or None if not found
        """
        if subscription_name not in self._subscriptions:
            return None
        
        info = self._subscriptions[subscription_name].copy()
        # Remove future from returned info (not serializable)
        info.pop("future", None)
        
        # Add health status
        future = self._subscriptions[subscription_name]["future"]
        info["is_running"] = future.running()
        info["is_cancelled"] = future.cancelled()
        
        return info
    
    async def _health_check_loop(self) -> None:
        """Background task for monitoring subscription health."""
        while self._is_running and not self._shutdown_event.is_set():
            try:
                # Check Pub/Sub connection health
                is_healthy = self.pubsub_client.check_health()
                
                if not is_healthy:
                    self.logger.error("pubsub_connection_unhealthy")
                
                # Check each subscription
                for sub_name, sub_info in self._subscriptions.items():
                    future = sub_info["future"]
                    
                    if future.cancelled():
                        self.logger.warning(
                            "subscription_cancelled",
                            subscription_name=sub_name
                        )
                    elif future.done():
                        # Check for errors
                        try:
                            future.result()
                        except Exception as e:
                            self.logger.error(
                                "subscription_error",
                                subscription_name=sub_name,
                                error=str(e)
                            )
                
                # Wait for next health check
                await asyncio.sleep(self._health_check_interval)
                
            except Exception as e:
                self.logger.error(
                    "health_check_error",
                    error=str(e),
                    exc_info=True
                )
                await asyncio.sleep(self._health_check_interval)
    
    async def start(self) -> None:
        """Start the event subscriber and health monitoring."""
        if self._is_running:
            self.logger.warning("subscriber_already_running")
            return
        
        self._is_running = True
        self._shutdown_event.clear()
        
        # Start health check loop
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        self.logger.info("subscriber_started")
    
    async def stop(self, timeout: int = 30) -> None:
        """
        Stop the event subscriber gracefully.
        
        Args:
            timeout: Maximum time to wait for shutdown in seconds
        """
        if not self._is_running:
            self.logger.warning("subscriber_not_running")
            return
        
        self.logger.info("stopping_subscriber")
        
        # Signal shutdown
        self._is_running = False
        self._shutdown_event.set()
        
        # Cancel health check
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await asyncio.wait_for(self._health_check_task, timeout=5)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
        
        # Stop all subscriptions
        subscription_names = list(self._subscriptions.keys())
        for sub_name in subscription_names:
            try:
                self.unsubscribe(sub_name, delete_subscription=False)
            except Exception as e:
                self.logger.error(
                    "error_stopping_subscription",
                    subscription_name=sub_name,
                    error=str(e)
                )
        
        # Shutdown message handler
        self.message_handler.shutdown()
        
        # Close Pub/Sub client
        self.pubsub_client.close()
        
        self.logger.info("subscriber_stopped")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary containing statistics
        """
        stats = self.message_handler.get_statistics()
        stats["active_subscriptions"] = len(self._subscriptions)
        stats["subscription_details"] = {
            name: {
                "topic": info["topic"],
                "is_running": info["future"].running(),
                "is_cancelled": info["future"].cancelled()
            }
            for name, info in self._subscriptions.items()
        }
        return stats
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - synchronous cleanup."""
        # Create event loop if needed for async stop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if self._is_running:
            loop.run_until_complete(self.stop())
        
        return False

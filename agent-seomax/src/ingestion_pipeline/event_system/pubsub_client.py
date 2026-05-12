"""
Pub/Sub client wrapper for managing GCP Pub/Sub operations.

This module provides a wrapper around the Google Cloud Pub/Sub client
with authentication, error handling, and subscription management.
"""

import asyncio
from typing import Optional, List, Dict, Any, Callable
from google.cloud import pubsub_v1
from google.api_core import retry
from google.api_core.exceptions import AlreadyExists, NotFound, GoogleAPIError
import structlog

from ..api_client.auth import GCPAuthManager


logger = structlog.get_logger(__name__)


class PubSubClient:
    """
    Client for managing Google Cloud Pub/Sub operations.
    
    Provides methods for creating topics and subscriptions, managing
    subscriptions, and handling Pub/Sub operations with proper
    authentication and error handling.
    """
    
    def __init__(
        self,
        auth_manager: GCPAuthManager,
        project_id: Optional[str] = None
    ):
        """
        Initialize the Pub/Sub client.
        
        Args:
            auth_manager: GCPAuthManager instance for authentication
            project_id: GCP project ID (uses auth_manager's if not provided)
        """
        self.auth_manager = auth_manager
        self.project_id = project_id or auth_manager.get_project_id()
        
        if not self.project_id:
            raise ValueError("Project ID must be provided or available from auth_manager")
        
        self.logger = logger.bind(
            component="pubsub_client",
            project_id=self.project_id
        )
        
        # Initialize publisher and subscriber clients
        credentials = auth_manager.authenticate()
        self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
        self.subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        
        self.logger.info("pubsub_client_initialized")
    
    def _get_topic_path(self, topic_name: str) -> str:
        """Get the full topic path."""
        return self.publisher.topic_path(self.project_id, topic_name)
    
    def _get_subscription_path(self, subscription_name: str) -> str:
        """Get the full subscription path."""
        return self.subscriber.subscription_path(self.project_id, subscription_name)
    
    def create_topic(self, topic_name: str) -> str:
        """
        Create a Pub/Sub topic.
        
        Args:
            topic_name: Name of the topic to create
            
        Returns:
            Full topic path
            
        Raises:
            GoogleAPIError: If topic creation fails
        """
        topic_path = self._get_topic_path(topic_name)
        
        try:
            topic = self.publisher.create_topic(request={"name": topic_path})
            self.logger.info(
                "topic_created",
                topic_name=topic_name,
                topic_path=topic_path
            )
            return topic.name
        except AlreadyExists:
            self.logger.info(
                "topic_already_exists",
                topic_name=topic_name,
                topic_path=topic_path
            )
            return topic_path
        except GoogleAPIError as e:
            self.logger.error(
                "topic_creation_failed",
                topic_name=topic_name,
                error=str(e)
            )
            raise
    
    def delete_topic(self, topic_name: str) -> None:
        """
        Delete a Pub/Sub topic.
        
        Args:
            topic_name: Name of the topic to delete
            
        Raises:
            GoogleAPIError: If topic deletion fails
        """
        topic_path = self._get_topic_path(topic_name)
        
        try:
            self.publisher.delete_topic(request={"topic": topic_path})
            self.logger.info(
                "topic_deleted",
                topic_name=topic_name,
                topic_path=topic_path
            )
        except NotFound:
            self.logger.warning(
                "topic_not_found",
                topic_name=topic_name,
                topic_path=topic_path
            )
        except GoogleAPIError as e:
            self.logger.error(
                "topic_deletion_failed",
                topic_name=topic_name,
                error=str(e)
            )
            raise
    
    def create_subscription(
        self,
        subscription_name: str,
        topic_name: str,
        ack_deadline_seconds: int = 60,
        message_retention_duration: int = 604800,  # 7 days
        filter_expression: Optional[str] = None
    ) -> str:
        """
        Create a Pub/Sub subscription.
        
        Args:
            subscription_name: Name of the subscription
            topic_name: Name of the topic to subscribe to
            ack_deadline_seconds: Message acknowledgment deadline (default: 60s)
            message_retention_duration: How long to retain unacknowledged messages (default: 7 days)
            filter_expression: Optional filter for messages
            
        Returns:
            Full subscription path
            
        Raises:
            GoogleAPIError: If subscription creation fails
        """
        topic_path = self._get_topic_path(topic_name)
        subscription_path = self._get_subscription_path(subscription_name)
        
        request = {
            "name": subscription_path,
            "topic": topic_path,
            "ack_deadline_seconds": ack_deadline_seconds,
            "message_retention_duration": {"seconds": message_retention_duration}
        }
        
        if filter_expression:
            request["filter"] = filter_expression
        
        try:
            subscription = self.subscriber.create_subscription(request=request)
            self.logger.info(
                "subscription_created",
                subscription_name=subscription_name,
                topic_name=topic_name,
                subscription_path=subscription_path,
                ack_deadline=ack_deadline_seconds,
                filter=filter_expression
            )
            return subscription.name
        except AlreadyExists:
            self.logger.info(
                "subscription_already_exists",
                subscription_name=subscription_name,
                subscription_path=subscription_path
            )
            return subscription_path
        except GoogleAPIError as e:
            self.logger.error(
                "subscription_creation_failed",
                subscription_name=subscription_name,
                topic_name=topic_name,
                error=str(e)
            )
            raise
    
    def delete_subscription(self, subscription_name: str) -> None:
        """
        Delete a Pub/Sub subscription.
        
        Args:
            subscription_name: Name of the subscription to delete
            
        Raises:
            GoogleAPIError: If subscription deletion fails
        """
        subscription_path = self._get_subscription_path(subscription_name)
        
        try:
            self.subscriber.delete_subscription(
                request={"subscription": subscription_path}
            )
            self.logger.info(
                "subscription_deleted",
                subscription_name=subscription_name,
                subscription_path=subscription_path
            )
        except NotFound:
            self.logger.warning(
                "subscription_not_found",
                subscription_name=subscription_name,
                subscription_path=subscription_path
            )
        except GoogleAPIError as e:
            self.logger.error(
                "subscription_deletion_failed",
                subscription_name=subscription_name,
                error=str(e)
            )
            raise
    
    def list_subscriptions(self, topic_name: Optional[str] = None) -> List[str]:
        """
        List all subscriptions in the project or for a specific topic.
        
        Args:
            topic_name: Optional topic name to filter subscriptions
            
        Returns:
            List of subscription names
        """
        try:
            if topic_name:
                topic_path = self._get_topic_path(topic_name)
                request = {"topic": topic_path}
                subscriptions = self.publisher.list_topic_subscriptions(request=request)
            else:
                project_path = f"projects/{self.project_id}"
                request = {"project": project_path}
                subscriptions = self.subscriber.list_subscriptions(request=request)
                subscriptions = [sub.name for sub in subscriptions]
            
            subscription_list = list(subscriptions)
            self.logger.info(
                "subscriptions_listed",
                topic_name=topic_name,
                count=len(subscription_list)
            )
            return subscription_list
        except GoogleAPIError as e:
            self.logger.error(
                "list_subscriptions_failed",
                topic_name=topic_name,
                error=str(e)
            )
            raise
    
    def get_subscription_info(self, subscription_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a subscription.
        
        Args:
            subscription_name: Name of the subscription
            
        Returns:
            Dictionary containing subscription information
        """
        subscription_path = self._get_subscription_path(subscription_name)
        
        try:
            subscription = self.subscriber.get_subscription(
                request={"subscription": subscription_path}
            )
            
            info = {
                "name": subscription.name,
                "topic": subscription.topic,
                "ack_deadline_seconds": subscription.ack_deadline_seconds,
                "retain_acked_messages": subscription.retain_acked_messages,
                "message_retention_duration": subscription.message_retention_duration.seconds,
                "expiration_policy": subscription.expiration_policy,
                "filter": subscription.filter if hasattr(subscription, "filter") else None
            }
            
            self.logger.debug(
                "subscription_info_retrieved",
                subscription_name=subscription_name,
                info=info
            )
            return info
        except NotFound:
            self.logger.error(
                "subscription_not_found",
                subscription_name=subscription_name
            )
            raise
        except GoogleAPIError as e:
            self.logger.error(
                "get_subscription_info_failed",
                subscription_name=subscription_name,
                error=str(e)
            )
            raise
    
    def update_subscription_ack_deadline(
        self,
        subscription_name: str,
        ack_deadline_seconds: int
    ) -> None:
        """
        Update the acknowledgment deadline for a subscription.
        
        Args:
            subscription_name: Name of the subscription
            ack_deadline_seconds: New acknowledgment deadline in seconds
        """
        subscription_path = self._get_subscription_path(subscription_name)
        
        try:
            subscription = self.subscriber.get_subscription(
                request={"subscription": subscription_path}
            )
            subscription.ack_deadline_seconds = ack_deadline_seconds
            
            update_mask = {"paths": ["ack_deadline_seconds"]}
            self.subscriber.update_subscription(
                request={
                    "subscription": subscription,
                    "update_mask": update_mask
                }
            )
            
            self.logger.info(
                "subscription_ack_deadline_updated",
                subscription_name=subscription_name,
                new_deadline=ack_deadline_seconds
            )
        except GoogleAPIError as e:
            self.logger.error(
                "update_ack_deadline_failed",
                subscription_name=subscription_name,
                error=str(e)
            )
            raise
    
    def publish_message(
        self,
        topic_name: str,
        data: bytes,
        attributes: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Publish a message to a topic.
        
        Args:
            topic_name: Name of the topic
            data: Message data as bytes
            attributes: Optional message attributes
            
        Returns:
            Message ID
        """
        topic_path = self._get_topic_path(topic_name)
        
        try:
            future = self.publisher.publish(
                topic_path,
                data,
                **(attributes or {})
            )
            message_id = future.result()
            
            self.logger.debug(
                "message_published",
                topic_name=topic_name,
                message_id=message_id,
                data_size=len(data)
            )
            return message_id
        except GoogleAPIError as e:
            self.logger.error(
                "publish_message_failed",
                topic_name=topic_name,
                error=str(e)
            )
            raise
    
    def check_health(self) -> bool:
        """
        Check if the Pub/Sub connection is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            project_path = f"projects/{self.project_id}"
            list(self.subscriber.list_subscriptions(
                request={"project": project_path, "page_size": 1}
            ))
            self.logger.debug("health_check_passed")
            return True
        except Exception as e:
            self.logger.error(
                "health_check_failed",
                error=str(e)
            )
            return False
    
    def close(self) -> None:
        """Close the Pub/Sub clients."""
        try:
            # Close publisher
            if hasattr(self.publisher, 'api') and hasattr(self.publisher.api, '_transport'):
                self.publisher.api._transport.close()
            
            # Close subscriber  
            if hasattr(self.subscriber, 'api') and hasattr(self.subscriber.api, '_transport'):
                self.subscriber.api._transport.close()
            
            self.logger.info("pubsub_client_closed")
        except Exception as e:
            self.logger.warning(
                "error_closing_pubsub_client",
                error=str(e)
            )

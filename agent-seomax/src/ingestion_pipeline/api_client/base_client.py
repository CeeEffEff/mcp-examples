"""
Base GCP API Client

Provides common functionality for all GCP API clients including:
- Rate limiting
- Pagination handling
- Retry logic with exponential backoff
- Error handling
"""

import time
from typing import Optional, Dict, Any, List, Callable, Iterator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import structlog
from google.api_core import retry, exceptions
from google.auth.credentials import Credentials

logger = structlog.get_logger(__name__)


class ResourceType(Enum):
    """Enumeration of GCP resource types."""
    VIRTUAL_MACHINE = "virtual_machine"
    PERSISTENT_DISK = "persistent_disk"
    INSTANCE_GROUP = "instance_group"
    GKE_CLUSTER = "gke_cluster"
    CLOUD_FUNCTION = "cloud_function"
    CLOUD_RUN_SERVICE = "cloud_run_service"
    VPC_NETWORK = "vpc_network"
    SUBNETWORK = "subnetwork"
    FIREWALL_RULE = "firewall_rule"
    LOAD_BALANCER = "load_balancer"
    CLOUD_ROUTER = "cloud_router"
    STORAGE_BUCKET = "storage_bucket"
    CLOUD_SQL_INSTANCE = "cloud_sql_instance"
    IAM_SERVICE_ACCOUNT = "iam_service_account"
    PUBSUB_TOPIC = "pubsub_topic"
    PUBSUB_SUBSCRIPTION = "pubsub_subscription"


@dataclass
class RateLimitConfig:
    """Configuration for API rate limiting."""
    requests_per_second: float = 10.0
    burst_size: int = 20
    

@dataclass
class RetryConfig:
    """Configuration for API retry logic."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0


class GCPAPIError(Exception):
    """Base exception for GCP API errors."""
    pass


class RateLimitExceeded(GCPAPIError):
    """Raised when API rate limit is exceeded."""
    pass


class TokenBucket:
    """
    Token bucket algorithm for rate limiting.
    
    Allows burst traffic while maintaining average rate limit.
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.
        
        Args:
            rate: Tokens per second
            capacity: Maximum burst capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def _refill(self):
        """Refill bucket based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        
        # Add tokens based on time elapsed
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now
    
    def wait_time(self, tokens: int = 1) -> float:
        """
        Calculate wait time needed for tokens.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Time in seconds to wait
        """
        self._refill()
        
        if self.tokens >= tokens:
            return 0.0
        
        needed = tokens - self.tokens
        return needed / self.rate


class BaseGCPClient(ABC):
    """
    Abstract base class for GCP API clients.
    
    Provides common functionality for all GCP service clients.
    """
    
    def __init__(
        self,
        credentials: Credentials,
        project_id: str,
        rate_limit_config: Optional[RateLimitConfig] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize base GCP client.
        
        Args:
            credentials: GCP credentials
            project_id: GCP project ID
            rate_limit_config: Rate limiting configuration
            retry_config: Retry logic configuration
        """
        self.credentials = credentials
        self.project_id = project_id
        
        # Rate limiting
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self.rate_limiter = TokenBucket(
            rate=self.rate_limit_config.requests_per_second,
            capacity=self.rate_limit_config.burst_size
        )
        
        # Retry configuration
        self.retry_config = retry_config or RetryConfig()
        self._retry_predicate = self._create_retry_predicate()
        
        logger.info(
            "Initialized GCP client",
            client_type=self.__class__.__name__,
            project_id=project_id,
            rate_limit=self.rate_limit_config.requests_per_second
        )
    
    @abstractmethod
    def get_resource_type(self) -> ResourceType:
        """
        Get the resource type handled by this client.
        
        Returns:
            ResourceType enum value
        """
        pass
    
    def _create_retry_predicate(self) -> retry.Retry:
        """
        Create retry predicate for API calls.
        
        Returns:
            Retry configuration for google-api-core
        """
        return retry.Retry(
            initial=self.retry_config.initial_delay,
            maximum=self.retry_config.max_delay,
            multiplier=self.retry_config.exponential_base,
            predicate=retry.if_exception_type(
                exceptions.TooManyRequests,
                exceptions.ServiceUnavailable,
                exceptions.DeadlineExceeded,
                exceptions.InternalServerError
            )
        )
    
    def _wait_for_rate_limit(self):
        """Wait for rate limit if necessary."""
        while not self.rate_limiter.consume():
            wait_time = self.rate_limiter.wait_time()
            if wait_time > 0:
                logger.debug(
                    "Rate limit reached, waiting",
                    wait_time=wait_time,
                    client_type=self.__class__.__name__
                )
                time.sleep(wait_time)
    
    def _execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute API call with retry logic and rate limiting.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            GCPAPIError: If API call fails after retries
        """
        self._wait_for_rate_limit()
        
        try:
            # Use google-api-core retry decorator
            decorated_func = self._retry_predicate(func)
            result = decorated_func(*args, **kwargs)
            
            logger.debug(
                "API call successful",
                function=func.__name__,
                client_type=self.__class__.__name__
            )
            
            return result
            
        except exceptions.GoogleAPIError as e:
            logger.error(
                "API call failed",
                function=func.__name__,
                error=str(e),
                error_code=getattr(e, 'code', None)
            )
            raise GCPAPIError(f"GCP API call failed: {str(e)}")
        
        except Exception as e:
            logger.error(
                "Unexpected error in API call",
                function=func.__name__,
                error=str(e)
            )
            raise GCPAPIError(f"Unexpected error: {str(e)}")
    
    def _paginate(
        self,
        list_func: Callable,
        *args,
        max_results: Optional[int] = None,
        **kwargs
    ) -> Iterator[Any]:
        """
        Handle pagination for list operations.
        
        Args:
            list_func: Function that returns paginated results
            *args: Positional arguments for list_func
            max_results: Maximum number of results to return
            **kwargs: Keyword arguments for list_func
            
        Yields:
            Individual items from paginated results
        """
        results_count = 0
        page_token = None
        
        while True:
            # Add page token if available
            if page_token:
                kwargs['page_token'] = page_token
            
            # Execute list operation with retry
            response = self._execute_with_retry(list_func, *args, **kwargs)
            
            # Yield items from current page
            items = self._extract_items_from_response(response)
            for item in items:
                yield item
                results_count += 1
                
                if max_results and results_count >= max_results:
                    return
            
            # Check for next page
            page_token = self._extract_next_page_token(response)
            if not page_token:
                break
            
            logger.debug(
                "Fetching next page",
                results_so_far=results_count,
                client_type=self.__class__.__name__
            )
    
    @abstractmethod
    def _extract_items_from_response(self, response: Any) -> List[Any]:
        """
        Extract items from API response.
        
        Args:
            response: API response object
            
        Returns:
            List of items from response
        """
        pass
    
    @abstractmethod
    def _extract_next_page_token(self, response: Any) -> Optional[str]:
        """
        Extract next page token from API response.
        
        Args:
            response: API response object
            
        Returns:
            Next page token or None if no more pages
        """
        pass
    
    @abstractmethod
    def list_resources(
        self,
        region: Optional[str] = None,
        zone: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List all resources of this type.
        
        Args:
            region: GCP region to filter by
            zone: GCP zone to filter by
            filters: Additional filters
            
        Returns:
            List of resource dictionaries
        """
        pass
    
    @abstractmethod
    def get_resource(self, resource_id: str) -> Dict[str, Any]:
        """
        Get a specific resource by ID.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Resource dictionary
        """
        pass

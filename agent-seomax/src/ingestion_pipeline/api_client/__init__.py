"""
GCP API Client Package

Provides authentication and API clients for interacting with GCP services.
"""

from .auth import GCPAuthManager, GCPAuthenticationError
from .base_client import (
    BaseGCPClient,
    ResourceType,
    RateLimitConfig,
    RetryConfig,
    GCPAPIError,
    RateLimitExceeded
)
from .compute_client import ComputeEngineClient
from .client_manager import GCPClientManager

__all__ = [
    # Authentication
    'GCPAuthManager',
    'GCPAuthenticationError',
    
    # Base classes
    'BaseGCPClient',
    'ResourceType',
    'RateLimitConfig',
    'RetryConfig',
    'GCPAPIError',
    'RateLimitExceeded',
    
    # Clients
    'ComputeEngineClient',
    'GCPClientManager',
]

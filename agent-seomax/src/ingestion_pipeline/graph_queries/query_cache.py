"""
Query Cache Module

This module provides LRU (Least Recently Used) caching functionality for Neo4j queries
to improve performance for frequently executed queries. It includes TTL-based expiration,
cache statistics tracking, and integration with the monitoring system.

Author: GCP Digital Twin Agent System
Date: 2025-01-06
"""

from typing import Dict, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json
from collections import OrderedDict
import threading

from ..monitoring import get_logger, get_metrics

logger = get_logger("QueryCache")
metrics = get_metrics()


class CacheEntry:
    """
    Represents a single cached query result with metadata.
    
    Attributes:
        data: The cached query result data
        timestamp: When the entry was cached
        ttl_seconds: Time-to-live in seconds
        hits: Number of cache hits for this entry
        query_hash: Hash of the query that produced this result
    """
    
    def __init__(self, data: Any, ttl_seconds: int, query_hash: str):
        """
        Initialize a cache entry.
        
        Args:
            data: Query result data to cache
            ttl_seconds: Time-to-live in seconds
            query_hash: Hash of the query
        """
        self.data = data
        self.timestamp = datetime.utcnow()
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.query_hash = query_hash
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl_seconds <= 0:
            return False  # Never expires
        
        age = (datetime.utcnow() - self.timestamp).total_seconds()
        return age >= self.ttl_seconds
    
    def increment_hits(self):
        """Increment the hit counter."""
        self.hits += 1
    
    def get_age_seconds(self) -> float:
        """Get the age of the entry in seconds."""
        return (datetime.utcnow() - self.timestamp).total_seconds()


class QueryCache:
    """
    LRU cache for Neo4j query results with TTL-based expiration.
    
    This cache uses an OrderedDict to maintain LRU ordering and provides
    thread-safe operations for concurrent query execution. It tracks cache
    statistics and integrates with the monitoring system.
    
    Features:
    - LRU eviction policy
    - TTL-based expiration
    - Thread-safe operations
    - Cache statistics tracking
    - Configurable cache size
    - Query hash-based keys
    
    Examples:
        >>> from ingestion_pipeline.graph_queries import get_query_cache
        >>> cache = get_query_cache()
        >>> 
        >>> # Cache a query result
        >>> cache.set("my_query_key", result_data, ttl_seconds=300)
        >>> 
        >>> # Retrieve from cache
        >>> cached_data = cache.get("my_query_key")
        >>> if cached_data is not None:
        ...     print("Cache hit!")
        >>> 
        >>> # Get cache statistics
        >>> stats = cache.get_statistics()
        >>> print(f"Hit rate: {stats['hit_rate']:.2%}")
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: int = 300,
        enable_metrics: bool = True
    ):
        """
        Initialize the query cache.
        
        Args:
            max_size: Maximum number of entries in the cache
            default_ttl_seconds: Default TTL for cache entries (seconds)
            enable_metrics: Whether to track and report metrics
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._max_size = max_size
        self._default_ttl = default_ttl_seconds
        self._enable_metrics = enable_metrics
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0
        
        logger.info(
            f"QueryCache initialized: max_size={max_size}, "
            f"default_ttl={default_ttl_seconds}s"
        )
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data if found and not expired, None otherwise
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                self._track_metric("cache_miss")
                logger.debug(f"Cache miss: {key}")
                return None
            
            if entry.is_expired():
                # Remove expired entry
                del self._cache[key]
                self._expirations += 1
                self._misses += 1
                self._track_metric("cache_expiration")
                logger.debug(f"Cache expiration: {key}")
                return None
            
            # Move to end (mark as recently used)
            self._cache.move_to_end(key)
            entry.increment_hits()
            self._hits += 1
            self._track_metric("cache_hit")
            
            logger.debug(
                f"Cache hit: {key} (age={entry.get_age_seconds():.1f}s, "
                f"hits={entry.hits})"
            )
            
            return entry.data
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: Cache key
            value: Data to cache
            ttl_seconds: Time-to-live in seconds (uses default if None)
        """
        if ttl_seconds is None:
            ttl_seconds = self._default_ttl
        
        with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]
            
            # Create new entry
            entry = CacheEntry(value, ttl_seconds, key)
            self._cache[key] = entry
            
            # Move to end (mark as recently used)
            self._cache.move_to_end(key)
            
            # Evict oldest entry if cache is at or over capacity
            while len(self._cache) > self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._evictions += 1
                self._track_metric("cache_eviction")
                logger.debug(f"Cache eviction: {oldest_key}")
            
            logger.debug(f"Cache set: {key} (ttl={ttl_seconds}s)")
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if entry was found and removed, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache invalidated: {key}")
                return True
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.
        
        Args:
            pattern: String pattern to match against keys
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if pattern in key
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
            
            if keys_to_remove:
                logger.info(
                    f"Invalidated {len(keys_to_remove)} entries matching "
                    f"pattern: {pattern}"
                )
            
            return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            entry_count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {entry_count} entries removed")
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
                self._expirations += 1
            
            if keys_to_remove:
                logger.debug(f"Cleaned up {len(keys_to_remove)} expired entries")
            
            return len(keys_to_remove)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "expirations": self._expirations,
                "total_requests": total_requests
            }
    
    def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            Dictionary with entry information or None if not found
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            return {
                "key": key,
                "age_seconds": entry.get_age_seconds(),
                "ttl_seconds": entry.ttl_seconds,
                "hits": entry.hits,
                "is_expired": entry.is_expired(),
                "timestamp": entry.timestamp.isoformat()
            }
    
    def _track_metric(self, metric_name: str) -> None:
        """Track a cache metric if metrics are enabled."""
        if self._enable_metrics and metrics:
            try:
                metrics.increment_counter(
                    f"query_cache_{metric_name}",
                    labels={"cache": "query_cache"}
                )
            except Exception as e:
                logger.warning(f"Failed to track metric {metric_name}: {e}")


def generate_cache_key(
    query_type: str,
    parameters: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    Generate a cache key from query type and parameters.
    
    Creates a deterministic hash-based key from the query type and parameters
    to uniquely identify query results.
    
    Args:
        query_type: Type of query (e.g., "find_by_id", "find_dependencies")
        parameters: Query parameters dictionary
        **kwargs: Additional parameters to include in the key
        
    Returns:
        Cache key string
    """
    # Combine all parameters
    all_params = {}
    if parameters:
        all_params.update(parameters)
    if kwargs:
        all_params.update(kwargs)
    
    # Create deterministic string representation
    param_str = json.dumps(all_params, sort_keys=True, default=str)
    
    # Generate hash
    key_string = f"{query_type}:{param_str}"
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    return f"{query_type}:{key_hash}"


def cached_query(
    ttl_seconds: int = 300,
    cache_instance: Optional[QueryCache] = None
):
    """
    Decorator to cache query method results.
    
    This decorator automatically caches the results of query methods,
    generating cache keys from the method name and parameters.
    
    Args:
        ttl_seconds: Time-to-live for cached results (default: 300)
        cache_instance: Specific cache instance to use (uses singleton if None)
        
    Returns:
        Decorated function with caching
        
    Example:
        >>> @cached_query(ttl_seconds=600)
        ... def find_resource(self, resource_id: str):
        ...     # Query implementation
        ...     return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache instance
            cache = cache_instance or get_query_cache()
            
            # Generate cache key
            # args[0] is 'self' for instance methods
            method_name = func.__name__
            cache_key = generate_cache_key(
                query_type=method_name,
                parameters=kwargs,
                args=args[1:] if len(args) > 1 else ()
            )
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Returning cached result for {method_name}")
                return cached_result
            
            # Execute query
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, ttl_seconds=ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


# Module-level singleton
_cache_instance: Optional[QueryCache] = None


def get_query_cache(
    max_size: int = 1000,
    default_ttl_seconds: int = 300,
    enable_metrics: bool = True
) -> QueryCache:
    """
    Get or create the singleton QueryCache instance.
    
    Args:
        max_size: Maximum number of entries in the cache
        default_ttl_seconds: Default TTL for cache entries
        enable_metrics: Whether to track and report metrics
        
    Returns:
        QueryCache singleton instance
    """
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = QueryCache(
            max_size=max_size,
            default_ttl_seconds=default_ttl_seconds,
            enable_metrics=enable_metrics
        )
    
    return _cache_instance


def reset_cache() -> None:
    """
    Reset the singleton cache instance.
    
    This is primarily useful for testing purposes.
    """
    global _cache_instance
    
    if _cache_instance is not None:
        _cache_instance.clear()
        _cache_instance = None
        logger.info("Query cache reset")

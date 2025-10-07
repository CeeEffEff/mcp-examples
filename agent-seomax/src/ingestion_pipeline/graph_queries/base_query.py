"""
Base Query Classes for Neo4j Graph Queries

Provides foundational classes and utilities for all graph query operations.
Includes error handling, monitoring integration, and common query patterns.
"""

import logging
from typing import Dict, Any, List, Optional, TypeVar, Generic
from abc import ABC, abstractmethod
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

from ..neo4j_ops import get_connection_manager, Neo4jConnectionError
from ..monitoring import get_logger, get_metrics


logger = logging.getLogger(__name__)


class QueryError(Exception):
    """Base exception for graph query errors."""
    pass


class QueryValidationError(QueryError):
    """Raised when query parameters are invalid."""
    pass


class QueryExecutionError(QueryError):
    """Raised when query execution fails."""
    pass


class QueryResultError(QueryError):
    """Raised when query result processing fails."""
    pass


T = TypeVar('T')


class QueryResult(Generic[T]):
    """
    Container for query results with metadata.
    
    Attributes:
        data: Query result data
        execution_time: Query execution time in seconds
        record_count: Number of records returned
        query: The executed query string (for debugging)
        parameters: Query parameters (for debugging)
    """
    
    def __init__(
        self,
        data: T,
        execution_time: float,
        record_count: int,
        query: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.data = data
        self.execution_time = execution_time
        self.record_count = record_count
        self.query = query
        self.parameters = parameters
        self.timestamp = datetime.utcnow()
    
    def __repr__(self) -> str:
        return (
            f"QueryResult(record_count={self.record_count}, "
            f"execution_time={self.execution_time:.3f}s)"
        )


class BaseQuery(ABC):
    """
    Base class for all graph query operations.
    
    Provides:
    - Connection management
    - Error handling
    - Monitoring integration
    - Query execution utilities
    - Result processing
    
    Subclasses should implement specific query methods.
    """
    
    def __init__(
        self,
        connection_manager=None,
        enable_monitoring: bool = True,
        query_timeout: int = 30,
    ):
        """
        Initialize base query handler.
        
        Args:
            connection_manager: Optional Neo4j connection manager instance
            enable_monitoring: Whether to track metrics and logs
            query_timeout: Query timeout in seconds
        """
        self._connection = connection_manager or get_connection_manager()
        self._enable_monitoring = enable_monitoring
        self._query_timeout = query_timeout
        
        # Monitoring
        if enable_monitoring:
            self._logger = get_logger(self.__class__.__name__)
            self._metrics = get_metrics()
        else:
            self._logger = logger
            self._metrics = None
    
    @contextmanager
    def _get_session(self, **kwargs):
        """
        Context manager for Neo4j sessions with error handling.
        
        Yields:
            Neo4j session object
        """
        try:
            with self._connection.get_session(**kwargs) as session:
                yield session
        except Neo4jConnectionError as e:
            self._log_error(f"Connection error: {e}")
            raise QueryExecutionError(f"Failed to establish Neo4j session: {e}") from e
        except Exception as e:
            self._log_error(f"Unexpected session error: {e}")
            raise QueryExecutionError(f"Session error: {e}") from e
    
    def _execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        query_type: str = "generic",
    ) -> QueryResult[List[Dict[str, Any]]]:
        """
        Execute a Cypher query with monitoring and error handling.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            query_type: Type of query for metrics (e.g., "resource_lookup")
            
        Returns:
            QueryResult containing records and metadata
            
        Raises:
            QueryExecutionError: If query execution fails
        """
        start_time = datetime.utcnow()
        params = parameters or {}
        
        try:
            # Log query execution
            self._log_debug(f"Executing {query_type} query", extra={
                "query_type": query_type,
                "parameters": params,
            })
            
            # Execute query
            with self._get_session() as session:
                result = session.run(query, params)
                records = [dict(record) for record in result]
                record_count = len(records)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Track metrics
            if self._metrics:
                self._metrics.increment_counter(
                    "queries_executed",
                    labels={"type": query_type}
                )
                self._metrics.record_histogram(
                    "query_duration_seconds",
                    execution_time,
                    labels={"type": query_type}
                )
                self._metrics.record_histogram(
                    "query_record_count",
                    record_count,
                    labels={"type": query_type}
                )
            
            # Log completion
            self._log_info(
                f"{query_type} query completed: {record_count} records in {execution_time:.3f}s"
            )
            
            return QueryResult(
                data=records,
                execution_time=execution_time,
                record_count=record_count,
                query=query,
                parameters=params,
            )
            
        except Neo4jConnectionError as e:
            self._log_error(f"Connection error during {query_type} query: {e}")
            if self._metrics:
                self._metrics.increment_counter(
                    "query_errors",
                    labels={"type": query_type, "error": "connection"}
                )
            raise QueryExecutionError(f"Connection failed: {e}") from e
            
        except Exception as e:
            self._log_error(f"Query execution error: {e}", extra={
                "query": query,
                "parameters": params,
            })
            if self._metrics:
                self._metrics.increment_counter(
                    "query_errors",
                    labels={"type": query_type, "error": "execution"}
                )
            raise QueryExecutionError(f"Query failed: {e}") from e
    
    def _execute_single_result_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        query_type: str = "generic",
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a query expecting a single result.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            query_type: Type of query for metrics
            
        Returns:
            Single record dict or None if no results
        """
        result = self._execute_query(query, parameters, query_type)
        
        if result.record_count == 0:
            return None
        elif result.record_count == 1:
            return result.data[0]
        else:
            self._log_warning(
                f"Expected single result, got {result.record_count} records. "
                "Returning first record."
            )
            return result.data[0]
    
    def _validate_required_params(
        self,
        params: Dict[str, Any],
        required: List[str],
    ) -> None:
        """
        Validate that required parameters are present.
        
        Args:
            params: Parameter dictionary
            required: List of required parameter names
            
        Raises:
            QueryValidationError: If required parameters are missing
        """
        missing = [key for key in required if key not in params or params[key] is None]
        
        if missing:
            raise QueryValidationError(
                f"Missing required parameters: {', '.join(missing)}"
            )
    
    def _validate_param_type(
        self,
        param_name: str,
        param_value: Any,
        expected_type: type,
    ) -> None:
        """
        Validate parameter type.
        
        Args:
            param_name: Parameter name
            param_value: Parameter value
            expected_type: Expected type
            
        Raises:
            QueryValidationError: If type doesn't match
        """
        if not isinstance(param_value, expected_type):
            raise QueryValidationError(
                f"Parameter '{param_name}' must be {expected_type.__name__}, "
                f"got {type(param_value).__name__}"
            )
    
    def _validate_positive_int(self, param_name: str, value: int) -> None:
        """
        Validate that a parameter is a positive integer.
        
        Args:
            param_name: Parameter name
            value: Value to validate
            
        Raises:
            QueryValidationError: If not a positive integer
        """
        if not isinstance(value, int) or value <= 0:
            raise QueryValidationError(
                f"Parameter '{param_name}' must be a positive integer, got {value}"
            )
    
    def _sanitize_label(self, label: str) -> str:
        """
        Sanitize a node label for use in queries.
        
        Args:
            label: Label to sanitize
            
        Returns:
            Sanitized label
        """
        # Remove non-alphanumeric characters except underscore
        sanitized = "".join(c for c in label if c.isalnum() or c == "_")
        
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = "Label_" + sanitized
        
        return sanitized or "Node"
    
    def _log_debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message with context."""
        if self._enable_monitoring:
            self._logger.debug(message, extra=extra or {})
    
    def _log_info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message with context."""
        if self._enable_monitoring:
            self._logger.info(message, extra=extra or {})
    
    def _log_warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message with context."""
        if self._enable_monitoring:
            self._logger.warning(message, extra=extra or {})
    
    def _log_error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log error message with context."""
        if self._enable_monitoring:
            self._logger.error(message, extra=extra or {})


def track_query_performance(query_type: str):
    """
    Decorator to track query performance metrics.
    
    Args:
        query_type: Type of query for metrics labeling
        
    Example:
        @track_query_performance("resource_search")
        def find_resources(self, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, '_metrics') or not self._metrics:
                return func(self, *args, **kwargs)
            
            with self._metrics.track_processing(query_type):
                return func(self, *args, **kwargs)
        
        return wrapper
    return decorator

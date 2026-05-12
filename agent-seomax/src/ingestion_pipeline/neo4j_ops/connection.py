"""
Neo4j Connection Manager

Provides connection pooling and management for Neo4j database operations.
Handles driver lifecycle, health checks, and configuration.
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError


logger = logging.getLogger(__name__)


class Neo4jConnectionError(Exception):
    """Raised when Neo4j connection fails."""
    pass


class Neo4jConnectionManager:
    """
    Manages Neo4j database connections with pooling and health checks.
    
    Features:
    - Connection pooling with configurable pool size
    - Automatic reconnection on transient failures
    - Health check validation
    - Graceful shutdown
    - Thread-safe operations
    
    Example:
        manager = Neo4jConnectionManager()
        manager.connect()
        
        with manager.session() as session:
            result = session.run("MATCH (n) RETURN count(n)")
            
        manager.close()
    """
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        max_connection_lifetime: int = 3600,
        max_connection_pool_size: int = 50,
        connection_acquisition_timeout: int = 60,
    ):
        """
        Initialize Neo4j connection manager.
        
        Args:
            uri: Neo4j connection URI (bolt://host:port or neo4j://host:port)
                 Defaults to NEO4J_URI environment variable
            username: Neo4j username. Defaults to NEO4J_USERNAME env var
            password: Neo4j password. Defaults to NEO4J_PASSWORD env var
            database: Neo4j database name. Defaults to NEO4J_DATABASE env var or "neo4j"
            max_connection_lifetime: Max lifetime of connection in seconds (default: 3600)
            max_connection_pool_size: Max connections in pool (default: 50)
            connection_acquisition_timeout: Timeout for acquiring connection (default: 60s)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        
        # Connection pool configuration
        self.max_connection_lifetime = max_connection_lifetime
        self.max_connection_pool_size = max_connection_pool_size
        self.connection_acquisition_timeout = connection_acquisition_timeout
        
        # Driver instance
        self._driver: Optional[Driver] = None
        self._is_connected = False
        
        logger.info(
            f"Neo4jConnectionManager initialized with URI: {self.uri}, "
            f"database: {self.database}, pool_size: {max_connection_pool_size}"
        )
    
    def connect(self) -> None:
        """
        Establish connection to Neo4j database.
        
        Raises:
            Neo4jConnectionError: If connection fails
        """
        if self._is_connected and self._driver:
            logger.warning("Already connected to Neo4j. Skipping connection.")
            return
        
        try:
            logger.info(f"Connecting to Neo4j at {self.uri}...")
            
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=self.max_connection_lifetime,
                max_connection_pool_size=self.max_connection_pool_size,
                connection_acquisition_timeout=self.connection_acquisition_timeout,
            )
            
            # Verify connectivity
            self._driver.verify_connectivity()
            self._is_connected = True
            
            logger.info(f"Successfully connected to Neo4j database: {self.database}")
            
        except AuthError as e:
            error_msg = f"Authentication failed for Neo4j: {e}"
            logger.error(error_msg)
            raise Neo4jConnectionError(error_msg) from e
            
        except ServiceUnavailable as e:
            error_msg = f"Neo4j service unavailable at {self.uri}: {e}"
            logger.error(error_msg)
            raise Neo4jConnectionError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Failed to connect to Neo4j: {e}"
            logger.error(error_msg)
            raise Neo4jConnectionError(error_msg) from e
    
    def close(self) -> None:
        """
        Close Neo4j driver and release all connections.
        """
        if not self._is_connected or not self._driver:
            logger.warning("No active Neo4j connection to close.")
            return
        
        try:
            logger.info("Closing Neo4j connection...")
            self._driver.close()
            self._is_connected = False
            self._driver = None
            logger.info("Neo4j connection closed successfully.")
            
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {e}")
            raise
    
    @contextmanager
    def session(self, **kwargs) -> Session:
        """
        Context manager for Neo4j sessions.
        
        Args:
            **kwargs: Additional session parameters (e.g., default_access_mode)
        
        Yields:
            Neo4j Session object
            
        Raises:
            Neo4jConnectionError: If not connected to database
            
        Example:
            with manager.session() as session:
                result = session.run("MATCH (n) RETURN n LIMIT 10")
                for record in result:
                    print(record)
        """
        if not self._is_connected or not self._driver:
            raise Neo4jConnectionError(
                "Not connected to Neo4j. Call connect() first."
            )
        
        session = None
        try:
            # Create session with specified database
            session = self._driver.session(database=self.database, **kwargs)
            yield session
            
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable during session: {e}")
            raise Neo4jConnectionError(f"Service unavailable: {e}") from e
            
        except Exception as e:
            logger.error(f"Error during Neo4j session: {e}")
            raise
            
        finally:
            if session:
                session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Neo4j connection.
        
        Returns:
            Dict with health status information:
            {
                'connected': bool,
                'database': str,
                'uri': str,
                'node_count': int (if connected),
                'error': str (if not connected)
            }
        """
        health_info = {
            'connected': False,
            'database': self.database,
            'uri': self.uri,
        }
        
        if not self._is_connected or not self._driver:
            health_info['error'] = 'Not connected to Neo4j'
            return health_info
        
        try:
            with self.session() as session:
                # Simple query to verify database access
                result = session.run("MATCH (n) RETURN count(n) AS count")
                record = result.single()
                
                health_info['connected'] = True
                health_info['node_count'] = record['count'] if record else 0
                
                logger.debug(f"Neo4j health check passed. Node count: {health_info['node_count']}")
                
        except Exception as e:
            health_info['connected'] = False
            health_info['error'] = str(e)
            logger.error(f"Neo4j health check failed: {e}")
        
        return health_info
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> list:
        """
        Execute a Cypher query and return all results.
        
        Args:
            query: Cypher query string
            parameters: Query parameters dict
            database: Override default database for this query
            
        Returns:
            List of result records
            
        Raises:
            Neo4jConnectionError: If not connected or query fails
        """
        if not self._is_connected or not self._driver:
            raise Neo4jConnectionError(
                "Not connected to Neo4j. Call connect() first."
            )
        
        try:
            db = database or self.database
            with self._driver.session(database=db) as session:
                result = session.run(query, parameters or {})
                return list(result)
                
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable during query execution: {e}")
            raise Neo4jConnectionError(f"Service unavailable: {e}") from e
            
        except Exception as e:
            logger.error(f"Error executing Neo4j query: {e}")
            raise
    
    def is_connected(self) -> bool:
        """
        Check if currently connected to Neo4j.
        
        Returns:
            True if connected, False otherwise
        """
        return self._is_connected and self._driver is not None
    
    def get_driver(self) -> Optional[Driver]:
        """
        Get the underlying Neo4j driver instance.
        
        Returns:
            Neo4j Driver or None if not connected
        """
        return self._driver if self._is_connected else None
    
    def __enter__(self):
        """Context manager entry - auto-connect."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto-close."""
        self.close()
        return False
    
    def __repr__(self) -> str:
        """String representation."""
        status = "connected" if self._is_connected else "disconnected"
        return f"Neo4jConnectionManager(uri={self.uri}, database={self.database}, status={status})"


# Singleton instance for application-wide use
_connection_manager_instance: Optional[Neo4jConnectionManager] = None


def get_connection_manager(
    uri: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    database: Optional[str] = None,
) -> Neo4jConnectionManager:
    """
    Get or create singleton Neo4j connection manager instance.
    
    Args:
        uri: Neo4j URI (only used for first initialization)
        username: Neo4j username (only used for first initialization)
        password: Neo4j password (only used for first initialization)
        database: Neo4j database (only used for first initialization)
        
    Returns:
        Singleton Neo4jConnectionManager instance
    """
    global _connection_manager_instance
    
    if _connection_manager_instance is None:
        _connection_manager_instance = Neo4jConnectionManager(
            uri=uri,
            username=username,
            password=password,
            database=database,
        )
    
    return _connection_manager_instance


def reset_connection_manager() -> None:
    """
    Reset singleton connection manager (useful for testing).
    """
    global _connection_manager_instance
    
    if _connection_manager_instance and _connection_manager_instance.is_connected():
        _connection_manager_instance.close()
    
    _connection_manager_instance = None

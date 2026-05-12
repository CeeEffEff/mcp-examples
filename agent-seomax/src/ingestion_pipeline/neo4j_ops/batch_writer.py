"""
Neo4j Batch Writer

Handles batch write operations to Neo4j with transaction management,
retry logic, and metrics tracking.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from neo4j.exceptions import (
    ServiceUnavailable,
    TransientError,
    ConstraintError,
    ClientError,
)

from .connection import Neo4jConnectionManager, Neo4jConnectionError
from .query_builder import CypherQueryBuilder, QueryBuilderError


logger = logging.getLogger(__name__)


@dataclass
class BatchWriteMetrics:
    """Metrics for batch write operations."""
    
    total_nodes: int = 0
    total_relationships: int = 0
    successful_nodes: int = 0
    successful_relationships: int = 0
    failed_nodes: int = 0
    failed_relationships: int = 0
    total_batches: int = 0
    failed_batches: int = 0
    total_duration_ms: float = 0.0
    avg_batch_duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate derived metrics."""
        if self.total_batches > 0:
            self.avg_batch_duration_ms = self.total_duration_ms / self.total_batches
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_nodes": self.total_nodes,
            "total_relationships": self.total_relationships,
            "successful_nodes": self.successful_nodes,
            "successful_relationships": self.successful_relationships,
            "failed_nodes": self.failed_nodes,
            "failed_relationships": self.failed_relationships,
            "total_batches": self.total_batches,
            "failed_batches": self.failed_batches,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "avg_batch_duration_ms": round(self.avg_batch_duration_ms, 2),
            "error_count": len(self.errors),
            "errors": self.errors[-10:]  # Last 10 errors
        }


class BatchWriterError(Exception):
    """Raised when batch write operation fails."""
    pass


class Neo4jBatchWriter:
    """
    Handles batch write operations to Neo4j with transactions.
    
    Features:
    - Configurable batch sizes for optimal performance
    - Transaction management with auto-commit
    - Atomic batch operations (all-or-nothing)
    - Comprehensive metrics tracking
    - Error handling with detailed logging
    
    Example:
        writer = Neo4jBatchWriter(connection_manager, batch_size=100)
        
        # Write nodes
        results = writer.write_nodes(
            label="VirtualMachine",
            unique_key="id",
            nodes=[{...}, {...}]
        )
        
        # Write relationships
        results = writer.write_relationships(relationships_list)
    """
    
    def __init__(
        self,
        connection_manager: Neo4jConnectionManager,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize batch writer.
        
        Args:
            connection_manager: Neo4j connection manager instance
            batch_size: Number of items per batch (default: 100)
            max_retries: Maximum retry attempts for transient failures (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
        """
        self.connection_manager = connection_manager
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.query_builder = CypherQueryBuilder()
        self.metrics = BatchWriteMetrics()
        
        logger.info(
            f"Neo4jBatchWriter initialized with batch_size={batch_size}, "
            f"max_retries={max_retries}"
        )
    
    def write_nodes(
        self,
        label: str,
        unique_key: str,
        nodes: List[Dict[str, Any]],
    ) -> BatchWriteMetrics:
        """
        Write multiple nodes to Neo4j in batches.
        
        Args:
            label: Node label
            unique_key: Property name for uniqueness constraint
            nodes: List of node property dictionaries
            
        Returns:
            BatchWriteMetrics with operation statistics
            
        Raises:
            BatchWriterError: If batch write fails after retries
        """
        if not nodes:
            logger.warning("No nodes provided for batch write")
            return BatchWriteMetrics()
        
        start_time = time.time()
        metrics = BatchWriteMetrics(total_nodes=len(nodes))
        
        logger.info(f"Starting batch write of {len(nodes)} {label} nodes")
        
        # Split into batches
        batches = self._create_batches(nodes, self.batch_size)
        metrics.total_batches = len(batches)
        
        for batch_idx, batch in enumerate(batches, 1):
            batch_start = time.time()
            
            try:
                # Build batch query
                query, params = self.query_builder.build_batch_node_merge(
                    label=label,
                    unique_key=unique_key,
                    nodes=batch,
                )
                
                # Execute with retry logic
                self._execute_with_retry(query, params)
                
                # Update metrics
                metrics.successful_nodes += len(batch)
                batch_duration = (time.time() - batch_start) * 1000
                metrics.total_duration_ms += batch_duration
                
                logger.debug(
                    f"Batch {batch_idx}/{len(batches)}: "
                    f"Wrote {len(batch)} {label} nodes in {batch_duration:.2f}ms"
                )
                
            except ConstraintError as e:
                # Constraint violation - log and continue
                error_msg = f"Constraint violation in batch {batch_idx}: {e}"
                logger.error(error_msg)
                metrics.failed_nodes += len(batch)
                metrics.failed_batches += 1
                metrics.errors.append(error_msg)
                
            except Exception as e:
                # Unexpected error
                error_msg = f"Error writing batch {batch_idx}: {e}"
                logger.error(error_msg, exc_info=True)
                metrics.failed_nodes += len(batch)
                metrics.failed_batches += 1
                metrics.errors.append(error_msg)
        
        total_duration = (time.time() - start_time) * 1000
        metrics.total_duration_ms = total_duration
        
        logger.info(
            f"Completed batch write: {metrics.successful_nodes}/{len(nodes)} nodes "
            f"written in {total_duration:.2f}ms "
            f"({metrics.failed_batches} failed batches)"
        )
        
        return metrics
    
    def write_relationships(
        self,
        relationships: List[Dict[str, Any]],
    ) -> BatchWriteMetrics:
        """
        Write multiple relationships to Neo4j in batches.
        
        Args:
            relationships: List of relationship dicts with keys:
                - source_label: str
                - source_key: str
                - source_id: Any
                - target_label: str
                - target_key: str
                - target_id: Any
                - relationship_type: str
                - properties: Optional[Dict]
                
        Returns:
            BatchWriteMetrics with operation statistics
        """
        if not relationships:
            logger.warning("No relationships provided for batch write")
            return BatchWriteMetrics()
        
        start_time = time.time()
        metrics = BatchWriteMetrics(total_relationships=len(relationships))
        
        logger.info(f"Starting batch write of {len(relationships)} relationships")
        
        # Split into batches
        batches = self._create_batches(relationships, self.batch_size)
        metrics.total_batches = len(batches)
        
        for batch_idx, batch in enumerate(batches, 1):
            batch_start = time.time()
            
            try:
                # Write relationships individually (more reliable than batch)
                # because dynamic relationship types are tricky in Cypher
                successful = 0
                for rel in batch:
                    try:
                        query, params = self.query_builder.build_relationship_merge(
                            source_label=rel["source_label"],
                            source_key=rel["source_key"],
                            source_id=rel["source_id"],
                            target_label=rel["target_label"],
                            target_key=rel["target_key"],
                            target_id=rel["target_id"],
                            relationship_type=rel["relationship_type"],
                            properties=rel.get("properties"),
                        )
                        
                        self._execute_with_retry(query, params)
                        successful += 1
                        
                    except Exception as e:
                        error_msg = (
                            f"Failed to write relationship "
                            f"{rel['source_label']}({rel['source_id']})-"
                            f"[{rel['relationship_type']}]->"
                            f"{rel['target_label']}({rel['target_id']}): {e}"
                        )
                        logger.warning(error_msg)
                        metrics.errors.append(error_msg)
                
                # Update metrics
                metrics.successful_relationships += successful
                metrics.failed_relationships += len(batch) - successful
                
                batch_duration = (time.time() - batch_start) * 1000
                metrics.total_duration_ms += batch_duration
                
                logger.debug(
                    f"Batch {batch_idx}/{len(batches)}: "
                    f"Wrote {successful}/{len(batch)} relationships in {batch_duration:.2f}ms"
                )
                
            except Exception as e:
                error_msg = f"Error writing relationship batch {batch_idx}: {e}"
                logger.error(error_msg, exc_info=True)
                metrics.failed_relationships += len(batch)
                metrics.failed_batches += 1
                metrics.errors.append(error_msg)
        
        total_duration = (time.time() - start_time) * 1000
        metrics.total_duration_ms = total_duration
        
        logger.info(
            f"Completed relationship batch write: "
            f"{metrics.successful_relationships}/{len(relationships)} written "
            f"in {total_duration:.2f}ms "
            f"({metrics.failed_batches} failed batches)"
        )
        
        return metrics
    
    def write_transformation_results(
        self,
        results: List[Dict[str, Any]],
    ) -> BatchWriteMetrics:
        """
        Write transformation results (nodes + relationships) to Neo4j.
        
        Args:
            results: List of transformation results with structure:
                {
                    "node": Dict[str, Any],
                    "node_label": str,
                    "relationships": List[Dict[str, Any]],
                    "resource_id": str,
                    "resource_type": str
                }
                
        Returns:
            Combined BatchWriteMetrics for both nodes and relationships
        """
        if not results:
            logger.warning("No transformation results provided")
            return BatchWriteMetrics()
        
        logger.info(f"Writing {len(results)} transformation results to Neo4j")
        
        # Extract nodes and relationships
        nodes_by_label: Dict[str, List[Dict[str, Any]]] = {}
        all_relationships: List[Dict[str, Any]] = []
        
        for result in results:
            # Group nodes by label
            label = result.get("node_label")
            node = result.get("node")
            
            if label and node:
                if label not in nodes_by_label:
                    nodes_by_label[label] = []
                nodes_by_label[label].append(node)
            
            # Collect relationships
            relationships = result.get("relationships", [])
            all_relationships.extend(relationships)
        
        # Write nodes by label
        combined_metrics = BatchWriteMetrics()
        
        for label, nodes in nodes_by_label.items():
            # Assume 'id' is the unique key (standard in our schema)
            unique_key = "id"
            
            node_metrics = self.write_nodes(
                label=label,
                unique_key=unique_key,
                nodes=nodes,
            )
            
            # Combine metrics
            combined_metrics.total_nodes += node_metrics.total_nodes
            combined_metrics.successful_nodes += node_metrics.successful_nodes
            combined_metrics.failed_nodes += node_metrics.failed_nodes
            combined_metrics.total_batches += node_metrics.total_batches
            combined_metrics.failed_batches += node_metrics.failed_batches
            combined_metrics.total_duration_ms += node_metrics.total_duration_ms
            combined_metrics.errors.extend(node_metrics.errors)
        
        # Write relationships
        if all_relationships:
            rel_metrics = self.write_relationships(all_relationships)
            
            combined_metrics.total_relationships += rel_metrics.total_relationships
            combined_metrics.successful_relationships += rel_metrics.successful_relationships
            combined_metrics.failed_relationships += rel_metrics.failed_relationships
            combined_metrics.total_batches += rel_metrics.total_batches
            combined_metrics.failed_batches += rel_metrics.failed_batches
            combined_metrics.total_duration_ms += rel_metrics.total_duration_ms
            combined_metrics.errors.extend(rel_metrics.errors)
        
        logger.info(
            f"Completed transformation results write: "
            f"{combined_metrics.successful_nodes} nodes, "
            f"{combined_metrics.successful_relationships} relationships "
            f"in {combined_metrics.total_duration_ms:.2f}ms"
        )
        
        return combined_metrics
    
    def delete_nodes(
        self,
        label: str,
        unique_key: str,
        node_ids: List[Any],
        soft_delete: bool = True,
    ) -> BatchWriteMetrics:
        """
        Delete multiple nodes from Neo4j.
        
        Args:
            label: Node label
            unique_key: Unique property name
            node_ids: List of node ID values to delete
            soft_delete: If True, set deletedAt property instead of hard delete
            
        Returns:
            BatchWriteMetrics with deletion statistics
        """
        if not node_ids:
            logger.warning("No node IDs provided for deletion")
            return BatchWriteMetrics()
        
        start_time = time.time()
        metrics = BatchWriteMetrics(total_nodes=len(node_ids))
        
        logger.info(
            f"Starting {'soft' if soft_delete else 'hard'} delete of "
            f"{len(node_ids)} {label} nodes"
        )
        
        for node_id in node_ids:
            try:
                if soft_delete:
                    query, params = self.query_builder.build_soft_delete_node(
                        label=label,
                        unique_key=unique_key,
                        unique_value=node_id,
                    )
                else:
                    query, params = self.query_builder.build_delete_node(
                        label=label,
                        unique_key=unique_key,
                        unique_value=node_id,
                        detach=True,
                    )
                
                self._execute_with_retry(query, params)
                metrics.successful_nodes += 1
                
            except Exception as e:
                error_msg = f"Failed to delete {label} node {node_id}: {e}"
                logger.error(error_msg)
                metrics.failed_nodes += 1
                metrics.errors.append(error_msg)
        
        metrics.total_duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Completed node deletion: {metrics.successful_nodes}/{len(node_ids)} "
            f"deleted in {metrics.total_duration_ms:.2f}ms"
        )
        
        return metrics
    
    def _execute_with_retry(
        self,
        query: str,
        parameters: Dict[str, Any],
    ) -> list:
        """
        Execute Cypher query with retry logic for transient failures.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            Query result records
            
        Raises:
            BatchWriterError: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                with self.connection_manager.session() as session:
                    result = session.run(query, parameters)
                    return list(result)
                    
            except TransientError as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Transient error on attempt {attempt + 1}/{self.max_retries + 1}: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Max retries exceeded for transient error: {e}")
                    
            except ServiceUnavailable as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Service unavailable on attempt {attempt + 1}/{self.max_retries + 1}: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Max retries exceeded for service unavailable: {e}")
                    
            except (ConstraintError, ClientError) as e:
                # Non-retryable errors - fail immediately
                logger.error(f"Non-retryable error: {e}")
                raise BatchWriterError(f"Query execution failed: {e}") from e
        
        # If we get here, all retries failed
        raise BatchWriterError(
            f"Query execution failed after {self.max_retries} retries: {last_exception}"
        ) from last_exception
    
    def _create_batches(
        self,
        items: List[Any],
        batch_size: int,
    ) -> List[List[Any]]:
        """
        Split items into batches of specified size.
        
        Args:
            items: List of items to batch
            batch_size: Size of each batch
            
        Returns:
            List of batches
        """
        batches = []
        for i in range(0, len(items), batch_size):
            batches.append(items[i:i + batch_size])
        return batches
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current batch writer metrics.
        
        Returns:
            Dictionary of metrics
        """
        return self.metrics.to_dict()
    
    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self.metrics = BatchWriteMetrics()
        logger.debug("Batch writer metrics reset")

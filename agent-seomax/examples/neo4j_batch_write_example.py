#!/usr/bin/env python3
"""
Neo4j Batch Write Integration Example

Demonstrates how to use the neo4j_ops module to write transformed
GCP resource data to Neo4j database.

Usage:
    python examples/neo4j_batch_write_example.py
"""

import os
import sys
import logging
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion_pipeline.neo4j_ops import (
    Neo4jConnectionManager,
    Neo4jBatchWriter,
    get_connection_manager,
)
from src.ingestion_pipeline.transformation import (
    TransformerFactory,
    TransformationResult,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_gcp_resources() -> List[Dict[str, Any]]:
    """Create sample GCP resource data for demonstration."""
    return [
        {
            "id": "projects/my-project/zones/us-central1-a/instances/vm-1",
            "name": "web-server-1",
            "machineType": "projects/my-project/zones/us-central1-a/machineTypes/n1-standard-1",
            "status": "RUNNING",
            "zone": "us-central1-a",
            "networkInterfaces": [
                {
                    "network": "projects/my-project/global/networks/default",
                    "subnetwork": "projects/my-project/regions/us-central1/subnetworks/default",
                }
            ],
            "disks": [
                {
                    "source": "projects/my-project/zones/us-central1-a/disks/boot-disk-1",
                    "boot": True,
                }
            ],
            "creationTimestamp": "2025-01-01T00:00:00.000-00:00",
        },
        {
            "id": "projects/my-project/zones/us-central1-a/instances/vm-2",
            "name": "app-server-1",
            "machineType": "projects/my-project/zones/us-central1-a/machineTypes/n1-standard-2",
            "status": "RUNNING",
            "zone": "us-central1-a",
            "networkInterfaces": [
                {
                    "network": "projects/my-project/global/networks/default",
                    "subnetwork": "projects/my-project/regions/us-central1/subnetworks/default",
                }
            ],
            "disks": [
                {
                    "source": "projects/my-project/zones/us-central1-a/disks/boot-disk-2",
                    "boot": True,
                }
            ],
            "creationTimestamp": "2025-01-02T00:00:00.000-00:00",
        },
    ]


def transform_resources(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform GCP resources using the transformation layer.
    
    Args:
        resources: List of raw GCP resource dictionaries
        
    Returns:
        List of transformation results ready for Neo4j
    """
    logger.info(f"Transforming {len(resources)} resources...")
    
    # Get transformer for compute instances
    transformer = TransformerFactory.get_transformer('compute.instances')
    
    transformation_results = []
    for resource in resources:
        try:
            # Transform resource
            result = transformer.transform(resource)
            
            # Convert to dict format expected by batch writer
            transformation_results.append({
                "node": result.node,
                "node_label": result.node_label,
                "relationships": result.relationships,
                "resource_id": result.resource_id,
                "resource_type": result.resource_type,
            })
            
            logger.debug(f"Transformed resource: {result.resource_id}")
            
        except Exception as e:
            logger.error(f"Failed to transform resource: {e}")
    
    logger.info(f"Successfully transformed {len(transformation_results)} resources")
    return transformation_results


def write_to_neo4j(transformation_results: List[Dict[str, Any]]) -> None:
    """
    Write transformation results to Neo4j database.
    
    Args:
        transformation_results: List of transformed resources
    """
    logger.info("Connecting to Neo4j...")
    
    # Get connection manager (uses environment variables)
    manager = get_connection_manager()
    
    try:
        # Connect to Neo4j
        manager.connect()
        
        # Perform health check
        health = manager.health_check()
        logger.info(f"Neo4j health check: {health}")
        
        if not health['connected']:
            logger.error(f"Neo4j not available: {health.get('error')}")
            return
        
        # Create batch writer
        writer = Neo4jBatchWriter(
            connection_manager=manager,
            batch_size=100,  # Process 100 items per batch
            max_retries=3,
            retry_delay=1.0,
        )
        
        # Write transformation results
        logger.info(f"Writing {len(transformation_results)} resources to Neo4j...")
        metrics = writer.write_transformation_results(transformation_results)
        
        # Display metrics
        logger.info("=" * 60)
        logger.info("BATCH WRITE METRICS")
        logger.info("=" * 60)
        logger.info(f"Total nodes:          {metrics.total_nodes}")
        logger.info(f"Successful nodes:     {metrics.successful_nodes}")
        logger.info(f"Failed nodes:         {metrics.failed_nodes}")
        logger.info(f"Total relationships:  {metrics.total_relationships}")
        logger.info(f"Successful rels:      {metrics.successful_relationships}")
        logger.info(f"Failed rels:          {metrics.failed_relationships}")
        logger.info(f"Total batches:        {metrics.total_batches}")
        logger.info(f"Failed batches:       {metrics.failed_batches}")
        logger.info(f"Total duration:       {metrics.total_duration_ms:.2f}ms")
        logger.info(f"Avg batch duration:   {metrics.avg_batch_duration_ms:.2f}ms")
        
        if metrics.errors:
            logger.warning(f"Encountered {len(metrics.errors)} errors:")
            for error in metrics.errors[-5:]:  # Show last 5 errors
                logger.warning(f"  - {error}")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during Neo4j operations: {e}", exc_info=True)
        
    finally:
        # Always close connection
        manager.close()
        logger.info("Neo4j connection closed")


def main():
    """Main execution function."""
    logger.info("Starting Neo4j Batch Write Example")
    logger.info("=" * 60)
    
    # Step 1: Create sample data
    logger.info("Step 1: Creating sample GCP resources...")
    resources = create_sample_gcp_resources()
    logger.info(f"Created {len(resources)} sample resources")
    
    # Step 2: Transform resources
    logger.info("\nStep 2: Transforming resources...")
    transformation_results = transform_resources(resources)
    
    # Step 3: Write to Neo4j
    logger.info("\nStep 3: Writing to Neo4j...")
    write_to_neo4j(transformation_results)
    
    logger.info("\nExample completed successfully!")


if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for required Neo4j configuration
    required_vars = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these in your .env file (copy from .env.example)")
        sys.exit(1)
    
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nExample interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Example failed with error: {e}", exc_info=True)
        sys.exit(1)

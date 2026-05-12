"""
Full GCP Ingestion Pipeline Example

This example demonstrates how to set up and run the complete GCP Digital Twin
ingestion pipeline with all components integrated.

Prerequisites:
    1. Neo4j database running (local or cloud)
    2. GCP project with APIs enabled
    3. GCP service account key file
    4. Pub/Sub topic and subscription configured
    5. Environment variables set (see .env.example)

Usage:
    # Using environment variables
    python examples/full_pipeline_example.py
    
    # Or with explicit configuration
    python examples/full_pipeline_example.py --config custom_config.json
"""

import asyncio
import sys
import os
import argparse
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion_pipeline.pipeline import (
    GCPIngestionPipeline,
    PipelineConfig,
    PipelineError,
)


def load_config_from_file(config_path: str) -> PipelineConfig:
    """Load pipeline configuration from JSON file."""
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    return PipelineConfig(**config_data)


async def run_pipeline_with_status_monitoring(pipeline: GCPIngestionPipeline):
    """
    Run pipeline with periodic status monitoring.
    
    This demonstrates how to:
    1. Initialize the pipeline
    2. Start processing
    3. Monitor status periodically
    4. Handle graceful shutdown
    """
    print("=" * 80)
    print("GCP Digital Twin Ingestion Pipeline")
    print("=" * 80)
    print()
    
    try:
        # Initialize pipeline
        print("Initializing pipeline...")
        await pipeline.initialize()
        print("✓ Pipeline initialized successfully")
        print()
        
        # Show initial status
        status = pipeline.get_status()
        print("Initial Status:")
        print(f"  Configuration: {status['config']['gcp_project_id']}")
        print(f"  Neo4j URI: {status['config']['neo4j_uri']}")
        print(f"  Pub/Sub Topic: {status['config']['pubsub_topic']}")
        print(f"  Batch Size: {status['config']['batch_size']}")
        print(f"  Max Workers: {status['config']['max_workers']}")
        print()
        
        # Start pipeline in background
        print("Starting pipeline...")
        pipeline_task = asyncio.create_task(pipeline.start())
        print("✓ Pipeline started")
        print()
        print("Monitoring pipeline (Press Ctrl+C to stop)...")
        print("-" * 80)
        print()
        
        # Monitor status every 30 seconds
        status_interval = 30
        iteration = 0
        
        while not pipeline_task.done():
            await asyncio.sleep(status_interval)
            iteration += 1
            
            status = pipeline.get_status()
            
            print(f"\n[Status Update #{iteration}] {asyncio.get_event_loop().time():.0f}s")
            print("-" * 80)
            
            # Show metrics if available
            if 'metrics' in status:
                metrics = status['metrics']
                print(f"Resources Processed: {metrics.get('pipeline_resources_processed', 0)}")
                print(f"Errors: {metrics.get('pipeline_errors_total', 0)}")
                print(f"Validation Errors: {metrics.get('pipeline_validation_errors', 0)}")
                print(f"Transformation Errors: {metrics.get('pipeline_transformation_errors', 0)}")
            
            # Show health status
            if 'health' in status:
                health = status['health']
                print(f"\nHealth Status: {health['overall_status']}")
                if health['healthy_components']:
                    print(f"  ✓ Healthy: {', '.join(health['healthy_components'])}")
                if health['degraded_components']:
                    print(f"  ⚠ Degraded: {', '.join(health['degraded_components'])}")
                if health['unhealthy_components']:
                    print(f"  ✗ Unhealthy: {', '.join(health['unhealthy_components'])}")
            
            # Show event subscriber status
            if 'event_subscriber' in status:
                sub_status = status['event_subscriber']
                print(f"\nEvent Subscriber:")
                print(f"  Running: {sub_status.get('is_running', False)}")
                print(f"  Callbacks Registered: {sub_status.get('callback_count', 0)}")
                print(f"  Subscriptions: {sub_status.get('subscription_count', 0)}")
            
            print()
        
        # Wait for pipeline task to complete
        await pipeline_task
        
    except KeyboardInterrupt:
        print("\n\nReceived shutdown signal...")
        print("Stopping pipeline gracefully...")
        await pipeline.stop()
        print("✓ Pipeline stopped")
        
    except PipelineError as e:
        print(f"\n✗ Pipeline error: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        print("\nShutting down pipeline...")
        await pipeline.shutdown()
        print("✓ Pipeline shutdown complete")
        print()


async def run_simple_pipeline():
    """
    Simple pipeline example using environment variables.
    
    This is the most straightforward way to run the pipeline.
    """
    # Load configuration from environment
    config = PipelineConfig.from_env()
    
    # Create pipeline
    pipeline = GCPIngestionPipeline(config=config)
    
    # Run with monitoring
    await run_pipeline_with_status_monitoring(pipeline)


async def run_custom_config_pipeline(config_path: str):
    """
    Pipeline example using custom configuration file.
    
    This demonstrates loading configuration from a JSON file.
    """
    # Load configuration from file
    config = load_config_from_file(config_path)
    
    # Create pipeline
    pipeline = GCPIngestionPipeline(config=config)
    
    # Run with monitoring
    await run_pipeline_with_status_monitoring(pipeline)


async def run_inline_config_pipeline():
    """
    Pipeline example with inline configuration.
    
    This demonstrates creating configuration programmatically.
    """
    # Create configuration inline
    pipeline = GCPIngestionPipeline(
        gcp_project_id=os.getenv("GCP_PROJECT_ID"),
        gcp_service_account_path=os.getenv("GCP_SERVICE_ACCOUNT_KEY_PATH"),
        gcp_region=os.getenv("GCP_REGION", "us-central1"),
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_username=os.getenv("NEO4J_USERNAME", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD"),
        pubsub_topic=os.getenv("PUBSUB_TOPIC", "gcp-resource-events"),
        pubsub_subscription=os.getenv("PUBSUB_SUBSCRIPTION", "pipeline-subscription"),
        batch_size=100,
        max_workers=10,
        log_level="INFO",
        enable_prometheus=True,
    )
    
    # Run with monitoring
    await run_pipeline_with_status_monitoring(pipeline)


def validate_environment():
    """Validate required environment variables are set."""
    required_vars = [
        "GCP_PROJECT_ID",
        "GCP_SERVICE_ACCOUNT_KEY_PATH",
        "NEO4J_URI",
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD",
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("✗ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
        print("Please set these variables in your .env file or environment.")
        print("See .env.example for reference.")
        sys.exit(1)


def main():
    """Main entry point for the example."""
    parser = argparse.ArgumentParser(
        description="Run the GCP Digital Twin ingestion pipeline"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON configuration file",
    )
    parser.add_argument(
        "--inline",
        action="store_true",
        help="Use inline configuration instead of environment variables",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration without running pipeline",
    )
    
    args = parser.parse_args()
    
    # Validate environment unless using config file
    if not args.config:
        validate_environment()
    
    # Validate only mode
    if args.validate_only:
        print("✓ Environment validation passed")
        if args.config:
            try:
                config = load_config_from_file(args.config)
                config.validate()
                print(f"✓ Configuration file validation passed: {args.config}")
            except Exception as e:
                print(f"✗ Configuration validation failed: {e}")
                sys.exit(1)
        sys.exit(0)
    
    # Run pipeline based on mode
    try:
        if args.config:
            print(f"Loading configuration from: {args.config}")
            asyncio.run(run_custom_config_pipeline(args.config))
        elif args.inline:
            print("Using inline configuration")
            asyncio.run(run_inline_config_pipeline())
        else:
            print("Using environment variable configuration")
            asyncio.run(run_simple_pipeline())
    except KeyboardInterrupt:
        print("\nShutdown complete.")


if __name__ == "__main__":
    main()

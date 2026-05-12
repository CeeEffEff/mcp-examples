# Neo4j Operations Module

Provides batch write operations, connection management, and query building for Neo4j database operations in the GCP Digital Twin ingestion pipeline.

## Overview

The `neo4j_ops` module handles all interactions with the Neo4j graph database, implementing efficient batch write operations with transaction management, retry logic, and comprehensive metrics tracking.

## Architecture

```
neo4j_ops/
├── __init__.py           # Public API exports
├── connection.py         # Neo4j connection management
├── query_builder.py      # Cypher query generation
├── batch_writer.py       # Batch write operations
└── README.md            # This file
```

## Components

### 1. Connection Manager (`connection.py`)

Manages Neo4j database connections with pooling and health checks.

**Features:**
- Connection pooling with configurable pool size
- Automatic reconnection on transient failures
- Health check validation
- Graceful shutdown
- Thread-safe operations

**Usage:**
```python
from ingestion_pipeline.neo4j_ops import get_connection_manager

# Get singleton connection manager
manager = get_connection_manager()
manager.connect()

# Use context manager
with manager.session() as session:
    result = session.run("MATCH (n) RETURN count(n)")
    
# Health check
health = manager.health_check()
print(health)

# Close connection
manager.close()
```

**Configuration:**
Set these environment variables in `.env`:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

### 2. Query Builder (`query_builder.py`)

Generates parameterized Cypher queries for Neo4j MERGE operations.

**Features:**
- Node MERGE with ON CREATE and ON MATCH clauses
- Relationship MERGE with property updates
- Temporal property handling (createdAt, updatedAt)
- Batch query generation with UNWIND
- Parameter sanitization

**Usage:**
```python
from ingestion_pipeline.neo4j_ops import CypherQueryBuilder

builder = CypherQueryBuilder()

# Build node MERGE query
query, params = builder.build_node_merge(
    label="VirtualMachine",
    unique_key="id",
    properties={"id": "vm-123", "name": "my-vm", "status": "RUNNING"}
)

# Build batch node MERGE
query, params = builder.build_batch_node_merge(
    label="VirtualMachine",
    unique_key="id",
    nodes=[
        {"id": "vm-1", "name": "vm1"},
        {"id": "vm-2", "name": "vm2"}
    ]
)

# Build relationship MERGE
query, params = builder.build_relationship_merge(
    source_label="VirtualMachine",
    source_key="id",
    source_id="vm-123",
    target_label="Subnet",
    target_key="id",
    target_id="subnet-456",
    relationship_type="ATTACHED_TO",
    properties={"interface_index": 0}
)
```

### 3. Batch Writer (`batch_writer.py`)

Handles batch write operations to Neo4j with transactions.

**Features:**
- Configurable batch sizes for optimal performance
- Transaction management with auto-commit
- Atomic batch operations (all-or-nothing)
- Exponential backoff retry logic
- Comprehensive metrics tracking
- Error handling with detailed logging

**Usage:**
```python
from ingestion_pipeline.neo4j_ops import (
    Neo4jBatchWriter,
    get_connection_manager
)

# Connect to Neo4j
manager = get_connection_manager()
manager.connect()

# Create batch writer
writer = Neo4jBatchWriter(
    connection_manager=manager,
    batch_size=100,
    max_retries=3,
    retry_delay=1.0
)

# Write nodes
metrics = writer.write_nodes(
    label="VirtualMachine",
    unique_key="id",
    nodes=[
        {"id": "vm-1", "name": "vm1", "status": "RUNNING"},
        {"id": "vm-2", "name": "vm2", "status": "STOPPED"}
    ]
)

# Write relationships
metrics = writer.write_relationships([
    {
        "source_label": "VirtualMachine",
        "source_key": "id",
        "source_id": "vm-1",
        "target_label": "Subnet",
        "target_key": "id",
        "target_id": "subnet-1",
        "relationship_type": "ATTACHED_TO",
        "properties": {"index": 0}
    }
])

# Write transformation results (recommended)
metrics = writer.write_transformation_results(transformation_results)

# Check metrics
print(f"Nodes written: {metrics.successful_nodes}/{metrics.total_nodes}")
print(f"Relationships written: {metrics.successful_relationships}/{metrics.total_relationships}")
print(f"Duration: {metrics.total_duration_ms:.2f}ms")
```

## Integration with Transformation Layer

The module is designed to work seamlessly with the transformation layer:

```python
from ingestion_pipeline.transformation import TransformerFactory
from ingestion_pipeline.neo4j_ops import (
    Neo4jBatchWriter,
    get_connection_manager
)

# Transform GCP resources
transformer = TransformerFactory.get_transformer('compute.instances')
results = [transformer.transform(resource) for resource in gcp_resources]

# Convert to dict format
transformation_results = [
    {
        "node": result.node,
        "node_label": result.node_label,
        "relationships": result.relationships,
        "resource_id": result.resource_id,
        "resource_type": result.resource_type,
    }
    for result in results
]

# Write to Neo4j
manager = get_connection_manager()
manager.connect()

writer = Neo4jBatchWriter(manager, batch_size=100)
metrics = writer.write_transformation_results(transformation_results)

manager.close()
```

## Performance Optimization

### Batch Size

The default batch size is 100 items. Adjust based on your needs:

- **Small batches (10-50):** Better for real-time updates, lower memory usage
- **Medium batches (100-500):** Balanced performance, recommended default
- **Large batches (500-1000):** Maximum throughput, higher memory usage

```python
writer = Neo4jBatchWriter(manager, batch_size=500)
```

### Connection Pool

Configure connection pool settings:

```python
manager = Neo4jConnectionManager(
    max_connection_pool_size=50,      # Max connections in pool
    max_connection_lifetime=3600,     # Connection lifetime (seconds)
    connection_acquisition_timeout=60  # Timeout for acquiring connection
)
```

### Retry Strategy

Configure retry behavior for transient failures:

```python
writer = Neo4jBatchWriter(
    manager,
    max_retries=3,      # Max retry attempts
    retry_delay=1.0     # Initial delay between retries (exponential backoff)
)
```

## Metrics Tracking

The `BatchWriteMetrics` class tracks comprehensive statistics:

```python
metrics = writer.write_transformation_results(results)

print(metrics.to_dict())
# {
#     "total_nodes": 1000,
#     "successful_nodes": 995,
#     "failed_nodes": 5,
#     "total_relationships": 2500,
#     "successful_relationships": 2480,
#     "failed_relationships": 20,
#     "total_batches": 10,
#     "failed_batches": 1,
#     "total_duration_ms": 5234.56,
#     "avg_batch_duration_ms": 523.46,
#     "error_count": 25,
#     "errors": [...]  # Last 10 errors
# }
```

## Error Handling

The module implements comprehensive error handling:

### Retryable Errors
- `TransientError`: Temporary Neo4j failures
- `ServiceUnavailable`: Neo4j service not reachable

These errors trigger automatic retry with exponential backoff.

### Non-Retryable Errors
- `ConstraintError`: Uniqueness constraint violations
- `ClientError`: Invalid queries or parameters

These errors fail immediately with detailed logging.

### Example Error Handling

```python
try:
    metrics = writer.write_nodes(label="VirtualMachine", unique_key="id", nodes=nodes)
    
    if metrics.failed_nodes > 0:
        logger.warning(f"Failed to write {metrics.failed_nodes} nodes")
        for error in metrics.errors:
            logger.error(f"Error: {error}")
            
except Neo4jConnectionError as e:
    logger.error(f"Connection failed: {e}")
except BatchWriterError as e:
    logger.error(f"Batch write failed: {e}")
```

## Best Practices

1. **Use Connection Manager Singleton:**
   ```python
   manager = get_connection_manager()  # Reuses existing connection
   ```

2. **Always Close Connections:**
   ```python
   try:
       manager.connect()
       # ... operations ...
   finally:
       manager.close()
   ```

3. **Use Context Managers:**
   ```python
   with manager.session() as session:
       result = session.run(query, params)
   ```

4. **Monitor Metrics:**
   ```python
   metrics = writer.write_transformation_results(results)
   if metrics.failed_batches > 0:
       # Handle failures
       pass
   ```

5. **Configure Appropriate Batch Sizes:**
   - Start with default (100)
   - Monitor performance
   - Adjust based on memory and latency requirements

6. **Use write_transformation_results():**
   This is the recommended high-level API that handles both nodes and relationships.

## Testing

See `examples/neo4j_batch_write_example.py` for a complete integration example.

To run the example:
```bash
# Set environment variables in .env
cp .env.example .env
# Edit .env with your Neo4j credentials

# Run example
python examples/neo4j_batch_write_example.py
```

## Dependencies

- `neo4j>=5.14.1` - Official Neo4j Python driver
- `pydantic>=2.5.3` - Data validation (used by transformation layer)

Install with:
```bash
pip install -r requirements.txt
```

## Neo4j Setup

1. Install Neo4j Desktop or use Neo4j Aura
2. Create a database
3. Run constraints and indexes from `docs/neo4j-schema/constraints-and-indexes.cypher`
4. Configure connection in `.env` file

## Troubleshooting

### Connection Issues

**Problem:** `Neo4jConnectionError: Service unavailable`
**Solution:** 
- Check Neo4j is running
- Verify URI, username, password in `.env`
- Check firewall settings

### Constraint Violations

**Problem:** `ConstraintError: Node with id already exists`
**Solution:**
- This is expected for MERGE operations (idempotent)
- Check logs to ensure it's not a data issue
- Verify unique keys are correct

### Performance Issues

**Problem:** Slow batch writes
**Solution:**
- Increase batch size (100 → 500)
- Ensure Neo4j indexes are created
- Check network latency
- Monitor Neo4j query performance

### Memory Issues

**Problem:** Out of memory errors
**Solution:**
- Decrease batch size (100 → 50)
- Process data in smaller chunks
- Check for memory leaks in transformation logic

## Version History

- **v0.1.0** (2025-06-10): Initial implementation
  - Connection management
  - Query building
  - Batch write operations
  - Metrics tracking
  - Retry logic

## License

Part of the GCP Digital Twin Agent System project.

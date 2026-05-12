# Neo4j Graph Queries Module

Comprehensive query system for the GCP Digital Twin graph database, providing powerful capabilities for resource lookup, dependency analysis, relationship exploration, cost analysis, and optimization recommendations.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Query Types](#query-types)
  - [Resource Queries](#resource-queries)
  - [Traversal Queries](#traversal-queries)
  - [Relationship Queries](#relationship-queries)
  - [Analysis Queries](#analysis-queries)
- [Query Caching](#query-caching)
- [API Reference](#api-reference)
- [Performance Optimization](#performance-optimization)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Overview

The graph queries module provides a high-level, Pythonic interface to query the Neo4j-based GCP digital twin. It abstracts away the complexity of Cypher queries while providing comprehensive functionality for:

- **Resource Discovery**: Find resources by ID, type, properties, or text search
- **Graph Traversal**: Analyze dependencies, find paths, detect cycles
- **Relationship Analysis**: Explore connections between resources
- **Infrastructure Analysis**: Cost analysis, bottleneck detection, security scanning
- **Performance**: Built-in caching with LRU and TTL strategies

### Key Features

✅ **Type-Safe**: Full type hints for IDE support  
✅ **Singleton Pattern**: Efficient resource management  
✅ **Monitoring Integration**: Automatic metrics and logging  
✅ **Error Handling**: Comprehensive exception hierarchy  
✅ **Query Caching**: LRU cache with TTL for performance  
✅ **Pagination Support**: Built-in limit/skip for large result sets  
✅ **Connection Management**: Automatic session handling  

## Installation

The module is part of the ingestion pipeline. No separate installation is required if you have the main project installed.

### Dependencies

```python
neo4j >= 5.0.0
structlog
prometheus-client
```

### Environment Variables

```bash
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

## Quick Start

```python
from ingestion_pipeline.graph_queries import (
    get_resource_queries,
    get_traversal_queries,
    get_relationship_queries,
    get_analysis_queries,
)

# Resource queries
resource_queries = get_resource_queries()
vm = resource_queries.find_by_id("projects/my-project/zones/us-central1-a/instances/web-server")

# Traversal queries
traversal_queries = get_traversal_queries()
dependencies = traversal_queries.find_dependencies(vm['id'])

# Relationship queries
relationship_queries = get_relationship_queries()
patterns = relationship_queries.analyze_relationship_patterns("my-project")

# Analysis queries
analysis_queries = get_analysis_queries()
costs = analysis_queries.analyze_costs("my-project")
```

## Query Types

### Resource Queries

Find and search for GCP resources in the graph.

#### find_by_id

Find a specific resource by its unique ID.

```python
vm = resource_queries.find_by_id(
    "projects/my-project/zones/us-central1-a/instances/web-server-1"
)
```

#### find_by_type

Find all resources of a specific type.

```python
vms = resource_queries.find_by_type(
    resource_type="VirtualMachine",
    project_id="my-project",
    status="RUNNING",
    limit=100
)
```

#### find_by_properties

Filter resources by property values.

```python
result = resource_queries.find_by_properties(
    resource_type="VirtualMachine",
    properties={"zone": "us-central1-a", "status": "RUNNING"},
    match_mode="AND"  # or "OR"
)
```

#### search

Full-text search across resource names and descriptions.

```python
results = resource_queries.search(
    search_term="production",
    resource_types=["VirtualMachine", "StorageBucket"],
    project_id="my-project"
)
```

#### count

Count resources with optional filtering.

```python
vm_count = resource_queries.count(
    resource_type="VirtualMachine",
    project_id="my-project",
    status="RUNNING"
)
```

#### Time-Based Queries

```python
# Recently created
recent = resource_queries.find_recently_created(
    hours=24,
    project_id="my-project"
)

# Recently updated
updated = resource_queries.find_recently_updated(
    hours=48,
    resource_type="VirtualMachine"
)
```

### Traversal Queries

Navigate the graph to understand resource relationships and dependencies.

#### find_dependencies

Find all resources that a given resource depends on.

```python
deps = traversal_queries.find_dependencies(
    resource_id="vm-id",
    max_depth=5,
    include_indirect=True
)
```

#### find_dependents

Find all resources that depend on a given resource.

```python
dependents = traversal_queries.find_dependents(
    resource_id="disk-id",
    max_depth=3
)
```

#### analyze_impact

Assess the impact if a resource fails.

```python
impact = traversal_queries.analyze_impact(
    resource_id="critical-vm-id",
    max_depth=10
)

print(f"Total affected: {impact['total_affected']}")
print(f"Critical resources: {impact['critical_count']}")
```

#### find_shortest_path

Find the shortest path between two resources.

```python
path = traversal_queries.find_shortest_path(
    source_id="vm-id",
    target_id="storage-id",
    path_type=PathType.SHORTEST
)
```

#### find_circular_dependencies

Detect circular dependency chains.

```python
cycles = traversal_queries.find_circular_dependencies(
    project_id="my-project",
    max_cycle_length=10
)
```

#### trace_network_path

Trace network connectivity between resources.

```python
network_path = traversal_queries.trace_network_path(
    source_id="vm-1-id",
    target_id="vm-2-id"
)
```

### Relationship Queries

Analyze relationships between resources.

#### find_relationships_between

Find all relationships between two specific resources.

```python
rels = relationship_queries.find_relationships_between(
    source_id="vm-id",
    target_id="disk-id",
    relationship_types=["USES", "DEPENDS_ON"]
)
```

#### find_by_type

Find all relationships of a specific type.

```python
depends_on_rels = relationship_queries.find_by_type(
    relationship_type="DEPENDS_ON",
    project_id="my-project",
    include_nodes=True
)
```

#### count_relationships

Count relationships for a resource.

```python
counts = relationship_queries.count_relationships(
    resource_id="vm-id",
    direction="both"  # or "incoming" or "outgoing"
)

print(f"Total: {counts['total']}")
print(f"Incoming: {counts['incoming']}")
print(f"Outgoing: {counts['outgoing']}")
```

#### analyze_relationship_patterns

Identify common relationship patterns.

```python
patterns = relationship_queries.analyze_relationship_patterns(
    project_id="my-project",
    min_count=2
)

# Access type distribution
for rel_type in patterns.data['type_distribution']:
    print(f"{rel_type['relationship_type']}: {rel_type['count']}")

# Access common patterns
for pattern in patterns.data['pair_patterns']:
    print(f"{pattern['source_type']} -[{pattern['relationship_type']}]-> "
          f"{pattern['target_type']}")
```

#### find_unused_relationships

Find orphaned relationships (pointing to deleted resources).

```python
orphaned = relationship_queries.find_unused_relationships(
    project_id="my-project"
)
```

### Analysis Queries

Advanced analysis for cost optimization, security, and performance.

#### analyze_costs

Analyze infrastructure costs.

```python
costs = analysis_queries.analyze_costs(
    project_id="my-project",
    time_window_days=30,
    group_by="resource_type"  # or "zone" or "label"
)

print(f"Total monthly cost: ${costs['total_monthly_cost']:.2f}")
for item in costs['breakdown']:
    print(f"{item['resource_type']}: ${item['total_cost']:.2f}")
```

#### identify_bottlenecks

Find resources with high dependency counts.

```python
bottlenecks = analysis_queries.identify_bottlenecks(
    project_id="my-project",
    min_dependency_count=5
)

for bn in bottlenecks.data:
    print(f"{bn['resource_name']}: {bn['dependency_count']} dependencies")
    print(f"Severity: {bn['severity']}")
    print(f"Recommendation: {bn['recommendation']}")
```

#### analyze_network_topology

Analyze VPC network structure.

```python
topology = analysis_queries.analyze_network_topology(
    vpc_id="vpc-id",
    include_subnets=True,
    include_routes=True
)

print(f"Subnets: {len(topology['subnets'])}")
print(f"Routes: {len(topology['routes'])}")
```

#### find_security_issues

Scan for security configuration issues.

```python
issues = analysis_queries.find_security_issues(
    project_id="my-project",
    check_types=["public_ips", "open_firewall", "unencrypted", "default_sa"]
)

for issue in issues.data:
    print(f"{issue['severity']}: {issue['issue_type']}")
    print(f"Resource: {issue['resource_name']}")
    print(f"Recommendation: {issue['recommendation']}")
```

#### suggest_optimizations

Get optimization recommendations.

```python
optimizations = analysis_queries.suggest_optimizations(
    project_id="my-project",
    optimization_types=["underutilized", "orphaned", "redundant"]
)

total_savings = sum(opt.get('estimated_monthly_savings', 0) or 0 
                   for opt in optimizations.data)
print(f"Potential savings: ${total_savings:.2f}/month")
```

## Query Caching

The module includes an LRU cache with TTL for query optimization.

### Basic Usage

```python
from ingestion_pipeline.graph_queries import get_query_cache

cache = get_query_cache()

# Manual caching
cache.set("my-key", {"data": "value"}, ttl_seconds=300)
result = cache.get("my-key")

# Cache statistics
stats = cache.get_statistics()
print(f"Hit rate: {stats['hit_rate']:.1%}")
```

### Cache Management

```python
# Invalidate specific entry
cache.invalidate("my-key")

# Invalidate by pattern
cache.invalidate_pattern("VirtualMachine")

# Cleanup expired entries
expired_count = cache.cleanup_expired()

# Clear all
cache.clear()
```

### Decorator Usage

```python
from ingestion_pipeline.graph_queries import cached_query

@cached_query(ttl_seconds=600)
def my_expensive_query(resource_id: str):
    # Query implementation
    return result
```

## API Reference

### Base Classes

#### QueryResult

Container for query results with metadata.

```python
class QueryResult:
    data: Any                    # Query result data
    query_type: str             # Type of query executed
    record_count: int           # Number of records returned
    execution_time: float       # Query execution time (seconds)
    timestamp: datetime         # When query was executed
```

### Exceptions

```python
QueryError                      # Base exception
├── QueryValidationError       # Invalid parameters
├── QueryExecutionError        # Neo4j/connection errors
└── QueryResultError           # Result processing errors
```

### Configuration

All query classes accept optional configuration:

```python
queries = get_resource_queries(
    connection_manager=custom_manager,  # Custom connection manager
    monitoring_enabled=True             # Enable/disable monitoring
)
```

## Performance Optimization

### Best Practices

1. **Use Pagination**: Always set `limit` for large result sets
2. **Enable Caching**: Use cache for frequently accessed data
3. **Specific Queries**: Use `find_by_id` instead of `search` when possible
4. **Filter Early**: Apply filters in queries rather than in Python
5. **Monitor Performance**: Check query execution times in logs

### Query Performance Tips

```python
# Good: Specific query with filters
vms = resource_queries.find_by_type(
    resource_type="VirtualMachine",
    project_id="my-project",
    status="RUNNING",
    limit=100
)

# Bad: Broad query with Python filtering
all_vms = resource_queries.find_by_type("VirtualMachine")
running_vms = [vm for vm in all_vms.data if vm['status'] == 'RUNNING']
```

### Caching Strategy

- **Short TTL (60-300s)**: Frequently changing data (resource status)
- **Medium TTL (300-3600s)**: Relatively stable data (resource lists)
- **Long TTL (3600-86400s)**: Rarely changing data (network topology)

## Error Handling

### Exception Handling

```python
from ingestion_pipeline.graph_queries import (
    QueryValidationError,
    QueryExecutionError,
    QueryResultError
)

try:
    vm = resource_queries.find_by_id(vm_id)
except QueryValidationError as e:
    # Invalid parameters
    logger.error(f"Invalid query parameters: {e}")
except QueryExecutionError as e:
    # Neo4j connection/query error
    logger.error(f"Query execution failed: {e}")
except QueryResultError as e:
    # Result processing error
    logger.error(f"Failed to process results: {e}")
```

### Validation

All query methods validate parameters before execution:

```python
# Raises QueryValidationError if resource_id is empty
vm = resource_queries.find_by_id("")

# Raises QueryValidationError if limit is negative
vms = resource_queries.find_by_type("VirtualMachine", limit=-1)
```

## Examples

### Complete Workflow Example

```python
from ingestion_pipeline.graph_queries import (
    get_resource_queries,
    get_traversal_queries,
    get_analysis_queries
)

# 1. Find a critical resource
resource_queries = get_resource_queries()
critical_vm = resource_queries.find_by_id("critical-vm-id")

# 2. Analyze its dependencies
traversal_queries = get_traversal_queries()
deps = traversal_queries.find_dependencies(critical_vm['id'])
print(f"Depends on {len(deps.data)} resources")

# 3. Assess impact if it fails
impact = traversal_queries.analyze_impact(critical_vm['id'])
print(f"Would affect {impact['total_affected']} resources")

# 4. Check for bottlenecks
analysis_queries = get_analysis_queries()
bottlenecks = analysis_queries.identify_bottlenecks("my-project")

if any(bn['resource_id'] == critical_vm['id'] for bn in bottlenecks.data):
    print("⚠️  Critical VM is a bottleneck!")
    
# 5. Get optimization suggestions
optimizations = analysis_queries.suggest_optimizations("my-project")
```

For more examples, see `examples/graph_query_examples.py`.

## Testing

Run the test suite:

```bash
# All tests
pytest tests/test_graph_queries.py -v

# Specific test class
pytest tests/test_graph_queries.py::TestResourceQueries -v

# With coverage
pytest tests/test_graph_queries.py --cov=src/ingestion_pipeline/graph_queries
```

## Monitoring

All queries are automatically monitored:

- **Metrics**: Query counts, durations, errors
- **Logging**: Structured logs with query context
- **Health Checks**: Connection status monitoring

Access metrics:

```python
from ingestion_pipeline.monitoring import get_metrics

metrics = get_metrics()
# Metrics are automatically collected for all queries
```

## Contributing

When adding new query methods:

1. Extend the appropriate query class (`ResourceQueries`, `TraversalQueries`, etc.)
2. Use `@track_query_performance` decorator
3. Follow validation patterns from existing methods
4. Add comprehensive tests
5. Update this README with usage examples

## License

Part of the GCP Digital Twin Agent System project.

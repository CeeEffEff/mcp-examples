# GCP Digital Twin - Neo4j Schema Documentation

## Overview

This directory contains comprehensive documentation for the Neo4j graph database schema designed to represent a Google Cloud Platform (GCP) digital twin environment.

## Documentation Files

### Core Schema Documents

1. **[schema-overview.md](schema-overview.md)** - **START HERE**
   - Complete schema documentation with visual models
   - Node and relationship reference guide
   - Common query patterns (50+ examples)
   - Implementation guidelines
   - Performance optimization strategies
   - Schema maintenance procedures

2. **[gcp-resource-inventory.md](gcp-resource-inventory.md)**
   - Catalog of 50+ GCP resource types
   - Organized by service category (Compute, Storage, Network, etc.)
   - Core attributes and lifecycle states
   - API endpoints and resource identifiers
   - Relationship mapping between resources

3. **[node-schema-definition.md](node-schema-definition.md)**
   - Detailed property specifications for all 48 node labels
   - Data types for each property
   - Sample Cypher CREATE statements
   - Common properties shared across nodes
   - Property naming conventions

4. **[relationship-schema-definition.md](relationship-schema-definition.md)**
   - 35+ relationship type specifications
   - Directionality and cardinality rules
   - Relationship properties and metadata
   - 25+ sample Cypher patterns
   - 10 complex graph traversal queries

5. **[constraints-and-indexes.cypher](constraints-and-indexes.cypher)**
   - Production-ready Cypher DDL script
   - 65 uniqueness constraints
   - 137 performance indexes (single, composite, full-text, relationship)
   - 17 existence constraints
   - Testing framework and verification queries
   - Maintenance and monitoring scripts

6. **[schema-diagrams.plantuml](schema-diagrams.plantuml)**
   - Visual schema representation in PlantUML format
   - Entity-relationship diagram with all node types
   - Color-coded by resource category
   - Complete relationship mappings

## Quick Start

### 1. Understanding the Schema

Start with the [schema-overview.md](schema-overview.md) document which provides:
- High-level architecture explanation
- Visual Mermaid diagrams embedded in the documentation
- Complete reference tables for all node and relationship types
- Data dictionary with property definitions

### 2. Implementing the Schema

Follow this sequence:

```bash
# Step 1: Review the schema documentation
cat schema-overview.md

# Step 2: Initialize Neo4j database with constraints and indexes
cat constraints-and-indexes.cypher | cypher-shell -u neo4j -p <password>

# Step 3: Verify schema creation
cypher-shell -u neo4j -p <password> "SHOW CONSTRAINTS;"
cypher-shell -u neo4j -p <password> "CALL db.indexes();"

# Step 4: Begin data ingestion (see Implementation Guidelines in overview)
```

### 3. Generating Visual Diagrams

#### Using PlantUML (Recommended)

The `schema-diagrams.plantuml` file can be rendered using various tools:

**Option 1: VS Code Extension**
```bash
# Install PlantUML extension in VS Code
# Extension ID: jebbs.plantuml
# Open schema-diagrams.plantuml and use Alt+D to preview
```

**Option 2: Command Line**
```bash
# Install PlantUML
brew install plantuml  # macOS
apt-get install plantuml  # Ubuntu/Debian

# Generate PNG diagram
plantuml -tpng docs/neo4j-schema/schema-diagrams.plantuml

# Generate SVG diagram (vector, recommended)
plantuml -tsvg docs/neo4j-schema/schema-diagrams.plantuml
```

**Option 3: Online Service**
- Visit: http://www.plantuml.com/plantuml
- Paste the contents of `schema-diagrams.plantuml`
- Download the rendered diagram

#### Using Mermaid

The overview document includes Mermaid diagrams that render automatically on:
- GitHub (native support)
- GitLab (native support)
- VS Code with Mermaid extension
- Many documentation platforms

### 4. Common Query Patterns

The [schema-overview.md](schema-overview.md) includes 50+ query examples organized by use case:

- **Resource Discovery**: Find resources by project, region, status
- **Network Topology**: Trace network paths, analyze firewall rules
- **Dependency Analysis**: Find dependencies, calculate depth, detect cycles
- **Impact Assessment**: Identify affected resources, downstream impacts
- **Cost Optimization**: Find unused resources, analyze disk usage
- **Security Analysis**: Audit service accounts, check permissions
- **Monitoring**: Find resources without monitoring, check alerts
- **Temporal Analysis**: Track resource age, find recent changes
- **Full-Text Search**: Search across resource metadata
- **Graph Traversal**: Find shortest paths, N-hop neighbors

## Schema Statistics

- **Node Labels**: 48 (representing different GCP resource types)
- **Relationship Types**: 35+ (defining connections between resources)
- **Uniqueness Constraints**: 65 (ensuring data integrity)
- **Indexes**: 137 total
  - 48 uniqueness constraint backing indexes
  - 45 single-property indexes
  - 16 composite indexes
  - 11 full-text indexes
  - 9 relationship indexes
- **Existence Constraints**: 17 (enforcing mandatory properties)

## Schema Categories

### Organizational Resources (3 types)
- Organization, Folder, Project

### Compute Resources (8 types)
- VirtualMachine, InstanceTemplate, InstanceGroup, InstanceGroupManager
- GKECluster, GKENodePool, CloudFunction, AppEngineService

### Storage Resources (9 types)
- PersistentDisk, StorageBucket, CloudSQLInstance, BigQueryDataset
- BigQueryTable, DatastoreIndex, FilestoreInstance, MemorystoreInstance

### Network Resources (13 types)
- VPCNetwork, Subnetwork, FirewallRule, CloudRouter, VPNTunnel
- CloudInterconnect, LoadBalancer, BackendService, HealthCheck
- URLMap, SSLCertificate, IPAddress, CloudDNSZone

### Security & IAM (4 types)
- ServiceAccount, ServiceAccountKey, IAMPolicy, SecretManagerSecret

### Monitoring & Logging (5 types)
- LogSink, AlertPolicy, Dashboard, UptimeCheck

### Messaging & Events (2 types)
- PubSubTopic, PubSubSubscription

### Data Processing (4 types)
- DataflowJob, DataprocCluster, ComposerEnvironment, DataFusionInstance

## Implementation Guidelines

### Property Naming Conventions

- **Node Labels**: PascalCase (e.g., `VirtualMachine`, `StorageBucket`)
- **Properties**: camelCase (e.g., `projectId`, `machineType`)
- **Relationships**: UPPER_SNAKE_CASE (e.g., `ATTACHED_TO`, `DEPENDS_ON`)
- **Status Values**: UPPER_CASE (e.g., `RUNNING`, `STOPPED`)

### Data Ingestion Best Practices

1. **Use MERGE for Upserts**: Handles both create and update operations
2. **Batch Operations**: Process in batches of 1000 for optimal performance
3. **Create Nodes First**: Always create nodes before establishing relationships
4. **Use Transactions**: Ensure atomic operations for complex changes
5. **Validate Data**: Check required fields and data types before ingestion
6. **Monitor Performance**: Use PROFILE and EXPLAIN for query optimization

### Performance Expectations

With proper indexing:
- **Point Lookups**: < 1ms (find node by unique ID)
- **Range Queries**: 1-10ms (filter by project + region)
- **Relationship Traversals**: 10-100ms (1-3 hops)
- **Deep Traversals**: 100ms-1s (4-6 hops)
- **Full-Text Search**: 10-100ms depending on corpus size

## Maintenance

### Regular Health Checks

- **Daily**: Verify constraint integrity, check for orphaned nodes
- **Weekly**: Analyze index performance, check database statistics
- **Monthly**: Deep traversal performance tests, identify schema drift

### Backup Strategy

```bash
# Full database dump
neo4j-admin dump --database=neo4j --to=/backups/neo4j-$(date +%Y%m%d).dump

# Incremental backup (Enterprise Edition)
neo4j-admin backup --from=localhost --backup-dir=/backups --name=neo4j
```

### Schema Evolution

When adding new properties or node types:

1. Update the relevant schema documentation file
2. Create constraints and indexes for new properties
3. Update the overview document with new patterns
4. Test all sample queries for correctness
5. Update visual diagrams if topology changes
6. Version control changes with descriptive commits

## Testing

### Verify Schema Installation

```cypher
// Check all constraints are created
SHOW CONSTRAINTS;

// Check all indexes are online
CALL db.indexes() 
YIELD name, state, populationPercent
WHERE state <> 'ONLINE' OR populationPercent < 100
RETURN name, state, populationPercent;

// Verify uniqueness constraints
MATCH (vm:VirtualMachine)
WITH vm.id AS id, count(*) AS count
WHERE count > 1
RETURN id, count;
```

### Sample Data Testing

```cypher
// Create sample project
MERGE (p:Project {
  id: "projects/test-project",
  project_id: "test-project",
  name: "Test Project",
  project_number: "123456789",
  state: "ACTIVE",
  created_at: datetime()
});

// Create sample VM
MERGE (vm:VirtualMachine {
  id: "projects/test-project/zones/us-central1-a/instances/test-vm",
  name: "test-vm",
  project_id: "test-project",
  zone: "us-central1-a",
  region: "us-central1",
  machine_type: "n1-standard-1",
  status: "RUNNING",
  cpu_count: 1,
  memory_gb: 3.75,
  created_at: datetime()
});

// Create relationship
MATCH (p:Project {project_id: "test-project"}),
      (vm:VirtualMachine {name: "test-vm"})
MERGE (p)-[:CONTAINS {created_at: datetime()}]->(vm);

// Verify creation
MATCH (p:Project {project_id: "test-project"})-[:CONTAINS]->(vm:VirtualMachine)
RETURN p.name, vm.name, vm.status;
```

## Resources

### Neo4j Documentation
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Developer Guides](https://neo4j.com/developer/)
- [APOC Procedures](https://neo4j.com/labs/apoc/)
- [Neo4j Graph Data Science](https://neo4j.com/docs/graph-data-science/current/)

### GCP Documentation
- [GCP Resource Manager](https://cloud.google.com/resource-manager/docs)
- [Compute Engine API Reference](https://cloud.google.com/compute/docs/reference/rest/v1)
- [Cloud Storage API Reference](https://cloud.google.com/storage/docs/json_api)
- [GCP API Design Guide](https://cloud.google.com/apis/design)

### Visualization Tools
- [PlantUML](http://plantuml.com/) - UML diagram generation
- [Neo4j Bloom](https://neo4j.com/product/bloom/) - Graph visualization (Commercial)
- [Neo4j Browser](https://neo4j.com/developer/neo4j-browser/) - Built-in query tool
- [yEd](https://www.yworks.com/products/yed) - Free graph editor
- [Mermaid](https://mermaid-js.github.io/) - Markdown-based diagrams

## Support and Contribution

### Reporting Issues

If you find errors or have suggestions for improvement:

1. Check existing documentation for answers
2. Review the sample queries in `schema-overview.md`
3. Test your queries with EXPLAIN/PROFILE
4. Document the issue with:
   - Expected behavior
   - Actual behavior
   - Cypher query used
   - Error messages (if any)

### Contributing

When contributing schema updates:

1. Update all relevant documentation files
2. Add sample queries demonstrating new patterns
3. Update constraints and indexes as needed
4. Test thoroughly with sample data
5. Update visual diagrams
6. Document changes in the Changelog section

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-06-10 | Platform Team | Initial comprehensive schema documentation |

## License

This schema documentation is part of the GCP Digital Twin Agent System project.

---

**Last Updated**: 2025-06-10  
**Maintained By**: GCP Digital Twin Platform Team  
**Status**: ✅ Production Ready

// ============================================================================
// Neo4j Constraints and Indexes for GCP Digital Twin
// ============================================================================
// 
// Purpose: Implement data integrity constraints and performance optimization
//          indexes for the GCP resource graph database
// 
// Author: GCP Digital Twin Agent System
// Date: 2025-06-10
// Version: 1.0.0
// 
// Related Documentation:
// - Node Schema: docs/neo4j-schema/node-schema-definition.md
// - Relationship Schema: docs/neo4j-schema/relationship-schema-definition.md
// - GCP Resource Inventory: docs/neo4j-schema/gcp-resource-inventory.md
// 
// Execution Order:
// 1. Drop existing constraints/indexes (optional, for clean slate)
// 2. Create uniqueness constraints
// 3. Create existence constraints  
// 4. Create single-property indexes
// 5. Create composite indexes
// 6. Create full-text indexes
// 7. Verify constraints and indexes
// 
// ============================================================================

// ============================================================================
// SECTION 1: DROP EXISTING CONSTRAINTS AND INDEXES (Optional)
// ============================================================================
// Uncomment these commands to start fresh. Use with caution in production!
// 
// DROP CONSTRAINT constraint_name IF EXISTS;
// DROP INDEX index_name IF EXISTS;
// 
// ============================================================================

// ============================================================================
// SECTION 2: UNIQUENESS CONSTRAINTS
// ============================================================================
// Ensures that resource identifiers are unique within each node label.
// These constraints also automatically create an index on the constrained property.
// 
// Rationale:
// - Prevents duplicate resources in the graph
// - Ensures data integrity when ingesting from GCP APIs
// - Automatically creates backing indexes for fast lookups
// - Essential for MERGE operations during data synchronization
// ============================================================================

// --- Organizational Resources ---

CREATE CONSTRAINT unique_organization_id IF NOT EXISTS
FOR (o:Organization)
REQUIRE o.id IS UNIQUE;

CREATE CONSTRAINT unique_folder_id IF NOT EXISTS
FOR (f:Folder)
REQUIRE f.id IS UNIQUE;

CREATE CONSTRAINT unique_project_id IF NOT EXISTS
FOR (p:Project)
REQUIRE p.id IS UNIQUE;

// --- Compute Resources ---

CREATE CONSTRAINT unique_virtualmachine_id IF NOT EXISTS
FOR (vm:VirtualMachine)
REQUIRE vm.id IS UNIQUE;

CREATE CONSTRAINT unique_instancetemplate_id IF NOT EXISTS
FOR (it:InstanceTemplate)
REQUIRE it.id IS UNIQUE;

CREATE CONSTRAINT unique_managedinstancegroup_id IF NOT EXISTS
FOR (mig:ManagedInstanceGroup)
REQUIRE mig.id IS UNIQUE;

CREATE CONSTRAINT unique_gkenode_id IF NOT EXISTS
FOR (node:GKENode)
REQUIRE node.id IS UNIQUE;

CREATE CONSTRAINT unique_gkecluster_id IF NOT EXISTS
FOR (cluster:GKECluster)
REQUIRE cluster.id IS UNIQUE;

CREATE CONSTRAINT unique_cloudfunction_id IF NOT EXISTS
FOR (fn:CloudFunction)
REQUIRE fn.id IS UNIQUE;

CREATE CONSTRAINT unique_cloudrunservice_id IF NOT EXISTS
FOR (svc:CloudRunService)
REQUIRE svc.id IS UNIQUE;

CREATE CONSTRAINT unique_cloudrunrevision_id IF NOT EXISTS
FOR (rev:CloudRunRevision)
REQUIRE rev.id IS UNIQUE;

CREATE CONSTRAINT unique_appengineservice_id IF NOT EXISTS
FOR (svc:AppEngineService)
REQUIRE svc.id IS UNIQUE;

// --- Networking Resources ---

CREATE CONSTRAINT unique_vpc_id IF NOT EXISTS
FOR (vpc:VPC)
REQUIRE vpc.id IS UNIQUE;

CREATE CONSTRAINT unique_subnet_id IF NOT EXISTS
FOR (subnet:Subnet)
REQUIRE subnet.id IS UNIQUE;

CREATE CONSTRAINT unique_firewall_id IF NOT EXISTS
FOR (fw:Firewall)
REQUIRE fw.id IS UNIQUE;

CREATE CONSTRAINT unique_route_id IF NOT EXISTS
FOR (route:Route)
REQUIRE route.id IS UNIQUE;

CREATE CONSTRAINT unique_loadbalancer_id IF NOT EXISTS
FOR (lb:LoadBalancer)
REQUIRE lb.id IS UNIQUE;

CREATE CONSTRAINT unique_backendservice_id IF NOT EXISTS
FOR (bs:BackendService)
REQUIRE bs.id IS UNIQUE;

CREATE CONSTRAINT unique_forwardingrule_id IF NOT EXISTS
FOR (fr:ForwardingRule)
REQUIRE fr.id IS UNIQUE;

CREATE CONSTRAINT unique_targetproxy_id IF NOT EXISTS
FOR (tp:TargetProxy)
REQUIRE tp.id IS UNIQUE;

CREATE CONSTRAINT unique_urlmap_id IF NOT EXISTS
FOR (um:URLMap)
REQUIRE um.id IS UNIQUE;

CREATE CONSTRAINT unique_networkinterface_id IF NOT EXISTS
FOR (nic:NetworkInterface)
REQUIRE nic.id IS UNIQUE;

CREATE CONSTRAINT unique_ipaddress_id IF NOT EXISTS
FOR (ip:IPAddress)
REQUIRE ip.id IS UNIQUE;

CREATE CONSTRAINT unique_vpcpeering_id IF NOT EXISTS
FOR (peer:VPCPeering)
REQUIRE peer.id IS UNIQUE;

CREATE CONSTRAINT unique_cloudnat_id IF NOT EXISTS
FOR (nat:CloudNAT)
REQUIRE nat.id IS UNIQUE;

CREATE CONSTRAINT unique_cloudrouter_id IF NOT EXISTS
FOR (router:CloudRouter)
REQUIRE router.id IS UNIQUE;

CREATE CONSTRAINT unique_vpngateway_id IF NOT EXISTS
FOR (vpn:VPNGateway)
REQUIRE vpn.id IS UNIQUE;

CREATE CONSTRAINT unique_vpntunnel_id IF NOT EXISTS
FOR (tunnel:VPNTunnel)
REQUIRE tunnel.id IS UNIQUE;

CREATE CONSTRAINT unique_interconnect_id IF NOT EXISTS
FOR (ic:Interconnect)
REQUIRE ic.id IS UNIQUE;

// --- Storage Resources ---

CREATE CONSTRAINT unique_persistentdisk_id IF NOT EXISTS
FOR (disk:PersistentDisk)
REQUIRE disk.id IS UNIQUE;

CREATE CONSTRAINT unique_snapshot_id IF NOT EXISTS
FOR (snap:Snapshot)
REQUIRE snap.id IS UNIQUE;

CREATE CONSTRAINT unique_image_id IF NOT EXISTS
FOR (img:Image)
REQUIRE img.id IS UNIQUE;

CREATE CONSTRAINT unique_bucket_id IF NOT EXISTS
FOR (bucket:Bucket)
REQUIRE bucket.id IS UNIQUE;

CREATE CONSTRAINT unique_filestore_id IF NOT EXISTS
FOR (fs:Filestore)
REQUIRE fs.id IS UNIQUE;

// --- Database Resources ---

CREATE CONSTRAINT unique_cloudsqlinstance_id IF NOT EXISTS
FOR (sql:CloudSQLInstance)
REQUIRE sql.id IS UNIQUE;

CREATE CONSTRAINT unique_cloudsqldatabase_id IF NOT EXISTS
FOR (db:CloudSQLDatabase)
REQUIRE db.id IS UNIQUE;

CREATE CONSTRAINT unique_spanner_id IF NOT EXISTS
FOR (spanner:Spanner)
REQUIRE spanner.id IS UNIQUE;

CREATE CONSTRAINT unique_bigtable_id IF NOT EXISTS
FOR (bt:Bigtable)
REQUIRE bt.id IS UNIQUE;

CREATE CONSTRAINT unique_firestore_id IF NOT EXISTS
FOR (firestore:Firestore)
REQUIRE firestore.id IS UNIQUE;

CREATE CONSTRAINT unique_memorystore_id IF NOT EXISTS
FOR (redis:Memorystore)
REQUIRE redis.id IS UNIQUE;

// --- IAM & Security Resources ---

CREATE CONSTRAINT unique_serviceaccount_id IF NOT EXISTS
FOR (sa:ServiceAccount)
REQUIRE sa.id IS UNIQUE;

CREATE CONSTRAINT unique_iampolicy_id IF NOT EXISTS
FOR (policy:IAMPolicy)
REQUIRE policy.id IS UNIQUE;

CREATE CONSTRAINT unique_kmskeyring_id IF NOT EXISTS
FOR (keyring:KMSKeyRing)
REQUIRE keyring.id IS UNIQUE;

CREATE CONSTRAINT unique_kmskey_id IF NOT EXISTS
FOR (key:KMSKey)
REQUIRE key.id IS UNIQUE;

CREATE CONSTRAINT unique_secret_id IF NOT EXISTS
FOR (secret:Secret)
REQUIRE secret.id IS UNIQUE;

// --- Application Services ---

CREATE CONSTRAINT unique_pubsubtopic_id IF NOT EXISTS
FOR (topic:PubSubTopic)
REQUIRE topic.id IS UNIQUE;

CREATE CONSTRAINT unique_pubsubsubscription_id IF NOT EXISTS
FOR (sub:PubSubSubscription)
REQUIRE sub.id IS UNIQUE;

CREATE CONSTRAINT unique_cloudschedulerjob_id IF NOT EXISTS
FOR (job:CloudSchedulerJob)
REQUIRE job.id IS UNIQUE;

CREATE CONSTRAINT unique_cloudtask_id IF NOT EXISTS
FOR (task:CloudTask)
REQUIRE task.id IS UNIQUE;

// --- Monitoring Resources ---

CREATE CONSTRAINT unique_logentry_id IF NOT EXISTS
FOR (log:LogEntry)
REQUIRE log.id IS UNIQUE;

CREATE CONSTRAINT unique_metric_id IF NOT EXISTS
FOR (metric:Metric)
REQUIRE metric.id IS UNIQUE;

CREATE CONSTRAINT unique_alert_id IF NOT EXISTS
FOR (alert:Alert)
REQUIRE alert.id IS UNIQUE;

CREATE CONSTRAINT unique_trace_id IF NOT EXISTS
FOR (trace:Trace)
REQUIRE trace.id IS UNIQUE;

// ============================================================================
// SECTION 3: EXISTENCE CONSTRAINTS (NODE REQUIRED PROPERTIES)
// ============================================================================
// Ensures that critical properties exist on nodes when they are created.
// These constraints enforce data completeness and prevent null values
// for essential fields.
// 
// Rationale:
// - Guarantees core properties are always present
// - Prevents incomplete resource records
// - Ensures graph integrity for critical operations
// - Supports reliable querying and traversal
// ============================================================================

// --- Project Property Existence ---
// Every resource must belong to a project for proper organization

CREATE CONSTRAINT require_vm_project IF NOT EXISTS
FOR (vm:VirtualMachine)
REQUIRE vm.project_id IS NOT NULL;

CREATE CONSTRAINT require_vpc_project IF NOT EXISTS
FOR (vpc:VPC)
REQUIRE vpc.project_id IS NOT NULL;

CREATE CONSTRAINT require_bucket_project IF NOT EXISTS
FOR (bucket:Bucket)
REQUIRE bucket.project_id IS NOT NULL;

CREATE CONSTRAINT require_cloudsql_project IF NOT EXISTS
FOR (sql:CloudSQLInstance)
REQUIRE sql.project_id IS NOT NULL;

CREATE CONSTRAINT require_gkecluster_project IF NOT EXISTS
FOR (cluster:GKECluster)
REQUIRE cluster.project_id IS NOT NULL;

CREATE CONSTRAINT require_cloudfunction_project IF NOT EXISTS
FOR (fn:CloudFunction)
REQUIRE fn.project_id IS NOT NULL;

CREATE CONSTRAINT require_cloudrun_project IF NOT EXISTS
FOR (svc:CloudRunService)
REQUIRE svc.project_id IS NOT NULL;

// --- Name Property Existence ---
// Resources must have human-readable names

CREATE CONSTRAINT require_vm_name IF NOT EXISTS
FOR (vm:VirtualMachine)
REQUIRE vm.name IS NOT NULL;

CREATE CONSTRAINT require_vpc_name IF NOT EXISTS
FOR (vpc:VPC)
REQUIRE vpc.name IS NOT NULL;

CREATE CONSTRAINT require_subnet_name IF NOT EXISTS
FOR (subnet:Subnet)
REQUIRE subnet.name IS NOT NULL;

CREATE CONSTRAINT require_bucket_name IF NOT EXISTS
FOR (bucket:Bucket)
REQUIRE bucket.name IS NOT NULL;

// --- Status Property Existence ---
// Resources must have a status for lifecycle management

CREATE CONSTRAINT require_vm_status IF NOT EXISTS
FOR (vm:VirtualMachine)
REQUIRE vm.status IS NOT NULL;

CREATE CONSTRAINT require_gkecluster_status IF NOT EXISTS
FOR (cluster:GKECluster)
REQUIRE cluster.status IS NOT NULL;

CREATE CONSTRAINT require_cloudsql_status IF NOT EXISTS
FOR (sql:CloudSQLInstance)
REQUIRE sql.status IS NOT NULL;

// --- Temporal Property Existence ---
// Track resource creation time for audit and analysis

CREATE CONSTRAINT require_vm_created IF NOT EXISTS
FOR (vm:VirtualMachine)
REQUIRE vm.created_at IS NOT NULL;

CREATE CONSTRAINT require_project_created IF NOT EXISTS
FOR (p:Project)
REQUIRE p.created_at IS NOT NULL;

// ============================================================================
// SECTION 4: SINGLE-PROPERTY INDEXES
// ============================================================================
// Creates indexes on frequently queried individual properties to improve
// query performance. These indexes are separate from uniqueness constraints.
// 
// Rationale:
// - Accelerates filtering queries (WHERE clauses)
// - Improves sorting operations (ORDER BY)
// - Optimizes range queries (temporal, numeric)
// - Reduces full node scans
// ============================================================================

// --- Project-based Queries ---
// Most queries filter by project to scope operations

CREATE INDEX idx_vm_project IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.project_id);

CREATE INDEX idx_subnet_project IF NOT EXISTS
FOR (subnet:Subnet)
ON (subnet.project_id);

CREATE INDEX idx_disk_project IF NOT EXISTS
FOR (disk:PersistentDisk)
ON (disk.project_id);

CREATE INDEX idx_firewall_project IF NOT EXISTS
FOR (fw:Firewall)
ON (fw.project_id);

CREATE INDEX idx_loadbalancer_project IF NOT EXISTS
FOR (lb:LoadBalancer)
ON (lb.project_id);

CREATE INDEX idx_topic_project IF NOT EXISTS
FOR (topic:PubSubTopic)
ON (topic.project_id);

CREATE INDEX idx_subscription_project IF NOT EXISTS
FOR (sub:PubSubSubscription)
ON (sub.project_id);

// --- Region/Zone-based Queries ---
// Location filtering is common for resource management

CREATE INDEX idx_vm_zone IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.zone);

CREATE INDEX idx_vm_region IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.region);

CREATE INDEX idx_disk_zone IF NOT EXISTS
FOR (disk:PersistentDisk)
ON (disk.zone);

CREATE INDEX idx_gkecluster_zone IF NOT EXISTS
FOR (cluster:GKECluster)
ON (cluster.zone);

CREATE INDEX idx_cloudsql_region IF NOT EXISTS
FOR (sql:CloudSQLInstance)
ON (sql.region);

CREATE INDEX idx_bucket_region IF NOT EXISTS
FOR (bucket:Bucket)
ON (bucket.region);

// --- Status-based Queries ---
// Filter resources by operational status

CREATE INDEX idx_vm_status IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.status);

CREATE INDEX idx_gkecluster_status IF NOT EXISTS
FOR (cluster:GKECluster)
ON (cluster.status);

CREATE INDEX idx_cloudsql_status IF NOT EXISTS
FOR (sql:CloudSQLInstance)
ON (sql.status);

CREATE INDEX idx_cloudrun_status IF NOT EXISTS
FOR (svc:CloudRunService)
ON (svc.status);

CREATE INDEX idx_loadbalancer_status IF NOT EXISTS
FOR (lb:LoadBalancer)
ON (lb.status);

// --- Name-based Lookups ---
// Enable fast name-based searches

CREATE INDEX idx_vm_name IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.name);

CREATE INDEX idx_vpc_name IF NOT EXISTS
FOR (vpc:VPC)
ON (vpc.name);

CREATE INDEX idx_subnet_name IF NOT EXISTS
FOR (subnet:Subnet)
ON (subnet.name);

CREATE INDEX idx_bucket_name IF NOT EXISTS
FOR (bucket:Bucket)
ON (bucket.name);

CREATE INDEX idx_serviceaccount_email IF NOT EXISTS
FOR (sa:ServiceAccount)
ON (sa.email);

// --- Temporal Queries ---
// Optimize time-based filtering and sorting

CREATE INDEX idx_vm_created IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.created_at);

CREATE INDEX idx_vm_updated IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.updated_at);

CREATE INDEX idx_logentry_timestamp IF NOT EXISTS
FOR (log:LogEntry)
ON (log.timestamp);

CREATE INDEX idx_metric_timestamp IF NOT EXISTS
FOR (metric:Metric)
ON (metric.timestamp);

CREATE INDEX idx_alert_timestamp IF NOT EXISTS
FOR (alert:Alert)
ON (alert.timestamp);

CREATE INDEX idx_trace_timestamp IF NOT EXISTS
FOR (trace:Trace)
ON (trace.timestamp);

// --- Resource-Specific Properties ---

CREATE INDEX idx_vm_machine_type IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.machine_type);

CREATE INDEX idx_disk_size IF NOT EXISTS
FOR (disk:PersistentDisk)
ON (disk.size_gb);

CREATE INDEX idx_disk_type IF NOT EXISTS
FOR (disk:PersistentDisk)
ON (disk.disk_type);

CREATE INDEX idx_ip_address IF NOT EXISTS
FOR (ip:IPAddress)
ON (ip.address);

CREATE INDEX idx_firewall_priority IF NOT EXISTS
FOR (fw:Firewall)
ON (fw.priority);

// ============================================================================
// SECTION 5: COMPOSITE INDEXES
// ============================================================================
// Creates multi-property indexes to optimize common query patterns that
// filter on multiple properties simultaneously.
// 
// Rationale:
// - Accelerates queries with multiple WHERE conditions
// - Optimizes common filtering patterns (project + region, project + status)
// - Reduces query execution time for complex filters
// - Supports efficient pagination and sorting
// ============================================================================

// --- Project + Region Composite ---
// Common pattern: "Find all resources in project X in region Y"

CREATE INDEX idx_vm_project_region IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.project_id, vm.region);

CREATE INDEX idx_cloudsql_project_region IF NOT EXISTS
FOR (sql:CloudSQLInstance)
ON (sql.project_id, sql.region);

CREATE INDEX idx_gkecluster_project_region IF NOT EXISTS
FOR (cluster:GKECluster)
ON (cluster.project_id, cluster.region);

CREATE INDEX idx_bucket_project_region IF NOT EXISTS
FOR (bucket:Bucket)
ON (bucket.project_id, bucket.region);

// --- Project + Zone Composite ---
// Common pattern: "Find all resources in project X in zone Y"

CREATE INDEX idx_vm_project_zone IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.project_id, vm.zone);

CREATE INDEX idx_disk_project_zone IF NOT EXISTS
FOR (disk:PersistentDisk)
ON (disk.project_id, disk.zone);

CREATE INDEX idx_gkecluster_project_zone IF NOT EXISTS
FOR (cluster:GKECluster)
ON (cluster.project_id, cluster.zone);

// --- Project + Status Composite ---
// Common pattern: "Find all resources in project X with status Y"

CREATE INDEX idx_vm_project_status IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.project_id, vm.status);

CREATE INDEX idx_gkecluster_project_status IF NOT EXISTS
FOR (cluster:GKECluster)
ON (cluster.project_id, cluster.status);

CREATE INDEX idx_cloudsql_project_status IF NOT EXISTS
FOR (sql:CloudSQLInstance)
ON (sql.project_id, sql.status);

CREATE INDEX idx_cloudrun_project_status IF NOT EXISTS
FOR (svc:CloudRunService)
ON (svc.project_id, svc.status);

// --- Region + Status Composite ---
// Common pattern: "Find all resources in region X with status Y"

CREATE INDEX idx_vm_region_status IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.region, vm.status);

CREATE INDEX idx_cloudsql_region_status IF NOT EXISTS
FOR (sql:CloudSQLInstance)
ON (sql.region, sql.status);

// --- Project + Created Time Composite ---
// Common pattern: "Find recent resources in project X"

CREATE INDEX idx_vm_project_created IF NOT EXISTS
FOR (vm:VirtualMachine)
ON (vm.project_id, vm.created_at);

CREATE INDEX idx_bucket_project_created IF NOT EXISTS
FOR (bucket:Bucket)
ON (bucket.project_id, bucket.created_at);

// --- Temporal Range Composite ---
// Common pattern: Time-series analysis with resource type filtering

CREATE INDEX idx_logentry_timestamp_severity IF NOT EXISTS
FOR (log:LogEntry)
ON (log.timestamp, log.severity);

CREATE INDEX idx_metric_timestamp_value IF NOT EXISTS
FOR (metric:Metric)
ON (metric.timestamp, metric.value);

// ============================================================================
// SECTION 6: FULL-TEXT INDEXES
// ============================================================================
// Creates full-text search indexes for text-heavy properties to enable
// efficient text search capabilities across the graph.
// 
// Rationale:
// - Enables natural language search across resource descriptions
// - Supports log message and error text searching
// - Improves user experience for discovery and troubleshooting
// - Allows fuzzy matching and relevance scoring
// ============================================================================

// --- Resource Names and Descriptions ---
// Enable full-text search across resource metadata

CREATE FULLTEXT INDEX fulltext_vm_search IF NOT EXISTS
FOR (vm:VirtualMachine)
ON EACH [vm.name, vm.description, vm.labels];

CREATE FULLTEXT INDEX fulltext_bucket_search IF NOT EXISTS
FOR (bucket:Bucket)
ON EACH [bucket.name, bucket.description, bucket.labels];

CREATE FULLTEXT INDEX fulltext_vpc_search IF NOT EXISTS
FOR (vpc:VPC)
ON EACH [vpc.name, vpc.description];

CREATE FULLTEXT INDEX fulltext_subnet_search IF NOT EXISTS
FOR (subnet:Subnet)
ON EACH [subnet.name, subnet.description];

CREATE FULLTEXT INDEX fulltext_gkecluster_search IF NOT EXISTS
FOR (cluster:GKECluster)
ON EACH [cluster.name, cluster.description, cluster.labels];

CREATE FULLTEXT INDEX fulltext_cloudfunction_search IF NOT EXISTS
FOR (fn:CloudFunction)
ON EACH [fn.name, fn.description, fn.labels];

CREATE FULLTEXT INDEX fulltext_cloudrun_search IF NOT EXISTS
FOR (svc:CloudRunService)
ON EACH [svc.name, svc.description, svc.labels];

// --- Logs and Messages ---
// Enable full-text search for troubleshooting and analysis

CREATE FULLTEXT INDEX fulltext_logentry_search IF NOT EXISTS
FOR (log:LogEntry)
ON EACH [log.message, log.labels];

CREATE FULLTEXT INDEX fulltext_alert_search IF NOT EXISTS
FOR (alert:Alert)
ON EACH [alert.message, alert.description];

// --- IAM Resources ---
// Enable search across service accounts and policies

CREATE FULLTEXT INDEX fulltext_serviceaccount_search IF NOT EXISTS
FOR (sa:ServiceAccount)
ON EACH [sa.email, sa.display_name, sa.description];

CREATE FULLTEXT INDEX fulltext_iampolicy_search IF NOT EXISTS
FOR (policy:IAMPolicy)
ON EACH [policy.role, policy.description];

// ============================================================================
// SECTION 7: RELATIONSHIP INDEXES
// ============================================================================
// Creates indexes on relationship properties to optimize graph traversals
// and relationship-based queries.
// 
// Rationale:
// - Accelerates path finding and traversal operations
// - Optimizes queries filtering on relationship properties
// - Improves performance of temporal relationship queries
// - Supports weighted graph algorithms
// ============================================================================

// --- Temporal Relationship Queries ---
// Track when relationships were created/updated

CREATE INDEX idx_rel_created IF NOT EXISTS
FOR ()-[r:CONTAINS]-()
ON (r.created_at);

CREATE INDEX idx_rel_updated IF NOT EXISTS
FOR ()-[r:CONTAINS]-()
ON (r.updated_at);

CREATE INDEX idx_routes_created IF NOT EXISTS
FOR ()-[r:ROUTES_TO]-()
ON (r.created_at);

CREATE INDEX idx_depends_created IF NOT EXISTS
FOR ()-[r:DEPENDS_ON]-()
ON (r.created_at);

// --- Network Relationship Properties ---
// Optimize network topology queries

CREATE INDEX idx_routes_priority IF NOT EXISTS
FOR ()-[r:ROUTES_TO]-()
ON (r.priority);

CREATE INDEX idx_allows_priority IF NOT EXISTS
FOR ()-[r:ALLOWS_TRAFFIC]-()
ON (r.priority);

CREATE INDEX idx_balances_weight IF NOT EXISTS
FOR ()-[r:BALANCES_TO]-()
ON (r.weight);

// --- Cost and Performance Metrics ---
// Support cost analysis and optimization queries

CREATE INDEX idx_routes_cost IF NOT EXISTS
FOR ()-[r:ROUTES_TO]-()
ON (r.cost);

CREATE INDEX idx_allows_bandwidth IF NOT EXISTS
FOR ()-[r:ALLOWS_TRAFFIC]-()
ON (r.bandwidth_mbps);

// ============================================================================
// SECTION 8: CONSTRAINT AND INDEX VERIFICATION
// ============================================================================
// Queries to verify that constraints and indexes have been created correctly
// and to assess their effectiveness.
// ============================================================================

// --- List All Constraints ---
// SHOW CONSTRAINTS;

// --- List All Indexes ---
// SHOW INDEXES;

// --- Check Constraint Details ---
// SHOW CONSTRAINT constraint_name;

// --- Check Index Details ---
// SHOW INDEX index_name;

// --- Verify Index Usage (After Running Queries) ---
// PROFILE your_query_here;
// Look for "NodeIndexSeek" or "NodeIndexScan" in the execution plan

// --- Check Index Population Status ---
// SHOW INDEXES YIELD name, state, populationPercent;

// ============================================================================
// SECTION 9: TESTING SCRIPTS
// ============================================================================
// Sample queries to test constraint enforcement and index effectiveness
// ============================================================================

// --- Test Uniqueness Constraint ---
// Should succeed (first insert)
// CREATE (vm:VirtualMachine {id: 'test-vm-001', name: 'Test VM 1', project_id: 'test-project', status: 'RUNNING', created_at: datetime()});

// Should fail with constraint violation
// CREATE (vm:VirtualMachine {id: 'test-vm-001', name: 'Test VM 2', project_id: 'test-project', status: 'RUNNING', created_at: datetime()});

// --- Test Existence Constraint ---
// Should fail (missing required property project_id)
// CREATE (vm:VirtualMachine {id: 'test-vm-002', name: 'Test VM 2', status: 'RUNNING'});

// --- Test Index Performance ---
// Before indexes: Profile this query and note execution time
// MATCH (vm:VirtualMachine {project_id: 'my-project-id', region: 'us-central1'})
// WHERE vm.status = 'RUNNING'
// RETURN vm.name, vm.zone;

// After indexes: Run PROFILE again to compare and verify "NodeIndexSeek"
// PROFILE
// MATCH (vm:VirtualMachine {project_id: 'my-project-id', region: 'us-central1'})
// WHERE vm.status = 'RUNNING'
// RETURN vm.name, vm.zone;

// --- Test Full-Text Search ---
// Search for VMs with "web" in name or description
// CALL db.index.fulltext.queryNodes('fulltext_vm_search', 'web*')
// YIELD node, score
// RETURN node.name, node.description, score
// ORDER BY score DESC
// LIMIT 10;

// --- Test Composite Index ---
// Verify project + region + status composite index is used
// PROFILE
// MATCH (vm:VirtualMachine)
// WHERE vm.project_id = 'my-project'
//   AND vm.region = 'us-central1'
//   AND vm.status = 'RUNNING'
// RETURN vm.name, vm.zone
// ORDER BY vm.created_at DESC
// LIMIT 20;

// ============================================================================
// SECTION 10: MAINTENANCE SCRIPTS
// ============================================================================
// Commands for ongoing constraint and index management
// ============================================================================

// --- Drop a Specific Constraint ---
// DROP CONSTRAINT constraint_name IF EXISTS;

// --- Drop a Specific Index ---
// DROP INDEX index_name IF EXISTS;

// --- Rebuild Index (if needed) ---
// First drop the index, then recreate it
// DROP INDEX index_name IF EXISTS;
// CREATE INDEX index_name FOR (n:Label) ON (n.property);

// --- Check Index Statistics ---
// CALL db.index.fulltext.listAvailableAnalyzers();
// CALL db.indexes();

// --- Monitor Index Performance ---
// CALL db.stats.retrieve('GRAPH COUNTS');

// ============================================================================
// IMPLEMENTATION NOTES
// ============================================================================
// 
// 1. Execution Order:
//    - Run this script in a Neo4j browser or via cypher-shell
//    - Execute sections sequentially for best results
//    - Monitor progress with SHOW CONSTRAINTS and SHOW INDEXES
// 
// 2. Performance Considerations:
//    - Creating constraints/indexes on large databases may take time
//    - Consider creating constraints first on smaller datasets
//    - Monitor index population progress with SHOW INDEXES
//    - Use PROFILE to verify index usage in production queries
// 
// 3. Version Compatibility:
//    - This script is designed for Neo4j 5.x+
//    - For Neo4j 4.x, adjust constraint syntax (remove IF NOT EXISTS)
//    - Full-text indexes may require different syntax in earlier versions
// 
// 4. Production Deployment:
//    - Test in development environment first
//    - Schedule constraint/index creation during low-traffic periods
//    - Monitor database performance during and after creation
//    - Document any custom modifications for team reference
// 
// 5. Maintenance:
//    - Regularly review index usage with query profiling
//    - Drop unused indexes to reduce storage overhead
//    - Update indexes when query patterns change
//    - Monitor constraint violations in application logs
// 
// 6. Integration with Data Ingestion:
//    - These constraints will be enforced during MERGE operations
//    - Ensure GCP API ingestion pipeline handles constraint violations
//    - Use MERGE instead of CREATE to respect uniqueness constraints
//    - Implement retry logic for transient constraint violations
// 
// 7. Expected Benefits:
//    - 10-100x query performance improvement for indexed properties
//    - Automatic data integrity enforcement
//    - Reduced application-side validation logic
//    - Improved graph algorithm performance
//    - Better user experience for search and discovery
// 
// ============================================================================
// END OF CONSTRAINTS AND INDEXES SCRIPT
// ============================================================================

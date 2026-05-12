# Neo4j Relationship Schema Definition for GCP Resources

## Document Purpose
This document defines all relationship types, properties, directionality, and cardinality constraints for connecting GCP resources in the digital twin. It complements the node schema by mapping the dependencies and connections between resources.

---

## 1. RELATIONSHIP DESIGN PRINCIPLES

### 1.1 Naming Conventions

**Relationship Types:**
- Use UPPER_SNAKE_CASE for all relationship types (e.g., `CONTAINS`, `DEPENDS_ON`)
- Use active verbs that clearly describe the relationship
- Be specific and descriptive (e.g., `ROUTES_TO` instead of `CONNECTS`)
- Direction should read naturally: `(Source)-[RELATIONSHIP]->(Target)`

**Relationship Properties:**
- Use camelCase for property names (e.g., `createdAt`, `weight`)
- Include temporal tracking for relationship changes
- Capture metadata specific to the connection

### 1.2 Standard Relationship Properties

All relationships SHOULD include these standard properties where applicable:

```cypher
// Temporal Tracking
createdAt: DateTime           // Relationship creation timestamp
updatedAt: DateTime           // Last update timestamp
deletedAt: DateTime           // Soft deletion timestamp (null if active)

// Metadata
weight: Float                 // Relationship strength/priority (optional)
metadata: Map<String, String> // Additional relationship metadata (optional)
```

### 1.3 Directionality Principles

- **Parent → Child**: Use for hierarchical containment (e.g., `CONTAINS`)
- **Source → Target**: Use for network traffic flow (e.g., `ROUTES_TO`, `FORWARDS_TO`)
- **Dependent → Dependency**: Use for resource dependencies (e.g., `DEPENDS_ON`, `USES`)
- **Bidirectional**: Represent as two separate relationships when semantics differ in each direction

### 1.4 Cardinality Notation

- **1:1** - One-to-one relationship
- **1:N** - One-to-many relationship
- **N:1** - Many-to-one relationship
- **N:M** - Many-to-many relationship

---

## 2. RESOURCE HIERARCHY RELATIONSHIPS

### 2.1 CONTAINS

**Purpose:** Represents hierarchical containment of resources.

**Direction:** Parent → Child

**Cardinality:** 1:N (One parent contains many children)

**Source → Target Patterns:**
- `Organization` → `Folder`
- `Organization` → `Project`
- `Folder` → `Folder` (nested folders)
- `Folder` → `Project`
- `VPCNetwork` → `Subnet`
- `InstanceGroup` → `ComputeInstance`
- `GKECluster` → `GKENodePool`
- `StorageBucket` → `StorageObject`
- `SpannerInstance` → `SpannerDatabase`
- `BigtableInstance` → `BigtableCluster`
- `KMSKeyRing` → `CryptoKey`

**Properties:**
```cypher
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// VPC contains Subnet
MATCH (vpc:VPCNetwork {gcpId: "net-123"})
MATCH (subnet:Subnet {gcpId: "subnet-456"})
CREATE (vpc)-[:CONTAINS {
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(subnet)
```

**Inverse Relationship:** `PART_OF` (Child → Parent)

---

### 2.2 PART_OF

**Purpose:** Reverse of CONTAINS; indicates child belongs to parent.

**Direction:** Child → Parent

**Cardinality:** N:1 (Many children belong to one parent)

**Source → Target Patterns:**
- `Folder` → `Organization`
- `Folder` → `Folder` (nested folders)
- `Project` → `Organization`
- `Project` → `Folder`
- `Subnet` → `VPCNetwork`
- `ComputeInstance` → `InstanceGroup`
- `GKENodePool` → `GKECluster`
- `StorageObject` → `StorageBucket`
- `SpannerDatabase` → `SpannerInstance`
- `BigtableCluster` → `BigtableInstance`
- `CryptoKey` → `KMSKeyRing`

**Properties:**
```cypher
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Subnet is part of VPC
MATCH (subnet:Subnet {gcpId: "subnet-456"})
MATCH (vpc:VPCNetwork {gcpId: "net-123"})
CREATE (subnet)-[:PART_OF {
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(vpc)
```

---

## 3. NETWORK CONNECTIVITY RELATIONSHIPS

### 3.1 ATTACHED_TO

**Purpose:** Indicates a resource is attached to a network component.

**Direction:** Resource → Network Component

**Cardinality:** N:M (Many resources can attach to many network components)

**Source → Target Patterns:**
- `ComputeInstance` → `Subnet`
- `ComputeInstance` → `VPCNetwork` (via network interface)
- `CloudFunction` → `VPCNetwork` (via VPC connector)
- `CloudRunService` → `VPCNetwork` (via VPC access)
- `CloudSQLInstance` → `VPCNetwork` (private IP)
- `GKECluster` → `VPCNetwork`
- `GKECluster` → `Subnet`

**Properties:**
```cypher
// Network Interface Details
interfaceIndex: Integer       // Interface number (0, 1, 2...)
networkIP: String            // Internal IP address assigned
accessConfigs: List<Map>     // External IP configurations
aliasIpRanges: List<Map>     // Alias IP ranges
nicType: String              // VIRTIO_NET | GVNIC
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Instance attached to Subnet
MATCH (vm:ComputeInstance {gcpId: "vm-789"})
MATCH (subnet:Subnet {gcpId: "subnet-456"})
CREATE (vm)-[:ATTACHED_TO {
  interfaceIndex: 0,
  networkIP: "10.128.0.2",
  accessConfigs: [{
    type: "ONE_TO_ONE_NAT",
    natIP: "35.192.1.1",
    name: "External NAT"
  }],
  nicType: "VIRTIO_NET",
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(subnet)
```

---

### 3.2 ROUTES_TO

**Purpose:** Defines routing paths between network resources.

**Direction:** Source → Destination

**Cardinality:** 1:N (One route can target multiple destinations)

**Source → Target Patterns:**
- `Route` → `VPCNetwork`
- `Route` → `ComputeInstance` (next hop instance)
- `Route` → `VPNTunnel` (next hop VPN)
- `Subnet` → `Route` (implicit routes)

**Properties:**
```cypher
// Route Configuration
destRange: String            // Destination IP range
priority: Integer            // Route priority
nextHopType: String          // GATEWAY | INSTANCE | IP | VPN_TUNNEL
tags: List<String>           // Instance tags this route applies to
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Route to VPN Tunnel
MATCH (route:Route {gcpId: "route-123"})
MATCH (vpn:VPNTunnel {gcpId: "vpn-456"})
CREATE (route)-[:ROUTES_TO {
  destRange: "192.168.0.0/16",
  priority: 1000,
  nextHopType: "VPN_TUNNEL",
  tags: ["vpn-traffic"],
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(vpn)
```

---

### 3.3 ALLOWS_TRAFFIC

**Purpose:** Firewall rules allowing traffic to/from resources.

**Direction:** FirewallRule → Target Resource/Tag

**Cardinality:** 1:N (One rule affects many resources)

**Source → Target Patterns:**
- `FirewallRule` → `ComputeInstance` (via tags or service accounts)
- `FirewallRule` → `VPCNetwork` (applies to network)

**Properties:**
```cypher
// Traffic Configuration
direction: String            // INGRESS | EGRESS
protocol: String             // TCP | UDP | ICMP | etc.
ports: List<String>          // Port ranges (e.g., ["80", "443", "8000-9000"])
sourceRanges: List<String>   // Source IP ranges (ingress)
destRanges: List<String>     // Destination IP ranges (egress)
priority: Integer            // Rule priority
action: String               // ALLOW | DENY
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Firewall allows traffic to instances with tag
MATCH (fw:FirewallRule {gcpId: "fw-123"})
MATCH (vm:ComputeInstance)
WHERE "web-server" IN vm.tags
CREATE (fw)-[:ALLOWS_TRAFFIC {
  direction: "INGRESS",
  protocol: "TCP",
  ports: ["80", "443"],
  sourceRanges: ["0.0.0.0/0"],
  priority: 1000,
  action: "ALLOW",
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(vm)
```

---

### 3.4 DENIES_TRAFFIC

**Purpose:** Firewall rules denying traffic to/from resources.

**Direction:** FirewallRule → Target Resource/Tag

**Cardinality:** 1:N

**Source → Target Patterns:**
- `FirewallRule` → `ComputeInstance`
- `FirewallRule` → `VPCNetwork`

**Properties:** Same as `ALLOWS_TRAFFIC` with `action: "DENY"`

---

### 3.5 PEERS_WITH

**Purpose:** VPC network peering connections.

**Direction:** Bidirectional (create two relationships)

**Cardinality:** N:M (Networks can peer with multiple networks)

**Source → Target Patterns:**
- `VPCNetwork` → `VPCNetwork`

**Properties:**
```cypher
// Peering Configuration
peeringName: String          // Peering connection name
state: String                // ACTIVE | INACTIVE
importCustomRoutes: Boolean  // Import custom routes
exportCustomRoutes: Boolean  // Export custom routes
importSubnetRoutesWithPublicIp: Boolean
exportSubnetRoutesWithPublicIp: Boolean
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// VPC peering (bidirectional)
MATCH (vpc1:VPCNetwork {gcpId: "net-123"})
MATCH (vpc2:VPCNetwork {gcpId: "net-456"})
CREATE (vpc1)-[:PEERS_WITH {
  peeringName: "vpc1-to-vpc2",
  state: "ACTIVE",
  importCustomRoutes: true,
  exportCustomRoutes: true,
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(vpc2)
CREATE (vpc2)-[:PEERS_WITH {
  peeringName: "vpc2-to-vpc1",
  state: "ACTIVE",
  importCustomRoutes: true,
  exportCustomRoutes: true,
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(vpc1)
```

---

### 3.6 FORWARDS_TO

**Purpose:** Load balancer forwarding to backend services.

**Direction:** Load Balancer → Backend Service/Instance Group

**Cardinality:** 1:N (One LB forwards to many backends)

**Source → Target Patterns:**
- `LoadBalancer` → `BackendService`
- `BackendService` → `InstanceGroup`
- `BackendService` → `ComputeInstance`

**Properties:**
```cypher
// Load Balancing Configuration
balancingMode: String        // RATE | UTILIZATION | CONNECTION
capacityScaler: Float        // Scaling factor (0.0-1.0)
maxRate: Integer             // Max requests per second
maxRatePerInstance: Float    // Max rate per instance
maxUtilization: Float        // Target utilization
weight: Float                // Traffic weight
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Backend service forwards to instance group
MATCH (bs:BackendService {gcpId: "bs-123"})
MATCH (ig:InstanceGroup {gcpId: "ig-456"})
CREATE (bs)-[:FORWARDS_TO {
  balancingMode: "UTILIZATION",
  capacityScaler: 1.0,
  maxUtilization: 0.8,
  weight: 1.0,
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(ig)
```

---

### 3.7 HEALTH_CHECKED_BY

**Purpose:** Resources monitored by health checks.

**Direction:** Resource → Health Check

**Cardinality:** N:M (Many resources can use many health checks)

**Source → Target Patterns:**
- `BackendService` → `HealthCheck`
- `InstanceGroup` → `HealthCheck`

**Properties:**
```cypher
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Backend service uses health check
MATCH (bs:BackendService {gcpId: "bs-123"})
MATCH (hc:HealthCheck {gcpId: "hc-789"})
CREATE (bs)-[:HEALTH_CHECKED_BY {
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(hc)
```

---

### 3.8 RESOLVES_TO

**Purpose:** DNS record resolution.

**Direction:** DNS Record → Resource/IP

**Cardinality:** 1:N (One record can resolve to multiple targets)

**Source → Target Patterns:**
- `DNSRecord` → `ComputeInstance`
- `DNSRecord` → `LoadBalancer`
- `DNSRecord` → `DNSRecord` (CNAME chains)

**Properties:**
```cypher
// Resolution Details
recordType: String           // A | AAAA | CNAME | etc.
ttl: Integer                 // Time to live
rrdatas: List<String>        // Record data
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

---

### 3.9 CONNECTS_THROUGH

**Purpose:** VPN tunnel connections.

**Direction:** VPN Tunnel → VPN Gateway

**Cardinality:** N:1 (Many tunnels connect through one gateway)

**Source → Target Patterns:**
- `VPNTunnel` → `VPNGateway`

**Properties:**
```cypher
// Tunnel Configuration
status: String               // ESTABLISHED | NO_INCOMING_PACKETS | etc.
ikeVersion: Integer          // 1 or 2
peerIp: String               // Peer gateway IP
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

---

## 4. COMPUTE RELATIONSHIPS

### 4.1 USES_TEMPLATE

**Purpose:** Instance group uses an instance template.

**Direction:** Instance Group → Instance Template

**Cardinality:** N:1 (Many groups can use one template)

**Source → Target Patterns:**
- `InstanceGroup` → `InstanceTemplate`

**Properties:**
```cypher
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Managed instance group uses template
MATCH (mig:InstanceGroup {gcpId: "mig-123"})
MATCH (tmpl:InstanceTemplate {gcpId: "tmpl-456"})
CREATE (mig)-[:USES_TEMPLATE {
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(tmpl)
```

---

### 4.2 SCALES

**Purpose:** Autoscaler controls an instance group.

**Direction:** Autoscaler → Instance Group

**Cardinality:** 1:1 (One autoscaler per instance group)

**Source → Target Patterns:**
- `Autoscaler` → `InstanceGroup`

**Properties:**
```cypher
// Autoscaling Configuration
minReplicas: Integer
maxReplicas: Integer
currentReplicas: Integer     // Current instance count
targetCpuUtilization: Float
mode: String                 // ON | OFF | ONLY_UP
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Autoscaler scales instance group
MATCH (as:Autoscaler {gcpId: "as-123"})
MATCH (mig:InstanceGroup {gcpId: "mig-456"})
CREATE (as)-[:SCALES {
  minReplicas: 2,
  maxReplicas: 10,
  currentReplicas: 5,
  targetCpuUtilization: 0.6,
  mode: "ON",
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(mig)
```

---

### 4.3 RUNS_ON

**Purpose:** Workload running on compute resource.

**Direction:** Workload → Compute Resource

**Cardinality:** N:1 (Many workloads on one resource)

**Source → Target Patterns:**
- `CloudFunction` → `ComputeInstance` (underlying VM)
- `CloudRunRevision` → `ComputeInstance` (underlying infrastructure)
- `GKENodePool` → `ComputeInstance` (node VMs)

**Properties:**
```cypher
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

---

### 4.4 HAS_REVISION

**Purpose:** Cloud Run service has multiple revisions.

**Direction:** Cloud Run Service → Cloud Run Revision

**Cardinality:** 1:N (One service has many revisions)

**Source → Target Patterns:**
- `CloudRunService` → `CloudRunRevision`

**Properties:**
```cypher
// Traffic Configuration
trafficPercent: Integer      // Percentage of traffic to this revision
isActive: Boolean            // Currently active revision
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Service has active revision
MATCH (svc:CloudRunService {gcpId: "svc-123"})
MATCH (rev:CloudRunRevision {gcpId: "rev-456"})
CREATE (svc)-[:HAS_REVISION {
  trafficPercent: 100,
  isActive: true,
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(rev)
```

---

## 5. STORAGE RELATIONSHIPS

### 5.1 USES_DISK

**Purpose:** Compute instance using persistent disk.

**Direction:** Instance → Disk

**Cardinality:** N:M (Many instances can use many disks)

**Source → Target Patterns:**
- `ComputeInstance` → `PersistentDisk`

**Properties:**
```cypher
// Disk Attachment Configuration
deviceName: String           // Device name within instance
boot: Boolean                // Boot disk flag
autoDelete: Boolean          // Delete disk when instance deleted
mode: String                 // READ_WRITE | READ_ONLY
interface: String            // SCSI | NVME
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Instance uses boot disk
MATCH (vm:ComputeInstance {gcpId: "vm-789"})
MATCH (disk:PersistentDisk {gcpId: "disk-123"})
CREATE (vm)-[:USES_DISK {
  deviceName: "persistent-disk-0",
  boot: true,
  autoDelete: true,
  mode: "READ_WRITE",
  interface: "SCSI",
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(disk)
```

---

### 5.2 CREATED_FROM

**Purpose:** Resource created from source (snapshot/image).

**Direction:** Resource → Source

**Cardinality:** N:1 (Many resources from one source)

**Source → Target Patterns:**
- `PersistentDisk` → `DiskSnapshot`
- `PersistentDisk` → `ComputeImage`
- `DiskSnapshot` → `PersistentDisk` (snapshot source)

**Properties:**
```cypher
sourceType: String           // SNAPSHOT | IMAGE | DISK
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Disk created from snapshot
MATCH (disk:PersistentDisk {gcpId: "disk-123"})
MATCH (snap:DiskSnapshot {gcpId: "snap-456"})
CREATE (disk)-[:CREATED_FROM {
  sourceType: "SNAPSHOT",
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(snap)
```

---

### 5.3 SNAPSHOT_OF

**Purpose:** Snapshot of a disk.

**Direction:** Snapshot → Disk

**Cardinality:** N:1 (Many snapshots of one disk)

**Source → Target Patterns:**
- `DiskSnapshot` → `PersistentDisk`

**Properties:**
```cypher
snapshotType: String         // STANDARD | ARCHIVE
storageBytes: Integer        // Actual storage used
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

---

### 5.4 STORES_IN

**Purpose:** Resource stores data in storage bucket.

**Direction:** Resource → Storage Bucket

**Cardinality:** N:M (Many resources use many buckets)

**Source → Target Patterns:**
- `CloudFunction` → `StorageBucket` (source code)
- `CloudSQLInstance` → `StorageBucket` (backups)
- `LogSink` → `StorageBucket` (log export)

**Properties:**
```cypher
purpose: String              // SOURCE_CODE | BACKUP | LOGS | DATA
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

---

## 6. DATABASE RELATIONSHIPS

### 6.1 HAS_DATABASE

**Purpose:** Database instance contains databases.

**Direction:** Instance → Database

**Cardinality:** 1:N (One instance has many databases)

**Source → Target Patterns:**
- `CloudSQLInstance` → `CloudSQLDatabase`
- `SpannerInstance` → `SpannerDatabase`

**Properties:**
```cypher
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// CloudSQL instance has database
MATCH (inst:CloudSQLInstance {gcpId: "sql-123"})
MATCH (db:CloudSQLDatabase {name: "app_db"})
CREATE (inst)-[:HAS_DATABASE {
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(db)
```

---

### 6.2 REPLICATES_FROM

**Purpose:** Read replica relationship.

**Direction:** Replica → Primary

**Cardinality:** N:1 (Many replicas from one primary)

**Source → Target Patterns:**
- `CloudSQLInstance` → `CloudSQLInstance` (read replica)

**Properties:**
```cypher
replicationType: String      // SYNCHRONOUS | ASYNCHRONOUS
replicationLag: Integer      // Lag in seconds
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

---

## 7. IAM & SECURITY RELATIONSHIPS

### 7.1 HAS_IAM_POLICY

**Purpose:** Resource has IAM policy attached.

**Direction:** Resource → IAM Policy

**Cardinality:** N:1 (Many resources share one policy, typically 1:1 per resource)

**Source → Target Patterns:**
- `Project` → `IAMPolicy`
- `StorageBucket` → `IAMPolicy`
- `ComputeInstance` → `IAMPolicy`
- `CloudSQLInstance` → `IAMPolicy`
- Any GCP resource → `IAMPolicy`

**Properties:**
```cypher
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Bucket has IAM policy
MATCH (bucket:StorageBucket {gcpId: "bucket-123"})
MATCH (policy:IAMPolicy {resourceId: "bucket-123"})
CREATE (bucket)-[:HAS_IAM_POLICY {
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(policy)
```

---

### 7.2 GRANTS_ROLE

**Purpose:** IAM policy grants role to members.

**Direction:** IAM Policy → IAM Role

**Cardinality:** N:M (Policies grant many roles, roles granted by many policies)

**Source → Target Patterns:**
- `IAMPolicy` → `IAMRole`

**Properties:**
```cypher
// Role Binding Information
members: List<String>        // Members granted this role
  // e.g., ["user:alice@example.com", "serviceAccount:sa@project.iam.gserviceaccount.com"]
condition: Map               // Conditional binding
  // {title: String, expression: String, description: String}
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Policy grants role to members
MATCH (policy:IAMPolicy {resourceId: "bucket-123"})
MATCH (role:IAMRole {name: "roles/storage.objectViewer"})
CREATE (policy)-[:GRANTS_ROLE {
  members: ["user:alice@example.com", "serviceAccount:reader@project.iam.gserviceaccount.com"],
  condition: null,
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(role)
```

---

### 7.3 USES_SERVICE_ACCOUNT

**Purpose:** Resource uses service account for authentication.

**Direction:** Resource → Service Account

**Cardinality:** N:M (Many resources use many service accounts)

**Source → Target Patterns:**
- `ComputeInstance` → `ServiceAccount`
- `CloudFunction` → `ServiceAccount`
- `CloudRunService` → `ServiceAccount`
- `GKENodePool` → `ServiceAccount`
- `CloudSQLInstance` → `ServiceAccount`

**Properties:**
```cypher
scopes: List<String>         // OAuth2 scopes granted
email: String                // Service account email
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Instance uses service account
MATCH (vm:ComputeInstance {gcpId: "vm-789"})
MATCH (sa:ServiceAccount {email: "compute@project.iam.gserviceaccount.com"})
CREATE (vm)-[:USES_SERVICE_ACCOUNT {
  scopes: ["https://www.googleapis.com/auth/cloud-platform"],
  email: "compute@project.iam.gserviceaccount.com",
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(sa)
```

---

### 7.4 ENCRYPTED_BY

**Purpose:** Resource encrypted by KMS key.

**Direction:** Resource → Crypto Key

**Cardinality:** N:1 (Many resources use one key)

**Source → Target Patterns:**
- `PersistentDisk` → `CryptoKey`
- `StorageBucket` → `CryptoKey`
- `DiskSnapshot` → `CryptoKey`
- `CloudSQLInstance` → `CryptoKey`
- `Secret` → `CryptoKey`

**Properties:**
```cypher
keyVersion: String           // Specific key version used
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Disk encrypted by KMS key
MATCH (disk:PersistentDisk {gcpId: "disk-123"})
MATCH (key:CryptoKey {gcpId: "key-789"})
CREATE (disk)-[:ENCRYPTED_BY {
  keyVersion: "1",
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(key)
```

---

### 7.5 HAS_SECRET

**Purpose:** Resource uses secret for configuration.

**Direction:** Resource → Secret

**Cardinality:** N:M (Many resources use many secrets)

**Source → Target Patterns:**
- `CloudFunction` → `Secret`
- `CloudRunService` → `Secret`
- `ComputeInstance` → `Secret`

**Properties:**
```cypher
versionId: String            // Secret version used
mountPath: String            // Path where secret is mounted (optional)
envVarName: String           // Environment variable name (optional)
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

---

### 7.6 HAS_VERSION

**Purpose:** Secret has multiple versions.

**Direction:** Secret → Secret Version

**Cardinality:** 1:N (One secret has many versions)

**Source → Target Patterns:**
- `Secret` → `SecretVersion`

**Properties:**
```cypher
alias: String                // Version alias (e.g., "latest")
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

---

## 8. APPLICATION SERVICE RELATIONSHIPS

### 8.1 PUBLISHES_TO

**Purpose:** Resource publishes messages to Pub/Sub topic.

**Direction:** Resource → Pub/Sub Topic

**Cardinality:** N:M (Many resources publish to many topics)

**Source → Target Patterns:**
- `CloudFunction` → `PubSubTopic`
- `CloudRunService` → `PubSubTopic`
- `ComputeInstance` → `PubSubTopic`
- `CloudScheduler` → `PubSubTopic`
- `LogSink` → `PubSubTopic`

**Properties:**
```cypher
messageFormat: String        // JSON | AVRO | PROTOBUF
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Function publishes to topic
MATCH (fn:CloudFunction {gcpId: "fn-123"})
MATCH (topic:PubSubTopic {gcpId: "topic-456"})
CREATE (fn)-[:PUBLISHES_TO {
  messageFormat: "JSON",
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(topic)
```

---

### 8.2 SUBSCRIBES_TO

**Purpose:** Subscription reads from Pub/Sub topic.

**Direction:** Subscription → Topic

**Cardinality:** N:1 (Many subscriptions per topic)

**Source → Target Patterns:**
- `PubSubSubscription` → `PubSubTopic`

**Properties:**
```cypher
ackDeadlineSeconds: Integer
filter: String               // Message filter
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Subscription reads from topic
MATCH (sub:PubSubSubscription {gcpId: "sub-123"})
MATCH (topic:PubSubTopic {gcpId: "topic-456"})
CREATE (sub)-[:SUBSCRIBES_TO {
  ackDeadlineSeconds: 10,
  filter: "attributes.eventType = \"user.signup\"",
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(topic)
```

---

### 8.3 TRIGGERED_BY

**Purpose:** Resource triggered by an event source.

**Direction:** Resource → Event Source

**Cardinality:** N:M (Many resources triggered by many sources)

**Source → Target Patterns:**
- `CloudFunction` → `PubSubTopic`
- `CloudFunction` → `StorageBucket`
- `CloudFunction` → `FirestoreDatabase`
- `CloudRunService` → `PubSubTopic`
- `TaskQueue` → `PubSubTopic`

**Properties:**
```cypher
triggerType: String          // PUBSUB | STORAGE | FIRESTORE | HTTP | SCHEDULER
eventType: String            // FINALIZE | DELETE | ARCHIVE | etc.
resource: String             // Specific resource path within source
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Function triggered by storage bucket
MATCH (fn:CloudFunction {gcpId: "fn-123"})
MATCH (bucket:StorageBucket {gcpId: "bucket-456"})
CREATE (fn)-[:TRIGGERED_BY {
  triggerType: "STORAGE",
  eventType: "FINALIZE",
  resource: "projects/_/buckets/my-bucket/objects/uploads/*",
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(bucket)
```

---

### 8.4 INVOKES

**Purpose:** Scheduler or workflow invokes a target.

**Direction:** Scheduler/Workflow → Target

**Cardinality:** 1:N (One scheduler invokes one target, but can have N jobs)

**Source → Target Patterns:**
- `SchedulerJob` → `CloudFunction`
- `SchedulerJob` → `CloudRunService`
- `SchedulerJob` → `PubSubTopic`
- `SchedulerJob` → `ComputeInstance` (HTTP endpoint)

**Properties:**
```cypher
schedule: String             // Cron expression
timeZone: String             // IANA timezone
httpMethod: String           // GET | POST | PUT | DELETE
headers: Map<String, String> // HTTP headers
body: String                 // Request body
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Scheduler invokes Cloud Function
MATCH (job:SchedulerJob {gcpId: "job-123"})
MATCH (fn:CloudFunction {gcpId: "fn-456"})
CREATE (job)-[:INVOKES {
  schedule: "0 2 * * *",
  timeZone: "America/New_York",
  httpMethod: "POST",
  headers: {"Content-Type": "application/json"},
  body: "{\"action\": \"daily_cleanup\"}",
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(fn)
```

---

## 9. MONITORING & ALERTING RELATIONSHIPS

### 9.1 MONITORS

**Purpose:** Alert policy monitors a resource or metric.

**Direction:** Alert Policy → Resource

**Cardinality:** N:M (Many policies monitor many resources)

**Source → Target Patterns:**
- `AlertPolicy` → `ComputeInstance`
- `AlertPolicy` → `CloudSQLInstance`
- `AlertPolicy` → `LoadBalancer`
- `AlertPolicy` → `GKECluster`
- `AlertPolicy` → Any monitorable resource

**Properties:**
```cypher
// Monitoring Configuration
metricType: String           // Metric being monitored
threshold: Float             // Alert threshold
comparisonType: String       // COMPARISON_GT | COMPARISON_LT | etc.
duration: String             // Duration before alerting
aggregation: Map             // Aggregation configuration
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Alert policy monitors instance CPU
MATCH (policy:AlertPolicy {gcpId: "policy-123"})
MATCH (vm:ComputeInstance {gcpId: "vm-789"})
CREATE (policy)-[:MONITORS {
  metricType: "compute.googleapis.com/instance/cpu/utilization",
  threshold: 0.9,
  comparisonType: "COMPARISON_GT",
  duration: "300s",
  aggregation: {
    alignmentPeriod: "60s",
    perSeriesAligner: "ALIGN_MEAN"
  },
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(vm)
```

---

### 9.2 NOTIFIES_THROUGH

**Purpose:** Alert policy sends notifications through channels.

**Direction:** Alert Policy → Notification Channel

**Cardinality:** N:M (Many policies use many channels)

**Source → Target Patterns:**
- `AlertPolicy` → `NotificationChannel`

**Properties:**
```cypher
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Alert policy notifies via email
MATCH (policy:AlertPolicy {gcpId: "policy-123"})
MATCH (channel:NotificationChannel {gcpId: "channel-456"})
CREATE (policy)-[:NOTIFIES_THROUGH {
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(channel)
```

---

### 9.3 EXPORTS_LOGS_TO

**Purpose:** Log sink exports logs to destination.

**Direction:** Resource → Log Sink → Destination

**Cardinality:** N:M (Many resources export to many sinks)

**Source → Target Patterns:**
- `Project` → `LogSink`
- `LogSink` → `StorageBucket`
- `LogSink` → `PubSubTopic`
- `LogSink` → `BigQueryDataset`

**Properties:**
```cypher
filter: String               // Log filter expression
includeChildren: Boolean     // Include child resources
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

---

## 10. DEPENDENCY RELATIONSHIPS

### 10.1 DEPENDS_ON

**Purpose:** Generic dependency between resources.

**Direction:** Dependent → Dependency

**Cardinality:** N:M (Many resources depend on many resources)

**Source → Target Patterns:**
- Any resource → Any resource (generic dependency)
- `ComputeInstance` → `VPCNetwork` (network dependency)
- `CloudFunction` → `PubSubTopic` (trigger dependency)
- `LoadBalancer` → `BackendService` (configuration dependency)

**Properties:**
```cypher
dependencyType: String       // REQUIRED | OPTIONAL | IMPLICIT
reason: String               // Human-readable dependency reason
critical: Boolean            // Critical dependency flag
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
```

**Sample Cypher:**
```cypher
// Function depends on topic for trigger
MATCH (fn:CloudFunction {gcpId: "fn-123"})
MATCH (topic:PubSubTopic {gcpId: "topic-456"})
CREATE (fn)-[:DEPENDS_ON {
  dependencyType: "REQUIRED",
  reason: "Function triggered by Pub/Sub messages",
  critical: true,
  createdAt: datetime(),
  updatedAt: datetime(),
  deletedAt: null
}]->(topic)
```

---

## 11. RELATIONSHIP CARDINALITY MATRIX

| Relationship | Source | Target | Cardinality | Bidirectional |
|--------------|--------|--------|-------------|---------------|
| CONTAINS | Parent | Child | 1:N | No (PART_OF) |
| PART_OF | Child | Parent | N:1 | No (CONTAINS) |
| ATTACHED_TO | Instance | Network | N:M | No |
| ROUTES_TO | Route | Target | 1:N | No |
| ALLOWS_TRAFFIC | Firewall | Resource | 1:N | No |
| PEERS_WITH | VPC | VPC | N:M | Yes |
| FORWARDS_TO | LB/Backend | Target | 1:N | No |
| HEALTH_CHECKED_BY | Resource | HealthCheck | N:M | No |
| USES_TEMPLATE | InstanceGroup | Template | N:1 | No |
| SCALES | Autoscaler | InstanceGroup | 1:1 | No |
| USES_DISK | Instance | Disk | N:M | No |
| CREATED_FROM | Resource | Source | N:1 | No |
| HAS_DATABASE | Instance | Database | 1:N | No |
| HAS_IAM_POLICY | Resource | Policy | 1:1 | No |
| GRANTS_ROLE | Policy | Role | N:M | No |
| USES_SERVICE_ACCOUNT | Resource | ServiceAccount | N:M | No |
| ENCRYPTED_BY | Resource | CryptoKey | N:1 | No |
| PUBLISHES_TO | Publisher | Topic | N:M | No |
| SUBSCRIBES_TO | Subscription | Topic | N:1 | No |
| TRIGGERED_BY | Function/Service | EventSource | N:M | No |
| MONITORS | AlertPolicy | Resource | N:M | No |
| NOTIFIES_THROUGH | AlertPolicy | Channel | N:M | No |
| DEPENDS_ON | Dependent | Dependency | N:M | No |

---

## 12. COMPLEX QUERY EXAMPLES

### 12.1 Find All Resources Affected by a Firewall Rule Change

```cypher
// Find all instances affected by a specific firewall rule
MATCH (fw:FirewallRule {name: "allow-web-traffic"})
MATCH (fw)-[r:ALLOWS_TRAFFIC]->(vm:ComputeInstance)
RETURN vm.name, vm.zone, r.ports, r.sourceRanges
```

### 12.2 Trace Network Path from Instance to Internet

```cypher
// Trace routing path from instance
MATCH path = (vm:ComputeInstance {name: "web-server-01"})
  -[:ATTACHED_TO]->(subnet:Subnet)
  -[:PART_OF]->(vpc:VPCNetwork)
  <-[:ROUTES_TO]-(route:Route)
WHERE route.destRange = "0.0.0.0/0"
RETURN path
```

### 12.3 Find All Resources Using a Specific Service Account

```cypher
// Find resources using compromised service account
MATCH (resource)-[r:USES_SERVICE_ACCOUNT]->(sa:ServiceAccount {
  email: "compromised@project.iam.gserviceaccount.com"
})
RETURN DISTINCT labels(resource)[0] as resourceType, 
       resource.name, 
       resource.gcpId,
       r.scopes
```

### 12.4 Identify Circular Dependencies

```cypher
// Find circular dependencies (depth 2-5)
MATCH path = (r1)-[:DEPENDS_ON*2..5]->(r1)
WHERE ALL(rel IN relationships(path) WHERE rel.deletedAt IS NULL)
RETURN path
LIMIT 10
```

### 12.5 Find Load Balancer Configuration Chain

```cypher
// Complete load balancer to instance chain
MATCH path = (lb:LoadBalancer {name: "web-lb"})
  -[:FORWARDS_TO]->(bs:BackendService)
  -[:FORWARDS_TO]->(ig:InstanceGroup)
  -[:CONTAINS]->(vm:ComputeInstance)
RETURN path
```

### 12.6 Find All Resources Encrypted by Specific KMS Key

```cypher
// Audit encryption key usage
MATCH (resource)-[r:ENCRYPTED_BY]->(key:CryptoKey {name: "production-key"})
RETURN labels(resource)[0] as resourceType,
       resource.name,
       r.keyVersion,
       resource.createdAt
ORDER BY resource.createdAt DESC
```

### 12.7 Identify Alert Coverage Gaps

```cypher
// Find compute instances without alert monitoring
MATCH (vm:ComputeInstance)
WHERE vm.status = "RUNNING"
  AND vm.deletedAt IS NULL
  AND NOT EXISTS {
    MATCH (vm)<-[:MONITORS]-(policy:AlertPolicy)
    WHERE policy.enabled = true
  }
RETURN vm.name, vm.zone, vm.machineType
```

### 12.8 Map Complete IAM Access Path

```cypher
// Find who has access to a bucket
MATCH (bucket:StorageBucket {name: "sensitive-data"})
  -[:HAS_IAM_POLICY]->(policy:IAMPolicy)
  -[grant:GRANTS_ROLE]->(role:IAMRole)
RETURN bucket.name,
       role.name,
       grant.members,
       role.includedPermissions
```

### 12.9 Trace Pub/Sub Message Flow

```cypher
// Trace complete message pipeline
MATCH path = (publisher)
  -[:PUBLISHES_TO]->(topic:PubSubTopic)
  <-[:SUBSCRIBES_TO]-(sub:PubSubSubscription)
  -[:TRIGGERS]->(consumer)
WHERE topic.name = "user-events"
RETURN path
```

### 12.10 Find Resource Hierarchy Path

```cypher
// Get complete hierarchy from resource to organization
MATCH path = (resource)
  -[:PART_OF*]->(org:Organization)
WHERE resource.gcpId = "vm-789"
RETURN path
```

---

## 13. RELATIONSHIP VALIDATION RULES

### 13.1 Mutual Exclusivity
- A resource cannot have both `ALLOWS_TRAFFIC` and `DENIES_TRAFFIC` from the same firewall rule
- A VPC cannot `PEERS_WITH` itself

### 13.2 Required Relationships
- Every `ComputeInstance` MUST have at least one `ATTACHED_TO` relationship with a `Subnet`
- Every `Subnet` MUST have exactly one `PART_OF` relationship with a `VPCNetwork`
- Every `Project` MUST have exactly one `PART_OF` relationship with either `Organization` or `Folder`

### 13.3 Cardinality Constraints
- One `Autoscaler` can only `SCALES` one `InstanceGroup` (1:1)
- One `CloudRunService` can `HAS_REVISION` multiple `CloudRunRevision` nodes (1:N)
- One `BackendService` can `FORWARDS_TO` multiple `InstanceGroup` nodes (1:N)

### 13.4 Temporal Consistency
- Relationship `createdAt` must be >= both source and target node `createdAt`
- If relationship has `deletedAt`, both source and target should exist (not have `deletedAt` before relationship deletion)

---

## 14. CYPHER CONSTRAINTS FOR RELATIONSHIPS

```cypher
// Ensure autoscaler only scales one instance group
CREATE CONSTRAINT autoscaler_unique_target IF NOT EXISTS
FOR ()-[r:SCALES]-()
REQUIRE (r.source, r.target) IS UNIQUE;

// Ensure relationships have temporal tracking
CREATE CONSTRAINT relationship_created_at IF NOT EXISTS
FOR ()-[r:DEPENDS_ON]-()
REQUIRE r.createdAt IS NOT NULL;
```

---

## 15. NEXT STEPS

This relationship schema enables:

1. **Subtask 1.4**: Implement Neo4j Constraints and Indexes
   - Create uniqueness constraints for relationships
   - Define indexes for frequently queried relationship properties
   - Set up composite indexes for complex traversals

2. **Subtask 1.5**: Create Schema Documentation and Visualization
   - Generate visual relationship diagram
   - Document traversal patterns
   - Create query optimization guide

3. **Phase I Development**: Neo4j Database Implementation
   - Implement relationship creation in data ingestion pipeline
   - Build graph traversal query library
   - Create relationship validation tools

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-06  
**Author:** Digital Twin Agent Team  
**Total Relationships Defined:** 35+ relationship types

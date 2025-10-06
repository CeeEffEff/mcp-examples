# Neo4j Node Schema Definition for GCP Resources

## Document Purpose
This document defines the Neo4j node labels, properties, and data types for all GCP resources in the digital twin. It translates the GCP resource inventory into a structured Neo4j schema with consistent naming conventions and temporal tracking capabilities.

---

## 1. SCHEMA DESIGN PRINCIPLES

### 1.1 Naming Conventions

**Labels:**
- Use PascalCase for node labels (e.g., `ComputeInstance`, `VPCNetwork`)
- Labels should be descriptive and match the resource type
- Use singular form (e.g., `ComputeInstance` not `ComputeInstances`)

**Properties:**
- Use camelCase for all property names (e.g., `machineType`, `ipCidrRange`)
- Avoid abbreviations unless they are GCP-standard (e.g., `id`, `cpu`, `vpc`)
- Use clear, descriptive names that match GCP terminology

**Data Types:**
- String: Text values, IDs, names, enums
- Integer: Counts, sizes, numeric IDs
- Float: Percentages, ratios, utilization metrics
- Boolean: True/false flags
- DateTime: ISO 8601 timestamps
- List<String>: Arrays of strings
- List<Map>: Arrays of complex objects

### 1.2 Standard Properties

All nodes MUST include these standard properties:

```cypher
// Temporal Tracking Properties (Required for all nodes)
createdAt: DateTime           // Resource creation timestamp
updatedAt: DateTime           // Last update timestamp
deletedAt: DateTime           // Soft deletion timestamp (null if active)
snapshotTimestamp: DateTime   // Digital twin snapshot capture time

// GCP Resource Properties (Required for all nodes)
gcpId: String                 // GCP unique identifier
gcpSelfLink: String          // Full GCP resource URL
resourceType: String          // GCP resource type (e.g., "compute.instances")

// Metadata Properties (Optional but recommended)
labels: Map<String, String>   // GCP resource labels
description: String           // Human-readable description
projectId: String            // Parent GCP project ID
```

---

## 2. COMPUTE RESOURCES

### 2.1 ComputeInstance

**Node Label:** `ComputeInstance`

**Properties:**
```cypher
// Identity
gcpId: String                           // Unique instance ID
name: String                            // Instance name
zone: String                            // Zone location (e.g., "us-central1-a")

// Configuration
machineType: String                     // Machine type (e.g., "n1-standard-1")
cpuPlatform: String                     // CPU architecture
status: String                          // ENUM: PROVISIONING|STAGING|RUNNING|STOPPING|TERMINATED|SUSPENDING|SUSPENDED

// Network Configuration
networkInterfaces: List<Map>            // Array of network interface configs
tags: List<String>                      // Network tags for firewall rules
canIpForward: Boolean                   // IP forwarding enabled

// Disk Configuration
disks: List<Map>                        // Array of attached disk configs
bootDiskSizeGb: Integer                // Boot disk size

// Metadata
metadata: Map<String, String>           // Custom metadata key-values
labels: Map<String, String>             // Resource labels

// Service Accounts
serviceAccounts: List<Map>              // Service account configurations

// Scheduling
preemptible: Boolean                    // Preemptible instance flag
automaticRestart: Boolean               // Auto-restart on failure
onHostMaintenance: String               // MIGRATE | TERMINATE

// Performance Metrics (updated periodically)
cpuUtilization: Float                   // CPU utilization percentage (0-100)
memoryUtilization: Float                // Memory utilization percentage (0-100)
diskReadOpsPerSec: Float               // Disk read operations per second
diskWriteOpsPerSec: Float              // Disk write operations per second
networkSentBytesPerSec: Float          // Network sent bytes per second
networkReceivedBytesPerSec: Float      // Network received bytes per second

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.instances"
projectId: String
```

**Sample Cypher CREATE:**
```cypher
CREATE (i:ComputeInstance {
  gcpId: "1234567890123456789",
  name: "web-server-01",
  zone: "us-central1-a",
  machineType: "n1-standard-2",
  cpuPlatform: "Intel Cascade Lake",
  status: "RUNNING",
  networkInterfaces: [
    {
      network: "projects/my-project/global/networks/default",
      subnetwork: "projects/my-project/regions/us-central1/subnetworks/default",
      networkIP: "10.128.0.2"
    }
  ],
  tags: ["web-server", "production"],
  canIpForward: false,
  disks: [
    {
      source: "projects/my-project/zones/us-central1-a/disks/web-server-01",
      boot: true,
      autoDelete: true
    }
  ],
  bootDiskSizeGb: 50,
  metadata: {env: "production", team: "platform"},
  labels: {environment: "prod", app: "web"},
  serviceAccounts: [
    {
      email: "web-sa@my-project.iam.gserviceaccount.com",
      scopes: ["https://www.googleapis.com/auth/cloud-platform"]
    }
  ],
  preemptible: false,
  automaticRestart: true,
  onHostMaintenance: "MIGRATE",
  cpuUtilization: 45.2,
  memoryUtilization: 62.8,
  diskReadOpsPerSec: 120.5,
  diskWriteOpsPerSec: 85.3,
  networkSentBytesPerSec: 1250000.0,
  networkReceivedBytesPerSec: 3400000.0,
  createdAt: datetime("2024-01-15T10:30:00Z"),
  updatedAt: datetime("2025-01-06T12:00:00Z"),
  deletedAt: null,
  snapshotTimestamp: datetime("2025-01-06T13:00:00Z"),
  gcpSelfLink: "https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instances/web-server-01",
  resourceType: "compute.instances",
  projectId: "my-project"
})
```

---

### 2.2 InstanceTemplate

**Node Label:** `InstanceTemplate`

**Properties:**
```cypher
// Identity
gcpId: String
name: String

// Configuration
properties: Map                         // VM configuration properties (nested)
description: String

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.instanceTemplates"
projectId: String
```

**Sample Cypher CREATE:**
```cypher
CREATE (t:InstanceTemplate {
  gcpId: "9876543210987654321",
  name: "web-server-template-v2",
  properties: {
    machineType: "n1-standard-2",
    disks: [{boot: true, initializeParams: {sourceImage: "debian-11"}}],
    networkInterfaces: [{network: "default"}]
  },
  description: "Template for web server instances",
  createdAt: datetime("2024-01-10T09:00:00Z"),
  updatedAt: datetime("2024-01-10T09:00:00Z"),
  deletedAt: null,
  snapshotTimestamp: datetime("2025-01-06T13:00:00Z"),
  gcpSelfLink: "https://www.googleapis.com/compute/v1/projects/my-project/global/instanceTemplates/web-server-template-v2",
  resourceType: "compute.instanceTemplates",
  projectId: "my-project"
})
```

---

### 2.3 InstanceGroup

**Node Label:** `InstanceGroup`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
zone: String                            // Zone location (null for regional)
region: String                          // Region location (null for zonal)

// Configuration
groupType: String                       // MANAGED | UNMANAGED
size: Integer                           // Current number of instances
targetSize: Integer                     // Desired number (managed only)

// Autohealing (Managed Instance Groups)
autohealing: Map                        // Health check configuration
updatePolicy: Map                       // Rolling update configuration

// Network
network: String                         // Network reference
subnetwork: String                      // Subnetwork reference

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.instanceGroups"
projectId: String
labels: Map<String, String>
```

**Sample Cypher CREATE:**
```cypher
CREATE (g:InstanceGroup {
  gcpId: "5555666677778888",
  name: "web-servers-mig",
  zone: "us-central1-a",
  region: null,
  groupType: "MANAGED",
  size: 5,
  targetSize: 5,
  autohealing: {
    healthCheck: "projects/my-project/global/healthChecks/web-hc",
    initialDelaySec: 300
  },
  updatePolicy: {
    type: "PROACTIVE",
    minimalAction: "REPLACE",
    maxSurge: {fixed: 3},
    maxUnavailable: {fixed: 0}
  },
  network: "projects/my-project/global/networks/default",
  subnetwork: "projects/my-project/regions/us-central1/subnetworks/default",
  createdAt: datetime("2024-02-01T14:00:00Z"),
  updatedAt: datetime("2025-01-06T10:30:00Z"),
  deletedAt: null,
  snapshotTimestamp: datetime("2025-01-06T13:00:00Z"),
  gcpSelfLink: "https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instanceGroups/web-servers-mig",
  resourceType: "compute.instanceGroups",
  projectId: "my-project",
  labels: {app: "web", managed: "true"}
})
```

---

### 2.4 Autoscaler

**Node Label:** `Autoscaler`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
zone: String
region: String

// Target
target: String                          // Instance group reference

// Autoscaling Policy
minNumReplicas: Integer                 // Minimum instances
maxNumReplicas: Integer                 // Maximum instances
coolDownPeriodSec: Integer             // Cooldown period
cpuUtilizationTarget: Float            // Target CPU percentage
loadBalancingUtilizationTarget: Float  // Target LB utilization

// Scaling Mode
mode: String                            // ON | OFF | ONLY_UP

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.autoscalers"
projectId: String
```

---

### 2.5 GKECluster

**Node Label:** `GKECluster`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
location: String                        // Zone or region

// Versions
currentMasterVersion: String            // K8s master version
currentNodeVersion: String              // K8s node version

// Status
status: String                          // ENUM: PROVISIONING|RUNNING|RECONCILING|STOPPING|ERROR|DEGRADED
statusMessage: String                   // Status details

// Network Configuration
network: String                         // VPC network reference
subnetwork: String                      // Subnetwork reference
clusterIpv4Cidr: String                // Cluster IP range
servicesIpv4Cidr: String               // Services IP range
endpoint: String                        // API server endpoint
privateClusterConfig: Map              // Private cluster configuration

// Node Configuration
nodeCount: Integer                      // Total nodes across all pools
currentNodeCount: Integer              // Current active nodes

// Addons
addonsConfig: Map                       // Enabled addons configuration
loggingService: String                 // Logging service
monitoringService: String              // Monitoring service

// Security
masterAuth: Map                         // Master authentication config
networkPolicy: Map                      // Network policy config

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "container.clusters"
projectId: String
labels: Map<String, String>
```

---

### 2.6 GKENodePool

**Node Label:** `GKENodePool`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
clusterName: String                     // Parent cluster name

// Status
status: String                          // ENUM: PROVISIONING|RUNNING|STOPPING|ERROR
statusMessage: String

// Configuration
instanceCount: Integer                  // Number of nodes
machineType: String                     // Node machine type
diskSizeGb: Integer                    // Boot disk size
diskType: String                        // pd-standard | pd-ssd
imageType: String                       // Node image type
preemptible: Boolean                    // Preemptible nodes flag

// Autoscaling
autoscaling: Map                        // Autoscaling configuration
  // {enabled: Boolean, minNodeCount: Integer, maxNodeCount: Integer}

// Management
management: Map                         // Auto-upgrade and auto-repair config
upgradeSettings: Map                    // Upgrade strategy

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "container.nodePools"
projectId: String
labels: Map<String, String>
```

---

### 2.7 CloudFunction

**Node Label:** `CloudFunction`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
region: String

// Status
status: String                          // ENUM: ACTIVE|OFFLINE|DEPLOY_IN_PROGRESS|DELETE_IN_PROGRESS|UNKNOWN
buildId: String                         // Build identifier

// Runtime Configuration
runtime: String                         // nodejs18 | python311 | go121 | etc.
entryPoint: String                      // Function entry point
sourceArchiveUrl: String                // Source code location
sourceRepository: Map                   // Source repository config

// Trigger Configuration
triggerType: String                     // HTTP | PUBSUB | STORAGE | FIRESTORE
httpsTrigger: Map                       // HTTPS trigger config
eventTrigger: Map                       // Event trigger config

// Resource Allocation
availableMemoryMb: Integer             // Allocated memory
timeout: String                         // Execution timeout (e.g., "60s")
maxInstances: Integer                   // Max concurrent executions
minInstances: Integer                   // Min instances for scaling

// Network
vpcConnector: String                    // VPC connector reference
ingressSettings: String                 // ALLOW_ALL | ALLOW_INTERNAL_ONLY | ALLOW_INTERNAL_AND_GCLB

// Environment
environmentVariables: Map<String, String>
buildEnvironmentVariables: Map<String, String>
serviceAccountEmail: String

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "cloudfunctions.functions"
projectId: String
labels: Map<String, String>
```

---

### 2.8 CloudRunService

**Node Label:** `CloudRunService`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
region: String

// Status
status: String                          // Ready | Failed | Unknown
statusMessage: String
url: String                             // Service URL
latestReadyRevisionName: String        // Current active revision

// Traffic Configuration
traffic: List<Map>                      // Traffic splitting config
  // [{revisionName: String, percent: Integer, tag: String}]

// Template Configuration
containerImage: String                  // Container image path
concurrency: Integer                    // Max concurrent requests per instance
timeoutSeconds: Integer                 // Request timeout
serviceAccountName: String              // Service account

// Resources
cpu: String                             // CPU allocation (e.g., "1000m")
memory: String                          // Memory allocation (e.g., "512Mi")

// Scaling
minScale: Integer                       // Minimum instances
maxScale: Integer                       // Maximum instances

// Network
ingress: String                         // INGRESS_TRAFFIC_ALL | INTERNAL | INTERNAL_AND_CLOUD_LOAD_BALANCING
vpcAccess: Map                          // VPC access configuration

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "run.services"
projectId: String
labels: Map<String, String>
```

---

### 2.9 CloudRunRevision

**Node Label:** `CloudRunRevision`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
serviceName: String                     // Parent service name
region: String

// Status
status: String                          // Active | Reserve | Retired
containerImage: String                  // Container image used

// Configuration
concurrency: Integer
timeoutSeconds: Integer
cpu: String
memory: String

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "run.revisions"
projectId: String
labels: Map<String, String>
```

---

## 3. NETWORKING RESOURCES

### 3.1 VPCNetwork

**Node Label:** `VPCNetwork`

**Properties:**
```cypher
// Identity
gcpId: String
name: String

// Configuration
autoCreateSubnetworks: Boolean          // Auto-create mode
routingMode: String                     // REGIONAL | GLOBAL
mtu: Integer                            // Maximum transmission unit

// Peering
peerings: List<Map>                     // VPC peering configurations

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.networks"
projectId: String
description: String
```

**Sample Cypher CREATE:**
```cypher
CREATE (n:VPCNetwork {
  gcpId: "1111222233334444",
  name: "production-vpc",
  autoCreateSubnetworks: false,
  routingMode: "GLOBAL",
  mtu: 1460,
  peerings: [],
  createdAt: datetime("2024-01-05T08:00:00Z"),
  updatedAt: datetime("2024-01-05T08:00:00Z"),
  deletedAt: null,
  snapshotTimestamp: datetime("2025-01-06T13:00:00Z"),
  gcpSelfLink: "https://www.googleapis.com/compute/v1/projects/my-project/global/networks/production-vpc",
  resourceType: "compute.networks",
  projectId: "my-project",
  description: "Production VPC network"
})
```

---

### 3.2 Subnet

**Node Label:** `Subnet`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
region: String

// Network Reference
network: String                         // Parent VPC network reference

// IP Configuration
ipCidrRange: String                     // Primary IP range (e.g., "10.0.0.0/24")
gatewayAddress: String                  // Gateway IP
secondaryIpRanges: List<Map>           // Secondary IP ranges
  // [{rangeName: String, ipCidrRange: String}]

// Access Configuration
privateIpGoogleAccess: Boolean          // Private Google access
enableFlowLogs: Boolean                 // VPC flow logs enabled
flowLogsConfig: Map                     // Flow logs configuration

// Purpose
purpose: String                         // PRIVATE | INTERNAL_HTTPS_LOAD_BALANCER | etc.
role: String                            // ACTIVE | BACKUP

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.subnetworks"
projectId: String
description: String
```

---

### 3.3 FirewallRule

**Node Label:** `FirewallRule`

**Properties:**
```cypher
// Identity
gcpId: String
name: String

// Network Reference
network: String                         // Parent VPC network reference

// Rule Configuration
direction: String                       // INGRESS | EGRESS
priority: Integer                       // 0-65535 (lower = higher priority)
action: String                          // ALLOW | DENY

// Traffic Specification
allowed: List<Map>                      // Allowed protocols/ports
  // [{protocol: String, ports: List<String>}]
denied: List<Map>                       // Denied protocols/ports

// Source/Destination (Ingress)
sourceRanges: List<String>              // Source IP ranges
sourceTags: List<String>                // Source instance tags
sourceServiceAccounts: List<String>     // Source service accounts

// Destination (Egress)
destinationRanges: List<String>         // Destination IP ranges

// Target
targetTags: List<String>                // Target instance tags
targetServiceAccounts: List<String>     // Target service accounts

// Status
disabled: Boolean                       // Rule disabled flag

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.firewalls"
projectId: String
description: String
```

---

### 3.4 Route

**Node Label:** `Route`

**Properties:**
```cypher
// Identity
gcpId: String
name: String

// Network Reference
network: String                         // Parent VPC network reference

// Route Configuration
destRange: String                       // Destination IP range (CIDR)
priority: Integer                       // Route priority (0-65535)

// Next Hop
nextHopType: String                     // GATEWAY | INSTANCE | IP | VPN_TUNNEL | INTERCONNECT
nextHopGateway: String                  // Gateway URL
nextHopInstance: String                 // Instance URL
nextHopIp: String                       // Next hop IP address
nextHopVpnTunnel: String               // VPN tunnel URL
nextHopInterconnectAttachment: String  // Interconnect attachment URL

// Tags
tags: List<String>                      // Instance tags this route applies to

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.routes"
projectId: String
description: String
```

---

### 3.5 LoadBalancer

**Node Label:** `LoadBalancer`

**Properties:**
```cypher
// Identity
gcpId: String
name: String

// Type
loadBalancerType: String                // HTTP | HTTPS | TCP | UDP | INTERNAL | INTERNAL_HTTP

// Configuration
ipAddress: String                       // Frontend IP address
ipProtocol: String                      // TCP | UDP
port: Integer                           // Frontend port
portRange: String                       // Port range (e.g., "80-8080")

// Backend Configuration
backendServices: List<String>           // Backend service references

// URL Routing (HTTP/HTTPS only)
urlMap: String                          // URL map reference

// SSL (HTTPS only)
sslCertificates: List<String>          // SSL certificate references
sslPolicy: String                       // SSL policy reference

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.targetHttpProxies" or similar
projectId: String
description: String
```

---

### 3.6 BackendService

**Node Label:** `BackendService`

**Properties:**
```cypher
// Identity
gcpId: String
name: String

// Protocol
protocol: String                        // HTTP | HTTPS | HTTP2 | TCP | UDP | GRPC
port: Integer                           // Backend port
portName: String                        // Named port

// Backends
backends: List<Map>                     // Backend configurations
  // [{group: String, balancingMode: String, capacityScaler: Float}]

// Health Checks
healthChecks: List<String>              // Health check references

// Timeout and Session
timeoutSec: Integer                     // Request timeout
connectionDrainingTimeoutSec: Integer  // Connection draining timeout
sessionAffinity: String                 // CLIENT_IP | GENERATED_COOKIE | etc.
affinityCookieTtlSec: Integer         // Cookie TTL

// Load Balancing
loadBalancingScheme: String             // EXTERNAL | INTERNAL | INTERNAL_SELF_MANAGED

// CDN Configuration
enableCDN: Boolean                      // Cloud CDN enabled
cdnPolicy: Map                          // CDN policy configuration

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.backendServices"
projectId: String
description: String
```

---

### 3.7 HealthCheck

**Node Label:** `HealthCheck`

**Properties:**
```cypher
// Identity
gcpId: String
name: String

// Type
healthCheckType: String                 // HTTP | HTTPS | TCP | SSL | HTTP2 | GRPC

// HTTP/HTTPS Configuration
requestPath: String                     // Request path
host: String                            // Host header
port: Integer                           // Health check port
proxyHeader: String                     // NONE | PROXY_V1

// TCP/SSL Configuration
portSpecification: String               // USE_FIXED_PORT | USE_NAMED_PORT | USE_SERVING_PORT

// Timing
checkIntervalSec: Integer              // Check interval
timeoutSec: Integer                     // Check timeout
healthyThreshold: Integer               // Healthy count threshold
unhealthyThreshold: Integer             // Unhealthy count threshold

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.healthChecks"
projectId: String
description: String
```

---

### 3.8 DNSZone

**Node Label:** `DNSZone`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
dnsName: String                         // DNS name (e.g., "example.com.")

// Type
visibility: String                      // PUBLIC | PRIVATE

// Name Servers
nameServers: List<String>               // Authoritative name servers

// DNSSEC
dnssecConfig: Map                       // DNSSEC configuration
  // {state: String, defaultKeySpecs: List<Map>}

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "dns.managedZones"
projectId: String
description: String
```

---

### 3.9 DNSRecord

**Node Label:** `DNSRecord`

**Properties:**
```cypher
// Identity (composite)
name: String                            // Record name (FQDN)
type: String                            // A | AAAA | CNAME | MX | TXT | NS | SOA | etc.
zoneName: String                        // Parent zone name

// Configuration
ttl: Integer                            // Time to live (seconds)
rrdatas: List<String>                   // Record data values

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "dns.resourceRecordSets"
projectId: String
```

---

### 3.10 VPNGateway

**Node Label:** `VPNGateway`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
region: String

// Network
network: String                         // Parent VPC network reference

// Configuration
vpnGatewayType: String                  // CLASSIC | HA
ipAddress: String                       // External IP address (Classic VPN)
vpnInterfaces: List<Map>                // Interfaces (HA VPN)

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.vpnGateways"
projectId: String
description: String
```

---

### 3.11 VPNTunnel

**Node Label:** `VPNTunnel`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
region: String

// Status
status: String                          // ENUM: PROVISIONING|WAITING_FOR_FULL_CONFIG|ESTABLISHED|NO_INCOMING_PACKETS
detailedStatus: String                  // Detailed status message

// Gateway References
vpnGateway: String                      // VPN gateway reference
peerGcpGateway: String                 // Peer GCP gateway (if HA VPN)
peerExternalGateway: String            // Peer external gateway

// Peer Configuration
peerIp: String                          // Peer gateway IP
peerGatewayInterface: Integer          // Peer gateway interface

// IKE Configuration
ikeVersion: Integer                     // 1 or 2
sharedSecretHash: String               // SHA256 hash of shared secret

// Routing
router: String                          // Cloud Router reference
localTrafficSelector: List<String>     // Local IP ranges
remoteTrafficSelector: List<String>    // Remote IP ranges

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.vpnTunnels"
projectId: String
description: String
```

---

## 4. STORAGE RESOURCES

### 4.1 StorageBucket

**Node Label:** `StorageBucket`

**Properties:**
```cypher
// Identity
gcpId: String
name: String                            // Globally unique bucket name

// Location
location: String                        // Region or multi-region
locationType: String                    // REGION | MULTI_REGION

// Storage Class
storageClass: String                    // STANDARD | NEARLINE | COLDLINE | ARCHIVE

// Versioning
versioningEnabled: Boolean              // Object versioning

// Lifecycle
lifecycleRules: List<Map>              // Lifecycle management rules

// Access Control
iamConfiguration: Map                   // IAM config (uniform vs fine-grained)
publicAccessPrevention: String          // inherited | enforced

// Encryption
encryption: Map                         // Default encryption configuration
  // {defaultKmsKeyName: String}

// Retention
retentionPolicy: Map                    // Data retention policy
  // {retentionPeriod: Integer, isLocked: Boolean}

// Logging
logging: Map                            // Access logging configuration

// Website
website: Map                            // Static website configuration

// CORS
cors: List<Map>                         // CORS configuration

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "storage.buckets"
projectId: String
labels: Map<String, String>
```

---

### 4.2 StorageObject

**Node Label:** `StorageObject`

**Properties:**
```cypher
// Identity
gcpId: String
name: String                            // Object path within bucket
bucket: String                          // Parent bucket name
generation: String                      // Object generation number

// Content
size: Integer                           // Object size in bytes
contentType: String                     // MIME type
crc32c: String                          // CRC32C checksum
md5Hash: String                         // MD5 hash

// Encryption
kmsKeyName: String                      // KMS key if encrypted

// Metadata
metadata: Map<String, String>           // Custom metadata
cacheControl: String                    // Cache control header
contentDisposition: String              // Content disposition header
contentEncoding: String                 // Content encoding header
contentLanguage: String                 // Content language header

// Versioning
isCurrentVersion: Boolean               // Current version flag
timeDeleted: DateTime                   // Deletion time (if versioned)

// Storage Class
storageClass: String                    // STANDARD | NEARLINE | COLDLINE | ARCHIVE

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "storage.objects"
projectId: String
```

---

### 4.3 PersistentDisk

**Node Label:** `PersistentDisk`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
zone: String

// Configuration
sizeGb: Integer                         // Disk size in GB
type: String                            // pd-standard | pd-balanced | pd-ssd | pd-extreme
physicalBlockSizeBytes: Integer        // Physical block size

// Status
status: String                          // ENUM: CREATING|RESTORING|READY|DELETING|FAILED
lastAttachTimestamp: DateTime          // Last attach time
lastDetachTimestamp: DateTime          // Last detach time

// Source
sourceSnapshot: String                  // Source snapshot reference
sourceImage: String                     // Source image reference

// Users
users: List<String>                     // Attached instance references

// Performance (pd-extreme only)
provisionedIops: Integer                // Provisioned IOPS

// Encryption
diskEncryptionKey: Map                  // Encryption key configuration

// Replication (regional disks)
replicaZones: List<String>             // Replica zones

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.disks"
projectId: String
description: String
labels: Map<String, String>
```

---

### 4.4 DiskSnapshot

**Node Label:** `DiskSnapshot`

**Properties:**
```cypher
// Identity
gcpId: String
name: String

// Source
sourceDisk: String                      // Source disk reference
sourceDiskId: String                    // Source disk ID

// Size
diskSizeGb: Integer                     // Original disk size
storageBytes: Integer                   // Actual storage used
storageBytesStatus: String             // UP_TO_DATE | UPDATING

// Status
status: String                          // ENUM: CREATING|UPLOADING|READY|DELETING|FAILED

// Encryption
snapshotEncryptionKey: Map             // Snapshot encryption key
sourceDiskEncryptionKey: Map           // Source disk encryption key

// Type
snapshotType: String                    // STANDARD | ARCHIVE

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "compute.snapshots"
projectId: String
description: String
labels: Map<String, String>
```

---

### 4.5 FilestoreInstance

**Node Label:** `FilestoreInstance`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
location: String                        // Zone location

// Status
state: String                           // ENUM: CREATING|READY|REPAIRING|DELETING|ERROR

// Tier
tier: String                            // STANDARD | PREMIUM | BASIC_HDD | BASIC_SSD | HIGH_SCALE_SSD | ENTERPRISE

// Capacity
capacityGb: Integer                     // Storage capacity

// File Shares
fileShares: List<Map>                   // File share configurations
  // [{name: String, capacityGb: Integer, nfsExportOptions: List<Map>}]

// Networks
networks: List<Map>                     // Network configurations
  // [{network: String, modes: List<String>, reservedIpRange: String, ipAddresses: List<String>}]

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "file.instances"
projectId: String
description: String
labels: Map<String, String>
```

---

## 5. DATABASE RESOURCES

### 5.1 CloudSQLInstance

**Node Label:** `CloudSQLInstance`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
connectionName: String                  // Connection name (project:region:instance)

// Database Engine
databaseVersion: String                 // MYSQL_5_7 | MYSQL_8_0 | POSTGRES_13 | POSTGRES_14 | SQLSERVER_2019

// Status
state: String                           // ENUM: RUNNABLE|SUSPENDED|PENDING_CREATE|MAINTENANCE|FAILED
statusMessage: String

// Location
region: String
gceZone: String                        // Primary zone

// Instance Type
tier: String                            // Machine type (e.g., db-n1-standard-1)
availabilityType: String                // ZONAL | REGIONAL

// Network
ipAddresses: List<Map>                  // IP configurations
  // [{type: String, ipAddress: String}]
privateNetwork: String                  // VPC network for private IP

// Storage
diskType: String                        // PD_SSD | PD_HDD
diskSizeGb: Integer                    // Disk size
diskAutoresizeLimit: Integer           // Max autoresize limit
diskAutoresize: Boolean                // Autoresize enabled

// Backup
backupEnabled: Boolean                  // Automated backups enabled
backupStartTime: String                // Backup start time
backupRetentionDays: Integer           // Backup retention period
pointInTimeRecoveryEnabled: Boolean    // PITR enabled

// High Availability
failoverReplica: Map                    // Failover replica config
replicaNames: List<String>             // Read replica names

// Maintenance
maintenanceWindow: Map                  // Maintenance window config

// Flags
databaseFlags: List<Map>               // Database flags
  // [{name: String, value: String}]

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "sqladmin.instances"
projectId: String
labels: Map<String, String>
```

---

### 5.2 CloudSQLDatabase

**Node Label:** `CloudSQLDatabase`

**Properties:**
```cypher
// Identity
name: String
instance: String                        // Parent instance reference

// Character Set
charset: String                         // Character set
collation: String                       // Collation

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "sqladmin.databases"
projectId: String
```

---

### 5.3 SpannerInstance

**Node Label:** `SpannerInstance`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
displayName: String

// Configuration
config: String                          // Regional or multi-regional config
  // e.g., "regional-us-central1" or "nam3"

// Capacity
nodeCount: Integer                      // Number of nodes
processingUnits: Integer                // Processing units (1 node = 1000 units)

// Status
state: String                           // ENUM: CREATING|READY

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "spanner.instances"
projectId: String
labels: Map<String, String>
```

---

### 5.4 SpannerDatabase

**Node Label:** `SpannerDatabase`

**Properties:**
```cypher
// Identity
name: String
instance: String                        // Parent instance reference

// Status
state: String                           // ENUM: CREATING|READY|READY_OPTIMIZING

// Backup
versionRetentionPeriod: String         // Version retention (e.g., "1h")
earliestVersionTime: DateTime          // Earliest available version

// Encryption
encryptionConfig: Map                   // Encryption configuration

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "spanner.databases"
projectId: String
```

---

### 5.5 BigtableInstance

**Node Label:** `BigtableInstance`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
displayName: String

// Type
type: String                            // PRODUCTION | DEVELOPMENT

// Status
state: String                           // ENUM: CREATING|READY

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "bigtableadmin.instances"
projectId: String
labels: Map<String, String>
```

---

### 5.6 BigtableCluster

**Node Label:** `BigtableCluster`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
instance: String                        // Parent instance reference

// Location
location: String                        // Zone location

// Capacity
serveNodes: Integer                     // Number of nodes
defaultStorageType: String              // SSD | HDD

// Status
state: String                           // ENUM: CREATING|READY|RESIZING

// Autoscaling
autoscalingConfig: Map                  // Autoscaling configuration

// Encryption
encryptionConfig: Map                   // Encryption configuration

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "bigtableadmin.clusters"
projectId: String
```

---

### 5.7 FirestoreDatabase

**Node Label:** `FirestoreDatabase`

**Properties:**
```cypher
// Identity
name: String
locationId: String                      // Database location

// Type
type: String                            // FIRESTORE_NATIVE | DATASTORE_MODE

// Concurrency
concurrencyMode: String                 // OPTIMISTIC | PESSIMISTIC

// App Engine Integration
appEngineIntegrationMode: String       // ENABLED | DISABLED

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "firestore.databases"
projectId: String
```

---

## 6. IAM & SECURITY RESOURCES

### 6.1 ServiceAccount

**Node Label:** `ServiceAccount`

**Properties:**
```cypher
// Identity
gcpId: String                           // Unique ID
email: String                           // Service account email
uniqueId: String                        // Unique numeric ID

// Display
displayName: String
description: String

// OAuth
oauth2ClientId: String                  // OAuth2 client ID

// Status
disabled: Boolean                       // Disabled status

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "iam.serviceAccounts"
projectId: String
```

---

### 6.2 IAMPolicy

**Node Label:** `IAMPolicy`

**Properties:**
```cypher
// Resource Association
resourceId: String                      // Associated resource ID
resourceType: String                    // Project | Folder | Organization | etc.

// Bindings
bindings: List<Map>                     // Role bindings
  // [{role: String, members: List<String>, condition: Map}]

// Version
version: Integer                        // Policy version
etag: String                            // Policy ETag for optimistic locking

// Audit Configuration
auditConfigs: List<Map>                // Audit logging configs

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
projectId: String
```

---

### 6.3 IAMRole

**Node Label:** `IAMRole`

**Properties:**
```cypher
// Identity
name: String                            // Role name
title: String                           // Role title

// Type
roleType: String                        // PREDEFINED | CUSTOM

// Permissions
includedPermissions: List<String>       // Granted permissions

// Lifecycle
stage: String                           // ALPHA | BETA | GA | DEPRECATED
deleted: Boolean                        // Soft deletion flag

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "iam.roles"
projectId: String
description: String
```

---

### 6.4 Secret

**Node Label:** `Secret`

**Properties:**
```cypher
// Identity
gcpId: String
name: String

// Replication
replication: Map                        // Replication policy
  // {automatic: Map, userManaged: Map}

// Rotation
rotation: Map                           // Rotation schedule
nextRotationTime: DateTime             // Next scheduled rotation

// Topics
topics: List<Map>                       // Pub/Sub notification topics

// Expiration
expireTime: DateTime                    // Secret expiration time
ttl: String                             // Time to live

// Version Management
versionAliases: Map<String, String>    // Version aliases

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "secretmanager.secrets"
projectId: String
labels: Map<String, String>
```

---

### 6.5 SecretVersion

**Node Label:** `SecretVersion`

**Properties:**
```cypher
// Identity
name: String                            // Version name
versionId: String                       // Version ID
secret: String                          // Parent secret reference

// Status
state: String                           // ENUM: ENABLED|DISABLED|DESTROYED

// Replication
replicationStatus: Map                  // Replication status

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "secretmanager.versions"
projectId: String
```

---

### 6.6 KMSKeyRing

**Node Label:** `KMSKeyRing`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
location: String                        // Key ring location

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "cloudkms.keyRings"
projectId: String
```

---

### 6.7 CryptoKey

**Node Label:** `CryptoKey`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
keyRing: String                         // Parent key ring reference

// Purpose
purpose: String                         // ENCRYPT_DECRYPT | ASYMMETRIC_SIGN | ASYMMETRIC_DECRYPT | MAC

// Version Template
versionTemplate: Map                    // Algorithm and protection level
  // {algorithm: String, protectionLevel: String}

// Primary Version
primary: Map                            // Primary version info
  // {name: String, state: String, algorithm: String}

// Rotation
nextRotationTime: DateTime             // Next rotation time
rotationPeriod: String                 // Rotation period (e.g., "7776000s" = 90 days)

// Destruction
destroyScheduledDuration: String       // Scheduled destruction duration

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "cloudkms.cryptoKeys"
projectId: String
labels: Map<String, String>
```

---

## 7. APPLICATION SERVICES

### 7.1 PubSubTopic

**Node Label:** `PubSubTopic`

**Properties:**
```cypher
// Identity
gcpId: String
name: String

// Message Storage
messageStoragePolicy: Map               // Storage location policy
  // {allowedPersistenceRegions: List<String>}

// Encryption
kmsKeyName: String                      // KMS key for encryption

// Schema
schemaSettings: Map                     // Message schema settings
  // {schema: String, encoding: String}

// Message Retention
messageRetentionDuration: String       // Message retention (e.g., "86400s")

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "pubsub.topics"
projectId: String
labels: Map<String, String>
```

---

### 7.2 PubSubSubscription

**Node Label:** `PubSubSubscription`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
topic: String                           // Parent topic reference

// Push Configuration
pushConfig: Map                         // Push endpoint configuration
  // {pushEndpoint: String, attributes: Map, oidcToken: Map}

// Acknowledgment
ackDeadlineSeconds: Integer            // Acknowledgment deadline

// Message Retention
retainAckedMessages: Boolean           // Retain acknowledged messages
messageRetentionDuration: String       // Retention duration (e.g., "604800s")

// Expiration
expirationPolicy: Map                   // Subscription expiration policy
  // {ttl: String}

// Filter
filter: String                          // Message filter expression

// Dead Letter
deadLetterPolicy: Map                   // Dead letter queue config
  // {deadLetterTopic: String, maxDeliveryAttempts: Integer}

// Retry
retryPolicy: Map                        // Retry policy
  // {minimumBackoff: String, maximumBackoff: String}

// Ordering
enableMessageOrdering: Boolean          // Message ordering enabled

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "pubsub.subscriptions"
projectId: String
labels: Map<String, String>
```

---

### 7.3 SchedulerJob

**Node Label:** `SchedulerJob`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
location: String                        // Region location

// Schedule
schedule: String                        // Cron expression
timeZone: String                        // IANA time zone

// Target
targetType: String                      // HTTP | PUBSUB | APP_ENGINE
httpTarget: Map                         // HTTP target config
pubsubTarget: Map                       // Pub/Sub target config
appEngineHttpTarget: Map               // App Engine target config

// Status
state: String                           // ENUM: ENABLED|PAUSED|DISABLED

// Retry
retryConfig: Map                        // Retry configuration
  // {retryCount: Integer, maxRetryDuration: String, minBackoffDuration: String, maxBackoffDuration: String}

// Execution
lastAttemptTime: DateTime              // Last execution attempt
scheduleTime: DateTime                  // Next scheduled execution

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "cloudscheduler.jobs"
projectId: String
description: String
```

---

### 7.4 TaskQueue

**Node Label:** `TaskQueue`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
location: String                        // Region location

// Status
state: String                           // ENUM: RUNNING|PAUSED|DISABLED

// Rate Limits
rateLimits: Map                         // Rate limiting config
  // {maxDispatchesPerSecond: Float, maxBurstSize: Integer, maxConcurrentDispatches: Integer}

// Retry
retryConfig: Map                        // Retry configuration
  // {maxAttempts: Integer, maxRetryDuration: String, minBackoff: String, maxBackoff: String, maxDoublings: Integer}

// Stackdriver Logging
stackdriverLoggingConfig: Map          // Logging configuration
  // {samplingRatio: Float}

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "cloudtasks.queues"
projectId: String
```

---

## 8. MONITORING & LOGGING

### 8.1 AlertPolicy

**Node Label:** `AlertPolicy`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
displayName: String

// Status
enabled: Boolean                        // Policy enabled flag

// Conditions
conditions: List<Map>                   // Alert conditions
  // [{displayName: String, conditionThreshold: Map, conditionAbsent: Map}]

// Combiner
combiner: String                        // AND | OR | AND_WITH_MATCHING_RESOURCE

// Notification Channels
notificationChannels: List<String>      // Notification channel references

// Documentation
documentation: Map                      // Alert documentation
  // {content: String, mimeType: String}

// User Labels
userLabels: Map<String, String>        // Custom labels

// Validity
validity: Map                           // Validation status

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "monitoring.alertPolicies"
projectId: String
```

---

### 8.2 NotificationChannel

**Node Label:** `NotificationChannel`

**Properties:**
```cypher
// Identity
gcpId: String
name: String
displayName: String

// Type
type: String                            // email | slack | pagerduty | webhook | sms | etc.

// Configuration
labels: Map<String, String>            // Channel configuration labels
  // e.g., {email_address: "alerts@example.com"} for email

// Status
enabled: Boolean                        // Channel enabled flag

// Verification
verificationStatus: String              // VERIFICATION_STATUS_UNSPECIFIED | UNVERIFIED | VERIFIED

// User Labels
userLabels: Map<String, String>        // Custom labels

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "monitoring.notificationChannels"
projectId: String
description: String
```

---

### 8.3 LogSink

**Node Label:** `LogSink`

**Properties:**
```cypher
// Identity
gcpId: String
name: String

// Destination
destination: String                     // Destination resource URI
  // e.g., "storage.googleapis.com/my-bucket"
  //       "pubsub.googleapis.com/projects/my-project/topics/my-topic"
  //       "bigquery.googleapis.com/projects/my-project/datasets/my_dataset"

// Filter
filter: String                          // Log filter expression

// Output Format
outputVersionFormat: String             // V1 | V2

// Writer Identity
writerIdentity: String                  // Service account for writing

// Include Children
includeChildren: Boolean                // Include child resources

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "logging.sinks"
projectId: String
description: String
```

---

## 9. RESOURCE HIERARCHY

### 9.1 Organization

**Node Label:** `Organization`

**Properties:**
```cypher
// Identity
gcpId: String                           // Organization ID
displayName: String                     // Organization name

// Lifecycle
lifecycleState: String                  // ENUM: ACTIVE|DELETE_REQUESTED

// Domain
directoryCustomerId: String            // G Suite customer ID

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "cloudresourcemanager.organizations"
```

---

### 9.2 Folder

**Node Label:** `Folder`

**Properties:**
```cypher
// Identity
gcpId: String                           // Folder ID
displayName: String                     // Folder name

// Hierarchy
parent: String                          // Parent resource reference
  // Format: "organizations/{org_id}" or "folders/{folder_id}"

// Lifecycle
lifecycleState: String                  // ENUM: ACTIVE|DELETE_REQUESTED

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "cloudresourcemanager.folders"
```

---

### 9.3 Project

**Node Label:** `Project`

**Properties:**
```cypher
// Identity
projectId: String                       // Project ID (immutable, user-chosen)
projectNumber: String                   // Project number (immutable, GCP-assigned)
name: String                            // Project name (mutable)

// Hierarchy
parent: String                          // Parent resource reference
  // Format: "organizations/{org_id}" or "folders/{folder_id}"

// Lifecycle
lifecycleState: String                  // ENUM: ACTIVE|DELETE_REQUESTED|DELETE_IN_PROGRESS

// Standard Properties
createdAt: DateTime
updatedAt: DateTime
deletedAt: DateTime
snapshotTimestamp: DateTime
gcpSelfLink: String
resourceType: String                    // "cloudresourcemanager.projects"
labels: Map<String, String>
```

---

## 10. CYPHER QUERY EXAMPLES

### 10.1 Create Complete ComputeInstance with Relationships

```cypher
// Create VPC Network
CREATE (vpc:VPCNetwork {
  gcpId: "net-123",
  name: "production-vpc",
  autoCreateSubnetworks: false,
  routingMode: "GLOBAL",
  mtu: 1460,
  createdAt: datetime("2024-01-05T08:00:00Z"),
  updatedAt: datetime("2024-01-05T08:00:00Z"),
  snapshotTimestamp: datetime("2025-01-06T13:00:00Z"),
  gcpSelfLink: "https://www.googleapis.com/compute/v1/projects/my-project/global/networks/production-vpc",
  resourceType: "compute.networks",
  projectId: "my-project"
})

// Create Subnet
CREATE (subnet:Subnet {
  gcpId: "subnet-456",
  name: "us-central1-subnet",
  region: "us-central1",
  network: "projects/my-project/global/networks/production-vpc",
  ipCidrRange: "10.128.0.0/20",
  gatewayAddress: "10.128.0.1",
  privateIpGoogleAccess: true,
  createdAt: datetime("2024-01-05T08:30:00Z"),
  updatedAt: datetime("2024-01-05T08:30:00Z"),
  snapshotTimestamp: datetime("2025-01-06T13:00:00Z"),
  gcpSelfLink: "https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1/subnetworks/us-central1-subnet",
  resourceType: "compute.subnetworks",
  projectId: "my-project"
})

// Create Compute Instance
CREATE (vm:ComputeInstance {
  gcpId: "vm-789",
  name: "web-server-01",
  zone: "us-central1-a",
  machineType: "n1-standard-2",
  status: "RUNNING",
  cpuUtilization: 45.2,
  memoryUtilization: 62.8,
  createdAt: datetime("2024-01-15T10:30:00Z"),
  updatedAt: datetime("2025-01-06T12:00:00Z"),
  snapshotTimestamp: datetime("2025-01-06T13:00:00Z"),
  gcpSelfLink: "https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instances/web-server-01",
  resourceType: "compute.instances",
  projectId: "my-project"
})

// Create Relationships
CREATE (subnet)-[:PART_OF]->(vpc)
CREATE (vm)-[:ATTACHED_TO]->(subnet)

RETURN vpc, subnet, vm
```

### 10.2 Query All Running Instances in a Subnet

```cypher
MATCH (vm:ComputeInstance)-[:ATTACHED_TO]->(subnet:Subnet {name: "us-central1-subnet"})
WHERE vm.status = "RUNNING"
RETURN vm.name, vm.machineType, vm.cpuUtilization, vm.memoryUtilization
ORDER BY vm.cpuUtilization DESC
```

### 10.3 Find Resources with High CPU Utilization

```cypher
MATCH (vm:ComputeInstance)
WHERE vm.cpuUtilization > 80.0 AND vm.status = "RUNNING"
RETURN vm.name, vm.zone, vm.cpuUtilization
ORDER BY vm.cpuUtilization DESC
```

### 10.4 Query Resource Hierarchy

```cypher
MATCH path = (org:Organization)-[:CONTAINS*]->(resource)
WHERE org.gcpId = "123456789"
RETURN path
```

---

## 11. VALIDATION CHECKLIST

- ✅ All resource types have corresponding Neo4j labels
- ✅ All properties include Neo4j data types
- ✅ Standard temporal properties included in all nodes
- ✅ Naming conventions documented (PascalCase labels, camelCase properties)
- ✅ Sample Cypher CREATE statements provided
- ✅ GCP-specific enums preserved as strings
- ✅ Complex nested structures represented as Map or List<Map>
- ✅ Resource hierarchy nodes defined (Organization, Folder, Project)
- ✅ Performance metrics included for applicable resources
- ✅ Lifecycle states captured for stateful resources

---

## 12. NEXT STEPS

This schema definition provides the foundation for:

1. **Subtask 1.3**: Design Relationship Types and Properties
   - Define all relationship types between nodes
   - Specify relationship properties and directionality
   - Document cardinality constraints

2. **Subtask 1.4**: Implement Neo4j Constraints and Indexes
   - Create uniqueness constraints on gcpId and other unique identifiers
   - Define indexes for frequently queried properties
   - Set up composite indexes for complex queries

3. **Subtask 1.5**: Create Schema Documentation and Visualization
   - Generate visual schema diagram
   - Create comprehensive API documentation
   - Develop schema migration guides

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-06  
**Author:** Digital Twin Agent Team

# GCP Resource Inventory for Neo4j Schema

## Document Purpose
This document provides a comprehensive categorization of Google Cloud Platform resources that will be represented in the Neo4j digital twin. Each resource type includes attributes, lifecycle states, and corresponding GCP APIs.

---

## 1. COMPUTE RESOURCES

### 1.1 Compute Engine

#### Virtual Machine Instances (compute.instances)
**Node Label:** `ComputeInstance`
**GCP API:** Compute Engine API v1
**Resource Endpoint:** `compute.instances.get`

**Core Attributes:**
- `id`: Unique instance ID
- `name`: Instance name
- `machineType`: Machine configuration (e.g., n1-standard-1, e2-medium)
- `zone`: Geographical zone (e.g., us-central1-a)
- `status`: PROVISIONING | STAGING | RUNNING | STOPPING | TERMINATED | SUSPENDING | SUSPENDED
- `creationTimestamp`: ISO 8601 timestamp
- `cpuPlatform`: CPU architecture (e.g., Intel Cascade Lake)
- `networkInterfaces`: Array of network configurations
- `disks`: Array of attached disk configurations
- `metadata`: Key-value pairs for custom metadata
- `labels`: Resource labels for organization
- `tags`: Network tags for firewall rules
- `serviceAccounts`: Array of service account configurations
- `scheduling`: Preemptibility and automatic restart settings

**Lifecycle States:**
1. PROVISIONING → STAGING → RUNNING (normal startup)
2. RUNNING → STOPPING → TERMINATED (shutdown)
3. RUNNING → SUSPENDING → SUSPENDED (suspend)
4. SUSPENDED → RUNNING (resume)
5. TERMINATED (final state, can be deleted)

**Performance Metrics (from Cloud Monitoring):**
- `cpuUtilization`: Percentage
- `memoryUtilization`: Percentage
- `diskReadOps`: Operations per second
- `diskWriteOps`: Operations per second
- `networkSentBytes`: Bytes per second
- `networkReceivedBytes`: Bytes per second

---

#### Instance Templates (compute.instanceTemplates)
**Node Label:** `InstanceTemplate`
**GCP API:** Compute Engine API v1

**Core Attributes:**
- `id`: Template ID
- `name`: Template name
- `description`: Template description
- `properties`: VM configuration properties
- `creationTimestamp`: ISO 8601 timestamp

---

#### Instance Groups (compute.instanceGroups)
**Node Label:** `InstanceGroup`
**GCP API:** Compute Engine API v1

**Types:**
- Managed Instance Groups (MIG)
- Unmanaged Instance Groups

**Core Attributes:**
- `id`: Group ID
- `name`: Group name
- `zone`: Zone location
- `size`: Current number of instances
- `targetSize`: Desired number of instances (MIG only)
- `autohealing`: Health check configuration
- `updatePolicy`: Rolling update configuration

---

#### Autoscalers (compute.autoscalers)
**Node Label:** `Autoscaler`
**GCP API:** Compute Engine API v1

**Core Attributes:**
- `id`: Autoscaler ID
- `name`: Autoscaler name
- `target`: Link to instance group
- `minNumReplicas`: Minimum instances
- `maxNumReplicas`: Maximum instances
- `cpuUtilization`: Target CPU percentage
- `loadBalancingUtilization`: Target LB utilization

---

### 1.2 Google Kubernetes Engine (GKE)

#### Clusters (container.clusters)
**Node Label:** `GKECluster`
**GCP API:** Kubernetes Engine API v1

**Core Attributes:**
- `id`: Cluster ID
- `name`: Cluster name
- `location`: Zone or region
- `status`: PROVISIONING | RUNNING | RECONCILING | STOPPING | ERROR | DEGRADED
- `currentMasterVersion`: Kubernetes version
- `currentNodeVersion`: Node pool Kubernetes version
- `nodeCount`: Total number of nodes
- `endpoint`: API server endpoint
- `network`: VPC network
- `subnetwork`: VPC subnetwork

**Lifecycle States:**
1. PROVISIONING → RUNNING (normal startup)
2. RUNNING → RECONCILING (updates)
3. RUNNING → STOPPING (deletion)
4. ERROR | DEGRADED (failure states)

---

#### Node Pools (container.nodePools)
**Node Label:** `GKENodePool`
**GCP API:** Kubernetes Engine API v1

**Core Attributes:**
- `id`: Node pool ID
- `name`: Node pool name
- `status`: PROVISIONING | RUNNING | STOPPING | ERROR
- `instanceCount`: Number of nodes
- `machineType`: Node machine type
- `diskSizeGb`: Boot disk size
- `autoscaling`: Autoscaling configuration

---

### 1.3 Cloud Functions

#### Functions (cloudfunctions.functions)
**Node Label:** `CloudFunction`
**GCP API:** Cloud Functions API v1

**Core Attributes:**
- `id`: Function ID
- `name`: Function name
- `status`: ACTIVE | OFFLINE | DEPLOY_IN_PROGRESS | DELETE_IN_PROGRESS | UNKNOWN
- `runtime`: Runtime environment (e.g., nodejs18, python311)
- `entryPoint`: Function entry point
- `trigger`: HTTP, Pub/Sub, Storage, Firestore
- `availableMemoryMb`: Allocated memory
- `timeout`: Execution timeout
- `maxInstances`: Maximum concurrent executions

---

### 1.4 Cloud Run

#### Services (run.services)
**Node Label:** `CloudRunService`
**GCP API:** Cloud Run API v1

**Core Attributes:**
- `id`: Service ID
- `name`: Service name
- `status`: Ready, Failed, Unknown
- `url`: Service URL
- `latestRevision`: Current revision
- `traffic`: Traffic splitting configuration
- `containerImage`: Container image path
- `concurrency`: Maximum concurrent requests

---

#### Revisions (run.revisions)
**Node Label:** `CloudRunRevision`
**GCP API:** Cloud Run API v1

**Core Attributes:**
- `id`: Revision ID
- `name`: Revision name
- `status`: Active, Reserve, Retired
- `containerImage`: Container image
- `creationTimestamp`: ISO 8601 timestamp

---

## 2. NETWORKING RESOURCES

### 2.1 Virtual Private Cloud (VPC)

#### Networks (compute.networks)
**Node Label:** `VPCNetwork`
**GCP API:** Compute Engine API v1

**Core Attributes:**
- `id`: Network ID
- `name`: Network name
- `autoCreateSubnetworks`: Boolean
- `routingConfig`: REGIONAL | GLOBAL
- `mtu`: Maximum transmission unit
- `peerings`: Array of VPC peering configurations

---

#### Subnets (compute.subnetworks)
**Node Label:** `Subnet`
**GCP API:** Compute Engine API v1

**Core Attributes:**
- `id`: Subnet ID
- `name`: Subnet name
- `network`: Parent network reference
- `ipCidrRange`: IP address range (e.g., 10.0.0.0/24)
- `region`: Geographical region
- `gatewayAddress`: Gateway IP
- `privateIpGoogleAccess`: Boolean
- `secondaryIpRanges`: Array of secondary IP ranges

---

#### Firewall Rules (compute.firewalls)
**Node Label:** `FirewallRule`
**GCP API:** Compute Engine API v1

**Core Attributes:**
- `id`: Rule ID
- `name`: Rule name
- `network`: Parent network reference
- `direction`: INGRESS | EGRESS
- `priority`: Rule priority (0-65535)
- `allowed`: Array of {protocol, ports}
- `denied`: Array of {protocol, ports}
- `sourceRanges`: Source IP ranges
- `destinationRanges`: Destination IP ranges
- `sourceTags`: Source instance tags
- `targetTags`: Target instance tags

---

#### Routes (compute.routes)
**Node Label:** `Route`
**GCP API:** Compute Engine API v1

**Core Attributes:**
- `id`: Route ID
- `name`: Route name
- `network`: Parent network reference
- `destRange`: Destination IP range
- `priority`: Route priority
- `nextHopGateway`: Gateway for next hop
- `nextHopInstance`: Instance for next hop
- `nextHopIp`: IP address for next hop

---

### 2.2 Load Balancing

#### Load Balancers (compute.targetHttpProxies, compute.targetHttpsProxies)
**Node Label:** `LoadBalancer`
**GCP API:** Compute Engine API v1

**Types:**
- HTTP(S) Load Balancer
- TCP/UDP Load Balancer
- Internal Load Balancer

**Core Attributes:**
- `id`: Load balancer ID
- `name`: Load balancer name
- `type`: HTTP | HTTPS | TCP | UDP | INTERNAL
- `ipAddress`: External IP address
- `backendServices`: Array of backend service references
- `urlMap`: URL routing configuration

---

#### Backend Services (compute.backendServices)
**Node Label:** `BackendService`
**GCP API:** Compute Engine API v1

**Core Attributes:**
- `id`: Backend service ID
- `name`: Backend service name
- `backends`: Array of backend configurations
- `healthChecks`: Array of health check references
- `protocol`: HTTP | HTTPS | TCP | UDP
- `timeoutSec`: Request timeout
- `sessionAffinity`: Session affinity configuration

---

#### Health Checks (compute.healthChecks)
**Node Label:** `HealthCheck`
**GCP API:** Compute Engine API v1

**Core Attributes:**
- `id`: Health check ID
- `name`: Health check name
- `type`: HTTP | HTTPS | TCP | SSL
- `checkIntervalSec`: Check interval
- `timeoutSec`: Check timeout
- `healthyThreshold`: Healthy count threshold
- `unhealthyThreshold`: Unhealthy count threshold

---

### 2.3 Cloud DNS

#### Managed Zones (dns.managedZones)
**Node Label:** `DNSZone`
**GCP API:** Cloud DNS API v1

**Core Attributes:**
- `id`: Zone ID
- `name`: Zone name
- `dnsName`: DNS name (e.g., example.com.)
- `description`: Zone description
- `nameServers`: Array of authoritative name servers

---

#### Resource Record Sets (dns.resourceRecordSets)
**Node Label:** `DNSRecord`
**GCP API:** Cloud DNS API v1

**Core Attributes:**
- `name`: Record name
- `type`: A | AAAA | CNAME | MX | TXT | etc.
- `ttl`: Time to live
- `rrdatas`: Array of record data

---

### 2.4 Cloud VPN

#### VPN Gateways (compute.vpnGateways)
**Node Label:** `VPNGateway`
**GCP API:** Compute Engine API v1

**Core Attributes:**
- `id`: Gateway ID
- `name`: Gateway name
- `network`: Parent network reference
- `region`: Region location
- `ipAddress`: External IP address

---

#### VPN Tunnels (compute.vpnTunnels)
**Node Label:** `VPNTunnel`
**GCP API:** Compute Engine API v1

**Core Attributes:**
- `id`: Tunnel ID
- `name`: Tunnel name
- `status`: PROVISIONING | WAITING_FOR_FULL_CONFIG | ESTABLISHED | NO_INCOMING_PACKETS
- `peerIp`: Peer gateway IP
- `sharedSecret`: Encrypted shared secret
- `ikeVersion`: IKE protocol version

---

## 3. STORAGE RESOURCES

### 3.1 Cloud Storage

#### Buckets (storage.buckets)
**Node Label:** `StorageBucket`
**GCP API:** Cloud Storage API v1

**Core Attributes:**
- `id`: Bucket ID
- `name`: Bucket name (globally unique)
- `location`: Storage location (region or multi-region)
- `storageClass`: STANDARD | NEARLINE | COLDLINE | ARCHIVE
- `lifecycle`: Object lifecycle management rules
- `versioning`: Boolean versioning enabled
- `iamConfiguration`: IAM policy configuration
- `encryption`: Encryption configuration
- `retentionPolicy`: Data retention policy

---

#### Objects (storage.objects)
**Node Label:** `StorageObject`
**GCP API:** Cloud Storage API v1

**Core Attributes:**
- `id`: Object ID
- `name`: Object name (path)
- `bucket`: Parent bucket reference
- `size`: Object size in bytes
- `contentType`: MIME type
- `timeCreated`: ISO 8601 timestamp
- `updated`: Last update timestamp
- `generation`: Object generation number
- `metadata`: Custom metadata key-values

---

### 3.2 Persistent Disks

#### Disks (compute.disks)
**Node Label:** `PersistentDisk`
**GCP API:** Compute Engine API v1

**Core Attributes:**
- `id`: Disk ID
- `name`: Disk name
- `zone`: Zone location
- `sizeGb`: Disk size in GB
- `type`: pd-standard | pd-balanced | pd-ssd | pd-extreme
- `status`: CREATING | RESTORING | READY | DELETING | FAILED
- `sourceSnapshot`: Source snapshot reference (if created from snapshot)
- `users`: Array of attached instance references

---

#### Snapshots (compute.snapshots)
**Node Label:** `DiskSnapshot`
**GCP API:** Compute Engine API v1

**Core Attributes:**
- `id`: Snapshot ID
- `name`: Snapshot name
- `sourceDisk`: Source disk reference
- `diskSizeGb`: Snapshot size
- `storageBytes`: Actual storage used
- `creationTimestamp`: ISO 8601 timestamp
- `status`: CREATING | UPLOADING | READY | DELETING | FAILED

---

### 3.3 Filestore

#### Instances (file.instances)
**Node Label:** `FilestoreInstance`
**GCP API:** Cloud Filestore API v1

**Core Attributes:**
- `id`: Instance ID
- `name`: Instance name
- `tier`: STANDARD | PREMIUM | ENTERPRISE
- `capacityGb`: Storage capacity
- `fileShares`: Array of file share configurations
- `networks`: Array of network configurations
- `status`: CREATING | READY | DELETING | ERROR

---

## 4. DATABASE RESOURCES

### 4.1 Cloud SQL

#### Instances (sqladmin.instances)
**Node Label:** `CloudSQLInstance`
**GCP API:** Cloud SQL Admin API v1beta4

**Core Attributes:**
- `id`: Instance ID
- `name`: Instance name
- `databaseVersion`: MYSQL_5_7 | MYSQL_8_0 | POSTGRES_13 | POSTGRES_14 | SQLSERVER_2019
- `region`: Region location
- `tier`: Machine type (e.g., db-n1-standard-1)
- `state`: RUNNABLE | SUSPENDED | PENDING_CREATE | MAINTENANCE | FAILED
- `ipAddresses`: Array of IP configurations
- `backupConfiguration`: Backup settings
- `replicaConfiguration`: Replication settings

---

#### Databases (sqladmin.databases)
**Node Label:** `CloudSQLDatabase`
**GCP API:** Cloud SQL Admin API v1beta4

**Core Attributes:**
- `name`: Database name
- `instance`: Parent instance reference
- `charset`: Character set
- `collation`: Collation setting

---

### 4.2 Cloud Spanner

#### Instances (spanner.instances)
**Node Label:** `SpannerInstance`
**GCP API:** Cloud Spanner API v1

**Core Attributes:**
- `id`: Instance ID
- `name`: Instance name
- `config`: Regional or multi-regional configuration
- `displayName`: Display name
- `nodeCount`: Number of nodes
- `state`: CREATING | READY

---

#### Databases (spanner.databases)
**Node Label:** `SpannerDatabase`
**GCP API:** Cloud Spanner API v1

**Core Attributes:**
- `name`: Database name
- `instance`: Parent instance reference
- `state`: CREATING | READY | READY_OPTIMIZING

---

### 4.3 Cloud Bigtable

#### Instances (bigtableadmin.instances)
**Node Label:** `BigtableInstance`
**GCP API:** Bigtable Admin API v2

**Core Attributes:**
- `id`: Instance ID
- `name`: Instance name
- `displayName`: Display name
- `type`: PRODUCTION | DEVELOPMENT
- `state`: CREATING | READY

---

#### Clusters (bigtableadmin.clusters)
**Node Label:** `BigtableCluster`
**GCP API:** Bigtable Admin API v2

**Core Attributes:**
- `id`: Cluster ID
- `name`: Cluster name
- `location`: Zone location
- `serveNodes`: Number of nodes
- `defaultStorageType`: SSD | HDD
- `state`: CREATING | READY | RESIZING

---

### 4.4 Firestore

#### Databases (firestore.databases)
**Node Label:** `FirestoreDatabase`
**GCP API:** Firestore API v1

**Core Attributes:**
- `name`: Database name
- `locationId`: Database location
- `type`: FIRESTORE_NATIVE | DATASTORE_MODE
- `concurrencyMode`: OPTIMISTIC | PESSIMISTIC

---

## 5. IAM & SECURITY RESOURCES

### 5.1 Identity and Access Management

#### Service Accounts (iam.serviceAccounts)
**Node Label:** `ServiceAccount`
**GCP API:** IAM API v1

**Core Attributes:**
- `id`: Unique ID
- `email`: Service account email
- `displayName`: Display name
- `projectId`: Parent project
- `oauth2ClientId`: OAuth2 client ID
- `disabled`: Boolean disabled status

---

#### IAM Policies (cloudresourcemanager.projects.getIamPolicy)
**Node Label:** `IAMPolicy`
**GCP API:** Cloud Resource Manager API v1

**Core Attributes:**
- `resourceId`: Associated resource ID
- `resourceType`: Project | Folder | Organization
- `bindings`: Array of {role, members}
- `etag`: Policy version

---

#### Roles (iam.roles)
**Node Label:** `IAMRole`
**GCP API:** IAM API v1

**Types:**
- Predefined Roles
- Custom Roles

**Core Attributes:**
- `name`: Role name
- `title`: Role title
- `description`: Role description
- `includedPermissions`: Array of permissions
- `stage`: ALPHA | BETA | GA | DEPRECATED
- `deleted`: Boolean

---

### 5.2 Secret Manager

#### Secrets (secretmanager.secrets)
**Node Label:** `Secret`
**GCP API:** Secret Manager API v1

**Core Attributes:**
- `name`: Secret name
- `replication`: Replication policy
- `labels`: Resource labels
- `createTime`: ISO 8601 timestamp

---

#### Secret Versions (secretmanager.versions)
**Node Label:** `SecretVersion`
**GCP API:** Secret Manager API v1

**Core Attributes:**
- `name`: Version name
- `state`: ENABLED | DISABLED | DESTROYED
- `createTime`: ISO 8601 timestamp

---

### 5.3 Cloud KMS

#### Key Rings (cloudkms.keyRings)
**Node Label:** `KMSKeyRing`
**GCP API:** Cloud KMS API v1

**Core Attributes:**
- `name`: Key ring name
- `location`: Location
- `createTime`: ISO 8601 timestamp

---

#### Crypto Keys (cloudkms.cryptoKeys)
**Node Label:** `CryptoKey`
**GCP API:** Cloud KMS API v1

**Core Attributes:**
- `name`: Key name
- `purpose`: ENCRYPT_DECRYPT | ASYMMETRIC_SIGN | ASYMMETRIC_DECRYPT
- `versionTemplate`: Algorithm and protection level
- `rotationSchedule`: Automatic rotation configuration

---

## 6. APPLICATION SERVICES

### 6.1 Pub/Sub

#### Topics (pubsub.topics)
**Node Label:** `PubSubTopic`
**GCP API:** Pub/Sub API v1

**Core Attributes:**
- `name`: Topic name
- `labels`: Resource labels
- `messageStoragePolicy`: Storage location policy
- `kmsKeyName`: Encryption key reference

---

#### Subscriptions (pubsub.subscriptions)
**Node Label:** `PubSubSubscription`
**GCP API:** Pub/Sub API v1

**Core Attributes:**
- `name`: Subscription name
- `topic`: Parent topic reference
- `ackDeadlineSeconds`: Acknowledgment deadline
- `retainAckedMessages`: Boolean
- `messageRetentionDuration`: Retention duration
- `filter`: Message filter expression
- `deadLetterPolicy`: Dead letter queue configuration

---

### 6.2 Cloud Scheduler

#### Jobs (cloudscheduler.jobs)
**Node Label:** `SchedulerJob`
**GCP API:** Cloud Scheduler API v1

**Core Attributes:**
- `name`: Job name
- `schedule`: Cron schedule expression
- `timeZone`: Time zone
- `target`: HTTP, Pub/Sub, or App Engine target
- `state`: ENABLED | PAUSED | DISABLED
- `retryConfig`: Retry configuration

---

### 6.3 Cloud Tasks

#### Queues (cloudtasks.queues)
**Node Label:** `TaskQueue`
**GCP API:** Cloud Tasks API v2

**Core Attributes:**
- `name`: Queue name
- `state`: RUNNING | PAUSED | DISABLED
- `rateLimits`: Rate limiting configuration
- `retryConfig`: Retry configuration

---

## 7. MONITORING & LOGGING

### 7.1 Cloud Monitoring

#### Alert Policies (monitoring.alertPolicies)
**Node Label:** `AlertPolicy`
**GCP API:** Cloud Monitoring API v3

**Core Attributes:**
- `name`: Policy name
- `displayName`: Display name
- `enabled`: Boolean
- `conditions`: Array of alert conditions
- `notificationChannels`: Array of notification channel references

---

#### Notification Channels (monitoring.notificationChannels)
**Node Label:** `NotificationChannel`
**GCP API:** Cloud Monitoring API v3

**Core Attributes:**
- `name`: Channel name
- `type`: email | slack | pagerduty | webhook | sms
- `displayName`: Display name
- `enabled`: Boolean
- `labels`: Configuration labels

---

### 7.2 Cloud Logging

#### Log Sinks (logging.sinks)
**Node Label:** `LogSink`
**GCP API:** Cloud Logging API v2

**Core Attributes:**
- `name`: Sink name
- `destination`: Destination resource (Pub/Sub, Storage, BigQuery)
- `filter`: Log filter expression
- `outputVersionFormat`: V1 | V2

---

## 8. PROJECT & ORGANIZATION RESOURCES

### 8.1 Resource Hierarchy

#### Organizations (cloudresourcemanager.organizations)
**Node Label:** `Organization`
**GCP API:** Cloud Resource Manager API v1

**Core Attributes:**
- `id`: Organization ID
- `displayName`: Organization name
- `lifecycleState`: ACTIVE | DELETE_REQUESTED

---

#### Folders (cloudresourcemanager.folders)
**Node Label:** `Folder`
**GCP API:** Cloud Resource Manager API v2

**Core Attributes:**
- `id`: Folder ID
- `displayName`: Folder name
- `parent`: Parent resource reference
- `lifecycleState`: ACTIVE | DELETE_REQUESTED

---

#### Projects (cloudresourcemanager.projects)
**Node Label:** `Project`
**GCP API:** Cloud Resource Manager API v1

**Core Attributes:**
- `projectId`: Project ID (immutable)
- `projectNumber`: Project number
- `name`: Project name
- `parent`: Parent resource reference (folder or organization)
- `lifecycleState`: ACTIVE | DELETE_REQUESTED | DELETE_IN_PROGRESS
- `createTime`: ISO 8601 timestamp
- `labels`: Resource labels

---

## 9. CROSS-CUTTING CONCERNS

### 9.1 Labels and Tags

All GCP resources support labels (key-value pairs) for organization and billing tracking.

**Standard Label Properties:**
- `labels`: Map of string key-value pairs
- `labelFingerprint`: Fingerprint for optimistic locking

---

### 9.2 Time-Dimension Properties

For historical state tracking, all nodes should include:

**Temporal Properties:**
- `createdAt`: Resource creation timestamp
- `updatedAt`: Last update timestamp
- `deletedAt`: Soft deletion timestamp (null if active)
- `snapshotTimestamp`: Digital twin snapshot time

---

### 9.3 Metadata and Annotations

**Common Metadata:**
- `description`: Human-readable description
- `annotations`: Arbitrary key-value metadata
- `fingerprint`: Optimistic locking fingerprint
- `selfLink`: Full GCP resource URL

---

## 10. RESOURCE RELATIONSHIPS

### 10.1 Common Relationship Types

#### Ownership Relationships
- `(:Project)-[:CONTAINS]->(:Resource)` - Project contains resources
- `(:Folder)-[:CONTAINS]->(:Project)` - Folder contains projects
- `(:Organization)-[:CONTAINS]->(:Folder)` - Organization contains folders

#### Network Relationships
- `(:ComputeInstance)-[:ATTACHED_TO]->(:Subnet)` - Instance attached to subnet
- `(:Subnet)-[:PART_OF]->(:VPCNetwork)` - Subnet part of VPC
- `(:FirewallRule)-[:APPLIES_TO]->(:VPCNetwork)` - Firewall rules apply to VPC

#### Storage Relationships
- `(:ComputeInstance)-[:USES_DISK]->(:PersistentDisk)` - Instance uses disk
- `(:PersistentDisk)-[:HAS_SNAPSHOT]->(:DiskSnapshot)` - Disk has snapshot
- `(:ComputeInstance)-[:WRITES_TO]->(:StorageBucket)` - Instance writes to bucket

#### IAM Relationships
- `(:ComputeInstance)-[:HAS_SERVICE_ACCOUNT]->(:ServiceAccount)` - Instance has service account
- `(:ServiceAccount)-[:HAS_ROLE]->(:IAMRole)` - Service account has role
- `(:IAMPolicy)-[:GRANTS_ROLE]->(:IAMRole)` - Policy grants role

#### Load Balancing Relationships
- `(:LoadBalancer)-[:ROUTES_TO]->(:BackendService)` - LB routes to backend
- `(:BackendService)-[:TARGETS]->(:InstanceGroup)` - Backend targets instance group
- `(:HealthCheck)-[:MONITORS]->(:BackendService)` - Health check monitors backend

#### Dependencies
- `(:Resource)-[:DEPENDS_ON]->(:Resource)` - Generic dependency
- `(:ComputeInstance)-[:DEPENDS_ON]->(:VPCNetwork)` - Instance depends on network
- `(:CloudFunction)-[:DEPENDS_ON]->(:PubSubTopic)` - Function depends on topic

#### Monitoring Relationships
- `(:AlertPolicy)-[:MONITORS]->(:Resource)` - Alert policy monitors resource
- `(:AlertPolicy)-[:NOTIFIES]->(:NotificationChannel)` - Policy notifies channel
- `(:LogSink)-[:EXPORTS_FROM]->(:Project)` - Sink exports from project

---

## 11. API ACCESS SUMMARY

### Primary GCP APIs for Resource Access

| Resource Category | API Name | Version | Authentication |
|------------------|----------|---------|----------------|
| Compute Engine | Compute Engine API | v1 | OAuth 2.0 |
| Kubernetes Engine | Kubernetes Engine API | v1 | OAuth 2.0 |
| Cloud Functions | Cloud Functions API | v1 | OAuth 2.0 |
| Cloud Run | Cloud Run API | v1 | OAuth 2.0 |
| Cloud Storage | Cloud Storage API | v1 | OAuth 2.0 |
| Cloud SQL | Cloud SQL Admin API | v1beta4 | OAuth 2.0 |
| Cloud Spanner | Cloud Spanner API | v1 | OAuth 2.0 |
| Cloud Bigtable | Bigtable Admin API | v2 | OAuth 2.0 |
| Firestore | Firestore API | v1 | OAuth 2.0 |
| VPC/Networking | Compute Engine API | v1 | OAuth 2.0 |
| Cloud DNS | Cloud DNS API | v1 | OAuth 2.0 |
| IAM | IAM API | v1 | OAuth 2.0 |
| Secret Manager | Secret Manager API | v1 | OAuth 2.0 |
| Cloud KMS | Cloud KMS API | v1 | OAuth 2.0 |
| Pub/Sub | Pub/Sub API | v1 | OAuth 2.0 |
| Cloud Scheduler | Cloud Scheduler API | v1 | OAuth 2.0 |
| Cloud Tasks | Cloud Tasks API | v2 | OAuth 2.0 |
| Cloud Monitoring | Cloud Monitoring API | v3 | OAuth 2.0 |
| Cloud Logging | Cloud Logging API | v2 | OAuth 2.0 |
| Resource Manager | Cloud Resource Manager API | v1/v2 | OAuth 2.0 |

---

## 12. HIERARCHICAL CATEGORIZATION

```
GCP Resources
├── Compute
│   ├── Compute Engine (VMs, Templates, Groups, Autoscalers)
│   ├── Kubernetes Engine (Clusters, Node Pools)
│   ├── Cloud Functions
│   └── Cloud Run (Services, Revisions)
├── Networking
│   ├── VPC (Networks, Subnets, Firewall Rules, Routes)
│   ├── Load Balancing (Load Balancers, Backend Services, Health Checks)
│   ├── Cloud DNS (Zones, Records)
│   └── Cloud VPN (Gateways, Tunnels)
├── Storage
│   ├── Cloud Storage (Buckets, Objects)
│   ├── Persistent Disks (Disks, Snapshots)
│   └── Filestore (Instances)
├── Databases
│   ├── Cloud SQL (Instances, Databases)
│   ├── Cloud Spanner (Instances, Databases)
│   ├── Cloud Bigtable (Instances, Clusters)
│   └── Firestore (Databases)
├── IAM & Security
│   ├── IAM (Service Accounts, Policies, Roles)
│   ├── Secret Manager (Secrets, Versions)
│   └── Cloud KMS (Key Rings, Crypto Keys)
├── Application Services
│   ├── Pub/Sub (Topics, Subscriptions)
│   ├── Cloud Scheduler (Jobs)
│   └── Cloud Tasks (Queues)
├── Monitoring & Logging
│   ├── Cloud Monitoring (Alert Policies, Notification Channels)
│   └── Cloud Logging (Log Sinks)
└── Resource Hierarchy
    ├── Organizations
    ├── Folders
    └── Projects
```

---

## 13. NEXT STEPS

This inventory provides the foundation for:
1. **Subtask 1.2**: Defining Neo4j node properties and labels schema
2. **Subtask 1.3**: Designing relationship types and properties
3. **Subtask 1.4**: Implementing constraints and indexes
4. **Subtask 1.5**: Creating schema documentation and visualization

### Validation Checklist
- ✅ Comprehensive list of GCP resources across all major categories
- ✅ Hierarchical categorization structure
- ✅ Resource-specific attributes and metadata documented
- ✅ Lifecycle states identified for stateful resources
- ✅ GCP API access information provided for each resource type
- ✅ Relationship types between resources defined
- ✅ Cross-cutting concerns (labels, temporal properties) documented

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-06  
**Author:** Digital Twin Agent Team

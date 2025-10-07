"""
Analysis Queries Module

This module provides advanced analysis capabilities for the GCP digital twin graph,
including cost analysis, bottleneck identification, network topology analysis,
security issue detection, and optimization recommendations.

Author: GCP Digital Twin Agent System
Date: 2025-01-06
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from .base_query import BaseQuery, QueryResult, track_query_performance
from ..monitoring import get_logger, get_metrics

logger = get_logger("AnalysisQueries")
metrics = get_metrics()


class AnalysisQueries(BaseQuery):
    """
    Query class for analysis and optimization operations in the GCP digital twin graph.
    
    This class provides methods for:
    - Cost analysis and aggregation
    - Bottleneck identification
    - Network topology analysis
    - Security configuration analysis
    - Optimization recommendations
    
    Examples:
        >>> from ingestion_pipeline.graph_queries import get_analysis_queries
        >>> queries = get_analysis_queries()
        >>> 
        >>> # Analyze costs for a project
        >>> costs = queries.analyze_costs("my-project")
        >>> print(f"Total monthly cost: ${costs['total_monthly_cost']}")
        >>> 
        >>> # Identify bottlenecks
        >>> bottlenecks = queries.identify_bottlenecks("my-project")
        >>> 
        >>> # Get optimization suggestions
        >>> suggestions = queries.suggest_optimizations("my-project")
    """
    
    def __init__(self, connection_manager=None, monitoring_enabled: bool = True):
        """
        Initialize AnalysisQueries.
        
        Args:
            connection_manager: Optional connection manager instance
            monitoring_enabled: Whether to enable monitoring (default: True)
        """
        super().__init__(connection_manager, monitoring_enabled)
        logger.info("AnalysisQueries initialized")
    
    @track_query_performance("analyze_costs")
    def analyze_costs(
        self,
        project_id: str,
        time_window_days: int = 30,
        group_by: str = "resource_type"
    ) -> Dict[str, Any]:
        """
        Analyze and aggregate costs for resources in a project.
        
        Note: This assumes cost data is stored in resource properties.
        Actual implementation may need to integrate with Cloud Billing API.
        
        Args:
            project_id: GCP project ID
            time_window_days: Number of days to analyze (default: 30)
            group_by: Grouping strategy - "resource_type", "zone", "label" (default: "resource_type")
            
        Returns:
            Dictionary containing cost analysis with totals and breakdowns
            
        Raises:
            QueryValidationError: If parameters are invalid
            QueryExecutionError: If query execution fails
        """
        self._validate_required_params(project_id=project_id)
        self._validate_positive_int(time_window_days, "time_window_days")
        
        if group_by not in ["resource_type", "zone", "label"]:
            raise ValueError(f"Invalid group_by: {group_by}. Must be 'resource_type', 'zone', or 'label'")
        
        # Query for resources with cost data
        if group_by == "resource_type":
            query = """
            MATCH (r {project_id: $project_id})
            WHERE r.estimated_monthly_cost IS NOT NULL
            RETURN 
                labels(r)[0] as resource_type,
                count(r) as resource_count,
                sum(toFloat(r.estimated_monthly_cost)) as total_cost,
                avg(toFloat(r.estimated_monthly_cost)) as avg_cost,
                min(toFloat(r.estimated_monthly_cost)) as min_cost,
                max(toFloat(r.estimated_monthly_cost)) as max_cost
            ORDER BY total_cost DESC
            """
        elif group_by == "zone":
            query = """
            MATCH (r {project_id: $project_id})
            WHERE r.estimated_monthly_cost IS NOT NULL AND r.zone IS NOT NULL
            RETURN 
                r.zone as zone,
                count(r) as resource_count,
                sum(toFloat(r.estimated_monthly_cost)) as total_cost,
                avg(toFloat(r.estimated_monthly_cost)) as avg_cost
            ORDER BY total_cost DESC
            """
        else:  # label
            query = """
            MATCH (r {project_id: $project_id})
            WHERE r.estimated_monthly_cost IS NOT NULL
            UNWIND keys(r) as key
            WITH r, key
            WHERE key STARTS WITH 'label_'
            RETURN 
                key as label_key,
                r[key] as label_value,
                count(r) as resource_count,
                sum(toFloat(r.estimated_monthly_cost)) as total_cost
            ORDER BY total_cost DESC
            LIMIT 20
            """
        
        result = self._execute_query(
            query=query,
            parameters={"project_id": project_id},
            query_type="analyze_costs"
        )
        
        # Process results
        breakdown = []
        total_cost = 0.0
        
        for record in result.records:
            if group_by == "resource_type":
                breakdown.append({
                    "resource_type": record["resource_type"],
                    "resource_count": record["resource_count"],
                    "total_cost": float(record["total_cost"]),
                    "avg_cost": float(record["avg_cost"]),
                    "min_cost": float(record["min_cost"]),
                    "max_cost": float(record["max_cost"])
                })
                total_cost += float(record["total_cost"])
            elif group_by == "zone":
                breakdown.append({
                    "zone": record["zone"],
                    "resource_count": record["resource_count"],
                    "total_cost": float(record["total_cost"]),
                    "avg_cost": float(record["avg_cost"])
                })
                total_cost += float(record["total_cost"])
            else:  # label
                breakdown.append({
                    "label": f"{record['label_key']}={record['label_value']}",
                    "resource_count": record["resource_count"],
                    "total_cost": float(record["total_cost"])
                })
                total_cost += float(record["total_cost"])
        
        analysis = {
            "project_id": project_id,
            "time_window_days": time_window_days,
            "group_by": group_by,
            "total_monthly_cost": total_cost,
            "breakdown": breakdown,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Cost analysis for {project_id}: ${total_cost:.2f}/month, "
            f"{len(breakdown)} groups"
        )
        
        return analysis
    
    @track_query_performance("identify_bottlenecks")
    def identify_bottlenecks(
        self,
        project_id: Optional[str] = None,
        min_dependency_count: int = 5,
        limit: int = 20
    ) -> QueryResult:
        """
        Identify resources that are potential bottlenecks due to high dependency counts.
        
        A bottleneck is a resource that many other resources depend on, making it
        a critical point of failure.
        
        Args:
            project_id: Optional filter by project ID
            min_dependency_count: Minimum number of dependencies to be considered a bottleneck
            limit: Maximum number of bottlenecks to return
            
        Returns:
            QueryResult containing list of bottleneck resources with dependency counts
            
        Raises:
            QueryExecutionError: If query execution fails
        """
        self._validate_positive_int(min_dependency_count, "min_dependency_count")
        self._validate_positive_int(limit, "limit")
        
        project_filter = "WHERE r.project_id = $project_id" if project_id else ""
        
        query = f"""
        MATCH (r)<-[dep:DEPENDS_ON]-(dependent)
        {project_filter}
        WITH r, count(dep) as dependency_count, collect(distinct dependent.id) as dependent_ids
        WHERE dependency_count >= $min_dependency_count
        RETURN 
            r.id as resource_id,
            labels(r)[0] as resource_type,
            r.name as resource_name,
            r.status as status,
            dependency_count,
            dependent_ids
        ORDER BY dependency_count DESC
        LIMIT $limit
        """
        
        parameters = {
            "min_dependency_count": min_dependency_count,
            "limit": limit
        }
        if project_id:
            parameters["project_id"] = project_id
        
        result = self._execute_query(
            query=query,
            parameters=parameters,
            query_type="identify_bottlenecks"
        )
        
        bottlenecks = []
        for record in result.records:
            bottlenecks.append({
                "resource_id": record["resource_id"],
                "resource_type": record["resource_type"],
                "resource_name": record["resource_name"],
                "status": record["status"],
                "dependency_count": record["dependency_count"],
                "dependent_resource_count": len(record["dependent_ids"]),
                "severity": self._calculate_bottleneck_severity(record["dependency_count"]),
                "recommendation": self._generate_bottleneck_recommendation(
                    record["resource_type"],
                    record["dependency_count"]
                )
            })
        
        logger.warning(
            f"Identified {len(bottlenecks)} potential bottlenecks in "
            f"{'project ' + project_id if project_id else 'all projects'}"
        )
        
        return QueryResult(
            data=bottlenecks,
            query_type="identify_bottlenecks",
            record_count=len(bottlenecks),
            execution_time=result.execution_time,
            timestamp=result.timestamp
        )
    
    @track_query_performance("analyze_network_topology")
    def analyze_network_topology(
        self,
        vpc_id: str,
        include_subnets: bool = True,
        include_routes: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze network topology for a specific VPC.
        
        Args:
            vpc_id: VPC network ID
            include_subnets: Whether to include subnet analysis
            include_routes: Whether to include routing analysis
            
        Returns:
            Dictionary containing network topology analysis
            
        Raises:
            QueryValidationError: If required parameters are missing
            QueryExecutionError: If query execution fails
        """
        self._validate_required_params(vpc_id=vpc_id)
        
        # Get VPC basic info
        vpc_query = """
        MATCH (vpc:VPCNetwork {id: $vpc_id})
        RETURN 
            vpc.id as vpc_id,
            vpc.name as vpc_name,
            vpc.project_id as project_id,
            vpc.auto_create_subnetworks as auto_create_subnetworks
        """
        
        vpc_result = self._execute_query(
            query=vpc_query,
            parameters={"vpc_id": vpc_id},
            query_type="analyze_network_topology_vpc"
        )
        
        if not vpc_result.records:
            logger.warning(f"VPC {vpc_id} not found")
            return {"error": f"VPC {vpc_id} not found"}
        
        vpc_info = dict(vpc_result.records[0])
        topology = {
            "vpc": vpc_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Get connected resources
        connected_query = """
        MATCH (vpc:VPCNetwork {id: $vpc_id})<-[r:IN_NETWORK|USES_NETWORK]-(resource)
        RETURN 
            labels(resource)[0] as resource_type,
            count(resource) as count
        ORDER BY count DESC
        """
        
        connected_result = self._execute_query(
            query=connected_query,
            parameters={"vpc_id": vpc_id},
            query_type="analyze_network_topology_connected"
        )
        
        topology["connected_resources"] = [
            {"resource_type": r["resource_type"], "count": r["count"]}
            for r in connected_result.records
        ]
        
        # Analyze subnets if requested
        if include_subnets:
            subnet_query = """
            MATCH (vpc:VPCNetwork {id: $vpc_id})<-[:IN_NETWORK]-(subnet:Subnetwork)
            OPTIONAL MATCH (subnet)<-[:IN_SUBNET]-(instance)
            RETURN 
                subnet.id as subnet_id,
                subnet.name as subnet_name,
                subnet.ip_cidr_range as cidr_range,
                subnet.region as region,
                count(distinct instance) as instance_count
            """
            
            subnet_result = self._execute_query(
                query=subnet_query,
                parameters={"vpc_id": vpc_id},
                query_type="analyze_network_topology_subnets"
            )
            
            topology["subnets"] = [
                {
                    "subnet_id": r["subnet_id"],
                    "subnet_name": r["subnet_name"],
                    "cidr_range": r["cidr_range"],
                    "region": r["region"],
                    "instance_count": r["instance_count"]
                }
                for r in subnet_result.records
            ]
        
        # Analyze routes if requested
        if include_routes:
            route_query = """
            MATCH (vpc:VPCNetwork {id: $vpc_id})<-[:IN_NETWORK]-(route:Route)
            RETURN 
                route.id as route_id,
                route.name as route_name,
                route.dest_range as dest_range,
                route.priority as priority,
                route.next_hop_gateway as next_hop
            ORDER BY route.priority
            """
            
            route_result = self._execute_query(
                query=route_query,
                parameters={"vpc_id": vpc_id},
                query_type="analyze_network_topology_routes"
            )
            
            topology["routes"] = [
                {
                    "route_id": r["route_id"],
                    "route_name": r["route_name"],
                    "dest_range": r["dest_range"],
                    "priority": r["priority"],
                    "next_hop": r["next_hop"]
                }
                for r in route_result.records
            ]
        
        logger.info(f"Analyzed network topology for VPC {vpc_id}")
        
        return topology
    
    @track_query_performance("find_security_issues")
    def find_security_issues(
        self,
        project_id: str,
        check_types: Optional[List[str]] = None
    ) -> QueryResult:
        """
        Identify potential security configuration issues in the project.
        
        Args:
            project_id: GCP project ID
            check_types: Optional list of check types to run. Options:
                        - "public_ips": Resources with public IP addresses
                        - "open_firewall": Firewall rules allowing broad access
                        - "unencrypted": Unencrypted storage resources
                        - "default_sa": Resources using default service accounts
                        If None, runs all checks.
            
        Returns:
            QueryResult containing list of security issues
            
        Raises:
            QueryValidationError: If parameters are invalid
            QueryExecutionError: If query execution fails
        """
        self._validate_required_params(project_id=project_id)
        
        if check_types is None:
            check_types = ["public_ips", "open_firewall", "unencrypted", "default_sa"]
        
        issues = []
        
        # Check 1: Resources with public IPs
        if "public_ips" in check_types:
            public_ip_query = """
            MATCH (r {project_id: $project_id})
            WHERE r.external_ip IS NOT NULL OR r.public_ip IS NOT NULL
            RETURN 
                r.id as resource_id,
                labels(r)[0] as resource_type,
                r.name as resource_name,
                coalesce(r.external_ip, r.public_ip) as public_ip
            """
            
            result = self._execute_query(
                query=public_ip_query,
                parameters={"project_id": project_id},
                query_type="find_security_issues_public_ips"
            )
            
            for record in result.records:
                issues.append({
                    "issue_type": "public_ip_exposure",
                    "severity": "medium",
                    "resource_id": record["resource_id"],
                    "resource_type": record["resource_type"],
                    "resource_name": record["resource_name"],
                    "details": f"Resource has public IP: {record['public_ip']}",
                    "recommendation": "Review if public access is necessary. Consider using Cloud NAT or private IPs."
                })
        
        # Check 2: Overly permissive firewall rules
        if "open_firewall" in check_types:
            firewall_query = """
            MATCH (fw:FirewallRule {project_id: $project_id})
            WHERE '0.0.0.0/0' IN fw.source_ranges
                AND (fw.direction = 'INGRESS' OR fw.direction IS NULL)
            RETURN 
                fw.id as firewall_id,
                fw.name as firewall_name,
                fw.allowed_ports as allowed_ports,
                fw.source_ranges as source_ranges
            """
            
            result = self._execute_query(
                query=firewall_query,
                parameters={"project_id": project_id},
                query_type="find_security_issues_firewall"
            )
            
            for record in result.records:
                issues.append({
                    "issue_type": "open_firewall_rule",
                    "severity": "high",
                    "resource_id": record["firewall_id"],
                    "resource_type": "FirewallRule",
                    "resource_name": record["firewall_name"],
                    "details": f"Firewall rule allows traffic from 0.0.0.0/0",
                    "recommendation": "Restrict source IP ranges to only necessary networks."
                })
        
        # Check 3: Unencrypted storage
        if "unencrypted" in check_types:
            storage_query = """
            MATCH (s:StorageBucket {project_id: $project_id})
            WHERE s.encryption IS NULL OR s.encryption = 'NONE'
            RETURN 
                s.id as bucket_id,
                s.name as bucket_name,
                s.location as location
            """
            
            result = self._execute_query(
                query=storage_query,
                parameters={"project_id": project_id},
                query_type="find_security_issues_encryption"
            )
            
            for record in result.records:
                issues.append({
                    "issue_type": "unencrypted_storage",
                    "severity": "high",
                    "resource_id": record["bucket_id"],
                    "resource_type": "StorageBucket",
                    "resource_name": record["bucket_name"],
                    "details": "Storage bucket is not encrypted",
                    "recommendation": "Enable encryption using Customer-Managed or Google-Managed keys."
                })
        
        # Check 4: Default service accounts
        if "default_sa" in check_types:
            sa_query = """
            MATCH (vm:VirtualMachine {project_id: $project_id})
            WHERE vm.service_account ENDS WITH '-compute@developer.gserviceaccount.com'
            RETURN 
                vm.id as vm_id,
                vm.name as vm_name,
                vm.service_account as service_account
            """
            
            result = self._execute_query(
                query=sa_query,
                parameters={"project_id": project_id},
                query_type="find_security_issues_service_accounts"
            )
            
            for record in result.records:
                issues.append({
                    "issue_type": "default_service_account",
                    "severity": "medium",
                    "resource_id": record["vm_id"],
                    "resource_type": "VirtualMachine",
                    "resource_name": record["vm_name"],
                    "details": f"Using default Compute Engine service account",
                    "recommendation": "Create custom service accounts with minimal required permissions."
                })
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        issues.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        logger.warning(f"Found {len(issues)} security issues in project {project_id}")
        
        return QueryResult(
            data=issues,
            query_type="find_security_issues",
            record_count=len(issues),
            execution_time=0,  # Combined from multiple queries
            timestamp=datetime.utcnow()
        )
    
    @track_query_performance("suggest_optimizations")
    def suggest_optimizations(
        self,
        project_id: str,
        optimization_types: Optional[List[str]] = None
    ) -> QueryResult:
        """
        Generate optimization recommendations for resources in a project.
        
        Args:
            project_id: GCP project ID
            optimization_types: Optional list of optimization types. Options:
                               - "underutilized": Underutilized resources
                               - "oversized": Oversized instances
                               - "orphaned": Orphaned resources
                               - "redundant": Redundant configurations
                               If None, runs all optimization checks.
            
        Returns:
            QueryResult containing list of optimization suggestions
            
        Raises:
            QueryValidationError: If parameters are invalid
            QueryExecutionError: If query execution fails
        """
        self._validate_required_params(project_id=project_id)
        
        if optimization_types is None:
            optimization_types = ["underutilized", "oversized", "orphaned", "redundant"]
        
        suggestions = []
        
        # Check 1: Underutilized VMs
        if "underutilized" in optimization_types:
            underutil_query = """
            MATCH (vm:VirtualMachine {project_id: $project_id, status: 'RUNNING'})
            WHERE vm.cpu_utilization < 10 OR vm.memory_utilization < 20
            RETURN 
                vm.id as vm_id,
                vm.name as vm_name,
                vm.machine_type as machine_type,
                vm.cpu_utilization as cpu_util,
                vm.memory_utilization as mem_util,
                vm.estimated_monthly_cost as cost
            LIMIT 20
            """
            
            result = self._execute_query(
                query=underutil_query,
                parameters={"project_id": project_id},
                query_type="suggest_optimizations_underutilized"
            )
            
            for record in result.records:
                suggestions.append({
                    "optimization_type": "underutilized_vm",
                    "potential_savings": "medium",
                    "resource_id": record["vm_id"],
                    "resource_name": record["vm_name"],
                    "current_config": {
                        "machine_type": record["machine_type"],
                        "cpu_utilization": record["cpu_util"],
                        "memory_utilization": record["mem_util"]
                    },
                    "recommendation": "Consider downsizing to a smaller machine type or stopping when not needed",
                    "estimated_monthly_savings": float(record["cost"]) * 0.5 if record["cost"] else None
                })
        
        # Check 2: Orphaned disks
        if "orphaned" in optimization_types:
            orphaned_query = """
            MATCH (disk:PersistentDisk {project_id: $project_id})
            WHERE NOT (disk)<-[:USES]-(VirtualMachine)
                AND disk.status = 'READY'
            RETURN 
                disk.id as disk_id,
                disk.name as disk_name,
                disk.size_gb as size_gb,
                disk.type as disk_type
            """
            
            result = self._execute_query(
                query=orphaned_query,
                parameters={"project_id": project_id},
                query_type="suggest_optimizations_orphaned"
            )
            
            for record in result.records:
                suggestions.append({
                    "optimization_type": "orphaned_disk",
                    "potential_savings": "high",
                    "resource_id": record["disk_id"],
                    "resource_name": record["disk_name"],
                    "current_config": {
                        "size_gb": record["size_gb"],
                        "disk_type": record["disk_type"]
                    },
                    "recommendation": "Delete unused disk or create snapshot and delete to reduce costs",
                    "estimated_monthly_savings": float(record["size_gb"]) * 0.04  # Rough estimate
                })
        
        # Check 3: Redundant firewall rules
        if "redundant" in optimization_types:
            redundant_fw_query = """
            MATCH (fw1:FirewallRule {project_id: $project_id})
            MATCH (fw2:FirewallRule {project_id: $project_id})
            WHERE fw1.id < fw2.id
                AND fw1.source_ranges = fw2.source_ranges
                AND fw1.allowed_ports = fw2.allowed_ports
                AND fw1.target_tags = fw2.target_tags
            RETURN 
                fw1.id as fw1_id,
                fw1.name as fw1_name,
                fw2.id as fw2_id,
                fw2.name as fw2_name
            LIMIT 10
            """
            
            result = self._execute_query(
                query=redundant_fw_query,
                parameters={"project_id": project_id},
                query_type="suggest_optimizations_redundant"
            )
            
            for record in result.records:
                suggestions.append({
                    "optimization_type": "redundant_firewall_rules",
                    "potential_savings": "low",
                    "resource_id": record["fw2_id"],
                    "resource_name": record["fw2_name"],
                    "current_config": {
                        "duplicate_of": record["fw1_name"]
                    },
                    "recommendation": f"Consolidate with rule {record['fw1_name']} to simplify management",
                    "estimated_monthly_savings": 0  # No cost savings, management overhead reduction
                })
        
        logger.info(
            f"Generated {len(suggestions)} optimization suggestions for project {project_id}"
        )
        
        return QueryResult(
            data=suggestions,
            query_type="suggest_optimizations",
            record_count=len(suggestions),
            execution_time=0,  # Combined from multiple queries
            timestamp=datetime.utcnow()
        )
    
    def _calculate_bottleneck_severity(self, dependency_count: int) -> str:
        """Calculate severity level based on dependency count."""
        if dependency_count >= 20:
            return "critical"
        elif dependency_count >= 10:
            return "high"
        elif dependency_count >= 5:
            return "medium"
        else:
            return "low"
    
    def _generate_bottleneck_recommendation(
        self,
        resource_type: str,
        dependency_count: int
    ) -> str:
        """Generate recommendation for bottleneck mitigation."""
        recommendations = {
            "VirtualMachine": "Consider load balancing or creating replicas",
            "PersistentDisk": "Review disk attachment strategy, consider regional persistent disks",
            "VPCNetwork": "Ensure network redundancy and proper subnet design",
            "StorageBucket": "Implement bucket replication for high availability"
        }
        
        base_rec = recommendations.get(
            resource_type,
            "Review dependencies and implement redundancy"
        )
        
        if dependency_count >= 20:
            return f"CRITICAL: {base_rec}. Implement immediate failover strategy."
        elif dependency_count >= 10:
            return f"HIGH PRIORITY: {base_rec}"
        else:
            return base_rec


# Module-level singleton accessor
_instance: Optional[AnalysisQueries] = None


def get_analysis_queries(
    connection_manager=None,
    monitoring_enabled: bool = True
) -> AnalysisQueries:
    """
    Get or create the singleton AnalysisQueries instance.
    
    Args:
        connection_manager: Optional connection manager instance
        monitoring_enabled: Whether to enable monitoring (default: True)
        
    Returns:
        AnalysisQueries singleton instance
    """
    global _instance
    
    if _instance is None:
        _instance = AnalysisQueries(
            connection_manager=connection_manager,
            monitoring_enabled=monitoring_enabled
        )
    
    return _instance

"""
Graph Query Usage Examples

This module demonstrates how to use the graph query system to query
the GCP Digital Twin graph database. It covers all query types:
- Resource queries
- Traversal queries
- Relationship queries
- Analysis queries
- Query caching

Author: GCP Digital Twin Agent System
Date: 2025-01-06
"""

from src.ingestion_pipeline.graph_queries import (
    get_resource_queries,
    get_traversal_queries,
    get_relationship_queries,
    get_analysis_queries,
    get_query_cache,
)
from src.ingestion_pipeline.monitoring import get_logger

logger = get_logger("GraphQueryExamples")


def example_resource_queries():
    """
    Demonstrate resource query operations.
    
    Resource queries allow you to find resources by:
    - ID (exact match)
    - Type (label)
    - Properties (filtering)
    - Text search
    - Time-based criteria
    """
    print("\n" + "="*70)
    print("RESOURCE QUERY EXAMPLES")
    print("="*70)
    
    queries = get_resource_queries()
    
    # Example 1: Find specific resource by ID
    print("\n1. Find VM by ID:")
    vm_id = "projects/my-project/zones/us-central1-a/instances/web-server-1"
    vm = queries.find_by_id(vm_id)
    if vm:
        print(f"   Found: {vm['name']} ({vm.get('_labels', [])})")
        print(f"   Status: {vm.get('status')}")
        print(f"   Zone: {vm.get('zone')}")
    else:
        print(f"   Resource not found: {vm_id}")
    
    # Example 2: Find all VMs in a project
    print("\n2. Find all VMs in project:")
    vms_result = queries.find_by_type(
        resource_type="VirtualMachine",
        project_id="my-project",
        limit=10
    )
    print(f"   Found {vms_result.record_count} VMs")
    for vm in vms_result.data[:3]:  # Show first 3
        print(f"   - {vm.get('name')} [{vm.get('status')}]")
    
    # Example 3: Find resources with specific properties
    print("\n3. Find running VMs in specific zone:")
    result = queries.find_by_properties(
        resource_type="VirtualMachine",
        properties={
            "status": "RUNNING",
            "zone": "us-central1-a"
        },
        match_mode="AND"
    )
    print(f"   Found {result.record_count} running VMs in us-central1-a")
    
    # Example 4: Search for resources by name/description
    print("\n4. Search for 'production' resources:")
    search_result = queries.search(
        search_term="production",
        resource_types=["VirtualMachine", "StorageBucket"],
        project_id="my-project"
    )
    print(f"   Found {search_result.record_count} production resources")
    
    # Example 5: Count resources
    print("\n5. Count resources by type:")
    vm_count = queries.count(
        resource_type="VirtualMachine",
        project_id="my-project"
    )
    disk_count = queries.count(
        resource_type="PersistentDisk",
        project_id="my-project"
    )
    print(f"   VMs: {vm_count}")
    print(f"   Disks: {disk_count}")
    
    # Example 6: Find recently created resources
    print("\n6. Find resources created in last 24 hours:")
    recent = queries.find_recently_created(
        hours=24,
        project_id="my-project",
        limit=10
    )
    print(f"   Found {recent.record_count} recently created resources")


def example_traversal_queries():
    """
    Demonstrate graph traversal operations.
    
    Traversal queries allow you to:
    - Find shortest paths
    - Analyze dependencies
    - Trace network paths
    - Assess impact
    - Detect circular dependencies
    """
    print("\n" + "="*70)
    print("TRAVERSAL QUERY EXAMPLES")
    print("="*70)
    
    queries = get_traversal_queries()
    
    # Example 1: Find dependencies
    print("\n1. Find all dependencies of a VM:")
    resource_id = "projects/my-project/zones/us-central1-a/instances/web-server-1"
    deps_result = queries.find_dependencies(
        resource_id=resource_id,
        max_depth=5,
        include_indirect=True
    )
    print(f"   Found {deps_result.record_count} dependencies")
    for dep in deps_result.data[:5]:
        print(f"   - {dep['resource_id']} (distance: {dep['distance']})")
    
    # Example 2: Find what depends on a resource
    print("\n2. Find resources depending on a disk:")
    disk_id = "projects/my-project/zones/us-central1-a/disks/data-disk-1"
    dependents = queries.find_dependents(
        resource_id=disk_id,
        max_depth=3
    )
    print(f"   {dependents.record_count} resources depend on this disk")
    
    # Example 3: Analyze impact if resource fails
    print("\n3. Impact analysis if disk fails:")
    impact = queries.analyze_impact(
        resource_id=disk_id,
        max_depth=5
    )
    print(f"   Total affected resources: {impact['total_affected']}")
    print(f"   Critical resources: {impact['critical_count']}")
    print(f"   Impact by type:")
    for resource_type, count in impact.get('by_type', {}).items():
        print(f"     - {resource_type}: {count}")
    
    # Example 4: Find shortest path between resources
    print("\n4. Find shortest path between VM and storage:")
    vm_id = "projects/my-project/zones/us-central1-a/instances/app-server"
    bucket_id = "projects/my-project/buckets/app-data"
    path = queries.find_shortest_path(
        source_id=vm_id,
        target_id=bucket_id
    )
    if path:
        print(f"   Path length: {path['path_length']}")
        print(f"   Path: {' -> '.join(path['node_ids'])}")
    else:
        print("   No path found")
    
    # Example 5: Detect circular dependencies
    print("\n5. Check for circular dependencies:")
    cycles = queries.find_circular_dependencies(
        project_id="my-project",
        max_cycle_length=10
    )
    if cycles.record_count > 0:
        print(f"   ⚠️  Found {cycles.record_count} circular dependency chains!")
        for cycle in cycles.data[:3]:
            print(f"   - Cycle of length {cycle['cycle_length']}")
    else:
        print("   ✓ No circular dependencies found")
    
    # Example 6: Trace network path
    print("\n6. Trace network path between VMs:")
    source_vm = "projects/my-project/zones/us-central1-a/instances/vm-1"
    target_vm = "projects/my-project/zones/us-east1-b/instances/vm-2"
    network_path = queries.trace_network_path(
        source_id=source_vm,
        target_id=target_vm
    )
    if network_path:
        print(f"   Network hops: {len(network_path.get('network_hops', []))}")
        for hop in network_path.get('network_hops', [])[:3]:
            print(f"   - {hop.get('resource_type')}: {hop.get('name')}")


def example_relationship_queries():
    """
    Demonstrate relationship analysis operations.
    
    Relationship queries allow you to:
    - Find relationships between resources
    - Query by relationship type
    - Count relationships
    - Analyze patterns
    - Find orphaned relationships
    """
    print("\n" + "="*70)
    print("RELATIONSHIP QUERY EXAMPLES")
    print("="*70)
    
    queries = get_relationship_queries()
    
    # Example 1: Find all relationships between two resources
    print("\n1. Find relationships between VM and disk:")
    vm_id = "projects/my-project/zones/us-central1-a/instances/web-server"
    disk_id = "projects/my-project/zones/us-central1-a/disks/web-disk"
    rels = queries.find_relationships_between(
        source_id=vm_id,
        target_id=disk_id
    )
    print(f"   Found {rels.record_count} relationships")
    for rel in rels.data:
        print(f"   - {rel['relationship_type']}")
    
    # Example 2: Find all DEPENDS_ON relationships
    print("\n2. Find all DEPENDS_ON relationships in project:")
    depends_on = queries.find_by_type(
        relationship_type="DEPENDS_ON",
        project_id="my-project",
        limit=10
    )
    print(f"   Found {depends_on.record_count} dependency relationships")
    
    # Example 3: Count relationships for a resource
    print("\n3. Count relationships for a VM:")
    counts = queries.count_relationships(
        resource_id=vm_id,
        direction="both"
    )
    print(f"   Incoming: {counts['incoming']}")
    print(f"   Outgoing: {counts['outgoing']}")
    print(f"   Total: {counts['total']}")
    
    # Example 4: Analyze relationship patterns
    print("\n4. Analyze relationship patterns in project:")
    patterns = queries.analyze_relationship_patterns(
        project_id="my-project",
        min_count=2
    )
    print(f"   Relationship type distribution:")
    for rel_type in patterns.data['type_distribution'][:5]:
        print(f"   - {rel_type['relationship_type']}: {rel_type['count']}")
    
    print(f"\n   Common patterns:")
    for pattern in patterns.data['pair_patterns'][:3]:
        print(f"   - {pattern['source_type']} -[{pattern['relationship_type']}]-> "
              f"{pattern['target_type']}: {pattern['count']}")
    
    # Example 5: Find orphaned relationships
    print("\n5. Check for orphaned relationships:")
    orphaned = queries.find_unused_relationships(
        project_id="my-project",
        limit=10
    )
    if orphaned.record_count > 0:
        print(f"   ⚠️  Found {orphaned.record_count} orphaned relationships")
    else:
        print("   ✓ No orphaned relationships found")
    
    # Example 6: Get relationship statistics
    print("\n6. Overall relationship statistics:")
    stats = queries.get_relationship_statistics(project_id="my-project")
    print(f"   Total relationships: {stats['total_relationships']}")
    print(f"   Unique types: {stats['unique_relationship_types']}")


def example_analysis_queries():
    """
    Demonstrate analysis and optimization operations.
    
    Analysis queries provide:
    - Cost analysis
    - Bottleneck identification
    - Network topology analysis
    - Security issue detection
    - Optimization recommendations
    """
    print("\n" + "="*70)
    print("ANALYSIS QUERY EXAMPLES")
    print("="*70)
    
    queries = get_analysis_queries()
    
    # Example 1: Analyze costs
    print("\n1. Cost analysis by resource type:")
    costs = queries.analyze_costs(
        project_id="my-project",
        group_by="resource_type"
    )
    print(f"   Total monthly cost: ${costs['total_monthly_cost']:.2f}")
    print(f"   Cost breakdown:")
    for item in costs['breakdown'][:5]:
        print(f"   - {item['resource_type']}: ${item['total_cost']:.2f} "
              f"({item['resource_count']} resources)")
    
    # Example 2: Identify bottlenecks
    print("\n2. Identify potential bottlenecks:")
    bottlenecks = queries.identify_bottlenecks(
        project_id="my-project",
        min_dependency_count=5
    )
    if bottlenecks.record_count > 0:
        print(f"   ⚠️  Found {bottlenecks.record_count} potential bottlenecks")
        for bn in bottlenecks.data[:3]:
            print(f"   - {bn['resource_name']} ({bn['resource_type']})")
            print(f"     Dependencies: {bn['dependency_count']}")
            print(f"     Severity: {bn['severity']}")
            print(f"     Recommendation: {bn['recommendation']}")
    else:
        print("   ✓ No major bottlenecks identified")
    
    # Example 3: Analyze network topology
    print("\n3. Analyze VPC network topology:")
    vpc_id = "projects/my-project/global/networks/default"
    topology = queries.analyze_network_topology(
        vpc_id=vpc_id,
        include_subnets=True,
        include_routes=True
    )
    if 'error' not in topology:
        print(f"   VPC: {topology['vpc']['vpc_name']}")
        print(f"   Connected resources: {len(topology.get('connected_resources', []))}")
        print(f"   Subnets: {len(topology.get('subnets', []))}")
        print(f"   Routes: {len(topology.get('routes', []))}")
    
    # Example 4: Find security issues
    print("\n4. Security issue scan:")
    security_issues = queries.find_security_issues(
        project_id="my-project"
    )
    if security_issues.record_count > 0:
        print(f"   ⚠️  Found {security_issues.record_count} security issues")
        
        # Group by severity
        by_severity = {}
        for issue in security_issues.data:
            severity = issue['severity']
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        for severity in ['high', 'medium', 'low']:
            count = by_severity.get(severity, 0)
            if count > 0:
                print(f"   - {severity.upper()}: {count}")
        
        # Show first high severity issue
        for issue in security_issues.data:
            if issue['severity'] == 'high':
                print(f"\n   Example (HIGH severity):")
                print(f"   - Type: {issue['issue_type']}")
                print(f"   - Resource: {issue['resource_name']}")
                print(f"   - Details: {issue['details']}")
                print(f"   - Recommendation: {issue['recommendation']}")
                break
    else:
        print("   ✓ No security issues found")
    
    # Example 5: Get optimization suggestions
    print("\n5. Optimization recommendations:")
    optimizations = queries.suggest_optimizations(
        project_id="my-project"
    )
    if optimizations.record_count > 0:
        print(f"   Found {optimizations.record_count} optimization opportunities")
        
        total_savings = sum(
            opt.get('estimated_monthly_savings', 0) or 0
            for opt in optimizations.data
        )
        print(f"   Potential monthly savings: ${total_savings:.2f}")
        
        print(f"\n   Top recommendations:")
        for opt in optimizations.data[:3]:
            print(f"   - {opt['optimization_type']}")
            print(f"     Resource: {opt['resource_name']}")
            print(f"     Recommendation: {opt['recommendation']}")
            if opt.get('estimated_monthly_savings'):
                print(f"     Savings: ${opt['estimated_monthly_savings']:.2f}/month")
    else:
        print("   ✓ Infrastructure is well-optimized")


def example_query_caching():
    """
    Demonstrate query caching functionality.
    
    Query caching provides:
    - LRU caching with TTL
    - Cache statistics
    - Manual cache management
    - Pattern-based invalidation
    """
    print("\n" + "="*70)
    print("QUERY CACHING EXAMPLES")
    print("="*70)
    
    cache = get_query_cache()
    
    # Example 1: Manual caching
    print("\n1. Manual cache operations:")
    cache.set("my-query-result", {"data": "cached value"}, ttl_seconds=300)
    cached_data = cache.get("my-query-result")
    print(f"   Cached data retrieved: {cached_data}")
    
    # Example 2: Cache statistics
    print("\n2. Cache statistics:")
    # Generate some cache activity
    queries = get_resource_queries()
    
    # These queries will be cached automatically if decorated
    for i in range(5):
        queries.count(resource_type="VirtualMachine", project_id="my-project")
    
    stats = cache.get_statistics()
    print(f"   Cache size: {stats['size']}/{stats['max_size']}")
    print(f"   Hit rate: {stats['hit_rate']:.1%}")
    print(f"   Hits: {stats['hits']}, Misses: {stats['misses']}")
    print(f"   Evictions: {stats['evictions']}")
    
    # Example 3: Cache invalidation
    print("\n3. Cache invalidation:")
    initial_size = cache.get_statistics()['size']
    
    # Invalidate specific key
    cache.invalidate("my-query-result")
    print(f"   Invalidated specific entry")
    
    # Invalidate by pattern
    invalidated_count = cache.invalidate_pattern("VirtualMachine")
    print(f"   Invalidated {invalidated_count} entries matching 'VirtualMachine'")
    
    final_size = cache.get_statistics()['size']
    print(f"   Cache size: {initial_size} → {final_size}")
    
    # Example 4: Cleanup expired entries
    print("\n4. Cleanup expired entries:")
    expired_count = cache.cleanup_expired()
    print(f"   Removed {expired_count} expired entries")
    
    # Example 5: Cache entry information
    print("\n5. Cache entry details:")
    cache.set("test-entry", "test-data", ttl_seconds=600)
    entry_info = cache.get_entry_info("test-entry")
    if entry_info:
        print(f"   Key: {entry_info['key']}")
        print(f"   Age: {entry_info['age_seconds']:.1f}s")
        print(f"   TTL: {entry_info['ttl_seconds']}s")
        print(f"   Hits: {entry_info['hits']}")


def example_combined_workflow():
    """
    Demonstrate a complete workflow using multiple query types.
    
    Scenario: Analyze a project's infrastructure and identify issues.
    """
    print("\n" + "="*70)
    print("COMBINED WORKFLOW EXAMPLE")
    print("="*70)
    print("\nScenario: Complete infrastructure analysis for 'my-project'\n")
    
    project_id = "my-project"
    
    # Step 1: Get resource inventory
    print("Step 1: Resource Inventory")
    print("-" * 40)
    resource_queries = get_resource_queries()
    
    vm_count = resource_queries.count("VirtualMachine", project_id=project_id)
    disk_count = resource_queries.count("PersistentDisk", project_id=project_id)
    bucket_count = resource_queries.count("StorageBucket", project_id=project_id)
    
    print(f"Resources in project '{project_id}':")
    print(f"  - VMs: {vm_count}")
    print(f"  - Disks: {disk_count}")
    print(f"  - Storage Buckets: {bucket_count}")
    
    # Step 2: Analyze dependencies
    print("\nStep 2: Dependency Analysis")
    print("-" * 40)
    relationship_queries = get_relationship_queries()
    
    rel_stats = relationship_queries.get_relationship_statistics(project_id)
    print(f"Total relationships: {rel_stats['total_relationships']}")
    print(f"Relationship types: {rel_stats['unique_relationship_types']}")
    
    # Step 3: Identify risks
    print("\nStep 3: Risk Assessment")
    print("-" * 40)
    analysis_queries = get_analysis_queries()
    
    bottlenecks = analysis_queries.identify_bottlenecks(project_id, min_dependency_count=3)
    print(f"Bottlenecks identified: {bottlenecks.record_count}")
    
    traversal_queries = get_traversal_queries()
    cycles = traversal_queries.find_circular_dependencies(project_id)
    print(f"Circular dependencies: {cycles.record_count}")
    
    # Step 4: Security scan
    print("\nStep 4: Security Scan")
    print("-" * 40)
    security_issues = analysis_queries.find_security_issues(project_id)
    print(f"Security issues found: {security_issues.record_count}")
    
    # Step 5: Cost analysis
    print("\nStep 5: Cost Analysis")
    print("-" * 40)
    costs = analysis_queries.analyze_costs(project_id)
    print(f"Estimated monthly cost: ${costs['total_monthly_cost']:.2f}")
    
    # Step 6: Optimization opportunities
    print("\nStep 6: Optimization Opportunities")
    print("-" * 40)
    optimizations = analysis_queries.suggest_optimizations(project_id)
    potential_savings = sum(
        opt.get('estimated_monthly_savings', 0) or 0
        for opt in optimizations.data
    )
    print(f"Optimization opportunities: {optimizations.record_count}")
    print(f"Potential monthly savings: ${potential_savings:.2f}")
    
    # Summary
    print("\n" + "="*70)
    print("ANALYSIS SUMMARY")
    print("="*70)
    print(f"✓ Project: {project_id}")
    print(f"✓ Total resources: {vm_count + disk_count + bucket_count}")
    print(f"{'⚠️ ' if bottlenecks.record_count > 0 else '✓'} Bottlenecks: {bottlenecks.record_count}")
    print(f"{'⚠️ ' if cycles.record_count > 0 else '✓'} Circular dependencies: {cycles.record_count}")
    print(f"{'⚠️ ' if security_issues.record_count > 0 else '✓'} Security issues: {security_issues.record_count}")
    print(f"✓ Monthly cost: ${costs['total_monthly_cost']:.2f}")
    print(f"✓ Optimization potential: ${potential_savings:.2f}/month")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("GRAPH QUERY SYSTEM - USAGE EXAMPLES")
    print("="*70)
    print("\nThis script demonstrates all capabilities of the graph query system.")
    print("Note: Examples use mock data and may show 'not found' results.")
    print("\nTo use with real data, ensure Neo4j is running and populated.")
    
    try:
        example_resource_queries()
        example_traversal_queries()
        example_relationship_queries()
        example_analysis_queries()
        example_query_caching()
        example_combined_workflow()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*70)
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        print(f"\n❌ Error running examples: {e}")
        print("This is expected if Neo4j is not running or not populated with data.")


if __name__ == "__main__":
    main()

"""
GCP Resource Transformation Layer

Provides transformation utilities for converting GCP API responses
into Neo4j-compatible format with relationships.

Usage Example:
    from ingestion_pipeline.transformation import TransformerFactory
    
    # Get transformer for resource type
    transformer = TransformerFactory.get_transformer('compute.instances')
    
    # Transform resource data
    result = transformer.transform(resource_data)
    
    # Access transformed node and relationships
    node = result.node
    relationships = result.relationships
"""

from .schemas import (
    # Base schemas
    BaseNodeSchema,
    BaseRelationshipSchema,
    TransformationResult,
    
    # Node schemas
    ComputeInstanceSchema,
    PersistentDiskSchema,
    VPCNetworkSchema,
    SubnetSchema,
    StorageBucketSchema,
    ServiceAccountSchema,
    
    # Relationship schemas
    AttachedToRelationship,
    UsesDiskRelationship,
    PartOfRelationship,
    
    # Enums
    InstanceStatus,
)

from .base_transformer import (
    BaseTransformer,
    TransformationError,
)

from .resource_transformers import (
    ComputeInstanceTransformer,
    PersistentDiskTransformer,
    VPCNetworkTransformer,
    SubnetTransformer,
    TransformerFactory,
)

from .relationship_extractor import (
    RelationshipExtractor,
    RelationshipMerger,
)

from .validators import (
    ResourceValidator,
    SchemaComplianceChecker,
    DataIntegrityValidator,
    ValidationError,
)

__all__ = [
    # Schemas
    'BaseNodeSchema',
    'BaseRelationshipSchema',
    'TransformationResult',
    'ComputeInstanceSchema',
    'PersistentDiskSchema',
    'VPCNetworkSchema',
    'SubnetSchema',
    'StorageBucketSchema',
    'ServiceAccountSchema',
    'AttachedToRelationship',
    'UsesDiskRelationship',
    'PartOfRelationship',
    'InstanceStatus',
    
    # Transformers
    'BaseTransformer',
    'TransformationError',
    'ComputeInstanceTransformer',
    'PersistentDiskTransformer',
    'VPCNetworkTransformer',
    'SubnetTransformer',
    'TransformerFactory',
    
    # Relationship utilities
    'RelationshipExtractor',
    'RelationshipMerger',
    
    # Validators
    'ResourceValidator',
    'SchemaComplianceChecker',
    'DataIntegrityValidator',
    'ValidationError',
]

# Version information
__version__ = '0.1.0'
__author__ = 'Digital Twin Agent Team'

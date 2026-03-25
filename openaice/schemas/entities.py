"""
Canonical entity schemas for the AI Infrastructure Control Plane.

Defines Pydantic models for the 12 canonical entity types that form the
internal state graph. All adapters must normalize their output into these
types. The policy engine reasons exclusively over these entities.

Reference: 04_canonical_state_model_and_scenario_to_state_mapping.md
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class EntityType(str, Enum):
    """The finite set of canonical entity types."""

    SERVICE = "service"
    DEPLOYMENT = "deployment"
    MODEL_REVISION = "model_revision"
    JOB = "job"
    WORKFLOW_RUN = "workflow_run"
    QUEUE = "queue"
    NODE = "node"
    GPU = "gpu"
    STORAGE_ENDPOINT = "storage_endpoint"
    NETWORK_PATH = "network_path"
    SCHEDULER_DOMAIN = "scheduler_domain"
    TENANT_SCOPE = "tenant_scope"


class SchedulerDomainType(str, Enum):
    """Known scheduler domains."""

    KUBERNETES = "kubernetes"
    SLURM = "slurm"
    RAY = "ray"
    MANAGED_CLOUD = "managed_cloud"
    UNKNOWN = "unknown"


class HealthState(str, Enum):
    """Discrete health states for entities."""

    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ServiceState(str, Enum):
    """Service operational states."""

    ACTIVE = "active"
    DEGRADED = "degraded"
    IDLE = "idle"
    SCALING = "scaling"
    UNKNOWN = "unknown"


class JobState(str, Enum):
    """Job lifecycle states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


class WorkloadType(str, Enum):
    """Scenario-aware workload classification."""

    ONLINE_INFERENCE = "online_inference"
    BATCH_INFERENCE = "batch_inference"
    DISTRIBUTED_TRAINING = "distributed_training"
    HPC_RESEARCH = "hpc_research"
    LLM_SERVING = "llm_serving"
    MANAGED_CLOUD = "managed_cloud"
    UNKNOWN = "unknown"


class CostMode(str, Enum):
    """Cost optimization intent."""

    PERFORMANCE = "performance"
    BALANCED = "balanced"
    COST_OPTIMIZED = "cost_optimized"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# State Fragment — the raw normalized unit produced by adapters
# ---------------------------------------------------------------------------


class StateFragment(BaseModel):
    """
    A single normalized observation from an adapter.

    Fragments are merged by entity_id in the state bus to produce
    complete canonical entity state.
    """

    source_type: str = Field(..., description="Adapter source, e.g. 'prometheus', 'kubernetes', 'slurm'")
    entity_type: EntityType
    entity_id: str
    observed_at: datetime
    fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value pairs to merge into the canonical entity.",
    )
    labels: dict[str, str] = Field(
        default_factory=dict,
        description="Source-specific labels for enrichment.",
    )


# ---------------------------------------------------------------------------
# Base Canonical Entity
# ---------------------------------------------------------------------------


class CanonicalEntity(BaseModel):
    """
    Base canonical entity — universal fields mandatory for every entity.

    Reference: doc 04, section 4.1
    """

    entity_type: EntityType
    entity_id: str
    source_type: str
    scheduler_domain: SchedulerDomainType = SchedulerDomainType.UNKNOWN
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    state_freshness_seconds: float = 0.0
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)

    # Operational fields (mandatory where applicable)
    health_state: HealthState = HealthState.UNKNOWN
    owner_scope: Optional[str] = None
    workload_type: WorkloadType = WorkloadType.UNKNOWN

    # Metadata
    extra: dict[str, Any] = Field(default_factory=dict)

    def update_freshness(self) -> None:
        """Recompute state_freshness_seconds from observed_at to now."""
        delta = datetime.utcnow() - self.observed_at
        self.state_freshness_seconds = delta.total_seconds()


# ---------------------------------------------------------------------------
# Typed Canonical Entities
# ---------------------------------------------------------------------------


class ServiceEntity(CanonicalEntity):
    """
    A user-facing or internally callable runtime endpoint.

    Examples: LLM inference API, embedding service, ranking endpoint.
    """

    entity_type: EntityType = EntityType.SERVICE
    service_state: ServiceState = ServiceState.UNKNOWN

    # Performance fields
    latency_p50_ms: Optional[float] = None
    latency_p95_ms: Optional[float] = None
    latency_p99_ms: Optional[float] = None
    throughput: Optional[float] = None
    queue_depth: Optional[int] = None
    error_rate: Optional[float] = None
    retry_rate: Optional[float] = None

    # Capacity
    replica_count: Optional[int] = None
    available_replicas: Optional[int] = None
    desired_replicas: Optional[int] = None


class DeploymentEntity(CanonicalEntity):
    """
    The runtime execution unit responsible for providing service capacity.

    Examples: Kubernetes Deployment, Knative revision, Ray Serve deployment.
    """

    entity_type: EntityType = EntityType.DEPLOYMENT

    # Capacity
    replica_count: Optional[int] = None
    available_replicas: Optional[int] = None
    desired_replicas: Optional[int] = None

    # Resource fields
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    gpu_utilization: Optional[float] = None


class ModelRevisionEntity(CanonicalEntity):
    """
    A specific deployed model or serving revision.

    Examples: model v1, quantized revision, canary target.
    """

    entity_type: EntityType = EntityType.MODEL_REVISION
    revision_state: Optional[str] = None
    traffic_percent: Optional[float] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None


class JobEntity(CanonicalEntity):
    """
    A schedulable execution unit with a start/end lifecycle.

    Examples: training job, batch inference job, fine-tuning run.
    """

    entity_type: EntityType = EntityType.JOB
    job_state: JobState = JobState.UNKNOWN

    # Resource fields
    gpu_utilization: Optional[float] = None
    gpu_memory_used: Optional[float] = None
    assigned_gpu_count: Optional[int] = None
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None

    # Capacity
    queue_depth: Optional[int] = None
    runtime_seconds: Optional[float] = None


class WorkflowRunEntity(CanonicalEntity):
    """
    A higher-level orchestrated unit containing one or more jobs.

    Examples: Airflow DAG run, Argo workflow, ML pipeline run.
    """

    entity_type: EntityType = EntityType.WORKFLOW_RUN
    workflow_state: Optional[str] = None
    job_ids: list[str] = Field(default_factory=list)
    total_jobs: Optional[int] = None
    completed_jobs: Optional[int] = None


class QueueEntity(CanonicalEntity):
    """
    Waiting work or buffered demand.

    Examples: request queue, pending Slurm jobs, message queue.
    """

    entity_type: EntityType = EntityType.QUEUE
    queue_depth: Optional[int] = None
    pending_jobs: Optional[int] = None
    active_jobs: Optional[int] = None
    avg_wait_seconds: Optional[float] = None


class NodeEntity(CanonicalEntity):
    """
    A compute node or worker host.

    Examples: K8s worker node, Slurm compute node, GPU VM.
    """

    entity_type: EntityType = EntityType.NODE

    # Resource fields
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    storage_io_pressure: Optional[float] = None
    network_error_rate: Optional[float] = None
    gpu_count: Optional[int] = None


class GPUEntity(CanonicalEntity):
    """
    An accelerator resource assigned to jobs, services, or revisions.

    Examples: single GPU, MIG slice.
    """

    entity_type: EntityType = EntityType.GPU

    # GPU-specific fields
    gpu_utilization: Optional[float] = None
    gpu_memory_used: Optional[float] = None
    gpu_memory_total: Optional[float] = None
    temperature_celsius: Optional[float] = None
    power_draw_watts: Optional[float] = None
    ecc_errors: Optional[int] = None
    assigned_job_id: Optional[str] = None
    assigned_service_id: Optional[str] = None


class StorageEndpointEntity(CanonicalEntity):
    """
    Object store, dataset mount, or checkpoint path dependency.

    Examples: model artifact store, checkpoint store, shared filesystem.
    """

    entity_type: EntityType = EntityType.STORAGE_ENDPOINT
    storage_type: Optional[str] = None
    io_throughput: Optional[float] = None
    io_latency_ms: Optional[float] = None
    capacity_used_pct: Optional[float] = None


class NetworkPathEntity(CanonicalEntity):
    """
    A relevant communication path affecting workload behavior.

    Examples: gateway-to-service path, node-to-node training path.
    """

    entity_type: EntityType = EntityType.NETWORK_PATH
    bandwidth_gbps: Optional[float] = None
    latency_ms: Optional[float] = None
    error_rate: Optional[float] = None
    path_endpoints: list[str] = Field(default_factory=list)


class SchedulerDomainEntity(CanonicalEntity):
    """
    The control domain responsible for workload placement.

    Examples: kubernetes, slurm, managed-cloud, ray.
    """

    entity_type: EntityType = EntityType.SCHEDULER_DOMAIN
    domain_type: SchedulerDomainType = SchedulerDomainType.UNKNOWN
    total_nodes: Optional[int] = None
    total_gpus: Optional[int] = None
    active_workloads: Optional[int] = None


class TenantScopeEntity(CanonicalEntity):
    """
    Ownership or administrative grouping for policy decisions.

    Examples: namespace, team, partition, project.
    """

    entity_type: EntityType = EntityType.TENANT_SCOPE
    scope_type: Optional[str] = None  # namespace, team, partition, project
    resource_quota: Optional[dict[str, Any]] = None
    active_workloads: Optional[int] = None


# ---------------------------------------------------------------------------
# Entity type registry — maps EntityType enum to the concrete class
# ---------------------------------------------------------------------------

ENTITY_TYPE_MAP: dict[EntityType, type[CanonicalEntity]] = {
    EntityType.SERVICE: ServiceEntity,
    EntityType.DEPLOYMENT: DeploymentEntity,
    EntityType.MODEL_REVISION: ModelRevisionEntity,
    EntityType.JOB: JobEntity,
    EntityType.WORKFLOW_RUN: WorkflowRunEntity,
    EntityType.QUEUE: QueueEntity,
    EntityType.NODE: NodeEntity,
    EntityType.GPU: GPUEntity,
    EntityType.STORAGE_ENDPOINT: StorageEndpointEntity,
    EntityType.NETWORK_PATH: NetworkPathEntity,
    EntityType.SCHEDULER_DOMAIN: SchedulerDomainEntity,
    EntityType.TENANT_SCOPE: TenantScopeEntity,
}

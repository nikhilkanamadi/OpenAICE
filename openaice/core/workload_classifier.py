"""
Workload Classifier — classifies canonical entities into scenario-aware categories.

This enables the policy engine to apply different rules to serving vs training
vs HPC workloads.

Reference: 05 (section 15)
"""

from __future__ import annotations

import logging

from openaice.schemas.entities import (
    CanonicalEntity,
    EntityType,
    SchedulerDomainType,
    ServiceEntity,
    WorkloadType,
)

logger = logging.getLogger(__name__)


class WorkloadClassifier:
    """
    Classifies canonical entities into WorkloadType categories.

    Uses a combination of entity type, scheduler domain, source type,
    and available telemetry signals to determine the workload class.
    """

    def classify(self, entity: CanonicalEntity) -> WorkloadType:
        """Classify a single entity and update its workload_type field."""
        workload_type = self._infer_workload_type(entity)
        entity.workload_type = workload_type
        return workload_type

    def classify_all(self, entities: list[CanonicalEntity]) -> None:
        """Classify all entities in place."""
        for entity in entities:
            self.classify(entity)

    def _infer_workload_type(self, entity: CanonicalEntity) -> WorkloadType:
        """
        Infer workload type from entity characteristics.

        Classification heuristics (ordered by specificity):
        1. Explicit workload_type if already set and not UNKNOWN
        2. Entity type + scheduler domain combination
        3. Signal-based heuristics
        """
        # If already classified, keep it
        if entity.workload_type != WorkloadType.UNKNOWN:
            return entity.workload_type

        # Service/Deployment in Kubernetes → online inference (or LLM serving)
        if entity.entity_type in (EntityType.SERVICE, EntityType.DEPLOYMENT):
            if entity.scheduler_domain == SchedulerDomainType.KUBERNETES:
                # Check for LLM-specific signals
                if isinstance(entity, ServiceEntity) and self._looks_like_llm(entity):
                    return WorkloadType.LLM_SERVING
                return WorkloadType.ONLINE_INFERENCE

        # Job entities
        if entity.entity_type == EntityType.JOB:
            if entity.scheduler_domain == SchedulerDomainType.SLURM:
                return WorkloadType.HPC_RESEARCH
            if entity.scheduler_domain == SchedulerDomainType.KUBERNETES:
                return WorkloadType.BATCH_INFERENCE
            return WorkloadType.DISTRIBUTED_TRAINING

        # GPU entities → classify based on scheduler domain
        if entity.entity_type == EntityType.GPU:
            if entity.scheduler_domain == SchedulerDomainType.SLURM:
                return WorkloadType.HPC_RESEARCH
            return WorkloadType.ONLINE_INFERENCE

        # Node entities → classify based on scheduler domain
        if entity.entity_type == EntityType.NODE:
            if entity.scheduler_domain == SchedulerDomainType.SLURM:
                return WorkloadType.HPC_RESEARCH
            return WorkloadType.ONLINE_INFERENCE

        # Queue entities → classify based on context
        if entity.entity_type == EntityType.QUEUE:
            if entity.scheduler_domain == SchedulerDomainType.SLURM:
                return WorkloadType.HPC_RESEARCH
            return WorkloadType.ONLINE_INFERENCE

        return WorkloadType.UNKNOWN

    def _looks_like_llm(self, entity: ServiceEntity) -> bool:
        """
        Heuristic: does this service look like an LLM serving endpoint?

        Checks for LLM-related keywords in entity_id or extra metadata.
        """
        llm_keywords = {"llm", "gpt", "chat", "completion", "embedding", "language", "token"}
        entity_id_lower = entity.entity_id.lower()

        if any(kw in entity_id_lower for kw in llm_keywords):
            return True

        # Check extra metadata
        model_name = entity.extra.get("model_name", "").lower()
        if any(kw in model_name for kw in llm_keywords):
            return True

        return False

"""
Tests for canonical entity and recommendation schemas.
"""

import pytest
from datetime import datetime

from openaice.schemas.entities import (
    CanonicalEntity,
    DeploymentEntity,
    EntityType,
    GPUEntity,
    HealthState,
    JobEntity,
    NodeEntity,
    SchedulerDomainType,
    ServiceEntity,
    StateFragment,
    WorkloadType,
)
from openaice.schemas.recommendations import (
    ActionType,
    ControlMode,
    Explanation,
    PolicyMode,
    Recommendation,
    RecommendedAction,
    RiskLevel,
)


class TestEntitySchemas:
    """Test canonical entity Pydantic models."""

    def test_service_entity_creation(self):
        svc = ServiceEntity(
            entity_id="inference-api",
            source_type="kubernetes",
            scheduler_domain=SchedulerDomainType.KUBERNETES,
            latency_p95_ms=142.0,
            queue_depth=46,
            throughput=115.0,
            confidence_score=0.91,
        )
        assert svc.entity_type == EntityType.SERVICE
        assert svc.latency_p95_ms == 142.0
        assert svc.queue_depth == 46
        assert svc.confidence_score == 0.91

    def test_job_entity_creation(self):
        job = JobEntity(
            entity_id="slurm-job-88912",
            source_type="slurm",
            scheduler_domain=SchedulerDomainType.SLURM,
            job_state="running",
            gpu_utilization=0.71,
            assigned_gpu_count=8,
            confidence_score=0.91,
        )
        assert job.entity_type == EntityType.JOB
        assert job.assigned_gpu_count == 8

    def test_gpu_entity_creation(self):
        gpu = GPUEntity(
            entity_id="gpu-node17-idx3",
            source_type="dcgm",
            scheduler_domain=SchedulerDomainType.SLURM,
            health_state=HealthState.WARNING,
            gpu_utilization=0.17,
            gpu_memory_used=0.22,
            confidence_score=0.64,
        )
        assert gpu.entity_type == EntityType.GPU
        assert gpu.health_state == HealthState.WARNING

    def test_node_entity_creation(self):
        node = NodeEntity(
            entity_id="worker-01",
            source_type="kubernetes",
            scheduler_domain=SchedulerDomainType.KUBERNETES,
            health_state=HealthState.HEALTHY,
            cpu_utilization=0.65,
        )
        assert node.entity_type == EntityType.NODE

    def test_deployment_entity_creation(self):
        dep = DeploymentEntity(
            entity_id="inference-api-dep",
            source_type="kubernetes",
            replica_count=3,
            available_replicas=2,
            desired_replicas=3,
        )
        assert dep.entity_type == EntityType.DEPLOYMENT
        assert dep.available_replicas == 2

    def test_confidence_score_validation(self):
        """Confidence must be between 0 and 1."""
        with pytest.raises(Exception):
            ServiceEntity(
                entity_id="test",
                source_type="test",
                confidence_score=1.5,
            )

    def test_state_fragment_creation(self):
        frag = StateFragment(
            source_type="prometheus",
            entity_type=EntityType.SERVICE,
            entity_id="test-svc",
            observed_at=datetime.utcnow(),
            fields={"latency_p95_ms": 142.0},
            labels={"namespace": "prod"},
        )
        assert frag.entity_type == EntityType.SERVICE
        assert frag.fields["latency_p95_ms"] == 142.0


class TestRecommendationSchemas:
    """Test recommendation and explanation schemas."""

    def test_recommendation_creation(self):
        rec = Recommendation(
            recommendation_id="rec-001",
            entity_type=EntityType.DEPLOYMENT,
            entity_id="inference-api",
            recommended_action=RecommendedAction(
                action_type=ActionType.SCALE_REPLICAS,
                parameters={"replicas": 5},
            ),
            reason="p95 latency above target",
            expected_benefit="Reduced queue wait",
            confidence_score=0.82,
            risk_level=RiskLevel.MEDIUM,
            benefit_score=0.7,
            urgency_score=0.8,
        )
        assert rec.recommended_action.action_type == ActionType.SCALE_REPLICAS
        assert rec.priority_score > 0

    def test_all_action_types_exist(self):
        """All 14 action types should be defined."""
        assert len(ActionType) == 14

    def test_explanation_creation(self):
        exp = Explanation(
            rule_id="test-rule",
            reason="Test reason",
            signals_used=["latency_p95_ms", "queue_depth"],
            objectives_impacted=["latency", "reliability"],
            confidence_score=0.85,
        )
        assert len(exp.signals_used) == 2

    def test_priority_score_calculation(self):
        """Higher benefit and urgency should produce higher priority."""
        rec_high = Recommendation(
            recommendation_id="rec-high",
            entity_type=EntityType.SERVICE,
            entity_id="svc-a",
            recommended_action=RecommendedAction(action_type=ActionType.SCALE_REPLICAS),
            reason="test",
            expected_benefit="test",
            confidence_score=0.9,
            risk_level=RiskLevel.LOW,
            benefit_score=0.9,
            urgency_score=0.9,
        )
        rec_low = Recommendation(
            recommendation_id="rec-low",
            entity_type=EntityType.SERVICE,
            entity_id="svc-b",
            recommended_action=RecommendedAction(action_type=ActionType.SCALE_REPLICAS),
            reason="test",
            expected_benefit="test",
            confidence_score=0.5,
            risk_level=RiskLevel.HIGH,
            benefit_score=0.3,
            urgency_score=0.3,
        )
        assert rec_high.priority_score > rec_low.priority_score

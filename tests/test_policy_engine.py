"""
Tests for the Policy Engine — rule evaluation and recommendation generation.
"""

from datetime import datetime
from pathlib import Path

from openaice.schemas.entities import (
    EntityType,
    HealthState,
    NodeEntity,
    SchedulerDomainType,
    ServiceEntity,
    WorkloadType,
)
from openaice.schemas.recommendations import ActionType, ControlMode, PolicyMode
from openaice.core.policy_engine import PolicyEngine


RULES_PATH = str(Path(__file__).parent.parent / "policies" / "rules.yaml")
PACK_PATH = str(Path(__file__).parent.parent / "policies" / "packs" / "balanced.yaml")


class TestPolicyEngine:
    """Test policy engine rule evaluation."""

    def _engine(self) -> PolicyEngine:
        engine = PolicyEngine(
            policy_mode=PolicyMode.BALANCED,
            control_mode=ControlMode.RECOMMEND_WITH_APPROVAL,
        )
        engine.load_rules(RULES_PATH)
        engine.load_policy_pack(PACK_PATH)
        return engine

    def test_queue_pressure_triggers_scale(self):
        """High latency + high queue should trigger scale_replicas."""
        engine = self._engine()

        svc = ServiceEntity(
            entity_id="inference-api",
            source_type="replay",
            scheduler_domain=SchedulerDomainType.KUBERNETES,
            workload_type=WorkloadType.ONLINE_INFERENCE,
            latency_p95_ms=320.0,
            queue_depth=42,
            throughput=100.0,
            confidence_score=0.91,
        )

        recs = engine.evaluate([svc])
        scale_recs = [r for r in recs if r.recommended_action.action_type == ActionType.SCALE_REPLICAS]
        assert len(scale_recs) > 0, "Should recommend scale_replicas for queue pressure"
        assert scale_recs[0].entity_id == "inference-api"

    def test_unhealthy_node_triggers_quarantine(self):
        """Degraded HPC node should trigger quarantine_node."""
        engine = self._engine()

        node = NodeEntity(
            entity_id="gpu-node-17",
            source_type="replay",
            scheduler_domain=SchedulerDomainType.SLURM,
            workload_type=WorkloadType.HPC_RESEARCH,
            health_state=HealthState.DEGRADED,
            confidence_score=0.88,
        )

        recs = engine.evaluate([node])
        quarantine_recs = [r for r in recs if r.recommended_action.action_type == ActionType.QUARANTINE_NODE]
        assert len(quarantine_recs) > 0, "Should recommend quarantine_node for degraded node"

    def test_idle_service_triggers_scale_to_zero(self):
        """Idle service should trigger enable_scale_to_zero."""
        engine = self._engine()

        svc = ServiceEntity(
            entity_id="idle-endpoint",
            source_type="replay",
            scheduler_domain=SchedulerDomainType.KUBERNETES,
            workload_type=WorkloadType.ONLINE_INFERENCE,
            throughput=0.1,
            latency_p95_ms=50.0,
            queue_depth=0,
            confidence_score=0.85,
        )

        recs = engine.evaluate([svc])
        s2z_recs = [r for r in recs if r.recommended_action.action_type == ActionType.ENABLE_SCALE_TO_ZERO]
        assert len(s2z_recs) > 0, "Should recommend scale-to-zero for idle service"

    def test_healthy_service_no_unnecessary_recs(self):
        """Healthy service with good latency should not get scale recommendations."""
        engine = self._engine()

        svc = ServiceEntity(
            entity_id="healthy-svc",
            source_type="replay",
            scheduler_domain=SchedulerDomainType.KUBERNETES,
            workload_type=WorkloadType.ONLINE_INFERENCE,
            latency_p95_ms=50.0,
            queue_depth=2,
            throughput=80.0,
            confidence_score=0.95,
        )

        recs = engine.evaluate([svc])
        scale_recs = [r for r in recs if r.recommended_action.action_type == ActionType.SCALE_REPLICAS]
        assert len(scale_recs) == 0, "Should not recommend scaling for healthy service"

    def test_low_confidence_blocks_actions(self):
        """Low confidence entities should not trigger high-risk recommendations."""
        engine = self._engine()

        node = NodeEntity(
            entity_id="uncertain-node",
            source_type="replay",
            scheduler_domain=SchedulerDomainType.SLURM,
            workload_type=WorkloadType.HPC_RESEARCH,
            health_state=HealthState.DEGRADED,
            confidence_score=0.40,  # below minimum_confidence of 0.85
        )

        recs = engine.evaluate([node])
        quarantine_recs = [r for r in recs if r.recommended_action.action_type == ActionType.QUARANTINE_NODE]
        assert len(quarantine_recs) == 0, "Should not quarantine with low confidence"

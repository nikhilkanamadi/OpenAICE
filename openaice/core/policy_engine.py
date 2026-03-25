"""
Policy Engine — evaluates YAML-defined decision rules against canonical state.

Produces typed recommendations with confidence scores: the core value
proposition of the control plane. Rules are scenario-aware and respect
the active policy mode and guardrails.

Reference: 05 (all sections)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from openaice.schemas.entities import (
    CanonicalEntity,
    EntityType,
    HealthState,
    JobEntity,
    NodeEntity,
    ServiceEntity,
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

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Decision rule model (loaded from YAML)
# ---------------------------------------------------------------------------


class DecisionRule:
    """A single decision rule parsed from YAML."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.rule_id: str = data["rule_id"]
        self.scenario_family: str = data.get("scenario_family", "any")
        self.preconditions: list[str] = data.get("preconditions", [])
        self.required_signals: list[str] = data.get("required_signals", [])
        self.action_type: ActionType = ActionType(data["recommended_action"]["action_type"])
        self.action_params: dict[str, Any] = data.get("recommended_action", {}).get("parameters", {})
        self.risk_level: RiskLevel = RiskLevel(data.get("risk_level", "medium"))
        self.minimum_confidence: float = data.get("minimum_confidence", 0.75)
        self.reason_template: str = data.get("reason", "Rule {rule_id} triggered")
        self.expected_benefit: str = data.get("expected_benefit", "Improved operational state")
        self.raw = data


# ---------------------------------------------------------------------------
# Policy Engine
# ---------------------------------------------------------------------------


class PolicyEngine:
    """
    Rule-based policy engine.

    Evaluates canonical entities against YAML-defined decision rules
    and produces Recommendation objects.
    """

    def __init__(
        self,
        policy_mode: PolicyMode = PolicyMode.BALANCED,
        control_mode: ControlMode = ControlMode.OBSERVE_ONLY,
    ) -> None:
        self.policy_mode = policy_mode
        self.control_mode = control_mode
        self.rules: list[DecisionRule] = []
        self._thresholds: dict[str, Any] = {}

    def load_rules(self, rules_path: str) -> None:
        """Load decision rules from a YAML file."""
        path = Path(rules_path)
        if not path.exists():
            logger.warning("Rules file not found: %s", rules_path)
            return

        with open(path) as f:
            data = yaml.safe_load(f)

        if not data or "rules" not in data:
            logger.warning("No rules found in %s", rules_path)
            return

        self.rules = [DecisionRule(r) for r in data["rules"]]
        self._thresholds = data.get("thresholds", {})
        logger.info("Loaded %d decision rules from %s", len(self.rules), rules_path)

    def load_policy_pack(self, pack_path: str) -> None:
        """Load a policy pack (thresholds, weights, defaults) from YAML."""
        path = Path(pack_path)
        if not path.exists():
            logger.warning("Policy pack not found: %s", pack_path)
            return

        with open(path) as f:
            data = yaml.safe_load(f)

        if data:
            self._thresholds.update(data.get("thresholds", {}))
            if "policy_mode" in data:
                self.policy_mode = PolicyMode(data["policy_mode"])
            logger.info("Loaded policy pack from %s", pack_path)

    def evaluate(self, entities: list[CanonicalEntity]) -> list[Recommendation]:
        """
        Evaluate all decision rules against all entities.

        Returns a list of recommendations, sorted by priority.
        """
        recommendations: list[Recommendation] = []

        for entity in entities:
            for rule in self.rules:
                rec = self._evaluate_rule(rule, entity)
                if rec is not None:
                    recommendations.append(rec)

        # Sort by priority score descending
        recommendations.sort(key=lambda r: r.priority_score, reverse=True)
        return recommendations

    def _evaluate_rule(
        self, rule: DecisionRule, entity: CanonicalEntity
    ) -> Recommendation | None:
        """
        Evaluate a single rule against a single entity.

        Returns a Recommendation if the rule fires, None otherwise.
        """
        # Check scenario family match
        if not self._matches_scenario(rule, entity):
            return None

        # Check preconditions
        if not self._check_preconditions(rule, entity):
            return None

        # Check required signals are present
        if not self._has_required_signals(rule, entity):
            return None

        # Evaluate rule logic
        if not self._evaluate_logic(rule, entity):
            return None

        # Check confidence threshold
        if entity.confidence_score < rule.minimum_confidence:
            logger.debug(
                "Rule %s: confidence %.2f below minimum %.2f for %s",
                rule.rule_id, entity.confidence_score, rule.minimum_confidence,
                entity.entity_id,
            )
            return None

        # Build recommendation
        return self._build_recommendation(rule, entity)

    def _matches_scenario(self, rule: DecisionRule, entity: CanonicalEntity) -> bool:
        """Check if entity's workload type matches the rule's scenario family."""
        if rule.scenario_family == "any":
            return True

        scenario_map: dict[str, list[WorkloadType]] = {
            "kubernetes_online_inference": [WorkloadType.ONLINE_INFERENCE],
            "llm_or_inference_serving": [WorkloadType.LLM_SERVING, WorkloadType.ONLINE_INFERENCE],
            "hpc_or_training": [WorkloadType.HPC_RESEARCH, WorkloadType.DISTRIBUTED_TRAINING],
            "managed_or_kserve_serving": [WorkloadType.ONLINE_INFERENCE, WorkloadType.LLM_SERVING],
            "batch": [WorkloadType.BATCH_INFERENCE],
        }

        allowed = scenario_map.get(rule.scenario_family, [])
        return entity.workload_type in allowed if allowed else True

    def _check_preconditions(self, rule: DecisionRule, entity: CanonicalEntity) -> bool:
        """Evaluate precondition expressions against entity state."""
        for precond in rule.preconditions:
            if not self._eval_precondition(precond, entity):
                return False
        return True

    def _eval_precondition(self, precond: str, entity: CanonicalEntity) -> bool:
        """Evaluate a single precondition string against entity attributes."""
        # Simple precondition evaluator
        precond = precond.strip()

        if "==" in precond:
            parts = precond.split("==")
            field = parts[0].strip()
            expected = parts[1].strip().strip("'\"")
            actual = self._get_field(entity, field)
            if actual is None:
                return False
            # Extract .value from enums for comparison
            actual_str = actual.value if hasattr(actual, "value") else str(actual)
            return actual_str == expected

        if "!=" in precond:
            parts = precond.split("!=")
            field = parts[0].strip()
            expected = parts[1].strip().strip("'\"")
            actual = self._get_field(entity, field)
            if actual is None:
                return True
            actual_str = actual.value if hasattr(actual, "value") else str(actual)
            return actual_str != expected

        return True

    def _has_required_signals(self, rule: DecisionRule, entity: CanonicalEntity) -> bool:
        """Check that all required signals are present (not None) on the entity."""
        for signal in rule.required_signals:
            val = self._get_field(entity, signal)
            if val is None:
                return False
        return True

    def _evaluate_logic(self, rule: DecisionRule, entity: CanonicalEntity) -> bool:
        """
        Evaluate rule-specific logic.

        Dispatches to specialized evaluation methods based on rule_id pattern.
        """
        rule_id = rule.rule_id

        if "scale_up" in rule_id or "queue_pressure" in rule_id:
            return self._logic_queue_pressure(entity)

        if "adjust_batching" in rule_id:
            return self._logic_low_gpu_high_queue(entity)

        if "quarantine" in rule_id or "unhealthy" in rule_id:
            return self._logic_unhealthy_node(entity)

        if "scale_to_zero" in rule_id or "idle" in rule_id:
            return self._logic_idle_service(entity)

        if "no_action" in rule_id or "low_confidence" in rule_id:
            return self._logic_low_confidence(entity)

        # Default: if preconditions and signals passed, fire the rule
        return True

    # ------------------------------------------------------------------
    # Logic evaluators
    # ------------------------------------------------------------------

    def _logic_queue_pressure(self, entity: CanonicalEntity) -> bool:
        """High latency + rising queue → needs scaling."""
        if not isinstance(entity, ServiceEntity):
            return False
        target_p95 = self._thresholds.get("target_p95_ms", 200)
        min_queue = self._thresholds.get("min_queue_depth_for_scale", 10)
        return (
            entity.latency_p95_ms is not None
            and entity.queue_depth is not None
            and entity.latency_p95_ms > target_p95
            and entity.queue_depth > min_queue
        )

    def _logic_low_gpu_high_queue(self, entity: CanonicalEntity) -> bool:
        """GPU underutilized but queue is high → adjust batching first."""
        if not isinstance(entity, ServiceEntity):
            return False
        target_gpu = self._thresholds.get("target_gpu_utilization", 0.55)
        min_queue = self._thresholds.get("min_queue_depth_for_batching", 5)

        gpu_util = getattr(entity, "gpu_utilization", None) or entity.extra.get("gpu_utilization")
        if gpu_util is None:
            return False

        return (
            entity.queue_depth is not None
            and float(gpu_util) < target_gpu
            and entity.queue_depth > min_queue
        )

    def _logic_unhealthy_node(self, entity: CanonicalEntity) -> bool:
        """Node or GPU health degraded → quarantine."""
        if isinstance(entity, NodeEntity):
            return entity.health_state in (HealthState.DEGRADED, HealthState.CRITICAL)
        return entity.health_state in (HealthState.DEGRADED, HealthState.CRITICAL)

    def _logic_idle_service(self, entity: CanonicalEntity) -> bool:
        """Service with near-zero throughput → scale to zero."""
        if not isinstance(entity, ServiceEntity):
            return False
        idle_threshold = self._thresholds.get("idle_throughput_threshold", 1.0)
        return (
            entity.throughput is not None
            and entity.throughput <= idle_threshold
        )

    def _logic_low_confidence(self, entity: CanonicalEntity) -> bool:
        """Confidence too low for any action → recommend no action."""
        no_action_threshold = self._thresholds.get("no_action_confidence_threshold", 0.5)
        return entity.confidence_score < no_action_threshold

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_field(self, entity: CanonicalEntity, field: str) -> Any:
        """Safely get a field from the entity."""
        if hasattr(entity, field):
            return getattr(entity, field)
        return entity.extra.get(field)

    def _build_recommendation(
        self, rule: DecisionRule, entity: CanonicalEntity
    ) -> Recommendation:
        """Build a Recommendation from a fired rule."""
        reason = rule.reason_template.format(
            rule_id=rule.rule_id,
            entity_id=entity.entity_id,
        )

        requires_approval = (
            self.control_mode != ControlMode.CONTROLLED_AUTO_ACT
            or rule.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        )

        # Compute scoring
        benefit_score = min(1.0 - entity.confidence_score + 0.5, 1.0)
        urgency_score = self._compute_urgency(entity)

        return Recommendation(
            recommendation_id=f"rec-{uuid.uuid4().hex[:8]}",
            entity_type=entity.entity_type,
            entity_id=entity.entity_id,
            recommended_action=RecommendedAction(
                action_type=rule.action_type,
                parameters=rule.action_params,
            ),
            reason=reason,
            expected_benefit=rule.expected_benefit,
            confidence_score=entity.confidence_score,
            risk_level=rule.risk_level,
            requires_approval=requires_approval,
            created_at=datetime.utcnow(),
            benefit_score=benefit_score,
            urgency_score=urgency_score,
        )

    def _compute_urgency(self, entity: CanonicalEntity) -> float:
        """Compute urgency score from entity state."""
        urgency = 0.5

        # Higher urgency for degraded health
        if entity.health_state == HealthState.CRITICAL:
            urgency = 1.0
        elif entity.health_state == HealthState.DEGRADED:
            urgency = 0.8

        # Higher urgency for high queue depth
        if isinstance(entity, ServiceEntity) and entity.queue_depth:
            if entity.queue_depth > 50:
                urgency = max(urgency, 0.9)
            elif entity.queue_depth > 20:
                urgency = max(urgency, 0.7)

        return urgency

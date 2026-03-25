"""
Recommendation, explanation, and action schemas.

Defines the output objects produced by the policy engine and recommender.
Every recommendation must be explainable, auditable, and carry risk metadata.

Reference: 03 (section 11-12), 05 (sections 4-8, 16)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from openaice.schemas.entities import EntityType


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ActionType(str, Enum):
    """The finite set of allowed recommendation action classes (v1)."""

    SCALE_REPLICAS = "scale_replicas"
    ADJUST_BATCHING = "adjust_batching"
    ADJUST_CONCURRENCY = "adjust_concurrency"
    SHIFT_TRAFFIC = "shift_traffic"
    CHANGE_PRIORITY_OR_QOS = "change_priority_or_qos"
    MOVE_WORKLOAD_DOMAIN = "move_workload_domain"
    QUARANTINE_NODE = "quarantine_node"
    DRAIN_OR_AVOID_NODE = "drain_or_avoid_node"
    ENABLE_SCALE_TO_ZERO = "enable_scale_to_zero"
    DISABLE_SCALE_TO_ZERO = "disable_scale_to_zero"
    INCREASE_KEEP_WARM_FLOOR = "increase_keep_warm_floor"
    DECREASE_KEEP_WARM_FLOOR = "decrease_keep_warm_floor"
    RECOMMEND_NO_ACTION = "recommend_no_action"
    ROLLBACK_PREVIOUS_ACTION = "rollback_previous_action"


class RiskLevel(str, Enum):
    """Recommendation risk classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ControlMode(str, Enum):
    """Top-level control modes for the control plane."""

    OBSERVE_ONLY = "observe_only"
    RECOMMEND_WITH_APPROVAL = "recommend_with_approval"
    CONTROLLED_AUTO_ACT = "controlled_auto_act"


class PolicyMode(str, Enum):
    """High-level policy optimization mode."""

    BALANCED = "balanced"
    LATENCY_FIRST = "latency_first"
    THROUGHPUT_FIRST = "throughput_first"
    COST_FIRST = "cost_first"
    RELIABILITY_FIRST = "reliability_first"
    FAIRNESS = "fairness"


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------


class RecommendedAction(BaseModel):
    """The specific action being recommended."""

    action_type: ActionType
    parameters: dict[str, Any] = Field(default_factory=dict)


class Recommendation(BaseModel):
    """
    A single infrastructure recommendation produced by the policy engine.

    Must be explainable, auditable, and carry risk metadata.
    """

    recommendation_id: str
    entity_type: EntityType
    entity_id: str
    recommended_action: RecommendedAction
    reason: str
    expected_benefit: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    requires_approval: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Scoring dimensions
    benefit_score: float = Field(default=0.0, ge=0.0, le=1.0)
    urgency_score: float = Field(default=0.0, ge=0.0, le=1.0)
    scope_size: int = Field(default=1, description="Number of entities affected")

    @property
    def priority_score(self) -> float:
        """Compute composite priority: benefit × urgency × confidence / risk."""
        risk_factor = {"low": 1.0, "medium": 0.7, "high": 0.4, "critical": 0.2}
        return (
            self.benefit_score
            * self.urgency_score
            * self.confidence_score
            * risk_factor.get(self.risk_level.value, 0.5)
        )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


class Explanation(BaseModel):
    """
    Structured explanation attached to every recommendation.

    Makes the decision transparent and testable.
    """

    rule_id: str
    reason: str
    signals_used: list[str] = Field(default_factory=list)
    objectives_impacted: list[str] = Field(default_factory=list)
    expected_benefit: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Action Result & Verification
# ---------------------------------------------------------------------------


class ActionResult(BaseModel):
    """Result of applying a recommendation."""

    action_result_id: str
    recommendation_id: str
    entity_id: str
    status: str  # "applied", "failed", "rolled_back", "pending_approval"
    applied_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    before_snapshot: dict[str, Any] = Field(default_factory=dict)
    after_snapshot: dict[str, Any] = Field(default_factory=dict)
    metric_deltas: dict[str, float] = Field(default_factory=dict)
    guardrail_violations: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Audit Record
# ---------------------------------------------------------------------------


class AuditRecord(BaseModel):
    """
    Immutable audit record for every recommendation lifecycle event.

    Stored in the audit log for compliance and debugging.
    """

    audit_id: str
    recommendation_id: str
    event_type: str  # "created", "approved", "applied", "verified", "rolled_back", "blocked"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str = "system"
    details: dict[str, Any] = Field(default_factory=dict)
    explanation: Optional[Explanation] = None

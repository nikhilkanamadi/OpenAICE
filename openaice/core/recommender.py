"""
Recommender — packages policy engine output into final recommendations.

Adds risk/benefit/urgency scoring and filters by control mode.

Reference: 03 (section 11), 05 (sections 8-9)
"""

from __future__ import annotations

import logging
from typing import Any

from openaice.schemas.recommendations import (
    ControlMode,
    Explanation,
    Recommendation,
    RiskLevel,
)

logger = logging.getLogger(__name__)


class Recommender:
    """
    Processes raw policy engine recommendations into prioritized,
    filtered output with explanations.
    """

    def __init__(self, control_mode: ControlMode = ControlMode.OBSERVE_ONLY) -> None:
        self.control_mode = control_mode

    def process(
        self, recommendations: list[Recommendation]
    ) -> list[tuple[Recommendation, Explanation]]:
        """
        Process recommendations: filter by control mode and attach explanations.

        Returns list of (Recommendation, Explanation) tuples.
        """
        results: list[tuple[Recommendation, Explanation]] = []

        for rec in recommendations:
            # In observe-only mode, still generate recommendations but mark as informational
            if self.control_mode == ControlMode.OBSERVE_ONLY:
                rec.requires_approval = True  # cannot auto-apply

            explanation = self._build_explanation(rec)
            results.append((rec, explanation))

        # Sort by priority score
        results.sort(key=lambda x: x[0].priority_score, reverse=True)

        return results

    def _build_explanation(self, rec: Recommendation) -> Explanation:
        """Build a structured explanation for a recommendation."""
        signals = self._infer_signals(rec)
        objectives = self._infer_objectives(rec)

        return Explanation(
            rule_id=rec.recommendation_id,
            reason=rec.reason,
            signals_used=signals,
            objectives_impacted=objectives,
            expected_benefit=rec.expected_benefit,
            risk_level=rec.risk_level,
            confidence_score=rec.confidence_score,
        )

    def _infer_signals(self, rec: Recommendation) -> list[str]:
        """Infer which signals were used based on action type."""
        action = rec.recommended_action.action_type.value
        signal_map: dict[str, list[str]] = {
            "scale_replicas": ["latency_p95_ms", "queue_depth", "available_replicas"],
            "adjust_batching": ["gpu_utilization", "queue_depth", "latency_p95_ms"],
            "adjust_concurrency": ["gpu_utilization", "throughput", "latency_p99_ms"],
            "quarantine_node": ["health_state", "gpu_health", "node_health"],
            "enable_scale_to_zero": ["throughput", "cost_mode"],
            "recommend_no_action": ["confidence_score", "state_freshness_seconds"],
        }
        return signal_map.get(action, ["confidence_score"])

    def _infer_objectives(self, rec: Recommendation) -> list[str]:
        """Infer which objectives are impacted."""
        action = rec.recommended_action.action_type.value
        objective_map: dict[str, list[str]] = {
            "scale_replicas": ["latency", "reliability"],
            "adjust_batching": ["gpu_utilization", "latency"],
            "adjust_concurrency": ["throughput", "gpu_utilization"],
            "quarantine_node": ["reliability", "operational_safety"],
            "enable_scale_to_zero": ["cost"],
            "recommend_no_action": ["operational_safety"],
        }
        return objective_map.get(action, ["operational_safety"])

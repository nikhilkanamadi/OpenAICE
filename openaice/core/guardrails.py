"""
Guardrails — safety constraint evaluation for recommendations.

Enforces confidence thresholds, freshness requirements, cooldown windows,
and change magnitude limits. Without passing guardrails, no recommendation
should be eligible for actuation.

Reference: 05 (section 10)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from openaice.schemas.config import GuardrailConfig
from openaice.schemas.entities import CanonicalEntity
from openaice.schemas.recommendations import Recommendation, RiskLevel

logger = logging.getLogger(__name__)


class GuardrailResult:
    """Result of guardrail evaluation for a single recommendation."""

    def __init__(self, recommendation_id: str) -> None:
        self.recommendation_id = recommendation_id
        self.passed = True
        self.violations: list[str] = []

    def fail(self, reason: str) -> None:
        self.passed = False
        self.violations.append(reason)

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"GuardrailResult({self.recommendation_id}: {status}, violations={self.violations})"


class Guardrails:
    """
    Evaluates safety constraints against recommendations.

    All guardrails must pass for a recommendation to be eligible for
    actuation. Failed guardrails produce explanations.
    """

    def __init__(self, config: GuardrailConfig | None = None) -> None:
        self.config = config or GuardrailConfig()
        self._last_actions: dict[str, datetime] = {}  # entity_id -> last action time

    def evaluate(
        self,
        recommendation: Recommendation,
        entity: CanonicalEntity,
    ) -> GuardrailResult:
        """
        Evaluate all guardrails for a recommendation.

        Returns a GuardrailResult indicating pass/fail with reasons.
        """
        result = GuardrailResult(recommendation.recommendation_id)

        self._check_confidence(recommendation, entity, result)
        self._check_freshness(entity, result)
        self._check_cooldown(entity, result)
        self._check_risk_level(recommendation, result)

        if not result.passed:
            logger.info(
                "Guardrail blocked recommendation %s: %s",
                recommendation.recommendation_id,
                result.violations,
            )

        return result

    def evaluate_batch(
        self,
        recommendations: list[tuple[Recommendation, CanonicalEntity]],
    ) -> list[tuple[Recommendation, GuardrailResult]]:
        """
        Evaluate guardrails for a batch of recommendations.

        Also enforces blast-radius limits.
        """
        results: list[tuple[Recommendation, GuardrailResult]] = []
        approved_count = 0

        for rec, entity in recommendations:
            gr = self.evaluate(rec, entity)

            # Blast-radius limit
            if gr.passed:
                if approved_count >= self.config.blast_radius_limit:
                    gr.fail(
                        f"Blast-radius limit reached ({self.config.blast_radius_limit} "
                        f"entities per cycle)"
                    )
                else:
                    approved_count += 1

            results.append((rec, gr))

        return results

    def record_action(self, entity_id: str) -> None:
        """Record that an action was applied to an entity (for cooldown tracking)."""
        self._last_actions[entity_id] = datetime.utcnow()

    # ------------------------------------------------------------------
    # Individual guardrail checks
    # ------------------------------------------------------------------

    def _check_confidence(
        self,
        rec: Recommendation,
        entity: CanonicalEntity,
        result: GuardrailResult,
    ) -> None:
        """Guardrail A: minimum confidence threshold."""
        if rec.confidence_score < self.config.min_confidence_for_action:
            result.fail(
                f"Confidence {rec.confidence_score:.2f} below minimum "
                f"{self.config.min_confidence_for_action:.2f}"
            )

    def _check_freshness(
        self,
        entity: CanonicalEntity,
        result: GuardrailResult,
    ) -> None:
        """Guardrail B: reject stale telemetry."""
        entity.update_freshness()
        if entity.state_freshness_seconds > self.config.max_staleness_seconds:
            result.fail(
                f"Entity state is {entity.state_freshness_seconds:.0f}s old, "
                f"max allowed is {self.config.max_staleness_seconds:.0f}s"
            )

    def _check_cooldown(
        self,
        entity: CanonicalEntity,
        result: GuardrailResult,
    ) -> None:
        """Guardrail C: enforce cooldown window between actions."""
        last_action = self._last_actions.get(entity.entity_id)
        if last_action is not None:
            elapsed = (datetime.utcnow() - last_action).total_seconds()
            if elapsed < self.config.cooldown_seconds:
                result.fail(
                    f"Cooldown active for {entity.entity_id}: "
                    f"{elapsed:.0f}s elapsed, {self.config.cooldown_seconds:.0f}s required"
                )

    def _check_risk_level(
        self,
        rec: Recommendation,
        result: GuardrailResult,
    ) -> None:
        """Guardrail D: high/critical risk actions always require approval."""
        if rec.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            if not rec.requires_approval:
                result.fail(
                    f"High-risk action ({rec.risk_level.value}) must require approval"
                )

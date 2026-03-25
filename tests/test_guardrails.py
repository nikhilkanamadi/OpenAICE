"""
Tests for guardrails — safety constraint enforcement.
"""

from datetime import datetime, timedelta

from openaice.schemas.config import GuardrailConfig
from openaice.schemas.entities import (
    EntityType,
    SchedulerDomainType,
    ServiceEntity,
)
from openaice.schemas.recommendations import (
    ActionType,
    Recommendation,
    RecommendedAction,
    RiskLevel,
)
from openaice.core.guardrails import Guardrails


class TestGuardrails:
    """Test safety guardrail evaluation."""

    def _make_rec(self, confidence: float = 0.9, risk: RiskLevel = RiskLevel.MEDIUM) -> Recommendation:
        return Recommendation(
            recommendation_id="rec-test",
            entity_type=EntityType.SERVICE,
            entity_id="test-svc",
            recommended_action=RecommendedAction(action_type=ActionType.SCALE_REPLICAS),
            reason="test",
            expected_benefit="test",
            confidence_score=confidence,
            risk_level=risk,
        )

    def _make_entity(self, freshness_age: timedelta = timedelta(seconds=10)) -> ServiceEntity:
        return ServiceEntity(
            entity_id="test-svc",
            source_type="replay",
            scheduler_domain=SchedulerDomainType.KUBERNETES,
            observed_at=datetime.utcnow() - freshness_age,
            confidence_score=0.9,
        )

    def test_passes_all_guardrails(self):
        g = Guardrails(GuardrailConfig(min_confidence_for_action=0.75, max_staleness_seconds=120))
        rec = self._make_rec(confidence=0.9)
        entity = self._make_entity(freshness_age=timedelta(seconds=10))

        result = g.evaluate(rec, entity)
        assert result.passed, f"Should pass: {result.violations}"

    def test_fails_low_confidence(self):
        g = Guardrails(GuardrailConfig(min_confidence_for_action=0.80))
        rec = self._make_rec(confidence=0.5)
        entity = self._make_entity()

        result = g.evaluate(rec, entity)
        assert not result.passed
        assert any("Confidence" in v for v in result.violations)

    def test_fails_stale_data(self):
        g = Guardrails(GuardrailConfig(max_staleness_seconds=60))
        rec = self._make_rec()
        entity = self._make_entity(freshness_age=timedelta(minutes=5))

        result = g.evaluate(rec, entity)
        assert not result.passed
        assert any("old" in v for v in result.violations)

    def test_fails_cooldown(self):
        g = Guardrails(GuardrailConfig(cooldown_seconds=300))
        g.record_action("test-svc")  # just acted on this entity

        rec = self._make_rec()
        entity = self._make_entity()

        result = g.evaluate(rec, entity)
        assert not result.passed
        assert any("Cooldown" in v for v in result.violations)

    def test_blast_radius_limit(self):
        config = GuardrailConfig(blast_radius_limit=2)
        g = Guardrails(config)

        pairs = []
        for i in range(4):
            rec = Recommendation(
                recommendation_id=f"rec-{i}",
                entity_type=EntityType.SERVICE,
                entity_id=f"svc-{i}",
                recommended_action=RecommendedAction(action_type=ActionType.SCALE_REPLICAS),
                reason="test",
                expected_benefit="test",
                confidence_score=0.9,
                risk_level=RiskLevel.LOW,
            )
            entity = ServiceEntity(
                entity_id=f"svc-{i}",
                source_type="replay",
                observed_at=datetime.utcnow(),
                confidence_score=0.9,
            )
            pairs.append((rec, entity))

        results = g.evaluate_batch(pairs)
        passed = [r for _, r in results if r.passed]
        blocked = [r for _, r in results if not r.passed]

        assert len(passed) == 2
        assert len(blocked) == 2

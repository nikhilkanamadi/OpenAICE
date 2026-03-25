"""
Golden replay tests — end-to-end pipeline tests using replay scenarios.

These are the backbone of confidence for the project:
replay known inputs → verify expected recommendations.
"""

from pathlib import Path

import yaml

from openaice.adapters.telemetry.replay import ReplayAdapter
from openaice.core.normalizer import Normalizer
from openaice.core.policy_engine import PolicyEngine
from openaice.core.recommender import Recommender
from openaice.core.state_bus import StateBus
from openaice.core.workload_classifier import WorkloadClassifier
from openaice.schemas.recommendations import ControlMode, PolicyMode


EXAMPLES_DIR = Path(__file__).parent.parent / "examples" / "telemetry-replay"
RULES_PATH = str(Path(__file__).parent.parent / "policies" / "rules.yaml")
PACK_PATH = str(Path(__file__).parent.parent / "policies" / "packs" / "balanced.yaml")


def _run_scenario(scenario_name: str) -> tuple:
    """Run a replay scenario through the full pipeline."""
    scenario_path = EXAMPLES_DIR / scenario_name

    # Initialize components
    state_bus = StateBus()
    normalizer = Normalizer()
    classifier = WorkloadClassifier()
    policy_engine = PolicyEngine(
        policy_mode=PolicyMode.BALANCED,
        control_mode=ControlMode.RECOMMEND_WITH_APPROVAL,
    )
    recommender = Recommender(control_mode=ControlMode.RECOMMEND_WITH_APPROVAL)

    # Load rules
    policy_engine.load_rules(RULES_PATH)
    policy_engine.load_policy_pack(PACK_PATH)

    # Load replay data
    adapter = ReplayAdapter()
    adapter.initialize({"scenario_path": str(scenario_path)})
    raw_records = adapter.collect()

    # Run pipeline
    fragments = normalizer.normalize(raw_records)
    state_bus.put_fragments(fragments)

    entities = state_bus.get_all_entities()
    classifier.classify_all(entities)

    recommendations = policy_engine.evaluate(entities)
    results = recommender.process(recommendations)

    # Load expected
    expected = adapter.load_expected()

    return entities, results, expected


class TestReplayScenarios:
    """Golden replay tests."""

    def test_k8s_inference_queue_pressure(self):
        """
        Scenario: K8s inference service under queue pressure.
        Expected: scale_replicas recommendation for inference-api.
        """
        entities, results, expected = _run_scenario("k8s-inference-queue-pressure")

        # Verify entities were loaded
        assert len(entities) >= 2, f"Expected ≥2 entities, got {len(entities)}"

        # Verify recommendations
        assert len(results) > 0, "Expected at least one recommendation"

        # Check that scale_replicas was recommended for inference-api
        rec_actions = {
            (r.entity_id, r.recommended_action.action_type.value)
            for r, _ in results
        }
        assert ("inference-api", "scale_replicas") in rec_actions, (
            f"Expected scale_replicas for inference-api, got: {rec_actions}"
        )

        # Verify against expected output
        if expected:
            for exp in expected:
                found = any(
                    r.entity_id == exp["entity_id"]
                    and r.recommended_action.action_type.value == exp["action_type"]
                    for r, _ in results
                )
                assert found, f"Expected recommendation not found: {exp}"

    def test_slurm_node_health_warning(self):
        """
        Scenario: Slurm HPC node with degraded health.
        Expected: quarantine_node recommendation for gpu-node-17.
        """
        entities, results, expected = _run_scenario("slurm-node-health-warning")

        # Verify entities
        assert len(entities) >= 2, f"Expected ≥2 entities, got {len(entities)}"

        # Check that quarantine_node was recommended
        rec_actions = {
            (r.entity_id, r.recommended_action.action_type.value)
            for r, _ in results
        }
        assert ("gpu-node-17", "quarantine_node") in rec_actions, (
            f"Expected quarantine_node for gpu-node-17, got: {rec_actions}"
        )

    def test_replay_determinism(self):
        """Same scenario should produce same results every time."""
        _, results1, _ = _run_scenario("k8s-inference-queue-pressure")
        _, results2, _ = _run_scenario("k8s-inference-queue-pressure")

        actions1 = {
            (r.entity_id, r.recommended_action.action_type.value)
            for r, _ in results1
        }
        actions2 = {
            (r.entity_id, r.recommended_action.action_type.value)
            for r, _ in results2
        }
        assert actions1 == actions2, "Replay should be deterministic"

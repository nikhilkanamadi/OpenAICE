"""
AICP API Server — FastAPI server for OpenAICE.

Endpoints:
  GET /health          — health check
  GET /state           — current canonical state snapshot
  GET /recommendations — current recommendations
  GET /audit           — audit history
  POST /replay         — run a replay scenario
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from openaice.schemas.config import OpenAICEConfig


class ReplayRequest(BaseModel):
    scenario_path: str


def create_app(config: OpenAICEConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if config is None:
        config = OpenAICEConfig()

    app = FastAPI(
        title="OpenAICE — Auto Infrastructure Configuration Engine",
        description="Adapter-based, recommendation-first control plane for modern AI infrastructure.",
        version="0.1.0",
    )

    # Shared state
    app.state.config = config
    app.state.entities = []
    app.state.recommendations = []
    app.state.audit_records = []

    @app.get("/health")
    def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": "0.1.0",
            "control_mode": config.control_mode.value,
            "policy_mode": config.policy_mode.value,
        }

    @app.get("/state")
    def get_state():
        """Get current canonical state snapshot."""
        return {
            "entity_count": len(app.state.entities),
            "entities": [e.model_dump(mode="json") for e in app.state.entities],
        }

    @app.get("/recommendations")
    def get_recommendations():
        """Get current recommendations."""
        return {
            "count": len(app.state.recommendations),
            "recommendations": [
                {
                    "recommendation": rec.model_dump(mode="json"),
                    "explanation": exp.model_dump(mode="json"),
                }
                for rec, exp in app.state.recommendations
            ],
        }

    @app.get("/audit")
    def get_audit():
        """Get audit history."""
        return {
            "count": len(app.state.audit_records),
            "records": app.state.audit_records,
        }

    @app.post("/replay")
    def run_replay(request: ReplayRequest):
        """Run a telemetry replay scenario."""
        from openaice.adapters.telemetry.replay import ReplayAdapter
        from openaice.core.normalizer import Normalizer
        from openaice.core.policy_engine import PolicyEngine
        from openaice.core.recommender import Recommender
        from openaice.core.state_bus import StateBus
        from openaice.core.workload_classifier import WorkloadClassifier

        scenario_path = Path(request.scenario_path)
        if not scenario_path.exists():
            raise HTTPException(status_code=404, detail=f"Scenario not found: {request.scenario_path}")

        # Run pipeline
        state_bus = StateBus()
        normalizer = Normalizer()
        classifier = WorkloadClassifier()
        policy_engine = PolicyEngine(
            policy_mode=config.policy_mode,
            control_mode=config.control_mode,
        )
        recommender = Recommender(control_mode=config.control_mode)

        policy_engine.load_rules(config.rules_path)
        policy_engine.load_policy_pack(config.policy_pack_path)

        adapter = ReplayAdapter()
        adapter.initialize({"scenario_path": str(scenario_path)})
        raw_records = adapter.collect()

        fragments = normalizer.normalize(raw_records)
        state_bus.put_fragments(fragments)

        entities = state_bus.get_all_entities()
        classifier.classify_all(entities)

        recommendations = policy_engine.evaluate(entities)
        results = recommender.process(recommendations)

        # Store in app state
        app.state.entities = entities
        app.state.recommendations = results

        return {
            "entities_loaded": len(entities),
            "recommendations_generated": len(results),
            "recommendations": [
                {
                    "recommendation": rec.model_dump(mode="json"),
                    "explanation": exp.model_dump(mode="json"),
                }
                for rec, exp in results
            ],
        }

    return app

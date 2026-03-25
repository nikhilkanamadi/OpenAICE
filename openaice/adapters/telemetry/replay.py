"""
Replay Adapter — loads pre-recorded telemetry for testing and demos.

This is the most important adapter for development: it enables
deterministic golden tests and demo scenarios without live infrastructure.

Reference: 11 (sections 3-5)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from openaice.adapters.base import TelemetryAdapter

logger = logging.getLogger(__name__)


class ReplayAdapter(TelemetryAdapter):
    """
    Replays pre-recorded telemetry from YAML/JSON files.

    Each replay scenario is a directory containing:
    - inputs/telemetry.yaml (or .json) — recorded state fragments
    - expected/recommendations.yaml — expected output (for golden tests)
    - config.yaml — scenario-specific config overrides
    """

    name = "replay"
    version = "0.1.0"

    def __init__(self) -> None:
        self._scenario_path: Path | None = None
        self._records: list[dict[str, Any]] = []

    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize with a scenario path."""
        path = config.get("scenario_path")
        if path:
            self._scenario_path = Path(path)
            self._load_scenario()

    def _load_scenario(self) -> None:
        """Load telemetry data from the scenario directory."""
        if not self._scenario_path or not self._scenario_path.exists():
            logger.warning("Replay scenario path not found: %s", self._scenario_path)
            return

        # Try YAML first, then JSON
        for filename in ["telemetry.yaml", "telemetry.json"]:
            input_file = self._scenario_path / "inputs" / filename
            if input_file.exists():
                self._records = self._load_file(input_file)
                logger.info(
                    "Loaded %d replay records from %s", len(self._records), input_file
                )
                return

        logger.warning("No telemetry data found in %s", self._scenario_path)

    def _load_file(self, path: Path) -> list[dict[str, Any]]:
        """Load records from a YAML or JSON file."""
        with open(path) as f:
            if path.suffix == ".yaml" or path.suffix == ".yml":
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        if isinstance(data, dict) and "records" in data:
            return data["records"]
        if isinstance(data, list):
            return data
        return []

    def collect(self) -> list[dict[str, Any]]:
        """Return all pre-loaded records."""
        return self._records

    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Replay records are already in normalized format."""
        return raw_records

    def load_expected(self) -> list[dict[str, Any]]:
        """Load expected recommendations for golden test comparison."""
        if not self._scenario_path:
            return []

        for filename in ["recommendations.yaml", "recommendations.json"]:
            expected_file = self._scenario_path / "expected" / filename
            if expected_file.exists():
                return self._load_file(expected_file)

        return []

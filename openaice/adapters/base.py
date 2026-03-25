"""
Base adapter classes — the adapter contract model.

Defines abstract base classes for all four adapter categories:
TelemetryAdapter, RuntimeStateAdapter, EnrichmentAdapter, ActuationAdapter.

Every adapter must implement these interfaces to integrate with the
control plane core.

Reference: 03 (sections 3-7)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """Base contract for all adapters."""

    name: str = "base"
    version: str = "0.1.0"
    adapter_type: str = "base"

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the adapter with configuration."""
        ...

    def healthcheck(self) -> dict[str, Any]:
        """Return adapter health status."""
        return {"adapter": self.name, "status": "healthy", "version": self.version}

    def capabilities(self) -> dict[str, Any]:
        """Declare adapter capabilities."""
        return {"adapter": self.name, "type": self.adapter_type}


class TelemetryAdapter(BaseAdapter):
    """
    Base contract for telemetry adapters.

    Ingest metrics, logs, traces, events and normalize into state fragments.
    """

    adapter_type: str = "telemetry"

    @abstractmethod
    def collect(self) -> list[dict[str, Any]]:
        """Fetch new telemetry from the source. Returns raw records."""
        ...

    @abstractmethod
    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize raw records into canonical fragment dicts."""
        ...

    def watermark(self) -> str:
        """Return the latest processed timestamp."""
        return ""


class RuntimeStateAdapter(BaseAdapter):
    """
    Base contract for runtime state adapters.

    Expose scheduler/orchestrator/serving state.
    """

    adapter_type: str = "runtime"

    @abstractmethod
    def snapshot(self) -> list[dict[str, Any]]:
        """Get a full snapshot of current runtime state. Returns raw records."""
        ...

    def watch(self) -> list[dict[str, Any]]:
        """Get incremental updates (optional). Returns raw records."""
        return []

    def resolve_entity(self, entity_id: str) -> dict[str, Any] | None:
        """Resolve a specific entity by ID (optional)."""
        return None


class EnrichmentAdapter(BaseAdapter):
    """
    Base contract for enrichment adapters.

    Attach context (job/user/namespace/revision) that raw metrics lack.
    """

    adapter_type: str = "enrichment"

    @abstractmethod
    def enrich(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Enrich records with additional metadata."""
        ...


class ActuationAdapter(BaseAdapter):
    """
    Base contract for actuation adapters.

    Apply recommended changes safely through existing tool APIs.
    """

    adapter_type: str = "actuation"

    @abstractmethod
    def plan(self, action: dict[str, Any]) -> dict[str, Any]:
        """Plan the action without executing."""
        ...

    @abstractmethod
    def dry_run(self, action: dict[str, Any]) -> dict[str, Any]:
        """Simulate the action."""
        ...

    @abstractmethod
    def apply(self, action: dict[str, Any]) -> dict[str, Any]:
        """Apply the action."""
        ...

    def verify(self, action_result: dict[str, Any]) -> dict[str, Any]:
        """Verify post-action state."""
        return {"status": "not_implemented"}

    def rollback(self, action_result: dict[str, Any]) -> dict[str, Any]:
        """Rollback the action."""
        return {"status": "not_implemented"}

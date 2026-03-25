"""
Audit Log — immutable event log for all recommendation lifecycle events.

Stores every recommendation, explanation, guardrail result, and state
snapshot as JSON Lines for compliance, debugging, and replay.

Reference: 08 (section 7.1)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from openaice.schemas.recommendations import AuditRecord, Explanation, Recommendation

logger = logging.getLogger(__name__)


class AuditLog:
    """
    Append-only audit log stored as JSON Lines (.jsonl).

    Every recommendation lifecycle event is recorded with full provenance.
    """

    def __init__(self, log_path: str = "audit.jsonl") -> None:
        self.log_path = Path(log_path)
        self._records: list[AuditRecord] = []

    def log_recommendation(
        self,
        recommendation: Recommendation,
        explanation: Explanation | None = None,
        event_type: str = "created",
    ) -> AuditRecord:
        """Log a recommendation lifecycle event."""
        record = AuditRecord(
            audit_id=f"audit-{len(self._records):06d}",
            recommendation_id=recommendation.recommendation_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            actor="policy_engine",
            details={
                "entity_id": recommendation.entity_id,
                "entity_type": recommendation.entity_type.value,
                "action_type": recommendation.recommended_action.action_type.value,
                "confidence_score": recommendation.confidence_score,
                "risk_level": recommendation.risk_level.value,
                "reason": recommendation.reason,
            },
            explanation=explanation,
        )

        self._records.append(record)
        self._append_to_file(record)
        return record

    def log_guardrail_block(
        self,
        recommendation: Recommendation,
        violations: list[str],
    ) -> AuditRecord:
        """Log that a recommendation was blocked by guardrails."""
        record = AuditRecord(
            audit_id=f"audit-{len(self._records):06d}",
            recommendation_id=recommendation.recommendation_id,
            event_type="blocked",
            timestamp=datetime.utcnow(),
            actor="guardrails",
            details={
                "entity_id": recommendation.entity_id,
                "violations": violations,
            },
        )

        self._records.append(record)
        self._append_to_file(record)
        return record

    def log_event(
        self,
        recommendation_id: str,
        event_type: str,
        details: dict[str, Any] | None = None,
    ) -> AuditRecord:
        """Log a generic audit event."""
        record = AuditRecord(
            audit_id=f"audit-{len(self._records):06d}",
            recommendation_id=recommendation_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            details=details or {},
        )

        self._records.append(record)
        self._append_to_file(record)
        return record

    def get_records(self, limit: int = 100) -> list[AuditRecord]:
        """Get the most recent audit records."""
        return self._records[-limit:]

    def get_records_for_recommendation(self, recommendation_id: str) -> list[AuditRecord]:
        """Get all audit records for a specific recommendation."""
        return [r for r in self._records if r.recommendation_id == recommendation_id]

    def _append_to_file(self, record: AuditRecord) -> None:
        """Append a record to the JSON Lines file."""
        try:
            with open(self.log_path, "a") as f:
                f.write(record.model_dump_json() + "\n")
        except Exception as e:
            logger.warning("Failed to write audit log: %s", e)

    def clear(self) -> None:
        """Clear in-memory records (for testing)."""
        self._records.clear()

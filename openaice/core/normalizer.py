"""
Normalizer — maps source-specific records into canonical state fragments.

Adapters produce raw records; the normalizer converts them into typed
StateFragment objects with schema validation via Pydantic.

Reference: 03 (section 3-4)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from openaice.schemas.entities import EntityType, SchedulerDomainType, StateFragment

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Source-to-entity mapping helpers
# ---------------------------------------------------------------------------

# Maps common source types to their default scheduler domain
SOURCE_DOMAIN_MAP: dict[str, SchedulerDomainType] = {
    "prometheus": SchedulerDomainType.UNKNOWN,  # domain comes from labels
    "kubernetes": SchedulerDomainType.KUBERNETES,
    "kserve": SchedulerDomainType.KUBERNETES,
    "slurm": SchedulerDomainType.SLURM,
    "gcm": SchedulerDomainType.SLURM,
    "dcgm": SchedulerDomainType.UNKNOWN,
    "ray": SchedulerDomainType.RAY,
    "replay": SchedulerDomainType.UNKNOWN,
}


class Normalizer:
    """
    Converts raw adapter records into validated StateFragment objects.

    The normalizer enforces that every fragment has:
    - a valid entity_type
    - a non-empty entity_id
    - an observed timestamp
    - a recognized source_type
    """

    def normalize(self, raw_records: list[dict[str, Any]]) -> list[StateFragment]:
        """
        Normalize a batch of raw records into StateFragment objects.

        Invalid records are logged and skipped.
        """
        fragments: list[StateFragment] = []

        for record in raw_records:
            try:
                frag = self._normalize_one(record)
                if frag:
                    fragments.append(frag)
            except Exception as e:
                logger.warning("Failed to normalize record: %s — %s", record, e)

        return fragments

    def _normalize_one(self, record: dict[str, Any]) -> StateFragment | None:
        """Normalize a single raw record."""
        # Required fields
        source_type = record.get("source_type")
        entity_type_raw = record.get("entity_type")
        entity_id = record.get("entity_id")

        if not all([source_type, entity_type_raw, entity_id]):
            logger.warning("Record missing required fields: %s", record)
            return None

        # Parse entity type
        try:
            entity_type = EntityType(entity_type_raw)
        except ValueError:
            logger.warning("Unknown entity_type: %s", entity_type_raw)
            return None

        # Parse timestamp
        observed_at = record.get("observed_at")
        if isinstance(observed_at, str):
            observed_at = datetime.fromisoformat(observed_at)
        elif not isinstance(observed_at, datetime):
            observed_at = datetime.utcnow()

        # Extract fields (everything except meta-keys)
        meta_keys = {"source_type", "entity_type", "entity_id", "observed_at", "labels"}
        fields = {k: v for k, v in record.items() if k not in meta_keys and v is not None}

        # Inject scheduler_domain if not present
        if "scheduler_domain" not in fields:
            fields["scheduler_domain"] = SOURCE_DOMAIN_MAP.get(
                source_type, SchedulerDomainType.UNKNOWN
            )

        # Extract labels
        labels = record.get("labels", {})
        if not isinstance(labels, dict):
            labels = {}

        return StateFragment(
            source_type=source_type,
            entity_type=entity_type,
            entity_id=entity_id,
            observed_at=observed_at,
            fields=fields,
            labels=labels,
        )

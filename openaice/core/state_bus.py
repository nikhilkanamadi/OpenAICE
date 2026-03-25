"""
In-memory State Bus — the central normalized state store.

Receives state fragments from adapters, merges them by entity ID,
maintains freshness metadata, and exposes the canonical entity graph
for the policy engine.

Reference: 03 (section 8), 04 (section 7)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from openaice.schemas.entities import (
    ENTITY_TYPE_MAP,
    CanonicalEntity,
    EntityType,
    StateFragment,
)

logger = logging.getLogger(__name__)


class StateBus:
    """
    In-memory state bus that stores and merges canonical entities.

    Thread-safety note: v1 runs single-threaded. For later
    concurrent use, wrap mutations in a lock.
    """

    def __init__(self) -> None:
        # Primary store: entity_id -> CanonicalEntity
        self._entities: dict[str, CanonicalEntity] = {}
        # Fragment history for audit/debug (bounded)
        self._fragment_log: list[StateFragment] = []
        self._max_fragment_log = 10_000

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    def put_fragments(self, fragments: list[StateFragment]) -> list[str]:
        """
        Ingest a batch of state fragments, merging them into canonical entities.

        Returns list of entity_ids that were created or updated.
        """
        updated_ids: list[str] = []

        for frag in fragments:
            entity_id = frag.entity_id

            if entity_id in self._entities:
                self._merge_fragment(self._entities[entity_id], frag)
            else:
                self._create_entity(frag)

            updated_ids.append(entity_id)

            # Keep bounded fragment log
            if len(self._fragment_log) < self._max_fragment_log:
                self._fragment_log.append(frag)

        return updated_ids

    def _create_entity(self, frag: StateFragment) -> None:
        """Create a new canonical entity from the first fragment."""
        entity_cls = ENTITY_TYPE_MAP.get(frag.entity_type, CanonicalEntity)

        # Build initial fields from fragment
        init_fields = {
            "entity_type": frag.entity_type,
            "entity_id": frag.entity_id,
            "source_type": frag.source_type,
            "observed_at": frag.observed_at,
        }
        # Merge fragment fields, skipping unknown fields for the entity class
        for key, value in frag.fields.items():
            if key in entity_cls.model_fields:
                init_fields[key] = value

        try:
            entity = entity_cls(**init_fields)
            self._entities[frag.entity_id] = entity
            logger.debug("Created entity %s (%s)", frag.entity_id, frag.entity_type.value)
        except Exception as e:
            logger.warning("Failed to create entity %s: %s", frag.entity_id, e)

    def _merge_fragment(self, entity: CanonicalEntity, frag: StateFragment) -> None:
        """
        Merge a new fragment into an existing entity.

        Rules:
        - Newer data wins when source reliability is similar
        - Preserve source attribution
        - Update freshness
        """
        # Only merge if the fragment is newer or same time
        if frag.observed_at < entity.observed_at:
            logger.debug(
                "Skipping stale fragment for %s (frag=%s, entity=%s)",
                entity.entity_id,
                frag.observed_at,
                entity.observed_at,
            )
            return

        # Update observed_at
        entity.observed_at = frag.observed_at
        entity.source_type = frag.source_type

        # Merge fields
        for key, value in frag.fields.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)

        entity.update_freshness()

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------

    def get_entity(self, entity_id: str) -> Optional[CanonicalEntity]:
        """Get a single entity by ID."""
        entity = self._entities.get(entity_id)
        if entity:
            entity.update_freshness()
        return entity

    def get_all_entities(self) -> list[CanonicalEntity]:
        """Get all known entities with updated freshness."""
        now = datetime.utcnow()
        for entity in self._entities.values():
            delta = now - entity.observed_at
            entity.state_freshness_seconds = delta.total_seconds()
        return list(self._entities.values())

    def get_entities_by_type(self, entity_type: EntityType) -> list[CanonicalEntity]:
        """Get all entities of a given type."""
        return [
            e for e in self.get_all_entities()
            if e.entity_type == entity_type
        ]

    def get_entity_count(self) -> int:
        """Get the total number of tracked entities."""
        return len(self._entities)

    # ------------------------------------------------------------------
    # Management
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Clear all state (useful for testing and replay)."""
        self._entities.clear()
        self._fragment_log.clear()

    def snapshot(self) -> list[dict]:
        """Export current state as a list of dicts (for API/audit)."""
        return [e.model_dump(mode="json") for e in self.get_all_entities()]

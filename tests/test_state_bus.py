"""
Tests for the State Bus — merge, freshness, deduplication.
"""

from datetime import datetime, timedelta

from openaice.schemas.entities import EntityType, StateFragment
from openaice.core.state_bus import StateBus


class TestStateBus:
    """Test state bus merge and retrieval."""

    def test_create_entity_from_fragment(self):
        bus = StateBus()
        frag = StateFragment(
            source_type="replay",
            entity_type=EntityType.SERVICE,
            entity_id="test-svc",
            observed_at=datetime.utcnow(),
            fields={"latency_p95_ms": 100.0, "confidence_score": 0.9},
        )
        bus.put_fragments([frag])

        entity = bus.get_entity("test-svc")
        assert entity is not None
        assert entity.entity_id == "test-svc"
        assert entity.entity_type == EntityType.SERVICE

    def test_merge_fragments(self):
        bus = StateBus()
        now = datetime.utcnow()

        frag1 = StateFragment(
            source_type="prometheus",
            entity_type=EntityType.SERVICE,
            entity_id="svc-a",
            observed_at=now,
            fields={"latency_p95_ms": 100.0, "confidence_score": 0.8},
        )
        frag2 = StateFragment(
            source_type="prometheus",
            entity_type=EntityType.SERVICE,
            entity_id="svc-a",
            observed_at=now + timedelta(seconds=5),
            fields={"queue_depth": 42, "confidence_score": 0.85},
        )

        bus.put_fragments([frag1])
        bus.put_fragments([frag2])

        entity = bus.get_entity("svc-a")
        assert entity is not None
        assert entity.confidence_score == 0.85  # updated by newer fragment

    def test_skip_stale_fragment(self):
        bus = StateBus()
        now = datetime.utcnow()

        fresh = StateFragment(
            source_type="replay",
            entity_type=EntityType.NODE,
            entity_id="node-1",
            observed_at=now,
            fields={"health_state": "healthy", "confidence_score": 0.9},
        )
        stale = StateFragment(
            source_type="replay",
            entity_type=EntityType.NODE,
            entity_id="node-1",
            observed_at=now - timedelta(hours=1),
            fields={"health_state": "degraded", "confidence_score": 0.5},
        )

        bus.put_fragments([fresh])
        bus.put_fragments([stale])  # should be skipped

        entity = bus.get_entity("node-1")
        assert entity is not None
        assert entity.health_state.value == "healthy"

    def test_get_entities_by_type(self):
        bus = StateBus()
        now = datetime.utcnow()

        bus.put_fragments([
            StateFragment(source_type="r", entity_type=EntityType.SERVICE, entity_id="s1", observed_at=now, fields={"confidence_score": 0.9}),
            StateFragment(source_type="r", entity_type=EntityType.SERVICE, entity_id="s2", observed_at=now, fields={"confidence_score": 0.9}),
            StateFragment(source_type="r", entity_type=EntityType.NODE, entity_id="n1", observed_at=now, fields={"confidence_score": 0.9}),
        ])

        services = bus.get_entities_by_type(EntityType.SERVICE)
        assert len(services) == 2

        nodes = bus.get_entities_by_type(EntityType.NODE)
        assert len(nodes) == 1

    def test_clear(self):
        bus = StateBus()
        bus.put_fragments([
            StateFragment(source_type="r", entity_type=EntityType.GPU, entity_id="g1", observed_at=datetime.utcnow(), fields={}),
        ])
        assert bus.get_entity_count() == 1

        bus.clear()
        assert bus.get_entity_count() == 0

    def test_snapshot(self):
        bus = StateBus()
        bus.put_fragments([
            StateFragment(source_type="r", entity_type=EntityType.SERVICE, entity_id="s1", observed_at=datetime.utcnow(), fields={"confidence_score": 0.9}),
        ])
        snap = bus.snapshot()
        assert len(snap) == 1
        assert snap[0]["entity_id"] == "s1"

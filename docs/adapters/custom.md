# Writing Custom Adapters

Extend OpenAICE with your own telemetry and runtime adapters.

## Step 1: Choose the Adapter Type

| Type | Base Class | Purpose |
|------|-----------|---------|
| Telemetry | `TelemetryAdapter` | Ingest metrics/logs from monitoring systems |
| Runtime State | `RuntimeStateAdapter` | Read orchestrator/scheduler state |

## Step 2: Implement the Interface

### Telemetry Adapter Example

```python
from openaice.adapters.base import TelemetryAdapter


class MyCustomAdapter(TelemetryAdapter):
    """Adapter for my custom monitoring system."""

    def initialize(self, config: dict) -> None:
        self.endpoint = config.get("endpoint", "http://localhost:8080")
        self._client = None  # Initialize your client

    def collect(self) -> list[dict]:
        """Collect raw records from the monitoring system."""
        # Fetch data from your source
        raw_data = self._fetch_metrics()

        # Return as list of dicts with required fields
        return [
            {
                "source_type": "my_system",
                "entity_type": "service",
                "entity_id": item["service_name"],
                "observed_at": item["timestamp"],
                "latency_p95_ms": item["p95"],
                "queue_depth": item["queue_size"],
                "throughput": item["rps"],
                "confidence_score": 0.85,
            }
            for item in raw_data
        ]

    def health_check(self) -> bool:
        """Check if the monitoring system is reachable."""
        try:
            resp = httpx.get(f"{self.endpoint}/health")
            return resp.status_code == 200
        except Exception:
            return False
```

## Step 3: Required Fields

Every raw record **must** include:

| Field | Type | Description |
|-------|------|-------------|
| `source_type` | `str` | Identifier for your adapter |
| `entity_type` | `str` | One of the 12 canonical types |
| `entity_id` | `str` | Unique entity identifier |
| `observed_at` | `str`/`datetime` | Observation timestamp |

All other fields are optional and map to the canonical entity schema.

## Step 4: Register the Adapter

Add your adapter to the pipeline in the CLI or API:

```python
from my_adapters import MyCustomAdapter

adapter = MyCustomAdapter()
adapter.initialize({"endpoint": "http://my-system:8080"})
raw_records = adapter.collect()

# Feed into the standard pipeline
fragments = normalizer.normalize(raw_records)
state_bus.put_fragments(fragments)
```

## Tips

!!! tip "Start with Replay"
    Before building a live adapter, create a replay scenario with sample data from your system.
    This lets you validate your entity mapping and policy rules without a live connection.

!!! warning "Confidence Scores"
    Always set a meaningful `confidence_score`. The policy engine uses this to gate recommendations — a low confidence score will block high-risk actions.

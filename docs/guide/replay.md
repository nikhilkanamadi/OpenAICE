# Replay & Testing

Replay is OpenAICE's primary testing mechanism — it lets you develop and validate without live infrastructure.

## How Replay Works

A replay scenario is a directory containing:

```
examples/telemetry-replay/my-scenario/
├── inputs/
│   └── telemetry.yaml     # Recorded telemetry data
└── expected/
    └── recommendations.yaml # Expected output (golden test)
```

The replay adapter loads `telemetry.yaml`, feeds it through the full pipeline, and compares the output against `expected/recommendations.yaml`.

## Creating a Replay Scenario

### 1. Create the Input Telemetry

```yaml
# inputs/telemetry.yaml
records:
  - source_type: replay
    entity_type: service
    entity_id: my-api
    observed_at: "2026-03-24T12:00:00"
    scheduler_domain: kubernetes
    workload_type: online_inference
    health_state: healthy
    latency_p95_ms: 420
    queue_depth: 55
    throughput: 200
    confidence_score: 0.92
```

### 2. Create the Expected Output

```yaml
# expected/recommendations.yaml
records:
  - entity_id: my-api
    action_type: scale_replicas
    risk_level: medium
    min_confidence: 0.75
```

### 3. Run the Scenario

```bash
python -m openaice.cli.cli replay \
  --scenario examples/telemetry-replay/my-scenario
```

## Built-in Scenarios

| Scenario | Description | Expected Recommendation |
|----------|------------|----------------------|
| `k8s-inference-queue-pressure` | Service with p95=320ms, queue=42 | `scale_replicas` for `inference-api` |
| `slurm-node-health-warning` | Node with degraded health, GPU with ECC errors | `quarantine_node` for `gpu-node-17` |

## Golden Tests

The replay golden tests in `tests/test_replay.py` validate that:

1. Known inputs produce expected recommendations
2. All expected entity types are loaded
3. Replay is deterministic (same inputs → same outputs every time)

```bash
# Run golden tests
pytest tests/test_replay.py -v
```

## Running All Tests

```bash
# Full test suite (30 tests)
pytest tests/ -v
```

| Test File | Count | What it tests |
|-----------|-------|-------------|
| `test_schemas.py` | 11 | Entity types, recommendations, validation |
| `test_state_bus.py` | 6 | Fragment merge, freshness, filtering |
| `test_policy_engine.py` | 5 | Rule matching, confidence gates |
| `test_guardrails.py` | 5 | Safety constraints, blast radius |
| `test_replay.py` | 3 | End-to-end golden replay tests |

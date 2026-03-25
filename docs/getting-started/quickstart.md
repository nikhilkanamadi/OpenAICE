# Quick Start

Get OpenAICE running in under 5 minutes with a replay demo.

## 1. Run Your First Replay

Replay scenarios let you test the full pipeline without any live infrastructure:

```bash
python -m openaice.cli.cli replay \
  --scenario examples/telemetry-replay/k8s-inference-queue-pressure
```

This loads synthetic telemetry data simulating a Kubernetes inference service under queue pressure, runs it through the policy engine, and outputs recommendations.

!!! success "Expected Output"
    You should see a recommendation to `scale_replicas` for the `inference-api` service with confidence 0.91 and risk level `medium`.

## 2. Try the Slurm Scenario

```bash
python -m openaice.cli.cli replay \
  --scenario examples/telemetry-replay/slurm-node-health-warning
```

!!! success "Expected Output"
    Recommendations to `quarantine_node` for the unhealthy GPU node with risk level `high`.

## 3. Start the API Server

```bash
python -m openaice.cli.cli serve --config configs/sample-k8s.yaml
```

Then visit [`http://localhost:8000/docs`](http://localhost:8000/docs) for the interactive OpenAPI documentation.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with control/policy mode |
| `/state` | GET | Current canonical entity state |
| `/recommendations` | GET | Active recommendations |
| `/audit` | GET | Audit event history |
| `/replay` | POST | Run a replay scenario via API |

## 4. Run a Replay via API

```bash
curl -X POST http://localhost:8000/replay \
  -H "Content-Type: application/json" \
  -d '{"scenario_path": "examples/telemetry-replay/k8s-inference-queue-pressure"}'
```

## 5. Inspect State

```bash
python -m openaice.cli.cli state \
  --scenario examples/telemetry-replay/k8s-inference-queue-pressure \
  --format yaml
```

This dumps the canonical entity state that the policy engine reasons over.

## 6. Run Tests

```bash
pytest tests/ -v
```

All 30 tests should pass, covering schemas, state bus, policy engine, guardrails, and end-to-end replay scenarios.

## Next Steps

- [Configuration Guide](configuration.md) — Customize adapters, policy mode, and guardrails
- [Architecture Overview](../architecture/overview.md) — Understand the full pipeline
- [Writing Custom Adapters](../adapters/custom.md) — Integrate your own telemetry sources

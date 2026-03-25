# Roadmap

OpenAICE is actively developed. Here's what's planned for future versions.

## v1.0 (Current) :material-check-circle:{ .green }

- [x] Canonical state model (12 entity types)
- [x] State bus with fragment merging and freshness tracking
- [x] YAML-driven policy engine (5 rules)
- [x] Safety guardrails (confidence, freshness, cooldown, blast-radius)
- [x] Explainable recommendations with structured output
- [x] Adapters: Prometheus, Kubernetes, Slurm, GPU, Generic Serving, Replay
- [x] CLI with replay, serve, and state commands
- [x] FastAPI REST API
- [x] Replay-based golden tests
- [x] Docker support

## v1.1 (Near-term)

- [ ] GCM integration adapter (Meta GPU Cluster Monitoring)
- [ ] OpenTelemetry Collector receiver adapter
- [ ] Prometheus metrics exporter for OpenAICE itself
- [ ] Grafana dashboard templates
- [ ] Additional policy rules for LLM-specific scenarios
- [ ] WebSocket support for real-time recommendation streaming
- [ ] Helm chart for Kubernetes deployment

## v2.0 (Medium-term)

- [ ] **Actuation adapters** — Execute approved recommendations via K8s API / Slurm commands
- [ ] **Approval workflow** — Slack/Teams/PagerDuty integration for human-in-the-loop
- [ ] **Metadata enrichment adapters** — MLflow, W&B experiment tracker integration
- [ ] **Multi-cluster federation** — Manage recommendations across multiple clusters
- [ ] **Persistent state** — PostgreSQL/Redis backend for state bus (replace in-memory)
- [ ] **Recommendation history** — Historical analysis and trend detection
- [ ] **Policy simulation** — "What-if" mode to test policy changes against historical data

## v3.0 (Long-term)

- [ ] **ML-augmented policies** — Learned thresholds for anomaly detection
- [ ] **Cost optimization engine** — Cloud spend forecasting and right-sizing
- [ ] **Compliance reporting** — Audit reports for regulatory requirements
- [ ] **Go migration** — Performance-critical paths rewritten in Go
- [ ] **Plugin SDK** — First-class plugin architecture for third-party extensions

## Possible Expansions

- Integration with more GPU types (AMD ROCm, Intel Gaudi)
- Support for additional schedulers (PBS, LSF, Ray)
- Custom health check framework (similar to GCM health checks)
- Agent-based node collectors for bare-metal environments

---

!!! info "Contributing"
    Want to help build the future of OpenAICE? See the [Contributing Guide](contributing.md).

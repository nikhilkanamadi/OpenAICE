# Configuration

OpenAICE is configured via YAML files. The configuration controls which adapters are active, the policy mode, objective weights, and safety guardrails.

## Configuration File

```bash
python -m openaice.cli.cli serve --config configs/sample-k8s.yaml
```

## Full Configuration Reference

```yaml
# ─── Telemetry Sources ───
prometheus:
  enabled: true
  url: http://localhost:9090
  scrape_interval_seconds: 30
  metric_mappings: {}          # Map custom metric names to canonical fields
  label_filters: {}            # Filter by Prometheus labels

otel:
  enabled: false
  otlp_endpoint: http://localhost:4317
  protocol: grpc               # grpc | http

gpu_metrics:
  enabled: true
  prometheus_url: http://localhost:9090
  metric_prefix: DCGM_FI_DEV_

# ─── Runtime Sources ───
kubernetes:
  enabled: true
  kubeconfig_path: null         # null = use in-cluster or default
  namespaces:
    - default
    - prod
  resource_types:
    - deployments
    - services
    - nodes

slurm:
  enabled: false
  mode: cli                     # cli | rest | mock
  slurmrestd_url: null
  partitions: []
  mock_data_path: null

generic_serving:
  enabled: true
  prometheus_url: http://localhost:9090
  service_selectors: {}

# ─── Replay (for testing) ───
replay:
  enabled: false
  scenario_path: null

# ─── Policy ───
policy_mode: balanced           # balanced | latency_first | throughput_first |
                                # cost_first | reliability_first | fairness

control_mode: observe_only      # observe_only | recommend_with_approval |
                                # controlled_auto_act

objectives:
  latency: 0.30
  throughput: 0.20
  gpu_utilization: 0.20
  cost: 0.10
  reliability: 0.20

# ─── Safety Guardrails ───
guardrails:
  min_confidence_for_action: 0.75
  max_staleness_seconds: 120
  cooldown_seconds: 300
  max_change_magnitude:
    max_replica_jump: 3
    max_traffic_shift_pct: 20
  blast_radius_limit: 5         # Max entities affected per cycle

# ─── Rules & Packs ───
rules_path: policies/rules.yaml
policy_pack_path: policies/packs/balanced.yaml

# ─── Server ───
api_host: "0.0.0.0"
api_port: 8000
audit_log_path: audit.jsonl
```

## Control Modes

| Mode | Behavior |
|------|----------|
| `observe_only` | Generates recommendations but marks all as informational |
| `recommend_with_approval` | Generates actionable recommendations that require human approval |
| `controlled_auto_act` | Low/medium risk actions can auto-execute; high/critical still require approval |

!!! warning "Production Deployment"
    Start with `observe_only` in production. Move to `recommend_with_approval` once you've validated the recommendations match your expectations. `controlled_auto_act` is a v2 feature.

## Policy Modes

| Mode | Optimization Weight Distribution |
|------|------|
| `balanced` | latency=0.30, throughput=0.20, gpu_util=0.20, cost=0.10, reliability=0.20 |
| `latency_first` | Prioritizes p95/p99 latency reduction |
| `cost_first` | Prioritizes resource cost savings |
| `reliability_first` | Prioritizes uptime and health |
| `fairness` | Prioritizes equitable resource distribution (HPC) |

## Sample Configurations

OpenAICE ships with three sample configs:

- **`configs/sample-k8s.yaml`** — Kubernetes inference environment
- **`configs/sample-slurm.yaml`** — Slurm HPC environment
- **`configs/sample-hybrid.yaml`** — Hybrid K8s + Slurm environment

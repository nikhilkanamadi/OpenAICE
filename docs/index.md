---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

<div class="hero-logo">
  <img src="assets/logo-dark.svg" alt="OpenAICE Logo" class="hero-logo-img" />
</div>

# OpenAICE

**Auto Infrastructure Configuration Engine**

An adapter-based, recommendation-first control plane that unifies observability, orchestration, and policy across Kubernetes, Slurm, and hybrid AI infrastructure environments.

<div class="hero-buttons">
  <a href="getting-started/installation/" class="md-button md-button--primary">Get Started →</a>
  <a href="https://github.com/nikhilkanamadi/OpenAICE" class="md-button">View on GitHub</a>
</div>

</div>


<div class="feature-grid" markdown>

<div class="feature-card" markdown>

### :material-swap-horizontal-bold: Adapter-Based Architecture

Pluggable adapters for Prometheus, Kubernetes, Slurm, GPU (dcgm-exporter), and more. Tool-specific logic stays at the edge — the core engine is tool-agnostic.

</div>

<div class="feature-card" markdown>

### :material-shield-check: Safety-First Recommendations

Observe → Recommend → Approve → Auto-Act control ladder. Every recommendation carries confidence scores, risk levels, and structured explanations.

</div>

<div class="feature-card" markdown>

### :material-graph: Canonical State Model

12 entity types normalize diverse infrastructure signals into a unified graph. One policy engine reasons across Kubernetes inference and Slurm HPC training.

</div>

<div class="feature-card" markdown>

### :material-file-document-check: Explainable Decisions

Every recommendation includes `rule_id`, `reason`, `signals_used`, `confidence_score`, and `objectives_impacted`. No black-box automation.

</div>

<div class="feature-card" markdown>

### :material-cog-play: YAML-Driven Policy Engine

5 built-in decision rules covering queue pressure scaling, GPU batching optimization, node quarantine, idle scale-to-zero, and low-confidence failsafe.

</div>

<div class="feature-card" markdown>

### :material-replay: Telemetry Replay

Deterministic golden tests via recorded telemetry scenarios. Develop and validate without live infrastructure.

</div>

</div>

---

## Quick Example

```bash
# Run the K8s inference queue pressure replay scenario
python -m openaice.cli.cli replay \
  --scenario examples/telemetry-replay/k8s-inference-queue-pressure
```

```
═══ OpenAICE Replay Results ═══
Scenario: k8s-inference-queue-pressure
Entities loaded: 3
Recommendations: 1

┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┓
┃ ID            ┃ Entity        ┃ Action         ┃ Risk   ┃ Confidence ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━┩
│ rec-f4c1be0f  │ inference-api │ scale_replicas │ medium │       0.91 │
└───────────────┴───────────────┴────────────────┴────────┴────────────┘

Explanations:
  rec-f4c1be0f: p95 latency exceeded target and queue depth rising
    Signals: latency_p95_ms, queue_depth, available_replicas
    Objectives: latency, reliability
```

---

## Scenario Coverage

OpenAICE covers **8 scenario families** across the AI infrastructure landscape:

| Scenario Family | Key Entities | Example Workloads |
|----------------|-------------|-------------------|
| :material-kubernetes: **K8s Online Inference** | Service, Deployment, GPU | Model serving, API endpoints |
| :material-layers-triple: **Batch Inference** | Job, Queue | Offline scoring, batch prediction |
| :fontawesome-solid-server: **Distributed Training** | Job, GPU, Node | Multi-node training runs |
| :material-chip: **HPC / Research** | Job, Node, Queue, GPU | Slurm-scheduled GPU research |
| :material-robot: **LLM Serving** | Service, ModelRevision | vLLM, Triton, TGI endpoints |
| :material-cloud: **Managed Cloud** | Service, Deployment | Cloud ML platform endpoints |
| :material-vector-combine: **Hybrid** | All entity types | K8s + Slurm unified management |
| :material-shield-lock: **Governance / Ops** | TenantScope, SchedulerDomain | Multi-tenant policy enforcement |

---

## License

OpenAICE is licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).

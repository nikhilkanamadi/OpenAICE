<div align="center">
  <img src="docs/assets/logo-dark.svg" alt="OpenAICE Logo" width="140" height="140" />
  <h1>OpenAICE</h1>
  <p><strong>Auto Infrastructure Configuration Engine</strong></p>
  <p>An adapter-based, recommendation-first control plane that unifies observability, orchestration, and policy across Kubernetes, Slurm, and hybrid AI infrastructure environments.</p>

  <p>
    <a href="https://nikhilkanamadi.github.io/OpenAICE/"><img src="https://img.shields.io/badge/docs-MkDocs-blue" alt="Docs"></a>
    <a href="https://github.com/nikhilkanamadi/OpenAICE/actions"><img src="https://img.shields.io/badge/build-passing-success" alt="Build Status"></a>
    <a href="https://pypi.org/project/openaice/"><img src="https://img.shields.io/pypi/v/openaice.svg" alt="PyPI"></a>
    <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  </p>
</div>

---

## What is OpenAICE?

**OpenAICE** is a recommendation-first control plane designed for modern AI infrastructure. It acts as the bridge between **observability** (Prometheus, DCGM, Slurm accounting) and **actuation** (Kubernetes API, Slurm controllers). 

Unlike traditional autoscale controllers that operate as black boxes, OpenAICE provides a transparent **Canonical State Model** and an explainable **Policy Engine**. Every scaling decision, node quarantine, or queue rebalancing action is output as a structured recommendation with a rationale, confidence score, and associated risks.

### Core Philosophy
- **Integration Stays at the Edge**: Adapters abstract away the nuances of K8s vs. Slurm.
- **Safety-First**: "Observe → Recommend → Approve → Act" ladder prevents runaway scaling.
- **Explainability**: Every action has a documented `rule_id` and `reason`.

## Quick Start

### Installation

```bash
# Recommended: Install via Poetry
git clone https://github.com/nikhilkanamadi/OpenAICE.git
cd openaice
pip install poetry
poetry install
```

*(Docker images and PyPI packages coming soon).*

### Run a Telemetry Replay

Test the engine without live infrastructure using our deterministic replay scenarios:

```bash
python -m openaice.cli.cli replay \
  --scenario examples/telemetry-replay/k8s-inference-queue-pressure
```

**Output:**
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
```

## Documentation

Full documentation is available at **[https://nikhilkanamadi.github.io/OpenAICE/](https://nikhilkanamadi.github.io/OpenAICE/)**, including:
- Architecture Overview & Mermaid Diagrams
- Writing Custom Adapters
- Policy Engine Configuration
- API & CLI Reference

## Reference Architecture

OpenAICE sits between your **observability stack** and your **infrastructure controllers**, normalizing signals from heterogeneous systems into a single canonical state graph:

```
┌─────────────────────────────────────────────────────────────────┐
│                     TELEMETRY SOURCES                           │
│                                                                 │
│  Prometheus ──┐   dcgm-exporter ──┐   Slurm CLI/REST ──┐       │
│  (PromQL)     │   (GPU metrics)   │   (squeue/sinfo)   │       │
│               ▼                   ▼                    ▼       │
│         ┌──────────┐       ┌──────────┐         ┌──────────┐   │
│         │ Telemetry│       │   GPU    │         │  Runtime │   │
│         │ Adapter  │       │ Adapter  │         │  Adapter │   │
│         └────┬─────┘       └────┬─────┘         └────┬─────┘   │
│              │                  │                    │          │
│              ▼                  ▼                    ▼          │
│        ┌─────────────────────────────────────────────────┐      │
│        │              NORMALIZER                         │      │
│        │    Raw records → Validated StateFragments       │      │
│        └─────────────────────┬───────────────────────────┘      │
│                              ▼                                  │
│        ┌─────────────────────────────────────────────────┐      │
│        │              STATE BUS                          │      │
│        │    Merge fragments by entity_id, track          │      │
│        │    freshness, build canonical entity graph      │      │
│        └─────────────────────┬───────────────────────────┘      │
│                              ▼                                  │
│        ┌─────────────────────────────────────────────────┐      │
│        │         WORKLOAD CLASSIFIER                     │      │
│        │    Assign scenario family per entity            │      │
│        └─────────────────────┬───────────────────────────┘      │
│                              ▼                                  │
│        ┌─────────────────────────────────────────────────┐      │
│        │           POLICY ENGINE                         │      │
│        │    Match YAML rules × classified entities       │      │
│        │    Generate candidate recommendations           │      │
│        └─────────────────────┬───────────────────────────┘      │
│                              ▼                                  │
│        ┌─────────────────────────────────────────────────┐      │
│        │            GUARDRAILS                           │      │
│        │    Confidence · Freshness · Cooldown · Blast    │      │
│        └─────────────────────┬───────────────────────────┘      │
│                              ▼                                  │
│              ┌───────────┬────────────┬──────────┐              │
│              │ CLI/Rich  │ REST API   │ Audit    │              │
│              │ Tables    │ (FastAPI)  │ JSONL    │              │
│              └───────────┴────────────┴──────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## Infrastructure Integrations

OpenAICE uses a **pluggable adapter architecture** to interconnect with diverse AI infrastructure systems. Each adapter translates tool-specific APIs into canonical state fragments — the core engine never sees raw payloads.

### Telemetry Adapters (Read-Only)

| System | Adapter | Connection Method | Data Collected | Canonical Entities |
|--------|---------|-------------------|----------------|-------------------|
| **Prometheus** | `PrometheusAdapter` | PromQL HTTP API (`/api/v1/query`) | p95/p99 latency, throughput, error rate, queue depth | `service` |
| **NVIDIA dcgm-exporter** | `GPUMetricsAdapter` | Prometheus scrape of DCGM metrics | GPU utilization, memory, temperature, ECC errors, power | `gpu` |
| **OpenTelemetry** *(v1.1)* | `OTelAdapter` | OTLP gRPC/HTTP receiver | Traces, metrics, spans | `service`, `deployment` |

### Runtime State Adapters

| System | Adapter | Connection Method | Data Collected | Canonical Entities |
|--------|---------|-------------------|----------------|-------------------|
| **Kubernetes** | `KubernetesAdapter` | K8s API (in-cluster or kubeconfig) | Deployments, Nodes, Services, resource utilization | `deployment`, `node`, `service` |
| **Slurm** | `SlurmAdapter` | CLI (`squeue`/`sinfo`/`sacct`), REST (`slurmrestd`), or mock YAML | Jobs, nodes, queues, partitions, GPU assignments | `job`, `node`, `queue` |
| **Generic Serving** | `GenericServingAdapter` | Prometheus metrics from any serving framework | Standard serving metrics (latency, RPS, errors) | `service` |

### How Adapters Feed the Core Engine

1. **Adapters emit StateFragments** — partial updates with a `source_type`, `entity_id`, and observed fields
2. **Normalizer validates** each fragment against the canonical schema (Pydantic models)
3. **State Bus merges** fragments by `entity_id` — newer data wins, stale data is rejected
4. **Workload Classifier** tags each entity with a scenario family (e.g., `online_inference`, `hpc_research`)
5. **Policy Engine** evaluates YAML rules against classified entities and generates recommendations
6. **Guardrails** enforce safety constraints (confidence threshold, data freshness, cooldown, blast-radius)

### Cross-System Correlation

The canonical state model enables **cross-system reasoning** that individual tools cannot provide:

```
Prometheus (latency spike)  ──┐
                              ├──→  Service Entity  ──→  Policy: "scale_replicas"
Kubernetes (low replicas)   ──┘

dcgm-exporter (ECC errors)  ──┐
                               ├──→  Node Entity    ──→  Policy: "quarantine_node"
Slurm (node state degraded) ──┘

Prometheus (zero throughput) ──┐
                               ├──→  Service Entity  ──→  Policy: "enable_scale_to_zero"
Kubernetes (idle deployment) ──┘
```

## Scenario Families

OpenAICE covers **8 scenario families** spanning the full spectrum of modern AI workloads:

| Scenario Family | Infrastructure | Key Adapters | Example Recommendations |
|----------------|---------------|-------------|------------------------|
| **K8s Online Inference** | Kubernetes | Prometheus + K8s | Scale replicas on queue pressure |
| **Batch Inference** | Kubernetes | Prometheus + K8s | Adjust job priority or quota |
| **Distributed Training** | Kubernetes / Slurm | GPU + Slurm + K8s | Checkpoint frequency, node replacement |
| **HPC / Research** | Slurm | Slurm + GPU | Quarantine unhealthy nodes, preempt jobs |
| **LLM Serving** | Kubernetes | Prometheus + GPU + K8s | Adjust batching before scale-out |
| **Managed Cloud** | Cloud ML Platforms | Generic Serving | Enable scale-to-zero for idle services |
| **Hybrid (K8s + Slurm)** | Mixed | All adapters | Unified policy across scheduler domains |
| **Governance / Multi-Tenant** | Any | K8s + Slurm | Fairness-based quota adjustments |

### Control Modes

| Mode | Behavior | Recommended For |
|------|----------|----------------|
| `observe_only` | Generate recommendations as informational output only | Initial deployment, evaluation |
| `recommend_with_approval` | Actionable recommendations requiring human approval | Production monitoring |
| `controlled_auto_act` *(v2)* | Low/medium risk actions auto-execute; high/critical require approval | Trusted environments |

## VS Code Extension

OpenAICE includes a **VS Code extension** that brings infrastructure state and recommendations directly into your editor.

### Features

| Feature | Description |
|---------|-------------|
| **Infrastructure State Sidebar** | Entities grouped by type (service, gpu, node, job) with health indicators |
| **Recommendations Panel** | Active recommendations with risk levels and confidence scores |
| **Recommendation Detail** | Click any recommendation for a rich webview with signals, objectives, and action parameters |
| **Replay Scenarios** | `Cmd+Shift+P` → "OpenAICE: Run Replay" — test without live infrastructure |
| **Status Bar** | Live connection state, entity count, and recommendation count |
| **Auto-Refresh** | Configurable polling interval (default: 30s) |

### Install

```bash
# From the packaged VSIX
code --install-extension openaice-vscode/openaice-0.1.0.vsix

# Then start the backend
python -m openaice.cli.cli serve --config configs/sample-k8s.yaml
```

The extension auto-connects to `http://localhost:8000` and displays state in the sidebar.

## Roadmap

- **v1.0 (Current)**: Recommendation Engine, Canonical State Model, K8s/Slurm Replay testing, VS Code Extension.
- **v1.1**: Chat participant (`@openaice` in VS Code chat), Grafana dashboards, WebSocket streaming.
- **v2.0**: Actuation adapters (moving from "recommend" to "auto-act"), persistent State Bus.
- **v3.0**: Cross-cluster hybrid bursting, LLM-based policy generation.

## Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing.md) for details on setting up your development environment, running the test suite (100% passing golden tests), and submitting Pull Requests.

## License

OpenAICE is licensed under the [Apache 2.0 License](LICENSE).

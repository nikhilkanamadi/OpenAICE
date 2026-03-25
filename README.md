<div align="center">
  <img src="docs/assets/logo-dark.svg" alt="OpenAICE Logo" width="140" height="140" />
  <h1>OpenAICE</h1>
  <p><strong>Auto Infrastructure Configuration Engine</strong></p>
  <p>An adapter-based, recommendation-first control plane that unifies observability, orchestration, and policy across Kubernetes, Slurm, and hybrid AI infrastructure environments.</p>

  <p>
    <a href="https://nikhilkanamadi.github.io/OpenAICE-auto-infrastructure-configuration-engine/"><img src="https://img.shields.io/badge/docs-MkDocs-blue" alt="Docs"></a>
    <a href="https://github.com/nikhilkanamadi/OpenAICE-auto-infrastructure-configuration-engine/actions"><img src="https://img.shields.io/badge/build-passing-success" alt="Build Status"></a>
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
git clone https://github.com/nikhilkanamadi/OpenAICE-auto-infrastructure-configuration-engine.git
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

Full documentation is available at **[https://nikhilkanamadi.github.io/OpenAICE-auto-infrastructure-configuration-engine/](https://nikhilkanamadi.github.io/OpenAICE-auto-infrastructure-configuration-engine/)**, including:
- Architecture Overview & Mermaid Diagrams
- Writing Custom Adapters
- Policy Engine Configuration
- API & CLI Reference

## Roadmap

- **v1.0 (Current)**: Recommendation Engine, Canonical State Model, K8s/Slurm Replay testing.
- **v2.0**: Actuation adapters (moving from "recommend" to "auto-act"), persistent State Bus.
- **v3.0**: Cross-cluster hybrid bursting, LLM-based policy generation.

## Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing.md) for details on setting up your development environment, running the test suite (100% passing golden tests), and submitting Pull Requests.

## License

OpenAICE is licensed under the [Apache 2.0 License](LICENSE).

# Architecture Overview

OpenAICE follows a **layered architecture** with strict separation between data collection (adapters), state management (bus), decision-making (policy engine), and safety (guardrails).

## System Architecture

```mermaid
graph TD
    subgraph Adapters["🔌 Adapters (Edge)"]
        PROM[Prometheus]
        K8S[Kubernetes API]
        SLURM[Slurm CLI/REST]
        GPU[dcgm-exporter]
        REPLAY[Replay Files]
    end

    subgraph Core["⚙️ Core Engine"]
        NORM[Normalizer]
        BUS[State Bus]
        CLASS[Workload Classifier]
        POLICY[Policy Engine]
        REC[Recommender]
        GUARD[Guardrails]
        AUDIT[Audit Log]
    end

    subgraph Output["📤 Output"]
        CLI[CLI / Rich Tables]
        API[FastAPI REST]
        LOG[Audit JSONL]
    end

    PROM --> NORM
    K8S --> NORM
    SLURM --> NORM
    GPU --> NORM
    REPLAY --> NORM

    NORM -->|State Fragments| BUS
    BUS -->|Canonical Entities| CLASS
    CLASS --> POLICY
    POLICY -->|Recommendations| REC
    REC --> GUARD
    GUARD --> AUDIT
    GUARD --> CLI
    GUARD --> API
    GUARD --> LOG
```

## Pipeline Flow

The control plane operates as a **sequential pipeline** on each evaluation cycle:

```mermaid
sequenceDiagram
    participant A as Adapters
    participant N as Normalizer
    participant S as State Bus
    participant C as Classifier
    participant P as Policy Engine
    participant G as Guardrails
    participant O as Output

    A->>N: Raw records
    N->>S: State fragments (validated)
    S->>S: Merge by entity_id
    S->>C: Canonical entities
    C->>C: Classify workload type
    C->>P: Classified entities
    P->>P: Match rules × entities
    P->>G: Candidate recommendations
    G->>G: Confidence, freshness, cooldown, blast-radius
    G->>O: Approved recommendations + explanations
```

## Key Design Principles

### 1. Integration Logic Stays at the Edge
Adapters handle all tool-specific translation. The core engine never sees raw Prometheus metrics or Kubernetes API objects — only canonical entities.

### 2. Policy is Data, Not Code
Decision rules live in `policies/rules.yaml`, not in Python source. This means:

- Non-engineers can review and modify policies
- Rules can be version-controlled independently
- Different environments can use different rule sets

### 3. Safety is Non-Negotiable
Every recommendation passes through 4 guardrails:

| Guardrail | What it checks |
|-----------|---------------|
| **Confidence threshold** | Entity confidence ≥ minimum for the action |
| **Data freshness** | Telemetry data is recent enough to act on |
| **Cooldown window** | Enough time has passed since last action on this entity |
| **Blast-radius limit** | Total entities affected per cycle doesn't exceed the cap |

### 4. Explainability by Default
Every recommendation includes:

- `rule_id` — which YAML rule fired
- `reason` — human-readable explanation
- `signals_used` — what telemetry signals triggered it
- `objectives_impacted` — which business objectives are affected
- `confidence_score` — how confident the system is

## Module Responsibilities

| Module | File | Responsibility |
|--------|------|---------------|
| **Normalizer** | `core/normalizer.py` | Converts raw adapter records into typed `StateFragment` objects |
| **State Bus** | `core/state_bus.py` | In-memory store that merges fragments by entity_id, tracks freshness |
| **Classifier** | `core/workload_classifier.py` | Assigns scenario family (e.g., `online_inference`, `hpc_research`) |
| **Policy Engine** | `core/policy_engine.py` | Evaluates YAML rules against classified entities |
| **Recommender** | `core/recommender.py` | Scores recommendations and generates structured explanations |
| **Guardrails** | `core/guardrails.py` | Enforces safety constraints before any recommendation is surfaced |
| **Audit Log** | `core/audit_log.py` | Writes immutable JSONL records for every recommendation lifecycle event |

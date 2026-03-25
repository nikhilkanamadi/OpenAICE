# Policy Rules Guide

Learn how to write, customize, and extend OpenAICE's YAML decision rules.

## Rule Anatomy

Every rule has 7 sections:

```yaml
- rule_id: my_custom_rule             # 1. Unique identifier
  scenario_family: hpc_or_training    # 2. Which workloads it applies to
  preconditions:                      # 3. Field guards
    - "scheduler_domain == slurm"
  required_signals:                   # 4. Required non-null fields
    - health_state
  recommended_action:                 # 5. What to do
    action_type: quarantine_node
    parameters: {}
  risk_level: high                    # 6. Risk classification
  minimum_confidence: 0.85            # 7. Confidence gate
  reason: "Node {entity_id} health degraded"
  expected_benefit: "Prevented failures"
```

## Writing Custom Rules

### Step 1: Identify the Scenario

Choose a `scenario_family`:

| Family | Workload Types |
|--------|---------------|
| `kubernetes_online_inference` | `online_inference` |
| `llm_or_inference_serving` | `llm_serving`, `online_inference` |
| `hpc_or_training` | `hpc_research`, `distributed_training` |
| `batch` | `batch_inference` |
| `any` | All |

### Step 2: Define Preconditions

Use `field == value` syntax:

```yaml
preconditions:
  - "workload_type == online_inference"
  - "scheduler_domain == kubernetes"
```

Supported operators: `==`, `!=`

### Step 3: Specify Required Signals

List the entity fields that **must be non-null** for the rule to fire:

```yaml
required_signals:
  - latency_p95_ms
  - queue_depth
```

### Step 4: Choose an Action

Pick from the [14 available action types](../architecture/policy-engine.md#all-14-action-types).

### Step 5: Set Risk and Confidence

| Risk Level | Confidence Minimum | Use Case |
|-----------|-------------------|----------|
| `low` | 0.60 | Informational, low-impact |
| `medium` | 0.75 | Standard operational changes |
| `high` | 0.85 | Changes affecting availability |
| `critical` | 0.90 | Always requires human approval |

## Example: Custom GPU Temperature Rule

```yaml
- rule_id: gpu_thermal_throttle_warning
  scenario_family: any
  preconditions:
    - "health_state != healthy"
  required_signals:
    - temperature_celsius
  recommended_action:
    action_type: quarantine_node
    parameters:
      reason: thermal_throttle
  risk_level: high
  minimum_confidence: 0.80
  reason: "GPU {entity_id} temperature critical — recommend quarantine"
  expected_benefit: "Prevented thermal throttling and potential hardware damage"
```

## Policy Packs

Policy packs set the thresholds and objective weights:

```yaml
# policies/packs/latency_first.yaml
policy_mode: latency_first

thresholds:
  target_p95_ms: 100       # Tighter latency target
  target_p99_ms: 300

objective_weights:
  latency: 0.50            # Heavily weight latency
  throughput: 0.15
  gpu_utilization: 0.10
  cost: 0.05
  reliability: 0.20
```

# Kubernetes Adapter

Reads runtime state from the Kubernetes API to create canonical entities for Deployments, Nodes, and Services.

## Configuration

```yaml
kubernetes:
  enabled: true
  kubeconfig_path: null   # null = in-cluster or ~/.kube/config
  namespaces:
    - default
    - prod
    - ml-serving
```

## Collected Entities

| K8s Resource | Entity Type | Key Fields |
|-------------|-------------|-----------|
| Deployment | `deployment` | replica_count, available_replicas, desired_replicas |
| Node | `node` | cpu_utilization, memory_utilization, gpu_count, health_state |
| Service | `service` | service_state, owner_scope |

## Mock Mode

When the Kubernetes API is unavailable, the adapter falls back to **mock mode** for development:

```python
# Automatically falls back to mock when K8s is unreachable
# Generates sample entities for testing
```

!!! tip "Development Workflow"
    Use the [Replay adapter](../guide/replay.md) for deterministic testing instead of the K8s mock mode.

## Health State Mapping

| K8s Condition | OpenAICE Health State |
|--------------|---------------------|
| All conditions True | `healthy` |
| MemoryPressure / DiskPressure | `degraded` |
| NotReady | `critical` |
| Unknown conditions | `unknown` |

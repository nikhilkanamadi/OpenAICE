# Slurm Adapter

Reads HPC cluster state from Slurm via CLI commands, REST API, or mock data.

## Configuration

=== "CLI Mode"

    ```yaml
    slurm:
      enabled: true
      mode: cli
      partitions:
        - gpu
        - compute
    ```

=== "REST Mode"

    ```yaml
    slurm:
      enabled: true
      mode: rest
      slurmrestd_url: http://slurmrestd:6820
      partitions:
        - gpu
    ```

=== "Mock Mode"

    ```yaml
    slurm:
      enabled: true
      mode: mock
      mock_data_path: examples/telemetry-replay/slurm-node-health-warning/inputs/telemetry.yaml
    ```

## Modes

| Mode | Source | Use Case |
|------|--------|----------|
| `cli` | `squeue`, `sinfo`, `sacct` shell commands | Production Slurm clusters |
| `rest` | Slurm REST API (`slurmrestd`) | REST-enabled clusters |
| `mock` | YAML file | Development and testing |

## Collected Entities

| Slurm Command | Entity Type | Key Fields |
|--------------|-------------|-----------|
| `squeue` | `job` | job_state, assigned_gpu_count, user |
| `sinfo` | `node` | health_state, cpu_utilization, partitions |
| `sacct` | `job` | elapsed_time, exit_code, gpu_utilization |

## CLI Commands Used

```bash
squeue --json                    # Job queue state
sinfo --json                     # Node state
sacct --json -S now-1hour        # Recent job accounting
```

## GCM Integration

!!! tip "Meta GCM Compatibility"
    OpenAICE's Slurm adapter is designed to complement [Meta's GPU Cluster Monitoring (GCM)](https://github.com/facebookresearch/gcm).
    GCM provides the data collection layer, while OpenAICE adds the policy and recommendation layer on top.

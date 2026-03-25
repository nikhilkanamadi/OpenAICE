# GPU Metrics Adapter

Ingests GPU telemetry from NVIDIA's dcgm-exporter via Prometheus.

## Configuration

```yaml
gpu_metrics:
  enabled: true
  prometheus_url: http://localhost:9090
  metric_prefix: DCGM_FI_DEV_   # Default dcgm-exporter prefix
```

## Collected Fields

| DCGM Metric | Entity Field | Description |
|------------|-------------|-------------|
| `DCGM_FI_DEV_GPU_UTIL` | `gpu_utilization` | GPU compute utilization (0-1) |
| `DCGM_FI_DEV_FB_USED` | `gpu_memory_used` | Frame buffer memory used |
| `DCGM_FI_DEV_FB_FREE` | `gpu_memory_total` | Frame buffer total (computed) |
| `DCGM_FI_DEV_GPU_TEMP` | `temperature_celsius` | GPU temperature |
| `DCGM_FI_DEV_ECC_DBE_VOL_TOTAL` | `ecc_errors` | Double-bit ECC errors |
| `DCGM_FI_DEV_POWER_USAGE` | `power_watts` | Power consumption |

## Entity ID Format

GPU entities are identified as: `{hostname}-gpu{index}`

Example: `gpu-node-17-gpu0`

## Health State Logic

| Condition | Health State |
|-----------|-------------|
| Temperature > 90°C | `critical` |
| Temperature > 80°C | `warning` |
| ECC errors > 0 | `degraded` |
| Normal operation | `healthy` |

## Prerequisites

Ensure [dcgm-exporter](https://github.com/NVIDIA/dcgm-exporter) is deployed and scraped by Prometheus:

```bash
# Verify dcgm-exporter metrics are available
curl http://localhost:9090/api/v1/query?query=DCGM_FI_DEV_GPU_UTIL
```

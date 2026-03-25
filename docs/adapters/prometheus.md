# Prometheus Adapter

Ingests metrics from Prometheus via PromQL queries.

## Configuration

```yaml
prometheus:
  enabled: true
  url: http://localhost:9090
  scrape_interval_seconds: 30
```

## Default PromQL Queries

| Metric | Query | Entity Field |
|--------|-------|-------------|
| p95 Latency | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` | `latency_p95_ms` |
| p99 Latency | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` | `latency_p99_ms` |
| Throughput | `sum(rate(http_requests_total[5m])) by (service)` | `throughput` |
| Error Rate | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` | `error_rate` |
| Queue Depth | `sum(pending_requests) by (service)` | `queue_depth` |

## Entity Mapping

The Prometheus adapter creates `ServiceEntity` fragments with the following mapping:

```
job label       → entity_id
namespace label → owner_scope
cluster label   → scheduler_domain
```

## Custom Metric Mappings

Override default queries in the config:

```yaml
prometheus:
  enabled: true
  url: http://prometheus:9090
  metric_mappings:
    latency_p95: 'histogram_quantile(0.95, rate(my_custom_metric_bucket[5m]))'
    throughput: 'sum(rate(my_custom_rps[5m])) by (service)'
```

"""
Prometheus Telemetry Adapter — queries Prometheus for metrics and produces state fragments.

Reference: 02 (section 1), 03 (section 4)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from openaice.adapters.base import TelemetryAdapter

logger = logging.getLogger(__name__)


class PrometheusAdapter(TelemetryAdapter):
    """
    Queries Prometheus via its HTTP API and converts metrics into
    canonical state fragment dicts.
    """

    name = "prometheus"
    version = "0.1.0"

    def __init__(self) -> None:
        self._url: str = "http://localhost:9090"
        self._metric_mappings: dict[str, str] = {}
        self._label_filters: dict[str, str] = {}
        self._client: httpx.Client | None = None

    def initialize(self, config: dict[str, Any]) -> None:
        self._url = config.get("url", self._url)
        self._metric_mappings = config.get("metric_mappings", {})
        self._label_filters = config.get("label_filters", {})
        self._client = httpx.Client(base_url=self._url, timeout=10.0)

    def collect(self) -> list[dict[str, Any]]:
        """Query configured Prometheus metrics."""
        records: list[dict[str, Any]] = []

        # Default queries for common AI infra metrics
        default_queries = {
            "latency_p95_ms": 'histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m])) * 1000',
            "throughput": 'sum(rate(request_total[5m])) by (service)',
            "error_rate": 'sum(rate(request_errors_total[5m])) by (service) / sum(rate(request_total[5m])) by (service)',
            "gpu_utilization": 'DCGM_FI_DEV_GPU_UTIL',
            "gpu_memory_used": 'DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_FREE',
        }

        queries = {**default_queries, **self._metric_mappings}

        for field_name, promql in queries.items():
            try:
                results = self._query(promql)
                for result in results:
                    record = self._result_to_record(field_name, result)
                    if record:
                        records.append(record)
            except Exception as e:
                logger.warning("Prometheus query failed for %s: %s", field_name, e)

        return records

    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Already normalized during collection."""
        return raw_records

    def _query(self, promql: str) -> list[dict[str, Any]]:
        """Execute a PromQL instant query."""
        if not self._client:
            return []

        try:
            resp = self._client.get("/api/v1/query", params={"query": promql})
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") == "success":
                return data.get("data", {}).get("result", [])
        except Exception as e:
            logger.warning("PromQL query error: %s", e)

        return []

    def _result_to_record(
        self, field_name: str, result: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Convert a Prometheus result into a state fragment dict."""
        metric = result.get("metric", {})
        value = result.get("value", [])

        if len(value) < 2:
            return None

        # Determine entity ID from labels
        entity_id = (
            metric.get("service")
            or metric.get("deployment")
            or metric.get("job")
            or metric.get("instance")
            or metric.get("pod")
            or "unknown"
        )

        # Apply label filters
        for key, expected in self._label_filters.items():
            if metric.get(key) != expected:
                return None

        # Determine entity type from labels
        entity_type = "service"  # default
        if "job" in metric and "service" not in metric:
            entity_type = "job"
        if "node" in metric:
            entity_type = "node"
        if "gpu" in metric.get("__name__", "").lower() or "DCGM" in metric.get("__name__", ""):
            entity_type = "gpu"

        try:
            metric_value = float(value[1])
        except (ValueError, TypeError):
            return None

        return {
            "source_type": "prometheus",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "observed_at": datetime.utcnow().isoformat(),
            field_name: metric_value,
            "labels": metric,
        }

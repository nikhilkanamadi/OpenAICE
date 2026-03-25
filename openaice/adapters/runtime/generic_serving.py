"""
Generic Serving Adapter — ingests standard serving metrics (latency, throughput, queue).

Works with any Prometheus-instrumented model serving system without
vendor lock-in to KServe, Triton, or vLLM.

Reference: 07 (section 9)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from openaice.adapters.base import RuntimeStateAdapter

logger = logging.getLogger(__name__)


class GenericServingAdapter(RuntimeStateAdapter):
    """
    Reads standard serving metrics from Prometheus and maps them
    to canonical Service entities.
    """

    name = "generic_serving"
    version = "0.1.0"

    def __init__(self) -> None:
        self._prometheus_url = "http://localhost:9090"
        self._service_selectors: dict[str, str] = {}
        self._client: httpx.Client | None = None

    def initialize(self, config: dict[str, Any]) -> None:
        self._prometheus_url = config.get("prometheus_url", self._prometheus_url)
        self._service_selectors = config.get("service_selectors", {})
        self._client = httpx.Client(base_url=self._prometheus_url, timeout=10.0)

    def snapshot(self) -> list[dict[str, Any]]:
        """Query serving metrics and build service entity records."""
        records: list[dict[str, Any]] = []

        # Standard serving metric queries
        queries = {
            "latency_p95_ms": 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)) * 1000',
            "latency_p99_ms": 'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)) * 1000',
            "throughput": 'sum(rate(http_requests_total[5m])) by (service)',
            "error_rate": 'sum(rate(http_requests_total{status=~"5.."}[5m])) by (service) / sum(rate(http_requests_total[5m])) by (service)',
            "queue_depth": 'sum(http_requests_in_flight) by (service)',
        }

        # Collect metrics per service
        service_data: dict[str, dict[str, Any]] = {}

        for field_name, promql in queries.items():
            try:
                results = self._query(promql)
                for result in results:
                    service_name = result.get("metric", {}).get("service", "unknown")
                    if service_name not in service_data:
                        service_data[service_name] = {}

                    value = result.get("value", [])
                    if len(value) >= 2:
                        try:
                            service_data[service_name][field_name] = float(value[1])
                        except (ValueError, TypeError):
                            pass
            except Exception as e:
                logger.warning("Serving metric query failed for %s: %s", field_name, e)

        # Build records
        for service_name, metrics in service_data.items():
            record = {
                "source_type": "generic_serving",
                "entity_type": "service",
                "entity_id": service_name,
                "observed_at": datetime.utcnow().isoformat(),
                "scheduler_domain": "kubernetes",
                "workload_type": "online_inference",
                **metrics,
            }
            records.append(record)

        return records

    def _query(self, promql: str) -> list[dict]:
        if not self._client:
            return []
        try:
            resp = self._client.get("/api/v1/query", params={"query": promql})
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "success":
                return data.get("data", {}).get("result", [])
        except Exception as e:
            logger.debug("Generic serving query error: %s", e)
        return []

"""
GPU Metrics Adapter — ingests dcgm-exporter metrics via Prometheus.

Reference: 02 (section 3)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from openaice.adapters.base import TelemetryAdapter

logger = logging.getLogger(__name__)


class GpuMetricsAdapter(TelemetryAdapter):
    """Reads DCGM GPU metrics via Prometheus and maps to GPU entities."""

    name = "gpu_metrics"
    version = "0.1.0"

    def __init__(self) -> None:
        self._prometheus_url = "http://localhost:9090"
        self._client: httpx.Client | None = None

    def initialize(self, config: dict[str, Any]) -> None:
        self._prometheus_url = config.get("prometheus_url", self._prometheus_url)
        self._client = httpx.Client(base_url=self._prometheus_url, timeout=10.0)

    def collect(self) -> list[dict[str, Any]]:
        """Query DCGM metrics from Prometheus."""
        records: list[dict[str, Any]] = []

        dcgm_queries = {
            "gpu_utilization": "DCGM_FI_DEV_GPU_UTIL",
            "gpu_memory_used": "DCGM_FI_DEV_FB_USED",
            "gpu_memory_total": "DCGM_FI_DEV_FB_FREE + DCGM_FI_DEV_FB_USED",
            "temperature_celsius": "DCGM_FI_DEV_GPU_TEMP",
            "power_draw_watts": "DCGM_FI_DEV_POWER_USAGE",
        }

        for field_name, query in dcgm_queries.items():
            try:
                results = self._query(query)
                for result in results:
                    record = self._to_record(field_name, result)
                    if record:
                        records.append(record)
            except Exception as e:
                logger.warning("GPU metrics query failed for %s: %s", field_name, e)

        return records

    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return raw_records

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
            logger.warning("GPU PromQL query error: %s", e)
        return []

    def _to_record(self, field_name: str, result: dict) -> dict[str, Any] | None:
        metric = result.get("metric", {})
        value = result.get("value", [])
        if len(value) < 2:
            return None

        gpu_id = metric.get("gpu", metric.get("UUID", metric.get("instance", "unknown")))
        entity_id = f"gpu-{gpu_id}"

        try:
            val = float(value[1])
            # Normalize utilization to 0-1 range if reported as percentage
            if field_name == "gpu_utilization" and val > 1.0:
                val = val / 100.0
        except (ValueError, TypeError):
            return None

        return {
            "source_type": "dcgm",
            "entity_type": "gpu",
            "entity_id": entity_id,
            "observed_at": datetime.utcnow().isoformat(),
            field_name: val,
            "labels": metric,
        }

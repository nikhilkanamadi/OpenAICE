"""
Slurm Runtime Adapter — reads Slurm job, node, and queue state.

Supports three modes:
- cli: parses squeue/sinfo/sacct JSON output
- rest: queries slurmrestd API (Slurm >=21.08)
- mock: uses static fixture data for development

Reference: 02 (section 4), 04 (scenario families 3-4)
"""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from openaice.adapters.base import RuntimeStateAdapter

logger = logging.getLogger(__name__)


class SlurmAdapter(RuntimeStateAdapter):
    """
    Reads Slurm HPC state and maps to canonical Job, Node, Queue, GPU entities.
    """

    name = "slurm"
    version = "0.1.0"

    def __init__(self) -> None:
        self._mode: str = "mock"
        self._slurmrestd_url: str | None = None
        self._partitions: list[str] = []
        self._mock_data_path: str | None = None

    def initialize(self, config: dict[str, Any]) -> None:
        self._mode = config.get("mode", "mock")
        self._slurmrestd_url = config.get("slurmrestd_url")
        self._partitions = config.get("partitions", [])
        self._mock_data_path = config.get("mock_data_path")

    def snapshot(self) -> list[dict[str, Any]]:
        """Get current Slurm state."""
        if self._mode == "mock":
            return self._mock_snapshot()
        elif self._mode == "cli":
            return self._cli_snapshot()
        elif self._mode == "rest":
            return self._rest_snapshot()
        return []

    # ------------------------------------------------------------------
    # CLI mode
    # ------------------------------------------------------------------

    def _cli_snapshot(self) -> list[dict[str, Any]]:
        """Parse Slurm CLI output (squeue, sinfo)."""
        records: list[dict[str, Any]] = []
        records.extend(self._parse_squeue())
        records.extend(self._parse_sinfo())
        return records

    def _parse_squeue(self) -> list[dict[str, Any]]:
        """Parse `squeue --json` output."""
        try:
            result = subprocess.run(
                ["squeue", "--json"],
                capture_output=True, text=True, timeout=10
            )
            data = json.loads(result.stdout)
            records = []
            for job in data.get("jobs", []):
                records.append({
                    "source_type": "slurm",
                    "entity_type": "job",
                    "entity_id": f"slurm-job-{job.get('job_id', 'unknown')}",
                    "observed_at": datetime.utcnow().isoformat(),
                    "scheduler_domain": "slurm",
                    "job_state": self._map_slurm_state(job.get("job_state", "UNKNOWN")),
                    "owner_scope": job.get("partition", "default"),
                    "assigned_gpu_count": self._extract_gpu_count(job),
                    "labels": {"user": job.get("user_name", ""), "partition": job.get("partition", "")},
                })
            return records
        except Exception as e:
            logger.warning("squeue parse failed: %s", e)
            return []

    def _parse_sinfo(self) -> list[dict[str, Any]]:
        """Parse `sinfo --json` output."""
        try:
            result = subprocess.run(
                ["sinfo", "--json"],
                capture_output=True, text=True, timeout=10
            )
            data = json.loads(result.stdout)
            records = []
            for node in data.get("nodes", []):
                state = node.get("state", "UNKNOWN").upper()
                records.append({
                    "source_type": "slurm",
                    "entity_type": "node",
                    "entity_id": node.get("name", "unknown"),
                    "observed_at": datetime.utcnow().isoformat(),
                    "scheduler_domain": "slurm",
                    "health_state": "healthy" if "IDLE" in state or "ALLOC" in state else "degraded",
                    "cpu_utilization": node.get("cpu_load", 0) / 100.0 if node.get("cpu_load") else None,
                    "labels": {"partition": node.get("partitions", [""])[0] if node.get("partitions") else ""},
                })
            return records
        except Exception as e:
            logger.warning("sinfo parse failed: %s", e)
            return []

    # ------------------------------------------------------------------
    # REST mode (slurmrestd)
    # ------------------------------------------------------------------

    def _rest_snapshot(self) -> list[dict[str, Any]]:
        """Query slurmrestd REST API."""
        if not self._slurmrestd_url:
            logger.warning("slurmrestd URL not configured")
            return []

        import httpx

        records: list[dict[str, Any]] = []
        try:
            client = httpx.Client(base_url=self._slurmrestd_url, timeout=10.0)

            # Jobs
            resp = client.get("/slurm/v0.0.39/jobs")
            if resp.status_code == 200:
                for job in resp.json().get("jobs", []):
                    records.append({
                        "source_type": "slurm",
                        "entity_type": "job",
                        "entity_id": f"slurm-job-{job.get('job_id')}",
                        "observed_at": datetime.utcnow().isoformat(),
                        "scheduler_domain": "slurm",
                        "job_state": self._map_slurm_state(job.get("job_state", ["UNKNOWN"])[0]),
                        "owner_scope": job.get("partition", "default"),
                    })

            # Nodes
            resp = client.get("/slurm/v0.0.39/nodes")
            if resp.status_code == 200:
                for node in resp.json().get("nodes", []):
                    records.append({
                        "source_type": "slurm",
                        "entity_type": "node",
                        "entity_id": node.get("name", "unknown"),
                        "observed_at": datetime.utcnow().isoformat(),
                        "scheduler_domain": "slurm",
                        "health_state": "healthy" if "idle" in node.get("state", "").lower() else "degraded",
                    })
        except Exception as e:
            logger.warning("slurmrestd query failed: %s", e)

        return records

    # ------------------------------------------------------------------
    # Mock mode
    # ------------------------------------------------------------------

    def _mock_snapshot(self) -> list[dict[str, Any]]:
        """Load mock data from file for development."""
        if self._mock_data_path:
            path = Path(self._mock_data_path)
            if path.exists():
                import yaml
                with open(path) as f:
                    data = yaml.safe_load(f)
                return data.get("records", []) if isinstance(data, dict) else data
        return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_slurm_state(state: str) -> str:
        """Map Slurm job state to canonical JobState."""
        state_map = {
            "PENDING": "pending",
            "RUNNING": "running",
            "COMPLETING": "completing",
            "COMPLETED": "completed",
            "FAILED": "failed",
            "CANCELLED": "cancelled",
            "SUSPENDED": "suspended",
            "TIMEOUT": "failed",
            "NODE_FAIL": "failed",
            "PREEMPTED": "cancelled",
        }
        return state_map.get(state.upper(), "unknown")

    @staticmethod
    def _extract_gpu_count(job: dict) -> int | None:
        """Extract GPU count from Slurm job GRES."""
        gres = job.get("gres_detail", [])
        if gres:
            for g in gres:
                if "gpu" in str(g).lower():
                    try:
                        return int(str(g).split(":")[-1])
                    except (ValueError, IndexError):
                        pass
        return None

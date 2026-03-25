"""
Kubernetes Runtime Adapter — reads K8s Deployment, Service, Node state.

Reference: 02 (section 4), 03 (section 5)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from openaice.adapters.base import RuntimeStateAdapter

logger = logging.getLogger(__name__)


class KubernetesAdapter(RuntimeStateAdapter):
    """
    Reads Kubernetes runtime state and maps to canonical entities.

    Uses the official kubernetes Python client when available,
    falls back to mock mode for development.
    """

    name = "kubernetes"
    version = "0.1.0"

    def __init__(self) -> None:
        self._namespaces: list[str] = ["default"]
        self._k8s_client: Any = None
        self._mock_mode: bool = False

    def initialize(self, config: dict[str, Any]) -> None:
        self._namespaces = config.get("namespaces", ["default"])

        try:
            from kubernetes import client, config as k8s_config

            kubeconfig = config.get("kubeconfig_path")
            if kubeconfig:
                k8s_config.load_kube_config(config_file=kubeconfig)
            else:
                try:
                    k8s_config.load_incluster_config()
                except k8s_config.ConfigException:
                    k8s_config.load_kube_config()

            self._k8s_client = client.AppsV1Api()
            self._core_client = client.CoreV1Api()
            logger.info("Kubernetes adapter initialized with live API")
        except Exception as e:
            logger.warning("Kubernetes client unavailable, using mock mode: %s", e)
            self._mock_mode = True

    def snapshot(self) -> list[dict[str, Any]]:
        """Get current K8s state as raw records."""
        if self._mock_mode:
            return []

        records: list[dict[str, Any]] = []

        for ns in self._namespaces:
            records.extend(self._get_deployments(ns))
            records.extend(self._get_nodes())

        return records

    def _get_deployments(self, namespace: str) -> list[dict[str, Any]]:
        """Get all deployments in a namespace."""
        records = []
        try:
            deps = self._k8s_client.list_namespaced_deployment(namespace)
            for dep in deps.items:
                status = dep.status
                records.append({
                    "source_type": "kubernetes",
                    "entity_type": "deployment",
                    "entity_id": f"{namespace}/{dep.metadata.name}",
                    "observed_at": datetime.utcnow().isoformat(),
                    "scheduler_domain": "kubernetes",
                    "owner_scope": namespace,
                    "replica_count": dep.spec.replicas or 0,
                    "available_replicas": status.available_replicas or 0,
                    "desired_replicas": dep.spec.replicas or 0,
                    "health_state": (
                        "healthy" if (status.available_replicas or 0) >= (dep.spec.replicas or 0)
                        else "degraded"
                    ),
                    "labels": dep.metadata.labels or {},
                })

                # Also create a service entity for the deployment
                records.append({
                    "source_type": "kubernetes",
                    "entity_type": "service",
                    "entity_id": f"svc-{namespace}/{dep.metadata.name}",
                    "observed_at": datetime.utcnow().isoformat(),
                    "scheduler_domain": "kubernetes",
                    "owner_scope": namespace,
                    "service_state": (
                        "active" if (status.available_replicas or 0) > 0 else "degraded"
                    ),
                    "replica_count": dep.spec.replicas or 0,
                    "available_replicas": status.available_replicas or 0,
                    "labels": dep.metadata.labels or {},
                })
        except Exception as e:
            logger.warning("Failed to get deployments in %s: %s", namespace, e)

        return records

    def _get_nodes(self) -> list[dict[str, Any]]:
        """Get all nodes."""
        records = []
        try:
            nodes = self._core_client.list_node()
            for node in nodes.items:
                conditions = {c.type: c.status for c in (node.status.conditions or [])}
                is_ready = conditions.get("Ready") == "True"

                records.append({
                    "source_type": "kubernetes",
                    "entity_type": "node",
                    "entity_id": node.metadata.name,
                    "observed_at": datetime.utcnow().isoformat(),
                    "scheduler_domain": "kubernetes",
                    "health_state": "healthy" if is_ready else "degraded",
                    "labels": node.metadata.labels or {},
                })
        except Exception as e:
            logger.warning("Failed to get nodes: %s", e)

        return records

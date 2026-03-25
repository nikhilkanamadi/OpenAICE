"""
Configuration schemas for the AI Infrastructure Control Plane.

Defines the declarative YAML configuration model for telemetry sources,
runtime sources, policy mode, objectives, and guardrails.

Reference: 08 (section 10)
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from openaice.schemas.recommendations import ControlMode, PolicyMode


# ---------------------------------------------------------------------------
# Telemetry source configs
# ---------------------------------------------------------------------------


class PrometheusConfig(BaseModel):
    """Configuration for the Prometheus telemetry adapter."""

    enabled: bool = True
    url: str = "http://localhost:9090"
    scrape_interval_seconds: int = 30
    metric_mappings: dict[str, str] = Field(
        default_factory=dict,
        description="Map Prometheus metric names to canonical field names.",
    )
    label_filters: dict[str, str] = Field(
        default_factory=dict,
        description="Label filters: e.g. {namespace: 'prod'}",
    )


class OtelConfig(BaseModel):
    """Configuration for the OpenTelemetry adapter."""

    enabled: bool = False
    otlp_endpoint: str = "http://localhost:4317"
    protocol: str = "grpc"  # grpc | http


class GpuMetricsConfig(BaseModel):
    """Configuration for GPU telemetry (dcgm-exporter via Prometheus)."""

    enabled: bool = True
    prometheus_url: str = "http://localhost:9090"
    metric_prefix: str = "DCGM_FI_DEV_"


# ---------------------------------------------------------------------------
# Runtime source configs
# ---------------------------------------------------------------------------


class KubernetesConfig(BaseModel):
    """Configuration for the Kubernetes runtime adapter."""

    enabled: bool = True
    kubeconfig_path: Optional[str] = None  # None = use in-cluster or default
    namespaces: list[str] = Field(
        default_factory=lambda: ["default"],
        description="Namespaces to watch.",
    )
    resource_types: list[str] = Field(
        default_factory=lambda: ["deployments", "services", "nodes"],
    )


class SlurmConfig(BaseModel):
    """Configuration for the Slurm runtime adapter."""

    enabled: bool = False
    mode: str = "cli"  # cli | rest | mock
    slurmrestd_url: Optional[str] = None
    partitions: list[str] = Field(default_factory=list)
    mock_data_path: Optional[str] = None


class GenericServingConfig(BaseModel):
    """Configuration for the generic serving adapter."""

    enabled: bool = True
    prometheus_url: str = "http://localhost:9090"
    service_selectors: dict[str, str] = Field(
        default_factory=dict,
        description="Label selectors to discover serving endpoints.",
    )


# ---------------------------------------------------------------------------
# Policy & guardrail configs
# ---------------------------------------------------------------------------


class ObjectiveWeights(BaseModel):
    """Weights for multi-objective optimization."""

    latency: float = 0.30
    throughput: float = 0.20
    gpu_utilization: float = 0.20
    cost: float = 0.10
    reliability: float = 0.20


class GuardrailConfig(BaseModel):
    """Safety guardrail configuration."""

    min_confidence_for_action: float = 0.75
    max_staleness_seconds: float = 120.0
    cooldown_seconds: float = 300.0
    max_change_magnitude: dict[str, Any] = Field(
        default_factory=lambda: {
            "max_replica_jump": 3,
            "max_traffic_shift_pct": 20,
        },
    )
    blast_radius_limit: int = Field(
        default=5,
        description="Max entities affected by a single policy evaluation cycle.",
    )


# ---------------------------------------------------------------------------
# Replay config
# ---------------------------------------------------------------------------


class ReplayConfig(BaseModel):
    """Configuration for the telemetry replay adapter."""

    enabled: bool = False
    scenario_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Top-level config
# ---------------------------------------------------------------------------


class OpenAICEConfig(BaseModel):
    """
    Top-level configuration for OpenAICE — Auto Infrastructure Configuration Engine.

    Loaded from YAML at startup.
    """

    # Telemetry sources
    prometheus: PrometheusConfig = Field(default_factory=PrometheusConfig)
    otel: OtelConfig = Field(default_factory=OtelConfig)
    gpu_metrics: GpuMetricsConfig = Field(default_factory=GpuMetricsConfig)

    # Runtime sources
    kubernetes: KubernetesConfig = Field(default_factory=KubernetesConfig)
    slurm: SlurmConfig = Field(default_factory=SlurmConfig)
    generic_serving: GenericServingConfig = Field(default_factory=GenericServingConfig)

    # Replay
    replay: ReplayConfig = Field(default_factory=ReplayConfig)

    # Policy
    policy_mode: PolicyMode = PolicyMode.BALANCED
    control_mode: ControlMode = ControlMode.OBSERVE_ONLY
    objectives: ObjectiveWeights = Field(default_factory=ObjectiveWeights)
    guardrails: GuardrailConfig = Field(default_factory=GuardrailConfig)

    # Rules
    rules_path: str = "policies/rules.yaml"
    policy_pack_path: str = "policies/packs/balanced.yaml"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    audit_log_path: str = "audit.jsonl"

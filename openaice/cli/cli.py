"""
AICP CLI — Command-line interface for the AI Infrastructure Control Plane.

Commands:
  serve      Start the API server
  replay     Run a telemetry replay scenario
  state      Dump current canonical state
  recommend  Generate and display recommendations
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table

from openaice.schemas.config import OpenAICEConfig

console = Console()


def _load_config(config_path: str | None) -> OpenAICEConfig:
    """Load config from YAML file or use defaults."""
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        return OpenAICEConfig(**data)
    return OpenAICEConfig()


def _run_pipeline(config: OpenAICEConfig) -> tuple:
    """Run the full control-plane pipeline and return (entities, recommendations)."""
    from openaice.adapters.telemetry.replay import ReplayAdapter
    from openaice.core.normalizer import Normalizer
    from openaice.core.policy_engine import PolicyEngine
    from openaice.core.recommender import Recommender
    from openaice.core.state_bus import StateBus
    from openaice.core.workload_classifier import WorkloadClassifier

    # Initialize components
    state_bus = StateBus()
    normalizer = Normalizer()
    classifier = WorkloadClassifier()
    policy_engine = PolicyEngine(
        policy_mode=config.policy_mode,
        control_mode=config.control_mode,
    )
    recommender = Recommender(control_mode=config.control_mode)

    # Load rules
    policy_engine.load_rules(config.rules_path)
    policy_engine.load_policy_pack(config.policy_pack_path)

    # Collect telemetry
    raw_records = []

    if config.replay.enabled and config.replay.scenario_path:
        adapter = ReplayAdapter()
        adapter.initialize({"scenario_path": config.replay.scenario_path})
        raw_records.extend(adapter.collect())

    # Normalize and ingest
    fragments = normalizer.normalize(raw_records)
    state_bus.put_fragments(fragments)

    # Classify
    entities = state_bus.get_all_entities()
    classifier.classify_all(entities)

    # Evaluate policies
    recommendations = policy_engine.evaluate(entities)

    # Process through recommender
    results = recommender.process(recommendations)

    return entities, results


@click.group()
def main():
    """OpenAICE — Auto Infrastructure Configuration Engine CLI."""
    pass


@main.command()
@click.option("--config", "-c", "config_path", default=None, help="Path to config YAML")
@click.option("--host", default="0.0.0.0", help="API server host")
@click.option("--port", default=8000, type=int, help="API server port")
def serve(config_path: str | None, host: str, port: int):
    """Start the AICP API server."""
    import uvicorn

    from openaice.api.server import create_app

    config = _load_config(config_path)
    config.api_host = host
    config.api_port = port

    app = create_app(config)

    console.print(f"[bold green]OpenAICE Control Plane[/] starting on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


@main.command()
@click.option("--scenario", "-s", required=True, help="Path to replay scenario directory")
@click.option("--config", "-c", "config_path", default=None, help="Path to config YAML")
@click.option("--format", "-f", "output_format", default="table", type=click.Choice(["table", "json", "yaml"]))
def replay(scenario: str, config_path: str | None, output_format: str):
    """Run a telemetry replay scenario and display recommendations."""
    config = _load_config(config_path)
    config.replay.enabled = True
    config.replay.scenario_path = scenario

    entities, results = _run_pipeline(config)

    console.print(f"\n[bold cyan]═══ OpenAICE Replay Results ═══[/]")
    console.print(f"[dim]Scenario: {scenario}[/]")
    console.print(f"[dim]Entities loaded: {len(entities)}[/]")
    console.print(f"[dim]Recommendations: {len(results)}[/]\n")

    if output_format == "json":
        output = [
            {
                "recommendation": rec.model_dump(mode="json"),
                "explanation": exp.model_dump(mode="json"),
            }
            for rec, exp in results
        ]
        console.print_json(json.dumps(output, indent=2, default=str))
        return

    if not results:
        console.print("[yellow]No recommendations generated.[/]")
        return

    # Table output
    table = Table(title="Recommendations", show_lines=True)
    table.add_column("ID", style="cyan", max_width=14)
    table.add_column("Entity", style="white")
    table.add_column("Action", style="green")
    table.add_column("Risk", style="yellow")
    table.add_column("Confidence", justify="right")
    table.add_column("Reason", style="dim", max_width=50)

    for rec, exp in results:
        risk_color = {"low": "green", "medium": "yellow", "high": "red", "critical": "bold red"}
        table.add_row(
            rec.recommendation_id,
            rec.entity_id,
            rec.recommended_action.action_type.value,
            f"[{risk_color.get(rec.risk_level.value, 'white')}]{rec.risk_level.value}[/]",
            f"{rec.confidence_score:.2f}",
            rec.reason,
        )

    console.print(table)

    # Explanations
    console.print(f"\n[bold]Explanations:[/]")
    for rec, exp in results:
        console.print(f"  [cyan]{rec.recommendation_id}[/]: {exp.reason}")
        console.print(f"    Signals: {', '.join(exp.signals_used)}")
        console.print(f"    Objectives: {', '.join(exp.objectives_impacted)}")
        console.print()


@main.command()
@click.option("--scenario", "-s", required=True, help="Path to replay scenario directory")
@click.option("--format", "-f", "output_format", default="yaml", type=click.Choice(["json", "yaml"]))
def state(scenario: str, output_format: str):
    """Dump current canonical state from a replay scenario."""
    config = OpenAICEConfig()
    config.replay.enabled = True
    config.replay.scenario_path = scenario

    entities, _ = _run_pipeline(config)

    data = [e.model_dump(mode="json") for e in entities]

    if output_format == "json":
        console.print_json(json.dumps(data, indent=2, default=str))
    else:
        console.print(yaml.dump(data, default_flow_style=False))


if __name__ == "__main__":
    main()

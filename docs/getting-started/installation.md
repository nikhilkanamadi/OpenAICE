# Installation

## Requirements

- Python 3.11+
- pip or Poetry

## Install from Source

=== "Poetry (recommended)"

    ```bash
    git clone https://github.com/your-username/openaice.git
    cd openaice
    pip install poetry
    poetry install
    ```

=== "pip"

    ```bash
    git clone https://github.com/your-username/openaice.git
    cd openaice
    pip install -e .
    ```

=== "Docker"

    ```bash
    docker build -t openaice .
    docker run -p 8000:8000 openaice
    ```

## Verify Installation

```bash
python -m openaice.cli.cli --help
```

You should see:

```
Usage: cli [OPTIONS] COMMAND [ARGS]...

  OpenAICE — Auto Infrastructure Configuration Engine CLI.

Options:
  --help  Show this message and exit.

Commands:
  replay  Run a telemetry replay scenario and display recommendations.
  serve   Start the OpenAICE API server.
  state   Dump current canonical state from a replay scenario.
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pydantic` | ^2.5 | Schema validation for canonical entities |
| `pyyaml` | ^6.0 | YAML config and policy rule parsing |
| `fastapi` | ^0.110 | REST API server |
| `uvicorn` | ^0.27 | ASGI server |
| `click` | ^8.1 | CLI framework |
| `httpx` | ^0.27 | HTTP client for adapters |
| `rich` | ^13.7 | Rich terminal output |

### Optional Dependencies

| Package | Purpose |
|---------|---------|
| `kubernetes` | Live Kubernetes API access |
| `prometheus-api-client` | Live Prometheus queries |

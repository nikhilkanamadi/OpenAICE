# CLI Reference

OpenAICE provides a rich CLI powered by Click and Rich for terminal output.

## Commands

### `openaice serve`

Start the FastAPI API server.

```bash
python -m openaice.cli.cli serve [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--config`, `-c` | None | Path to config YAML file |
| `--host` | `0.0.0.0` | API server host |
| `--port` | `8000` | API server port |

**Example:**

```bash
python -m openaice.cli.cli serve --config configs/sample-k8s.yaml --port 9000
```

---

### `openaice replay`

Run a telemetry replay scenario and display recommendations.

```bash
python -m openaice.cli.cli replay [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--scenario`, `-s` | *(required)* | Path to replay scenario directory |
| `--config`, `-c` | None | Path to config YAML file |
| `--format`, `-f` | `table` | Output format: `table`, `json`, `yaml` |

**Examples:**

```bash
# Rich table output (default)
python -m openaice.cli.cli replay \
  --scenario examples/telemetry-replay/k8s-inference-queue-pressure

# JSON output for piping
python -m openaice.cli.cli replay \
  --scenario examples/telemetry-replay/slurm-node-health-warning \
  --format json

# With custom config
python -m openaice.cli.cli replay \
  --scenario examples/telemetry-replay/k8s-inference-queue-pressure \
  --config configs/sample-k8s.yaml
```

---

### `openaice state`

Dump the canonical state from a replay scenario.

```bash
python -m openaice.cli.cli state [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--scenario`, `-s` | *(required)* | Path to replay scenario directory |
| `--format`, `-f` | `yaml` | Output format: `json`, `yaml` |

**Example:**

```bash
python -m openaice.cli.cli state \
  --scenario examples/telemetry-replay/k8s-inference-queue-pressure \
  --format json
```

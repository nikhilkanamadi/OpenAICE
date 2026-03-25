# OpenAICE — VS Code Extension

**AI Infrastructure Control Plane, right inside VS Code.**

View canonical infrastructure state, browse explainable recommendations, and run replay scenarios — all without leaving your editor.

## Features

| Feature | Description |
|---------|-------------|
| **Infrastructure State Sidebar** | View entities (services, deployments, GPUs, nodes, jobs, queues) grouped by type with health indicators |
| **Recommendations Panel** | Browse active recommendations with risk levels, confidence scores, and click-to-detail |
| **Recommendation Detail** | Rich webview showing reason, signals, objectives, action parameters |
| **Replay Scenarios** | Run telemetry replay from the command palette — test without live infrastructure |
| **Status Bar** | Live connection state, entity count, and recommendation count |
| **Auto-Refresh** | Configurable polling interval (default: 30s) |

## Quick Start

1. Install the extension from the VS Code Marketplace
2. Start the OpenAICE backend:
   ```bash
   pip install openaice
   python -m openaice.cli.cli serve --config configs/sample-k8s.yaml
   ```
3. The extension auto-connects to `http://localhost:8000`

Or use **Cmd+Shift+P → "OpenAICE: Run Replay"** to test without a live server.

## Commands

| Command | Description |
|---------|-------------|
| `OpenAICE: Set API URL` | Configure the backend server URL |
| `OpenAICE: Refresh` | Manually refresh state and recommendations |
| `OpenAICE: Run Replay Scenario` | Run a telemetry replay scenario |
| `OpenAICE: Start Backend Server` | Launch the backend in an integrated terminal |

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `openaice.apiUrl` | `http://localhost:8000` | Backend server URL |
| `openaice.refreshInterval` | `30` | Auto-refresh interval in seconds (0 to disable) |
| `openaice.autoConnect` | `true` | Auto-connect on extension activation |

## Requirements

- [OpenAICE](https://github.com/nikhilkanamadi/OpenAICE) backend (Python 3.11+)
- VS Code 1.85+

## License

Apache 2.0 — [OpenAICE](https://github.com/nikhilkanamadi/OpenAICE)

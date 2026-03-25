import * as vscode from 'vscode';
import { OpenAICEClient } from '../api/client';

export async function runReplay(client: OpenAICEClient): Promise<void> {
  const scenarios = [
    {
      label: '$(beaker) K8s Inference Queue Pressure',
      description: 'Service with p95=320ms, queue=42 → scale_replicas',
      path: 'examples/telemetry-replay/k8s-inference-queue-pressure',
    },
    {
      label: '$(alert) Slurm Node Health Warning',
      description: 'Node with degraded health, ECC errors → quarantine_node',
      path: 'examples/telemetry-replay/slurm-node-health-warning',
    },
    {
      label: '$(file) Custom Scenario Path...',
      description: 'Enter a custom scenario directory path',
      path: '__custom__',
    },
  ];

  const picked = await vscode.window.showQuickPick(scenarios, {
    placeHolder: 'Select a replay scenario',
    title: 'OpenAICE: Run Replay Scenario',
  });

  if (!picked) {
    return;
  }

  let scenarioPath = picked.path;

  if (scenarioPath === '__custom__') {
    const input = await vscode.window.showInputBox({
      prompt: 'Enter the path to the replay scenario directory',
      placeHolder: 'examples/telemetry-replay/my-scenario',
    });
    if (!input) {
      return;
    }
    scenarioPath = input;
  }

  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'OpenAICE: Running replay...',
        cancellable: false,
      },
      async () => {
        const result = await client.runReplay(scenarioPath);

        const recCount = result.recommendations_generated;
        const entityCount = result.entities_loaded;

        if (recCount === 0) {
          vscode.window.showInformationMessage(
            `OpenAICE Replay: ${entityCount} entities loaded, no recommendations generated.`
          );
        } else {
          const detail = result.recommendations
            .map((r) => {
              const rec = r.recommendation;
              return `• ${rec.recommended_action.action_type} → ${rec.entity_id} (${rec.risk_level}, ${(rec.confidence_score * 100).toFixed(0)}%)`;
            })
            .join('\n');

          vscode.window.showInformationMessage(
            `OpenAICE Replay: ${entityCount} entities, ${recCount} recommendation(s):\n${detail}`,
            { modal: false }
          );
        }
      }
    );
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    vscode.window.showErrorMessage(`OpenAICE Replay failed: ${msg}`);
  }
}

export async function setApiUrl(client: OpenAICEClient): Promise<void> {
  const config = vscode.workspace.getConfiguration('openaice');
  const current = config.get<string>('apiUrl', 'http://localhost:8000');

  const input = await vscode.window.showInputBox({
    prompt: 'Enter the OpenAICE API server URL',
    value: current,
    placeHolder: 'http://localhost:8000',
  });

  if (input) {
    await config.update('apiUrl', input, vscode.ConfigurationTarget.Global);
    client.setUrl(input);
    try {
      const health = await client.health();
      vscode.window.showInformationMessage(
        `Connected to OpenAICE ${health.version} (${health.policy_mode} / ${health.control_mode})`
      );
    } catch {
      vscode.window.showWarningMessage(`Cannot connect to ${input}. Is the server running?`);
    }
  }
}

import * as vscode from 'vscode';
import { OpenAICEClient } from './api/client';
import { StateTreeProvider } from './providers/stateTree';
import { RecsTreeProvider } from './providers/recsTree';
import { showRecommendationDetail } from './panels/recDetail';
import { runReplay, setApiUrl } from './commands/replay';
import { StatusBarManager } from './statusBar';
import { RecommendationWithExplanation } from './api/client';

let refreshTimer: NodeJS.Timeout | undefined;

export function activate(context: vscode.ExtensionContext): void {
  const config = vscode.workspace.getConfiguration('openaice');
  const apiUrl = config.get<string>('apiUrl', 'http://localhost:8000');

  // Initialize API client
  const client = new OpenAICEClient(apiUrl);

  // Initialize tree providers
  const stateProvider = new StateTreeProvider(client);
  const recsProvider = new RecsTreeProvider(client);

  // Register tree views
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('openaice.state', stateProvider),
    vscode.window.registerTreeDataProvider('openaice.recommendations', recsProvider)
  );

  // Initialize status bar
  const statusBar = new StatusBarManager(client);
  context.subscriptions.push({ dispose: () => statusBar.dispose() });

  // Refresh function
  const refreshAll = async () => {
    await stateProvider.loadData();
    await recsProvider.loadData();
    await statusBar.update();
  };

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('openaice.refresh', refreshAll),

    vscode.commands.registerCommand('openaice.connect', async () => {
      await setApiUrl(client);
      await refreshAll();
    }),

    vscode.commands.registerCommand('openaice.replay', async () => {
      await runReplay(client);
      await refreshAll();
    }),

    vscode.commands.registerCommand('openaice.viewRecommendation', (rec: RecommendationWithExplanation) => {
      showRecommendationDetail(context, rec);
    }),

    vscode.commands.registerCommand('openaice.startServer', () => {
      const terminal = vscode.window.createTerminal('OpenAICE Server');
      terminal.sendText('source .venv/bin/activate && python -m openaice.cli.cli serve --config configs/sample-k8s.yaml');
      terminal.show();
    })
  );

  // Auto-connect on startup
  if (config.get<boolean>('autoConnect', true)) {
    refreshAll().catch(() => {
      // Silently fail on startup — server might not be running
    });
  }

  // Set up auto-refresh timer
  const intervalSec = config.get<number>('refreshInterval', 30);
  if (intervalSec > 0) {
    refreshTimer = setInterval(refreshAll, intervalSec * 1000);
  }

  // Watch for config changes
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration('openaice.apiUrl')) {
        const newUrl = vscode.workspace.getConfiguration('openaice').get<string>('apiUrl', 'http://localhost:8000');
        client.setUrl(newUrl);
        refreshAll();
      }
      if (e.affectsConfiguration('openaice.refreshInterval')) {
        if (refreshTimer) {
          clearInterval(refreshTimer);
        }
        const newInterval = vscode.workspace.getConfiguration('openaice').get<number>('refreshInterval', 30);
        if (newInterval > 0) {
          refreshTimer = setInterval(refreshAll, newInterval * 1000);
        }
      }
    })
  );

  // Show welcome message
  vscode.window.showInformationMessage(
    'OpenAICE extension activated. Click the sidebar icon to view infrastructure state.',
    'Connect', 'Run Replay'
  ).then((selection) => {
    if (selection === 'Connect') {
      vscode.commands.executeCommand('openaice.connect');
    } else if (selection === 'Run Replay') {
      vscode.commands.executeCommand('openaice.replay');
    }
  });
}

export function deactivate(): void {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
}

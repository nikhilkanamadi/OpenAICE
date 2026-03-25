import * as vscode from 'vscode';
import { OpenAICEClient } from './api/client';

export class StatusBarManager {
  private item: vscode.StatusBarItem;
  private client: OpenAICEClient;

  constructor(client: OpenAICEClient) {
    this.client = client;
    this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 50);
    this.item.command = 'openaice.connect';
    this.item.show();
    this.setDisconnected();
  }

  setConnected(entityCount: number, recCount: number, policyMode: string): void {
    this.item.text = `$(pass-filled) OpenAICE: ${entityCount} entities, ${recCount} recs`;
    this.item.tooltip = `Connected · ${policyMode} mode\nClick to change server URL`;
    this.item.backgroundColor = undefined;
  }

  setDisconnected(): void {
    this.item.text = '$(debug-disconnect) OpenAICE: Disconnected';
    this.item.tooltip = 'Click to connect to OpenAICE server';
    this.item.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
  }

  setError(msg: string): void {
    this.item.text = '$(error) OpenAICE: Error';
    this.item.tooltip = msg;
    this.item.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
  }

  async update(): Promise<void> {
    try {
      const health = await this.client.health();
      const state = await this.client.getState();
      const recs = await this.client.getRecommendations();
      this.setConnected(state.entity_count, recs.count, health.policy_mode);
    } catch {
      this.setDisconnected();
    }
  }

  dispose(): void {
    this.item.dispose();
  }
}

import * as vscode from 'vscode';
import { OpenAICEClient, Entity } from '../api/client';

const HEALTH_ICONS: Record<string, string> = {
  healthy: '$(pass-filled)',
  warning: '$(warning)',
  degraded: '$(error)',
  critical: '$(flame)',
  unknown: '$(question)',
};

const TYPE_ICONS: Record<string, string> = {
  service: '$(globe)',
  deployment: '$(layers)',
  gpu: '$(circuit-board)',
  node: '$(server)',
  job: '$(tasklist)',
  queue: '$(list-ordered)',
  model_revision: '$(tag)',
  scheduler_domain: '$(layout)',
  tenant_scope: '$(organization)',
};

export class StateTreeProvider implements vscode.TreeDataProvider<StateTreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<StateTreeItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
  private entities: Entity[] = [];

  constructor(private client: OpenAICEClient) {}

  refresh(): void {
    this._onDidChangeTreeData.fire(undefined);
  }

  async loadData(): Promise<void> {
    try {
      const state = await this.client.getState();
      this.entities = state.entities;
    } catch {
      this.entities = [];
    }
    this.refresh();
  }

  getTreeItem(element: StateTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: StateTreeItem): StateTreeItem[] {
    if (!element) {
      // Root level: group by entity_type
      const types = new Map<string, Entity[]>();
      for (const e of this.entities) {
        const list = types.get(e.entity_type) || [];
        list.push(e);
        types.set(e.entity_type, list);
      }
      return Array.from(types.entries()).map(([type, entities]) => {
        const icon = TYPE_ICONS[type] || '$(symbol-misc)';
        return new StateTreeItem(
          `${icon} ${type} (${entities.length})`,
          vscode.TreeItemCollapsibleState.Expanded,
          { type: 'group', entityType: type, entities }
        );
      });
    }

    if (element.data?.type === 'group') {
      return (element.data.entities as Entity[]).map((entity) => {
        const healthIcon = HEALTH_ICONS[entity.health_state] || '$(question)';
        const conf = entity.confidence_score ? ` · ${(entity.confidence_score * 100).toFixed(0)}%` : '';
        const desc = `${entity.scheduler_domain} · ${entity.health_state}${conf}`;

        const item = new StateTreeItem(
          `${healthIcon} ${entity.entity_id}`,
          vscode.TreeItemCollapsibleState.None,
          { type: 'entity', entity }
        );
        item.description = desc;
        item.tooltip = makeEntityTooltip(entity);
        return item;
      });
    }

    return [];
  }
}

function makeEntityTooltip(e: Entity): vscode.MarkdownString {
  const md = new vscode.MarkdownString();
  md.appendMarkdown(`### ${e.entity_id}\n\n`);
  md.appendMarkdown(`| Field | Value |\n|---|---|\n`);
  md.appendMarkdown(`| **Type** | ${e.entity_type} |\n`);
  md.appendMarkdown(`| **Health** | ${e.health_state} |\n`);
  md.appendMarkdown(`| **Domain** | ${e.scheduler_domain} |\n`);
  md.appendMarkdown(`| **Workload** | ${e.workload_type} |\n`);
  md.appendMarkdown(`| **Confidence** | ${(e.confidence_score * 100).toFixed(0)}% |\n`);

  // Add dynamic fields
  const skip = new Set(['entity_id', 'entity_type', 'source_type', 'scheduler_domain', 'workload_type', 'health_state', 'confidence_score', 'observed_at']);
  for (const [k, v] of Object.entries(e)) {
    if (!skip.has(k) && v !== null && v !== undefined) {
      md.appendMarkdown(`| ${k} | ${v} |\n`);
    }
  }
  return md;
}

export class StateTreeItem extends vscode.TreeItem {
  constructor(
    label: string,
    collapsibleState: vscode.TreeItemCollapsibleState,
    public data?: Record<string, unknown>
  ) {
    super(label, collapsibleState);
  }
}

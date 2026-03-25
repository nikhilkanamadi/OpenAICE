import * as vscode from 'vscode';
import { OpenAICEClient, RecommendationWithExplanation } from '../api/client';

const RISK_ICONS: Record<string, string> = {
  low: '$(info)',
  medium: '$(warning)',
  high: '$(error)',
  critical: '$(flame)',
};

export class RecsTreeProvider implements vscode.TreeDataProvider<RecTreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<RecTreeItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
  private recs: RecommendationWithExplanation[] = [];

  constructor(private client: OpenAICEClient) {}

  refresh(): void {
    this._onDidChangeTreeData.fire(undefined);
  }

  async loadData(): Promise<void> {
    try {
      const resp = await this.client.getRecommendations();
      this.recs = resp.recommendations;
    } catch {
      this.recs = [];
    }
    this.refresh();
  }

  getTreeItem(element: RecTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: RecTreeItem): RecTreeItem[] {
    if (element) {
      return [];
    }

    if (this.recs.length === 0) {
      const empty = new RecTreeItem(
        '$(check) No active recommendations',
        vscode.TreeItemCollapsibleState.None
      );
      empty.description = 'All systems nominal';
      return [empty];
    }

    return this.recs.map((r) => {
      const rec = r.recommendation;
      const icon = RISK_ICONS[rec.risk_level] || '$(zap)';
      const conf = (rec.confidence_score * 100).toFixed(0);

      const item = new RecTreeItem(
        `${icon} ${rec.recommended_action.action_type}`,
        vscode.TreeItemCollapsibleState.None,
        r
      );
      item.description = `${rec.entity_id} · ${rec.risk_level} · ${conf}%`;
      item.tooltip = makeRecTooltip(r);
      item.command = {
        command: 'openaice.viewRecommendation',
        title: 'View Recommendation',
        arguments: [r],
      };
      return item;
    });
  }
}

function makeRecTooltip(r: RecommendationWithExplanation): vscode.MarkdownString {
  const rec = r.recommendation;
  const exp = r.explanation;
  const md = new vscode.MarkdownString();
  md.appendMarkdown(`### ${rec.recommended_action.action_type}\n\n`);
  md.appendMarkdown(`**Entity:** ${rec.entity_id}\n\n`);
  md.appendMarkdown(`**Reason:** ${rec.reason}\n\n`);
  md.appendMarkdown(`**Risk:** ${rec.risk_level} · **Confidence:** ${(rec.confidence_score * 100).toFixed(0)}%\n\n`);
  md.appendMarkdown(`**Signals:** ${exp.signals_used.join(', ')}\n\n`);
  md.appendMarkdown(`**Objectives:** ${exp.objectives_impacted.join(', ')}\n\n`);
  return md;
}

export class RecTreeItem extends vscode.TreeItem {
  constructor(
    label: string,
    collapsibleState: vscode.TreeItemCollapsibleState,
    public recData?: RecommendationWithExplanation
  ) {
    super(label, collapsibleState);
  }
}

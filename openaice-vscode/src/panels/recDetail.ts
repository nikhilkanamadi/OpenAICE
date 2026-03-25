import * as vscode from 'vscode';
import { RecommendationWithExplanation } from '../api/client';

export function showRecommendationDetail(
  context: vscode.ExtensionContext,
  rec: RecommendationWithExplanation
): void {
  const r = rec.recommendation;
  const e = rec.explanation;

  const panel = vscode.window.createWebviewPanel(
    'openaice.recDetail',
    `${r.recommended_action.action_type} — ${r.entity_id}`,
    vscode.ViewColumn.One,
    { enableScripts: false }
  );

  const riskColors: Record<string, string> = {
    low: '#22c55e',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#dc2626',
  };

  const riskColor = riskColors[r.risk_level] || '#888';
  const confPct = (r.confidence_score * 100).toFixed(0);
  const params = Object.entries(r.recommended_action.parameters || {})
    .map(([k, v]) => `<tr><td>${k}</td><td><code>${v}</code></td></tr>`)
    .join('');

  panel.webview.html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Recommendation Detail</title>
  <style>
    body {
      font-family: var(--vscode-font-family, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif);
      color: var(--vscode-foreground, #ccc);
      background: var(--vscode-editor-background, #1e1e1e);
      padding: 24px;
      line-height: 1.6;
    }
    h1 { font-size: 1.5rem; font-weight: 700; margin-bottom: 4px; }
    .subtitle { color: var(--vscode-descriptionForeground, #888); margin-bottom: 24px; font-size: 0.95rem; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
    .card {
      background: var(--vscode-editorWidget-background, #252526);
      border: 1px solid var(--vscode-editorWidget-border, #333);
      border-radius: 6px;
      padding: 16px;
    }
    .card-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--vscode-descriptionForeground, #888); margin-bottom: 4px; }
    .card-value { font-size: 1.2rem; font-weight: 600; }
    .risk-badge {
      display: inline-block;
      padding: 2px 10px;
      border-radius: 12px;
      font-weight: 600;
      font-size: 0.85rem;
      color: #fff;
      background: ${riskColor};
    }
    .section { margin-bottom: 20px; }
    .section h2 { font-size: 1rem; font-weight: 600; border-bottom: 1px solid var(--vscode-editorWidget-border, #333); padding-bottom: 6px; margin-bottom: 10px; }
    .reason-box {
      background: var(--vscode-textBlockQuote-background, #2a2d2e);
      border-left: 3px solid var(--vscode-textLink-foreground, #3794ff);
      padding: 12px 16px;
      border-radius: 4px;
      font-size: 0.95rem;
    }
    .tag {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.8rem;
      margin-right: 6px;
      margin-bottom: 4px;
      background: var(--vscode-badge-background, #333);
      color: var(--vscode-badge-foreground, #ccc);
    }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--vscode-editorWidget-border, #333); }
    th { font-size: 0.75rem; text-transform: uppercase; color: var(--vscode-descriptionForeground, #888); }
    code { background: var(--vscode-textCodeBlock-background, #2a2d2e); padding: 1px 4px; border-radius: 3px; font-size: 0.9em; }
    .id-text { font-family: var(--vscode-editor-font-family, monospace); font-size: 0.85rem; color: var(--vscode-descriptionForeground, #888); }
  </style>
</head>
<body>
  <h1>${r.recommended_action.action_type}</h1>
  <div class="subtitle">
    Entity: <strong>${r.entity_id}</strong> · <span class="id-text">${r.recommendation_id}</span>
  </div>

  <div class="grid">
    <div class="card">
      <div class="card-label">Risk Level</div>
      <div class="card-value"><span class="risk-badge">${r.risk_level.toUpperCase()}</span></div>
    </div>
    <div class="card">
      <div class="card-label">Confidence Score</div>
      <div class="card-value">${confPct}%</div>
    </div>
    <div class="card">
      <div class="card-label">Approval Required</div>
      <div class="card-value">${r.requires_approval ? 'Yes' : 'No'}</div>
    </div>
    <div class="card">
      <div class="card-label">Rule ID</div>
      <div class="card-value id-text">${e.rule_id}</div>
    </div>
  </div>

  <div class="section">
    <h2>Reason</h2>
    <div class="reason-box">${r.reason}</div>
  </div>

  <div class="section">
    <h2>Signals Used</h2>
    <div>${e.signals_used.map((s: string) => `<span class="tag">${s}</span>`).join('')}</div>
  </div>

  <div class="section">
    <h2>Objectives Impacted</h2>
    <div>${e.objectives_impacted.map((o: string) => `<span class="tag">${o}</span>`).join('')}</div>
  </div>

  ${params ? `
  <div class="section">
    <h2>Action Parameters</h2>
    <table>
      <thead><tr><th>Parameter</th><th>Value</th></tr></thead>
      <tbody>${params}</tbody>
    </table>
  </div>` : ''}
</body>
</html>`;
}

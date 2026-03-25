import * as http from 'http';
import * as https from 'https';
import * as url from 'url';

export interface Entity {
  entity_id: string;
  entity_type: string;
  source_type: string;
  scheduler_domain: string;
  workload_type: string;
  health_state: string;
  confidence_score: number;
  observed_at: string;
  [key: string]: unknown;
}

export interface RecommendedAction {
  action_type: string;
  parameters: Record<string, unknown>;
}

export interface Recommendation {
  recommendation_id: string;
  entity_id: string;
  recommended_action: RecommendedAction;
  reason: string;
  confidence_score: number;
  risk_level: string;
  requires_approval: boolean;
}

export interface Explanation {
  rule_id: string;
  signals_used: string[];
  objectives_impacted: string[];
}

export interface RecommendationWithExplanation {
  recommendation: Recommendation;
  explanation: Explanation;
}

export interface HealthResponse {
  status: string;
  version: string;
  control_mode: string;
  policy_mode: string;
}

export interface StateResponse {
  entity_count: number;
  entities: Entity[];
}

export interface RecommendationsResponse {
  count: number;
  recommendations: RecommendationWithExplanation[];
}

export interface ReplayResponse {
  entities_loaded: number;
  recommendations_generated: number;
  recommendations: RecommendationWithExplanation[];
}

function httpGet(requestUrl: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const parsed = url.parse(requestUrl);
    const client = parsed.protocol === 'https:' ? https : http;
    const req = client.get(requestUrl, { timeout: 5000 }, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
          resolve(data);
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Request timeout')); });
  });
}

function httpPost(requestUrl: string, body: object): Promise<string> {
  return new Promise((resolve, reject) => {
    const parsed = url.parse(requestUrl);
    const client = parsed.protocol === 'https:' ? https : http;
    const postData = JSON.stringify(body);
    const options = {
      method: 'POST',
      hostname: parsed.hostname,
      port: parsed.port,
      path: parsed.path,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
      },
      timeout: 10000,
    };
    const req = client.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
          resolve(data);
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Request timeout')); });
    req.write(postData);
    req.end();
  });
}

export class OpenAICEClient {
  private baseUrl: string;
  private _connected: boolean = false;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  get connected(): boolean {
    return this._connected;
  }

  setUrl(newUrl: string): void {
    this.baseUrl = newUrl.replace(/\/$/, '');
    this._connected = false;
  }

  async health(): Promise<HealthResponse> {
    try {
      const data = await httpGet(`${this.baseUrl}/health`);
      this._connected = true;
      return JSON.parse(data);
    } catch {
      this._connected = false;
      throw new Error('Cannot connect to OpenAICE server');
    }
  }

  async getState(): Promise<StateResponse> {
    const data = await httpGet(`${this.baseUrl}/state`);
    return JSON.parse(data);
  }

  async getRecommendations(): Promise<RecommendationsResponse> {
    const data = await httpGet(`${this.baseUrl}/recommendations`);
    return JSON.parse(data);
  }

  async runReplay(scenarioPath: string): Promise<ReplayResponse> {
    const data = await httpPost(`${this.baseUrl}/replay`, { scenario_path: scenarioPath });
    return JSON.parse(data);
  }

  async getAudit(): Promise<{ count: number; records: unknown[] }> {
    const data = await httpGet(`${this.baseUrl}/audit`);
    return JSON.parse(data);
  }
}

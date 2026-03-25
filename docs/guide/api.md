# API Reference

OpenAICE exposes a REST API via FastAPI with automatic OpenAPI documentation.

## Base URL

```
http://localhost:8000
```

Interactive API docs at [`/docs`](http://localhost:8000/docs) (Swagger UI) or [`/redoc`](http://localhost:8000/redoc).

## Endpoints

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "control_mode": "recommend_with_approval",
  "policy_mode": "balanced"
}
```

---

### `GET /state`

Returns the current canonical entity state snapshot.

**Response:**
```json
{
  "entity_count": 3,
  "entities": [
    {
      "entity_id": "inference-api",
      "entity_type": "service",
      "source_type": "replay",
      "scheduler_domain": "kubernetes",
      "workload_type": "online_inference",
      "health_state": "healthy",
      "confidence_score": 0.91,
      "latency_p95_ms": 320.0,
      "queue_depth": 42
    }
  ]
}
```

---

### `GET /recommendations`

Returns currently active recommendations.

**Response:**
```json
{
  "count": 1,
  "recommendations": [
    {
      "recommendation": {
        "recommendation_id": "rec-f4c1be0f",
        "entity_id": "inference-api",
        "recommended_action": {
          "action_type": "scale_replicas",
          "parameters": {"direction": "up", "max_increment": 3}
        },
        "reason": "p95 latency exceeded target",
        "confidence_score": 0.91,
        "risk_level": "medium",
        "requires_approval": true
      },
      "explanation": {
        "rule_id": "rec-f4c1be0f",
        "signals_used": ["latency_p95_ms", "queue_depth"],
        "objectives_impacted": ["latency", "reliability"]
      }
    }
  ]
}
```

---

### `GET /audit`

Returns audit event history.

**Response:**
```json
{
  "count": 0,
  "records": []
}
```

---

### `POST /replay`

Run a telemetry replay scenario and return recommendations.

**Request body:**
```json
{
  "scenario_path": "examples/telemetry-replay/k8s-inference-queue-pressure"
}
```

**Response:**
```json
{
  "entities_loaded": 3,
  "recommendations_generated": 1,
  "recommendations": [...]
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8000/replay \
  -H "Content-Type: application/json" \
  -d '{"scenario_path": "examples/telemetry-replay/k8s-inference-queue-pressure"}'
```

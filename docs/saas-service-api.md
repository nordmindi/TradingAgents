# TradingAgents SaaS Service API

This service wrapper lets a SaaS backend submit TradingAgents analysis jobs and fetch generated PDF reports. The dashboard should authenticate users in the SaaS app; this service should be kept private and protected with a service-to-service API key.

## Run

```bash
pip install -e .
uvicorn tradingagents.service.api:app --host 0.0.0.0 --port 8000
```

Optional environment variables:

```bash
TRADINGAGENTS_SERVICE_API_KEY=change-me
TRADINGAGENTS_SERVICE_REPORTS_DIR=reports/api
TRADINGAGENTS_SERVICE_CACHE_DIR=.tradingagents_service/cache
TRADINGAGENTS_SERVICE_MEMORY_DIR=.tradingagents_service/memory
TRADINGAGENTS_SERVICE_WORKERS=1
```

## Submit Report Job

```http
POST /v1/reports
X-API-Key: change-me
Content-Type: application/json
```

```json
{
  "ticker": "NVDA",
  "analysis_date": "2026-05-07",
  "selected_analysts": ["market", "news", "fundamentals"],
  "llm_provider": "openai",
  "deep_think_llm": "gpt-5.4",
  "quick_think_llm": "gpt-5.4-mini",
  "max_debate_rounds": 1,
  "max_risk_discuss_rounds": 1,
  "output_language": "English",
  "user_id": "saas-user-id"
}
```

Response:

```json
{
  "job_id": "abc123",
  "status": "queued",
  "status_url": "/v1/reports/abc123",
  "pdf_url": "/v1/reports/abc123/pdf"
}
```

## Poll Status

```http
GET /v1/reports/{job_id}
X-API-Key: change-me
```

Statuses are `queued`, `running`, `completed`, and `failed`.

## Download PDF

```http
GET /v1/reports/{job_id}/pdf
X-API-Key: change-me
```

The endpoint returns `409` until the job is complete.

## SaaS Integration Notes

- Keep end-user auth, subscriptions, billing, quotas, and report ownership in the SaaS backend.
- Treat this service as a private worker API. Do not expose it directly to browsers.
- The current job store is in-memory and intended for a first service boundary. For production, replace it with a database table plus a queue worker such as Redis/RQ, Celery, Dramatiq, or a managed queue.
- Store generated PDFs in object storage for production downloads. The current implementation writes to local disk under `TRADINGAGENTS_SERVICE_REPORTS_DIR`.
- Start with `TRADINGAGENTS_SERVICE_WORKERS=1` unless your LLM/data-provider rate limits and machine resources support parallel agent runs.

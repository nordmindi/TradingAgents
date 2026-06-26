# TradingAgents Service Deployment Guide

This guide explains how to deploy the TradingAgents service as a cloud-hosted API that can serve multiple applications.

## Architecture Overview

The TradingAgents service is a FastAPI application that provides a REST API for generating trading analysis reports. It follows this architecture:

1. **API Layer**: FastAPI service that handles HTTP requests
2. **Processing Layer**: TradingAgents core that runs the multi-agent analysis
3. **Storage Layer**: File-based storage for reports and caching
4. **Authentication**: API key-based authentication

## Deployment Options

### 1. Docker Deployment (Recommended)

The service includes Docker support for easy deployment:

```bash
# Build the Docker image
docker build -t tradingagents-service .

# Run the service
docker run -p 8000:8000 \
  -e TRADINGAGENTS_SERVICE_API_KEY=your-secret-key \
  -e TRADINGAGENTS_SERVICE_REPORTS_DIR=/data/reports \
  -e TRADINGAGENTS_SERVICE_CACHE_DIR=/data/cache \
  -e TRADINGAGENTS_SERVICE_MEMORY_DIR=/data/memory \
  -v tradingagents-data:/data \
  tradingagents-service python scripts/run_service.py
```

### 2. Docker Compose Deployment

For a complete setup with Ollama support:

```bash
# Copy the example env file
cp .env.example .env
# Edit .env to set your API key and other configurations

# Start the services
docker-compose --profile ollama up -d
```

### 3. Cloud Provider Deployment

#### AWS ECS/EKS Deployment

1. Build and push the Docker image to ECR
2. Create an ECS service or EKS deployment
3. Configure environment variables in the task definition
4. Set up an Application Load Balancer

#### Google Cloud Run

```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/PROJECT-ID/tradingagents-service
gcloud run deploy --image gcr.io/PROJECT-ID/tradingagents-service \
  --platform managed \
  --set-env-vars TRADINGAGENTS_SERVICE_API_KEY=your-secret-key \
  --port 8000
```

#### Azure Container Instances

```bash
# Deploy to Azure Container Instances
az container create \
  --resource-group myResourceGroup \
  --name tradingagents-service \
  --image tradingagents/tradingagents:latest \
  --dns-name-label tradingagents-service \
  --ports 8000 \
  --environment-variables TRADINGAGENTS_SERVICE_API_KEY=your-secret-key
```

## Environment Variables

Configure the service using these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TRADINGAGENTS_SERVICE_API_KEY` | API key for service authentication | None (required) |
| `TRADINGAGENTS_SERVICE_REPORTS_DIR` | Directory for storing reports | `reports/api` |
| `TRADINGAGENTS_SERVICE_CACHE_DIR` | Directory for caching data | `.tradingagents_service/cache` |
| `TRADINGAGENTS_SERVICE_MEMORY_DIR` | Directory for memory logs | `.tradingagents_service/memory` |
| `TRADINGAGENTS_SERVICE_WORKERS` | Number of worker processes | `1` |
| `HOST` | Host to bind the service to | `0.0.0.0` |
| `PORT` | Port to listen on | `8000` |
| `WORKERS` | Number of Uvicorn workers | `1` |

## API Usage

### Authentication

All API endpoints require an `X-API-Key` header with a valid API key:

```http
X-API-Key: your-secret-api-key
```

### Submit Report Job

```http
POST /v1/reports
Content-Type: application/json
X-API-Key: your-secret-api-key
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

### Poll Job Status

```http
GET /v1/reports/{job_id}
X-API-Key: your-secret-api-key
```

### Download PDF Report

```http
GET /v1/reports/{job_id}/pdf
X-API-Key: your-secret-api-key
```

## API Testing with Postman

We provide a comprehensive Postman collection for testing the API:

1. Import the collection from `postman/TradingAgents-Service-API.postman_collection.json`
2. Configure the environment variables
3. Test all endpoints including error cases

The collection includes:
- Health check requests
- Report job creation with various configurations
- Job status polling
- PDF download requests
- Error case testing

## Scaling Considerations

1. **LLM Rate Limits**: Start with 1 worker and increase based on your LLM provider's rate limits
2. **Memory Usage**: Each analysis can consume significant memory; monitor usage
3. **Storage**: For production, use cloud storage (S3, GCS, Azure Blob) instead of local storage
4. **Database**: For production, replace the in-memory job store with a database

## Monitoring and Logging

The service outputs logs to stdout/stderr. For production:

1. Use a logging service (Cloud Logging, Datadog, etc.)
2. Monitor memory and CPU usage
3. Set up alerts for failed jobs
4. Track API usage and performance metrics

## Security Considerations

1. Always use HTTPS in production
2. Store API keys securely (AWS Secrets Manager, etc.)
3. Implement rate limiting to prevent abuse
4. Use a reverse proxy (nginx, Envoy) for additional security
5. Regularly update dependencies and base images

## Backup and Recovery

1. Regularly backup the storage volumes
2. Implement a backup strategy for generated reports
3. Test recovery procedures regularly
4. Monitor for failed jobs and implement retry logic

## Example Client Integration

Here's a simple Python client to interact with the service:

```python
import requests
import time

class TradingAgentsClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
    
    def submit_report(self, ticker, analysis_date=None, analysts=None):
        payload = {
            "ticker": ticker,
            "analysis_date": analysis_date,
            "selected_analysts": analysts or ["market", "news", "fundamentals"]
        }
        response = requests.post(
            f"{self.base_url}/v1/reports",
            json=payload,
            headers=self.headers
        )
        return response.json()
    
    def get_report_status(self, job_id):
        response = requests.get(
            f"{self.base_url}/v1/reports/{job_id}",
            headers=self.headers
        )
        return response.json()
    
    def download_pdf(self, job_id, filename):
        response = requests.get(
            f"{self.base_url}/v1/reports/{job_id}/pdf",
            headers=self.headers
        )
        with open(filename, 'wb') as f:
            f.write(response.content)

# Usage
client = TradingAgentsClient("http://localhost:8000", "your-api-key")
job = client.submit_report("NVDA", "2026-05-07")
print(f"Job submitted: {job['job_id']}")

# Poll for completion
while True:
    status = client.get_report_status(job['job_id'])
    if status['status'] == 'completed':
        client.download_pdf(job['job_id'], f"report_{job['job_id']}.pdf")
        print("Report downloaded!")
        break
    elif status['status'] == 'failed':
        print(f"Job failed: {status['error']}")
        break
    else:
        print(f"Job status: {status['status']}")
        time.sleep(10)
```
# Kubernetes Deployment for TradingAgents Service

This directory contains Kubernetes manifests for deploying the TradingAgents service in a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (minikube, EKS, GKE, AKS, etc.)
- kubectl configured to access your cluster
- Docker images built and available in a registry

## Deployment Steps

1. **Create the namespace:**
   ```bash
   kubectl apply -f tradingagents-service.yaml
   ```

2. **Create secrets:**
   Edit `tradingagents-secrets.yaml` with your actual API keys (base64 encoded) and apply:
   ```bash
   kubectl apply -f tradingagents-secrets.yaml
   ```

3. **Deploy the service:**
   ```bash
   kubectl apply -f tradingagents-service.yaml
   ```

## Configuration

### Environment Variables

The service is configured using a ConfigMap defined in `tradingagents-service.yaml`. You can modify these values as needed:

- `HOST`: Bind address (default: 0.0.0.0)
- `PORT`: Port to listen on (default: 8000)
- `TRADINGAGENTS_SERVICE_WORKERS`: Number of worker processes (default: 1)
- `TRADINGAGENTS_SERVICE_REPORTS_DIR`: Reports directory (default: /data/reports)
- `TRADINGAGENTS_SERVICE_CACHE_DIR`: Cache directory (default: /data/cache)
- `TRADINGAGENTS_SERVICE_MEMORY_DIR`: Memory directory (default: /data/memory)

### Secrets

Secrets are stored in `tradingagents-secrets.yaml`. You need to base64 encode your values:

```bash
echo -n 'your-api-key' | base64
```

### Persistent Storage

The deployment uses a PersistentVolumeClaim for data persistence. Adjust the storage size in the PVC definition as needed.

## Scaling

To scale the deployment:

```bash
kubectl scale deployment tradingagents-service -n tradingagents --replicas=3
```

Note: Be mindful of LLM provider rate limits when scaling.

## Monitoring

Check the deployment status:

```bash
kubectl get pods -n tradingagents
kubectl get services -n tradingagents
kubectl logs -n tradingagents -l app=tradingagents-service
```

## Updating the Deployment

To update the deployment with a new image:

1. Update the image tag in the deployment spec
2. Apply the updated manifest:
   ```bash
   kubectl apply -f tradingagents-service.yaml
   ```

## Ingress Configuration

The deployment includes an Ingress resource. Update the `host` field to match your domain:

```yaml
spec:
  rules:
  - host: tradingagents.yourdomain.com
```

Make sure your Ingress controller is properly configured.

## Security Considerations

1. Store secrets securely using Kubernetes Secrets
2. Use network policies to restrict access to the service
3. Enable TLS for the Ingress
4. Regularly update the base images
5. Monitor resource usage and set appropriate limits
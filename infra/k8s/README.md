# Pulse Kubernetes Deployment Guide

## Overview

This directory contains Kubernetes manifests for deploying Pulse in a production environment with horizontal scaling, monitoring, and high availability.

## Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- Helm (for monitoring stack)
- cert-manager (for TLS certificates)
- NGINX Ingress Controller

## Quick Start

1. **Create namespace and apply configurations:**
```bash
kubectl apply -f config.yaml
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
```

2. **Build and push Docker images:**
```bash
# Build backend image
cd backend/
docker build -t your-registry/pulse/backend:latest .
docker push your-registry/pulse/backend:latest

# Build worker image
cd ../worker/
docker build -t your-registry/pulse/worker:latest .
docker push your-registry/pulse/worker:latest
```

3. **Update image references in manifests:**
```bash
# Update backend.yaml and worker.yaml with your registry URLs
sed -i 's|pulse/backend:latest|your-registry/pulse/backend:latest|g' backend.yaml
sed -i 's|pulse/worker:latest|your-registry/pulse/worker:latest|g' worker.yaml
```

4. **Deploy application:**
```bash
kubectl apply -f backend.yaml
kubectl apply -f worker.yaml
kubectl apply -f ingress.yaml
```

## Configuration

### Secrets Setup

Update the secrets in `config.yaml` with your actual API keys:

```bash
kubectl create secret generic pulse-secrets \
  --from-literal=POSTGRES_PASSWORD=your_secure_password \
  --from-literal=NEWSAPI_KEY=your_newsapi_key \
  --from-literal=OPENAI_API_KEY=your_openai_key \
  --from-literal=X_BEARER_TOKEN=your_x_bearer_token \
  --namespace=pulse
```

### Domain Configuration

Update `ingress.yaml` with your actual domain:
- Replace `api.pulse.yourdomain.com` with your domain
- Ensure DNS points to your cluster's ingress IP

## Scaling

### Horizontal Pod Autoscaler

The deployment includes HPA for both backend and worker:

- **Backend**: 2-10 replicas based on CPU/memory usage
- **Worker**: 3-20 replicas based on CPU/memory usage

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment backend --replicas=5 -n pulse

# Scale worker
kubectl scale deployment worker --replicas=10 -n pulse
```

## Monitoring

### Prometheus Metrics

The backend exposes metrics at `/metrics` endpoint. To set up monitoring:

1. **Install Prometheus using Helm:**
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

2. **Create ServiceMonitor:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: pulse-backend
  namespace: pulse
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: http
    path: /metrics
```

### Grafana Dashboards

Import the provided Grafana dashboard from `../grafana/dashboards/` for monitoring:
- Pipeline job metrics
- HTTP request metrics
- System resource usage
- Error rates

## Storage

### Persistent Volumes

The deployment uses PVCs for data persistence:
- **PostgreSQL**: 20Gi for database storage
- **Redis**: 5Gi for cache and job queue

For production, consider:
- Using StorageClasses with better performance (SSD)
- Regular backups of PostgreSQL data
- Redis persistence configuration

## Security

### Network Policies

Create network policies to restrict traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: pulse-network-policy
  namespace: pulse
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: pulse
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  egress:
  - {}
```

### Pod Security Standards

Enable pod security standards:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: pulse
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

## Backup and Recovery

### Database Backup

Set up regular PostgreSQL backups:

```bash
# Create backup job
kubectl create job --from=cronjob/postgres-backup postgres-backup-manual -n pulse

# Restore from backup
kubectl exec -it postgres-xxx -n pulse -- psql -U pulse_user -d pulse_db < backup.sql
```

### Redis Backup

Redis data is primarily cache and job queues, but for durability:

```bash
# Enable Redis persistence in deployment
- name: redis
  image: redis:7-alpine
  command: ["redis-server", "--appendonly", "yes", "--save", "60", "1"]
```

## Troubleshooting

### Common Issues

1. **Pods stuck in Pending:**
```bash
kubectl describe pod <pod-name> -n pulse
# Check resource requests and node capacity
```

2. **Database connection issues:**
```bash
kubectl logs deployment/backend -n pulse
kubectl exec -it postgres-xxx -n pulse -- pg_isready -U pulse_user
```

3. **Worker not processing jobs:**
```bash
kubectl logs deployment/worker -n pulse
kubectl exec -it redis-xxx -n pulse -- redis-cli monitor
```

### Debug Commands

```bash
# Check all resources
kubectl get all -n pulse

# Check events
kubectl get events -n pulse --sort-by='.lastTimestamp'

# Port forward for local testing
kubectl port-forward service/backend 8000:8000 -n pulse
```

## Production Checklist

- [ ] Update all default passwords and API keys
- [ ] Configure TLS certificates
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Implement network policies
- [ ] Set resource limits and requests
- [ ] Configure log aggregation
- [ ] Set up health checks
- [ ] Plan disaster recovery
- [ ] Configure image scanning

## Cost Optimization

- Use node selectors for appropriate instance types
- Configure cluster autoscaling
- Use spot/preemptible instances for workers
- Set appropriate resource requests/limits
- Monitor and optimize based on usage patterns
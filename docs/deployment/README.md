# 🚀 Deployment Guide

## Overview

This guide covers the deployment process for the DataGovAI system in production environments. It includes infrastructure setup, security configurations, and maintenance procedures.

## System Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 4 cores | 8+ cores    |
| RAM       | 16 GB   | 32+ GB      |
| Storage   | 100 GB  | 500+ GB     |
| Network   | 1 Gbps  | 10 Gbps     |

### Software Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Python    | 3.10+   | Required for core services |
| PostgreSQL| 14+     | Database backend |
| Redis     | 7.0+    | Caching and queues |
| Docker    | 24.0+   | Container runtime |
| Kubernetes| 1.26+   | Container orchestration |

## Infrastructure Setup

### 1. Cloud Provider Configuration

```yaml
# terraform/main.tf
provider "aws" {
  region = "us-west-2"
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "datagovai-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["us-west-2a", "us-west-2b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  
  enable_nat_gateway = true
  single_nat_gateway = false
}

module "eks" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = "datagovai-cluster"
  cluster_version = "1.26"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  eks_managed_node_groups = {
    general = {
      desired_size = 2
      min_size    = 1
      max_size    = 4
      
      instance_types = ["t3.xlarge"]
      capacity_type  = "ON_DEMAND"
    }
  }
}
```

### 2. Database Setup

```yaml
# kubernetes/postgres.yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: datagovai-db
spec:
  instances: 3
  storage:
    size: 100Gi
    storageClass: gp3
  postgresql:
    parameters:
      max_connections: 200
      shared_buffers: 4GB
      effective_cache_size: 12GB
      maintenance_work_mem: 1GB
      checkpoint_completion_target: 0.9
      wal_buffers: 16MB
      default_statistics_target: 100
      random_page_cost: 1.1
      effective_io_concurrency: 200
      work_mem: 52428kB
      min_wal_size: 1GB
      max_wal_size: 4GB
```

### 3. Redis Configuration

```yaml
# kubernetes/redis.yaml
apiVersion: redis.redis.opstreelabs.in/v1beta1
kind: Redis
metadata:
  name: datagovai-redis
spec:
  kubernetesConfig:
    image: redis:7.0
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
  storage:
    volumeClaimTemplate:
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 5Gi
  redisConfig:
    maxmemory: "400mb"
    maxmemory-policy: "allkeys-lru"
```

## Application Deployment

### 1. Core Services

```yaml
# kubernetes/core-services.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: datagovai-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: datagovai-api
  template:
    metadata:
      labels:
        app: datagovai-api
    spec:
      containers:
      - name: api
        image: datagovai/api:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: datagovai-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: datagovai-secrets
              key: redis-url
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 2. Worker Services

```yaml
# kubernetes/worker-services.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: datagovai-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: datagovai-worker
  template:
    metadata:
      labels:
        app: datagovai-worker
    spec:
      containers:
      - name: worker
        image: datagovai/worker:1.0.0
        env:
        - name: QUEUE_URL
          valueFrom:
            secretKeyRef:
              name: datagovai-secrets
              key: queue-url
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 4000m
            memory: 8Gi
```

### 3. Ingress Configuration

```yaml
# kubernetes/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: datagovai-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.datagovai.utah.gov
    secretName: datagovai-tls
  rules:
  - host: api.datagovai.utah.gov
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: datagovai-api
            port:
              number: 80
```

## Security Configuration

### 1. Network Policies

```yaml
# kubernetes/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: datagovai-network-policy
spec:
  podSelector:
    matchLabels:
      app: datagovai-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: datagovai
    ports:
    - protocol: TCP
      port: 5432
    - protocol: TCP
      port: 6379
```

### 2. Secret Management

```yaml
# kubernetes/secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: datagovai-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: ClusterSecretStore
  target:
    name: datagovai-secrets
    creationPolicy: Owner
  data:
  - secretKey: database-url
    remoteRef:
      key: datagovai/production/database-url
  - secretKey: redis-url
    remoteRef:
      key: datagovai/production/redis-url
  - secretKey: api-key
    remoteRef:
      key: datagovai/production/api-key
```

## Monitoring Setup

### 1. Prometheus Configuration

```yaml
# kubernetes/prometheus.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: datagovai-monitor
spec:
  selector:
    matchLabels:
      app: datagovai-api
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
```

### 2. Grafana Dashboards

```yaml
# kubernetes/grafana-dashboards.yaml
apiVersion: integreatly.org/v1alpha1
kind: GrafanaDashboard
metadata:
  name: datagovai-dashboard
spec:
  json: |
    {
      "title": "DataGovAI Overview",
      "panels": [
        {
          "title": "API Request Rate",
          "type": "graph",
          "datasource": "Prometheus",
          "targets": [
            {
              "expr": "rate(http_requests_total{app=\"datagovai-api\"}[5m])"
            }
          ]
        },
        {
          "title": "Processing Queue Length",
          "type": "gauge",
          "datasource": "Prometheus",
          "targets": [
            {
              "expr": "processing_queue_length"
            }
          ]
        }
      ]
    }
```

## Backup and Recovery

### 1. Backup Configuration

```yaml
# kubernetes/backup.yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: datagovai-backup
spec:
  schedule: "0 1 * * *"
  template:
    includedNamespaces:
    - datagovai
    includedResources:
    - deployments
    - services
    - configmaps
    - secrets
    volumeSnapshotLocations:
    - name: aws-default
  ttl: 720h
```

### 2. Database Backup

```bash
#!/bin/bash
# scripts/backup-database.sh

# Set variables
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="datagovai"

# Create backup
pg_dump \
  --format=custom \
  --compress=9 \
  --file="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.backup" \
  --username="${DB_USER}" \
  --host="${DB_HOST}" \
  "${DB_NAME}"

# Rotate old backups (keep last 30 days)
find ${BACKUP_DIR} -type f -mtime +30 -delete
```

## Scaling Configuration

### 1. Horizontal Pod Autoscaling

```yaml
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: datagovai-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: datagovai-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. Vertical Pod Autoscaling

```yaml
# kubernetes/vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: datagovai-api-vpa
spec:
  targetRef:
    apiVersion: "apps/v1"
    kind: Deployment
    name: datagovai-api
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: '*'
      minAllowed:
        cpu: 100m
        memory: 512Mi
      maxAllowed:
        cpu: 4
        memory: 8Gi
```

## Maintenance Procedures

### 1. Database Maintenance

```sql
-- maintenance/vacuum.sql
VACUUM ANALYZE documents;
VACUUM ANALYZE chunks;
VACUUM ANALYZE entities;
VACUUM ANALYZE relationships;

-- maintenance/reindex.sql
REINDEX TABLE documents;
REINDEX TABLE chunks;
REINDEX TABLE entities;
REINDEX TABLE relationships;
```

### 2. Cache Maintenance

```bash
#!/bin/bash
# scripts/clear-cache.sh

# Clear Redis cache
redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} FLUSHDB

# Clear vector cache
kubectl exec -it \
  $(kubectl get pod -l app=datagovai-api -o jsonpath='{.items[0].metadata.name}') \
  -- python -c "from app.cache import clear_vector_cache; clear_vector_cache()"
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database connectivity
   kubectl exec -it ${POD_NAME} -- pg_isready -h ${DB_HOST}
   
   # Check connection pool metrics
   kubectl exec -it ${POD_NAME} -- python -c "
   from app.db import get_pool_metrics
   print(get_pool_metrics())
   "
   ```

2. **Memory Issues**
   ```bash
   # Check memory usage
   kubectl top pods
   
   # Get container memory stats
   kubectl exec -it ${POD_NAME} -- cat /sys/fs/cgroup/memory/memory.stat
   ```

3. **Network Issues**
   ```bash
   # Test network connectivity
   kubectl exec -it ${POD_NAME} -- curl -v ${SERVICE_URL}
   
   # Check DNS resolution
   kubectl exec -it ${POD_NAME} -- nslookup ${SERVICE_NAME}
   ```

## See Also
- [Architecture Overview](../architecture/README.md)
- [API Documentation](../api/README.md)
- [Monitoring Guide](../maintenance/monitoring.md) 
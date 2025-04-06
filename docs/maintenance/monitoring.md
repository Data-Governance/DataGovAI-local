# 📊 Monitoring Guide

## Overview

This guide covers the monitoring setup and practices for the DataGovAI system. It includes metrics collection, alerting, logging, and performance monitoring.

## Metrics Collection

### 1. Application Metrics

```python
# app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration_seconds = Histogram(
    'request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

# Processing metrics
documents_processed_total = Counter(
    'documents_processed_total',
    'Total documents processed',
    ['status']
)

processing_duration_seconds = Histogram(
    'processing_duration_seconds',
    'Document processing duration in seconds',
    buckets=[1, 5, 10, 30, 60, 120]
)

# Queue metrics
processing_queue_length = Gauge(
    'processing_queue_length',
    'Number of documents in processing queue'
)

# Database metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)
```

### 2. System Metrics

```yaml
# kubernetes/node-exporter.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      containers:
      - name: node-exporter
        image: prom/node-exporter:v1.6.0
        args:
        - --path.procfs=/host/proc
        - --path.sysfs=/host/sys
        volumeMounts:
        - name: proc
          mountPath: /host/proc
        - name: sys
          mountPath: /host/sys
        ports:
        - containerPort: 9100
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys
```

## Alerting Configuration

### 1. Alert Rules

```yaml
# kubernetes/prometheus-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: datagovai-alerts
spec:
  groups:
  - name: datagovai
    rules:
    # High error rate alert
    - alert: HighErrorRate
      expr: |
        sum(rate(http_requests_total{status=~"5.."}[5m])) 
        / 
        sum(rate(http_requests_total[5m])) > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: High HTTP error rate
        description: Error rate is above 5% for 5 minutes

    # Processing queue backup
    - alert: ProcessingQueueBackup
      expr: processing_queue_length > 1000
      for: 15m
      labels:
        severity: warning
      annotations:
        summary: Processing queue is backing up
        description: Queue length has been above 1000 for 15 minutes

    # Database connection saturation
    - alert: DatabaseConnectionSaturation
      expr: db_connections_active / db_connections_max > 0.8
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: Database connections near limit
        description: Over 80% of database connections are in use

    # High memory usage
    - alert: HighMemoryUsage
      expr: container_memory_usage_bytes{container!=""} 
            / container_spec_memory_limit_bytes{container!=""} > 0.9
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: High memory usage
        description: Container using over 90% of memory limit
```

### 2. Alert Manager Configuration

```yaml
# kubernetes/alertmanager.yaml
apiVersion: monitoring.coreos.com/v1
kind: Alertmanager
metadata:
  name: datagovai
spec:
  replicas: 2
  config:
    global:
      resolve_timeout: 5m
      slack_api_url: '${SLACK_WEBHOOK_URL}'
      opsgenie_api_key: '${OPSGENIE_API_KEY}'

    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
      receiver: 'slack-notifications'
      routes:
      - match:
          severity: critical
        receiver: 'opsgenie-critical'
        continue: true

    receivers:
    - name: 'slack-notifications'
      slack_configs:
      - channel: '#datagovai-alerts'
        send_resolved: true
        title: '{{ template "slack.title" . }}'
        text: '{{ template "slack.text" . }}'

    - name: 'opsgenie-critical'
      opsgenie_configs:
      - api_key: '${OPSGENIE_API_KEY}'
        message: '{{ template "opsgenie.message" . }}'
        description: '{{ template "opsgenie.description" . }}'
        tags: ['{{ .GroupLabels.alertname }}', '{{ .GroupLabels.severity }}']
        priority: P1
```

## Logging Configuration

### 1. Application Logging

```python
# app/logging/config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(timestamp)s %(level)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'json',
            'filename': '/var/log/datagovai/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        'app': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'app.api': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'app.processing': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    }
}

# Initialize logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('app')
```

### 2. Log Aggregation

```yaml
# kubernetes/fluentd.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1.16-debian-elasticsearch7-1
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch-master"
        - name: FLUENT_ELASTICSEARCH_PORT
          value: "9200"
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: containers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: containers
        hostPath:
          path: /var/lib/docker/containers
```

## Dashboard Configuration

### 1. System Overview

```json
{
  "dashboard": {
    "title": "DataGovAI System Overview",
    "panels": [
      {
        "title": "System Health",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(up{job=\"datagovai\"})",
            "legendFormat": "Healthy Services"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (endpoint)",
            "legendFormat": "{{endpoint}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
            "legendFormat": "Error Rate"
          }
        ]
      }
    ]
  }
}
```

### 2. Processing Pipeline

```json
{
  "dashboard": {
    "title": "Document Processing Pipeline",
    "panels": [
      {
        "title": "Processing Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(documents_processed_total[5m])",
            "legendFormat": "Documents/min"
          }
        ]
      },
      {
        "title": "Processing Duration",
        "type": "heatmap",
        "targets": [
          {
            "expr": "rate(processing_duration_seconds_bucket[5m])",
            "legendFormat": "{{le}}"
          }
        ]
      },
      {
        "title": "Queue Length",
        "type": "gauge",
        "targets": [
          {
            "expr": "processing_queue_length",
            "legendFormat": "Queue Size"
          }
        ]
      }
    ]
  }
}
```

## Performance Monitoring

### 1. Query Performance

```sql
-- monitoring/slow_queries.sql
SELECT 
    calls,
    total_time / 1000 as total_seconds,
    mean_time / 1000 as mean_seconds,
    query
FROM pg_stat_statements
WHERE db_name = 'datagovai'
ORDER BY total_time DESC
LIMIT 10;

-- monitoring/index_usage.sql
SELECT 
    schemaname,
    relname,
    seq_scan,
    idx_scan,
    n_live_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

### 2. Cache Performance

```python
# app/monitoring/cache.py
from prometheus_client import Histogram

cache_operation_duration = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration in seconds',
    ['operation', 'cache_type'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1]
)

def monitor_cache_performance():
    # Redis cache stats
    redis_info = redis_client.info()
    cache_hits = redis_info['keyspace_hits']
    cache_misses = redis_info['keyspace_misses']
    hit_rate = cache_hits / (cache_hits + cache_misses)
    
    # Vector cache stats
    vector_cache_stats = vector_cache.get_stats()
    vector_hit_rate = vector_cache_stats['hits'] / vector_cache_stats['total']
    
    return {
        'redis_hit_rate': hit_rate,
        'vector_hit_rate': vector_hit_rate,
        'memory_usage': redis_info['used_memory_human'],
        'total_keys': redis_info['db0']['keys']
    }
```

## Resource Utilization

### 1. Memory Monitoring

```python
# app/monitoring/resources.py
import psutil
from prometheus_client import Gauge

process_memory_bytes = Gauge(
    'process_memory_bytes',
    'Memory usage by process',
    ['process_name']
)

def monitor_memory():
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            process_memory_bytes.labels(
                process_name=proc.info['name']
            ).set(proc.info['memory_info'].rss)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
```

### 2. CPU Monitoring

```python
# app/monitoring/resources.py
from prometheus_client import Gauge

process_cpu_seconds = Gauge(
    'process_cpu_seconds_total',
    'CPU time spent by process',
    ['process_name', 'mode']
)

def monitor_cpu():
    for proc in psutil.process_iter(['pid', 'name', 'cpu_times']):
        try:
            cpu_times = proc.info['cpu_times']
            process_cpu_seconds.labels(
                process_name=proc.info['name'],
                mode='user'
            ).set(cpu_times.user)
            process_cpu_seconds.labels(
                process_name=proc.info['name'],
                mode='system'
            ).set(cpu_times.system)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
```

## Maintenance Tasks

### 1. Log Rotation

```yaml
# kubernetes/logrotate-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: logrotate-config
data:
  logrotate.conf: |
    /var/log/datagovai/*.log {
        daily
        rotate 7
        compress
        delaycompress
        missingok
        notifempty
        create 0640 datagovai datagovai
        postrotate
            systemctl reload datagovai
        endscript
    }
```

### 2. Metric Cleanup

```python
# app/maintenance/metrics.py
from datetime import datetime, timedelta

def cleanup_old_metrics():
    # Clean up old time series data
    cutoff = datetime.utcnow() - timedelta(days=30)
    
    # Delete old metrics from Prometheus
    prometheus.delete_series(
        match=['job="datagovai"'],
        start=datetime.min,
        end=cutoff
    )
    
    # Compact storage
    prometheus.compact()
```

## See Also
- [Deployment Guide](../deployment/README.md)
- [Architecture Overview](../architecture/README.md)
- [API Documentation](../api/README.md) 
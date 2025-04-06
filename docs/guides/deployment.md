# 🚀 Deployment Guide

This guide provides detailed instructions for deploying the DataGovAI Knowledge Base system in a production environment.

## 📋 Prerequisites

### Hardware Requirements
- **CPU**: 8+ cores
- **RAM**: 32GB minimum
- **GPU**: NVIDIA GPU with 16GB+ VRAM
- **Storage**: 500GB+ SSD
- **Network**: 1Gbps minimum

### Software Requirements
- Ubuntu 22.04 LTS or later
- Docker 24.0+
- Docker Compose 2.20+
- NVIDIA Container Toolkit
- PostgreSQL 15+
- Redis 7.0+

## 🔧 Installation

### 1. System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    docker.io \
    docker-compose \
    postgresql-15 \
    redis-server \
    nvidia-container-toolkit

# Configure NVIDIA Container Toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 2. Clone Repository
```bash
git clone https://github.com/utah-odp/datagovai.git
cd datagovai
git checkout main  # or specific version tag
```

### 3. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit environment variables
nano .env
```

Required environment variables:
```env
# Database Configuration
POSTGRES_USER=kb_agent_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=knowledge_base
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=secure_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_KEY=your_secure_api_key

# Model Configuration
EMBEDDING_MODEL=all-mpnet-base-v2
EMBEDDING_DEVICE=cuda
EXTRACTOR_MODEL=mistralai/Mistral-7B-Instruct-v0.2
EXTRACTOR_DEVICE=cuda
EXTRACTOR_4BIT=true

# Security
JWT_SECRET=your_secure_jwt_secret
ALLOWED_ORIGINS=https://your-domain.com
```

### 4. Database Setup
```bash
# Create database and user
sudo -u postgres psql

postgres=# CREATE USER kb_agent_user WITH PASSWORD 'secure_password';
postgres=# CREATE DATABASE knowledge_base;
postgres=# GRANT ALL PRIVILEGES ON DATABASE knowledge_base TO kb_agent_user;
postgres=# \q

# Run migrations
docker-compose run --rm api python -m alembic upgrade head
```

### 5. Docker Deployment
```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d
```

## 🔒 Security Configuration

### 1. SSL/TLS Setup
```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Configure Nginx
sudo nano /etc/nginx/sites-available/datagovai
```

Nginx configuration:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Firewall Configuration
```bash
# Configure UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. API Key Management
```bash
# Generate secure API key
openssl rand -base64 32

# Add to environment
echo "API_KEY=generated_key" >> .env
```

## 📊 Monitoring Setup

### 1. Prometheus Configuration
```yaml
# /etc/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'datagovai'
    static_configs:
      - targets: ['localhost:8000']
```

### 2. Grafana Dashboard
```bash
# Install Grafana
sudo apt install -y grafana

# Start Grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

### 3. Logging Configuration
```yaml
# config/logging.yml
version: 1
formatters:
  json:
    format: '%(asctime)s %(levelname)s %(name)s %(message)s'
handlers:
  file:
    class: logging.handlers.RotatingFileHandler
    formatter: json
    filename: /var/log/datagovai/app.log
    maxBytes: 10485760
    backupCount: 5
```

## 🔄 Maintenance Procedures

### 1. Backup Configuration
```bash
# Database backup
pg_dump -U kb_agent_user knowledge_base > backup.sql

# Document backup
rsync -av /data/documents/ /backup/documents/
```

### 2. Update Procedure
```bash
# Stop services
docker-compose down

# Pull updates
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations
docker-compose run --rm api python -m alembic upgrade head
```

### 3. Health Checks
```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs -f api

# Monitor resources
htop
nvidia-smi
```

## 🎯 Performance Tuning

### 1. PostgreSQL Optimization
```ini
# /etc/postgresql/15/main/postgresql.conf
max_connections = 100
shared_buffers = 8GB
effective_cache_size = 24GB
maintenance_work_mem = 2GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 83886kB
min_wal_size = 1GB
max_wal_size = 4GB
```

### 2. Redis Configuration
```ini
# /etc/redis/redis.conf
maxmemory 8gb
maxmemory-policy allkeys-lru
```

### 3. API Server Tuning
```python
# config/gunicorn.py
workers = 4
worker_class = 'uvicorn.workers.UvicornWorker'
bind = '0.0.0.0:8000'
max_requests = 1000
max_requests_jitter = 50
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Issues**
```bash
# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Test connection
psql -U kb_agent_user -h localhost -d knowledge_base
```

2. **GPU Issues**
```bash
# Check GPU status
nvidia-smi

# Check container GPU access
docker run --gpus all nvidia/cuda:12.0-base nvidia-smi
```

3. **API Performance Issues**
```bash
# Check API logs
docker-compose logs api

# Monitor resource usage
docker stats
```

## 📈 Scaling Guidelines

### 1. Horizontal Scaling
- Deploy multiple API instances
- Use load balancer
- Implement Redis cluster
- Configure PostgreSQL replication

### 2. Vertical Scaling
- Upgrade GPU capacity
- Increase RAM
- Add CPU cores
- Expand storage

## 🔗 Additional Resources

- [Architecture Documentation](../architecture/README.md)
- [API Documentation](../api-reference/README.md)
- [Monitoring Guide](monitoring.md)
- [Backup Guide](backup_recovery.md)

---

For technical support, contact the DataGovAI team at support@datagovai.utah.gov 
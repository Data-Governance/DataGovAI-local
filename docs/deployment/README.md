# 🚀 Deployment Guide

## Overview

This guide covers the deployment process for the DataGovAI system in production environments.

## Prerequisites

| Component | Requirement |
|-----------|-------------|
| Python | 3.10+ |
| PostgreSQL | 14+ with pgvector |
| Redis | 7.0+ |
| CUDA | 12.0+ (for GPU support) |

## Directory Structure

```
DataGovAI/
├── app/                # Main application code
│   ├── static/        # CSS, JS, and assets
│   └── templates/     # HTML templates
├── app.py             # Flask application
├── data/              # Document storage
├── docs/              # Documentation
├── scripts/           # Utility scripts
└── tests/             # Test suite
```

## Deployment Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DataGovAI.git
cd DataGovAI
```

2. Create and activate virtual environment:
```bash
python -m venv prod_env
source prod_env/bin/activate
```

3. Install production dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with production settings
```

5. Initialize database:
```bash
python scripts/init_db.py
```

6. Configure Gunicorn:
```bash
# gunicorn.conf.py
workers = 4
bind = "0.0.0.0:8000"
worker_class = "uvicorn.workers.UvicornWorker"
```

7. Start the application:
```bash
gunicorn app:app
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| FLASK_ENV | Environment type | `production` |
| DEBUG | Debug mode | `False` |
| DATABASE_URL | PostgreSQL connection | `postgresql://user:pass@host:5432/db` |
| REDIS_URL | Redis connection | `redis://localhost:6379/0` |
| SECRET_KEY | Application secret | `your-secret-key` |
| ALLOWED_HOSTS | Allowed hostnames | `example.com,api.example.com` |

## Security Considerations

1. SSL/TLS Configuration:
```nginx
# /etc/nginx/sites-available/datagovai
server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. Firewall Rules:
```bash
# Allow only necessary ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5432/tcp  # PostgreSQL
ufw enable
```

## Monitoring

1. Configure logging:
```python
# logging.conf
[loggers]
keys=root,gunicorn.error,gunicorn.access

[handlers]
keys=console,error_file,access_file

[formatters]
keys=generic,access

[logger_root]
level=INFO
handlers=console

[logger_gunicorn.error]
level=INFO
handlers=error_file
propagate=0
qualname=gunicorn.error

[logger_gunicorn.access]
level=INFO
handlers=access_file
propagate=0
qualname=gunicorn.access

[handler_console]
class=StreamHandler
formatter=generic
args=(sys.stdout, )

[handler_error_file]
class=logging.FileHandler
formatter=generic
args=('/var/log/datagovai/error.log',)

[handler_access_file]
class=logging.FileHandler
formatter=access
args=('/var/log/datagovai/access.log',)

[formatter_generic]
format=%(asctime)s [%(process)d] [%(levelname)s] %(message)s
datefmt=%Y-%m-%d %H:%M:%S
class=logging.Formatter

[formatter_access]
format=%(message)s
class=logging.Formatter
```

2. Set up monitoring tools:
```bash
# Install Prometheus and Grafana
apt-get update
apt-get install -y prometheus grafana

# Configure Prometheus
cat > /etc/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'datagovai'
    static_configs:
      - targets: ['localhost:8000']
EOF

# Start services
systemctl enable prometheus grafana-server
systemctl start prometheus grafana-server
```

## Backup and Recovery

1. Database backup:
```bash
#!/bin/bash
# /usr/local/bin/backup-datagovai.sh

BACKUP_DIR="/var/backups/datagovai"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup database
pg_dump -U datagovai_user datagovai > "$BACKUP_DIR/db_$TIMESTAMP.sql"

# Backup document storage
tar -czf "$BACKUP_DIR/documents_$TIMESTAMP.tar.gz" /path/to/data/documents

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -type f -mtime +7 -delete
```

2. Recovery procedure:
```bash
# Restore database
psql -U datagovai_user datagovai < backup.sql

# Restore documents
tar -xzf documents_backup.tar.gz -C /path/to/data/
```

## Scaling

1. Horizontal scaling:
```nginx
# /etc/nginx/conf.d/upstream.conf
upstream datagovai {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
}
```

2. Load balancing:
```nginx
# /etc/nginx/sites-available/datagovai
server {
    listen 443 ssl;
    server_name api.example.com;

    location / {
        proxy_pass http://datagovai;
        proxy_next_upstream error timeout invalid_header http_500;
        proxy_next_upstream_tries 3;
    }
}
```

## Troubleshooting

Common issues and solutions:

1. Application not starting:
```bash
# Check logs
tail -f /var/log/datagovai/error.log

# Verify permissions
chown -R datagovai:datagovai /path/to/application
chmod -R 755 /path/to/application
```

2. Database connection issues:
```bash
# Check PostgreSQL status
systemctl status postgresql

# Verify connection
psql -U datagovai_user -h localhost -d datagovai
```

3. Memory issues:
```bash
# Monitor memory usage
free -m
top

# Adjust Gunicorn workers
worker_class = "uvicorn.workers.UvicornWorker"
workers = 4
worker_connections = 1000
```

## Support

For deployment support:
- Email: devops@datagovai.utah.gov
- Internal Wiki: https://wiki.utah.gov/datagovai/deployment
- Emergency Contact: +1 (555) 123-4567 
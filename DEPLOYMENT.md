# Project Management Service - Deployment Guide

## Quick Start (Docker Compose)

### Prerequisites

- Docker & Docker Compose installed
- 4+ GB RAM available
- Ports 8000, 5432, 6379 available

### Step 1: Clone & Configure

```bash
git clone <repo>
cd backend
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### Step 2: Initialize Database

```bash
# Create initial database schema
docker compose run --rm web python -c "from projects import init_db; init_db()"
```

### Step 3: Start Services

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f web celery-worker-git celery-worker-webhooks

# Verify health
curl http://localhost:8000/health
```

### Step 4: Access Services

- **FastAPI API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Flower (Celery Monitoring)**: http://localhost:5555
- **PostgreSQL**: localhost:5432 (psql)
- **Redis**: localhost:6379 (redis-cli)

## Production Deployment

### Architecture for Production

```
┌─────────────────────────────────────────────────────────┐
│                  Load Balancer (ALB)                    │
│                    (SSL/TLS)                            │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
    ┌───▼───┐   ┌───▼───┐   ┌───▼───┐
    │ Web 1 │   │ Web 2 │   │ Web 3 │  (Auto-scaling group)
    └───┬───┘   └───┬───┘   └───┬───┘
        │           │           │
        └───────────┼───────────┘
                    │
        ┌───────────▼───────────┐
        │ RDS PostgreSQL (HA)   │
        │ - Primary + Standby   │
        │ - Automated backups   │
        │ - Multi-AZ            │
        └───────────────────────┘

        ┌───────────┐
        │ ElastiCache Redis     │
        │ - Cluster mode        │
        │ - Automatic failover  │
        └───────────┘

        ┌────────────────────────────────┐
        │ Celery Worker Fleet            │
        │ ├─ Workers (Git ops): 5-10     │
        │ ├─ Workers (Webhooks): 10-20   │
        │ ├─ Beat scheduler: 1           │
        │ └─ Auto-scaling on queue depth │
        └────────────────────────────────┘
```

### AWS Deployment (Kubernetes on EKS)

#### 1. Create Kubernetes Manifests

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: projects-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: projects-web
  template:
    metadata:
      labels:
        app: projects-web
    spec:
      containers:
      - name: web
        image: your-registry/projects-web:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: projects-secrets
              key: database-url
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
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
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: projects-web-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  selector:
    app: projects-web

---
apiVersion: batch/v1
kind: Deployment
metadata:
  name: projects-worker-git
spec:
  replicas: 5
  selector:
    matchLabels:
      app: projects-worker-git
  template:
    metadata:
      labels:
        app: projects-worker-git
    spec:
      containers:
      - name: worker
        image: your-registry/projects-worker:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: projects-secrets
              key: database-url
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef:
              name: projects-secrets
              key: redis-url
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
        volumeMounts:
        - name: repos
          mountPath: /data/repos
      volumes:
      - name: repos
        persistentVolumeClaim:
          claimName: projects-repos-pvc
```

#### 2. Deploy to EKS

```bash
# Create namespace
kubectl create namespace projects

# Create secrets
kubectl create secret generic projects-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=redis-url="redis://..." \
  -n projects

# Deploy
kubectl apply -f deployment.yaml -n projects

# Verify
kubectl get pods -n projects
kubectl logs -f deployment/projects-web -n projects
```

### Docker Image Building

#### Dockerfile.web

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Dockerfile.worker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

CMD ["celery", "-A", "src.projects.celery_app", "worker", "-l", "info"]
```

#### Build & Push

```bash
docker build -f Dockerfile.web -t your-registry/projects-web:latest .
docker build -f Dockerfile.worker -t your-registry/projects-worker:latest .

docker push your-registry/projects-web:latest
docker push your-registry/projects-worker:latest
```

## Monitoring & Logging

### Metrics to Track

1. **API Performance**
   - Request latency (p50, p95, p99)
   - Error rate (4xx, 5xx)
   - Request volume per endpoint

2. **Background Jobs**
   - Clone job success rate
   - Task execution time distribution
   - Queue depth

3. **Infrastructure**
   - Database connection pool usage
   - Redis memory usage
   - CPU/Memory per service

### CloudWatch Integration

```python
# In main.py
import watchtower
import logging

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        watchtower.CloudWatchLogHandler(
            log_group="/aws/projects/service",
            stream_name="projects-api"
        )
    ]
)
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

repo_clone_duration = Histogram(
    "repo_clone_duration_seconds",
    "Time to clone repository",
    ["provider", "status"]
)

webhook_events = Counter(
    "webhook_events_total",
    "Total webhook events received",
    ["provider", "event_type"]
)
```

## Backup & Disaster Recovery

### Database Backups

```bash
# Manual backup
docker compose exec postgres pg_dump -U postgres projects_db > backup-$(date +%Y%m%d).sql

# Restore
docker compose exec -T postgres psql -U postgres projects_db < backup-20260519.sql
```

### Production Strategy

1. **Automated Backups**
   - RDS automatic backups (daily, 7-day retention)
   - S3 cross-region replication

2. **Repositories**
   - Regular git GC (garbage collection)
   - Mirror to backup location
   - EBS snapshots of /data/repos volume

3. **Recovery Plan**
   - RTO: 1 hour (database restoration)
   - RPO: 1 hour (last backup)
   - Tested weekly via failover drills

## Security

### SSL/TLS

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Secrets Management

Use AWS Secrets Manager or HashiCorp Vault:

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name projects/database-url \
  --secret-string "postgresql://..."

# Kubernetes
kubectl create secret generic projects-db \
  --from-literal=password="..." \
  -n projects
```

### Network Security

- Deploy in private subnet
- RDS in private subnet with security group
- Redis in private subnet
- ALB in public subnet only
- VPC security groups restrict traffic

## Scaling

### Horizontal Scaling

```bash
# Scale web replicas
kubectl scale deployment projects-web --replicas=5 -n projects

# Scale workers
kubectl scale deployment projects-worker-git --replicas=10 -n projects
```

### Auto-scaling Policy

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: projects-web-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: projects-web
  minReplicas: 3
  maxReplicas: 20
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

## Troubleshooting

### Issue: Clone tasks stuck in PENDING

```bash
# Check Celery queue depth
redis-cli LLEN celery

# Inspect task
celery -A projects.celery_app inspect active

# Restart workers
docker compose restart celery-worker-git
```

### Issue: Database connection exhausted

```bash
# Check connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Increase pool size in DATABASE_URL
sqlalchemy.pool_size = 30
sqlalchemy.max_overflow = 10
```

### Issue: Webhook not triggered

```bash
# Check webhook delivery logs
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/{owner}/{repo}/hooks/{id}/deliveries

# Verify webhook secret matches
SELECT webhook_secret FROM webhook_subscriptions WHERE id = ...
```

## Maintenance

### Database Maintenance

```bash
# Vacuum & analyze (weekly)
VACUUM ANALYZE;

# Reindex (monthly)
REINDEX DATABASE projects_db;
```

### Git Repository Maintenance

```bash
# Run git GC on all repos (monthly)
for repo in /data/repos/*; do
  git -C "$repo" gc --aggressive
done
```

### Dependency Updates

```bash
# Check for vulnerabilities
pip audit

# Update dependencies
pip install --upgrade -r requirements.txt
```

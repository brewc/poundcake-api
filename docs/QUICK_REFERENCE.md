# Quick Reference Guide

## Getting Started in 3 Minutes

```bash
# 1. Navigate to project
cd poundcake-api

# 2. Start services
./quickstart.sh

# 3. Test the API
curl http://localhost:8000/api/v1/health
```

That's it! You now have a fully functional Alertmanager processor running.

## Common Commands

### Docker Operations
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart api

# Scale workers
docker-compose up -d --scale worker=5

# Rebuild images
docker-compose build
```

### API Testing
```bash
# Health check
curl http://localhost:8000/api/v1/health

# List alerts
curl http://localhost:8000/api/v1/alerts

# Get statistics
curl http://localhost:8000/api/v1/stats

# Send test webhook
curl -X POST http://localhost:8000/api/v1/webhook \
  -H "Content-Type: application/json" \
  -d @tests/sample_webhook.json
```

### Database Operations
```bash
# Connect to database
docker-compose exec mariadb psql -U mariadb -d poundcake

# View tables
docker-compose exec mariadb psql -U mariadb -d poundcake -c "\dt"

# Query alerts
docker-compose exec mariadb psql -U mariadb -d poundcake -c \
  "SELECT fingerprint, alert_name, status, processing_status FROM alerts ORDER BY created_at DESC LIMIT 10;"

# Query API calls
docker-compose exec mariadb psql -U mariadb -d poundcake -c \
  "SELECT request_id, method, path, status_code, created_at FROM api_calls ORDER BY created_at DESC LIMIT 10;"
```

### Redis Operations
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# View all keys
docker-compose exec redis redis-cli KEYS '*'

# Monitor Redis commands
docker-compose exec redis redis-cli MONITOR

# Check queue length
docker-compose exec redis redis-cli LLEN celery

# Flush all data (DANGER!)
docker-compose exec redis redis-cli FLUSHALL
```

### Celery Operations
```bash
# Check worker status
docker-compose exec worker celery -A app.tasks.celery_app:celery_app inspect active

# View registered tasks
docker-compose exec worker celery -A app.tasks.celery_app:celery_app inspect registered

# View worker stats
docker-compose exec worker celery -A app.tasks.celery_app:celery_app inspect stats

# Purge all tasks (DANGER!)
docker-compose exec worker celery -A app.tasks.celery_app:celery_app purge
```

## Monitoring Dashboards

### Flower (Celery Monitoring)
- **URL**: http://localhost:5555
- **Features**: Real-time task monitoring, worker stats, task history

### API Documentation
- **URL**: http://localhost:8000/docs
- **Features**: Interactive API testing, schema exploration

## Key Metrics to Monitor

### API Metrics
```bash
# Request rate
SELECT COUNT(*) FROM api_calls WHERE created_at > NOW() - INTERVAL '1 hour';

# Average response time
SELECT AVG(processing_time_ms) FROM api_calls WHERE created_at > NOW() - INTERVAL '1 hour';

# Error rate
SELECT 
  COUNT(CASE WHEN status_code >= 400 THEN 1 END)::float / COUNT(*) * 100 as error_rate_percent
FROM api_calls 
WHERE created_at > NOW() - INTERVAL '1 hour';
```

### Alert Metrics
```bash
# Alerts by status
SELECT status, COUNT(*) FROM alerts GROUP BY status;

# Processing status
SELECT processing_status, COUNT(*) FROM alerts GROUP BY processing_status;

# Recent alerts
SELECT COUNT(*) FROM alerts WHERE created_at > NOW() - INTERVAL '1 hour';

# Failed alerts
SELECT fingerprint, alert_name, error_message 
FROM alerts 
WHERE processing_status = 'failed' 
ORDER BY created_at DESC 
LIMIT 10;
```

### Celery Metrics
Access via Flower: http://localhost:5555

## Troubleshooting

### API Not Responding
```bash
# Check if container is running
docker-compose ps api

# View API logs
docker-compose logs -f api

# Restart API
docker-compose restart api

# Check health
curl http://localhost:8000/api/v1/health
```

### Alerts Not Processing
```bash
# Check worker status
docker-compose ps worker

# View worker logs
docker-compose logs -f worker

# Check Celery connection
docker-compose exec worker celery -A app.tasks.celery_app:celery_app inspect ping

# Check queue depth
docker-compose exec redis redis-cli LLEN celery

# Restart workers
docker-compose restart worker
```

### Database Connection Issues
```bash
# Check MariaDB is running
docker-compose ps mariadb

# View database logs
docker-compose logs postgres

# Test connection
docker-compose exec mariadb psql -U mariadb -d poundcake -c "SELECT 1;"

# Restart database (CAUTION: may cause downtime)
docker-compose restart postgres
```

### Out of Memory
```bash
# Check container memory usage
docker stats

# Increase memory limits in docker-compose.yml
services:
  api:
  deploy:
  resources:
    limits:
    memory: 2G

# Restart services
docker-compose up -d
```

## Configuration

### Environment Variables

Key variables in `.env`:

```bash
# Database
DATABASE_URL=mysql+pymysql://poundcake:poundcake@mariadb:3306/alertmanager

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1

# API
API_PORT=8000
API_WORKERS=4

# Celery
CELERY_WORKER_PREFETCH_MULTIPLIER=4
CELERY_TASK_TIME_LIMIT=300

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Scaling Guidelines

#### API Instances
- Light load (< 10 req/s): 2 instances
- Medium load (10-50 req/s): 3-4 instances
- Heavy load (> 50 req/s): 5+ instances

#### Celery Workers
- Light load (< 100 alerts/min): 2 workers
- Medium load (100-500 alerts/min): 4-6 workers
- Heavy load (> 500 alerts/min): 8+ workers

#### Database
- Light load: 2 CPU, 4GB RAM
- Medium load: 4 CPU, 8GB RAM
- Heavy load: 8+ CPU, 16GB+ RAM

## Sample Webhook Payload

Save as `sample_webhook.json`:

```json
{
  "version": "4",
  "groupKey": "{}:{alertname=\"HighCPUUsage\"}",
  "truncatedAlerts": 0,
  "status": "firing",
  "receiver": "webhook",
  "groupLabels": {
  "alertname": "HighCPUUsage"
  },
  "commonLabels": {
  "alertname": "HighCPUUsage",
  "severity": "warning",
  "instance": "server-01:9100"
  },
  "commonAnnotations": {
  "summary": "High CPU usage detected",
  "description": "CPU usage is above 80% for more than 5 minutes"
  },
  "externalURL": "http://alertmanager:9093",
  "alerts": [
  {
  "status": "firing",
  "labels": {
    "alertname": "HighCPUUsage",
    "severity": "warning",
    "instance": "server-01:9100",
    "job": "node-exporter"
  },
  "annotations": {
    "summary": "High CPU usage on server-01",
    "description": "CPU usage is 85% (threshold: 80%)"
  },
  "startsAt": "2024-01-09T10:00:00Z",
  "endsAt": "0001-01-01T00:00:00Z",
  "generatorURL": "http://prometheus:9090/graph?g0.expr=...",
  "fingerprint": "abc123def456"
  }
  ]
}
```

## Production Checklist

Before deploying to production:

- [ ] Change default passwords in `.env`
- [ ] Enable authentication on API
- [ ] Configure TLS/SSL certificates
- [ ] Set up automated backups
- [ ] Configure monitoring alerts
- [ ] Document runbooks
- [ ] Test disaster recovery
- [ ] Set retention policies
- [ ] Review security settings
- [ ] Configure log aggregation
- [ ] Set up metrics collection
- [ ] Test with production load

## Additional Resources

- **Full Documentation**: See `README.md`
- **Architecture Details**: See `docs/ARCHITECTURE.md`
- **API Documentation**: http://localhost:8000/docs (when running)
- **Flower Dashboard**: http://localhost:5555 (when running)

## Getting Help

### Check Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f postgres
```

### Common Issues

**Port Already in Use**:
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # API on 8001 instead of 8000
```

**Permission Denied**:
```bash
# Make sure Docker has permissions
sudo chmod 666 /var/run/docker.sock
```

**Services Won't Start**:
```bash
# Clean up and start fresh
docker-compose down -v
docker-compose up -d --build
```

## Learning Path

1. **Day 1**: Get it running with quickstart.sh
2. **Day 2**: Send test webhooks, explore API
3. **Day 3**: Configure Alertmanager integration
4. **Day 4**: Customize alert processing logic
5. **Day 5**: Set up monitoring and alerting
6. **Week 2**: Production hardening
7. **Week 3**: Performance tuning
8. **Week 4**: Operational excellence

---

**Happy Monitoring! **

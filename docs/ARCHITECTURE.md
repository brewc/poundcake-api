# Architecture Documentation

## System Overview

The PoundCake API is a distributed system designed to receive, process, and store alerts from Prometheus Alertmanager in a scalable and fault-tolerant manner.

## Components

### 1. FastAPI Application (API Layer)

**Purpose**: HTTP API for receiving webhooks and serving queries

**Key Features**:
- Request ID middleware for all non-GET requests
- Automatic logging of all API calls to MariaDB
- Async request handling
- Health check endpoints for Kubernetes
- CORS support for cross-origin requests

**Endpoints**:
```
POST /api/v1/webhook     - Receive Alertmanager webhooks
GET  /api/v1/alerts    - List alerts with filtering
GET  /api/v1/alerts/{fp}   - Get specific alert
POST /api/v1/alerts/{fp}/retry - Retry failed alert
GET  /api/v1/tasks/{id}    - Get task status
GET  /api/v1/health    - Health check
GET  /api/v1/health/ready  - Readiness probe
GET  /api/v1/health/live   - Liveness probe
GET  /api/v1/stats     - Statistics
GET  /api/v1/stats/celery  - Celery stats
```

**Scaling**: Horizontal scaling via load balancer

**Resource Requirements**:
- CPU: 0.5-1 core per instance
- Memory: 512MB-1GB per instance
- Recommended: 2-4 instances for HA

### 2. MariaDB Database

**Purpose**: Long-term storage for alerts and API calls

**Tables**:

1. **api_calls** - All non-GET HTTP requests
 - Indexed on: request_id, created_at, method+path
 - Retention: Configurable (default 30 days)

2. **alerts** - Alertmanager alerts
 - Indexed on: fingerprint, status, processing_status, alert_name, severity, created_at
 - Retention: Configurable (default 30 days)
 - Cascade deletes with api_calls

3. **task_executions** - Celery task tracking
 - Indexed on: task_id, status, created_at
 - Retention: Configurable (default 30 days)

**Performance Tuning**:
```sql
-- Recommended indexes
CREATE INDEX CONCURRENTLY idx_alerts_composite 
ON alerts(status, processing_status, created_at DESC);

-- Partitioning for large datasets (optional)
CREATE TABLE alerts_2024_01 PARTITION OF alerts
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

**Scaling**: 
- Vertical: Increase CPU/memory for larger datasets
- Horizontal: Read replicas for queries
- Backup: Automated daily backups recommended

### 3. Redis

**Purpose**: 
- Celery message broker (DB 1)
- Celery result backend (DB 2)
- Application state cache (DB 0)

**Configuration**:
```
# redis.conf recommendations
maxmemory 2gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
```

**Scaling**:
- Single instance sufficient for most use cases
- Redis Sentinel for HA
- Redis Cluster for very high throughput

### 4. Celery Workers

**Purpose**: Asynchronous alert processing

**Tasks**:
1. `process_alert` - Process individual alert
2. `process_alert_batch` - Queue multiple alerts
3. `cleanup_old_data` - Periodic cleanup (optional)

**Configuration**:
```bash
# Worker settings
--concurrency=4      # Tasks per worker
--max-tasks-per-child=1000 # Prevent memory leaks
--loglevel=info      # Logging level
--time-limit=300     # 5 min task timeout
```

**Scaling**: 
- Add workers based on queue depth
- Monitor via Flower dashboard
- Typical: 1 worker per 100 alerts/minute

**Resource Requirements**:
- CPU: 1-2 cores per worker
- Memory: 256MB-512MB per worker
- Recommended: 2-4 workers minimum

### 5. Flower Dashboard

**Purpose**: Celery monitoring and management

**Features**:
- Real-time task monitoring
- Worker statistics
- Task history
- Rate limit controls

**Access**: http://localhost:5555

**Security**: Add basic auth in production

## Data Flow

### 1. Webhook Receipt
```

‚ 1. Alertmanager sends webhook         ‚
‚  POST /api/v1/webhook           ‚
¬
       ‚
       ¼

‚ 2. Request ID Middleware          ‚
‚  - Generate UUID            ‚
‚  - Store in api_calls table        ‚
‚  - Add X-Request-ID header         ‚
¬
       ‚
       ¼

‚ 3. Webhook Handler            ‚
‚  - Validate payload           ‚
‚  - Store alerts in database        ‚
‚  - Queue for processing          ‚
‚  - Return 202 Accepted immediately     ‚
¬
       ‚
       ¼

‚ 4. Response               ‚
‚  {                ‚
‚  "status": "accepted",          ‚
‚  "request_id": "uuid",          ‚
‚  "alerts_received": 5,          ‚
‚  "task_ids": ["task-uuid-1"]        ‚
‚  }                ‚

```

### 2. Alert Processing
```

‚ 1. Celery picks up batch task from queue     ‚
¬
       ‚
       ¼

‚ 2. process_alert_batch          ‚
‚  - Query alerts from database        ‚
‚  - Queue individual processing tasks     ‚
‚  - Update task_executions table      ‚
¬
       ‚
       ¼

‚ 3. process_alert (per alert)        ‚
‚  - Update status to "processing"       ‚
‚  - Execute business logic        ‚
‚  - Update status to "completed" or "failed"  ‚
‚  - Store results           ‚
¬
       ‚
       ¼

‚ 4. Task complete            ‚
‚  - Update task_executions        ‚
‚  - Send notifications (if configured)    ‚
‚  - Clean up temporary data         ‚

```

### 3. Request Lifecycle
```
Time  ‚ Event
¼
0ms ‚ Request received
1ms ‚ Request ID generated (UUID)
2ms ‚ API call logged to database (async)
5ms ‚ Webhook validated
10ms  ‚ Alerts stored in database
15ms  ‚ Batch task queued to Celery
20ms  ‚ Response sent (202 Accepted)
¼
100ms ‚ Worker picks up batch task
150ms ‚ Individual alert tasks queued
¼
200ms ‚ Alert 1 processing starts
500ms ‚ Alert 1 processing completes
¼
```

## Failure Handling

### 1. API Failures

**Scenario**: API server crashes during request
- **Impact**: Request may not be logged
- **Mitigation**: Alertmanager will retry
- **Recovery**: None needed (idempotent)

### 2. Database Failures

**Scenario**: MariaDB unavailable
- **Impact**: 
  - API calls fail with 500
  - Task execution fails
- **Mitigation**: 
  - API returns error immediately
  - Alertmanager retries
  - Connection pooling handles transient failures
- **Recovery**: Fix database, alerts will be retried

### 3. Redis Failures

**Scenario**: Redis unavailable
- **Impact**:
  - Task queue stops
  - Workers cannot pick up tasks
  - New alerts queued but not processed
- **Mitigation**:
  - Redis persistence (AOF)
  - High availability via Sentinel
- **Recovery**: 
  - Restart Redis
  - Workers reconnect automatically
  - Queued tasks resume

### 4. Worker Failures

**Scenario**: Worker crashes during task
- **Impact**: Task marked as failed
- **Mitigation**:
  - Automatic retry (3 attempts)
  - Exponential backoff
  - Task acknowledged only on success
- **Recovery**: 
  - Manual retry via API: `POST /api/v1/alerts/{fp}/retry`
  - Or wait for automatic retry

### 5. Task Timeouts

**Scenario**: Task exceeds time limit (5 min)
- **Impact**: Task terminated, marked as failed
- **Mitigation**: 
  - Configurable timeout
  - Soft timeout warning at 4:50
- **Recovery**: Manual retry or adjust timeout

## Security Considerations

### 1. Authentication

**Current**: None (internal service)

**Production Recommendations**:
- API Key authentication
- JWT tokens
- Mutual TLS
- IP allowlisting

```python
# Example: Add API key middleware
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
  if credentials.credentials != settings.api_key:
    raise HTTPException(status_code=403, detail="Invalid API key")
  return credentials
```

### 2. Data Privacy

**Sensitive Data**:
- Alert labels may contain hostnames, IPs
- Annotations may contain sensitive info

**Recommendations**:
- Encrypt database at rest
- Secure database connections (SSL/TLS)
- Rotate credentials regularly
- Implement data retention policies

### 3. Network Security

**Recommendations**:
- Deploy behind firewall
- Use private network for DB/Redis
- Enable TLS for all connections
- Restrict Flower access (basic auth)

### 4. Secrets Management

**Current**: Environment variables

**Production**:
- Kubernetes Secrets
- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault

## Monitoring & Observability

### 1. Metrics to Track

**API Metrics**:
- Request rate
- Response time (p50, p95, p99)
- Error rate
- Request ID uniqueness

**Database Metrics**:
- Connection pool usage
- Query duration
- Table sizes
- Index efficiency

**Celery Metrics**:
- Queue depth
- Task success/failure rate
- Worker utilization
- Task duration

**Business Metrics**:
- Alerts received per minute
- Alerts by severity
- Processing success rate
- Time to process

### 2. Logging

**Structured Logging** (JSON format):
```json
{
  "timestamp": "2024-01-09T10:00:00Z",
  "level": "INFO",
  "message": "Alert processing completed",
  "request_id": "uuid",
  "fingerprint": "abc123",
  "duration_ms": 450
}
```

**Log Aggregation**: 
- ELK Stack
- Splunk
- CloudWatch Logs
- Datadog

### 3. Alerting

**Critical Alerts**:
- API response time > 1s (p95)
- Error rate > 1%
- Database connection pool exhausted
- No active Celery workers
- Queue depth > 1000

**Warning Alerts**:
- Worker memory > 80%
- Database disk > 80%
- Task retry rate > 5%

## Performance Optimization

### 1. Database

```sql
-- Vacuum regularly
VACUUM ANALYZE alerts;

-- Monitor slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Optimize indexes
CREATE INDEX CONCURRENTLY idx_alerts_hot_path
ON alerts(processing_status, created_at)
WHERE processing_status IN ('pending', 'processing');
```

### 2. API

- Use connection pooling
- Enable HTTP/2
- Implement caching for read endpoints
- Add rate limiting

### 3. Celery

- Optimize task granularity
- Use task routing for priority
- Implement result expiration
- Monitor worker CPU/memory

### 4. Redis

- Use pipeline for bulk operations
- Set appropriate maxmemory
- Monitor memory fragmentation
- Use Redis Cluster for scale

## Disaster Recovery

### 1. Backup Strategy

**Database**:
```bash
# Daily backups
pg_dump -h localhost -U mariadb poundcake > backup_$(date +%Y%m%d).sql

# Continuous archiving (WAL)
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
```

**Redis**:
- AOF persistence enabled
- RDB snapshots every 5 minutes
- Backup to S3 daily

### 2. Recovery Procedures

**Database Recovery**:
```bash
# Restore from backup
psql -h localhost -U mariadb -d poundcake < backup_20240109.sql

# Point-in-time recovery (if WAL archiving enabled)
pg_restore -d poundcake -C backup.dump
```

**Redis Recovery**:
```bash
# Stop Redis
# Replace dump.rdb / appendonly.aof
# Start Redis
```

### 3. Testing

- Monthly DR drills
- Backup verification
- Failover testing
- Document runbooks

## Cost Optimization

### 1. Database

- Archive old data to cold storage
- Use partitioning for large tables
- Right-size instance (CPU/memory)
- Use read replicas judiciously

### 2. Compute

- Auto-scale workers based on queue
- Use spot/preemptible instances
- Right-size API instances
- Enable CPU throttling

### 3. Storage

- Set retention policies
- Compress backups
- Use tiered storage
- Monitor growth trends

## Future Enhancements

### 1. Short Term
- [ ] Prometheus metrics exporter
- [ ] Grafana dashboards
- [ ] Alert routing rules
- [ ] Notification integrations

### 2. Medium Term
- [ ] Multi-tenancy support
- [ ] Alert correlation
- [ ] ML-based anomaly detection
- [ ] API authentication

### 3. Long Term
- [ ] Event sourcing
- [ ] Real-time streaming
- [ ] GraphQL API
- [ ] Alert enrichment pipeline

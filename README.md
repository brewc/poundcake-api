# PoundCake API

**A lightweight tracking layer for Alertmanager webhooks with StackStorm integration**

**✨ Fully containerized setup - no host installation required!**

PoundCake API receives Prometheus Alertmanager webhooks, generates unique request IDs for complete audit trails, and triggers StackStorm workflows for automated remediation.

## Architecture

**Everything runs in Docker containers:**
- PoundCake (webhook tracking + Celery workers)
- StackStorm (complete workflow engine)
- Shared MariaDB database
- Redis (Celery broker)
- RabbitMQ (StackStorm message broker)

```
Alert → PoundCake (container) → Celery (container) → StackStorm (container) → Remediation
          ↓                                              ↓
      MariaDB (container - shared database)
```

## Features

### Fully Containerized
- ✅ **No host installation** - Everything in Docker
- ✅ **Easy cleanup** - Just `docker-compose down`
- ✅ **Portable** - Works on any system with Docker
- ✅ **13 containers** working together

### Request Tracking
- **Unique request_id** for every webhook
- **Complete audit trail** from alert to execution
- **Cross-system queries** with StackStorm

### Database (Simple!)
- **Only 3 tables:**
  - `poundcake_api_calls` - Request tracking
  - `poundcake_alerts` - Alert data  
  - `poundcake_st2_execution_link` - Link to ST2 executions

### StackStorm Integration (Containerized)
- 7 StackStorm services in containers
- Trigger ST2 workflows via API
- Pass `request_id` for tracking
- Store execution links
- Query complete history

### Async Processing
- Celery + Redis for background tasks
- Non-blocking webhook responses
- Reliable task execution
- Flower monitoring dashboard

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4 GB RAM minimum (8 GB recommended)

### One-Command Setup

```bash
# Extract
tar -xzf poundcake-api-v1.2.0-containers.tar.gz
cd poundcake-api

# Run quickstart (starts all 13 containers!)
chmod +x scripts/quickstart.sh
./scripts/quickstart.sh
```

**That's it!** Everything is running in containers:
- PoundCake API → http://localhost:8000
- Flower (Celery) → http://localhost:5555
- StackStorm API → http://localhost:9101
- RabbitMQ UI → http://localhost:15672

## API Endpoints

### POST `/api/v1/webhook`
Receive Alertmanager webhook

**Response:**
```json
{
  "status": "accepted",
  "request_id": "uuid",
  "alerts_received": 1
}
```

### GET `/api/v1/status/{request_id}`
Get complete status including ST2 executions

**Response:**
```json
{
  "request_id": "uuid",
  "received_at": "2026-01-14T12:00:00",
  "alerts": [...],
  "stackstorm_executions": [
    {
      "st2_execution_id": "5f9e8a7b...",
      "st2_workflow": "remediation.host_down_workflow"
    }
  ]
}
```

### GET `/api/v1/executions/recent`
List recent webhook requests

### GET `/api/v1/alerts/active`
List currently firing alerts

### GET `/api/v1/st2/executions`
List all ST2 executions triggered by PoundCake

### GET `/api/v1/health`
Health check endpoint

## Database Schema

### poundcake_api_calls
Tracks all webhook requests with unique request_id
```sql
id, request_id (unique), method, path, headers, body,
status_code, created_at, completed_at
```

### poundcake_alerts
Stores Alertmanager alert data
```sql
id, api_call_id, fingerprint, alert_name, severity,
instance, labels, annotations, st2_rule_matched, created_at
```

### poundcake_st2_execution_link
Links PoundCake requests to StackStorm executions
```sql
id, request_id, alert_id, st2_execution_id,
st2_rule_ref, st2_action_ref, created_at
```

## Query Examples

### Get Complete Audit Trail

```sql
SELECT 
    api.request_id,
    alert.alert_name,
    alert.severity,
    link.st2_execution_id,
    exec.action as st2_workflow,
    exec.status
FROM poundcake_api_calls api
JOIN poundcake_alerts alert ON alert.api_call_id = api.id
LEFT JOIN poundcake_st2_execution_link link ON link.alert_id = alert.id
LEFT JOIN execution_db exec ON exec.id = link.st2_execution_id
WHERE api.request_id = 'your-request-id';
```

### Get Workflow Success Rates

```sql
SELECT 
    exec.action as workflow,
    COUNT(*) as total,
    SUM(CASE WHEN exec.status = 'succeeded' THEN 1 ELSE 0 END) as succeeded,
    ROUND(AVG(TIMESTAMPDIFF(SECOND, exec.start_timestamp, exec.end_timestamp)), 2) as avg_duration_sec
FROM execution_db exec
JOIN poundcake_st2_execution_link link ON exec.id = link.st2_execution_id
GROUP BY exec.action;
```

## Stack Components

### PoundCake Services
- **api** - FastAPI application (webhook receiver)
- **celery** - Background task processing
- **redis** - Celery broker and result backend
- **mariadb** - Database (can be shared with ST2)
- **flower** - Celery monitoring UI (optional)

### StackStorm Services (Separate)
- **st2api** - StackStorm REST API
- **st2actionrunner** - Action execution
- **st2stream** - Event streaming
- **st2rulesengine** - Rule evaluation
- **rabbitmq** - ST2 message queue (NOT shared with PoundCake)
- **mariadb** - Database (can be shared with PoundCake)

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=mysql+pymysql://poundcake:poundcake@localhost:3306/poundcake

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# StackStorm
ST2_API_URL=http://localhost:9101/v1
ST2_API_KEY=your-api-key-here

# App
LOG_LEVEL=INFO
```

### Celery Task

The single Celery task (`process_alert`) handles:
1. Get alert from database
2. Determine which ST2 workflow to trigger
3. Call ST2 API with alert data + request_id
4. Store execution link

## Monitoring

### Celery (Flower)
```bash
# Access Flower UI
open http://localhost:5555
```

### StackStorm
```bash
# ST2 CLI
st2 execution list
st2 execution get <execution-id>

# ST2 Web UI
open https://your-server-ip
```

### Database
```bash
# Recent executions
mysql -upoundcake -ppoundcake poundcake -e "
SELECT COUNT(*) as total, st2_action_ref
FROM poundcake_st2_execution_link
GROUP BY st2_action_ref;
"
```

## Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Complete architecture guide
- **[STACKSTORM_INTEGRATION.md](docs/STACKSTORM_INTEGRATION.md)** - ST2 integration details
- **[STACKSTORM_MARIADB_INSTALL.md](docs/STACKSTORM_MARIADB_INSTALL.md)** - ST2 installation
- **[MIGRATION_COMPLEX_TO_SIMPLE.md](docs/MIGRATION_COMPLEX_TO_SIMPLE.md)** - Migration from old versions
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues
- **[SAMPLE_PAYLOADS.md](docs/SAMPLE_PAYLOADS.md)** - Example webhooks

## Benefits

### Simplicity
- Only 3 database tables
- Clear separation of concerns
- Easy to understand and maintain

### Power
- Full StackStorm capabilities
- ActionChains, Mistral, Orquesta workflows
- 100+ community packs from ST2 Pack Exchange
- ST2 Web UI for workflow management

### Complete Audit Trail
- Unique request_id for every webhook
- Track from alert → workflow → execution → result
- Cross-system queries via simple link table

### Scalability
- Celery workers scale independently
- ST2 action runners scale independently
- Database can be shared or separate

## Why This Architecture?

PoundCake is intentionally a **thin layer** that does ONE thing well: tracking webhooks with request_id.

We don't duplicate StackStorm's workflow engine. Instead:
- **PoundCake:** Webhook tracking and request_id generation
- **StackStorm:** ALL workflow and action execution

This keeps PoundCake simple while leveraging ST2's full power.

## Requirements

- Docker 20.10+
- Docker Compose 2.0+
- StackStorm 3.8+ with MariaDB backend
- 2 GB RAM minimum

## License

MIT

## Support

- GitHub: https://github.com/brewc/poundcake-api
- Documentation: See `docs/` directory
- Issues: GitHub Issues

## Summary

**PoundCake = Thin tracking layer with request_id**  
**StackStorm = Workflow engine**

Simple, powerful, and maintainable.

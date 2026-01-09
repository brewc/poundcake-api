# PoundCake API

A production-ready FastAPI application for processing Prometheus Alertmanager webhooks with Celery task queue, request ID tracking, and PostgreSQL storage.

## Features

-  **FastAPI** - Modern, fast Python web framework
-  **Celery** - Distributed task queue for async alert processing
-  **PostgreSQL** - Reliable SQL database via SQLAlchemy
-  **Redis** - Backend for Celery tasks and state management
-  **Request ID Tracking** - Automatic request ID generation for all non-GET requests
-  **Database Logging** - All non-GET API calls stored in PostgreSQL
-  **Health Checks** - Kubernetes-ready liveness and readiness probes
-  **Docker Support** - Full Docker Compose setup included
-  **Monitoring** - Flower dashboard for Celery tasks

## Architecture

```
    
‚ Prometheus  ‚¶‚  Alertmanager ‚¶‚ FastAPI API ‚
‚ (Monitoring)  ‚   ‚ (Alerting)  ‚   ‚  (Webhook)  ‚
    ¬
                    ‚
                    ‚ Store & Queue
                    ¼
           
        ‚ PostgreSQL  ‚—‚ Middleware  ‚
        ‚ (Storage)   ‚   ‚  (Request IDs)  ‚
           
                    ‚
              ‚
        ‚   Redis   ‚—
        ‚  (Task Queue) ‚      ‚
        ¬      ‚
           ‚        ‚
           ¼        ¼
           
        ‚ Celery Workers  ‚¶‚ Alert Processing‚
        ‚  (Processing) ‚   ‚   Logic   ‚
           
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
# Clone or create the project
cd poundcake-api

# Copy environment file
cp .env.example .env

# Edit .env with your configuration (optional for local dev)
```

### 2. Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
curl http://localhost:8000/api/v1/health
```

Services will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower Dashboard**: http://localhost:5555
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 3. Send a Test Webhook

```bash
curl -X POST http://localhost:8000/api/v1/webhook \
  -H "Content-Type: application/json" \
  -d '{
  "version": "4",
  "groupKey": "{}:{alertname=\"TestAlert\"}",
  "truncatedAlerts": 0,
  "status": "firing",
  "receiver": "webhook",
  "groupLabels": {
  "alertname": "TestAlert"
  },
  "commonLabels": {
  "alertname": "TestAlert",
  "severity": "warning"
  },
  "commonAnnotations": {},
  "externalURL": "http://poundcake:9093",
  "alerts": [
  {
    "status": "firing",
    "labels": {
    "alertname": "TestAlert",
    "severity": "warning",
    "instance": "localhost:9090"
    },
    "annotations": {
    "summary": "Test alert",
    "description": "This is a test alert"
    },
    "startsAt": "2024-01-09T10:00:00Z",
    "endsAt": "0001-01-01T00:00:00Z",
    "generatorURL": "http://prometheus:9090/graph",
    "fingerprint": "abc123def456"
  }
  ]
  }'
```

Response:
```json
{
  "status": "accepted",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "alerts_received": 1,
  "task_ids": ["task-uuid-here"],
  "message": "Successfully received and queued 1 alerts"
}
```

## API Endpoints

### Webhook Endpoint

**POST /api/v1/webhook** - Receive Alertmanager webhooks
- Stores alerts in PostgreSQL
- Queues processing via Celery
- Returns 202 Accepted immediately
- Includes X-Request-ID header

### Alert Management

**GET /api/v1/alerts** - List all alerts
- Query params: `status`, `processing_status`, `alert_name`, `severity`, `limit`, `offset`

**GET /api/v1/alerts/{fingerprint}** - Get specific alert

**POST /api/v1/alerts/{fingerprint}/retry** - Retry failed alert processing

### Task Status

**GET /api/v1/tasks/{task_id}** - Get Celery task status

### Health & Stats

**GET /api/v1/health** - Health check (database, Redis, Celery)

**GET /api/v1/health/ready** - Readiness probe (Kubernetes)

**GET /api/v1/health/live** - Liveness probe (Kubernetes)

**GET /api/v1/stats** - System statistics

**GET /api/v1/stats/celery** - Celery worker statistics

## Request ID Tracking

All non-GET requests automatically:
1. Generate a unique request ID (UUID)
2. Add `X-Request-ID` header to response
3. Store request details in `api_calls` table
4. Track processing time

Example response headers:
```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Processing-Time-Ms: 45
```

## Database Schema

### api_calls Table
Stores all non-GET API calls:
- `request_id` - Unique request identifier
- `method`, `path` - HTTP method and path
- `headers`, `query_params`, `body` - Request data
- `status_code`, `response_body` - Response data
- `processing_time_ms` - Request duration
- `created_at`, `completed_at` - Timestamps

### alerts Table
Stores Alertmanager alerts:
- `fingerprint` - Unique alert identifier
- `status` - firing/resolved
- `alert_name`, `severity`, `instance` - Alert metadata
- `labels`, `annotations` - Alert data
- `processing_status` - pending/processing/completed/failed
- `task_id` - Associated Celery task
- `api_call_id` - Foreign key to api_calls

### task_executions Table
Tracks Celery task executions:
- `task_id` - Celery task ID
- `task_name` - Task function name
- `status` - Task status
- `result`, `error`, `traceback` - Execution results
- Timestamps for lifecycle tracking

## Configuration

Configuration via environment variables (see `.env.example`):

### Application
- `APP_NAME` - Application name
- `DEBUG` - Debug mode (true/false)

### API
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)
- `API_WORKERS` - Number of Uvicorn workers

### Database
- `DATABASE_URL` - PostgreSQL connection string
- `DATABASE_ECHO` - Log SQL queries (true/false)

### Redis & Celery
- `REDIS_URL` - Redis connection for app state
- `CELERY_BROKER_URL` - Redis DB for Celery broker
- `CELERY_RESULT_BACKEND` - Redis DB for Celery results
- `CELERY_TASK_TIME_LIMIT` - Task timeout (seconds)
- `CELERY_WORKER_PREFETCH_MULTIPLIER` - Worker prefetch
- `CELERY_WORKER_MAX_TASKS_PER_CHILD` - Max tasks per worker

### Logging
- `LOG_LEVEL` - INFO, DEBUG, WARNING, ERROR
- `LOG_FORMAT` - json or console

## Local Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Upgrade pip and install build tools
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -e ".[dev]"

# Start PostgreSQL and Redis (via Docker)
docker-compose up -d postgres redis

# Set environment variables
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/poundcake
export REDIS_URL=redis://localhost:6379/0
export CELERY_BROKER_URL=redis://localhost:6379/1
export CELERY_RESULT_BACKEND=redis://localhost:6379/2
export DEBUG=true
export LOG_FORMAT=console

# Run database migrations (create tables)
python -c "from app.core.database import init_db; init_db()"

# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A app.tasks.celery_app:celery_app worker --loglevel=info

# Optional: Start Flower
celery -A app.tasks.celery_app:celery_app flower
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Monitoring

### Flower Dashboard

Access at http://localhost:5555

Features:
- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Task rate limiting controls

### Logs

All services log in JSON format (when `LOG_FORMAT=json`):

```bash
# View API logs
docker-compose logs -f api

# View worker logs
docker-compose logs -f worker

# View all logs
docker-compose logs -f
```

### Metrics

Health endpoint provides system status:

```bash
curl http://localhost:8000/api/v1/health
```

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "healthy",
  "redis": "healthy",
  "celery": "healthy (2 workers)",
  "timestamp": "2024-01-09T10:00:00Z"
}
```

## Production Deployment

### Kubernetes

```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: poundcake-api-api
spec:
  replicas: 3
  selector:
  matchLabels:
  app: poundcake-api-api
  template:
  metadata:
  labels:
    app: poundcake-api-api
  spec:
  containers:
  - name: api
    image: poundcake-api:latest
    ports:
    - containerPort: 8000
    env:
    - name: DATABASE_URL
    valueFrom:
    secretKeyRef:
      name: app-secrets
      key: database-url
    livenessProbe:
    httpGet:
    path: /api/v1/health/live
    port: 8000
    initialDelaySeconds: 30
    periodSeconds: 10
    readinessProbe:
    httpGet:
    path: /api/v1/health/ready
    port: 8000
    initialDelaySeconds: 5
    periodSeconds: 5
```

### Scaling

Scale workers based on load:

```bash
# Docker Compose
docker-compose up -d --scale worker=5

# Kubernetes
kubectl scale deployment poundcake-api-worker --replicas=5
```

## Alertmanager Configuration

Configure Alertmanager to send webhooks:

```yaml
# poundcake.yml
receivers:
  - name: 'webhook'
  webhook_configs:
  - url: 'http://poundcake-api:8000/api/v1/webhook'
    send_resolved: true

route:
  receiver: 'webhook'
  routes:
  - match:
    severity: critical
  receiver: 'webhook'
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U postgres -d poundcake -c "SELECT 1"

# View database logs
docker-compose logs postgres
```

### Celery Worker Issues

```bash
# Check worker status
docker-compose ps worker

# View worker logs
docker-compose logs -f worker

# Restart workers
docker-compose restart worker

# Inspect active tasks
docker-compose exec worker celery -A app.tasks.celery_app:celery_app inspect active
```

### Redis Issues

```bash
# Check Redis is running
docker-compose exec redis redis-cli ping

# View keys
docker-compose exec redis redis-cli keys '*'

# Monitor Redis
docker-compose exec redis redis-cli monitor
```

## Project Structure

```
poundcake-api/
 src/
‚  app/
‚    api/
‚   ‚  routes.py    # Main API routes
‚   ‚  health.py    # Health check endpoints
‚    core/
‚   ‚  config.py    # Configuration
‚   ‚  database.py    # Database setup
‚   ‚  logging.py   # Logging configuration
‚   ‚  middleware.py  # Request ID middleware
‚    models/
‚   ‚  models.py    # SQLAlchemy models
‚    schemas/
‚   ‚  schemas.py   # Pydantic schemas
‚    tasks/
‚   ‚  celery_app.py  # Celery configuration
‚   ‚  alert_tasks.py   # Celery tasks
‚    main.py      # FastAPI application
 tests/
‚  ...        # Test files
 .env.example       # Environment template
 docker-compose.yml     # Docker Compose config
 Dockerfile       # Docker image
 pyproject.toml       # Project metadata
 README.md        # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

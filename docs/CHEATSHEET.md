# Quick Command Cheatsheet

## Fresh Ubuntu VM  Running PoundCake API (5 minutes)

Copy and paste these commands one section at a time:

### Step 1: Install Docker (2 minutes)
```bash
# Download and run Docker installer
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add yourself to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify (should show version)
docker --version
```

### Step 2: Extract PoundCake API (30 seconds)
```bash
# Extract the archive
tar -xzf poundcake-api.tar.gz
cd poundcake-api

# Make quickstart executable
chmod +x quickstart.sh
```

### Step 3: Start Everything (1 minute)
```bash
# Run the quickstart script
./quickstart.sh

# Wait 30 seconds for services to initialize
sleep 30
```

### Step 4: Verify It's Working (10 seconds)
```bash
# Check health
curl http://localhost:8000/api/v1/health

# Should return:
# {"status":"healthy","version":"0.1.0",...}
```

Done!

Access the services:
- **API**: http://YOUR_VM_IP:8000
- **Docs**: http://YOUR_VM_IP:8000/docs
- **Flower**: http://YOUR_VM_IP:5555

---

## Essential Commands

### Managing Services
```bash
# View running containers
docker ps

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f api

# Restart everything
docker-compose restart

# Stop everything
docker-compose down

# Start again
docker-compose up -d

# Fresh start (removes all data)
docker-compose down -v
docker-compose up -d
```

### Testing the API
```bash
# Health check
curl http://localhost:8000/api/v1/health

# List alerts
curl http://localhost:8000/api/v1/alerts

# Get statistics
curl http://localhost:8000/api/v1/stats

# Send test alert
curl -X POST http://localhost:8000/api/v1/webhook \
  -H "Content-Type: application/json" \
  -d '{
  "version": "4",
  "status": "firing",
  "alerts": [{
  "status": "firing",
  "labels": {"alertname": "TestAlert", "severity": "warning"},
  "startsAt": "2024-01-09T10:00:00Z",
  "fingerprint": "test123"
  }]
  }'
```

### Database Access
```bash
# Connect to MariaDB
docker-compose exec mariadb psql -U mariadb -d poundcake

# Query alerts
docker-compose exec mariadb psql -U mariadb -d poundcake -c \
  "SELECT fingerprint, alert_name, status, processing_status FROM alerts LIMIT 10;"

# Query API calls
docker-compose exec mariadb psql -U mariadb -d poundcake -c \
  "SELECT request_id, method, path, status_code FROM api_calls LIMIT 10;"
```

### Troubleshooting
```bash
# Check if Docker is running
sudo systemctl status docker

# Check container status
docker ps -a

# Check resource usage
docker stats

# View container logs
docker-compose logs api
docker-compose logs worker
docker-compose logs postgres

# Restart Docker service
sudo systemctl restart docker

# Check ports in use
sudo lsof -i :8000
sudo lsof -i :5432
sudo lsof -i :6379
```

---

## Common Issues

### "Cannot connect to Docker daemon"
```bash
sudo systemctl start docker
```

### "Permission denied"
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### "Port already in use"
```bash
# Find what's using the port
sudo lsof -i :8000

# Kill it or change port in docker-compose.yml
```

### Services won't start
```bash
# Check logs
docker-compose logs

# Fresh restart
docker-compose down -v
docker-compose up -d
```

---

## Opening Firewall Ports

### Ubuntu (UFW)
```bash
sudo ufw allow 8000/tcp
sudo ufw allow 5555/tcp
sudo ufw status
```

### CentOS/RHEL (firewalld)
```bash
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=5555/tcp
sudo firewall-cmd --reload
```

### Cloud VMs (AWS/GCP/Azure)
Open ports in security group:
- **8000** - API
- **5555** - Flower

---

## Quick Monitoring

### Check Everything is Healthy
```bash
# One-liner status check
curl -s http://localhost:8000/api/v1/health | jq '.'
```

### Monitor Logs in Real-Time
```bash
# All services
docker-compose logs -f

# Just API
docker-compose logs -f api

# Just workers
docker-compose logs -f worker
```

### Check Database
```bash
# Row counts
docker-compose exec mariadb psql -U mariadb -d poundcake -c "
  SELECT 'api_calls' as table_name, COUNT(*) as count FROM api_calls
  UNION ALL
  SELECT 'alerts', COUNT(*) FROM alerts
  UNION ALL
  SELECT 'task_executions', COUNT(*) FROM task_executions;
"
```

### Check Celery Workers
```bash
# Worker status (via Flower web interface)
open http://localhost:5555

# Or via command line
docker-compose exec worker celery -A app.tasks.celery_app:celery_app inspect active
```

---

## Production Checklist

Before going to production:

```bash
# 1. Update passwords in .env
nano .env  # Change POSTGRES_PASSWORD, etc.

# 2. Restart with new config
docker-compose down
docker-compose up -d

# 3. Verify health
curl http://localhost:8000/api/v1/health

# 4. Set up backups (example)
# Backup script: backup.sh
docker-compose exec mariadb pg_dump -U mariadb poundcake > backup_$(date +%Y%m%d).sql

# 5. Monitor logs
docker-compose logs -f
```

---

## Backup and Restore

### Backup Database
```bash
# Create backup
docker-compose exec mariadb pg_dump -U mariadb poundcake > backup.sql

# Or with timestamp
docker-compose exec mariadb pg_dump -U mariadb poundcake > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database
```bash
# Restore from backup
docker-compose exec -T mariadb psql -U mariadb poundcake < backup.sql
```

### Backup Everything (Docker volumes)
```bash
# Stop containers
docker-compose down

# Backup volume data
sudo tar -czf poundcake-volumes-backup.tar.gz /var/lib/docker/volumes/poundcake*

# Start containers
docker-compose up -d
```

---

## Update/Upgrade

### Update PoundCake API
```bash
# Stop services
docker-compose down

# Extract new version
tar -xzf poundcake-api-new.tar.gz
cd poundcake-api

# Start with new version
docker-compose up -d --build

# Verify
curl http://localhost:8000/api/v1/health
```

### Update Docker
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install --only-upgrade docker-ce docker-ce-cli containerd.io docker-compose-plugin

# CentOS/RHEL
sudo yum update docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

---

## Get Help

### View Full Documentation
```bash
# Main README
cat README.md | less

# Docker installation guide
cat DOCKER_INSTALL.md | less

# Quick reference
cat QUICK_REFERENCE.md | less

# Architecture details
cat docs/ARCHITECTURE.md | less
```

### Test Everything
```bash
# Run health checks
make health  # If you have make installed

# Or manually
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/stats
docker ps
docker-compose logs --tail=50
```

---

**That's it! You're all set! **

For more detailed information, see:
- `DOCKER_INSTALL.md` - Full Docker installation guide
- `README.md` - Complete documentation
- `QUICK_REFERENCE.md` - Detailed command reference

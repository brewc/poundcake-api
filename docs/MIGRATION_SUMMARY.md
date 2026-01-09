# Migration Summary - PostgreSQL to MariaDB

## Changes Completed

### 1. Database Migration: PostgreSQL to MariaDB

**Python Dependencies:**
- Removed: `psycopg2-binary>=2.9.9`
- Added: `pymysql>=1.1.0` and `cryptography>=41.0.0`

**Connection String Format:**
- Old: `postgresql://postgres:postgres@localhost:5432/poundcake`
- New: `mysql+pymysql://poundcake:poundcake@localhost:3306/poundcake`

**Docker Service:**
- Old: PostgreSQL 15 Alpine on port 5432
- New: MariaDB 11 on port 3306

**Files Updated:**
1. `pyproject.toml` - Updated dependencies
2. `src/app/core/config.py` - Updated default DATABASE_URL
3. `.env.example` - Updated connection string
4. `docker-compose.yml` - Replaced postgres service with mariadb service
5. `Dockerfile` - Replaced postgresql-client with default-libmysqlclient-dev
6. `README.md` - Updated all PostgreSQL references to MariaDB
7. All documentation files in `docs/` folder

**Database Configuration:**
```yaml
mariadb:
  image: mariadb:11
  environment:
    MYSQL_ROOT_PASSWORD: rootpass
    MYSQL_DATABASE: poundcake
    MYSQL_USER: poundcake
    MYSQL_PASSWORD: poundcake
  ports:
    - "3306:3306"
```

**Character Set:**
- MariaDB configured with UTF-8MB4 (utf8mb4_unicode_ci)
- Supports full Unicode including emojis

### 2. Documentation Reorganization

**All documentation moved to docs/ folder:**

Moved from root to docs/:
- CHEATSHEET.md
- CLEAN_VERSION.md
- DOCKER_INSTALL.md
- EXTRACTION_GUIDE.md
- INSTALL.md
- PYPROJECT_FIX.md
- QUICK_REFERENCE.md
- RENAME_SUMMARY.md
- TARBALL_FIX.md
- TODO_NEXT_SESSION.md

Kept in root:
- README.md (standard practice)

**README.md Updates:**
- Added Documentation section with links to all docs
- Updated all database references
- Updated services list

**New Project Structure:**
```
poundcake-api/
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CHEATSHEET.md
│   ├── INSTALL.md
│   ├── DOCKER_INSTALL.md
│   ├── QUICK_REFERENCE.md
│   └── ... (all other docs)
└── src/
    └── app/
        └── ...
```

## SQLAlchemy Compatibility

SQLAlchemy abstracts most database differences. The following work identically:
- Table definitions
- Queries with ORM
- Transactions
- Indexes
- Foreign keys

**No code changes required in:**
- Models (src/app/models/models.py)
- Database operations (src/app/core/database.py)
- API routes
- Celery tasks

## Installation Instructions

### Using Docker (Recommended)

```bash
cd poundcake-api
./quickstart.sh
```

Docker will automatically:
- Build image with pymysql
- Start MariaDB service
- Initialize database
- Start all services

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install build tools
pip install --upgrade pip setuptools wheel

# Install application
pip install -e ".[dev]"

# Start services
docker-compose up -d mariadb redis

# Set environment
export DATABASE_URL=mysql+pymysql://poundcake:poundcake@localhost:3306/poundcake
export REDIS_URL=redis://localhost:6379/0
export CELERY_BROKER_URL=redis://redis:6379/1
export CELERY_RESULT_BACKEND=redis://redis:6379/2

# Initialize database
python -c "from app.core.database import init_db; init_db()"

# Start API
uvicorn app.main:app --reload
```

## Testing the Migration

### 1. Verify Services Start

```bash
docker-compose up -d
docker-compose ps
```

Should show:
- mariadb (healthy)
- redis (healthy)
- api (running)
- worker (2 instances)
- flower (running)

### 2. Test Database Connection

```bash
# Check health
curl http://localhost:8000/api/v1/health

# Should return:
# {
#   "status": "healthy",
#   "database": "healthy",
#   ...
# }
```

### 3. Test API Operations

```bash
# Send test webhook
curl -X POST http://localhost:8000/api/v1/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "version": "4",
    "status": "firing",
    "alerts": [{
      "status": "firing",
      "labels": {"alertname": "TestAlert"},
      "startsAt": "2024-01-09T10:00:00Z",
      "fingerprint": "test123"
    }]
  }'

# Check database
docker-compose exec mariadb mariadb -upoundcake -ppoundcake poundcake -e "SELECT COUNT(*) FROM alerts;"
```

### 4. Verify Documentation

```bash
# Check documentation structure
ls -la docs/

# Should show all .md files in docs/ folder
```

## Differences Between PostgreSQL and MariaDB

### Advantages of MariaDB:
1. **Performance** - Generally faster for read-heavy workloads
2. **Storage Engine** - InnoDB with better optimization
3. **Compatibility** - MySQL ecosystem compatibility
4. **Licensing** - More permissive GPL license
5. **JSON Support** - Full JSON column type support

### Considerations:
1. **Data Types** - Minor differences in some types (SQLAlchemy handles this)
2. **Sequences** - MariaDB uses AUTO_INCREMENT instead of SERIAL
3. **Arrays** - No native array type (use JSON instead)
4. **Full Text Search** - Different syntax but available

### Not Affected:
- Application logic
- API endpoints
- Celery tasks
- Request ID tracking
- All core functionality

## MariaDB-Specific Configuration

The docker-compose.yml includes MariaDB optimizations:

```yaml
command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```

This ensures:
- Full UTF-8 support including emojis
- Proper string comparison
- International character support

## Troubleshooting

### Issue: Connection refused to MariaDB

```bash
# Check MariaDB is running
docker-compose ps mariadb

# View logs
docker-compose logs mariadb

# Restart service
docker-compose restart mariadb
```

### Issue: Authentication error

Default credentials:
- Username: `poundcake`
- Password: `poundcake`
- Database: `poundcake`

### Issue: Character encoding problems

MariaDB is configured with utf8mb4. To verify:

```bash
docker-compose exec mariadb mariadb -upoundcake -ppoundcake -e "SHOW VARIABLES LIKE 'char%';"
```

## Rollback Procedure

If you need to revert to PostgreSQL:

1. Replace `pymysql` with `psycopg2-binary` in pyproject.toml
2. Change DATABASE_URL back to postgresql://
3. Replace mariadb service with postgres in docker-compose.yml
4. Rebuild: `docker-compose down -v && docker-compose up -d --build`

## Summary

All TODO items completed:
- PostgreSQL to MariaDB migration
- Documentation moved to docs/ folder
- All references updated
- Project structure cleaned up

**Status: Ready for deployment**

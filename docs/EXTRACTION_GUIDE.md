# Extraction Verification Guide

## Correct Directory Structure

After extracting `poundcake-api.tar.gz`, you should see this structure:

```
poundcake-api/
 .env.example
 .gitignore
 CHEATSHEET.md
 DOCKER_INSTALL.md
 Dockerfile
 Makefile
 QUICK_REFERENCE.md
 README.md
 RENAME_SUMMARY.md
 config/
‚  alertmanager.example.yml
 docker-compose.yml
 docs/
‚  ARCHITECTURE.md
 pyproject.toml
 quickstart.sh
 src/
‚  app/
‚    __init__.py
‚    main.py
‚    api/
‚   ‚  __init__.py
‚   ‚  health.py
‚   ‚  routes.py
‚    core/
‚   ‚  __init__.py
‚   ‚  config.py
‚   ‚  database.py
‚   ‚  logging.py
‚   ‚  middleware.py
‚    models/
‚   ‚  __init__.py
‚   ‚  models.py
‚    schemas/
‚   ‚  __init__.py
‚   ‚  schemas.py
‚    tasks/
‚    __init__.py
‚    alert_tasks.py
‚    celery_app.py
 tests/
   __init__.py
   test_api.py
```

## Quick Verification

After extraction, run these commands to verify:

```bash
# 1. List top-level directories
ls -la poundcake-api/

# You should see exactly these directories:
# config/  docs/  src/  tests/

# 2. Check src structure
ls -la poundcake-api/src/app/

# You should see:
# api/  core/  models/  schemas/  tasks/  __init__.py  main.py

# 3. Count Python files
find poundcake-api/ -name "*.py" | wc -l

# Should be: 16 Python files

# 4. Verify key files exist
ls -1 poundcake-api/*.sh poundcake-api/*.yml poundcake-api/*.md | wc -l

# Should be: 8 files
```

## Common Issues and Fixes

### Issue 1: Malformed directories (like `{src`)

**Symptom**: You see directories with strange names like `{src`

**Cause**: Corrupted or improperly created tarball

**Fix**: 
```bash
# Delete the extracted directory
rm -rf poundcake-api/

# Re-extract with verbose output
tar -xzvf poundcake-api.tar.gz

# If you still see issues, the tarball may be corrupted
# Re-download it or request a new one
```

### Issue 2: Permission denied errors

**Symptom**: Cannot access files after extraction

**Fix**:
```bash
# Change ownership to your user
sudo chown -R $USER:$USER poundcake-api/

# Make quickstart.sh executable
chmod +x poundcake-api/quickstart.sh
```

### Issue 3: Missing files

**Symptom**: Python files or directories are missing

**Verification**:
```bash
# Check tarball contents before extracting
tar -tzf poundcake-api.tar.gz | head -50

# Should show poundcake-api/ followed by all files
```

## Correct Extraction Steps

```bash
# 1. Verify tarball exists and size is reasonable
ls -lh poundcake-api.tar.gz
# Should be around 15-20 KB

# 2. Extract
tar -xzf poundcake-api.tar.gz

# 3. Verify extraction
ls -la poundcake-api/

# 4. Check key files
test -f poundcake-api/quickstart.sh && echo " quickstart.sh found"
test -f poundcake-api/docker-compose.yml && echo " docker-compose.yml found"
test -f poundcake-api/src/app/main.py && echo " main.py found"
test -d poundcake-api/src/app/api && echo " api directory found"

# 5. Make quickstart executable
chmod +x poundcake-api/quickstart.sh

# 6. You're ready to run!
cd poundcake-api
./quickstart.sh
```

## Tarball Integrity Check

To verify the tarball is not corrupted:

```bash
# Test tarball integrity
tar -tzf poundcake-api.tar.gz > /dev/null && echo " Tarball is valid"

# List contents
tar -tzf poundcake-api.tar.gz | head -20

# Should show:
# poundcake-api/
# poundcake-api/.env.example
# poundcake-api/.gitignore
# poundcake-api/CHEATSHEET.md
# ... etc
```

## Alternative Extraction Methods

### Using GNU tar (Linux)
```bash
tar -xzf poundcake-api.tar.gz
```

### Using BSD tar (macOS)
```bash
tar -xzf poundcake-api.tar.gz
```

### Using 7-Zip (Windows with WSL)
```bash
7z x poundcake-api.tar.gz
7z x poundcake-api.tar
```

### Extract to specific directory
```bash
mkdir -p /opt/poundcake
tar -xzf poundcake-api.tar.gz -C /opt/poundcake --strip-components=1
```

## File Count Reference

After extraction, these counts should match:

| Type | Count |
|------|-------|
| Python files (*.py) | 16 |
| Markdown files (*.md) | 6 |
| YAML files (*.yml) | 2 |
| Shell scripts (*.sh) | 1 |
| Directories (top-level) | 4 (config, docs, src, tests) |

Verify with:
```bash
cd poundcake-api
find . -name "*.py" | wc -l  # Should be 16
find . -name "*.md" | wc -l  # Should be 6
find . -name "*.yml" | wc -l # Should be 2
find . -name "*.sh" | wc -l  # Should be 1
ls -d */ | wc -l     # Should be 4
```

## Checksum Verification (Optional)

If you want to verify file integrity:

```bash
# After extraction, generate checksums
cd poundcake-api
find . -type f -exec sha256sum {} \; > checksums.txt

# Save for future verification
```

## Still Having Issues?

If you continue to see malformed directories or missing files:

1. **Verify tarball download**: Re-download the tarball
2. **Check disk space**: Ensure you have at least 1GB free
3. **Check tar version**: `tar --version`
4. **Try different extraction**: `gunzip -c poundcake-api.tar.gz | tar -xf -`
5. **Extract with verbose**: `tar -xzvf poundcake-api.tar.gz` to see what's being extracted

## Quick Sanity Check Script

Save this as `verify.sh`:

```bash
#!/bin/bash
echo "Verifying PoundCake API structure..."

ERRORS=0

# Check directories
for dir in config docs src tests src/app src/app/api src/app/core src/app/models src/app/schemas src/app/tasks; do
  if [ ! -d "$dir" ]; then
    echo "— Missing directory: $dir"
    ERRORS=$((ERRORS + 1))
  else
    echo " Found: $dir"
  fi
done

# Check key files
for file in quickstart.sh docker-compose.yml pyproject.toml src/app/main.py; do
  if [ ! -f "$file" ]; then
    echo "— Missing file: $file"
    ERRORS=$((ERRORS + 1))
  else
    echo " Found: $file"
  fi
done

if [ $ERRORS -eq 0 ]; then
  echo ""
  echo " All checks passed! Structure is correct."
  echo "Run ./quickstart.sh to start the application."
else
  echo ""
  echo " Found $ERRORS errors. Please re-extract the tarball."
fi
```

Run it:
```bash
cd poundcake-api
chmod +x verify.sh
./verify.sh
```

---

**The tarball has been fixed and should now extract cleanly!** 

If you still encounter issues, please verify:
- Your tar command is working: `tar --version`
- You have write permissions in the directory
- There's sufficient disk space: `df -h`

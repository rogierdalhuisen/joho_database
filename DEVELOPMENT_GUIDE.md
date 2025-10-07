# Development Guide: Docker & Django Workflow

## Table of Contents
1. [When to Build vs When to Restart](#when-to-build-vs-when-to-restart)
2. [Common Commands Cheatsheet](#common-commands-cheatsheet)
3. [Detailed Workflows](#detailed-workflows)
4. [Database Migrations Guide](#database-migrations-guide)
5. [Troubleshooting](#troubleshooting)

---

## When to Build vs When to Restart

### 🔨 When to BUILD (`docker-compose build`)

Rebuild the Docker image when you change:
- ✅ `Dockerfile`
- ✅ `pyproject.toml` (adding/removing dependencies)
- ✅ `requirements.txt` (if you were using it)
- ✅ System packages in Dockerfile (apt-get install...)

**Command:**
```bash
docker-compose build
# or rebuild and start:
docker-compose up -d --build
```

### 🔄 When to RESTART (`docker-compose restart`)

Restart containers (NO rebuild needed) when you change:
- ✅ `.env` file (environment variables)
- ✅ `docker-compose.yml` (ports, volumes, etc.)

**Command:**
```bash
docker-compose restart
```

### ⚡ NO ACTION NEEDED

These changes are **automatically reflected** (no build/restart):
- ✅ Python code changes (`models.py`, `views.py`, `admin.py`, etc.)
- ✅ Django settings (`settings.py`)
- ✅ Templates and static files

Why? Because your code is mounted as a volume (`- .:/app`) and Django's development server auto-reloads.

**Exception:** After changing `models.py`, you need to run migrations (see below).

---

## Common Commands Cheatsheet

### Starting & Stopping

```bash
# Start all services in background
docker-compose up -d

# Start and view logs in foreground
docker-compose up

# Stop all services (keeps data)
docker-compose down

# Stop and remove ALL data (including database!)
docker-compose down -v

# Restart services
docker-compose restart

# Restart only web service
docker-compose restart web
```

### Viewing Logs

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View only web service logs
docker-compose logs -f web

# View last 50 lines
docker-compose logs --tail=50 web
```

### Accessing Containers

```bash
# Execute command in web container
docker-compose exec web python src/manage.py shell

# Access bash shell in web container
docker-compose exec web bash

# Access PostgreSQL database
docker-compose exec db psql -U expat_user -d expat_insurance
```

---

## Detailed Workflows

### 🚀 Initial Setup (First Time)

```bash
# 1. Build the images
docker-compose build

# 2. Start the containers
docker-compose up -d

# 3. Wait for database to be healthy (check with)
docker-compose ps

# 4. Create initial migrations
docker-compose exec web python src/manage.py makemigrations

# 5. Apply migrations
docker-compose exec web python src/manage.py migrate

# 6. Create superuser for admin access
docker-compose exec web python src/manage.py createsuperuser

# 7. Access admin at http://localhost:8000/admin
```

### 📝 Daily Development Workflow

**Scenario 1: Just coding (models.py, views.py, etc.)**
```bash
# 1. Make sure containers are running
docker-compose ps

# If not running:
docker-compose up -d

# 2. Edit your code (auto-reloads)
# No other actions needed!

# 3. Check logs if needed
docker-compose logs -f web
```

**Scenario 2: Changed models (models.py)**
```bash
# 1. Edit models.py
# (containers auto-detect code changes)

# 2. Create migration file
docker-compose exec web python src/manage.py makemigrations

# 3. Apply migration
docker-compose exec web python src/manage.py migrate

# 4. If you changed admin.py to use new fields, verify:
docker-compose logs -f web
```

**Scenario 3: Added new Python package**
```bash
# 1. Add to pyproject.toml dependencies list
# Example: "requests>=2.31.0"

# 2. Rebuild the image
docker-compose down
docker-compose build

# 3. Start containers
docker-compose up -d

# 4. Verify package is installed
docker-compose exec web python -c "import requests; print(requests.__version__)"
```

**Scenario 4: Changed environment variables (.env)**
```bash
# 1. Edit .env file

# 2. Restart containers (no rebuild needed)
docker-compose down
docker-compose up -d
```

---

## Database Migrations Guide

### What are Migrations?

Django migrations are version control for your database schema. They track changes to your models and apply them to the database.

### Complete Migration Workflow

#### 1️⃣ Creating Migrations

```bash
# After changing models.py, create migration file
docker-compose exec web python src/manage.py makemigrations

# Create migration with a descriptive name
docker-compose exec web python src/manage.py makemigrations --name add_customer_phone_field

# See what SQL will be executed (without running it)
docker-compose exec web python src/manage.py sqlmigrate comparator_app 0001
```

#### 2️⃣ Viewing Migrations

```bash
# List all migrations and their status
docker-compose exec web python src/manage.py showmigrations

# Show which migrations need to be applied
docker-compose exec web python src/manage.py showmigrations --plan
```

#### 3️⃣ Applying Migrations

```bash
# Apply all pending migrations
docker-compose exec web python src/manage.py migrate

# Apply migrations for specific app only
docker-compose exec web python src/manage.py migrate comparator_app

# Apply up to a specific migration
docker-compose exec web python src/manage.py migrate comparator_app 0003
```

#### 4️⃣ Rolling Back Migrations

```bash
# Roll back to previous migration
docker-compose exec web python src/manage.py migrate comparator_app 0002

# Roll back all migrations for an app
docker-compose exec web python src/manage.py migrate comparator_app zero

# ⚠️ WARNING: This will delete all data in those tables!
```

#### 5️⃣ Handling Migration Conflicts

If you get migration conflicts (common in team environments):

```bash
# Option 1: Merge migrations
docker-compose exec web python src/manage.py makemigrations --merge

# Option 2: Start fresh (DEVELOPMENT ONLY - loses data!)
# Delete migration files
rm src/comparator_app/migrations/0*.py

# Reset database
docker-compose exec -T db psql -U expat_user -d expat_insurance -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Recreate migrations
docker-compose exec web python src/manage.py makemigrations
docker-compose exec web python src/manage.py migrate
```

### Migration Best Practices

✅ **DO:**
- Run `makemigrations` after every model change
- Review migration files before committing
- Test migrations on a copy of production data before deploying
- Keep migrations small and focused
- Commit migration files to git

❌ **DON'T:**
- Edit migration files manually (unless you know what you're doing)
- Delete migration files that have been applied in production
- Skip migrations when deploying to production

---

## Troubleshooting

### Problem: Port 8000 already in use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process (replace PID)
kill -9 <PID>

# Or change port in docker-compose.yml:
ports:
  - "8001:8000"  # Use 8001 on host instead
```

### Problem: Database connection errors

```bash
# Check if database is healthy
docker-compose ps

# If not healthy, check logs
docker-compose logs db

# Restart database
docker-compose restart db

# Nuclear option: reset everything
docker-compose down -v
docker-compose up -d
```

### Problem: "Module not found" error

```bash
# Rebuild image (might have forgotten after adding dependency)
docker-compose down
docker-compose build
docker-compose up -d
```

### Problem: Django says "No migrations to apply" but changes aren't in DB

```bash
# Check if migrations were created
ls -la src/comparator_app/migrations/

# Check migration status
docker-compose exec web python src/manage.py showmigrations

# If migrations exist but aren't applied:
docker-compose exec web python src/manage.py migrate

# If no migrations exist:
docker-compose exec web python src/manage.py makemigrations
docker-compose exec web python src/manage.py migrate
```

### Problem: Code changes aren't reflecting

```bash
# Check if volume is mounted correctly
docker-compose exec web ls -la /app/src/comparator_app/

# Restart web container
docker-compose restart web

# Check Django logs for errors
docker-compose logs -f web
```

### Problem: Want to completely start over

```bash
# ⚠️ WARNING: This deletes ALL data!

# 1. Stop and remove everything
docker-compose down -v

# 2. Remove all migration files
rm src/comparator_app/migrations/0*.py

# 3. Rebuild and start
docker-compose build
docker-compose up -d

# 4. Create fresh migrations
docker-compose exec web python src/manage.py makemigrations
docker-compose exec web python src/manage.py migrate

# 5. Create superuser
docker-compose exec web python src/manage.py createsuperuser
```

---

## Quick Reference: Your Current State

After following this guide, your setup is:

- ✅ Docker containers running: `docker-compose ps`
- ✅ Database migrated: `docker-compose exec web python src/manage.py showmigrations`
- ✅ Admin interface: http://localhost:8000/admin
- ✅ PostgreSQL: localhost:5432 (expat_insurance / expat_user)
- ✅ Code changes auto-reload (no restart needed)
- ✅ Migrations needed after model changes only

### Daily Commands You'll Use Most

```bash
# Start working
docker-compose up -d

# After changing models.py
docker-compose exec web python src/manage.py makemigrations
docker-compose exec web python src/manage.py migrate

# View logs when debugging
docker-compose logs -f web

# End of day (optional)
docker-compose down
```

---

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Django Admin | http://localhost:8000/admin | Your superuser |
| Django App | http://localhost:8000 | - |
| PostgreSQL | localhost:5432 | expat_user / expat_password_local |
| Database Name | expat_insurance | - |

---

## Need Help?

- Django docs: https://docs.djangoproject.com/
- Docker compose docs: https://docs.docker.com/compose/
- PostgreSQL in container: `docker-compose exec db psql -U expat_user -d expat_insurance`
- Django shell: `docker-compose exec web python src/manage.py shell`

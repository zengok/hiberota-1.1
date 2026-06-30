# HibeRota Deployment & Operations Procedures

**Tarih:** 30 Haziran 2026  
**Versiyon:** 1.0  
**Amaç:** Production deployments, scaling, monitoring, incident response  

---

## 📋 TABLE OF CONTENTS

1. [Deployment Pipeline](#deployment-pipeline)
2. [Staging to Production Workflow](#staging-to-production)
3. [Rollback Procedures](#rollback-procedures)
4. [Scaling Procedures](#scaling-procedures)
5. [Incident Response](#incident-response)
6. [Monitoring & Alerting](#monitoring--alerting)
7. [Database Maintenance](#database-maintenance)
8. [Team Runbooks](#team-runbooks)

---

## 🚀 DEPLOYMENT PIPELINE

### Automated CI/CD (GitHub Actions)

**Current Status:** ✅ Configured (from TASKS.md - Faz 1)

```yaml
# Deployment flow:
1. Developer pushes to main branch
2. GitHub Actions runs:
   - Linting (ruff check)
   - Type checking (mypy)
   - Tests (pytest)
   - Security (bandit, pip-audit)
3. If all pass → Deploy to staging
4. Manual approval → Deploy to production
```

### Deployment Checklist

**Before Deployment:**
- [ ] All tests pass (CI/CD green)
- [ ] Code review approved (2+ reviewers)
- [ ] Security audit passed
- [ ] Database migrations reviewed
- [ ] Performance impact analyzed
- [ ] Rollback plan documented

**During Deployment:**
- [ ] Notify team in Slack
- [ ] Monitor application logs
- [ ] Monitor server resources
- [ ] Monitor uptime (status page)
- [ ] Have SSH access ready for rollback

**After Deployment:**
- [ ] Verify functionality (smoke tests)
- [ ] Check error rates (< 0.1%)
- [ ] Monitor performance (latency, throughput)
- [ ] Gather user feedback
- [ ] Post-mortem if issues

---

## 🔄 STAGING TO PRODUCTION WORKFLOW

### Pre-Production Testing (Staging)

**Staging Environment:** staging.hiberota.com (separate instance)

```bash
# Deploy to staging
1. Merge PR to develop branch
2. Staging auto-deploys (GitHub Actions)
3. Run smoke tests: pytest -m smoke
4. Load testing: python manage.py run_staging_load_smoke
5. Manual testing: Verify key features

# Data in Staging:
- Sanitized copy of production DB (weekly)
- Test accounts with sample data
- Live crawling disabled (prevent data pollution)
```

### Production Deployment Process

**Deployment Window:** Tuesdays & Thursdays, 10 AM UTC (low traffic)

```
Step 1: Prepare
  └─ Verify all systems healthy
  └─ Create database backup
  └─ Document current state

Step 2: Deploy Code
  └─ Pull latest from main branch
  └─ Run migrations: python manage.py migrate
  └─ Collect static files: python manage.py collectstatic
  └─ Restart Gunicorn: systemctl restart gunicorn_hiberota

Step 3: Verify
  └─ Check health endpoint: /health/ready
  └─ Verify API responses
  └─ Check error logs (no 5xx errors)

Step 4: Monitor
  └─ Monitor for 30 minutes
  └─ Check uptime status page
  └─ Monitor error rates and latency

Step 5: Communicate
  └─ Send update to team
  └─ Update status page
  └─ Notify early access users (if major feature)
```

### Zero-Downtime Deployment Strategy

```bash
# Using blue-green deployment:

1. Blue Instance: Current production (running)
2. Green Instance: New version (prepared)

Deployment:
  1. Deploy code to green instance
  2. Run migrations on green
  3. Run smoke tests on green
  4. Switch Nginx upstream to green
  5. Monitor for issues
  6. If OK: Keep green as primary
     If issues: Nginx points back to blue (instant rollback)

Benefits:
  - Zero downtime
  - Instant rollback if issues
  - Easy to debug problems
```

### Deployment Script Template

```bash
#!/bin/bash
# deploy_to_production.sh

set -e

APP_DIR="/var/www/hiberota"
BACKUP_DIR="/backups/hiberota"
LOG_FILE="/var/log/deployment_$(date +%Y-%m-%d_%H-%M-%S).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# 1. Create backup
log "Creating backup..."
pg_dump -U hiberota hiberota | gzip > $BACKUP_DIR/pre_deploy_$(date +%Y-%m-%d_%H-%M-%S).sql.gz

# 2. Pull latest code
log "Pulling latest code..."
cd $APP_DIR
git fetch origin
git checkout main
git pull origin main

# 3. Install dependencies
log "Installing dependencies..."
source .venv/bin/activate
pip install -r requirements/prod.txt

# 4. Run migrations
log "Running migrations..."
python manage.py migrate

# 5. Collect static files
log "Collecting static files..."
python manage.py collectstatic --noinput

# 6. Run tests
log "Running tests..."
pytest -x

# 7. Restart services
log "Restarting services..."
systemctl restart gunicorn_hiberota
systemctl restart celery_hiberota

# 8. Verify deployment
log "Verifying deployment..."
sleep 5
curl -f https://hiberota.com/health/ready || exit 1

log "✅ Deployment successful!"
```

---

## ⚙️ ROLLBACK PROCEDURES

### Scenario 1: Code Issues (Simple Rollback)

```bash
# Detect issue (within 10 minutes)
ERROR_RATE=$(curl -s https://api.hiberota.com/metrics | jq '.error_rate')

if [ $ERROR_RATE -gt 0.01 ]; then
    echo "❌ Error rate too high: $ERROR_RATE"
    
    # Rollback immediately
    cd /var/www/hiberota
    git revert HEAD
    git push origin main
    
    # Restart services
    systemctl restart gunicorn_hiberota
    
    # Verify
    sleep 5
    curl https://hiberota.com/health/ready
fi
```

### Scenario 2: Database Migration Issues

```bash
# If migration failed:

# 1. Stop application
systemctl stop gunicorn_hiberota

# 2. Restore from backup
pg_restore -U hiberota hiberota < /backups/hiberota/pre_deploy_latest.sql

# 3. Revert code changes
cd /var/www/hiberota
git revert HEAD

# 4. Run old migrations
python manage.py migrate --no-input

# 5. Restart application
systemctl start gunicorn_hiberota

# 6. Verify
curl https://hiberota.com/health/ready
```

### Scenario 3: Infrastructure Failure

```bash
# If server is down (Güzel Hosting outage):

# Action: Failover to cloud (temporary)
1. SSH to cloud backup server (if available)
2. Restore database from latest backup
3. Deploy latest code
4. Point DNS to cloud IP (temporary)
5. Notify users of degraded service
6. Wait for Güzel Hosting recovery
7. Migrate back when ready
```

---

## 📈 SCALING PROCEDURES

### Horizontal Scaling (Add more servers)

**Q2 2027 - Transition to Cloud**

```bash
# Load balancer setup (AWS ALB)
1. Create Application Load Balancer
2. Create target group (3x web servers)
3. Add health checks: /health/live
4. Configure auto-scaling group:
   - Min: 2 instances
   - Max: 10 instances
   - Target CPU: 70%

# Gunicorn worker configuration
workers = (2 * CPU_CORES) + 1  # e.g., 8 cores = 17 workers

# For 3x t3.small servers (2 cores each):
workers = 5 per server × 3 = 15 total workers
```

### Vertical Scaling (Bigger server)

**Q4 2026 - Single Server Upgrade**

```bash
# Current: 4GB RAM, 60GB HDD
# Upgrade: 16GB RAM, 250GB SSD

# Steps:
1. Notify Güzel Hosting (request downtime 30 min)
2. Create full backup
3. Stop services
4. Perform upgrade
5. Verify hardware
6. Restart services
7. Run smoke tests
8. Notify team

# No code changes needed - just infrastructure
```

### Database Scaling (Read Replicas)

**Q2 2027 - High Traffic**

```sql
-- Create read replica (AWS RDS)
CREATE ROLE readonly WITH PASSWORD 'secure_password' LOGIN;
GRANT CONNECT ON DATABASE hiberota TO readonly;
GRANT USAGE ON SCHEMA public TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;

-- Configure Django for read/write splitting:
DATABASES = {
    'default': {  # Write master
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'hiberota-db-master.c9akciq32.us-east-1.rds.amazonaws.com',
        'NAME': 'hiberota',
    },
    'read_replica': {  # Read-only replica
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'hiberota-db-replica.c9akciq32.us-east-1.rds.amazonaws.com',
        'NAME': 'hiberota',
    }
}

# Use in queries:
# Write: GrantCall.objects.using('default').create(...)
# Read:  GrantCall.objects.using('read_replica').filter(...)
```

### Cache Scaling (Cluster)

**Q1 2027 - Memory Pressure**

```bash
# Migrate Redis to cluster mode
# Use redis-cluster for high availability

# Configuration:
redis-cluster-enabled yes
redis-cluster-node-timeout 15000
cluster-require-full-coverage no

# Connect from Django:
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'rediscluster://redis-node-1:6379?skip_full_coverage_check=True',
    }
}
```

---

## 🚨 INCIDENT RESPONSE

### Alert Levels

| Level | Example | Response Time | Action |
|-------|---------|----------------|--------|
| 🟢 **Green** | CPU 40%, latency 100ms | N/A | Monitor |
| 🟡 **Yellow** | CPU 75%, latency 500ms | 15 min | Investigate |
| 🔴 **Red** | Site down, error rate 50% | 5 min | Engage on-call, notify users |
| ⚫ **Critical** | Data loss, security breach | 2 min | Escalate, initiate incident response |

### Incident Response Checklist

**IMMEDIATE (within 5 minutes)**
- [ ] Acknowledge alert
- [ ] Verify issue (not false positive)
- [ ] Notify on-call team (Slack/SMS)
- [ ] Start incident channel: #incident-YYYY-MM-DD
- [ ] Note start time

**MITIGATION (within 15 minutes)**
- [ ] Stop bleeding (rollback if needed)
- [ ] Isolate affected systems
- [ ] Implement workaround if available
- [ ] Communicate status to users

**INVESTIGATION (parallel)**
- [ ] Check error logs
- [ ] Review recent deployments
- [ ] Check resource usage
- [ ] Check external dependencies (DNS, CDN)

**RESOLUTION**
- [ ] Root cause identified
- [ ] Fix deployed
- [ ] Verification complete
- [ ] Post-mortem scheduled

**POST-INCIDENT**
- [ ] Write post-mortem (within 24 hours)
- [ ] Identify action items
- [ ] Update runbooks
- [ ] Communicate lessons learned

### Common Issues & Solutions

**Issue: High CPU**
```bash
# Check what's using CPU
top -b -n 1 | head -20
ps aux --sort -%cpu | head -10

# If Gunicorn: Restart workers
systemctl restart gunicorn_hiberota

# If PostgreSQL: Kill long-running queries
SELECT pid, duration, query FROM pg_stat_activity 
WHERE duration > interval '5 minutes';
SELECT pg_terminate_backend(pid) WHERE duration > interval '5 minutes';
```

**Issue: Database Connection Timeout**
```bash
# Check connection pool
psql -U hiberota -d hiberota -c "SELECT count(*) FROM pg_stat_activity;"

# Increase pool size in Django settings:
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

**Issue: Memory Leak (Growing memory)**
```bash
# Monitor memory over time
free -h && sleep 60 && free -h && sleep 60 && free -h

# Check process memory
ps aux | grep gunicorn
ps aux | grep celery
ps aux | grep postgres

# If Gunicorn is leaking: Increase max_requests
# In Gunicorn config:
max_requests = 1000  # Restart worker after 1000 requests
max_requests_jitter = 50  # Add jitter to prevent thundering herd
```

---

## 📊 MONITORING & ALERTING

### Key Metrics to Monitor

```
Application:
  - Request latency (p50, p95, p99)
  - Error rate (5xx errors)
  - Request throughput (RPS)
  - Active connections
  
Infrastructure:
  - CPU usage
  - Memory usage
  - Disk I/O
  - Disk space
  - Network bandwidth
  
Database:
  - Query latency
  - Slow queries (> 1s)
  - Connection count
  - Cache hit ratio
  
Workers:
  - Queue depth
  - Task duration
  - Failed tasks
  - Worker uptime
```

### Alert Thresholds

```
CRITICAL (page on-call):
  - Request latency p95 > 5s
  - Error rate > 5%
  - Disk usage > 90%
  - Memory usage > 90%
  - CPU usage > 95% sustained
  - Site down (503 Service Unavailable)

WARNING (notify team):
  - Request latency p95 > 1s
  - Error rate > 1%
  - Disk usage > 75%
  - Memory usage > 75%
  - Queue depth > 1000
  - Slow queries > 10% of queries
```

### Monitoring Tools Setup

```bash
# Use Prometheus + Grafana
# Install on separate monitoring server

# 1. Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-2.40.0.linux-amd64.tar.gz
cd prometheus-2.40.0.linux-amd64
./prometheus --config.file=prometheus.yml

# 2. Configure scrape targets (prometheus.yml)
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'hiberota'
    static_configs:
      - targets: ['70.40.138.74:9100']  # node exporter
      - targets: ['70.40.138.74:5432']  # PostgreSQL
      - targets: ['70.40.138.74:6379']  # Redis

# 3. Install Grafana
docker run -d -p 3000:3000 grafana/grafana

# 4. Add Prometheus data source
# UI: Admin → Data Sources → Add Prometheus → http://prometheus:9090
```

---

## 🗄️ DATABASE MAINTENANCE

### Regular Maintenance Tasks

**Daily:**
```bash
# Run daily at 2 AM (low traffic)
psql -U hiberota -d hiberota << EOF
  -- Vacuum dead rows
  VACUUM;
  
  -- Check for issues
  SELECT schemaname, tablename, n_dead_tup, n_live_tup
  FROM pg_stat_user_tables
  WHERE n_dead_tup > 10000;
EOF
```

**Weekly:**
```bash
# Run weekly (Sunday 3 AM)
psql -U hiberota -d hiberota << EOF
  -- Full vacuum with reindex
  VACUUM FULL ANALYZE;
  
  -- Reindex tables with high bloat
  REINDEX DATABASE hiberota;
  
  -- Check table sizes
  SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size('"'||schemaname||'"."'||tablename||'"'))
  FROM pg_tables
  WHERE schemaname != 'pg_catalog'
  ORDER BY pg_total_relation_size('"'||schemaname||'"."'||tablename||'"') DESC
  LIMIT 10;
EOF
```

**Monthly:**
```bash
# Run monthly (first Sunday)
# 1. Update statistics
psql -U hiberota -d hiberota -c "ANALYZE;"

# 2. Check query plans for issues
psql -U hiberota -d hiberota << EOF
  EXPLAIN ANALYZE
  SELECT * FROM calls_grantcall WHERE deadline_at > NOW() LIMIT 10;
EOF

# 3. Monitor log growth
tail -1000 /var/log/postgresql/postgresql.log | grep "duration:"
```

---

## 👥 TEAM RUNBOOKS

### On-Call Responsibilities

**Daily on-call engineer:**
- Monitor alert channels
- Respond to incidents within SLA
- Document issues and resolutions
- Hand off to next engineer

**Key contacts:**
```
Platform Engineer (Django/DevOps):
  Name: [TBD]
  Slack: @[handle]
  Phone: [number]
  
Database Administrator:
  Name: [TBD]
  Slack: @[handle]
  Phone: [number]
  
Product Manager (for escalation):
  Name: [TBD]
  Slack: @[handle]
  Email: [email]
```

### Communication Channels

```
Real-time alerts:    #incidents (Slack)
Status updates:      #status (Slack)
Post-mortems:        #post-mortems (Slack)
On-call rotation:    PagerDuty or Opsgenie
```

### Escalation Path

```
Level 1: On-call engineer
  Response: 15 minutes
  Can handle: Most operational issues
  
Level 2: Engineering manager
  Response: 5 minutes
  Can handle: Technical decisions, resource allocation
  
Level 3: VP Engineering
  Response: 2 minutes
  Can handle: Business impact, customer communication
  
Level 4: CEO
  Response: 1 minute
  Can handle: Major incidents, public disclosure
```

---

## ✅ PRE-LAUNCH CHECKLIST (July 2026)

For Faz 12 (REST API Launch):

- [ ] Deployment script tested on staging
- [ ] Rollback procedure documented and tested
- [ ] Monitoring alerts configured
- [ ] On-call rotation established
- [ ] Incident response runbook written
- [ ] Database backup tested
- [ ] Load balancer configured (if multiple servers)
- [ ] DNS failover plan documented
- [ ] Team trained on deployment process
- [ ] Status page set up and tested

---

## 📚 REFERENCE DOCUMENTS

| Document | Purpose |
|----------|---------|
| `SERVER_SETUP_GUIDE.md` | Infrastructure setup & monitoring |
| `DEPLOYMENT_AND_OPERATIONS.md` | This document - deployment & incident response |
| `.github/workflows/ci.yml` | CI/CD pipeline configuration |
| `docs/BACKUP_RESTORE.md` | Backup/restore procedures |
| `docs/FIRST_72_HOUR_MONITORING_REPORT.md` | Post-launch monitoring |

---

**Created:** 30 June 2026  
**Status:** READY FOR IMPLEMENTATION  
**Next Review:** 1 July 2026 (after server upgrade)

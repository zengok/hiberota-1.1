# HibeRota Production Server Setup & Operations Guide

**Tarih:** 30 Haziran 2026  
**Server:** server.hiberota.com  
**Status:** ✅ Online & Active  

---

## 📋 SERVER SPECIFICATIONS

### Mevcut Altyapı

```
Hostname:           server.hiberota.com
Primary IP:         70.40.138.74
IPv6:               2a06:41c0:1:1:151d:f437
Status:             Online ✅
Uptime:             Active

Hardware:
  RAM:              4 GB
  Disk:             60 GB HDD
  
Traffic:
  Monthly Used:     3.98 GB / 2 TB
  Available:        Unlimited
  
Nameservers:
  NS1:              ns1.hiberota.com.tr (Güzel Hosting)
  NS2:              ns2.hiberota.com.tr (Güzel Hosting)
  Additional:       tr.guzelhosting.com
                    eu.guzelhosting.com
                    us.guzelhosting.com
                    sg.guzelhosting.com
```

### Hosting Provider
- **Provider:** Güzel Hosting (guzelhosting.com)
- **Kontrol Paneli:** cPanel / DirectAdmin
- **Nameserver Management:** Custom nameservers configured

---

## ⚠️ SERVER CAPACITY ANALYSIS

### Current Usage vs. Roadmap Needs

| Metrik | Current | Q3 2026 Needs | Q4 2026 Needs | Status |
|--------|---------|---------------|---------------|--------|
| **RAM** | 4 GB | 4-6 GB | 6-8 GB | ⚠️ TIGHT |
| **Disk** | 60 GB | 80-100 GB | 150-200 GB | ⚠️ CRITICAL |
| **Traffic** | 3.98 GB/mo | 20-30 GB/mo | 50-80 GB/mo | ✅ OK |
| **CPU** | Unknown | 2-4 cores needed | 4-8 cores needed | ❓ VERIFY |

### 🚨 URGENT ISSUES

1. **Disk Space Crisis** (60 GB)
   - Current DB size unknown
   - Need 150-200 GB by Q4 2026
   - **ACTION:** Upgrade to 250 GB+ HDD immediately

2. **RAM Constraint** (4 GB)
   - Django: ~500 MB
   - PostgreSQL: ~1 GB
   - Redis: ~500 MB
   - Celery workers: ~1.5 GB
   - **Remaining:** ~500 MB (dangerously low)
   - **ACTION:** Upgrade to 8-16 GB RAM

3. **No SSD** (HDD only)
   - Database performance bottleneck
   - Load time will suffer under traffic
   - **ACTION:** Upgrade to SSD (NVMe preferred)

---

## 📊 RECOMMENDED UPGRADE PATH

### Phase 1: Immediate (Before July 1, 2026)
```
Current:    4 GB RAM, 60 GB HDD
Upgrade to: 8 GB RAM, 150 GB SSD
Cost:       ~$30-50/month
Timeline:   Before Faz 12 launch
```

**Why:** Faz 12 (API) will increase load. Current resources insufficient.

### Phase 2: Q4 2026
```
Current:    8 GB RAM, 150 GB SSD
Upgrade to: 16 GB RAM, 250 GB SSD
Cost:       ~$50-80/month
Timeline:   October 2026
```

**Why:** User growth, analytics data accumulation.

### Phase 3: Q2 2027 (Scaling Decision)
```
Options:
  A) Dedicated Server (16+ GB, 500+ GB SSD)
  B) Cloud Infrastructure (AWS, DigitalOcean, Linode)
  C) Multi-server setup (load balancing)
  
Recommendation: Option B (Cloud) for elasticity
Cost:           ~$100-200/month
Timeline:       April 2027
```

---

## 🔧 IMMEDIATE ACTIONS (This Week)

### 1. Server Resource Audit ⏰ TODAY

```bash
# SSH into server
ssh root@70.40.138.74

# Check current usage
df -h              # Disk space
free -h            # RAM usage
top                # CPU usage
ps aux             # Running processes

# Check database size
sudo -u postgres psql
> SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) 
  FROM pg_database 
  WHERE datname = 'hiberota';

# Check Redis memory
redis-cli INFO memory
```

### 2. Submit Upgrade Request ⏰ TODAY

Contact Güzel Hosting (guzelhosting.com):
```
Request: Server resource upgrade
Current: 4 GB RAM, 60 GB HDD
New:     8 GB RAM, 150 GB SSD
Timeline: Within 24 hours (before July 1)
Reason: Production traffic increase
```

### 3. Backup Everything ⏰ TODAY

```bash
# Full database backup
pg_dump -U hiberota hiberota > /backup/hiberota_backup_2026-06-30.sql

# Media files backup
tar -czf /backup/media_2026-06-30.tar.gz /var/www/hiberota/media/

# Static files backup
tar -czf /backup/static_2026-06-30.tar.gz /var/www/hiberota/static/

# Config backup
tar -czf /backup/config_2026-06-30.tar.gz /var/www/hiberota/config/ /var/www/hiberota/.env
```

### 4. Monitor Current Load ⏰ ONGOING

```bash
# Install monitoring
apt-get install htop iotop

# Watch real-time resources
watch -n 1 'free -h && df -h'

# Log to file
(while true; do echo "$(date): $(free -h | grep Mem) - $(df -h | grep /dev)"; sleep 60; done) >> /var/log/resource_monitor.log
```

---

## 🌐 DOMAIN & DNS CONFIGURATION

### Current DNS Setup

```
Domain:        hiberota.com
Registrar:     (Verify - likely same as hosting)
Nameservers:   Güzel Hosting custom NS

DNS Records:
  A Record:              70.40.138.74
  AAAA Record:           2a06:41c0:1:1:151d:f437
  MX Records:            (Check current setup)
  TXT Records:           SPF, DKIM, DMARC (verify)

Subdomains Configured:
  www.hiberota.com       → 70.40.138.74
  staging.hiberota.com   → (Separate stack or same?)
  api.hiberota.com       → (Ready for Faz 12 API)
  admin.hiberota.com     → (For admin panel access?)
```

### DNS Changes Needed for Faz 12

```
NEW Subdomains to Add:
  api.hiberota.com       → 70.40.138.74
  docs.hiberota.com      → 70.40.138.74 (API documentation)
  status.hiberota.com    → 70.40.138.74 (uptime status page)
  
Email Configuration:
  mail.hiberota.com      → (Set up if needed)
  MX Records             → (Configure email delivery)
```

**Action:** Update DNS records in cPanel/hosting panel

---

## 🚀 APPLICATION DEPLOYMENT SETUP

### Current Django Setup

```
Web Root:          /var/www/hiberota/ (assumed)
Django User:       hiberota (recommended)
Web Server:        Nginx (from README)
App Server:        Gunicorn (4 workers)
Process Manager:   Systemd or Supervisor

Database:          PostgreSQL (localhost:5432)
Cache:             Redis (localhost:6379)
Task Queue:        Celery (Redis broker)
Scheduler:         Celery Beat
```

### Verify Deployment

```bash
# Check if services are running
systemctl status nginx
systemctl status gunicorn_hiberota
systemctl status postgresql
systemctl status redis-server
systemctl status celery_hiberota
systemctl status celery_beat_hiberota

# Check logs for errors
tail -f /var/log/nginx/error.log
tail -f /var/www/hiberota/logs/gunicorn.log
tail -f /var/log/postgresql/postgresql.log
```

### Create Systemd Services (if not exists)

```bash
# Gunicorn service
sudo tee /etc/systemd/system/gunicorn_hiberota.service > /dev/null <<EOF
[Unit]
Description=Gunicorn daemon for HibeRota
After=network.target

[Service]
Type=notify
User=hiberota
WorkingDirectory=/var/www/hiberota
ExecStart=/var/www/hiberota/.venv/bin/gunicorn \
  --workers 4 \
  --worker-class sync \
  --bind unix:/var/run/gunicorn_hiberota.sock \
  --timeout 60 \
  config.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable gunicorn_hiberota
sudo systemctl start gunicorn_hiberota
```

---

## 🔐 SECURITY HARDENING

### Current Security Status

```
Firewall:          Configured (via Güzel Hosting)
SSL/TLS:           Cloudflare (origin verified)
SSH:               Key-only access (from docs)
Root Login:        Disabled (from docs)
Fail2Ban:          Configured (from docs)
```

### Verify Security

```bash
# Check SSH config
sudo sshd -T | grep -E "PasswordAuthentication|PermitRootLogin"

# Check firewall (if using UFW)
sudo ufw status
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS

# Check Fail2Ban
sudo fail2ban-client status
sudo fail2ban-client status sshd

# Check SSL certificate
openssl s_client -connect server.hiberota.com:443 -showcerts

# Verify CSP headers
curl -I https://hiberota.com | grep -i "Content-Security-Policy"
```

### Harden Further

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Configure fail2ban for Django
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[sshd]
enabled = true
maxretry = 3
findtime = 600
bantime = 3600

[recidive]
enabled = true
maxretry = 3
findtime = 604800
bantime = 2592000
EOF

sudo systemctl restart fail2ban
```

---

## 📊 MONITORING & UPTIME

### Setup Monitoring

```bash
# Install monitoring tools
sudo apt-get install prometheus-node-exporter

# Configure systemd for node exporter
sudo systemctl enable prometheus-node-exporter
sudo systemctl start prometheus-node-exporter

# Setup log aggregation
sudo apt-get install rsyslog
sudo systemctl enable rsyslog
```

### Create Uptime Check Script

```bash
# /etc/cron.hourly/hiberota_health_check.sh
#!/bin/bash

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://hiberota.com/health/ready)

if [ "$RESPONSE" = "200" ]; then
  echo "$TIMESTAMP - OK (200)" >> /var/log/hiberota_health.log
else
  echo "$TIMESTAMP - ERROR ($RESPONSE)" >> /var/log/hiberota_health.log
  # Send alert
  mail -s "HibeRota Health Check Failed: $RESPONSE" admin@hiberota.com <<< "Server returned $RESPONSE"
fi
```

### Setup Uptime Status Page

```bash
# Create public status page
mkdir -p /var/www/hiberota/public/status/
cat > /var/www/hiberota/public/status/index.html <<EOF
<!DOCTYPE html>
<html>
<head>
  <title>HibeRota Status</title>
  <meta http-equiv="refresh" content="300">
</head>
<body>
  <h1>HibeRota System Status</h1>
  <p>Last updated: <span id="last-update">Loading...</span></p>
  <ul>
    <li>Web: <span id="web-status">Checking...</span></li>
    <li>API: <span id="api-status">Checking...</span></li>
    <li>Database: <span id="db-status">Checking...</span></li>
  </ul>
  <script>
    // Check status every 30 seconds
    setInterval(checkStatus, 30000);
    checkStatus();
    
    function checkStatus() {
      fetch('https://hiberota.com/health/ready')
        .then(r => {
          document.getElementById('web-status').textContent = r.ok ? '✅ Online' : '❌ Offline';
          document.getElementById('last-update').textContent = new Date().toLocaleString();
        })
        .catch(() => {
          document.getElementById('web-status').textContent = '❌ Offline';
        });
    }
  </script>
</body>
</html>
EOF
```

---

## 📈 PERFORMANCE OPTIMIZATION

### Database Optimization

```bash
# Connect to PostgreSQL
sudo -u postgres psql hiberota

# Analyze tables
ANALYZE;

# Reindex database
REINDEX DATABASE hiberota;

# Vacuum database
VACUUM FULL;

# Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;
```

### Redis Optimization

```bash
# Check Redis memory
redis-cli INFO memory

# Clear unused keys
redis-cli KEYS "*" | wc -l  # Show key count
redis-cli FLUSHDB           # Clear if needed

# Monitor Redis commands
redis-cli MONITOR
```

### Nginx Optimization

```bash
# Update nginx config for caching
sudo tee /etc/nginx/conf.d/hiberota_cache.conf > /dev/null <<EOF
# Cache static files for 30 days
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}

# Cache HTML for 1 hour
location ~* \.html$ {
    expires 1h;
    add_header Cache-Control "public";
}
EOF

sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔄 BACKUP & DISASTER RECOVERY

### Automated Backup Strategy

```bash
# Daily backup script
sudo tee /etc/cron.daily/hiberota_backup.sh > /dev/null <<'EOF'
#!/bin/bash

BACKUP_DIR="/backups/hiberota"
DATE=$(date +%Y-%m-%d)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U hiberota hiberota | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/hiberota/media/

# Backup config
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /var/www/hiberota/config/ /var/www/hiberota/.env

# Remove old backups
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
EOF

sudo chmod +x /etc/cron.daily/hiberota_backup.sh
```

### Backup Verification

```bash
# Test restore from backup (to separate database)
gunzip -c /backups/hiberota/db_2026-06-30.sql.gz | \
  psql -U hiberota -d hiberota_restore

# Verify restore
psql -U hiberota -d hiberota_restore -c "SELECT COUNT(*) FROM calls_grantcall;"
```

---

## 📋 MAINTENANCE CHECKLIST

### Weekly
- [ ] Check disk space: `df -h`
- [ ] Check error logs: `tail -100 /var/log/nginx/error.log`
- [ ] Verify all services running
- [ ] Monitor CPU/RAM usage

### Monthly
- [ ] Run database VACUUM and ANALYZE
- [ ] Review security logs
- [ ] Update system packages: `apt update && apt upgrade`
- [ ] Test backup restoration
- [ ] Review and rotate logs

### Quarterly
- [ ] Full security audit
- [ ] Performance benchmarking
- [ ] Capacity planning review
- [ ] Disaster recovery drill

---

## 🚨 TROUBLESHOOTING GUIDE

### Site is slow

```bash
# Check resources
free -h
df -h
top

# Check database
sudo -u postgres psql hiberota -c "SELECT count(*) FROM calls_grantcall;"

# Check Redis
redis-cli INFO stats

# Check Nginx
tail -50 /var/log/nginx/access.log | awk '{print $7}' | sort | uniq -c | sort -rn
```

### Site is down

```bash
# Check services
systemctl status nginx gunicorn_hiberota postgresql redis-server

# Restart services
sudo systemctl restart nginx
sudo systemctl restart gunicorn_hiberota
sudo systemctl restart postgresql
sudo systemctl restart redis-server

# Check logs
tail -100 /var/log/syslog
tail -100 /var/log/nginx/error.log
```

### Database issues

```bash
# Check connections
psql -U hiberota -d hiberota -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Kill stuck connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'hiberota' AND state = 'idle';

# Rebuild indexes
REINDEX DATABASE hiberota;
```

---

## ✅ PRE-LAUNCH CHECKLIST (Faz 12)

Before API launch on July 1:

- [ ] Server upgraded to 8 GB RAM, 150 GB SSD
- [ ] All services verified running
- [ ] Backup system tested and working
- [ ] Monitoring dashboard set up
- [ ] SSL certificate renewed (if needed)
- [ ] DNS records updated (api.hiberota.com, docs.hiberota.com)
- [ ] Rate limiting configured
- [ ] Logging enabled for API calls
- [ ] Email system tested
- [ ] Failover procedure documented

---

## 📞 SUPPORT & CONTACTS

### Server Provider
- **Company:** Güzel Hosting
- **Website:** guzelhosting.com
- **Support:** Support ticket system in cPanel
- **Nameservers:** tr.guzelhosting.com, eu.guzelhosting.com, us.guzelhosting.com, sg.guzelhosting.com

### Recommended Escalation Path
1. Check server health yourself
2. Contact Güzel Hosting support
3. If critical: Prepare migration plan to cloud provider (AWS, DigitalOcean, Linode)

---

## 🔮 FUTURE INFRASTRUCTURE (2027)

### Recommended Upgrade Path

**Q2 2027 - Cloud Migration**
```
Current:   Single 4GB VPS
Migrate to: AWS/DigitalOcean multi-instance setup

Components:
  - 2x Web servers (Gunicorn) - t3.small each
  - 1x Database server - t3.medium (RDS preferred)
  - 1x Redis server - t3.small
  - 1x Worker server - t3.small
  - Load balancer (AWS ALB or DigitalOcean LB)
  - Auto-scaling group for workers
  - RDS backup automation
  - CloudFront CDN for static assets

Estimated Cost: $200-300/month
Benefits: Auto-scaling, auto-backup, high availability
```

---

**Prepared by:** DevOps/Operations Team  
**Last Updated:** 30 June 2026  
**Next Review:** 1 July 2026 (post-upgrade)  
**Status:** READY TO IMPLEMENT UPGRADES

# AWS Deployment Update Guide - Step by Step

## 🚀 Complete Guide to Pull and Update on AWS

**Date:** February 15, 2026  
**Server:** AWS EC2 (13.135.109.229)  
**Changes:** Database migrations, CHECK constraints, query optimizations, coupon feature

---

## ⚠️ IMPORTANT: Pre-Deployment Checklist

Before starting, ensure you have:
- [ ] SSH access to AWS server
- [ ] Backup of current database (or snapshot)
- [ ] No users currently using the system (or plan for minimal downtime)
- [ ] Environment variables properly configured on server

---

## 📋 Step-by-Step Deployment Commands

### Step 1: Connect to AWS Server

```bash
# SSH into your AWS EC2 instance
ssh -i your-key.pem ubuntu@13.135.109.229

# Or if using default user
ssh ubuntu@13.135.109.229
```

---

### Step 2: Navigate to Project Directory

```bash
# Go to the project directory
cd /path/to/MultiBook

# Verify you're in the correct directory
pwd
ls -la

# Check current branch
git branch
```

---

### Step 3: Backup Current State (CRITICAL!)

```bash
# Create a backup of the current code
cd ..
tar -czf multibook-backup-$(date +%Y%m%d-%H%M%S).tar.gz MultiBook/

# Verify backup was created
ls -lh multibook-backup-*.tar.gz

# Go back to project directory
cd MultiBook
```

---

### Step 4: Backup Database (CRITICAL!)

```bash
# If using PostgreSQL/Supabase, create a dump
# Note: Adjust connection details based on your .env file
cd backend

# Export to SQL file
python manage.py dumpdata > backup-$(date +%Y%m%d-%H%M%S).json

# Or use pg_dump if you have direct PostgreSQL access
# pg_dump -h your-supabase-host -U your-user -d your-db > backup.sql

cd ..
```

---

### Step 5: Check Current Status

```bash
# Check git status
git status

# Check for uncommitted changes
git diff

# If there are uncommitted changes, stash them
git stash save "Local changes before deployment $(date +%Y%m%d-%H%M%S)"
```

---

### Step 6: Pull Latest Changes from GitHub

```bash
# Fetch latest changes
git fetch origin

# Show what will be pulled
git log HEAD..origin/main --oneline

# Pull the latest code
git pull origin main

# Verify the pull was successful
git log -1
```

---

### Step 7: Check What Changed

```bash
# See the files that changed
git diff HEAD~1 --stat

# Review migration files
ls -la backend/apps/*/migrations/

# View the latest commit
git show --stat
```

---

### Step 8: Update Backend Dependencies (if needed)

```bash
# Navigate to backend
cd backend

# Activate virtual environment (if you're using one)
source venv/bin/activate
# or
source env/bin/activate

# Install/upgrade any new dependencies
pip install --upgrade -r requirements.txt

# Verify installations
pip list | grep -E "django|supabase|setuptools"
```

---

### Step 9: Run Database Migrations (CRITICAL!)

```bash
# Still in backend directory with venv activated

# First, check migration status
python manage.py showmigrations

# Review pending migrations
python manage.py migrate --plan

# Run migrations (this will apply all CHECK constraints)
python manage.py migrate

# Verify all migrations applied successfully
python manage.py showmigrations

# Expected migrations to be applied:
# - accounts.0004_invitation_invitation_valid_role_and_more
# - customers.0002_address_address_valid_type_and_more
# - staff.0004_staff_staff_name_not_empty_and_more
# - services.0003_category_category_name_not_empty_and_more
# - appointments.0004_appointment_appointment_valid_status_and_more
# - orders.0003_changerequest_changerequest_valid_status_and_more
# - subscriptions.0003_subscription_subscription_valid_frequency_and_more
# - coupons.0002_coupon_coupon_valid_discount_type_and_more
```

---

### Step 10: Test Database Constraints

```bash
# Test that the database is working correctly
python manage.py check

# Run a quick test query
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT COUNT(*) FROM accounts_user'); print(f'Users: {cursor.fetchone()[0]}')"

# Exit shell
```

---

### Step 11: Build Frontend

**CRITICAL:** Create `.env.production` *before* building. Next.js bakes `NEXT_PUBLIC_*` vars at build time. Without correct values, the app will show "Application error: a client-side exception".

```bash
# Go back to project root
cd ..

# Navigate to frontend
cd frontend

# Create .env.production with EC2 URLs (adjust hostname if different)
cat > .env.production << 'EOF'
NEXT_PUBLIC_API_URL=https://ec2-13-135-109-229.eu-west-2.compute.amazonaws.com/api
NEXT_PUBLIC_APP_URL=https://ec2-13-135-109-229.eu-west-2.compute.amazonaws.com
NEXT_PUBLIC_APP_NAME=MultiBook
NEXT_PUBLIC_API_VERSION=v1
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
EOF

# Replace YOUR_PROJECT_REF and anon key with your actual Supabase values
nano .env.production

# Install any new npm packages (if package.json changed)
npm install

# Build the frontend
npm run build

# Or if using production build
npm run build:production
```

---

### Step 12: Restart Backend Services

```bash
# Go back to backend
cd ../backend

# Restart Gunicorn (adjust service name if different)
sudo systemctl restart gunicorn
# or
sudo systemctl restart multibook-backend

# Check service status
sudo systemctl status gunicorn

# View recent logs
sudo journalctl -u gunicorn -n 50 --no-pager

# Or if using supervisor
sudo supervisorctl restart multibook
sudo supervisorctl status
```

---

### Step 13: Restart Frontend Service (if applicable)

```bash
# If you have a separate frontend service (Next.js, etc.)
cd ../frontend

# Restart the service
sudo systemctl restart multibook-frontend
# or
sudo systemctl restart nextjs

# Check status
sudo systemctl status multibook-frontend

# Or if using PM2
pm2 restart multibook-frontend
pm2 status
pm2 logs multibook-frontend --lines 50
```

---

### Step 14: Restart Nginx (if needed)

```bash
# Test nginx configuration
sudo nginx -t

# Reload nginx (graceful restart)
sudo systemctl reload nginx

# Or full restart if needed
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

---

### Step 15: Clear Cache (if using Redis/Celery)

```bash
# If you're using Redis for caching
redis-cli FLUSHALL

# Or flush specific database
redis-cli -n 0 FLUSHDB

# Restart Celery workers if you have them
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat

# Check Celery status
celery -A config inspect active
```

---

### Step 16: Verify Deployment

```bash
# Check all services are running
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status multibook-frontend  # if applicable

# Check application logs
sudo tail -f /var/log/gunicorn/error.log
sudo tail -f /var/log/nginx/error.log

# Test API endpoint
curl http://localhost:8000/api/health/
# or
curl https://your-domain.com/api/health/

# Check database connectivity
cd backend
python manage.py dbshell
# Then in psql:
\dt  # List all tables
\q   # Quit
```

---

### Step 17: Test Critical Features

```bash
# Test from the server
cd backend

# Test user authentication
python manage.py shell -c "from apps.accounts.models import User; print(f'Total users: {User.objects.count()}')"

# Test orders
python manage.py shell -c "from apps.orders.models import Order; print(f'Total orders: {Order.objects.count()}')"

# Test coupons (new feature)
python manage.py shell -c "from apps.coupons.models import Coupon; print(f'Total coupons: {Coupon.objects.count()}')"

# Test database constraints are working
python manage.py shell -c "from apps.orders.models import Order; from django.db import connection; cursor = connection.cursor(); cursor.execute(\"SELECT conname FROM pg_constraint WHERE conrelid = 'orders_order'::regclass;\"); print([c[0] for c in cursor.fetchall()])"
```

---

### Step 18: Monitor for Issues

```bash
# Monitor application logs in real-time
# Open multiple terminal sessions for this

# Terminal 1: Backend logs
sudo journalctl -u gunicorn -f

# Terminal 2: Nginx logs
sudo tail -f /var/log/nginx/access.log

# Terminal 3: Frontend logs (if applicable)
sudo journalctl -u multibook-frontend -f
# or
pm2 logs multibook-frontend

# Monitor for 5-10 minutes to ensure no errors
```

---

### Step 19: Test from Browser

Open your browser and test:

1. **Homepage**: https://your-domain.com
2. **Admin Panel**: https://your-domain.com/admin
3. **API**: https://your-domain.com/api/
4. **Customer Dashboard**: Test order creation
5. **New Coupon Feature**: Create and apply a coupon
6. **Test Guest Checkout**: Ensure guest orders work with constraints

---

### Step 20: Clean Up (Optional)

```bash
# Remove old backups (keep last 5)
cd /path/to/backups
ls -t multibook-backup-*.tar.gz | tail -n +6 | xargs rm -f

# Clean up pip cache
pip cache purge

# Clean up npm cache
cd frontend
npm cache clean --force

# Clean up old log files if needed
sudo find /var/log -name "*.log" -mtime +30 -delete
```

---

## 🔍 Troubleshooting Common Issues

### Issue 1: Migration Fails Due to Data Violation

```bash
# If a constraint migration fails due to existing bad data

# Check the error message for the constraint name
# Example: constraint "order_valid_status" fails

# Option A: Fix the data first
python manage.py shell
>>> from apps.orders.models import Order
>>> bad_orders = Order.objects.filter(status='invalid_status')
>>> bad_orders.update(status='pending')
>>> exit()

# Then run migrations again
python manage.py migrate

# Option B: Temporarily disable constraint (NOT RECOMMENDED)
# Only as last resort - fix data instead
```

### Issue 2: Service Won't Start

```bash
# Check detailed error logs
sudo journalctl -xe -u gunicorn

# Check if port is already in use
sudo netstat -tulpn | grep :8000

# Kill process if needed
sudo kill -9 <PID>

# Restart service
sudo systemctl restart gunicorn
```

### Issue 3: Frontend Build Fails

```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Issue 4: Database Connection Issues

```bash
# Check environment variables
cat backend/.env | grep DATABASE

# Test database connection
cd backend
python manage.py dbshell

# Check PostgreSQL is running (if local)
sudo systemctl status postgresql
```

### Issue 5: Permission Issues

```bash
# Fix ownership of files
sudo chown -R ubuntu:ubuntu /path/to/MultiBook

# Fix permissions
sudo chmod -R 755 /path/to/MultiBook
sudo chmod -R 644 /path/to/MultiBook/backend/.env
```

### Issue 6: "Application error: a client-side exception has occurred"

This usually means the frontend was built with wrong or missing env vars.

**1. Check browser console (F12 → Console)** for the actual error.

**2. Ensure `.env.production` exists before building:**
```bash
cd /var/www/VALClean/frontend
cat .env.production
# Must have:
# NEXT_PUBLIC_API_URL=https://ec2-13-135-109-229.eu-west-2.compute.amazonaws.com/api
# NEXT_PUBLIC_APP_URL=https://ec2-13-135-109-229.eu-west-2.compute.amazonaws.com
```

**3. Rebuild after fixing env:**
```bash
rm -rf .next
npm run build
# Restart frontend (PM2/systemd)
```

**4. Common causes:**
- Built with `localhost` URLs → API calls fail from user's browser
- Invalid `NEXT_PUBLIC_SUPABASE_URL` or `NEXT_PUBLIC_SUPABASE_ANON_KEY` (placeholders like `YOUR_PROJECT_REF`)
- Served over HTTP while CSP has `upgrade-insecure-requests` → use HTTPS

### Issue 7: MIME type ("text/plain") mismatch / NS_ERROR_CORRUPTED_CONTENT on _next/static/chunks

**Cause:** Nginx serves JS files with wrong `Content-Type` or serves a fallback (e.g. index.html) when the file path is wrong.

**Fix:** Proxy `/_next/*` to the Next.js server instead of serving files directly. Nginx should not use `try_files` with SPA fallback for `/_next/`.

**Recommended Nginx config** (proxy everything to Next.js):

```nginx
server {
    listen 80;
    server_name ec2-13-135-109-229.eu-west-2.compute.amazonaws.com;

    # API proxy (if Django runs on 8000)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy everything else (including /_next/static) to Next.js
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**If you must serve static files directly**, ensure correct MIME types and path:

```nginx
# Include MIME types (usually in http block)
include /etc/nginx/mime.types;
default_type application/octet-stream;

# Explicit JS MIME type
types {
    application/javascript js mjs;
}

location /_next/static/ {
    alias /var/www/VALClean/frontend/.next/static/;
    # Or for standalone: alias /var/www/VALClean/frontend/.next/standalone/.next/static/;
    add_header Cache-Control "public, max-age=31536000, immutable";
}
```

**After changing Nginx:** `sudo nginx -t && sudo systemctl reload nginx`

**Clear browser cache** (hard refresh: Ctrl+Shift+R) after fixing.

---

## 🔄 Rollback Plan (If Deployment Fails)

If something goes wrong, here's how to rollback:

```bash
# Step 1: Stop services
sudo systemctl stop gunicorn
sudo systemctl stop multibook-frontend

# Step 2: Restore code from backup
cd /path/to
rm -rf MultiBook
tar -xzf multibook-backup-YYYYMMDD-HHMMSS.tar.gz

# Step 3: Restore database (if needed)
cd MultiBook/backend
python manage.py loaddata backup-YYYYMMDD-HHMMSS.json

# Step 4: Rollback migrations (if needed)
python manage.py migrate accounts 0003
python manage.py migrate customers 0001
python manage.py migrate staff 0003
python manage.py migrate services 0002
python manage.py migrate appointments 0003
python manage.py migrate orders 0002
python manage.py migrate subscriptions 0002
python manage.py migrate coupons 0001

# Step 5: Restart services
sudo systemctl start gunicorn
sudo systemctl start multibook-frontend
sudo systemctl reload nginx
```

---

## 📊 Expected Changes After Deployment

After successful deployment, your database will have:

✅ **80 new CHECK constraints** protecting data integrity  
✅ **8 new migration files** applied  
✅ **Coupon management** feature available  
✅ **Optimized queries** reducing N+1 problems  
✅ **Enhanced validation** at database level  

---

## 📞 Support Commands

```bash
# Check Django version
python -c "import django; print(django.get_version())"

# Check all installed apps
python manage.py showmigrations

# Check database tables
python manage.py dbshell -c "\dt"

# View constraint details
python manage.py dbshell -c "\d orders_order"

# Check server resources
free -h
df -h
top -n 1
```

---

## ✅ Deployment Checklist

- [ ] SSH into AWS server
- [ ] Navigate to project directory
- [ ] Backup current code
- [ ] Backup database
- [ ] Pull latest changes from GitHub
- [ ] Update backend dependencies
- [ ] Run database migrations
- [ ] Test database constraints
- [ ] Build frontend
- [ ] Restart backend services
- [ ] Restart frontend services
- [ ] Restart Nginx
- [ ] Clear cache
- [ ] Verify all services running
- [ ] Test critical features
- [ ] Monitor logs for 10 minutes
- [ ] Test from browser
- [ ] Update documentation

---

**Deployment Time Estimate:** 20-30 minutes  
**Downtime:** 2-5 minutes (during service restart)  
**Risk Level:** Low (migrations are additive, no data loss)

Good luck with your deployment! 🚀

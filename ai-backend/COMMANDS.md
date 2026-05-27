# MindNest AI Backend — Production Command Reference

## Startup Commands

### Local Development
```bash
python app.py
```

### Local Testing with Gunicorn
```bash
gunicorn --config gunicorn_config.py wsgi:app
```

### Docker (Recommended)
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart API service
docker-compose restart api
```

### Linux Systemd
```bash
# Start service
sudo systemctl start mindnest-api

# Stop service
sudo systemctl stop mindnest-api

# Restart service
sudo systemctl restart mindnest-api

# Check status
sudo systemctl status mindnest-api
```

---

## Verification Commands

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Model Information
```bash
curl http://localhost:5000/api/model-info
```

### Test Analysis (Sample Request)
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"I feel amazing today!"}'
```

### Test Wellness Chat
```bash
curl -X POST http://localhost:5000/api/wellness-chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How can I manage anxiety?"}'
```

---

## Logging Commands

### View Real-time Logs
```bash
# Docker
docker-compose logs -f api

# Local (tail)
tail -f logs/mindnest.log

# Systemd
journalctl -u mindnest-api -f

# Last 100 lines
journalctl -u mindnest-api -n 100
```

### Search Logs
```bash
# Find errors
grep ERROR logs/mindnest.log

# Find warnings
grep WARNING logs/mindnest.log

# Find specific endpoint
grep "/api/analyze" logs/mindnest.log

# Count requests
grep -c "INFO in" logs/mindnest.log
```

### Log Rotation
```bash
# Docker (auto-handled)
# Local - files automatically rotate at 10MB

# Manual cleanup
rm logs/mindnest.log.*
```

---

## Database Commands

### PostgreSQL (Docker)
```bash
# Access PostgreSQL container
docker-compose exec postgres psql -U mindnest -d mindnest

# Backup database
docker-compose exec postgres pg_dump mindnest > backup.sql

# Restore database
docker-compose exec -T postgres psql mindnest < backup.sql

# Useful SQL commands:
# List all entries: SELECT * FROM journal_entry;
# Count entries: SELECT COUNT(*) FROM journal_entry;
# Recent entries: SELECT * FROM journal_entry ORDER BY date DESC LIMIT 10;
# Delete old entries: DELETE FROM journal_entry WHERE date < NOW() - INTERVAL '30 days';
```

### SQLite (Local)
```bash
# Access SQLite
sqlite3 mindnest.db

# Backup
cp mindnest.db mindnest.db.backup

# Vacuum (cleanup)
sqlite3 mindnest.db "VACUUM;"
```

---

## Performance & Monitoring

### Check Resource Usage
```bash
# CPU & Memory (Gunicorn)
ps aux | grep gunicorn

# Docker containers
docker stats

# Open file handles
lsof -i :5000
```

### Stress Test Endpoint
```bash
# Using Apache Bench
ab -n 100 -c 10 http://localhost:5000/api/health

# Using curl in loop
for i in {1..100}; do curl http://localhost:5000/api/health > /dev/null 2>&1; done
```

### Monitor Rate Limiting
```bash
# Make multiple requests and watch rate limit headers
for i in {1..35}; do 
  echo "Request $i:"
  curl -I http://localhost:5000/api/analyze 2>/dev/null | grep -i "ratelimit\|remaining"
done
```

---

## Configuration Management

### Update Environment Variables
```bash
# Docker - edit .env and restart
nano .env
docker-compose up -d api

# Systemd - edit /opt/mindnest/.env
sudo nano /opt/mindnest/.env
sudo systemctl restart mindnest-api

# Local - set environment variable
export FLASK_ENV=production
python app.py
```

### Verify Configuration
```bash
# Check if API started correctly
curl http://localhost:5000/api/health

# Check environment
echo $FLASK_ENV
echo $GEMINI_API_KEY
```

---

## Debugging Commands

### Test API Endpoints
```bash
# POST request with data
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"Sample text"}'

# With error handling
curl -v http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"invalid":"data"}' 2>&1 | head -20
```

### Check Process Information
```bash
# Gunicorn processes
ps aux | grep gunicorn

# Port usage
lsof -i :5000

# Kill hung process
kill -9 <PID>
```

### Test Database Connection
```bash
# Test PostgreSQL
python -c "import psycopg2; print('Connected')"

# Test Flask app
python -c "from app import db; print(db.engine.url)"
```

### Check Model Status
```bash
python -c "
import joblib
model = joblib.load('model/emotion_classifier.pkl')
print('✅ Model loaded successfully')
print(f'Classes: {model[\"classes\"]}')
print(f'Accuracy: {model.get(\"accuracy\", 0):.2%}')
"
```

---

## Maintenance Commands

### Clean Up Docker
```bash
# Remove unused containers
docker container prune -f

# Remove unused images
docker image prune -f

# Full cleanup (careful!)
docker system prune -a --volumes
```

### Clean Up Logs
```bash
# Archive old logs
tar -czf logs/mindnest-$(date +%Y%m%d).tar.gz logs/*.log

# Remove old log backups (keep last 30 days)
find logs/ -name "mindnest.log.*" -mtime +30 -delete
```

### Database Maintenance
```bash
# PostgreSQL vacuum (optimize)
docker-compose exec postgres vacuumdb mindnest

# SQLite vacuum
sqlite3 mindnest.db "VACUUM;"
```

---

## Deployment Workflow

### Update & Redeploy
```bash
# 1. Update code
git pull origin main

# 2. Install new dependencies
pip install -r requirements.txt

# 3. Restart service
docker-compose restart api
# OR
sudo systemctl restart mindnest-api

# 4. Verify
curl http://localhost:5000/api/health
```

### Rollback
```bash
# Docker - switch to previous image
docker-compose down
git checkout HEAD~1
docker-compose up -d

# Systemd
git checkout HEAD~1
sudo systemctl restart mindnest-api
```

### Zero-Downtime Deployment (Multiple Instances)
```bash
# 1. Update code on new instance
# 2. Start new service
docker-compose -f docker-compose.v2.yml up -d api_v2

# 3. Switch load balancer to new instance
# 4. Gracefully stop old instance
docker-compose stop api

# 5. Verify
curl http://localhost:5000/api/health
```

---

## Emergency Commands

### Service is Down
```bash
# Check status
sudo systemctl status mindnest-api

# View error logs
journalctl -u mindnest-api -n 50

# Restart
sudo systemctl restart mindnest-api

# Check if port is free
lsof -i :5000
```

### Port Already in Use
```bash
# Find process using port
lsof -i :5000

# Kill process
kill -9 <PID>

# Change port (temporary)
GUNICORN_BIND=0.0.0.0:5001 gunicorn wsgi:app
```

### Database Connection Lost
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# Wait for it to be ready
docker-compose exec postgres pg_isready -U mindnest
```

### High Memory Usage
```bash
# Check memory usage
docker stats

# Reduce workers
GUNICORN_WORKERS=2 gunicorn wsgi:app

# Check for memory leaks in logs
grep -i "memory\|leak" logs/mindnest.log
```

---

## Performance Tuning

### Optimize Gunicorn
```bash
# Increase workers (for CPU-bound)
GUNICORN_WORKERS=16 gunicorn wsgi:app

# Increase timeouts (for slow models)
gunicorn --timeout 300 wsgi:app

# Use sync worker (default, good for I/O)
gunicorn --worker-class sync wsgi:app
```

### Optimize Database
```bash
# Enable query logging (PostgreSQL)
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();

# Create indexes
docker-compose exec postgres psql -U mindnest -d mindnest \
  -c "CREATE INDEX idx_mood ON journal_entry(mood);"
```

### Enable Caching
```bash
# Redis cache (docker-compose handles this)
# Use REDIS_URL in .env

# Check Redis
redis-cli PING
redis-cli INFO
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start server | `python app.py` or `docker-compose up -d` |
| Check health | `curl http://localhost:5000/api/health` |
| View logs | `docker-compose logs -f api` or `tail -f logs/mindnest.log` |
| Restart service | `docker-compose restart api` |
| Stop service | `docker-compose down` |
| Test API | `curl -X POST http://localhost:5000/api/analyze -H "Content-Type: application/json" -d '{"text":"test"}'` |
| Database backup | `docker-compose exec postgres pg_dump mindnest > backup.sql` |
| Check processes | `ps aux \| grep gunicorn` |
| Monitor stats | `docker stats` |

---

## Support & Resources

- **Logs**: Check `logs/mindnest.log` for detailed errors
- **Health Check**: `GET /api/health` for service status
- **Model Info**: `GET /api/model-info` for model details
- **Documentation**: See `PRODUCTION.md` and `DEPLOYMENT.md`

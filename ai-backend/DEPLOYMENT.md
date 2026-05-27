# MindNest AI Backend — Production Deployment Guide

## Overview

This guide covers deploying the MindNest AI backend to production with enterprise-grade reliability, security, and scalability.

## Prerequisites

- Python 3.9+
- PostgreSQL (recommended for production) or SQLite
- Redis (optional, for rate limiting and caching)
- Gunicorn or similar WSGI server
- Nginx (reverse proxy)
- SSL/TLS certificates (Let's Encrypt recommended)

## Quick Start - Local Production Mode

```bash
# Set environment
export FLASK_ENV=production
export SECRET_KEY="your-secret-key-here"
export GEMINI_API_KEY="your-api-key"

# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn --config gunicorn_config.py wsgi:app
```

## Deployment Strategies

### Option 1: Docker (Recommended)

```bash
# Build Docker image
docker build -t mindnest-api:latest .

# Run container
docker run -d \
  -p 5000:5000 \
  -e FLASK_ENV=production \
  -e SECRET_KEY="your-secret" \
  -e GEMINI_API_KEY="your-key" \
  -v /data/mindnest:/app/instance \
  mindnest-api:latest
```

### Option 2: Gunicorn + Nginx

```bash
# Start Gunicorn service (systemd)
sudo systemctl start mindnest-api
sudo systemctl enable mindnest-api

# Nginx configuration (reverse proxy on port 80/443)
upstream mindnest_api {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    listen 443 ssl http2;
    server_name api.mindnest.com;
    
    ssl_certificate /etc/letsencrypt/live/api.mindnest.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.mindnest.com/privkey.pem;
    
    location / {
        proxy_pass http://mindnest_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Option 3: Cloud Platforms

#### AWS (EC2 + RDS + ALB)
```bash
# EC2 user data script
#!/bin/bash
apt-get update
apt-get install -y python3 python3-pip nginx supervisor
git clone https://github.com/your-repo/mindnest.git
cd mindnest/ai-backend
pip install -r requirements.txt
sudo supervisorctl restart mindnest
```

#### Google Cloud Run
```bash
gcloud run deploy mindnest-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars FLASK_ENV=production,GEMINI_API_KEY=... \
  --memory 2Gi \
  --cpu 2
```

#### Heroku
```bash
heroku create mindnest-api
heroku config:set FLASK_ENV=production GEMINI_API_KEY=...
git push heroku main
```

## Environment Configuration

Create a `.env` file (see `.env.example`):

```bash
# Core
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/mindnest

# AI Services
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-2.5-flash

# Server
GUNICORN_WORKERS=8
GUNICORN_BIND=0.0.0.0:5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/mindnest/app.log

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Redis (optional, for rate limiting)
REDIS_URL=redis://localhost:6379/0
```

## Security Best Practices

### 1. SSL/TLS
```bash
# Let's Encrypt (free)
sudo certbot certonly --standalone -d api.mindnest.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### 2. Secrets Management
```bash
# Use environment variables (not hardcoded)
# Better: Use secrets manager
# AWS Secrets Manager, Google Secret Manager, HashiCorp Vault, etc.
```

### 3. Database
```bash
# Strong credentials
psql -U postgres
CREATE USER mindnest WITH PASSWORD 'strong-random-password';
CREATE DATABASE mindnest OWNER mindnest;
GRANT ALL PRIVILEGES ON DATABASE mindnest TO mindnest;

# Regular backups
pg_dump mindnest > /backups/mindnest-$(date +%Y%m%d).sql
```

### 4. Rate Limiting
Already configured in `app.py`:
- `/api/analyze`: 30 requests/minute
- `/api/wellness-chat`: 30 requests/minute
- `/api/rag-query`: 20 requests/minute
- Default: 50 requests/hour

### 5. CORS
Update `CORS_ORIGINS` in `.env` to your frontend domain only:
```
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Monitoring & Logging

### Structured Logging
All requests and errors are logged to:
- Console (stdout)
- File: `/var/log/mindnest/app.log` (rotated daily, 10MB max)

### Health Check Endpoint
```bash
curl http://localhost:5000/api/health

# Response:
{
  "status": "healthy",
  "timestamp": "2025-05-20T10:30:00",
  "environment": "production",
  "model_loaded": true,
  "rag_enabled": true,
  "gemini_enabled": true
}
```

### Performance Monitoring
```bash
# Using New Relic
pip install newrelic
NEW_RELIC_CONFIG_FILE=newrelic.ini \
  newrelic-admin run-program gunicorn wsgi:app

# Using DataDog
pip install datadog
# Configure in app
```

## Database Migrations

```bash
# Initialize database
python -c "from app import db; db.create_all()"

# For larger deployments, use Alembic
pip install Flask-Migrate
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

## Scaling

### Horizontal Scaling
```bash
# Multiple Gunicorn instances behind Nginx (load balancing)
# Gunicorn workers: 2N+1 (where N = CPU cores)
workers = 9  # For 4-core machine
```

### Vertical Scaling
- Increase Gunicorn workers
- Use PostgreSQL instead of SQLite
- Enable Redis for rate limiting + caching
- Use CDN for static assets

### Load Testing
```bash
# Apache Bench
ab -n 1000 -c 10 http://localhost:5000/api/health

# Locust
locust -f locustfile.py --host=http://localhost:5000
```

## Troubleshooting

### Port Already in Use
```bash
lsof -i :5000
kill -9 <PID>
```

### Model Not Loading
```bash
# Check file exists
ls -la model/emotion_classifier.pkl

# Re-train if needed
python train_model.py
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U mindnest -d mindnest

# Check database URL format
postgresql://user:password@host:5432/database
```

### High Memory Usage
```bash
# Reduce Gunicorn workers
export GUNICORN_WORKERS=4

# Monitor memory
ps aux | grep gunicorn
```

## Performance Checklist

- [x] Environment-based configuration (dev/prod)
- [x] Structured logging
- [x] Error handling & recovery
- [x] Rate limiting (30 req/min per endpoint)
- [x] Security headers (HSTS, CSP, X-Frame-Options)
- [x] CORS properly configured
- [x] Database connection pooling
- [x] Request validation
- [x] Health check endpoint
- [x] WSGI server (Gunicorn/Waitress)

## Next Steps

1. **Database**: Migrate from SQLite to PostgreSQL
2. **Caching**: Add Redis for rate limiting + response caching
3. **Monitoring**: Integrate APM (New Relic, DataDog, Sentry)
4. **CI/CD**: GitHub Actions, GitLab CI, or Jenkins
5. **Containerization**: Docker + Kubernetes for scale
6. **Testing**: Add unit/integration tests with pytest

## Support

For issues or questions:
- Check logs: `/var/log/mindnest/app.log`
- Health check: `GET /api/health`
- Model info: `GET /api/model-info`

# MindNest AI Backend — Quick Production Start

## Installation & Setup

### 1. Environment Setup

```bash
# Clone/navigate to project
cd MindNest/ai-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required environment variables:**
```env
FLASK_ENV=production
SECRET_KEY=your-secure-random-key
GEMINI_API_KEY=your-google-api-key
DATABASE_URL=sqlite:///mindnest.db  # or PostgreSQL for production
```

### 3. Run in Production Mode

#### Option A: Local Testing (Waitress)
```bash
python app.py
# Server starts on http://localhost:5000
```

#### Option B: Production (Gunicorn)
```bash
pip install gunicorn
gunicorn --config gunicorn_config.py wsgi:app
```

#### Option C: Docker
```bash
docker-compose up -d

# Access via http://localhost:5000
# Check health: curl http://localhost:5000/api/health
```

## Verification

### Health Check
```bash
curl http://localhost:5000/api/health

# Expected response:
{
  "status": "healthy",
  "environment": "production",
  "model_loaded": true,
  "rag_enabled": true,
  "gemini_enabled": true
}
```

### Model Info
```bash
curl http://localhost:5000/api/model-info
```

### Test Analysis
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I am feeling great today!"
  }'
```

## Security Checklist

- [ ] **SECRET_KEY** — Changed from default value
- [ ] **HTTPS** — SSL certificates configured
- [ ] **CORS** — Restricted to your frontend domain
- [ ] **Rate Limiting** — Enabled (default: 30 req/min)
- [ ] **Database** — Using PostgreSQL (not SQLite) for production
- [ ] **Logging** — Configured with rotation (see `logs/` directory)
- [ ] **API Keys** — Stored in `.env`, never in code
- [ ] **GEMINI_API_KEY** — Set and working
- [ ] **Secrets** — Using environment variables only
- [ ] **Backups** — Database backed up daily

## Performance Optimization

### Database
```bash
# For production, use PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/mindnest

# Enable connection pooling (automatic with SQLAlchemy)
```

### Caching & Rate Limiting
```bash
# Use Redis for better rate limiting
REDIS_URL=redis://localhost:6379/0

# Install Redis (Docker recommended)
docker run -d -p 6379:6379 redis:7-alpine
```

### Worker Scaling
```bash
# Gunicorn workers = (2 × CPU cores) + 1
# For 4-core server: 9 workers
GUNICORN_WORKERS=9
```

## Logging

### View Logs
```bash
# Docker
docker-compose logs -f api

# Local
tail -f logs/mindnest.log

# Systemd
journalctl -u mindnest-api -f
```

### Log Levels
- **DEBUG**: Development only
- **INFO**: Production (default)
- **WARNING**: Warnings & issues
- **ERROR**: Critical errors

## Monitoring

### Key Metrics
- Request count & latency
- Error rate
- Model accuracy (see `/api/model-info`)
- RAG availability
- Gemini API status

### Health Endpoint (Automated Monitoring)
```bash
# Monitor every 30 seconds
watch -n 30 'curl -s http://localhost:5000/api/health | jq'
```

## Troubleshooting

### Port Already in Use
```bash
lsof -i :5000
kill -9 <PID>
```

### Model Not Found
```bash
# Train the model first
python train_model.py

# Verify model exists
ls -la model/emotion_classifier.pkl
```

### Gemini API Issues
```bash
# Verify API key
echo $GEMINI_API_KEY

# Test connection
python -c "from google import genai; print('OK')"
```

### High Memory Usage
```bash
# Reduce workers
export GUNICORN_WORKERS=4

# Monitor memory
ps aux | grep gunicorn
```

## Scaling to Production

### Phase 1: Single Server
- ✅ Gunicorn + Waitress
- ✅ SQLite (local testing only)
- ✅ Simple logging

### Phase 2: High Availability
- 🔄 PostgreSQL + connection pooling
- 🔄 Redis for caching + rate limiting
- 🔄 Nginx load balancing
- 🔄 Structured logging (ELK/Splunk)

### Phase 3: Enterprise Scale
- 📊 Kubernetes / Docker Swarm
- 📊 Multiple replicas
- 📊 APM (New Relic, DataDog)
- 📊 CDN for static assets
- 📊 Database replication
- 📊 Auto-scaling

## Useful Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f api

# Restart service
docker-compose restart api

# Update configuration
# Edit .env, then:
docker-compose up -d api

# Backup database
docker-compose exec postgres pg_dump mindnest > backup.sql

# Restore database
docker-compose exec -T postgres psql mindnest < backup.sql
```

## Next Steps

1. **Database Migration** → Use PostgreSQL instead of SQLite
2. **Monitoring** → Add New Relic or DataDog
3. **CI/CD** → GitHub Actions for automated deployments
4. **Testing** → Add pytest unit/integration tests
5. **Documentation** → API docs with Swagger/OpenAPI
6. **Load Testing** → Use Locust to stress-test endpoints

## Support Resources

- **API Documentation**: `GET /api/model-info`
- **Health Status**: `GET /api/health`
- **Production Guide**: See `DEPLOYMENT.md`
- **Configuration**: See `.env.example`
- **Logs**: Check `logs/mindnest.log`

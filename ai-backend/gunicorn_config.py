"""
Gunicorn configuration for Render deployment.
Use with: gunicorn --config gunicorn_config.py wsgi:app
"""

import os

# Server socket — Render sets PORT dynamically
port = os.getenv("PORT", "5000")
bind = f"0.0.0.0:{port}"

# Worker processes — keep at 1 for free tier memory limits
workers = int(os.getenv("GUNICORN_WORKERS", "1"))
worker_class = "sync"
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Process naming
proc_name = "mindnest-api"

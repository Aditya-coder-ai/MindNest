"""
Gunicorn configuration for production deployment.
Use with: gunicorn --config gunicorn_config.py wsgi:app
"""

import os
import multiprocessing

# Server socket — Railway sets PORT dynamically
port = os.getenv("PORT", "5000")
bind = os.getenv("GUNICORN_BIND", f"0.0.0.0:{port}")
backlog = 2048

# Worker processes — keep low for Railway free tier memory limits
workers = int(os.getenv("GUNICORN_WORKERS", min(multiprocessing.cpu_count() * 2 + 1, 2)))
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "mindnest-api"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = os.getenv("GUNICORN_KEYFILE", None)
certfile = os.getenv("GUNICORN_CERTFILE", None)
ssl_version = 2
cert_reqs = 0
ca_certs = None

# Application
paste = None
on_starting = None
when_ready = None
on_exit = None

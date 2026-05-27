"""
WSGI entry point for production deployment (Gunicorn, Waitress, etc.)
"""

import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    app.run()

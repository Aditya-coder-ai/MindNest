"""
Production-level configuration management for MindNest AI backend.
Supports development, testing, and production environments.
"""

import os
from datetime import timedelta

# ═════════════════════════════════════════════════════════════════
#  Environment & Base Config
# ═════════════════════════════════════════════════════════════════

ENV = os.getenv("FLASK_ENV", "production").lower()
DEBUG = ENV == "development"


class Config:
    """Base configuration for all environments."""
    
    # Flask
    FLASK_ENV = ENV
    DEBUG = DEBUG
    TESTING = False
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "prod-secret-key-change-in-production")
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        "sqlite:///mindnest.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }
    
    # CORS — allow Firebase frontend + local dev by default
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS", 
        "https://mindnest-de930.web.app,http://localhost:5173,http://localhost:5000"
    ).split(",")
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]
    CORS_EXPOSE_HEADERS = ["X-Total-Count"]
    
    # API
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = DEBUG
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv("REDIS_URL", "memory://")
    RATELIMIT_ENABLED = True
    
    # AI Models
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")
    LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    LOG_FILE = os.getenv("LOG_FILE", "logs/mindnest.log")
    
    # Model paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, "model", "emotion_classifier.pkl")


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    TESTING = False


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False


# ═════════════════════════════════════════════════════════════════
#  Configuration selector
# ═════════════════════════════════════════════════════════════════

def get_config():
    """Get configuration object based on FLASK_ENV."""
    configs = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }
    return configs.get(ENV, ProductionConfig)

"""
Logging configuration for MindNest AI backend.
Provides structured logging with file and console handlers.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from config import Config


def setup_logging(app):
    """Configure logging for Flask application."""
    
    # Ensure logs directory exists
    log_dir = os.path.dirname(Config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Remove default Flask logger handlers
    app.logger.handlers.clear()
    
    # Create logger
    logger = logging.getLogger("mindnest")
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Formatter
    formatter = logging.Formatter(Config.LOG_FORMAT)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler with rotation
    if Config.LOG_FILE:
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("flask").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return logger


def get_logger(name):
    """Get a logger instance by name."""
    return logging.getLogger(f"mindnest.{name}")

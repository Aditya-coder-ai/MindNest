"""
Error handling and utility middleware for production API.
"""

from flask import jsonify, request
from functools import wraps
from logger_config import get_logger
import traceback

logger = get_logger("errors")


class APIError(Exception):
    """Custom API error class for structured error responses."""
    
    def __init__(self, message, status_code=400, error_code=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "API_ERROR"
    
    def to_dict(self):
        return {
            "error": self.message,
            "errorCode": self.error_code,
            "status": self.status_code,
        }


def handle_errors(app):
    """Register error handlers with Flask app."""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = error.to_dict()
        logger.warning(f"API Error: {error.message} ({error.error_code})")
        return jsonify(response), error.status_code
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        logger.warning(f"Bad Request: {error}")
        return jsonify({
            "error": "Bad Request",
            "errorCode": "BAD_REQUEST",
            "status": 400,
        }), 400
    
    @app.errorhandler(404)
    def handle_not_found(error):
        logger.warning(f"Not Found: {request.path}")
        return jsonify({
            "error": "Endpoint not found",
            "errorCode": "NOT_FOUND",
            "status": 404,
        }), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal Server Error: {error}\n{traceback.format_exc()}")
        return jsonify({
            "error": "Internal server error",
            "errorCode": "INTERNAL_ERROR",
            "status": 500,
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unhandled_exception(error):
        logger.error(f"Unhandled Exception: {error}\n{traceback.format_exc()}")
        return jsonify({
            "error": "Internal server error",
            "errorCode": "INTERNAL_ERROR",
            "status": 500,
        }), 500


def validate_request(required_fields=None):
    """Decorator to validate JSON request and required fields."""
    required_fields = required_fields or []
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if request has JSON
            if not request.is_json:
                raise APIError(
                    "Request must be JSON",
                    status_code=400,
                    error_code="INVALID_CONTENT_TYPE"
                )
            
            data = request.get_json()
            
            # Check required fields
            for field in required_fields:
                if field not in data or not data[field]:
                    raise APIError(
                        f"Missing required field: {field}",
                        status_code=400,
                        error_code="MISSING_FIELD"
                    )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_request(app):
    """Log all incoming requests."""
    
    @app.before_request
    def before_request():
        logger.debug(f"{request.method} {request.path} from {request.remote_addr}")
    
    @app.after_request
    def after_request(response):
        logger.debug(f"Response: {request.method} {request.path} - {response.status_code}")
        return response

"""
Error handling middleware for the Multi-Agent Jira Card Creator application.
Provides comprehensive error handling, logging, and user-friendly error responses.
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class ApplicationError(Exception):
    """Base application error with context and user-friendly messaging."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.user_message = user_message or message
        self.error_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()


class ValidationError(ApplicationError):
    """Validation error for input validation failures."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field, "value": str(value) if value else None},
            user_message=f"Invalid input: {message}"
        )


class ConfigurationError(ApplicationError):
    """Configuration error for missing or invalid configuration."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details={"config_key": config_key},
            user_message="System configuration error. Please check the application setup."
        )


class ExternalServiceError(ApplicationError):
    """Error for external service failures (AWS, Jira, etc.)."""
    
    def __init__(self, message: str, service: str, operation: str = None):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service, "operation": operation},
            user_message=f"External service unavailable: {service}. Please try again later."
        )


class RepositoryError(ApplicationError):
    """Error for repository scanning and analysis failures."""
    
    def __init__(self, message: str, repository: str = None, operation: str = None):
        super().__init__(
            message=message,
            error_code="REPOSITORY_ERROR",
            status_code=400,
            details={"repository": repository, "operation": operation},
            user_message=f"Repository processing error: {message}"
        )


class DatabaseError(ApplicationError):
    """Error for database connection and query failures."""
    
    def __init__(self, message: str, operation: str = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details={"operation": operation},
            user_message="Database connection error. Please check your database configuration."
        )


class AgentError(ApplicationError):
    """Error for AI agent processing failures."""
    
    def __init__(self, message: str, agent_type: str = None, step: str = None):
        super().__init__(
            message=message,
            error_code="AGENT_ERROR",
            status_code=500,
            details={"agent_type": agent_type, "step": step},
            user_message="AI agent processing failed. Please try again or contact support."
        )


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Comprehensive error handling middleware."""
    
    async def dispatch(self, request: Request, call_next):
        """Handle all requests with comprehensive error catching."""
        
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown"
        )
        
        try:
            response = await call_next(request)
            
            # Log successful response
            logger.info(
                "Request completed",
                request_id=request_id,
                status_code=response.status_code
            )
            
            return response
            
        except ApplicationError as e:
            # Handle known application errors
            logger.error(
                "Application error",
                request_id=request_id,
                error_id=e.error_id,
                error_code=e.error_code,
                message=e.message,
                details=e.details,
                status_code=e.status_code
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "error_id": e.error_id,
                        "error_code": e.error_code,
                        "message": e.user_message,
                        "details": e.details,
                        "timestamp": e.timestamp,
                        "request_id": request_id
                    }
                }
            )
            
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            error_id = str(uuid.uuid4())
            
            logger.warning(
                "HTTP exception",
                request_id=request_id,
                error_id=error_id,
                status_code=e.status_code,
                detail=e.detail
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "error_id": error_id,
                        "error_code": "HTTP_ERROR",
                        "message": str(e.detail),
                        "details": {},
                        "timestamp": datetime.utcnow().isoformat(),
                        "request_id": request_id
                    }
                }
            )
            
        except Exception as e:
            # Handle unexpected errors
            error_id = str(uuid.uuid4())
            
            logger.error(
                "Unexpected error",
                request_id=request_id,
                error_id=error_id,
                error_type=type(e).__name__,
                message=str(e),
                traceback=traceback.format_exc()
            )
            
            # Don't expose internal errors to users in production
            user_message = "An unexpected error occurred. Please try again or contact support."
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "error_id": error_id,
                        "error_code": "INTERNAL_ERROR",
                        "message": user_message,
                        "details": {"error_type": type(e).__name__},
                        "timestamp": datetime.utcnow().isoformat(),
                        "request_id": request_id
                    }
                }
            )


def validate_required_config(config: Dict[str, Any], required_keys: list) -> None:
    """Validate that required configuration keys are present and not empty."""
    
    missing_keys = []
    empty_keys = []
    
    for key in required_keys:
        if key not in config:
            missing_keys.append(key)
        elif not config[key] or (isinstance(config[key], str) and not config[key].strip()):
            empty_keys.append(key)
    
    if missing_keys or empty_keys:
        details = {}
        if missing_keys:
            details["missing_keys"] = missing_keys
        if empty_keys:
            details["empty_keys"] = empty_keys
            
        raise ConfigurationError(
            f"Required configuration missing: {missing_keys + empty_keys}",
            config_key=", ".join(missing_keys + empty_keys)
        )


def validate_repository_path(path: str) -> None:
    """Validate repository path exists and is accessible."""
    
    import os
    
    if not path:
        raise ValidationError("Repository path cannot be empty", "repositories_path")
    
    if not os.path.exists(path):
        raise RepositoryError(
            f"Repository path does not exist: {path}",
            repository=path,
            operation="path_validation"
        )
    
    if not os.path.isdir(path):
        raise RepositoryError(
            f"Repository path is not a directory: {path}",
            repository=path,
            operation="path_validation"
        )
    
    if not os.access(path, os.R_OK):
        raise RepositoryError(
            f"Repository path is not readable: {path}",
            repository=path,
            operation="path_validation"
        )


def validate_context_id(context_id: str) -> None:
    """Validate context ID format."""
    
    if not context_id:
        raise ValidationError("Context ID cannot be empty", "context_id")
    
    if not isinstance(context_id, str):
        raise ValidationError("Context ID must be a string", "context_id", context_id)
    
    # Basic UUID format validation
    import re
    uuid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    if not re.match(uuid_pattern, context_id):
        raise ValidationError("Context ID must be a valid UUID", "context_id", context_id)


def validate_task_request(task_data: Dict[str, Any]) -> None:
    """Validate task creation request data."""
    
    required_fields = ["task_id", "description", "task_type"]
    
    for field in required_fields:
        if field not in task_data:
            raise ValidationError(f"Required field missing: {field}", field)
        
        if not task_data[field] or not str(task_data[field]).strip():
            raise ValidationError(f"Required field cannot be empty: {field}", field)
    
    # Validate task_type
    valid_task_types = ["feature", "bug", "technical", "infrastructure"]
    if task_data["task_type"] not in valid_task_types:
        raise ValidationError(
            f"Invalid task type. Must be one of: {', '.join(valid_task_types)}",
            "task_type",
            task_data["task_type"]
        )
    
    # Validate task_id format
    task_id = task_data["task_id"].strip()
    if len(task_id) < 3:
        raise ValidationError("Task ID must be at least 3 characters long", "task_id", task_id)
    
    if len(task_id) > 50:
        raise ValidationError("Task ID must be no more than 50 characters long", "task_id", task_id)
    
    # Validate description length
    description = task_data["description"].strip()
    if len(description) < 10:
        raise ValidationError("Task description must be at least 10 characters long", "description")
    
    if len(description) > 5000:
        raise ValidationError("Task description must be no more than 5000 characters long", "description")


def safe_external_call(func, *args, service_name: str, operation: str = None, **kwargs):
    """Safely call external services with proper error handling."""
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(
            "External service call failed",
            service=service_name,
            operation=operation,
            error=str(e),
            traceback=traceback.format_exc()
        )
        
        raise ExternalServiceError(
            f"Failed to call {service_name}: {str(e)}",
            service=service_name,
            operation=operation
        )


def log_performance(func):
    """Decorator to log performance metrics."""
    
    import functools
    import time
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__
        
        logger.debug(
            "Function started",
            function=function_name,
            args_count=len(args),
            kwargs_keys=list(kwargs.keys())
        )
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(
                "Function completed",
                function=function_name,
                duration=f"{duration:.3f}s"
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                "Function failed",
                function=function_name,
                duration=f"{duration:.3f}s",
                error=str(e)
            )
            
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__
        
        logger.debug(
            "Function started",
            function=function_name,
            args_count=len(args),
            kwargs_keys=list(kwargs.keys())
        )
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(
                "Function completed",
                function=function_name,
                duration=f"{duration:.3f}s"
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                "Function failed",
                function=function_name,
                duration=f"{duration:.3f}s",
                error=str(e)
            )
            
            raise
    
    if hasattr(func, '__call__'):
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return func
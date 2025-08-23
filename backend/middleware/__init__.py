"""
Middleware package for the Multi-Agent Jira Card Creator application.
"""

from .error_handler import (
    ErrorHandlerMiddleware,
    ApplicationError,
    ValidationError,
    ConfigurationError,
    ExternalServiceError,
    RepositoryError,
    DatabaseError,
    AgentError,
    validate_required_config,
    validate_repository_path,
    validate_context_id,
    validate_task_request,
    safe_external_call,
    log_performance
)

__all__ = [
    "ErrorHandlerMiddleware",
    "ApplicationError",
    "ValidationError",
    "ConfigurationError",
    "ExternalServiceError",
    "RepositoryError",
    "DatabaseError",
    "AgentError",
    "validate_required_config",
    "validate_repository_path",
    "validate_context_id",
    "validate_task_request",
    "safe_external_call",
    "log_performance"
]
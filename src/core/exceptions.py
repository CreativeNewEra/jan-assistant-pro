"""
Custom exception classes for Jan Assistant Pro
Provides structured error handling throughout the application
"""

from typing import Any, Dict, Optional

from .user_friendly_error import UserFriendlyError

from .error_reporter import record_error


class JanAssistantError(Exception):
    """Base exception for all Jan Assistant Pro errors"""
    
    def __init__(self, message: str, error_code: str = None, 
                 context: Dict[str, Any] = None):
        """
        Initialize exception with structured error information
        
        Args:
            message: Human-readable error message
            error_code: Unique error code for programmatic handling
            context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization"""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'context': self.context
        }


class ConfigurationError(JanAssistantError):
    """Raised when configuration is invalid or missing"""
    pass


class APIError(JanAssistantError):
    """Raised when API communication fails"""
    
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_data: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_data = response_data
        self.context.update({
            'status_code': status_code,
            'response_data': response_data
        })


class ToolError(JanAssistantError):
    """Raised when tool execution fails"""
    
    def __init__(self, message: str, tool_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.tool_name = tool_name
        if tool_name:
            self.context['tool_name'] = tool_name


class FileOperationError(ToolError):
    """Raised when file operations fail"""
    
    def __init__(self, message: str, file_path: str = None, 
                 operation: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.file_path = file_path
        self.operation = operation
        self.context.update({
            'file_path': file_path,
            'operation': operation
        })


class SecurityError(JanAssistantError):
    """Raised when security violations are detected"""
    
    def __init__(self, message: str, violation_type: str = None, 
                 attempted_action: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.violation_type = violation_type
        self.attempted_action = attempted_action
        self.context.update({
            'violation_type': violation_type,
            'attempted_action': attempted_action
        })


class MemoryError(JanAssistantError):
    """Raised when memory operations fail"""
    pass


class ValidationError(JanAssistantError):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field_name: str = None, 
                 field_value: Any = None, **kwargs):
        super().__init__(message, **kwargs)
        self.field_name = field_name
        self.field_value = field_value
        self.context.update({
            'field_name': field_name,
            'field_value': str(field_value) if field_value is not None else None
        })


class RetryableError(JanAssistantError):
    """Base class for errors that can be retried"""
    
    def __init__(self, message: str, max_retries: int = 3, 
                 retry_delay: float = 1.0, **kwargs):
        super().__init__(message, **kwargs)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.context.update({
            'max_retries': max_retries,
            'retry_delay': retry_delay
        })


class NetworkError(RetryableError):
    """Raised when network operations fail"""
    pass


class ResourceError(JanAssistantError):
    """Raised when system resources are unavailable"""
    
    def __init__(self, message: str, resource_type: str = None, 
                 resource_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.context.update({
            'resource_type': resource_type,
            'resource_name': resource_name
        })


def to_user_friendly_error(exc: Exception) -> UserFriendlyError:
    """Convert an exception into a UserFriendlyError instance."""
    if isinstance(exc, JanAssistantError):
        message = exc.message
    else:
        message = str(exc)

    suggestions: list[str] = []
    doc_link: str | None = None
    if isinstance(exc, PermissionError) or (
        isinstance(exc, FileOperationError) and isinstance(exc.__cause__, PermissionError)
    ):
        suggestions = [
            "Check file or directory permissions",
            "Try a different path",
        ]
        doc_link = "https://example.com/docs/errors#permissions"
    return UserFriendlyError(
        cause=exc.__class__.__name__,
        user_message=message,
        suggestions=suggestions,
        documentation_link=doc_link,
    )


def handle_exception(exc: Exception) -> Dict[str, Any]:
    """
    Convert any exception to a standardized error response
    
    Args:
        exc: Exception to handle
        
    Returns:
        Standardized error dictionary
    """
    record_error(exc)
    if isinstance(exc, JanAssistantError):
        error_dict = exc.to_dict()
    else:
        error_dict = {
            'error_type': 'UnexpectedError',
            'error_code': 'UNEXPECTED_ERROR',
            'message': str(exc),
            'context': {
                'exception_type': exc.__class__.__name__
            }
        }

    return {
        'success': False,
        'error': error_dict,
        'user_error': to_user_friendly_error(exc).to_dict(),
    }


def create_error_response(message: str, error_code: str = None, 
                         context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a standardized error response
    
    Args:
        message: Error message
        error_code: Optional error code
        context: Optional context information
        
    Returns:
        Standardized error dictionary
    """
    return {
        'success': False,
        'error': {
            'error_type': 'GenericError',
            'error_code': error_code or 'GENERIC_ERROR',
            'message': message,
            'context': context or {}
        },
        'user_error': UserFriendlyError(
            cause='GenericError',
            user_message=message,
            suggestions=[],
            documentation_link=None,
        ).to_dict(),
    }

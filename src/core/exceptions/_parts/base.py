"""
Exception hierarchy for AI Agent Hub V3.
Provides structured error handling across all system layers.
ARCHITECTURE_V3: Core Layer - Error Handling
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field



class HubError(Exception):
    """
    Base exception for all AI Agent Hub errors.
    All custom exceptions should inherit from this.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "HUB_ERROR",
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        super().__init__(message)
    
    def __str__(self) -> str:
        base = f"[{self.error_code}] {self.message}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base += f" | Details: {details_str}"
        if self.original_exception:
            base += f" | Original: {type(self.original_exception).__name__}: {str(self.original_exception)}"
        return base
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "exception_type": self.__class__.__name__,
            "original_exception": str(self.original_exception) if self.original_exception else None
        }

class ConfigurationError(HubError):
    """Errors related to configuration."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        if config_value:
            details["config_value"] = config_value
        
        error_code = kwargs.pop("error_code", "CONFIGURATION_ERROR")
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )



class EnvironmentError(ConfigurationError):
    """Errors related to environment variables."""
    
    def __init__(
        self,
        message: str,
        env_var: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if env_var:
            details["env_var"] = env_var
        
        super().__init__(
            message=message,
            config_key=env_var,
            error_code="ENVIRONMENT_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )



class ValidationError(ConfigurationError):
    """Errors related to data validation."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value:
            details["value"] = value
        if expected:
            details["expected"] = expected
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


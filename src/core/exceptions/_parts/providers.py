from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from .base import HubError, ConfigurationError

# ============ PROVIDER ERRORS ============
class ProviderError(HubError):
    """Base error for all provider-related errors."""

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        provider_type: Optional[str] = None,
        error_code: str = "PROVIDER_ERROR",
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        final_details = details or {}
        if provider_name:
            final_details["provider_name"] = provider_name
        if provider_type:
            final_details["provider_type"] = provider_type

        super().__init__(
            message=message,
            error_code=error_code,
            details=final_details,
            original_exception=original_exception,
        )

class LLMError(ProviderError):
    """Errors related to LLM operations."""
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        prompt: Optional[str] = None,
        tokens_used: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if model:
            details["model"] = model
        if prompt:
            # Truncate long prompts in error details
            details["prompt"] = prompt[:100] + "..." if len(prompt) > 100 else prompt
        if tokens_used:
            details["tokens_used"] = tokens_used
        
        error_code = kwargs.pop("error_code", "LLM_ERROR")
        super().__init__(
            message=message,
            provider_type="llm",
            error_code=error_code,
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )



class VectorStoreError(ProviderError):
    """Errors related to vector store operations."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        document_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if operation:
            details["operation"] = operation
        if document_id:
            details["document_id"] = document_id
        
        error_code = kwargs.pop("error_code", "VECTOR_STORE_ERROR")
        super().__init__(
            message=message,
            provider_type="vector_store",
            error_code=error_code,
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )



class EmbeddingError(VectorStoreError):
    """Errors related to embedding generation."""
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        text: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if model:
            details["embedding_model"] = model
        if text:
            details["text"] = text[:50] + "..." if len(text) > 50 else text
        
        error_code = kwargs.pop("error_code", "EMBEDDING_ERROR")
        super().__init__(
            message=message,
            operation="embedding",
            error_code=error_code,
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )

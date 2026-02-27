"""
OpenAI LLM Adapter for AI Agent Hub V3.
Implements LLMProvider contract for OpenAI API.
ARCHITECTURE_V3: Adapters Layer - OpenAI Integration
"""

import asyncio
import json
from typing import List, AsyncGenerator, Dict, Any, Optional
from datetime import datetime

from openai import AsyncOpenAI, APIError, AuthenticationError, RateLimitError
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from src.core.contracts import LLMProvider, LLMCompletion, LLMChunk
from src.core.types import Message, MessageRole, LLMConfig
from src.core.exceptions import LLMError, wrap_exception
from src.adapters.logging_adapter import get_logger


class OpenAIAdapter(LLMProvider):
    """
    OpenAI LLM Provider implementation.
    Supports both completion and streaming modes.
    """
    
    def __init__(self, config: LLMConfig):
        """
        Initialize OpenAI adapter.
        
        Args:
            config: LLM configuration
        """
        self._name = "openai"
        self._config = config
        
        # Initialize OpenAI client
        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries or 3,
        )
        
        # Model-specific context lengths
        self._context_lengths = {
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo": 128000,
            "gpt-4-turbo-preview": 128000,
            "gpt-3.5-turbo": 16385,
            "gpt-3.5-turbo-16k": 16385,
            "gpt-3.5-turbo-instruct": 4096,
        }
        
        self._logger = get_logger()
        
        # Default model if not specified
        self._model = config.model or "gpt-4-turbo-preview"
    
    @property
    def name(self) -> str:
        """Provider name."""
        return self._name
    
    @property
    def context_length(self) -> int:
        """Maximum context length for the current model."""
        # Find the best matching model
        for model_pattern, length in self._context_lengths.items():
            if model_pattern in self._model:
                return length
        
        # Default for unknown models
        return 8192
    
    async def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the provider.
        
        Args:
            config: Configuration dictionary
        """
        try:
            self._config = LLMConfig(**config)
            
            # Reinitialize client with new config
            self._client = AsyncOpenAI(
                api_key=self._config.api_key,
                base_url=self._config.base_url,
                timeout=self._config.timeout,
                max_retries=self._config.max_retries or 3,
            )
            
            if "model" in config:
                self._model = config["model"]
            
            self._logger.info(
                "OpenAI adapter reconfigured",
                context={
                    "model": self._model,
                }
            )
            
        except Exception as e:
            wrapped = wrap_exception(
                e,
                LLMError,
                message="Failed to configure OpenAI adapter",
                model=self._model
            )
            raise wrapped from e
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.
        
        Returns:
            Health status dictionary
        """
        try:
            start_time = datetime.utcnow()
            
            # Simple test request
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
            )
            
            latency = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "model": self._model,
                "latency_seconds": latency,
                "response_id": response.id,
                "provider": self.name,
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self._model,
                "error": str(e),
                "provider": self.name,
            }
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        Convert internal Message objects to OpenAI format.
        
        Args:
            messages: List of Message objects
            
        Returns:
            List of OpenAI message dictionaries
        """
        openai_messages = []
        
        for msg in messages:
            # Convert role
            if msg.role == MessageRole.SYSTEM:
                role = "system"
            elif msg.role == MessageRole.USER:
                role = "user"
            elif msg.role == MessageRole.ASSISTANT:
                role = "assistant"
            elif msg.role == MessageRole.TOOL:
                role = "tool"
            else:
                role = "user"  # Default
            
            # Basic message structure
            message_dict = {
                "role": role,
                "content": msg.content,
            }
            
            # Add name if present
            if msg.metadata and "name" in msg.metadata:
                message_dict["name"] = msg.metadata["name"]
            
            # Handle tool calls
            if msg.tool_calls:
                # For assistant messages with tool calls
                if msg.role == MessageRole.ASSISTANT:
                    message_dict["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments)
                            }
                        }
                        for tc in msg.tool_calls
                    ]
            
            # Handle tool results
            if msg.role == MessageRole.TOOL and msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id
            
            openai_messages.append(message_dict)
        
        return openai_messages


    def _extract_text_from_responses(self, resp: Any) -> str:
        """Best-effort extraction of output text from Responses API result."""
        try:
            # New SDK typically provides output_text
            ot = getattr(resp, "output_text", None)
            if ot:
                return str(ot)
        except Exception:
            pass

        # Fallback: walk output items
        try:
            out = getattr(resp, "output", None) or []
            parts: list[str] = []
            for item in out:
                content = getattr(item, "content", None) or []
                for c in content:
                    if getattr(c, "type", None) == "output_text":
                        parts.append(str(getattr(c, "text", "") or ""))
            if parts:
                return "".join(parts)
        except Exception:
            pass

        return ""
    
    async def complete(
        self,
        messages: List[Message],
        config: Optional[Dict[str, Any]] = None
    ) -> LLMCompletion:
        """
        Generate a completion from messages.
        
        Args:
            messages: List of messages in conversation
            config: Optional configuration overrides
            
        Returns:
            LLMCompletion object
        """
        request_id = f"req_{datetime.utcnow().timestamp()}"
        
        try:
            # Merge configs
            merged_config = self._config.dict() if hasattr(self._config, 'dict') else {}
            if config:
                merged_config.update(config)
            
            # Convert messages
            openai_messages = self._convert_messages(messages)
            
            self._logger.debug(
                "Starting OpenAI completion request",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "message_count": len(messages),
                    "config": {k: v for k, v in merged_config.items() if k != "api_key"}
                }
            )
            
            # Prepare request parameters
            request_params = {
                "model": merged_config.get("model", self._model),
                "messages": openai_messages,
                "temperature": merged_config.get("temperature", 0.7),
                "max_tokens": merged_config.get("max_tokens"),
                "top_p": merged_config.get("top_p", 1.0),
                "frequency_penalty": merged_config.get("frequency_penalty", 0.0),
                "presence_penalty": merged_config.get("presence_penalty", 0.0),
                "stop": merged_config.get("stop_sequences"),
                "stream": False,
            }
            
            # Remove None values
            request_params = {k: v for k, v in request_params.items() if v is not None}
            
            # Make API call
            start_time = datetime.utcnow()
            try:
                response: ChatCompletion = await self._client.chat.completions.create(
                    **request_params
                )
                latency = (datetime.utcnow() - start_time).total_seconds()
            except APIError as e:
                # Some environments/proxies may not support Chat Completions; fallback to Responses API when 404.
                if getattr(e, "status_code", None) == 404:
                    # Responses API input: use a single user message string
                    prompt_text = "\n".join([m.get("content","") for m in openai_messages if m.get("role") == "user"])
                    r2 = await self._client.responses.create(
                        model=request_params.get("model", self._model),
                        input=prompt_text or "Hello",
                    )
                    latency = (datetime.utcnow() - start_time).total_seconds()
                    content = self._extract_text_from_responses(r2) or ""
                    completion = LLMCompletion(
                        content=content,
                        model=getattr(r2, "model", request_params.get("model", self._model)),
                        provider=self.name,
                        tokens_used=int(getattr(getattr(r2, "usage", None), "total_tokens", 0) or 0),
                        finish_reason=str(getattr(r2, "status", "stop") or "stop"),
                        metadata={
                            "id": getattr(r2, "id", None),
                            "latency_seconds": latency,
                            "request_id": request_id,
                            "fallback_api": "responses",
                        },
                    )
                    self._logger.info(
                        "OpenAI completion completed (responses fallback)",
                        context={
                            "request_id": request_id,
                            "model": completion.model,
                            "tokens_used": completion.tokens_used,
                            "latency_seconds": latency,
                        }
                    )
                    return completion
                raise
            # Extract response
            choice = response.choices[0]
            content = choice.message.content or ""
            
            # Create completion result
            completion = LLMCompletion(
                content=content,
                model=response.model,
                provider=self.name,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                finish_reason=choice.finish_reason,
                metadata={
                    "id": response.id,
                    "created": response.created,
                    "latency_seconds": latency,
                    "request_id": request_id,
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                }
            )
            
            self._logger.info(
                "OpenAI completion completed",
                context={
                    "request_id": request_id,
                    "model": response.model,
                    "tokens_used": completion.tokens_used,
                    "latency_seconds": latency,
                    "finish_reason": completion.finish_reason,
                }
            )
            
            return completion
            
        except AuthenticationError as e:
            self._logger.error(
                "OpenAI authentication failed",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "error": str(e)
                }
            )
            raise wrap_exception(
                e,
                LLMError,
                message="OpenAI authentication failed. Check your API key.",
                model=self._model,
                details={"request_id": request_id}
            )
            
        except RateLimitError as e:
            self._logger.warning(
                "OpenAI rate limit exceeded",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "error": str(e)
                }
            )
            raise wrap_exception(
                e,
                LLMError,
                message="OpenAI rate limit exceeded. Please try again later.",
                model=self._model,
                details={"request_id": request_id}
            )
            
        except APIError as e:
            self._logger.error(
                "OpenAI API error",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "error": str(e),
                    "status_code": e.status_code if hasattr(e, 'status_code') else None,
                }
            )
            raise wrap_exception(
                e,
                LLMError,
                message=f"OpenAI API error: {str(e)}",
                model=self._model,
                details={
                    "request_id": request_id,
                    "status_code": e.status_code if hasattr(e, 'status_code') else None,
                }
            )
            
        except Exception as e:
            self._logger.error(
                "Unexpected error in OpenAI completion",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "error": str(e)
                }
            )
            raise wrap_exception(
                e,
                LLMError,
                message="Unexpected error in OpenAI completion",
                model=self._model,
                details={"request_id": request_id}
            )
    
    async def complete_stream(
        self,
        messages: List[Message],
        config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[LLMChunk, None]:
        """
        Stream a completion from messages.
        
        Args:
            messages: List of messages in conversation
            config: Optional configuration overrides
            
        Yields:
            LLMChunk objects
        """
        request_id = f"stream_req_{datetime.utcnow().timestamp()}"
        
        try:
            # Merge configs
            merged_config = self._config.dict() if hasattr(self._config, 'dict') else {}
            if config:
                merged_config.update(config)
            
            # Convert messages
            openai_messages = self._convert_messages(messages)
            
            self._logger.debug(
                "Starting OpenAI streaming request",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "message_count": len(messages),
                }
            )
            
            # Prepare request parameters
            request_params = {
                "model": merged_config.get("model", self._model),
                "messages": openai_messages,
                "temperature": merged_config.get("temperature", 0.7),
                "max_tokens": merged_config.get("max_tokens"),
                "top_p": merged_config.get("top_p", 1.0),
                "stream": True,
            }
            
            # Remove None values
            request_params = {k: v for k, v in request_params.items() if v is not None}
            
            # Start streaming
            start_time = datetime.utcnow()
            stream = await self._client.chat.completions.create(
                **request_params
            )
            
            chunk_index = 0
            full_content = ""
            finish_reason = None
            
            async for chunk in stream:
                chunk: ChatCompletionChunk
                
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    
                    yield LLMChunk(
                        content=content,
                        chunk_index=chunk_index,
                        is_final=False,
                    )
                    
                    chunk_index += 1
                
                if chunk.choices and chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason
            
            latency = (datetime.utcnow() - start_time).total_seconds()
            
            # Final chunk
            yield LLMChunk(
                content="",
                chunk_index=chunk_index,
                is_final=True,
                finish_reason=finish_reason,
            )
            
            self._logger.info(
                "OpenAI streaming completed",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "total_chunks": chunk_index,
                    "latency_seconds": latency,
                    "finish_reason": finish_reason,
                }
            )
            
        except AuthenticationError as e:
            self._logger.error(
                "OpenAI authentication failed in streaming",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "error": str(e)
                }
            )
            raise wrap_exception(
                e,
                LLMError,
                message="OpenAI authentication failed. Check your API key.",
                model=self._model,
                details={"request_id": request_id}
            )
            
        except RateLimitError as e:
            self._logger.warning(
                "OpenAI rate limit exceeded in streaming",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "error": str(e)
                }
            )
            raise wrap_exception(
                e,
                LLMError,
                message="OpenAI rate limit exceeded. Please try again later.",
                model=self._model,
                details={"request_id": request_id}
            )
            
        except Exception as e:
            self._logger.error(
                "Unexpected error in OpenAI streaming",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "error": str(e)
                }
            )
            raise wrap_exception(
                e,
                LLMError,
                message="Unexpected error in OpenAI streaming",
                model=self._model,
                details={"request_id": request_id}
            )
    
    async def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using OpenAI's tiktoken.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Token count
        """
        try:
            # Import tiktoken (should be in dependencies)
            import tiktoken
            
            # Get encoding for the current model
            try:
                encoding = tiktoken.encoding_for_model(self._model)
            except KeyError:
                # Fallback to cl100k_base (used by gpt-4, gpt-3.5-turbo)
                encoding = tiktoken.get_encoding("cl100k_base")
            
            tokens = encoding.encode(text)
            return len(tokens)
            
        except ImportError:
            # Fallback: rough estimate (4 chars per token)
            return len(text) // 4
        except Exception as e:
            self._logger.warning(
                "Failed to count tokens precisely",
                context={
                    "model": self._model,
                    "error": str(e),
                    "text_length": len(text)
                }
            )
            # Rough fallback
            return len(text) // 4


class OpenAIProviderFactory:
    """
    Factory for creating OpenAI adapter instances.
    Implements the LLMProviderFactory pattern.
    """
    
    @staticmethod
    async def create_provider(config: LLMConfig) -> OpenAIAdapter:
        """
        Create an OpenAI adapter instance.
        
        Args:
            config: LLM configuration
            
        Returns:
            OpenAIAdapter instance
        """
        # Validate required config
        if not config.api_key:
            raise LLMError(
                message="OpenAI API key is required",
                model=config.model or "unknown",
                details={"config": config.dict() if hasattr(config, 'dict') else {}}
            )
        
        # Create adapter
        adapter = OpenAIAdapter(config)
        
        # Test connection
        try:
            health = await adapter.health_check()
            if health["status"] != "healthy":
                raise LLMError(
                    message=f"OpenAI health check failed: {health.get('error')}",
                    model=config.model or "unknown",
                    details={"health_check": health}
                )
        except Exception as e:
            # Log but continue - adapter might still work
            logger = get_logger()
            await logger.warning(
                "OpenAI health check failed on creation",
                context={
                    "model": config.model,
                    "error": str(e)
                }
            )
        
        return adapter
    
    @staticmethod
    async def get_available_providers() -> List[str]:
        """
        Get list of available provider types.
        
        Returns:
            List of provider names
        """
        return ["openai"]


# Factory function for convenience
def create_openai_adapter(config: LLMConfig) -> OpenAIAdapter:
    """
    Convenience function to create OpenAI adapter.
    
    Args:
        config: LLM configuration
        
    Returns:
        OpenAIAdapter instance
    """
    return OpenAIAdapter(config)

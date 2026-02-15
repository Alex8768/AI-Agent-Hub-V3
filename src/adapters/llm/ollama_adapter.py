"""
Ollama LLM Adapter for AI Agent Hub V3.
Implements LLMProvider contract for local Ollama instances.
ARCHITECTURE_V3: Adapters Layer - Ollama Integration
"""

import asyncio
import json
from typing import List, AsyncGenerator, Dict, Any, Optional
from datetime import datetime

from ollama import AsyncClient as OllamaAsyncClient

from src.core.contracts import LLMProvider, LLMCompletion, LLMChunk
from src.core.types import Message, MessageRole, LLMConfig
from src.core.exceptions import LLMError, wrap_exception
from src.adapters.logging_adapter import get_logger


class OllamaAdapter(LLMProvider):
    """
    Ollama LLM Provider implementation for local models.
    Supports Llama, Mistral, CodeLlama, and other local models.
    """
    
    def __init__(self, config: LLMConfig):
        """
        Initialize Ollama adapter.
        
        Args:
            config: LLM configuration
        """
        self._name = "ollama"
        self._config = config
        
        # Initialize Ollama client
        self._client = OllamaAsyncClient(
            host=config.base_url or "http://localhost:11434",
            timeout=config.timeout or 120,
        )
        
        # Default model
        self._model = config.model or "llama3.2:latest"
        
        # Model context lengths (approximate)
        self._context_lengths = {
            "llama3.2": 8192,
            "llama3.1": 131072,
            "mistral": 32768,
            "mixtral": 32768,
            "codellama": 16384,
            "neural-chat": 4096,
        }
        
        self._logger = get_logger()
        
        # Запланировать асинхронную инициализацию
        self._initialized = False
    
    async def _initialize(self) -> None:
        """Async initialization."""
        if not self._initialized:
            self._logger.info(
                "Ollama adapter initialized",
                context={
                    "model": self._model,
                    "base_url": self._config.base_url,
                    "timeout": self._config.timeout,
                }
            )
            self._initialized = True
    
    @property
    def name(self) -> str:
        """Provider name."""
        return self._name
    
    @property
    def context_length(self) -> int:
        """Maximum context length for the current model."""
        # Find the best matching model
        for model_pattern, length in self._context_lengths.items():
            if model_pattern in self._model.lower():
                return length
        
        # Default for unknown models
        return 4096
    
    async def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the provider.
        
        Args:
            config: Configuration dictionary
        """
        try:
            # Update config
            if "model" in config:
                self._model = config["model"]
            
            if "base_url" in config:
                self._client = OllamaAsyncClient(
                    host=config["base_url"],
                    timeout=config.get("timeout", self._config.timeout or 120),
                )
            
            self._logger.info(
                "Ollama adapter reconfigured",
                context={
                    "model": self._model,
                    "config_keys": list(config.keys())
                }
            )
            
        except Exception as e:
            wrapped = wrap_exception(
                e,
                LLMError,
                message="Failed to configure Ollama adapter",
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
            
            # List models to check connectivity
            response = await self._client.list()
            latency = (datetime.utcnow() - start_time).total_seconds()
            
            # Check if our model is available
            model_available = any(
                model_info["name"] == self._model 
                for model_info in response.get("models", [])
            )
            
            return {
                "status": "healthy" if model_available else "degraded",
                "model": self._model,
                "model_available": model_available,
                "available_models": [m["name"] for m in response.get("models", [])],
                "latency_seconds": latency,
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
        Convert internal Message objects to Ollama format.
        
        Args:
            messages: List of Message objects
            
        Returns:
            List of Ollama message dictionaries
        """
        ollama_messages = []
        
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
            
            ollama_messages.append(message_dict)
        
        return ollama_messages
    
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
        # Ensure async initialization
        await self._initialize()
        
        request_id = f"ollama_req_{datetime.utcnow().timestamp()}"
        
        try:
            # Merge configs
            merged_config = self._config.dict() if hasattr(self._config, 'dict') else {}
            if config:
                merged_config.update(config)
            
            # Convert messages
            ollama_messages = self._convert_messages(messages)
            
            self._logger.debug(
                "Starting Ollama completion request",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "message_count": len(messages),
                    "temperature": merged_config.get("temperature", 0.7),
                }
            )
            
            # Prepare request parameters
            options = {
                "temperature": merged_config.get("temperature", 0.7),
                "top_p": merged_config.get("top_p", 1.0),
                "num_predict": merged_config.get("max_tokens"),
            }
            
            # Remove None values
            options = {k: v for k, v in options.items() if v is not None}
            
            # Make API call
            start_time = datetime.utcnow()
            response = await self._client.chat(
                model=self._model,
                messages=ollama_messages,
                options=options,
                stream=False
            )
            latency = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract response
            content = response["message"]["content"]
            
            # Create completion result
            completion = LLMCompletion(
                content=content,
                model=self._model,
                provider=self.name,
                tokens_used=(
                    response.get("prompt_eval_count", 0) + 
                    response.get("eval_count", 0)
                ),
                finish_reason="stop",  # Ollama doesn't provide detailed finish reasons
                metadata={
                    "latency_seconds": latency,
                    "request_id": request_id,
                    "prompt_eval_count": response.get("prompt_eval_count"),
                    "eval_count": response.get("eval_count"),
                    "total_duration": response.get("total_duration"),
                    "load_duration": response.get("load_duration"),
                }
            )
            
            self._logger.info(
                "Ollama completion completed",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "tokens_used": completion.tokens_used,
                    "latency_seconds": latency,
                    "content_length": len(content),
                }
            )
            
            return completion
            
        except ConnectionError as e:
            self._logger.error(
                "Ollama connection failed",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "error": str(e),
                    "base_url": self._client.host,
                }
            )
            raise wrap_exception(
                e,
                LLMError,
                message=f"Cannot connect to Ollama at {self._client.host}. Is Ollama running?",
                model=self._model,
                details={
                    "request_id": request_id,
                    "base_url": self._client.host,
                }
            )
            
        except Exception as e:
            self._logger.error(
                "Unexpected error in Ollama completion",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "error": str(e)
                }
            )
            raise wrap_exception(
                e,
                LLMError,
                message="Unexpected error in Ollama completion",
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
        # Ensure async initialization
        await self._initialize()
        
        request_id = f"ollama_stream_{datetime.utcnow().timestamp()}"
        
        try:
            # Merge configs
            merged_config = self._config.dict() if hasattr(self._config, 'dict') else {}
            if config:
                merged_config.update(config)
            
            # Convert messages
            ollama_messages = self._convert_messages(messages)
            
            self._logger.debug(
                "Starting Ollama streaming request",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "message_count": len(messages),
                }
            )
            
            # Prepare request parameters
            options = {
                "temperature": merged_config.get("temperature", 0.7),
                "top_p": merged_config.get("top_p", 1.0),
                "num_predict": merged_config.get("max_tokens"),
            }
            
            # Remove None values
            options = {k: v for k, v in options.items() if v is not None}
            
            # Start streaming
            start_time = datetime.utcnow()
            stream = await self._client.chat(
                model=self._model,
                messages=ollama_messages,
                options=options,
                stream=True
            )
            
            chunk_index = 0
            full_content = ""
            
            async for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    content = chunk["message"]["content"]
                    full_content += content
                    
                    yield LLMChunk(
                        content=content,
                        chunk_index=chunk_index,
                        is_final=False,
                    )
                    
                    chunk_index += 1
                
                if chunk.get("done", False):
                    break
            
            latency = (datetime.utcnow() - start_time).total_seconds()
            
            # Final chunk
            yield LLMChunk(
                content="",
                chunk_index=chunk_index,
                is_final=True,
                finish_reason="stop",
            )
            
            self._logger.info(
                "Ollama streaming completed",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "total_chunks": chunk_index,
                    "latency_seconds": latency,
                    "content_length": len(full_content),
                }
            )
            
        except ConnectionError as e:
            self._logger.error(
                "Ollama connection failed in streaming",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "error": str(e),
                    "base_url": self._client.host,
                }
            )
            raise wrap_exception(
                e,
                LLMError,
                message=f"Cannot connect to Ollama at {self._client.host}",
                model=self._model,
                details={
                    "request_id": request_id,
                    "base_url": self._client.host,
                }
            )
            
        except Exception as e:
            self._logger.error(
                "Unexpected error in Ollama streaming",
                context={
                    "request_id": request_id,
                    "model": self._model,
                    "error": str(e)
                }
            )
            raise wrap_exception(
                e,
                LLMError,
                message="Unexpected error in Ollama streaming",
                model=self._model,
                details={"request_id": request_id}
            )
    
    async def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        Note: Ollama doesn't have a token counting API, so we use an approximation.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Approximate token count
        """
        # Ensure async initialization
        await self._initialize()
        
        # Rough approximation for Llama models
        # Average English: 1 token ≈ 4 characters
        # This is not accurate but better than nothing
        return len(text) // 4

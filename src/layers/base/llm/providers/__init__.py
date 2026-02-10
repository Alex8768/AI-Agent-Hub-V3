"""
LLM Provider Factory for AI Agent Hub V3.
Central point for instantiating LLM adapters based on configuration.
ARCHITECTURE_V3: Base Layer - LLM Provider Factory
"""

from typing import Dict, Type, Optional, List, Any  # ← ДОБАВИТЬ Any
import asyncio

from src.core.contracts import LLMProvider, LLMProviderFactory
from src.core.types import LLMConfig
from src.core.config import settings
from src.core.exceptions import LLMError, ConfigurationError
from src.adapters.logging_adapter import get_logger

# Import adapters
try:
    from src.adapters.llm.openai_adapter import OpenAIAdapter, OpenAIProviderFactory
except ImportError:
    OpenAIAdapter = None
    OpenAIProviderFactory = None

try:
    from src.adapters.llm.ollama_adapter import OllamaAdapter
except ImportError:
    OllamaAdapter = None


class LLMProviderFactoryImpl(LLMProviderFactory):
    """
    Factory to create and manage LLM providers.
    Uses lazy loading and caching for efficiency.
    """
    
    def __init__(self):
        """Initialize the factory."""
        self._providers: Dict[str, Type[LLMProvider]] = {}
        self._instances: Dict[str, LLMProvider] = {}
        self._logger = get_logger()
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Register available providers."""
        # OpenAI
        if OpenAIAdapter is not None:
            self._providers["openai"] = OpenAIAdapter
        
        # Ollama
        if OllamaAdapter is not None:
            self._providers["ollama"] = OllamaAdapter
        
        # Anthropic (to be implemented)
        # if AnthropicAdapter is not None:
        #     self._providers["anthropic"] = AnthropicAdapter
        
        # Google (to be implemented)
        # if GoogleAdapter is not None:
        #     self._providers["google"] = GoogleAdapter
        
        # Hybrid provider (special)
        self._providers["hybrid"] = self._create_hybrid_provider
    
    def _create_hybrid_provider(self, config: LLMConfig) -> LLMProvider:
        """Create a hybrid provider that can fallback between providers."""
        # This is a placeholder - we'll implement this later
        # For now, it returns the first available provider
        from src.adapters.llm.openai_adapter import OpenAIAdapter
        return OpenAIAdapter(config)
    
    async def create_provider(self, config: LLMConfig) -> LLMProvider:
        """
        Create an LLM provider from configuration.
        
        Args:
            config: LLM configuration
            
        Returns:
            LLMProvider instance
        """
        provider_type = config.provider.lower()
        
        # Check if provider is supported
        if provider_type not in self._providers:
            available = list(self._providers.keys())
            raise ConfigurationError(
                message=f"Unsupported LLM provider: {provider_type}",
                config_key="provider",
                config_value=provider_type,
                details={"available_providers": available}
            )
        
        # Validate provider-specific requirements
        if provider_type == "openai" and not config.api_key:
            raise ConfigurationError(
                message="OpenAI provider requires an API key",
                config_key="api_key",
                details={"provider": provider_type}
            )
        
        # Create cache key
        cache_key = f"{provider_type}:{config.model or 'default'}"
        
        # Return cached instance if available
        if cache_key in self._instances:
            return self._instances[cache_key]
        
        # Create new instance
        provider_class = self._providers[provider_type]
        
        # Special handling for hybrid provider
        if provider_type == "hybrid":
            provider = provider_class(config)
        else:
            provider = provider_class(config)
        
        # Test the provider
        try:
            health = await provider.health_check()
            if health.get("status") != "healthy":
                self._logger.warning(
                    f"Provider {provider_type} health check: {health.get('status')}",
                    context={"health": health}
                )
        except Exception as e:
            self._logger.warning(
                f"Provider {provider_type} health check failed",
                context={"error": str(e)}
            )
        
        # Cache the instance
        self._instances[cache_key] = provider
        
        self._logger.info(
            f"Created LLM provider: {provider_type}",
            context={
                "provider": provider_type,
                "model": config.model,
                "cache_key": cache_key,
            }
        )
        
        return provider
    
    async def get_available_providers(self) -> List[str]:
        """
        Get list of available provider types.
        
        Returns:
            List of provider names
        """
        # Check which providers are actually usable
        available = []
        
        for provider_name in self._providers.keys():
            if provider_name == "hybrid":
                # Hybrid is always available if we have at least one provider
                if len(self._providers) > 1:
                    available.append("hybrid")
                continue
            
            # Check if provider can be instantiated
            try:
                # Create a test config
                test_config = LLMConfig(
                    provider=provider_name,
                    model="test" if provider_name != "openai" else "gpt-3.5-turbo",
                    api_key="test" if provider_name == "openai" else None,
                    base_url="http://localhost:11434" if provider_name == "ollama" else None,
                )
                
                provider_class = self._providers[provider_name]
                provider = provider_class(test_config)
                
                # Quick health check (non-blocking)
                health_task = asyncio.create_task(provider.health_check())
                await asyncio.sleep(0.1)  # Short timeout
                
                if not health_task.done():
                    health_task.cancel()
                    # Provider exists but health check timed out
                    available.append(provider_name)
                else:
                    # Provider exists and responded
                    available.append(provider_name)
                    
            except Exception:
                # Provider cannot be instantiated
                pass
        
        return available


# Global factory instance
_global_factory: Optional[LLMProviderFactoryImpl] = None


def get_llm_provider_factory() -> LLMProviderFactoryImpl:
    """
    Get or create the global LLM provider factory.
    
    Returns:
        LLMProviderFactory instance
    """
    global _global_factory
    
    if _global_factory is None:
        _global_factory = LLMProviderFactoryImpl()
    
    return _global_factory


async def get_llm_provider(
    provider_type: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> LLMProvider:
    """
    Convenience function to get an LLM provider.
    
    Args:
        provider_type: Specific provider type (optional)
        config: Custom configuration (optional)
        
    Returns:
        LLMProvider instance
    """
    # Use settings if not specified
    if provider_type is None:
        provider_type = settings.llm_provider.value
    
    # Get configuration
    if config:
        llm_config = LLMConfig(**config)
    else:
        llm_config = settings.get_llm_config(provider_type)
    
    # Get provider from factory
    factory = get_llm_provider_factory()
    return await factory.create_provider(llm_config)

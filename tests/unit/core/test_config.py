"""
Unit tests for configuration module.
"""

import pytest
import os
from unittest.mock import patch, mock_open
from src.core.config import Settings, get_settings


class TestSettings:
    """Test settings configuration."""
    
    def test_default_values(self):
        """Test default settings values."""
        settings = Settings(_env_file=None)
        
        assert settings.environment == "development"
        assert settings.app_name == "AI Agent Hub V3"
        assert settings.debug is True
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
    
    def test_llm_provider_default(self):
        """Test LLM provider default (from model default, not .env)."""
        settings = Settings(_env_file=None)
        default_provider = Settings.model_fields["llm_provider"].default
        assert settings.llm_provider == default_provider
    
    def test_get_llm_config_openai_requires_key(self):
        """OPENAI provider must fail-fast if key is missing."""
        from src.core.exceptions import ConfigurationError
        settings = Settings(_env_file=None)
        with pytest.raises(ConfigurationError):
            settings.get_llm_config(provider="openai")

    def test_get_llm_config_anthropic_requires_key(self):
        """ANTHROPIC provider must fail-fast if key is missing."""
        from src.core.exceptions import ConfigurationError
        settings = Settings(_env_file=None)
        with pytest.raises(ConfigurationError):
            settings.get_llm_config(provider="anthropic")

    def test_get_llm_config_unknown_provider_falls_back_hybrid(self):
        """Unknown provider should safely fallback to hybrid config."""
        settings = Settings(_env_file=None)
        cfg = settings.get_llm_config(provider="custom-provider")
        assert cfg.provider == "hybrid"
        assert cfg.model == "hybrid"

    def test_get_vector_store_config_unknown_provider_falls_back_faiss(self):
        """Unknown vector provider should safely fallback to FAISS config."""
        settings = Settings(_env_file=None)
        cfg = settings.get_vector_store_config(provider="custom-vector-provider")
        assert cfg.provider == "faiss"
        assert cfg.path == settings.faiss_index_path

    def test_cors_origins_parsing(self):
        """Test CORS origins parsing."""
        test_cases = [
            # JSON array string
            ('["http://localhost:3000", "http://localhost:8000"]', 
             ["http://localhost:3000", "http://localhost:8000"]),
            # Comma-separated string
            ("http://localhost:3000,http://localhost:8000",
             ["http://localhost:3000", "http://localhost:8000"]),
            # Already a list
            (["http://localhost:3000", "http://localhost:8000"],
             ["http://localhost:3000", "http://localhost:8000"]),
        ]
        
        for input_val, expected in test_cases:
            settings = Settings(cors_origins=input_val)
            assert settings.cors_origins == expected
    
    def test_settings_singleton(self):
        """Test settings singleton pattern."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_env_file_loading(self):
        """Test that environment can be loaded from ENV vars (deterministic)."""
        with patch.dict(os.environ, {"ENVIRONMENT": "testing"}, clear=False):
            settings = Settings(_env_file=None)
            assert settings.environment == "testing"


class TestFeatureFlags:
    """Test feature flags."""
    
    def test_base_layer_enabled_by_default(self):
        """Test that base layer is enabled by default."""
        settings = Settings(_env_file=None)
        assert settings.feature_base_layer is True
    
    def test_pro_layer_disabled_by_default(self):
        """Test that pro layer is disabled by default."""
        settings = Settings(_env_file=None)
        assert settings.feature_pro_layer is False
    
    def test_feature_flags_independent(self):
        """Test that feature flags can be set independently."""
        settings = Settings(
            feature_base_layer=True,
            feature_pro_layer=True,
            feature_graph_rag=True,
            feature_canvas=False,
            feature_semantic_memory=False,
            feature_multi_agent=False,
        )
        
        assert settings.feature_base_layer is True
        assert settings.feature_pro_layer is True
        assert settings.feature_graphrag is True
        assert settings.feature_graph_rag is True
        assert settings.feature_canvas is False
        assert settings.feature_semantic_memory is False
        assert settings.feature_multi_agent is False

    def test_feature_graphrag_alias_inconsistent_raises(self):
        """Canonical true + alias false must fail fast."""
        from src.core.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError):
            Settings(
                feature_graphrag=True,
                feature_graph_rag=False,
            )


class TestConfigContracts:
    """Freeze external config getter contracts."""

    def test_get_llm_config_openai_contract_shape(self):
        settings = Settings(
            _env_file=None,
            openai_api_key="test-openai-key",
            openai_base_url="https://api.openai.com/v1",
            openai_model="gpt-4o-mini",
            openai_timeout=45,
            openai_max_retries=5,
            openai_max_tokens=2048,
        )
        cfg = settings.get_llm_config(provider="openai")
        data = cfg.model_dump()

        assert set(data.keys()) == {
            "provider",
            "model",
            "api_key",
            "base_url",
            "temperature",
            "max_tokens",
            "timeout",
            "max_retries",
        }
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4o-mini"
        assert data["timeout"] == 45
        assert data["max_retries"] == 5
        assert data["max_tokens"] == 2048

    def test_get_vector_store_config_qdrant_contract_shape(self):
        settings = Settings(
            _env_file=None,
            qdrant_host="localhost",
            qdrant_port=6333,
            qdrant_collection="ai_agent_hub",
        )
        cfg = settings.get_vector_store_config(provider="qdrant")
        data = cfg.model_dump()

        assert set(data.keys()) == {
            "provider",
            "path",
            "index_name",
            "dimension",
            "similarity_metric",
        }
        assert data["provider"] == "qdrant"
        assert data["path"] == settings.qdrant_url
        assert data["index_name"] == "ai_agent_hub"
        assert data["similarity_metric"] == "cosine"

    def test_get_mcp_config_contract_shape(self):
        settings = Settings(
            _env_file=None,
            mcp_enabled=True,
            mcp_servers=["http://server-1", "http://server-2"],
            mcp_max_tools=7,
        )
        cfg = settings.get_mcp_config()
        data = cfg.model_dump()

        assert set(data.keys()) == {
            "enabled",
            "servers",
            "max_tools_per_server",
        }
        assert data["enabled"] is True
        assert data["max_tools_per_server"] == 7
        assert data["servers"] == [
            {"name": "http://server-1", "url": "http://server-1"},
            {"name": "http://server-2", "url": "http://server-2"},
        ]

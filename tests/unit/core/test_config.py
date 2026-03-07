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
        assert settings.feature_graph_rag is True
        assert settings.feature_canvas is False
        assert settings.feature_semantic_memory is False
        assert settings.feature_multi_agent is False

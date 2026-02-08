"""
Unit tests for configuration module.
"""

import pytest
from unittest.mock import patch, mock_open
from src.core.config import Settings, get_settings


class TestSettings:
    """Test settings configuration."""
    
    def test_default_values(self):
        """Test default settings values."""
        settings = Settings()
        
        assert settings.environment == "development"
        assert settings.app_name == "AI Agent Hub V3"
        assert settings.debug is True
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
    
    def test_llm_provider_default(self):
        """Test LLM provider default."""
        settings = Settings()
        assert settings.llm_provider == "hybrid"
    
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
    
    @patch("builtins.open", new_callable=mock_open, read_data="ENVIRONMENT=test")
    @patch("pathlib.Path.exists", return_value=True)
    def test_env_file_loading(self, mock_exists, mock_file):
        """Test environment file loading."""
        settings = Settings()
        # Note: Pydantic settings loads .env automatically
        # This test verifies the file reading mechanism
        assert mock_file.called


class TestFeatureFlags:
    """Test feature flags."""
    
    def test_base_layer_enabled_by_default(self):
        """Test that base layer is enabled by default."""
        settings = Settings()
        assert settings.feature_base_layer is True
    
    def test_pro_layer_disabled_by_default(self):
        """Test that pro layer is disabled by default."""
        settings = Settings()
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

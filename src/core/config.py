"""
Configuration management for AI Agent Hub V3.
Uses pydantic-settings for environment variable loading and validation.
ARCHITECTURE_V3: Core Layer - Configuration Management
"""

from typing import List, Optional, Dict, Any, Union
from enum import Enum
from pathlib import Path

from pydantic import (
    Field, 
    validator, 
    field_validator,
    model_validator,
    ConfigDict, 
    SecretStr, 
    EmailStr,
    HttpUrl
)
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

from src.core.config_parts.parsers import parse_json_or_csv_list

from src.core.exceptions import ConfigurationError

from src.core.paths import get_default_data_dir, ensure_dir

from src.core.types import LLMConfig, VectorStoreConfig, MCPConfig


class LogLevel(str, Enum):
    """Valid log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Valid environment values."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    HYBRID = "hybrid"


class VectorStoreProvider(str, Enum):
    """Supported vector store providers."""
    FAISS = "faiss"
    QDRANT = "qdrant"
    CHROMA = "chroma"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"


class Settings(BaseSettings):
    """
    Main settings class for AI Agent Hub V3.
    Loads from .env file and environment variables.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Игнорировать лишние поля в .env
        env_prefix="",  # Без префикса для env vars
    )

    # ============ HUGGINGFACE / TRANSFORMERS (EMBEDDINGS) ============
    # These map directly from .env variables:
    # HF_HOME, HF_HUB_DISABLE_TELEMETRY, HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE
    hf_home: Optional[str] = Field(
        default=None,
        description="HuggingFace cache dir (HF_HOME)"
    )

    # Hardware/device selection
    # DEVICE=auto|cpu|cuda|mps
    device: str = Field(
        default="auto",
        description="Compute device preference: auto|cpu|cuda|mps",
    )

    # Embedding batching (optional override)
    # EMBEDDING_BATCH_SIZE=32 (or unset to auto-tune)
    embedding_batch_size: Optional[int] = Field(
        default=None,
        description="Embedding batch size override (None = auto)",
        ge=1,
        le=4096,
    )

    hf_hub_disable_telemetry: bool = Field(
        default=False,
        description="Disable HF telemetry (HF_HUB_DISABLE_TELEMETRY)"
    )

    hf_hub_offline: bool = Field(
        default=False,
        description="HF offline mode (HF_HUB_OFFLINE)"
    )

    transformers_offline: bool = Field(
        default=False,
        description="Transformers offline mode (TRANSFORMERS_OFFLINE)"
    )

    
    # ============ APPLICATION SETTINGS ============
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )
    
    project_name: str = Field(
        default="AI Agent Hub V3",
        description="Project name for API documentation"
    )
    
    version: str = Field(
        default="3.0.0",
        description="Application version"
    )
    
    debug: bool = Field(
        default=True,
        description="Debug mode (auto-disabled in production)"
    )
    
    @field_validator("debug")
    @classmethod
    def validate_debug(cls, v: bool, info) -> bool:
        """Auto-disable debug in production."""
        if info.data.get("environment") == Environment.PRODUCTION:
            return False
        return v

    # ============ DATA DIRECTORIES (CROSS-PLATFORM) ============
    data_dir: Path = Field(
        default_factory=get_default_data_dir,
        description="Cross-platform app data dir (override: AI_AGENT_HUB_DATA_DIR)",
    )

    @property
    def storage_dir(self) -> Path:
        """Local file storage directory (uploads, temp, etc.)."""
        return ensure_dir(self.data_dir / "storage")

    @property
    def faiss_dir(self) -> Path:
        """FAISS indices directory."""
        return ensure_dir(self.data_dir / "faiss")

    @property
    def db_dir(self) -> Path:
        """SQLite / local DB directory."""
        return ensure_dir(self.data_dir / "db")
    
    # ============ API SETTINGS ============
    api_v1_str: str = Field(
        default="/api/v1",
        description="API version 1 prefix"
    )
    
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind the API server"
    )
    
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port to bind the API server"
    )
    
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )

    allowed_hosts: List[str] = Field(
        default=["*"],
        description="Allowed hosts for TrustedHost middleware"
    )


    # ============ AUTH / SECURITY SETTINGS ============
    jwt_backend: str = Field(
        default="internal",
        description="JWT backend: 'internal' (no deps) or 'jose' (python-jose)",
    )

    @field_validator("jwt_backend")
    @classmethod
    def validate_jwt_backend(cls, v: str) -> str:
        v2 = (v or "").strip().lower()
        if v2 not in ("internal", "jose"):
            raise ValueError("jwt_backend must be one of: internal, jose")
        return v2

    reload: bool = Field(
        default=False,
        description="Enable auto-reload for development server"
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from JSON string or comma-separated list."""
        return parse_json_or_csv_list(v)

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from JSON string or comma-separated list."""
        return parse_json_or_csv_list(v)
    
    # ============ DATABASE SETTINGS ============
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/ai_agent_hub.db",
        description="Database connection URL"
    )

    database_enabled: bool = Field(
        default=True,
        description="Enable database layer"
    )

    
    database_pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Database connection pool size"
    )
    
    database_max_overflow: int = Field(
        default=20,
        ge=0,
        description="Database connection max overflow"
    )
    
    database_echo: bool = Field(
        default=False,
        description="Echo SQL queries (debug only)"
    )
    
    # ============ LLM PROVIDER SETTINGS ============
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OLLAMA,
        description="Default LLM provider"
    )
    
    # OpenAI
    openai_api_key: Optional[SecretStr] = Field(
        default=None,
        description="OpenAI API key"
    )
    
    openai_base_url: Optional[HttpUrl] = Field(
        default=None,
        description="OpenAI API base URL (for custom deployments)"
    )
    
    openai_model: str = Field(
        default="gpt-4-turbo-preview",
        description="Default OpenAI model"
    )
    
    openai_timeout: int = Field(
        default=30,
        ge=1,
        description="OpenAI API timeout in seconds"
    )
    
    openai_max_retries: int = Field(
        default=3,
        ge=0,
        description="OpenAI API max retries"
    )
    
    openai_max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=128000,
        description="OpenAI max tokens per request"
    )
    
    @field_validator("openai_max_tokens", mode="before")
    @classmethod
    def validate_openai_max_tokens(cls, v: Any) -> Optional[int]:
        """Handle empty string for openai_max_tokens."""
        if v == "" or v == "null" or v is None:
           return None
        return v

    # Anthropic
    anthropic_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Anthropic API key"
    )
    
    anthropic_model: str = Field(
        default="claude-3-opus-20240229",
        description="Default Anthropic model"
    )
    
    anthropic_timeout: int = Field(
        default=30,
        ge=1,
        description="Anthropic API timeout in seconds"
    )
    
    # Google
    google_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Google AI API key"
    )
    
    google_model: str = Field(
        default="gemini-pro",
        description="Default Google AI model"
    )
    
    # Ollama (Local)
    ollama_base_url: HttpUrl = Field(
        default="http://localhost:11434",
        description="Ollama base URL"
    )
    
    ollama_model: str = Field(
        default="llama3.2:latest",
        description="Default Ollama model"
    )
    
    ollama_timeout: int = Field(
        default=120,  # Longer timeout for local models
        ge=1,
        description="Ollama API timeout in seconds"
    )
    
    ollama_max_tokens: int = Field(
        default=4096,
        ge=1,
        description="Ollama max tokens per request"
    )
    
    # ============ VECTOR STORE SETTINGS ============
    vector_store_provider: VectorStoreProvider = Field(
        default=VectorStoreProvider.FAISS,
        description="Default vector store provider"
    )

    # ============ PRO FEATURE FLAGS (OFF BY DEFAULT) ============
    # These flags gate Pro-only capabilities. Base must remain stable when all are False.
    feature_qdrant: bool = Field(
        default=False,
        description="Enable Pro Qdrant vector store adapter (Pro)"
    )

    feature_acl: bool = Field(
        default=False,
        description="Enable Pro ACL/Authorizer layer (Pro)"
    )

    feature_memory: bool = Field(
        default=False,
        description="Enable Pro durable memory layer (Pro)"
    )

    feature_memory_embeddings: bool = Field(
        default=False,
        description="Enable semantic memory embeddings index (Pro)"
    )

    feature_graphrag: bool = Field(
        default=False,
        description="Enable Pro GraphRAG layer (Pro)"
    )


    # ---- Backward/compat alias ----
    # NOTE:
    # Historically we had both `feature_graphrag` and `feature_graph_rag`.
    # Canonical flag: feature_graphrag
    # Alias (deprecated): feature_graph_rag
    #
    # We keep the alias field for env/backward compatibility but normalize it.
    feature_graph_rag: bool = Field(
        default=False,
        description="DEPRECATED alias for feature_graphrag (kept for backward compatibility)",
    )

    def _apply_feature_graphrag_alias(self) -> None:
        # Canonical: feature_graphrag
        # Alias: feature_graph_rag
        if bool(self.feature_graph_rag) and not bool(self.feature_graphrag):
            object.__setattr__(self, "feature_graphrag", True)

    def _validate_feature_graphrag_consistency(self) -> None:
        # If canonical True but alias False -> misconfiguration (prevents silent surprises)
        if bool(self.feature_graphrag) and not bool(self.feature_graph_rag):
            raise ConfigurationError(
                "Inconsistent feature flags: feature_graphrag=True but feature_graph_rag=False. "
                "Use only feature_graphrag (canonical) or set both consistently."
            )

    @model_validator(mode="after")
    def _normalize_feature_flag_aliases(self) -> "Settings":
        """Normalize deprecated aliases for feature flags.

        - If only alias is enabled, enable canonical flag.
        - If both are set but disagree, raise ConfigurationError (fail-fast).
        """
        self._apply_feature_graphrag_alias()
        self._validate_feature_graphrag_consistency()
        return self
    feature_reasoning: bool = Field(
        default=False,
        description="Enable graph-aware reasoning answer synthesis layer (Pro)",
    )

    feature_reasoning_llm_dry_run: bool = Field(
        default=False,
        description="Enable deterministic dry-run LLM mode for reasoning (Pro)",
    )

    feature_reasoning_llm_enabled: bool = Field(
        default=False,
        description="Enable real LLM calls in reasoning (Pro). When False, LLM is never resolved.",
    )

    feature_hybrid_search_api: bool = Field(
        default=False,
        description="Enable /api/v1/search-hybrid endpoint (Pro risky surface)",
    )

    feature_reasoning_api: bool = Field(
        default=False,
        description="Enable /api/v1/answer endpoint (Pro risky surface)",
    )

    feature_assistant_mode: bool = Field(
        default=False,
        description="Enable assistant-first response mode orchestration (A2.34)",
    )

    feature_assistant_proactive: bool = Field(
        default=False,
        description="Enable proactive assistant suggestions pipeline (A2.34)",
    )

    feature_assistant_actions: bool = Field(
        default=False,
        description="Enable assistant draft action planning/execution contracts (A2.34)",
    )

    feature_agent_router_v1: bool = Field(
        default=True,
        description="Enable agent router v1 path (A1-A6 containers, memory-lite, reflection-lite, tool policy)",
    )



    
    # FAISS
    faiss_index_path: str = Field(
        default_factory=lambda: str(get_default_data_dir() / "faiss" / "faiss_index"),
        description="Path to FAISS index file"
    )
    
    faiss_dimension: int = Field(
        default=384,  # sentence-transformers MiniLM dimension
        ge=1,
        description="FAISS embedding dimension"
    )
    
    # Qdrant
    qdrant_host: str = Field(
        default="localhost",
        description="Qdrant server host"
    )
    
    qdrant_port: int = Field(
        default=6333,
        ge=1,
        le=65535,
        description="Qdrant server port"
    )
    
    qdrant_collection: str = Field(
        default="ai_agent_hub",
        description="Qdrant collection name"
    )
    
    qdrant_timeout: int = Field(
        default=10,
        ge=1,
        description="Qdrant API timeout in seconds"
    )
    
    # ============ LOGGING SETTINGS ============
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Application log level"
    )
    
    log_format: str = Field(
        default="json",
        description="Log format (json or plain)"
    )
    
    log_file: Optional[str] = Field(
        default=None,
        description="Log file path (if None, logs to stdout)"
    )
    
    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        valid_formats = ["json", "plain", "structured"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {', '.join(valid_formats)}")
        return v.lower()
    
    # ============ MCP SETTINGS ============
    mcp_enabled: bool = Field(
        default=False,
        description="Enable MCP protocol support"
    )
    
    mcp_servers: List[str] = Field(
        default_factory=list,
        description="List of MCP server configurations"
    )
    
    @field_validator("mcp_servers", mode="before")
    @classmethod
    def parse_mcp_servers(cls, v):
        """Parse MCP servers from JSON string or comma-separated list."""
        return parse_json_or_csv_list(v)
    
    mcp_max_tools: int = Field(
        default=10,
        ge=1,
        description="Maximum tools per MCP server"
    )
    
    # ============ WORKSPACE SETTINGS ============
    workspace_root: Path = Field(
        default=Path("./workspace"),
        description="Root directory for workspaces"
    )
    
    workspace_max_size_mb: int = Field(
        default=1024,  # 1GB
        ge=10,
        description="Maximum workspace size in MB"
    )

    workspace_tools_use_repo_root_in_dev: bool = Field(
        default=False,
        description="Use repository root for workspace MCP tools in development mode"
    )
    
    # ============ SECURITY SETTINGS ============
    secret_key: SecretStr = Field(
        default_factory=lambda: SecretStr("dev-secret-key-change-in-production"),
        description="Secret key for cryptographic operations"
    )
    
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        description="Access token expiration in minutes"
    )

    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable rate limiting middleware"
    )
    
    rate_limit_requests: int = Field(
        default=100,
        ge=1,
        description="Rate limit requests per period"
    )
    
    rate_limit_period: int = Field(
        default=60,
        ge=1,
        description="Rate limit period in seconds"
    )

    # ============ INGEST SETTINGS ============
    ingest_chunk_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Default chunk size for document ingest"
    )

    ingest_chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=1000,
        description="Default chunk overlap for document ingest"
    )

    # ============ STREAMING SETTINGS ============
    streaming_enabled: bool = Field(
        default=False,
        description="Enable SSE streaming endpoints"
    )
    
    # ============ FEATURE FLAGS ============
    feature_base_layer: bool = Field(
        default=True,
        description="Enable Base Layer features"
    )
    
    feature_pro_layer: bool = Field(
        default=False,
        description="Enable Pro Layer features"
    )
    feature_canvas: bool = Field(
        default=False,
        description="Enable Split View Canvas feature"
    )
    
    feature_semantic_memory: bool = Field(
        default=False,
        description="Enable Semantic Memory feature"
    )
    
    feature_multi_agent: bool = Field(
        default=False,
        description="Enable Multi-Agent feature"
    )
    
    # ============ COMPUTED PROPERTIES ============
    @property
    def is_production(self) -> bool:
        """Check if environment is production."""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if environment is development."""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_testing(self) -> bool:
        """Check if environment is testing."""
        return self.environment == Environment.TESTING

    @property
    def app_name(self) -> str:
        """Alias for API layer compatibility."""
        return self.project_name

    @property
    def app_version(self) -> str:
        """Alias for API layer compatibility."""
        return self.version
    
    @property
    def api_base_url(self) -> str:
        """Get base API URL."""
        return f"http://{self.host}:{self.port}{self.api_v1_str}"
    
    @property
    def qdrant_url(self) -> str:
        """Get Qdrant URL."""
        return f"http://{self.qdrant_host}:{self.qdrant_port}"
    
    @property
    def workspace_root_path(self) -> Path:
        """Get absolute workspace root path."""
        return self.workspace_root.resolve()

    def _validate_llm_provider_requirements(self, provider: LLMProvider) -> None:
        # Base: fail-fast on missing API keys for remote providers
        if provider == LLMProvider.OPENAI and not self.openai_api_key:
            raise ConfigurationError(
                message="OPENAI provider selected but OPENAI_API_KEY is not set",
                config_key="OPENAI_API_KEY",
            )
        if provider == LLMProvider.ANTHROPIC and not self.anthropic_api_key:
            raise ConfigurationError(
                message="ANTHROPIC provider selected but ANTHROPIC_API_KEY is not set",
                config_key="ANTHROPIC_API_KEY",
            )

    def _build_llm_provider_config_map(self) -> Dict[LLMProvider, Dict[str, Any]]:
        return {
            LLMProvider.OPENAI: {
                "provider": "openai",
                "model": self.openai_model,
                "api_key": self.openai_api_key.get_secret_value() if self.openai_api_key else None,
                "base_url": str(self.openai_base_url) if self.openai_base_url else None,
                "timeout": self.openai_timeout,
                "max_retries": self.openai_max_retries,
                "max_tokens": self.openai_max_tokens,
            },
            LLMProvider.ANTHROPIC: {
                "provider": "anthropic",
                "model": self.anthropic_model,
                "api_key": self.anthropic_api_key.get_secret_value() if self.anthropic_api_key else None,
                "timeout": self.anthropic_timeout,
            },
            LLMProvider.OLLAMA: {
                "provider": "ollama",
                "model": self.ollama_model,
                "base_url": str(self.ollama_base_url),
                "timeout": self.ollama_timeout,
                "max_tokens": self.ollama_max_tokens,
            },
            LLMProvider.HYBRID: {
                "provider": "hybrid",
                "model": "hybrid",  # Will use best available
                "api_key": None,
                "timeout": 30,
            }
        }

    def _build_vector_store_config_map(self) -> Dict[VectorStoreProvider, Dict[str, Any]]:
        return {
            VectorStoreProvider.FAISS: {
                "provider": "faiss",
                "path": self.faiss_index_path,
                "dimension": self.faiss_dimension,
                "similarity_metric": "cosine",
            },
            VectorStoreProvider.QDRANT: {
                "provider": "qdrant",
                "path": self.qdrant_url,
                "index_name": self.qdrant_collection,
                "similarity_metric": "cosine",
            },
        }
    
    def get_llm_config(self, provider: Optional[LLMProvider] = None) -> LLMConfig:
        """Get LLM configuration for a provider."""
        provider = provider or self.llm_provider
        self._validate_llm_provider_requirements(provider)
        config_map = self._build_llm_provider_config_map()
        config = config_map.get(provider, config_map[LLMProvider.HYBRID])
        return LLMConfig(**config)
    
    def get_vector_store_config(self, provider: Optional[VectorStoreProvider] = None) -> VectorStoreConfig:
        """Get vector store configuration."""
        provider = provider or self.vector_store_provider
        config_map = self._build_vector_store_config_map()
        config = config_map.get(provider, config_map[VectorStoreProvider.FAISS])
        return VectorStoreConfig(**config)
    
    def get_mcp_config(self) -> MCPConfig:
        """Get MCP configuration."""
        return MCPConfig(
            enabled=self.mcp_enabled,
            servers=[{"name": server, "url": server} for server in self.mcp_servers],
            max_tools_per_server=self.mcp_max_tools,
        )


# Global settings instance
settings = Settings()


def reload_settings() -> None:
    """Reload settings from environment."""
    global settings
    settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance (for dependency injection)."""
    return settings

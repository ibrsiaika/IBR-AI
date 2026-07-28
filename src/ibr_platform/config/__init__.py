"""
Configuration Management (PRD Section 17, 32).

Uses Pydantic Settings for type-safe configuration with environment variable
support. Configuration can be loaded from:
1. Environment variables (prefixed with IBR_)
2. YAML config files
3. Default values

The deployment mode (tiny/compact/professional/enterprise) controls resource
budgets, concurrency, and feature flags per PRD Section 17.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeploymentMode(StrEnum):
    """Deployment modes per PRD Section 17.1.

    - TINY: Laptop (4-8 GB RAM), 1 user, 2 GB budget
    - COMPACT: Workstation (16-32 GB RAM), 5 users, 8 GB budget
    - PROFESSIONAL: Server (64-128 GB RAM), 50 users, 32 GB budget
    - ENTERPRISE: Cluster (256+ GB RAM), 500+ users, 128+ GB budget
    """

    TINY = "tiny"
    COMPACT = "compact"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    sql_backend: str = Field(default="sqlite", description="sqlite or postgresql")
    sql_url: str = Field(default="sqlite:///ibr.db", description="SQL database URL")
    vector_backend: str = Field(default="pgvector", description="pgvector, qdrant, or milvus")
    vector_url: str = Field(default="", description="Vector DB URL (empty for embedded)")
    graph_backend: str = Field(default="neo4j", description="neo4j or none")
    graph_url: str = Field(default="bolt://localhost:7687", description="Graph DB URL")
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")


class SecurityConfig(BaseSettings):
    """Security configuration (PRD Section 22)."""

    secret_key: str = Field(default="change-me-in-production", description="Secret key for signing")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiry_hours: int = Field(default=24)
    audit_log_enabled: bool = Field(default=True)
    audit_log_retention_days: int = Field(default=2555)  # 7 years for compliance
    sandbox_enabled: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=60)


class ObservabilityConfig(BaseSettings):
    """Observability configuration (PRD Section 24)."""

    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    metrics_enabled: bool = Field(default=True)
    metrics_port: int = Field(default=9090)
    tracing_enabled: bool = Field(default=True)
    tracing_endpoint: str = Field(default="http://localhost:4317")


class ModelConfig(BaseSettings):
    """Model configuration."""

    default_model: str = Field(default="llama-3.2-1b")
    default_quantization: str = Field(default="q4_k_m")
    inference_engine: str = Field(default="llama_cpp")
    embedding_model: str = Field(default="bge-large-en-v1.5")
    embedding_dim: int = Field(default=1024)
    max_context_length: int = Field(default=8192)
    gpu_enabled: bool = Field(default=False)


class Settings(BaseSettings):
    """
    Main configuration for the IBR Platform.

    Loads from environment variables (prefixed IBR_) and optional YAML file.
    Environment variables take precedence over YAML, which takes precedence
    over defaults.

    Usage:
        from ibr_platform.config import settings
        print(settings.deployment_mode)

        # Or load from YAML:
        settings = Settings.from_yaml("configs/enterprise.yaml")
    """

    model_config = SettingsConfigDict(
        env_prefix="IBR_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Deployment
    deployment_mode: DeploymentMode = Field(
        default=DeploymentMode.TINY,
        description="Deployment mode: tiny, compact, professional, or enterprise",
    )

    # Resource budgets (in MB)
    ram_budget_mb: int = Field(default=2048, description="RAM budget in MB")
    max_concurrent_agents: int = Field(default=1, description="Max concurrent agent workers")

    # Feature flags
    enable_training: bool = Field(default=False)
    enable_distributed: bool = Field(default=False)
    enable_gpu: bool = Field(default=False)
    enable_dashboard: bool = Field(default=True)

    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)

    # Paths
    data_dir: Path = Field(default=Path("./data"), description="Data directory")
    models_dir: Path = Field(default=Path("./models"), description="Model directory")
    logs_dir: Path = Field(default=Path("./logs"), description="Logs directory")

    @field_validator("deployment_mode", mode="before")
    @classmethod
    def normalize_deployment_mode(cls, v: Any) -> DeploymentMode:
        """Normalize deployment mode string."""
        if isinstance(v, DeploymentMode):
            return v
        if isinstance(v, str):
            v = v.lower().strip()
            try:
                return DeploymentMode(v)
            except ValueError:
                valid = [m.value for m in DeploymentMode]
                raise ValueError(
                    f"Invalid deployment_mode '{v}'. Must be one of: {valid}"
                ) from None
        raise ValueError(
            f"deployment_mode must be string or DeploymentMode, got {type(v)}"
        ) from None

    @classmethod
    def from_yaml(cls, path: str | Path) -> Settings:
        """Load settings from a YAML file.

        Args:
            path: Path to YAML config file.

        Returns:
            Settings instance with values from YAML.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    def apply_deployment_defaults(self) -> Settings:
        """Apply resource defaults based on deployment mode.

        Returns self for chaining.
        """
        defaults = {
            DeploymentMode.TINY: {
                "ram_budget_mb": 2048,
                "max_concurrent_agents": 1,
                "enable_training": False,
                "enable_distributed": False,
                "enable_gpu": False,
            },
            DeploymentMode.COMPACT: {
                "ram_budget_mb": 8192,
                "max_concurrent_agents": 5,
                "enable_training": True,
                "enable_distributed": False,
                "enable_gpu": False,
            },
            DeploymentMode.PROFESSIONAL: {
                "ram_budget_mb": 32768,
                "max_concurrent_agents": 20,
                "enable_training": True,
                "enable_distributed": False,
                "enable_gpu": True,
            },
            DeploymentMode.ENTERPRISE: {
                "ram_budget_mb": 131072,
                "max_concurrent_agents": 100,
                "enable_training": True,
                "enable_distributed": True,
                "enable_gpu": True,
            },
        }
        defaults_for_mode = defaults.get(self.deployment_mode, {})
        for key, value in defaults_for_mode.items():
            # Only set if not explicitly configured (check env)
            env_key = f"IBR_{key.upper()}"
            import os
            if env_key not in os.environ:
                setattr(self, key, value)
        return self


# Global settings instance (lazy-loaded)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance.

    Loads from environment variables on first call.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.apply_deployment_defaults()
    return _settings


def set_settings(settings: Settings) -> None:
    """Override the global settings (useful for testing)."""
    global _settings
    _settings = settings


# Convenience alias
settings = get_settings()

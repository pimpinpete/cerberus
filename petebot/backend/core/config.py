"""Configuration management with Pydantic settings."""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class DatabaseConfig(BaseModel):
    """Database configuration."""
    postgres_url: str = "postgresql://localhost:5432/petebot"
    redis_url: str = "redis://localhost:6379/0"
    timescale_url: Optional[str] = None  # Uses postgres_url if not set


class AIConfig(BaseModel):
    """AI/LLM configuration."""
    default_model: str = "claude-opus-4-20250514"
    fallback_models: List[str] = ["claude-sonnet-4-20250514", "gpt-4o"]
    max_tokens: int = 4096
    temperature: float = 0.7
    cache_responses: bool = True
    cache_ttl: int = 3600


class TradingConfig(BaseModel):
    """Trading configuration."""
    enabled: bool = False
    paper_trading: bool = True
    max_position_size: float = 10000.0
    max_daily_loss: float = 500.0
    max_positions: int = 10
    risk_per_trade: float = 0.02  # 2% per trade


class IntegrationConfig(BaseModel):
    """Integration-specific config."""
    enabled: bool = True
    rate_limit: int = 100
    timeout: int = 30
    retry_attempts: int = 3


class IntegrationsConfig(BaseModel):
    """All integrations configuration."""
    webull: IntegrationConfig = IntegrationConfig()
    plaid: IntegrationConfig = IntegrationConfig()
    whoop: IntegrationConfig = IntegrationConfig()
    discord: IntegrationConfig = IntegrationConfig()
    gmail: IntegrationConfig = IntegrationConfig()
    calendar: IntegrationConfig = IntegrationConfig()


class ObservabilityConfig(BaseModel):
    """Observability configuration."""
    log_level: str = "INFO"
    structured_logging: bool = True
    metrics_enabled: bool = True
    metrics_port: int = 9090
    tracing_enabled: bool = True
    tracing_endpoint: Optional[str] = None


class SecurityConfig(BaseModel):
    """Security configuration."""
    secret_key: str = Field(default_factory=lambda: os.urandom(32).hex())
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    use_keychain: bool = True
    audit_trail: bool = True


class AgentConfig(BaseModel):
    """Mac automation agent configuration."""
    enabled: bool = True
    api_token: str = os.getenv("API_TOKEN", "dev-local-only")
    allow_shell: bool = True
    allowed_shell_prefixes: List[str] = [
        "python3",
        "python",
        "echo",
        "osascript",
        "shortcuts",
        "open",
        "bash",
        "zsh",
    ]
    default_timeout_seconds: int = 120


class Config(BaseSettings):
    """Main application configuration."""

    # App metadata
    app_name: str = "PeteBot V2"
    app_version: str = "2.0.0"
    environment: str = "development"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Base paths
    base_path: Path = Path.home() / "cerberus" / "petebot"
    data_path: Path = Path.home() / ".petebot"

    # Nested configs
    database: DatabaseConfig = DatabaseConfig()
    ai: AIConfig = AIConfig()
    trading: TradingConfig = TradingConfig()
    integrations: IntegrationsConfig = IntegrationsConfig()
    observability: ObservabilityConfig = ObservabilityConfig()
    security: SecurityConfig = SecurityConfig()
    agent: AgentConfig = AgentConfig()

    # Feature flags
    features: Dict[str, bool] = {
        "trading_enabled": False,
        "backtesting_enabled": True,
        "ai_chat_enabled": True,
        "health_tracking_enabled": True,
        "banking_enabled": True,
    }

    class Config:
        env_prefix = "PETEBOT_"
        env_file = ".env"
        env_nested_delimiter = "__"

    def is_production(self) -> bool:
        return self.environment == "production"

    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache()
def get_config() -> Config:
    """Get cached configuration instance."""
    return Config()


# Convenience function for tests
def get_test_config() -> Config:
    """Get test configuration."""
    return Config(
        environment="test",
        debug=True,
        database=DatabaseConfig(
            postgres_url="postgresql://localhost:5432/petebot_test",
            redis_url="redis://localhost:6379/1"
        ),
        trading=TradingConfig(enabled=False, paper_trading=True)
    )

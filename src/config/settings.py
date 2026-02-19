from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.enums import AppStage


def build_postgres_memory_uri(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
) -> str:
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


class Settings(BaseSettings):
    app_stage: AppStage = Field(
        default=AppStage.DEVELOPMENT,
        alias="ENVIRONMENT",
        description="Application deployment stage: development, qa, or production",
    )
    log_level: str = Field(
        default="info",
        description="Logging level: debug, info, warning, error, critical",
    )
    app_port: int = Field(
        default=8000,
        description="Port number for the FastAPI application server",
    )

    api_key: str = Field(
        description="Secret API key for authenticating requests to this api service",
    )
    cors_origins_raw: str = Field(
        default="",
        alias="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins for cross-origin requests",
    )
    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum number of requests allowed per minute per API key",
    )

    openai_api_key: str = Field(
        description="OpenAI API key for LLM and embedding model access",
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI model name for generating text embeddings",
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model name for chat completions",
    )

    langfuse_public_key: str | None = Field(
        default=None,
        description="Langfuse public key for observability tracing (optional)",
    )
    langfuse_secret_key: str | None = Field(
        default=None,
        description="Langfuse secret key for observability tracing (optional)",
    )
    langfuse_host: str = Field(
        default="http://localhost:3000",
        description="Langfuse server URL for observability data submission",
    )

    openweather_api_key: str | None = Field(
        default=None,
        description="OpenWeatherMap API key for weather data retrieval",
    )

    alpaca_api_key: str | None = Field(
        default=None,
        description="Alpaca API key ID for market data",
    )
    alpaca_secret_key: str | None = Field(
        default=None,
        description="Alpaca API secret key for market data",
    )
    alpaca_use_sandbox: bool = Field(
        default=False,
        description="Use Alpaca sandbox environment instead of production",
    )

    postgres_memory_host: str = Field(
        default="localhost",
        description="PostgreSQL memory store host for agent conversation persistence",
    )
    postgres_memory_port: int = Field(
        default=5433,
        description="PostgreSQL memory store port",
    )
    postgres_memory_user: str = Field(
        default="veramoney",
        description="PostgreSQL memory store user",
    )
    postgres_memory_password: str = Field(
        default="veramoney_secret",
        description="PostgreSQL memory store password",
    )
    postgres_memory_db: str = Field(
        default="veramoney_memory",
        description="PostgreSQL memory store database name",
    )

    agent_model: str = Field(
        default="gpt-5-mini-2025-08-07",
        description="OpenAI model for conversational agent",
    )
    agent_timeout_seconds: float = Field(
        default=30.0,
        description="Timeout for LLM API calls in seconds",
    )
    agent_max_context_messages: int = Field(
        default=20,
        description="Maximum messages to keep in conversation context",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        if not self.cors_origins_raw:
            return []
        origins = [origin.strip() for origin in self.cors_origins_raw.split(",")]
        return [origin for origin in origins if origin]

    @property
    def is_production(self) -> bool:
        return self.app_stage == AppStage.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.app_stage == AppStage.DEVELOPMENT

    @computed_field
    @property
    def postgres_memory_uri(self) -> str:
        return build_postgres_memory_uri(
            host=self.postgres_memory_host,
            port=self.postgres_memory_port,
            user=self.postgres_memory_user,
            password=self.postgres_memory_password,
            database=self.postgres_memory_db,
        )


settings = Settings()

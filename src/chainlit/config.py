from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChainlitSettings(BaseSettings):
    backend_url: str = Field(
        default="http://localhost:8000",
        alias="BACKEND_URL",
        description="FastAPI backend URL",
    )
    api_key: str = Field(
        alias="CHAINLIT_API_KEY",
        description="Shared API key for backend authentication",
    )
    request_timeout: float = Field(
        default=120.0,
        alias="CHAINLIT_REQUEST_TIMEOUT",
        description="SSE stream timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        alias="CHAINLIT_MAX_RETRIES",
        description="Network failure retry attempts",
    )
    retry_delay: float = Field(
        default=1.0,
        alias="CHAINLIT_RETRY_DELAY",
        description="Initial retry delay in seconds",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )


chainlit_settings = ChainlitSettings()

"""
LangFuse Configuration Settings Example

This file demonstrates the configuration pattern for LangFuse
in a Pydantic settings class.
Source: clickbait project - app/core/config.py

Key patterns:
- Environment variable loading
- Default values for optional settings
- Boolean string conversion helper
- Type-safe configuration with Pydantic
"""

import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_TRUTHY_STRING_VALUES = {"true", "1", "yes", "on"}


def str_to_bool(value: str | None) -> bool:
    """Convert string environment variable to boolean.

    Args:
        value: String value from environment variable

    Returns:
        - True for: 'true', '1', 'yes', 'on' (case-insensitive)
        - False for: None, '', 'false', '0', 'no', 'off', or any other value
    """
    has_no_value = value is None or value == ""
    if has_no_value:
        return False

    normalized_value = value.lower().strip()
    return normalized_value in _TRUTHY_STRING_VALUES


class Settings(BaseSettings):
    """Application settings with LangFuse configuration.

    LangFuse requires these environment variables:
    - LANGFUSE_PUBLIC_KEY: Your public key from LangFuse
    - LANGFUSE_SECRET_KEY: Your secret key from LangFuse

    Optional configuration:
    - LANGFUSE_BASE_URL: Custom LangFuse instance URL (default: cloud.langfuse.com)
    - LANGFUSE_TRACING_ENVIRONMENT: Environment tag for traces
    - LANGFUSE_RELEASE: Release version for traces
    - LANGFUSE_DEBUG: Enable debug logging
    - LANGFUSE_SAMPLE_RATE: Sampling rate (0.0-1.0)

    Usage:
        from app.core.config import settings

        # LangFuse client automatically uses these settings
        from langfuse import get_client
        client = get_client()  # Reads from environment
    """

    model_config = SettingsConfigDict(extra="ignore", env_file=".env")

    # Application Environment
    APP_ENV: Literal["PROD", "QA", "DEV"] = os.getenv("APP_ENV", "DEV")

    # ========================================================================
    # LangFuse Observability Configuration
    # ========================================================================

    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_BASE_URL: str = os.getenv(
        "LANGFUSE_BASE_URL",
        "https://cloud.langfuse.com",
    )
    LANGFUSE_TRACING_ENVIRONMENT: str = os.getenv(
        "LANGFUSE_TRACING_ENVIRONMENT",
        APP_ENV,
    )
    LANGFUSE_RELEASE: str = os.getenv("LANGFUSE_RELEASE", "v1.0.0")
    LANGFUSE_DEBUG: bool = str_to_bool(os.getenv("LANGFUSE_DEBUG", "false"))
    LANGFUSE_SAMPLE_RATE: float = float(os.getenv("LANGFUSE_SAMPLE_RATE", "1.0"))

    # ========================================================================
    # Optional: Custom Tracing Control
    # ========================================================================

    ENABLE_CUSTOM_TRACE: bool = str_to_bool(
        os.getenv("ENABLE_CUSTOM_TRACE", "true"),
    )
    CUSTOM_TRACE_SAMPLE_RATE: int = Field(
        int(os.getenv("CUSTOM_TRACE_SAMPLE_RATE", "100")),
        description="Percentage (0-100) of operations to trace",
    )

    # ========================================================================
    # Optional: Dataset Sampling for AI Evaluation
    # ========================================================================

    DATASET_SAMPLE_RATE: int = Field(
        int(os.getenv("DATASET_SAMPLE_RATE", "0")),
        description="Percentage (0-100) of operations to save to datasets",
    )


# ============================================================================
# ENVIRONMENT FILE TEMPLATE
# ============================================================================

ENV_TEMPLATE = """
# .env.example - LangFuse Configuration

# Required: Your LangFuse keys (get from https://cloud.langfuse.com)
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key

# Optional: Custom LangFuse instance (default: cloud.langfuse.com)
LANGFUSE_BASE_URL=https://cloud.langfuse.com

# Optional: Environment tag for filtering traces
LANGFUSE_TRACING_ENVIRONMENT=production

# Optional: Release version for tracking deployments
LANGFUSE_RELEASE=v1.0.0

# Optional: Enable debug logging (default: false)
LANGFUSE_DEBUG=false

# Optional: Sampling rate 0.0-1.0 (default: 1.0 = 100%)
LANGFUSE_SAMPLE_RATE=1.0

# Optional: Custom trace control
ENABLE_CUSTOM_TRACE=true
CUSTOM_TRACE_SAMPLE_RATE=100

# Optional: Dataset sampling for AI evaluation
DATASET_SAMPLE_RATE=5
"""


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Set example environment variables
    os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-test-key"
    os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-test-key"
    os.environ["APP_ENV"] = "DEV"

    settings = Settings()

    print("LangFuse Configuration:")
    print(f"  Base URL: {settings.LANGFUSE_BASE_URL}")
    print(f"  Environment: {settings.LANGFUSE_TRACING_ENVIRONMENT}")
    print(f"  Release: {settings.LANGFUSE_RELEASE}")
    print(f"  Debug: {settings.LANGFUSE_DEBUG}")
    print(f"  Sample Rate: {settings.LANGFUSE_SAMPLE_RATE}")
    print(f"  Public Key: {settings.LANGFUSE_PUBLIC_KEY[:10]}...")

    print("\n" + "="*60)
    print("Environment File Template:")
    print("="*60)
    print(ENV_TEMPLATE)

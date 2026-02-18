from functools import lru_cache
from typing import Annotated

from fastapi import Depends


# Placeholder for future service dependencies
# These will be implemented as the application services are built


@lru_cache
def get_settings() -> "Settings":
    """Get application settings (cached).

    Returns:
        Application settings instance.
    """
    # Import here to avoid circular imports
    # Will be replaced with actual settings from config module
    from pydantic import BaseModel

    class Settings(BaseModel):
        """Placeholder settings class."""

        app_name: str = "VeraMoney API"
        debug: bool = False

    return Settings()


# Type alias for settings dependency injection
SettingsDep = Annotated["Settings", Depends(get_settings)]

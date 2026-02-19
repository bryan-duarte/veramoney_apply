from typing import Annotated

from fastapi import Depends, Header, HTTPException

from src.config import Settings, settings


SettingsDep = Annotated[Settings, Depends(lambda: settings)]


def get_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> str:
    is_api_key_missing = x_api_key is None
    is_api_key_invalid = x_api_key != settings.api_key

    if is_api_key_missing or is_api_key_invalid:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return x_api_key


APIKeyDep = Annotated[str, Depends(get_api_key)]

import asyncio
import logging
import os

import httpx
from langfuse import Langfuse, get_client

from src.config import settings

logger = logging.getLogger(__name__)

LANGFUSE_CLIENT_NAME = "veramoney-api"
TRACE_NAME_PREFIX = "veramoney-"

_MAX_INIT_RETRIES = 3
_INIT_RETRY_DELAY_SECONDS = 5

_langfuse_initialized: bool = False
_langfuse_prompt_synced: bool = False


def _ensure_env_vars_set() -> None:
    if settings.langfuse_public_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
    if settings.langfuse_secret_key:
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
    if settings.langfuse_host:
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host


def _log_public_key_prefix() -> str:
    if settings.langfuse_public_key:
        return settings.langfuse_public_key[:10] + "..."
    return "None"


def _configure_langfuse_singleton() -> None:
    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


async def _check_langfuse_auth() -> bool:
    url = f"{settings.langfuse_host}/api/public/projects"
    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            response = await http.get(
                url,
                auth=(settings.langfuse_public_key, settings.langfuse_secret_key),
            )
        if response.status_code == 200:
            return True
        if response.status_code == 401:
            logger.warning(
                "Langfuse credentials rejected host=%s public_key_prefix=%s",
                settings.langfuse_host,
                _log_public_key_prefix(),
            )
            return False
        logger.warning(
            "Langfuse auth check returned unexpected status=%d host=%s",
            response.status_code,
            settings.langfuse_host,
        )
        return False
    except httpx.TimeoutException as exc:
        raise TimeoutError(f"Langfuse auth check timed out: {exc}") from exc


async def _initialize_singleton() -> bool:
    if not settings.langfuse_enabled:
        logger.debug("Langfuse not configured - missing keys")
        return False

    _ensure_env_vars_set()

    for attempt in range(1, _MAX_INIT_RETRIES + 1):
        try:
            is_authenticated = await _check_langfuse_auth()
            if not is_authenticated:
                return False

            _configure_langfuse_singleton()
            logger.info(
                "Langfuse client initialized host=%s environment=%s attempt=%d",
                settings.langfuse_host,
                settings.langfuse_environment,
                attempt,
            )
            return True

        except Exception as exc:
            if attempt < _MAX_INIT_RETRIES:
                logger.warning(
                    "Langfuse init failed (attempt %d/%d): %s - retrying in %ds",
                    attempt,
                    _MAX_INIT_RETRIES,
                    exc,
                    _INIT_RETRY_DELAY_SECONDS,
                )
                await asyncio.sleep(_INIT_RETRY_DELAY_SECONDS)
            else:
                logger.warning(
                    "Langfuse init failed after %d attempts: %s - observability disabled",
                    _MAX_INIT_RETRIES,
                    exc,
                )

    return False


async def initialize_langfuse_client() -> Langfuse | None:
    global _langfuse_initialized
    if not _langfuse_initialized and settings.langfuse_enabled:
        _langfuse_initialized = await _initialize_singleton()
    return get_langfuse_client()


def get_langfuse_client() -> Langfuse | None:
    if _langfuse_initialized:
        return get_client()
    return None


def is_langfuse_enabled() -> bool:
    return _langfuse_initialized


def is_prompt_synced() -> bool:
    return _langfuse_prompt_synced


def mark_prompt_synced() -> None:
    global _langfuse_prompt_synced
    _langfuse_prompt_synced = True

import logging

import httpx
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from src.config import Settings


logger = logging.getLogger(__name__)


class LangfuseManager:
    MAX_INIT_RETRIES: int = 3
    INIT_RETRY_DELAY_SECONDS: int = 5
    HTTP_OK: int = 200

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: Langfuse | None = None
        self._initialized = False

    @property
    def is_enabled(self) -> bool:
        return self._initialized and self._client is not None

    @property
    def client(self) -> Langfuse | None:
        return self._client if self._initialized else None

    async def initialize(self) -> None:
        if not self._settings.langfuse_enabled:
            logger.debug("Langfuse not configured - missing keys")
            return

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.MAX_INIT_RETRIES),
                wait=wait_fixed(self.INIT_RETRY_DELAY_SECONDS),
                reraise=True,
            ):
                with attempt:
                    is_authenticated = await self._check_auth()
                    if not is_authenticated:
                        return

                    self._client = Langfuse(
                        public_key=self._settings.langfuse_public_key,
                        secret_key=self._settings.langfuse_secret_key,
                        base_url=self._settings.langfuse_host,
                    )
                    self._initialized = True
                    logger.info(
                        "Langfuse client initialized host=%s environment=%s attempt=%d",
                        self._settings.langfuse_host,
                        self._settings.langfuse_environment,
                        attempt.retry_state.attempt_number,
                    )
                    return
        except Exception as exc:
            logger.warning(
                "Langfuse init failed after %d attempts: %s - observability disabled",
                self.MAX_INIT_RETRIES,
                exc,
            )

    async def _check_auth(self) -> bool:
        url = f"{self._settings.langfuse_host}/api/public/projects"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    auth=(self._settings.langfuse_public_key, self._settings.langfuse_secret_key),
                )
            if response.status_code == self.HTTP_OK:
                return True
            logger.warning(
                "Langfuse auth check returned status=%d host=%s",
                response.status_code,
                self._settings.langfuse_host,
            )
            return False
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Langfuse auth check timed out: {exc}") from exc

    def get_handler(self, session_id: str) -> CallbackHandler | None:
        if not self.is_enabled:
            return None
        try:
            handler = CallbackHandler(
                public_key=self._settings.langfuse_public_key,
            )
            logger.debug("Langfuse handler created session=%s", session_id)
            return handler
        except Exception as exc:
            logger.warning("Failed to create Langfuse handler: %s", exc)
            return None

    def flush(self) -> None:
        if self._client:
            self._client.flush()

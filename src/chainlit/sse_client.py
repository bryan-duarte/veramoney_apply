import json
import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.chainlit.config import ChainlitSettings
from src.chainlit.constants import (
    BACKOFF_MULTIPLIER,
    ERROR_MESSAGE_NETWORK,
    ERROR_MESSAGE_RATE_LIMITED,
    ERROR_MESSAGE_SERVER_ERROR,
    ERROR_MESSAGE_TIMEOUT,
    ERROR_MESSAGE_UNAUTHORIZED,
    HTTP_STATUS_RATE_LIMITED,
)


logger = logging.getLogger(__name__)

_RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.TimeoutException,
)


@dataclass
class SSEEvent:
    type: str
    data: dict[str, object]


class SSEClient:
    def __init__(self, settings: ChainlitSettings) -> None:
        self._settings = settings

    async def stream_chat(
        self,
        message: str,
        session_id: str,
    ) -> AsyncGenerator[SSEEvent, None]:
        last_error: Exception | None = None

        retryer = AsyncRetrying(
            stop=stop_after_attempt(self._settings.max_retries),
            wait=wait_exponential(
                multiplier=self._settings.retry_delay,
                exp_base=BACKOFF_MULTIPLIER,
            ),
            retry=retry_if_exception_type((*_RETRYABLE_EXCEPTIONS, _RetryableHTTPError)),
            reraise=False,
        )

        retry_iterator = retryer.__aiter__()
        attempt_number = 0

        while True:
            attempt_number += 1
            try:
                await retry_iterator.__anext__()
            except StopAsyncIteration:
                break

            try:
                async for event in self._fetch_events(message, session_id):
                    yield event
                return
            except _RETRYABLE_EXCEPTIONS as exc:
                last_error = exc
                self._log_retry_error(exc, attempt_number)
            except _RetryableHTTPError as exc:
                last_error = exc
                logger.warning(
                    "sse_server_error attempt=%d/%d status=%d",
                    attempt_number,
                    self._settings.max_retries,
                    exc.status_code,
                )

        error_message = self._classify_final_error(last_error)
        yield SSEEvent(type="error", data={"message": error_message})

    def _log_retry_error(self, exc: Exception, attempt: int) -> None:
        is_network_error = isinstance(exc, (httpx.ConnectError, httpx.ReadError))
        is_timeout = isinstance(exc, httpx.TimeoutException)

        if is_network_error:
            logger.warning(
                "sse_network_error attempt=%d/%d error=%s",
                attempt,
                self._settings.max_retries,
                str(exc),
            )
        elif is_timeout:
            logger.warning(
                "sse_timeout attempt=%d/%d",
                attempt,
                self._settings.max_retries,
            )

    async def _fetch_events(
        self,
        message: str,
        session_id: str,
    ) -> AsyncGenerator[SSEEvent, None]:
        timeout = httpx.Timeout(
            connect=10.0, read=self._settings.request_timeout, write=10.0, pool=5.0
        )

        async with (
            httpx.AsyncClient(timeout=timeout) as client,
            client.stream(
                "POST",
                f"{self._settings.backend_url}/chat",
                json={"message": message, "session_id": session_id},
                headers={
                    "X-API-Key": self._settings.api_key,
                    "Accept": "text/event-stream",
                },
            ) as response,
        ):
            if not response.is_success:
                if response.status_code in (401, 403):
                    yield SSEEvent(
                        type="error", data={"message": ERROR_MESSAGE_UNAUTHORIZED}
                    )
                    return
                if response.status_code == HTTP_STATUS_RATE_LIMITED:
                    yield SSEEvent(
                        type="error", data={"message": ERROR_MESSAGE_RATE_LIMITED}
                    )
                    return
                raise _RetryableHTTPError(response.status_code)

            current_event: str | None = None

            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    current_event = line[len("event:") :].strip()
                elif line.startswith("data:"):
                    raw_data = line[len("data:") :].strip()
                    if not raw_data:
                        continue

                    try:
                        data: dict[str, object] = json.loads(raw_data)
                    except json.JSONDecodeError:
                        logger.warning("sse_parse_error raw=%s", raw_data)
                        current_event = None
                        continue

                    event_type = current_event or "token"
                    event = SSEEvent(type=event_type, data=data)
                    yield event

                    if event_type == "done":
                        return

                    current_event = None

    def _classify_final_error(self, error: Exception | None) -> str:
        if isinstance(error, httpx.TimeoutException):
            return ERROR_MESSAGE_TIMEOUT
        if isinstance(error, (httpx.ConnectError, httpx.ReadError)):
            return ERROR_MESSAGE_NETWORK
        if isinstance(error, _RetryableHTTPError):
            return ERROR_MESSAGE_SERVER_ERROR
        return ERROR_MESSAGE_SERVER_ERROR


class _RetryableHTTPError(Exception):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Retryable HTTP error: {status_code}")

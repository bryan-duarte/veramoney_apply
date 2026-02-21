import asyncio
import logging
from datetime import datetime
from typing import Any

from langfuse.api.resources.commons.errors.not_found_error import NotFoundError

from src.config import Settings
from src.observability.manager import LangfuseManager
from src.prompts import (
    KNOWLEDGE_WORKER_PROMPT,
    STOCK_WORKER_PROMPT,
    SUPERVISOR_SYSTEM_PROMPT_FALLBACK,
    WEATHER_WORKER_PROMPT,
)


logger = logging.getLogger(__name__)

PROMPT_NAME_SUPERVISOR = "vera-supervisor-prompt"
PROMPT_NAME_WEATHER_WORKER = "vera-weather-worker"
PROMPT_NAME_STOCK_WORKER = "vera-stock-worker"
PROMPT_NAME_KNOWLEDGE_WORKER = "vera-knowledge-worker"

WORKER_PROMPT_MAP: dict[str, str] = {
    "weather": WEATHER_WORKER_PROMPT,
    "stock": STOCK_WORKER_PROMPT,
    "knowledge": KNOWLEDGE_WORKER_PROMPT,
}

WORKER_PROMPT_NAME_MAP: dict[str, str] = {
    "weather": PROMPT_NAME_WEATHER_WORKER,
    "stock": PROMPT_NAME_STOCK_WORKER,
    "knowledge": PROMPT_NAME_KNOWLEDGE_WORKER,
}

CHAT_PROMPT_TEMPLATE = [
    {"type": "placeholder", "name": "chat_history"},
    {"role": "user", "content": "{{user_message}}"},
]


class PromptManager:
    AGENT_VERSION = "2.0"
    PROMPT_TYPE: str = "chat"

    def __init__(
        self,
        settings: Settings,
        langfuse_manager: LangfuseManager | None = None,
    ):
        self._settings = settings
        self._langfuse_manager = langfuse_manager

    @property
    def _langfuse_available(self) -> bool:
        return self._langfuse_manager is not None and self._langfuse_manager.is_enabled

    @property
    def _client(self):
        return self._langfuse_manager.client if self._langfuse_available else None

    async def sync_to_langfuse(self) -> None:
        if not self._langfuse_available:
            return

        logger.info("Syncing prompts to Langfuse...")
        sync_results = await asyncio.gather(
            self.sync_supervisor_prompt(),
            self.sync_worker_prompts(),
            return_exceptions=True,
        )

        errors = [r for r in sync_results if isinstance(r, Exception)]
        if errors:
            for error in errors:
                logger.warning("Prompt sync error: %s", error)
        else:
            logger.info("All prompts synced successfully")

    async def sync_supervisor_prompt(self) -> None:
        if not self._langfuse_available:
            return
        await self._sync_chat_prompt(
            prompt_name=PROMPT_NAME_SUPERVISOR,
            system_content=SUPERVISOR_SYSTEM_PROMPT_FALLBACK,
        )

    async def sync_worker_prompts(self) -> None:
        if not self._langfuse_available:
            return
        for worker_name, prompt_name in WORKER_PROMPT_NAME_MAP.items():
            fallback_content = WORKER_PROMPT_MAP.get(worker_name, "")
            await self._sync_text_prompt(
                prompt_name=prompt_name,
                fallback_content=fallback_content,
            )

    async def _sync_chat_prompt(self, prompt_name: str, system_content: str) -> None:
        expected_messages = [
            {"role": "system", "content": system_content},
            *CHAT_PROMPT_TEMPLATE,
        ]
        existing_system_content = await self._fetch_existing_system_content(prompt_name)
        prompt_exists = existing_system_content is not None
        content_matches = existing_system_content == system_content

        if content_matches:
            logger.debug("Prompt '%s' already synced", prompt_name)
            return

        try:
            await asyncio.to_thread(
                self._client.create_prompt,
                name=prompt_name,
                type=self.PROMPT_TYPE,
                prompt=expected_messages,
                labels=["production"],
            )
            sync_action = "Created" if not prompt_exists else "Updated"
            logger.info("%s chat-type prompt '%s'", sync_action, prompt_name)
        except Exception as exc:
            logger.warning("Failed to sync prompt '%s': %s", prompt_name, exc)
            raise

    async def _sync_text_prompt(self, prompt_name: str, fallback_content: str) -> None:
        existing_content = await self._fetch_existing_text_content(prompt_name)
        prompt_exists = existing_content is not None
        content_matches = existing_content == fallback_content

        if content_matches:
            logger.debug("Prompt '%s' already synced", prompt_name)
            return

        try:
            await asyncio.to_thread(
                self._client.create_prompt,
                name=prompt_name,
                type="text",
                prompt=fallback_content,
                labels=["production"],
            )
            sync_action = "Created" if not prompt_exists else "Updated"
            logger.info("%s text-type prompt '%s'", sync_action, prompt_name)
        except Exception as exc:
            logger.warning("Failed to sync prompt '%s': %s", prompt_name, exc)
            raise

    async def _fetch_existing_system_content(self, prompt_name: str) -> str | None:
        langfuse_prompt = await self._safe_get_prompt(prompt_name, type=self.PROMPT_TYPE)
        if langfuse_prompt is None:
            return None
        return self._extract_system_content(langfuse_prompt.prompt)

    async def _fetch_existing_text_content(self, prompt_name: str) -> str | None:
        langfuse_prompt = await self._safe_get_prompt(prompt_name)
        if langfuse_prompt is None:
            return None
        return langfuse_prompt.prompt

    async def _safe_get_prompt(self, prompt_name: str, **kwargs: Any) -> Any:
        try:
            return await asyncio.to_thread(
                self._client.get_prompt,
                prompt_name,
                **kwargs,
            )
        except NotFoundError:
            logger.debug("Prompt '%s' not found in Langfuse (will be created)", prompt_name)
            return None
        except Exception as exc:
            logger.debug("Could not fetch prompt '%s': %s", prompt_name, exc)
            return None

    def get_compiled_supervisor_prompt(self) -> tuple[str, dict]:
        current_date = datetime.now().strftime("%d %B, %y")
        if not self._langfuse_available:
            return self._apply_template_vars(SUPERVISOR_SYSTEM_PROMPT_FALLBACK, current_date), {"prompt_source": "fallback"}
        try:
            langfuse_prompt = self._client.get_prompt(PROMPT_NAME_SUPERVISOR, type=self.PROMPT_TYPE)
            system_content = self._extract_system_content(langfuse_prompt.prompt)
            compiled = self._apply_template_vars(system_content, current_date)
            return compiled, {
                "prompt_source": "langfuse",
                "prompt_name": PROMPT_NAME_SUPERVISOR,
                "prompt_version": langfuse_prompt.version,
                "langfuse_prompt": langfuse_prompt,
            }
        except Exception as exc:
            logger.warning("Failed to compile supervisor prompt from Langfuse, using fallback: %s", exc)
            return self._apply_template_vars(SUPERVISOR_SYSTEM_PROMPT_FALLBACK, current_date), {"prompt_source": "fallback"}

    def get_worker_prompt(self, worker_name: str) -> tuple[str, dict]:
        current_date = datetime.now().strftime("%d %B, %y")
        fallback_prompt = WORKER_PROMPT_MAP.get(worker_name, "")
        prompt_name = WORKER_PROMPT_NAME_MAP.get(worker_name)
        if not self._langfuse_available or prompt_name is None:
            return self._apply_worker_template_vars(fallback_prompt, current_date), {"prompt_source": "fallback"}
        try:
            langfuse_prompt = self._client.get_prompt(prompt_name)
            compiled = self._apply_worker_template_vars(langfuse_prompt.prompt, current_date)
            return compiled, {
                "prompt_source": "langfuse",
                "prompt_name": prompt_name,
                "prompt_version": langfuse_prompt.version,
            }
        except Exception as exc:
            logger.warning("Failed to fetch worker prompt '%s' from Langfuse, using fallback: %s", worker_name, exc)
            return self._apply_worker_template_vars(fallback_prompt, current_date), {"prompt_source": "fallback"}

    def _apply_template_vars(self, content: str, current_date: str) -> str:
        content = content.replace("{{current_date}}", current_date)
        content = content.replace("{{model_name}}", self._settings.agent_model)
        content = content.replace("{{version}}", self.AGENT_VERSION)
        return content

    @staticmethod
    def _apply_worker_template_vars(content: str, current_date: str) -> str:
        return content.replace("{{current_date}}", current_date)

    @staticmethod
    def _extract_system_content(prompt_messages: list[dict]) -> str:
        for msg in prompt_messages:
            if msg.get("role") == "system":
                return msg.get("content", "")
        return ""


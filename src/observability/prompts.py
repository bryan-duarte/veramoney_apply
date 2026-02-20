import logging
from datetime import datetime
from typing import Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.agent.core.prompts import VERA_FALLBACK_SYSTEM_PROMPT
from src.config import Settings
from src.observability.manager import LangfuseManager


logger = logging.getLogger(__name__)

PROMPT_NAME_VERA_SYSTEM = "vera-system-prompt"


class PromptManager:
    AGENT_VERSION = "1.0"
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
        try:
            self._client.get_prompt(PROMPT_NAME_VERA_SYSTEM, type=self.PROMPT_TYPE)
            logger.info("Prompt '%s' already exists in Langfuse - skipping creation", PROMPT_NAME_VERA_SYSTEM)
        except Exception:
            try:
                self._client.create_prompt(
                    name=PROMPT_NAME_VERA_SYSTEM,
                    type=self.PROMPT_TYPE,
                    prompt=[
                        {"role": "system", "content": VERA_FALLBACK_SYSTEM_PROMPT},
                        {"type": "placeholder", "name": "chat_history"},
                        {"role": "user", "content": "{{user_message}}"},
                    ],
                    labels=["production"],
                )
                logger.info("Created chat-type prompt '%s' in Langfuse", PROMPT_NAME_VERA_SYSTEM)
            except Exception as exc:
                logger.warning("Failed to create prompt '%s' in Langfuse: %s", PROMPT_NAME_VERA_SYSTEM, exc)

    def get_compiled_system_prompt(self) -> tuple[str, dict]:
        current_date = datetime.now().strftime("%d %B, %y")
        if not self._langfuse_available:
            return self._apply_template_vars(VERA_FALLBACK_SYSTEM_PROMPT, current_date), {"prompt_source": "fallback"}
        try:
            langfuse_prompt = self._client.get_prompt(PROMPT_NAME_VERA_SYSTEM, type=self.PROMPT_TYPE)
            system_content = self._extract_system_content(langfuse_prompt.prompt)
            compiled = self._apply_template_vars(system_content, current_date)
            return compiled, {
                "prompt_source": "langfuse",
                "prompt_name": PROMPT_NAME_VERA_SYSTEM,
                "prompt_version": langfuse_prompt.version,
                "langfuse_prompt": langfuse_prompt,
            }
        except Exception as exc:
            logger.warning("Failed to compile prompt from Langfuse, using fallback: %s", exc)
            return self._apply_template_vars(VERA_FALLBACK_SYSTEM_PROMPT, current_date), {"prompt_source": "fallback"}

    def get_langchain_template(self) -> ChatPromptTemplate:
        if not self._langfuse_available:
            return self._build_fallback_template(VERA_FALLBACK_SYSTEM_PROMPT)
        try:
            langfuse_prompt = self._client.get_prompt(PROMPT_NAME_VERA_SYSTEM, type=self.PROMPT_TYPE)
            langchain_messages = langfuse_prompt.get_langchain_prompt()
            template = ChatPromptTemplate.from_messages(langchain_messages)
            template.metadata = {"langfuse_prompt": langfuse_prompt}
            return template
        except Exception as exc:
            logger.warning("Failed to fetch prompt from Langfuse, using fallback: %s", exc)
            return self._build_fallback_template(VERA_FALLBACK_SYSTEM_PROMPT)

    def get_langfuse_prompt(self) -> Any:
        _, metadata = self.get_compiled_system_prompt()
        return metadata.get("langfuse_prompt")

    def _apply_template_vars(self, content: str, current_date: str) -> str:
        content = content.replace("{{current_date}}", current_date)
        content = content.replace("{{model_name}}", self._settings.agent_model)
        content = content.replace("{{version}}", self.AGENT_VERSION)
        return content

    @staticmethod
    def _extract_system_content(prompt_messages: list[dict]) -> str:
        for msg in prompt_messages:
            if msg.get("role") == "system":
                return msg.get("content", "")
        return ""

    @staticmethod
    def _build_fallback_template(system_content: str) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", system_content),
            MessagesPlaceholder("chat_history"),
            ("human", "{user_message}"),
        ])

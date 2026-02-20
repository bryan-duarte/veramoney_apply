import logging
from datetime import datetime

from langfuse import Langfuse
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

PROMPT_NAME_VERA_SYSTEM = "vera-system-prompt"
PROMPT_TYPE = "chat"
PROMPT_VERSION = "1.0"


def format_current_date() -> str:
    return datetime.now().strftime("%d %B, %y")


def sync_prompt_to_langfuse(
    client: Langfuse | None,
    prompt_name: str,
    prompt_content: str,
) -> None:
    if client is None:
        return

    try:
        client.get_prompt(prompt_name, type=PROMPT_TYPE)
        logger.info("Prompt '%s' already exists in Langfuse - skipping creation", prompt_name)

    except Exception:
        try:
            client.create_prompt(
                name=prompt_name,
                type=PROMPT_TYPE,
                prompt=[
                    {"role": "system", "content": prompt_content},
                    {"type": "placeholder", "name": "chat_history"},
                    {"role": "user", "content": "{{user_message}}"},
                ],
                labels=["production"],
            )
            logger.info("Created chat-type prompt '%s' in Langfuse", prompt_name)

        except Exception as exc:
            logger.warning("Failed to create prompt '%s' in Langfuse: %s", prompt_name, exc)


def get_langchain_prompt(
    client: Langfuse | None,
    fallback_system: str,
) -> tuple[ChatPromptTemplate, dict]:
    if client is None:
        return _create_fallback_template(fallback_system), {"prompt_source": "fallback"}

    try:
        langfuse_prompt = client.get_prompt(PROMPT_NAME_VERA_SYSTEM, type=PROMPT_TYPE)
        langchain_messages = langfuse_prompt.get_langchain_prompt()

        template = ChatPromptTemplate.from_messages(langchain_messages)
        template.metadata = {"langfuse_prompt": langfuse_prompt}

        prompt_metadata = {
            "prompt_source": "langfuse",
            "prompt_name": PROMPT_NAME_VERA_SYSTEM,
            "prompt_version": langfuse_prompt.version,
        }

        return template, prompt_metadata

    except Exception as exc:
        logger.warning("Failed to fetch prompt from Langfuse, using fallback: %s", exc)
        return _create_fallback_template(fallback_system), {"prompt_source": "fallback"}


def get_compiled_system_prompt(
    client: Langfuse | None,
    fallback_system: str,
    current_date: str,
    model_name: str,
    version: str = PROMPT_VERSION,
) -> tuple[str, dict]:
    if client is None:
        return _compile_fallback(fallback_system, current_date, model_name, version), {
            "prompt_source": "fallback",
        }

    try:
        langfuse_prompt = client.get_prompt(PROMPT_NAME_VERA_SYSTEM, type=PROMPT_TYPE)

        prompt_messages = langfuse_prompt.prompt
        system_content = _extract_system_content(prompt_messages)

        compiled = system_content.replace("{{current_date}}", current_date)
        compiled = compiled.replace("{{model_name}}", model_name)
        compiled = compiled.replace("{{version}}", version)

        prompt_metadata = {
            "prompt_source": "langfuse",
            "prompt_name": PROMPT_NAME_VERA_SYSTEM,
            "prompt_version": langfuse_prompt.version,
            "langfuse_prompt": langfuse_prompt,
        }

        return compiled, prompt_metadata

    except Exception as exc:
        logger.warning("Failed to compile prompt from Langfuse, using fallback: %s", exc)
        return _compile_fallback(fallback_system, current_date, model_name, version), {
            "prompt_source": "fallback",
        }


def _extract_system_content(prompt_messages: list[dict]) -> str:
    for msg in prompt_messages:
        is_system_message = msg.get("role") == "system"
        if is_system_message:
            return msg.get("content", "")
    return ""


def _compile_fallback(
    system_content: str,
    current_date: str,
    model_name: str,
    version: str,
) -> str:
    compiled = system_content.replace("{{current_date}}", current_date)
    compiled = compiled.replace("{{model_name}}", model_name)
    compiled = compiled.replace("{{version}}", version)
    return compiled


def _create_fallback_template(system_content: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", system_content),
        MessagesPlaceholder("chat_history"),
        ("human", "{user_message}"),
    ])

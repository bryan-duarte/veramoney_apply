import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request

from src.agent.memory.store import MemoryStore
from src.config import Settings, settings
from src.observability.datasets import DatasetManager
from src.observability.manager import LangfuseManager
from src.observability.prompts import PromptManager
from src.rag.retriever import KnowledgeRetriever


SettingsDep = Annotated[Settings, Depends(lambda: settings)]


def get_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> str:
    is_api_key_missing = x_api_key is None
    is_api_key_invalid = not secrets.compare_digest(x_api_key or "", settings.api_key)

    if is_api_key_missing or is_api_key_invalid:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return x_api_key


def get_memory_store(request: Request) -> MemoryStore:
    return request.app.state.memory_store


def get_langfuse_manager(request: Request) -> LangfuseManager | None:
    return request.app.state.langfuse_manager


def get_dataset_manager(request: Request) -> DatasetManager:
    return request.app.state.dataset_manager


def get_prompt_manager(request: Request) -> PromptManager | None:
    return request.app.state.prompt_manager


def get_knowledge_retriever(request: Request) -> KnowledgeRetriever | None:
    return getattr(request.app.state, "knowledge_retriever", None)


APIKeyDep = Annotated[str, Depends(get_api_key)]
MemoryStoreDep = Annotated[MemoryStore, Depends(get_memory_store)]
LangfuseManagerDep = Annotated[LangfuseManager | None, Depends(get_langfuse_manager)]
DatasetManagerDep = Annotated[DatasetManager, Depends(get_dataset_manager)]
PromptManagerDep = Annotated[PromptManager | None, Depends(get_prompt_manager)]
KnowledgeRetrieverDep = Annotated[KnowledgeRetriever | None, Depends(get_knowledge_retriever)]

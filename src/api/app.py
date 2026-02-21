import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.agent.memory.store import MemoryStore
from src.api.core import (
    global_exception_handler,
    limiter,
    rate_limit_handler,
    security_headers_middleware,
)
from src.api.endpoints import chat_complete_router, chat_stream_router, health_router
from src.config import configure_logging, settings
from src.observability.datasets import DatasetManager
from src.observability.manager import LangfuseManager
from src.observability.prompts import PromptManager
from src.rag.pipeline import RAGPipeline
from src.tools.stock.tool import get_shared_stock_client
from src.tools.weather.tool import get_shared_weather_client


_LOG_LEVEL = configure_logging()

logger = logging.getLogger(__name__)
logger.info("Logging configured: level=%s", _LOG_LEVEL)


OPENAPI_TAGS_METADATA = [
    {
        "name": "health",
        "description": "Health check endpoints for monitoring systems and load balancers. "
        "Use these endpoints to verify the API is running and responsive.",
    },
    {
        "name": "chat",
        "description": "Conversational AI endpoints for interacting with the Vera assistant. "
        "**Features:**\n"
        "- Multi-turn conversation with context management\n"
        "- Tool calling for weather and stock data\n"
        "- Both streaming (SSE) and complete response modes\n\n"
        "The assistant can answer questions about weather conditions and stock prices "
        "by automatically calling the appropriate tools.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("=" * 60)
    logger.info("APPLICATION STARTUP")
    logger.info("=" * 60)

    langfuse_manager = LangfuseManager(settings=settings)
    await langfuse_manager.initialize()

    prompt_manager: PromptManager | None = None
    if langfuse_manager.is_enabled:
        prompt_manager = PromptManager(settings=settings, langfuse_manager=langfuse_manager)
        await prompt_manager.sync_to_langfuse()
        logger.info("Langfuse client initialized")
    else:
        logger.debug("Langfuse not configured - observability disabled")

    rag_pipeline = RAGPipeline(settings=settings)
    rag_init_success = False
    try:
        await rag_pipeline.initialize()
        rag_init_success = rag_pipeline.is_ready
        if rag_init_success:
            app.state.knowledge_retriever = rag_pipeline.retriever
        if rag_pipeline.has_errors:
            for error in rag_pipeline.status.errors:
                logger.warning("  - %s", error)
    except Exception as error:
        logger.exception("RAG PIPELINE FAILED: %s", str(error))
        logger.warning("Application will continue WITHOUT knowledge base")

    memory_store = MemoryStore(settings=settings)
    await memory_store.initialize()

    app.state.memory_store = memory_store
    app.state.langfuse_manager = langfuse_manager
    app.state.dataset_manager = DatasetManager(langfuse_manager=langfuse_manager)
    app.state.prompt_manager = prompt_manager

    logger.info("-" * 60)
    logger.info("AVAILABLE TOOLS:")
    logger.info("  - get_weather: %s", "enabled" if settings.weatherapi_key else "disabled (no API key)")
    logger.info("  - get_stock_price: %s", "enabled" if settings.finnhub_api_key else "disabled (no API key)")
    logger.info("  - search_knowledge: %s", "enabled" if rag_init_success else "disabled (RAG failed)")
    logger.info("  - langfuse: %s", "enabled" if langfuse_manager.is_enabled else "disabled (no keys)")
    logger.info("=" * 60)
    logger.info("APPLICATION READY")
    logger.info("=" * 60)

    yield

    logger.info("=" * 60)
    logger.info("APPLICATION SHUTDOWN")
    logger.info("=" * 60)

    await memory_store.close()

    try:
        await get_shared_weather_client().aclose()
        await get_shared_stock_client().aclose()
    except Exception:
        logger.exception("Error closing HTTP clients")

    langfuse_manager.flush()
    logger.info("Application shutdown complete")


class CustomOpenAPI:
    def __init__(self, app: FastAPI) -> None:
        self._app = app

    def __call__(self) -> dict:
        if self._app.openapi_schema:
            return self._app.openapi_schema

        openapi_schema = get_openapi(
            title="VeraMoney API",
            version="0.1.0",
            description="AI-powered financial assistant API with weather and stock tools.\n\n"
            "**Authentication:** All endpoints except `/health` require an API key via the `X-API-Key` header.\n\n"
            "**Rate Limiting:** 60 requests per minute per API key.",
            routes=self._app.routes,
            tags=OPENAPI_TAGS_METADATA,
        )

        openapi_schema["info"]["contact"] = {
            "name": "VeraMoney API Support",
            "email": "api-support@veramoney.com",
        }

        openapi_schema["info"]["license"] = {
            "name": "Proprietary",
        }

        openapi_schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key authentication for all chat endpoints",
            }
        }

        openapi_schema["security"] = [{"ApiKeyAuth": []}]

        self._app.openapi_schema = openapi_schema
        return self._app.openapi_schema


def create_app() -> FastAPI:
    docs_url = "/docs" if settings.docs_enabled else None
    redoc_url = "/redoc" if settings.docs_enabled else None
    openapi_url = "/openapi.json" if settings.docs_enabled else None

    app = FastAPI(
        title="VeraMoney API",
        description="AI-powered financial assistant API with weather and stock tools.\n\n"
        "**Authentication:** All endpoints except `/health` require an API key via the `X-API-Key` header.\n\n"
        "**Rate Limiting:** 60 requests per minute per API key.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        openapi_tags=OPENAPI_TAGS_METADATA,
    )

    if settings.docs_enabled:
        app.openapi = CustomOpenAPI(app)

    app.state.limiter = limiter

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    app.add_middleware(SlowAPIMiddleware)

    app.middleware("http")(security_headers_middleware)

    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    app.include_router(health_router)
    app.include_router(chat_stream_router)
    app.include_router(chat_complete_router)

    return app


app = create_app()

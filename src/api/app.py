import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.agent.core.prompts import VERA_SYSTEM_PROMPT
from src.api.core import (
    global_exception_handler,
    limiter,
    rate_limit_handler,
    security_headers_middleware,
)
from src.api.endpoints import chat_complete_router, chat_stream_router, health_router
from src.config import configure_logging
from src.config import settings
from src.observability import (
    PROMPT_NAME_VERA_SYSTEM,
    initialize_langfuse_client,
    is_langfuse_enabled,
    mark_prompt_synced,
    sync_prompt_to_langfuse,
)
from src.rag import initialize_rag_pipeline
from src.tools.knowledge import configure_knowledge_client


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

    langfuse_client = await initialize_langfuse_client()
    if langfuse_client:
        logger.info("Langfuse client initialized")
        sync_prompt_to_langfuse(
            client=langfuse_client,
            prompt_name=PROMPT_NAME_VERA_SYSTEM,
            prompt_content=VERA_SYSTEM_PROMPT,
        )
        mark_prompt_synced()
    else:
        logger.debug("Langfuse not configured - observability disabled")

    rag_init_success = False

    try:
        retriever, status = await initialize_rag_pipeline(
            chroma_host=settings.chroma_host,
            chroma_port=settings.chroma_port,
            collection_name=settings.rag_collection_name,
            openai_api_key=settings.openai_api_key,
            embedding_model=settings.openai_embedding_model,
            retrieval_k=settings.rag_retrieval_k,
        )

        configure_knowledge_client(retriever)
        rag_init_success = True

        if status.errors:
            logger.warning("RAG completed with %d error(s):", len(status.errors))
            for error in status.errors:
                logger.warning("  - %s", error)

    except Exception as error:
        logger.exception("RAG PIPELINE FAILED: %s", str(error))
        logger.warning("Application will continue WITHOUT knowledge base")
        logger.warning("Only weather and stock tools will be available")

    app.state.rag_initialized = rag_init_success

    logger.info("-" * 60)
    logger.info("AVAILABLE TOOLS:")
    logger.info("  - get_weather: %s", "enabled" if settings.weatherapi_key else "disabled (no API key)")
    logger.info("  - get_stock_price: %s", "enabled" if settings.finnhub_api_key else "disabled (no API key)")
    logger.info("  - search_knowledge: %s", "enabled" if rag_init_success else "disabled (RAG failed)")
    logger.info("  - langfuse: %s", "enabled" if langfuse_client else "disabled (no keys)")
    logger.info("=" * 60)
    logger.info("APPLICATION READY")
    logger.info("=" * 60)

    yield

    logger.info("=" * 60)
    logger.info("APPLICATION SHUTDOWN")
    logger.info("=" * 60)

    if is_langfuse_enabled() and langfuse_client:
        langfuse_client.flush()
        logger.info("Langfuse traces flushed")


def _build_custom_openapi(app: FastAPI):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title="VeraMoney API",
            version="0.1.0",
            description="AI-powered financial assistant API with weather and stock tools.\n\n"
            "**Authentication:** All endpoints except `/health` require an API key via the `X-API-Key` header.\n\n"
            "**Rate Limiting:** 60 requests per minute per API key.",
            routes=app.routes,
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

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return custom_openapi


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
        app.openapi = _build_custom_openapi(app)

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

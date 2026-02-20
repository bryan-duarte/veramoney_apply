import uvicorn

from src.config import settings

CHAINLIT_PORT = 8002


def _print_startup_info() -> None:
    fastapi_url = f"http://localhost:{settings.app_port}"
    chainlit_url = f"http://localhost:{CHAINLIT_PORT}"
    langfuse_url = settings.langfuse_host

    print("\nService URLs:")
    print(f"  FastAPI App  : {fastapi_url}")
    print(f"  Chainlit UI  : {chainlit_url}")
    print(f"  Langfuse Web : {langfuse_url}")
    print(f"  API Docs     : {fastapi_url}/docs\n")


def main() -> None:
    _print_startup_info()
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

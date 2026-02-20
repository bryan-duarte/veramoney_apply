import uvicorn

from src.config import settings


def main() -> None:
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

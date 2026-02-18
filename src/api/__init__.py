"""API layer for the VeraMoney application.

This package implements the Clean Architecture API layer with:
- main.py: FastAPI application factory
- dependencies.py: Dependency injection container
- endpoints/: API endpoint modules
"""

from src.api.main import app, create_app

__all__ = ["app", "create_app"]

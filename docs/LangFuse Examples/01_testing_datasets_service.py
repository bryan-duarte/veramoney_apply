"""
LangFuse Dataset Management Example

This file demonstrates how to use LangFuse for AI evaluation datasets.
Source: clickbait project - app/services/ai/testing_datasets_service.py

Key patterns:
- Creating/finding datasets
- Adding examples to datasets
- Non-blocking error handling
- Explicit Langfuse client initialization
"""

import logging
import traceback
from typing import Any

from langfuse import Langfuse
from enum import Enum


class DatasetServiceError(Exception):
    """Base exception for dataset service errors."""


class DatasetNotFoundError(DatasetServiceError):
    """Exception when a dataset is not found."""


class DatasetCreationError(DatasetServiceError):
    """Exception when dataset creation fails."""


class ExampleCreationError(DatasetServiceError):
    """Exception when creating an example in the dataset fails."""


class TestingDatasetsEnum(Enum):
    """Example enum for dataset names."""
    NEWS_INFO_TO_GROUP = "NEWS_INFO_TO_GROUP"
    NEWS_INFO_TO_CLASSIFY = "NEWS_INFO_TO_CLASSIFY"
    INDIVIDUAL_NEWS = "INDIVIDUAL_NEWS"
    MARKDOWN_TO_EXTRACT_NEWS = "MARKDOWN_TO_EXTRACT_NEWS"


class TestingDatasetsService:
    """Service for managing LangFuse datasets for AI evaluation.

    Usage:
        from langfuse import Langfuse
        from app.core.config import settings

        langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )
        dataset_service = TestingDatasetsService(langfuse_client)

        dataset_service.add_example_to_dataset(
            info_to_add="Sample content to evaluate",
            dataset_enum=TestingDatasetsEnum.INDIVIDUAL_NEWS,
            additional_inputs={"source": "web", "category": "tech"}
        )
    """

    def __init__(self, langfuse_client: Langfuse):
        if not langfuse_client:
            raise ValueError(
                "Langfuse client is required. Use: "
                "Langfuse(public_key=LANGFUSE_PUBLIC_KEY, secret_key=LANGFUSE_SECRET_KEY, host=LANGFUSE_BASE_URL)"
            )
        self.langfuse_client = langfuse_client

    def _find_or_create(self, dataset_name: str) -> bool:
        """Find a dataset by name or create it if it doesn't exist.

        Args:
            dataset_name: Name of the dataset to find or create.

        Returns:
            True if dataset exists or was created successfully.

        Raises:
            DatasetCreationError: If dataset creation fails.
        """
        try:
            from langfuse.api.resources.commons.errors.not_found_error import NotFoundError

            self.langfuse_client.get_dataset(dataset_name)
            logging.debug(f"Dataset '{dataset_name}' found successfully")
            return True

        except NotFoundError:
            try:
                self.langfuse_client.create_dataset(name=dataset_name)
                self.langfuse_client.flush()

                logging.info(f"Dataset '{dataset_name}' created successfully")
                return True

            except Exception as create_error:
                logging.exception(f"Error creating dataset '{dataset_name}': {create_error}")
                raise DatasetCreationError(
                    f"Failed to create dataset '{dataset_name}': {create_error}",
                ) from create_error

        except Exception as read_error:
            logging.exception(f"Error reading dataset '{dataset_name}': {read_error}")
            raise

    def add_example_to_dataset(
        self,
        info_to_add: str,
        dataset_enum: TestingDatasetsEnum,
        additional_inputs: dict[str, Any] | None = None,
    ) -> bool:
        """Add a single example to the specified dataset.

        Args:
            info_to_add: The input data for the example.
            dataset_enum: The enum member for the target dataset.
            additional_inputs: Additional input fields to include.

        Returns:
            True if the example was added successfully, False otherwise.
        """
        try:
            dataset_name = dataset_enum.value

            self._find_or_create(dataset_name)

            inputs = {"input": info_to_add}

            if additional_inputs:
                inputs.update(additional_inputs)

            self.langfuse_client.create_dataset_item(
                dataset_name=dataset_name,
                input=inputs,
                expected_output=None,
            )

            self.langfuse_client.flush()

            logging.info(f"Example added to dataset '{dataset_name}' successfully")
            return True

        except DatasetCreationError as e:
            logging.warning(
                f"[Non blocking error] Dataset creation failed for '{dataset_enum.value}': {e}"
            )
            return False

        except Exception as e:
            logging.warning(
                f"[Non blocking error] Failed to add example to dataset '{dataset_enum.value}': {e}",
            )
            logging.debug(traceback.format_exc())
            return False


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    import os

    langfuse_client = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
    )

    service = TestingDatasetsService(langfuse_client)

    success = service.add_example_to_dataset(
        info_to_add="This is a sample news article content...",
        dataset_enum=TestingDatasetsEnum.INDIVIDUAL_NEWS,
        additional_inputs={
            "article_title": "Sample Title",
            "url": "https://example.com/article",
        },
    )

    print(f"Example added: {success}")

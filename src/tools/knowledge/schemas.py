from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator


class DocumentTypeFilter(StrEnum):
    VERA_HISTORY = "vera_history"
    FINTEC_REGULATION = "fintec_regulation"
    BANK_REGULATION = "bank_regulation"


class KnowledgeInput(BaseModel):
    QUERY_MIN_LENGTH: ClassVar[int] = 1
    QUERY_MAX_LENGTH: ClassVar[int] = 1000

    query: str = Field(
        min_length=1,
        max_length=1000,
        description="Search query to find relevant information in the knowledge base",
    )
    document_type: str | None = Field(
        default=None,
        description="Optional filter: vera_history, fintec_regulation, or bank_regulation",
    )

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        return value.strip()

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip().lower()

        valid_types = {
            DocumentTypeFilter.VERA_HISTORY.value,
            DocumentTypeFilter.FINTEC_REGULATION.value,
            DocumentTypeFilter.BANK_REGULATION.value,
        }

        is_valid_type = normalized_value in valid_types

        if not is_valid_type:
            return None

        return normalized_value


class RetrievedChunkOutput(BaseModel):
    content: str = Field(description="Text content of the retrieved chunk")
    document_title: str = Field(description="Human-readable document title")
    document_type: str = Field(description="Document type classification")
    page_number: int = Field(description="Original page number in PDF")
    relevance_score: float = Field(description="Similarity score from vector search")


class KnowledgeOutput(BaseModel):
    query: str = Field(description="The original search query")
    chunks: list[RetrievedChunkOutput] = Field(
        default_factory=list,
        description="List of retrieved chunks with metadata",
    )
    total_results: int = Field(description="Total number of chunks retrieved")


class KnowledgeError(BaseModel):
    error: str = Field(description="Error message describing what went wrong")

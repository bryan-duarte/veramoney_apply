from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    VERA_HISTORY = "vera_history"
    FINTEC_REGULATION = "fintec_regulation"
    BANK_REGULATION = "bank_regulation"


class DocumentConfig(BaseModel):
    key: str = Field(description="Unique identifier for the document")
    url: str = Field(description="URL to download the PDF document")
    document_type: DocumentType = Field(description="Type classification for the document")
    title: str = Field(description="Human-readable title for the document")
    language: str = Field(description="Language code (e.g., 'es' for Spanish)")
    chunk_size: int = Field(description="Character count for text chunking")
    chunk_overlap: int = Field(description="Character overlap between consecutive chunks")


class ChunkMetadata(BaseModel):
    document_type: str = Field(description="Document type classification")
    source_url: str = Field(description="Original PDF URL")
    document_title: str = Field(description="Human-readable document title")
    language: str = Field(description="Language code")
    page_number: int = Field(description="Original page number in PDF")
    chunk_index: int = Field(description="Position of chunk within document")


class RetrievalResult(BaseModel):
    content: str = Field(description="Text content of the retrieved chunk")
    metadata: ChunkMetadata = Field(description="Metadata associated with the chunk")
    relevance_score: float = Field(description="Similarity score from vector search")


class RAGPipelineStatus(BaseModel):
    status: str = Field(description="Pipeline status: initialized, loading, ready, error")
    document_count: int = Field(default=0, description="Number of documents indexed")
    chunk_count: int = Field(default=0, description="Total chunks in vector store")
    errors: list[str] = Field(default_factory=list, description="Error messages if any")

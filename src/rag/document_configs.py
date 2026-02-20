from src.rag.schemas import ChunkMetadata, DocumentConfig, DocumentType


VERA_HISTORY_CHUNK_SIZE = 1000
VERA_HISTORY_CHUNK_OVERLAP = 200
REGULATION_CHUNK_SIZE = 1500
REGULATION_CHUNK_OVERLAP = 300
DOCUMENT_LANGUAGE = "es"

DOCUMENT_SOURCES: list[DocumentConfig] = [
    DocumentConfig(
        key="vera_history",
        url="https://pub-739843c5b2e64a7881e1fa442a3d9075.r2.dev/veramoney-history.pdf",
        document_type=DocumentType.VERA_HISTORY,
        title="Historia de VeraMoney",
        language=DOCUMENT_LANGUAGE,
        chunk_size=VERA_HISTORY_CHUNK_SIZE,
        chunk_overlap=VERA_HISTORY_CHUNK_OVERLAP,
    ),
    DocumentConfig(
        key="fintec_regulation",
        url="https://pub-739843c5b2e64a7881e1fa442a3d9075.r2.dev/Regulacio%CC%81n%20fintec.pdf",
        document_type=DocumentType.FINTEC_REGULATION,
        title="Regulacion Fintech Uruguay",
        language=DOCUMENT_LANGUAGE,
        chunk_size=REGULATION_CHUNK_SIZE,
        chunk_overlap=REGULATION_CHUNK_OVERLAP,
    ),
    DocumentConfig(
        key="bank_regulation",
        url="https://pub-739843c5b2e64a7881e1fa442a3d9075.r2.dev/Regulacio%CC%81n%20Bancaria%20Uruguaya_%20Investigacio%CC%81n%20Profunda.pdf",
        document_type=DocumentType.BANK_REGULATION,
        title="Regulacion Bancaria Uruguaya",
        language=DOCUMENT_LANGUAGE,
        chunk_size=REGULATION_CHUNK_SIZE,
        chunk_overlap=REGULATION_CHUNK_OVERLAP,
    ),
]


def build_chunk_metadata(
    document_config: DocumentConfig,
    page_number: int,
    chunk_index: int,
) -> ChunkMetadata:
    return ChunkMetadata(
        document_type=document_config.document_type.value,
        source_url=document_config.url,
        document_title=document_config.title,
        language=document_config.language,
        page_number=page_number,
        chunk_index=chunk_index,
    )

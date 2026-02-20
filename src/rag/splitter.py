import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag.document_configs import build_chunk_metadata
from src.rag.schemas import DocumentConfig


logger = logging.getLogger(__name__)

TEXT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def split_documents(
    documents: list[Document],
    document_config: DocumentConfig,
) -> list[Document]:
    if not documents:
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=document_config.chunk_size,
        chunk_overlap=document_config.chunk_overlap,
        separators=TEXT_SEPARATORS,
    )

    split_texts = text_splitter.split_documents(documents)

    chunks_with_metadata = []

    for chunk_index, split_text in enumerate(split_texts):
        original_metadata = split_text.metadata
        page_number = original_metadata.get("page", 0)

        chunk_metadata = build_chunk_metadata(
            document_config=document_config,
            page_number=page_number,
            chunk_index=chunk_index,
        )

        chunk_document = Document(
            page_content=split_text.page_content,
            metadata=chunk_metadata.model_dump(),
        )
        chunks_with_metadata.append(chunk_document)

    logger.info(
        "splitter_complete document=%s pages=%d chunks=%d",
        document_config.key,
        len(documents),
        len(chunks_with_metadata),
    )

    return chunks_with_metadata

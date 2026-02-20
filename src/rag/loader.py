import logging
import tempfile
from pathlib import Path

import httpx
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_core.documents import Document
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential,
)

from src.rag.document_configs import build_chunk_metadata
from src.rag.schemas import DocumentConfig


logger = logging.getLogger(__name__)

MAX_DOWNLOAD_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1.0
DOWNLOAD_TIMEOUT_SECONDS = 60.0


class DocumentDownloadError(Exception):
    pass


async def download_pdf_to_temp_file(url: str) -> Path:
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(MAX_DOWNLOAD_RETRIES),
        wait=wait_exponential(multiplier=INITIAL_RETRY_DELAY_SECONDS),
        reraise=True,
    ):
        with attempt:
            async with httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT_SECONDS) as http_client:
                response = await http_client.get(url)
                response.raise_for_status()

                temp_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
                    suffix=".pdf",
                    delete=False,
                )
                temp_file.write(response.content)
                temp_file.close()
                return Path(temp_file.name)


def load_pdf_with_plumber(file_path: Path) -> list[Document]:
    loader = PDFPlumberLoader(str(file_path))
    return loader.load()


def enrich_document_metadata(
    documents: list[Document],
    document_config: DocumentConfig,
) -> list[Document]:
    enriched_documents = []

    for document in documents:
        page_number = document.metadata.get("page", 0)

        chunk_metadata = build_chunk_metadata(
            document_config=document_config,
            page_number=page_number,
            chunk_index=0,
        )

        enriched_document = Document(
            page_content=document.page_content,
            metadata=chunk_metadata.model_dump(),
        )
        enriched_documents.append(enriched_document)

    return enriched_documents


async def download_and_load_document(
    document_config: DocumentConfig,
) -> list[Document]:
    logger.info(
        "loader_downloading document=%s url=%s",
        document_config.key,
        document_config.url,
    )

    try:
        temp_file_path = await download_pdf_to_temp_file(document_config.url)

        documents = load_pdf_with_plumber(temp_file_path)

        temp_file_path.unlink()

        enriched_documents = enrich_document_metadata(
            documents=documents,
            document_config=document_config,
        )

        logger.info(
            "loader_loaded document=%s pages=%d",
            document_config.key,
            len(enriched_documents),
        )

        return enriched_documents

    except httpx.HTTPStatusError as error:
        logger.exception(
            "loader_download_failed document=%s status=%d",
            document_config.key,
            error.response.status_code,
        )
        raise DocumentDownloadError(
            f"Failed to download {document_config.key}: HTTP {error.response.status_code}"
        ) from error
    except httpx.TimeoutException as error:
        logger.exception(
            "loader_download_timeout document=%s",
            document_config.key,
        )
        raise DocumentDownloadError(
            f"Timeout downloading {document_config.key}"
        ) from error
    except Exception as error:
        logger.exception(
            "loader_load_failed document=%s error=%s",
            document_config.key,
            str(error),
        )
        raise DocumentDownloadError(
            f"Failed to load {document_config.key}: {error}"
        ) from error

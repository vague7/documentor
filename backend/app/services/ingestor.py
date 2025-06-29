# Add this to any Python file and run it
from typing import Dict, Any
import logging

from app.config import logger
from app.services.doc_parser import parse_pdf, parse_url
from app.utils.text_utils import clean_text, chunk_text
from app.vector.chroma_client import store_embeddings
from langchain_community.vectorstores import Chroma




def ingest_pdf(file: bytes) -> Dict[str, Any]:
    """
    Parses, cleans, chunks, embeds, and stores a PDF document.
    Args:
        file (bytes): The PDF file content.
    Returns:
        Dict[str, Any]: Summary of ingestion (counts, status).
    """
    try:
        raw_text = parse_pdf(file)
        cleaned = clean_text(raw_text)
        chunks = chunk_text(cleaned)
        metadatas = [{"source": "pdf", "chunk_id": i} for i in range(len(chunks))]
        store_embeddings(chunks, metadatas)
        logger.info(f"PDF ingestion complete. {len(chunks)} chunks stored.")
        return {"status": "success", "chunks": len(chunks), "source": "pdf"}
    except Exception as e:
        logger.error(f"PDF ingestion failed: {e}")
        return {"status": "error", "error": str(e), "source": "pdf"}


def ingest_url(url: str) -> Dict[str, Any]:
    """
    Parses, cleans, chunks, embeds, and stores a document from a URL.
    Args:
        url (str): The URL to ingest.
    Returns:
        Dict[str, Any]: Summary of ingestion (counts, status).
    """
    try:
        raw_text = parse_url(url)
        cleaned = clean_text(raw_text)
        chunks = chunk_text(cleaned)
        metadatas = [{"source": "url", "url": url, "chunk_id": i} for i in range(len(chunks))]
        store_embeddings(chunks, metadatas)
        logger.info(f"URL ingestion complete. {len(chunks)} chunks stored.")
        return {"status": "success", "chunks": len(chunks), "source": "url"}
    except Exception as e:
        logger.error(f"URL ingestion failed: {e}")
        return {"status": "error", "error": str(e), "source": "url"} 
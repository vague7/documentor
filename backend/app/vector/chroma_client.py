"""Vector store utilities built on top of LangChain's `Chroma` wrapper.

This replaces the bespoke Chroma Cloud client logic with the official
LangChain integration. The public API surface (`store_embeddings`,
`query_similar_docs`) remains unchanged so that downstream services do
not need to be refactored.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Dict, Union, Any

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import chromadb  # type: ignore  # noqa: F401

from app.services.embedding_service import get_embedder
from app.config import logger


# ---------------------------------------------------------------------------
# Singleton helpers
# ---------------------------------------------------------------------------


@lru_cache()
def _get_chroma_client() -> Any:  # pragma: no cover
    """Instantiate a Chroma Cloud client from env variables."""
    api_key = os.getenv("CHROMA_API_KEY")
    tenant = os.getenv("CHROMA_TENANT")
    database = os.getenv("CHROMA_DATABASE")
    if not api_key or not tenant or not database:
        logger.error("Missing Chroma Cloud environment variables.")
        raise ValueError("Missing Chroma Cloud environment variables.")
    return chromadb.CloudClient(api_key=api_key, tenant=tenant, database=database)


@lru_cache()
def get_vectorstore() -> Chroma:
    """Return a singleton LangChain `Chroma` vector store instance."""
    client = _get_chroma_client()
    embedder = get_embedder()
    vs = Chroma(
        client=client,
        collection_name="documentor",
        embedding_function=embedder,
    )
    logger.info("LangChain Chroma vector store initialised.")
    return vs


# ---------------------------------------------------------------------------
# Public API (compatible with previous implementation)
# ---------------------------------------------------------------------------


def store_embeddings(
    chunks: List[str],
    metadatas: List[Dict[str, Union[str, int, float, bool, None]]],
) -> None:
    """Add text chunks to the Chroma vector store."""

    docs = [Document(page_content=text, metadata=meta) for text, meta in zip(chunks, metadatas)]
    try:
        get_vectorstore().add_documents(docs)
        logger.info("Stored %d chunks in Chroma.", len(chunks))
    except Exception as e:
        logger.error("Failed to store embeddings: %s", e)
        raise


def query_similar_docs(query: str, k: int = 5) -> List[str]:
    """Return the `k` most similar document chunks for the given query."""

    retriever = get_vectorstore().as_retriever(search_kwargs={"k": k})
    try:
        docs = retriever.invoke(query)
        logger.info("Found %d similar chunks for query.", len(docs))
        return [doc.page_content for doc in docs]
    except Exception as e:
        logger.error("Failed to query similar docs: %s", e)
        raise 
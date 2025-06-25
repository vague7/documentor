from typing import List, Dict, Any, Optional, Union, Sequence, Mapping, cast
import logging
import os
from dotenv import load_dotenv
import numpy as np
import uuid
from app.config import logger
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from app.services.embedding_service import embed_texts

load_dotenv()

_client: Optional[ClientAPI] = None
_collection: Optional[Collection] = None


def get_chroma_client() -> ClientAPI:
    """
    Initializes and returns a ChromaDB Cloud client using environment variables.
    """
    global _client
    if _client is None:
        api_key = os.getenv("CHROMA_API_KEY")
        tenant = os.getenv("CHROMA_TENANT")
        database = os.getenv("CHROMA_DATABASE")
        if not api_key or not tenant or not database:
            logger.error("Missing Chroma Cloud environment variables.")
            raise ValueError("Missing Chroma Cloud environment variables.")
        _client = chromadb.CloudClient(
            api_key=api_key,
            tenant=tenant,
            database=database
        )
        logger.info("Chroma Cloud client initialized.")
    return _client


def get_chroma_collection(client: Optional[ClientAPI] = None) -> Collection:
    """
    Initializes and returns the ChromaDB collection.
    """
    global _collection
    if _collection is None:
        if client is None:
            client = get_chroma_client()
        _collection = client.get_or_create_collection(name="documentor")
        logger.info("Chroma Cloud collection initialized.")
    return _collection


def store_embeddings(chunks: List[str], metadatas: List[Dict[str, Union[str, int, float, bool, None]]]) -> None:
    """
    Stores text chunks and their metadata in Chroma Cloud collection.
    Args:
        chunks (List[str]): List of text chunks.
        metadatas (List[dict]): List of metadata dicts for each chunk.
    """
    try:
        collection = get_chroma_collection()
        ids = [f"chunk_{uuid.uuid4()}" for _ in range(len(chunks))]

        vectors = [np.asarray(vec, dtype=np.float32) for vec in embed_texts(chunks)]
        metadatas_cast = cast(List[Mapping[str, Optional[Union[str, int, float, bool]]]], metadatas)
        collection.add(
            ids=ids,
            embeddings=cast(List[Any], vectors),  # type: ignore[arg-type]
            metadatas=metadatas_cast,
            documents=chunks,
        )
        logger.info("Stored %d chunks in Chroma Cloud.", len(chunks))
    except Exception as e:
        logger.error(f"Failed to store embeddings: {e}")
        raise


def query_similar_docs(query: str, k: int = 5) -> List[str]:
    """
    Queries Chroma Cloud for the most similar document chunks to the query.
    Args:
        query (str): The user query.
        k (int): Number of top results to return.
    Returns:
        List[str]: List of relevant text chunks.
    """
    try:
        collection = get_chroma_collection()
        query_vec = np.asarray(embed_texts([query])[0], dtype=np.float32)
        results = collection.query(query_embeddings=[query_vec], n_results=k)
        documents = results.get("documents")
        if not documents or not isinstance(documents, list) or not documents[0]:
            logger.info("No similar chunks found for query.")
            return []
        logger.info("Found %d similar chunks for query.", len(documents[0]))
        return documents[0]
    except Exception as e:
        logger.error(f"Failed to query similar docs: {e}")
        raise 
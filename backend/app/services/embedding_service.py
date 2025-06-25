"""Service layer for text embeddings via Google Generative AI (Gemini)."""
from functools import lru_cache
from typing import List, Any, cast

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import SecretStr

from app.config import get_settings


@lru_cache()
def get_embedder() -> GoogleGenerativeAIEmbeddings:
    """Return a singleton instance of the Gemini embedding model."""
    settings = get_settings()
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=SecretStr(settings.gemini_api_key),
    )


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts into vectors using Gemini embeddings."""
    embedder = get_embedder()
    return embedder.embed_documents(texts) 
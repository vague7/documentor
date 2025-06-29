import logging
import tempfile
from typing import List

# LangChain loaders
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader

# Fallback deps for local parsing (kept for backwards compatibility)
import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document

try:
    from app.config import logger
except ImportError:
    logger = logging.getLogger(__name__)


def _join_documents(docs: List[Document]) -> str:
    """Helper to concatenate page contents from a list of LangChain Documents."""
    return "\n".join(doc.page_content for doc in docs)


def parse_pdf(file: bytes) -> str:
    """Extract text from a PDF (bytes) using LangChain's `PyPDFLoader`.

    We persist the bytes to a temporary file so that the loader can operate
    on a path. If the loader fails for any reason, we fall back to the
    previous PyMuPDF extraction to avoid breaking ingestion.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
            tmp.write(file)
            tmp.flush()
            loader = PyPDFLoader(tmp.name)
            docs = loader.load()
            text = _join_documents(docs)
            logger.info("PDF parsed via PyPDFLoader. Pages: %d", len(docs))
            return text
    except Exception as e:
        logger.warning("PyPDFLoader failed (%s). Falling back to PyMuPDF extraction.", e)
        try:
            doc = fitz.open(stream=file, filetype="pdf")
            text = "\n".join(page.get_text("text") for page in doc)
            logger.info("PDF parsed via PyMuPDF fallback. Pages: %d", doc.page_count)
            return text
        except Exception as inner:
            logger.error("Failed to parse PDF: %s", inner)
            raise


def parse_url(url: str) -> str:
    """Fetch and return cleaned text from a public URL via LangChain `WebBaseLoader`.

    Falls back to a simple requests+BeautifulSoup scraper if the loader
    raises.
    """
    try:
        loader = WebBaseLoader(web_paths=(url,))
        docs = loader.load()
        text = _join_documents(docs)
        logger.info("URL parsed via WebBaseLoader: %s", url)
        return text
    except Exception as e:
        logger.warning("WebBaseLoader failed (%s). Falling back to requests scraping.", e)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            logger.info("URL parsed via fallback: %s", url)
            return text
        except Exception as inner:
            logger.error("Failed to parse URL %s: %s", url, inner)
            raise 
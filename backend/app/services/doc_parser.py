import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging

try:
    from app.config import logger
except ImportError:
    logger = logging.getLogger(__name__)


def parse_pdf(file: bytes) -> str:
    """
    Extracts and returns text from a PDF file (as bytes) using PyMuPDF.
    Args:
        file (bytes): The PDF file content.
    Returns:
        str: Extracted text from the PDF.
    """
    try:
        doc = fitz.open(stream=file, filetype="pdf")
        text = "\n".join(page.get_text("text") for page in doc)
        logger.info("PDF parsed successfully. Number of pages: %d", doc.page_count)
        return text
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        raise


def parse_url(url: str) -> str:
    """
    Fetches and returns cleaned text from a public HTML URL using requests and BeautifulSoup.
    Args:
        url (str): The URL to fetch.
    Returns:
        str: Extracted and cleaned text from the HTML page.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Remove script and style elements
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        logger.info(f"URL parsed successfully: {url}")
        return text
    except Exception as e:
        logger.error(f"Failed to parse URL {url}: {e}")
        raise 
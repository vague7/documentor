from typing import List
import re
import logging

try:
    from app.config import logger
except ImportError:
    logger = logging.getLogger(__name__)

from langchain_text_splitters import RecursiveCharacterTextSplitter


def clean_text(text: str) -> str:
    """
    Cleans up text by removing excessive whitespace and non-printable characters.
    Args:
        text (str): Raw text to clean.
    Returns:
        str: Cleaned text.
    """
    try:
        # Remove non-printable characters
        cleaned = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
        # Collapse multiple spaces/newlines
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        logger.info("Text cleaned successfully. Length: %d", len(cleaned))
        return cleaned
    except Exception as e:
        logger.error(f"Failed to clean text: {e}")
        raise


def chunk_text(text: str) -> List[str]:
    """
    Splits text into chunks using LangChain's RecursiveCharacterTextSplitter.
    Args:
        text (str): The text to split.
    Returns:
        List[str]: List of text chunks.
    """
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", " "]
        )
        chunks = splitter.split_text(text)
        logger.info("Text split into %d chunks.", len(chunks))
        return chunks
    except Exception as e:
        logger.error(f"Failed to chunk text: {e}")
        raise 
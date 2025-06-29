from pydantic_settings import BaseSettings
from pydantic import SecretStr

from functools import lru_cache
import logging
from dotenv import load_dotenv
import os

# Load environment variables from a .env file if present
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """
    gemini_api_key: str
    chroma_api_key: str
    chroma_tenant: str
    chroma_database: str
    history_backend: str = "mongo"
    mongodb_uri: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """
    Singleton accessor for application settings.
    """
    return Settings()  # type: ignore[arg-type]

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("documentor.backend") 
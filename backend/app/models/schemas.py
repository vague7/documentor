from pydantic import BaseModel, Field
from typing import Optional, List

class IngestRequest(BaseModel):
    """
    Request model for document ingestion (PDF or URL).
    """
    file: Optional[bytes] = Field(None, description="PDF file content as bytes")
    url: Optional[str] = Field(None, description="Public URL to API documentation")

class ChatRequest(BaseModel):
    """
    Request model for chat endpoint.
    """
    user_question: str = Field(..., description="User's natural language question about the API docs")

class ChatResponse(BaseModel):
    """
    Response model for chat endpoint.
    """
    answer: str = Field(..., description="LLM-generated answer to the user's question")
    sources: Optional[List[str]] = Field(None, description="List of source document chunks used for the answer") 
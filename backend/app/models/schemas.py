from pydantic import BaseModel, Field
from typing import Optional, List
from langchain_core.documents import Document

class IngestRequest(BaseModel):
    """
    Request model for document ingestion (PDF or URL).
    """
    file: Optional[bytes] = Field(None, description="PDF file content as bytes")
    url: Optional[str] = Field(None, description="Public URL to API documentation")

class ChatRequest(BaseModel):
    """Request model for chat endpoint, optionally tied to a session."""

    user_question: str = Field(..., description="User's natural language question about the API docs")
    session_id: Optional[str] = Field(None, description="Client-provided session identifier for conversational memory")

class ChatResponse(BaseModel):
    """
    Response model for chat endpoint.
    """
    answer: str = Field(..., description="LLM-generated answer to the user's question")
    sources: Optional[List[str]] = Field(None, description="List of source document chunks used for the answer") 

# ---------------------------------------------------------------------------
# Agent endpoint schemas (reuse structure of chat but separate type for clarity)
# ---------------------------------------------------------------------------

class AgentRequest(ChatRequest):
    """Request model for agent endpoint (developer assistant agent)."""

    # Inherits user_question and session_id fields.

# For responses we can reuse ChatResponse since structure is identical.




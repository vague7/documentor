from fastapi import APIRouter, HTTPException, status
from app.config import logger
from app.models.schemas import ChatRequest, ChatResponse
from app.services.query_engine import answer_query

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint for natural language Q&A over API docs.
    Accepts a ChatRequest and returns a ChatResponse from the LLM agent.
    """
    try:
        response = answer_query(request.user_question)
        return response
    except Exception as e:
        logger.error(f"/chat failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat request.") 
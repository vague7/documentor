from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.config import logger
from app.models.schemas import AgentRequest, ChatResponse
from app.services.agent_engine import run_agent_query, stream_agent_answer

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def agent_endpoint(request: AgentRequest) -> ChatResponse:
    """Developer assistant agent endpoint (non-streaming)."""
    try:
        response = run_agent_query(request.user_question, session_id=request.session_id or "default")
        return response
    except Exception as e:
        logger.error(f"/agent failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process agent request.")


@router.post("/stream", status_code=status.HTTP_200_OK)
def agent_stream_endpoint(request: AgentRequest):
    """Stream agent response chunk-by-chunk via SSE/plain text."""
    try:
        generator = stream_agent_answer(request.user_question, session_id=request.session_id or "default")
        return StreamingResponse(generator, media_type="text/plain")
    except Exception as e:
        logger.error(f"/agent/stream failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream agent response.") 
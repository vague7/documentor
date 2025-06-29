from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import logger
from app.routers.ingest_router import router as ingest_router
from app.routers.chat_router import router as chat_router
from app.routers.agent_router import router as agent_router

openapi_tags = [
    {
        "name": "chat",
        "description": "Conversational RAG endpoint for direct Q&A over documentation.",
    },
    {
        "name": "agent",
        "description": (
            "Developer assistant powered by Gemini. Shares persistent chat history via "
            "MongoDB Atlas when `HISTORY_BACKEND=mongo`. Supports tools such as "
            "**knowledge_search**, code_snippet, endpoint_suggester."
        ),
    },
    {"name": "ingest", "description": "Administration endpoints for adding docs to the vector store."},
    {"name": "health", "description": "Liveness / readiness probe."},
]

app = FastAPI(title="DocuMentor Backend API", version="1.0.0", openapi_tags=openapi_tags)

# CORS middleware (allow all origins for now; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(ingest_router)
app.include_router(chat_router)
app.include_router(agent_router)

@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint.
    """
    logger.info("Health check called.")
    return {"status": "ok"} 
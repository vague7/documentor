from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import logger
from app.routers.ingest_router import router as ingest_router
from app.routers.chat_router import router as chat_router

app = FastAPI(title="DocuMentor Backend API", version="1.0.0")

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

@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint.
    """
    logger.info("Health check called.")
    return {"status": "ok"} 
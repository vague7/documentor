from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import status, Request
from app.config import logger
from app.services.ingestor import ingest_pdf, ingest_url
from app.models.schemas import IngestRequest

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/pdf", status_code=status.HTTP_200_OK)
def ingest_pdf_endpoint(file: UploadFile = File(...)):
    """
    Ingest a PDF file. Accepts a file upload and returns ingestion summary.
    """
    try:
        content = file.file.read()
        result = ingest_pdf(content)
        return result
    except Exception as e:
        logger.error(f"/ingest/pdf failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/url", status_code=status.HTTP_200_OK)
def ingest_url_endpoint(request: IngestRequest):
    """
    Ingest a document from a public URL. Accepts JSON with 'url' and returns ingestion summary.
    """
    if not request.url:
        raise HTTPException(status_code=400, detail="Missing 'url' in request body.")
    try:
        result = ingest_url(request.url)
        return result
    except Exception as e:
        logger.error(f"/ingest/url failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
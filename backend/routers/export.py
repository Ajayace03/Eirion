import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from auth import get_current_user
from models.request import AnalysisRequest
from models.response import AnalysisResponse
from engine.pdf_generator import generate_clinical_pdf

router = APIRouter()

class ExportRequest(BaseModel):
    request_payload: AnalysisRequest
    response_payload: AnalysisResponse

@router.post("/clinician-report")
async def generate_clinician_pdf(request: ExportRequest, user: dict = Depends(get_current_user)):
    """
    Generates a professional 3-page PDF outlining the user's biomarkers, 
    pharmacogenomics, and recommended longevity stack for their physician.
    """
    try:
        pdf_bytes = generate_clinical_pdf(request.request_payload, request.response_payload)
        
        return Response(
            content=pdf_bytes, 
            media_type="application/pdf", 
            headers={"Content-Disposition": "attachment; filename=Eirion_Clinical_Report.pdf"}
        )

    except Exception:
        import logging
        logging.getLogger(__name__).error("PDF generation failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate clinical report.")


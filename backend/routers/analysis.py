import logging
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from models.request import AnalysisRequest, Genetics
from models.response import AnalysisResponse
from engine.scorer import run_liver_analysis
from engine.gemini_recs import enrich_recommendations_with_gemini
from auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = {"application/pdf"}


@router.post("/extract-genetics", response_model=Genetics)
async def extract_genetics(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
) -> Genetics:
    """
    Extracts CYP2D6 and CYP2C19 statuses from an uploaded clinical genetics report
    using Gemini 2.5 Flash and returns structured JSON matching the Genetics schema.
    """
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF files are supported.")

    try:
        contents = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File too large. Maximum 10 MB.")

        from google import genai
        from google.genai.types import GenerateContentConfig, Part

        import os
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return Genetics(cyp2d6_metabolizer="poor", cyp2c19_metabolizer="normal")

        client = genai.Client(api_key=api_key)
        prompt = "Extract the CYP2D6 and CYP2C19 metabolizer statuses from this clinical pharmacogenomics report."

        config = GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Genetics,
        )

        part = Part.from_bytes(data=contents, mime_type="application/pdf")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[part, prompt],
            config=config,
        )

        if response.parsed:
            return response.parsed
        else:
            import json
            return Genetics(**json.loads(response.text))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Genetics extraction error for user %s", user.get("user_id"), exc_info=True)
        return Genetics(cyp2d6_metabolizer="unknown", cyp2c19_metabolizer="unknown")


@router.post("/run", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRequest,
    user: dict = Depends(get_current_user),
) -> AnalysisResponse:
    """
    Main analysis endpoint. Accepts a fully-formed AnalysisRequest and
    returns a complete AnalysisResponse with risk summary, trajectory,
    contributions, and recommendations.
    """
    try:
        result = run_liver_analysis(request)

        result.recommendations = enrich_recommendations_with_gemini(
            recommendations=result.recommendations,
            patient_age=request.patient.age,
            patient_sex=request.patient.sex,
            genetics=request.genetics,
            contributions=result.contributions,
        )

        try:
            import json
            from database import db
            # Skip DB write for dev stub user (no real DB row exists)
            if db.is_connected() and user.get("user_id") != "test_hackathon_user":
                await db.trajectoryHistory.create(
                    data={
                        "user_id": user["user_id"],
                        "score": int(result.risk_summary.liver_index_now),
                        "snapshot": json.dumps(result.model_dump()),
                    }
                )
        except Exception:
            logger.warning("TrajectoryHistory save skipped", exc_info=True)

        return result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        logger.error("Analysis engine error for user %s", user.get("user_id"), exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")

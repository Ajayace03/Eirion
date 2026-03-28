from fastapi import APIRouter, HTTPException, File, UploadFile
from ..models.request import AnalysisRequest, Genetics
from ..models.response import AnalysisResponse
from ..engine.scorer import run_liver_analysis
from ..engine.gemini_recs import enrich_recommendations_with_gemini

router = APIRouter()


@router.post("/extract-genetics", response_model=Genetics)
async def extract_genetics(file: UploadFile = File(...)) -> Genetics:
    \"\"\"
    Extracts CYP2D6 and CYP2C19 statuses from an uploaded clinical genetics report
    using Gemini 2.5 Flash and returns structured JSON matching the Genetics schema.
    \"\"\"
    try:
        contents = await file.read()
        mime_type = file.content_type or "application/pdf"
        
        from google import genai
        from google.genai.types import GenerateContentConfig, Part

        # Failsafe dummy data if no API key is provided
        import os
        if not os.environ.get("GEMINI_API_KEY"):
            return Genetics(cyp2d6_metabolizer="poor", cyp2c19_metabolizer="normal")

        client = genai.Client()
        prompt = "Extract the CYP2D6 and CYP2C19 metabolizer statuses from this clinical pharmacogenomics report."
        
        config = GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Genetics,
        )
        
        part = Part.from_bytes(data=contents, mime_type=mime_type)
        
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
            
    except Exception as e:
        print(f"Extraction error: {e}")
        # Fallback to defaults so the onboarding can continue during local development
        return Genetics(cyp2d6_metabolizer="unknown", cyp2c19_metabolizer="unknown")


@router.post("/run", response_model=AnalysisResponse)
async def run_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """
    Main analysis endpoint. Accepts a fully-formed AnalysisRequest and
    returns a complete AnalysisResponse with risk summary, trajectory,
    contributions, and recommendations.

    Phase 0: Synchronous engine, < 500ms target.
    """
    try:
        result = run_liver_analysis(request)

        # Attempt Gemini enrichment (no-op if GEMINI_API_KEY not set)
        result.recommendations = enrich_recommendations_with_gemini(
            recommendations=result.recommendations,
            patient_age=request.patient.age,
            patient_sex=request.patient.sex,
            genetics=request.genetics,
            contributions=result.contributions,
        )

        # Persist snapshot to TrajectoryHistory (best-effort, non-blocking)
        try:
            import json
            from database import db
            if db.is_connected():
                await db.trajectoryhistory.create(
                    data={
                        "user_id": "anonymous",
                        "score": int(result.risk_summary.liver_index_now),
                        "snapshot": json.dumps(result.model_dump()),
                    }
                )
        except Exception as db_err:
            print(f"[DB] TrajectoryHistory save skipped: {db_err}")

        return result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis engine error: {str(e)}")


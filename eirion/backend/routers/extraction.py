import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from google import genai
from pydantic import BaseModel
import json

router = APIRouter()

# Initialize Gemini Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class ExtractionResponse(BaseModel):
    extracted_data: dict

@router.post("/parse-labs", response_model=ExtractionResponse)
async def parse_lab_pdf(file: UploadFile = File(...)):
    """
    Accepts a raw LabCorp or Quest Diagnostics PDF via multipart/form-data.
    Uses Gemini 2.5 Flash Multimodal to strictly extract metabolic biomarkers
    into a structured JSON shape mirroring the Onboarding Wizard state.
    """
    if not client:
        raise HTTPException(status_code=503, detail="Eirion Extraction AI is currently offline.")
        
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are currently supported for auto-extraction.")

    try:
        # Read the file bytes directly into memory
        file_bytes = await file.read()
        
        # Upload using the new genai SDK exactly as mandated by core docs
        # We use 'application/pdf' mime type
        uploaded_file = client.files.upload(
            file=file_bytes,
            config={"mime_type": "application/pdf"}
        )

        system_prompt = """
        You are a clinical data extraction AI. The user has provided an uploaded medical 
        laboratory PDF document (e.g. from Quest or LabCorp).
        Your ONLY job is to extract the following exact numeric values, if present:
        - "ast" (Aspartate Aminotransferase, integer)
        - "alt" (Alanine Aminotransferase, integer)
        - "glucose" (Fasting Glucose mg/dL, integer)
        - "hba1c" (Hemoglobin A1C percentage, float)
        - "cholesterol_ldl" (LDL-C mg/dL, integer)
        
        If a value is not found in the PDF, output `null` for that key.
        Return ONLY valid JSON. Absolutely no markdown backticks, no markdown blocks, no explanation text whatsoever.
        Just raw JSON.
        
        Expected output shape:
        {
           "ast": 25,
           "alt": 21,
           "glucose": 88,
           "hba1c": 5.1,
           "cholesterol_ldl": 110
        }
        """

        # Generate content natively analyzing the uploaded document
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, system_prompt],
             config=genai.types.GenerateContentConfig(
                temperature=0.0, # zero temperature for strict extraction
                # We could set response_mime_type="application/json" but prompt control is usually fine
                response_mime_type="application/json"
            )
        )
        
        # Clean up the file from Google's temporary infrastructure
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception as e:
            print(f"Warning: Failed to delete Gemini temp file: {e}")

        # The JSON should be directly parseable because of response_mime_type
        extracted_dict = json.loads(response.text)
        return ExtractionResponse(extracted_data=extracted_dict)

    except json.JSONDecodeError:
        print(f"[Extraction] Flawed JSON output: {response.text}")
        raise HTTPException(status_code=500, detail="AI failed to structure the PDF correctly.")
    except Exception as e:
        print(f"[Extraction] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

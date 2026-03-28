import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from google import genai
from auth import get_current_user

router = APIRouter()

# Initialize Gemini Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class ChatRequest(BaseModel):
    message: str
    context_payload: dict  # The AnalysisResponse containing all health data

@router.post("/ask")
async def ask_eirion(request: ChatRequest, user: dict = Depends(get_current_user)):
    """
    Handles a user's question by feeding their entire metabolic and genetic 
    context into Gemini 2.5 Flash for a highly personalized answer.
    """
    if not client:
        return {"reply": "Eirion AI is in offline fallback mode. Please configure your API key."}

    system_instruction = f"""
    You are Eirion, an elite clinical longevity AI. 
    You are speaking directly to the user about their specific health data.
    Be concise, highly scientific, yet empathetic. Use markdown formatting.
    
    Here is the user's current complete health profile, biomarkers, and regimen:
    {str(request.context_payload)}
    
    CRITICAL RULES:
    1. Answer their question strictly based on their data. 
    2. If evaluating an interaction, reference their CYP liver enzymes or AST/ALT labs.
    3. If they ask about something unrelated to health or longevity, politely refuse to answer.
    4. Keep answers to 1-2 paragraphs max.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=request.message,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3, # Low temperature for more clinical/deterministic answers
            )
        )
        return {"reply": response.text}
    except Exception as e:
        print(f"[Chat] Gemini error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

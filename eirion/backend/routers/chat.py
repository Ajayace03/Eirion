import logging
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from google import genai
from auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_client = None

def _get_client():
    global _client
    if _client is None and GEMINI_API_KEY and not GEMINI_API_KEY.startswith("YOUR_"):
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

MAX_CONTEXT_CHARS = 8_000  # prevent prompt-token abuse


class ChatRequest(BaseModel):
    message: str
    context_payload: dict

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message must not be empty")
        if len(v) > 2000:
            raise ValueError("message too long (max 2000 chars)")
        return v


@router.post("/ask")
async def ask_eirion(request: ChatRequest, user: dict = Depends(get_current_user)):
    """
    Handles a user's question by feeding their metabolic and genetic
    context into Gemini 2.5 Flash for a personalised answer.
    """
    client = _get_client()
    if not client:
        return {"reply": "Eirion AI is in offline fallback mode. Please configure your API key."}

    import json
    try:
        context_str = json.dumps(request.context_payload, default=str)
    except Exception:
        context_str = "{}"
    # Truncate to prevent runaway token costs
    context_str = context_str[:MAX_CONTEXT_CHARS]

    system_instruction = (
        "You are Eirion, an elite clinical longevity AI. "
        "You are speaking directly to the user about their specific health data. "
        "Be concise, highly scientific, yet empathetic. Use markdown formatting.\n\n"
        f"Here is the user's current health profile:\n{context_str}\n\n"
        "CRITICAL RULES:\n"
        "1. Answer their question strictly based on their data.\n"
        "2. If evaluating an interaction, reference their CYP liver enzymes or AST/ALT labs.\n"
        "3. If they ask about something unrelated to health or longevity, politely refuse.\n"
        "4. Keep answers to 1-2 paragraphs max."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=request.message,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
            ),
        )
        return {"reply": response.text}
    except Exception:
        logger.error("Gemini chat error for user %s", user.get("user_id"), exc_info=True)
        raise HTTPException(status_code=500, detail="AI assistant is temporarily unavailable.")

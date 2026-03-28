"""
EIRION Gemini API Integration — Phase 0
Generates personalized recommendation text via the Gemini API.
Falls back to static template text if GEMINI_API_KEY is not set.
"""

import os
from typing import Optional


def generate_rec_text(
    patient_age: int,
    patient_sex: str,
    top_contributor_name: str,
    top_load: float,
    rec_title: str,
    rec_action_type: str,
    genetics_summary: str,
) -> Optional[str]:
    """
    Calls Gemini to generate a personalized 2-sentence recommendation explanation.
    Returns None if GEMINI_API_KEY is not set (falls back to static text).
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        prompt = (
            f"You are a precision medicine AI writing a personalized health recommendation. "
            f"Be specific, evidence-grounded, and clear. Do NOT include any medical disclaimer — "
            f"this is already shown separately in the app.\n\n"
            f"User profile:\n"
            f"- Age: {patient_age}, Sex: {patient_sex}\n"
            f"- Genetics: {genetics_summary}\n"
            f"- Top liver stressor in their stack: {top_contributor_name} (load score: {top_load:.1f})\n\n"
            f"Recommendation being made: '{rec_title}' (action type: {rec_action_type})\n\n"
            f"Write exactly 2 sentences explaining why this recommendation is specifically "
            f"important for this user given their genetics and supplement/medication stack. "
            f"Use plain language, cite the specific mechanism (e.g. CYP450 pathway), "
            f"and quantify the benefit where possible."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        if response and response.text:
            return response.text.strip()
        return None

    except Exception:
        # Any failure (network, rate limit, etc.) → fall back gracefully
        return None


def enrich_recommendations_with_gemini(
    recommendations: list,
    patient_age: int,
    patient_sex: str,
    genetics,
    contributions: list,
) -> list:
    """
    Attempts to enrich each recommendation's `details` field with Gemini-generated text.
    If Gemini is unavailable, the static details text is kept unchanged.
    """
    # Find top load contributor for context
    harmful = sorted(
        [c for c in contributions if not c.is_protective and c.load > 0],
        key=lambda c: c.load,
        reverse=True,
    )
    top_contributor_name = harmful[0].name if harmful else "unknown"
    top_load = harmful[0].load if harmful else 0.0

    genetics_summary = (
        f"CYP2D6 {genetics.cyp2d6_metabolizer} metabolizer"
        + (
            f", CYP2C19 {genetics.cyp2c19_metabolizer} metabolizer"
            if getattr(genetics, "cyp2c19_metabolizer", "unknown") != "unknown"
            else ""
        )
    )

    for rec in recommendations:
        ai_text = generate_rec_text(
            patient_age=patient_age,
            patient_sex=patient_sex,
            top_contributor_name=top_contributor_name,
            top_load=top_load,
            rec_title=rec.title,
            rec_action_type=rec.action_type,
            genetics_summary=genetics_summary,
        )
        if ai_text:
            rec.details = ai_text

    return recommendations

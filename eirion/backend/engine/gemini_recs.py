"""
EIRION Gemini Recommendation Engine — Enhanced Prompt
=====================================================
Uses a rich multi-section prompt that gives Gemini full clinical context:
  - Patient demographics + lifestyle risk factors
  - All organ scores + key lab values
  - Full regimen with DDI flags
  - Pharmacogenomics (CYP450 panel)
  - Risk projection headline
  - Per-recommendation personalised rationale
"""

import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


# ── Prompt builder ─────────────────────────────────────────────────────────────

def _build_system_prompt() -> str:
    return (
        "You are Eirion's Clinical Intelligence Engine — an expert precision medicine AI "
        "trained in clinical pharmacology, hepatology, nephrology, and longevity science. "
        "You write evidence-based, mechanistically specific recommendations personalized to "
        "the patient's exact genetic profile, organ health scores, and supplement stack. "
        "Tone: confident, clinical, specific. Never hedge with 'consult a doctor' — "
        "that disclaimer is shown separately in the app. Never give generic advice. "
        "Always cite the specific enzyme, pathway, or biomarker driving the recommendation."
    )


def _build_patient_context(
    request,
    response,
    organ_scores: dict,
) -> str:
    p  = request.patient
    ls = request.lifestyle
    g  = request.genetics
    risk = response.risk_summary

    # Labs summary
    labs = request.labs
    labs_lines = []
    if labs:
        for field, label in [
            ("alt_u_per_l",              "ALT"),
            ("ast_u_per_l",              "AST"),
            ("ggt_u_per_l",              "GGT"),
            ("alp_u_per_l",              "ALP"),
            ("albumin_g_per_dl",         "Albumin"),
            ("egfr_ml_per_min",          "eGFR"),
            ("creatinine_mg_per_dl",     "Creatinine"),
            ("hba1c_pct",                "HbA1c"),
            ("ldl_mg_per_dl",            "LDL"),
            ("hdl_mg_per_dl",            "HDL"),
            ("hscrp_mg_per_l",           "hsCRP"),
            ("triglycerides_mg_per_dl",  "Triglycerides"),
        ]:
            val = getattr(labs, field, None)
            if val is not None:
                labs_lines.append(f"    {label}: {val}")
    labs_text = "\n".join(labs_lines) if labs_lines else "    (No labs provided)"

    # Regimen
    regimen_lines = []
    for item in request.regimen:
        ddi_note = ""
        if hasattr(response, "ddi_flags"):
            for ddi in response.ddi_flags:
                if item.compound_id in (getattr(ddi, "compound_a", "") + getattr(ddi, "compound_b", "")):
                    ddi_note = f" ⚠️ DDI: {getattr(ddi, 'mechanism', '')}"
                    break
        regimen_lines.append(
            f"    • {item.compound_id.replace('_',' ').title()} "
            f"{item.dose_mg}mg × {item.frequency_per_day}/day"
            f"{ddi_note}"
        )
    regimen_text = "\n".join(regimen_lines) if regimen_lines else "    (No compounds)"

    # Conditions
    conditions_text = ", ".join(
        c.condition_id.replace("_", " ").title()
        for c in (request.conditions or [])
    ) or "None reported"

    # Organ scores
    organ_text = "\n".join(
        f"    {organ.title()}: {score:.0f}/100"
        for organ, score in organ_scores.items()
    )

    # Lifestyle risk summary
    sleep_risk = "⚠️ CRITICAL" if getattr(ls, "sleep_hours_avg", 7) < 5 else (
        "⚠️ Low" if getattr(ls, "sleep_hours_avg", 7) < 6.5 else "OK"
    )
    stress_risk = "⚠️ HIGH" if getattr(ls, "stress_level", 5) >= 7 else "Moderate" if getattr(ls, "stress_level", 5) >= 5 else "Low"
    alcohol_risk = "⚠️ High" if getattr(ls, "alcohol_drinks_per_week", 0) > 14 else "Elevated" if getattr(ls, "alcohol_drinks_per_week", 0) > 7 else "Low"

    return f"""
PATIENT PROFILE
───────────────
Demographics:
    Age: {p.age} | Sex: {p.sex.title()} | Weight: {p.weight_kg}kg | Height: {getattr(p, 'height_cm', '?')}cm
    BMI: {p.weight_kg / ((getattr(p, 'height_cm', 170)/100)**2):.1f}

Pharmacogenomics (CYP450 Panel):
    CYP2D6:  {g.cyp2d6_metabolizer.replace('_', ' ')} metabolizer (metabolizes: codeine, tamoxifen, antidepressants)
    CYP2C19: {g.cyp2c19_metabolizer.replace('_', ' ')} metabolizer (metabolizes: omeprazole, clopidogrel, SSRIs)
    CYP3A4:  {getattr(g, 'cyp3a4_metabolizer', 'unknown').replace('_', ' ')} metabolizer (metabolizes: statins, benzodiazepines, ~50% of all drugs)
    CYP2C9:  {getattr(g, 'cyp2c9_metabolizer', 'unknown').replace('_', ' ')} metabolizer (metabolizes: warfarin, NSAIDs, sulfonylureas)
    MTHFR C677T: {getattr(g, 'mthfr_c677t', 'unknown')} (folate methylation / homocysteine)
    SLCO1B1: {getattr(g, 'slco1b1_function', 'unknown')} (statin hepatic uptake transporter)

Active Conditions:
    {conditions_text}

Lifestyle Risk Factors:
    Sleep: {getattr(ls, 'sleep_hours_avg', 7):.1f}h/night [{sleep_risk}]
    Stress: {getattr(ls, 'stress_level', 5)}/10 [{stress_risk}]
    Alcohol: {getattr(ls, 'alcohol_drinks_per_week', 0)} drinks/wk [{alcohol_risk}]
    Sugar: {getattr(ls, 'sugar_g_per_day', 50)}g/day | Exercise: {getattr(ls, 'exercise_mins_per_week', 0)} min/wk
    Smoking: {getattr(ls, 'smoking_status', 'never').replace('_', ' ')}
    Diet: {getattr(ls, 'diet_type', 'omnivore').replace('_', ' ').title()}

Current Lab Values:
{labs_text}

Organ Health Scores (0-100, higher = healthier):
{organ_text}

Risk Summary:
    Overall Index: {risk.liver_index_now:.0f}/100 | Risk Level: {risk.risk_level.upper()}
    Polypharmacy Score: {getattr(response, 'polypharmacy_score', 'N/A')}
    Headline: {risk.headline}
    5-Year Projection: -{risk.projected_drop_percent}% decline (baseline, no changes)

Current Supplement/Medication Stack ({len(request.regimen)} compounds):
{regimen_text}
""".strip()


def _build_recommendation_prompt(
    patient_context: str,
    rec_title: str,
    rec_action_type: str,
    rec_details_static: str,
    top_contributor_name: str,
    top_load: float,
) -> str:
    return f"""
{_build_system_prompt()}

{patient_context}

─────────────────────────────────────────────
RECOMMENDATION TO PERSONALIZE:
    Action: [{rec_action_type.upper()}] {rec_title}
    Static base text: "{rec_details_static}"
    Primary driver: {top_contributor_name} (hepatic load: {top_load:.1f}/100)
─────────────────────────────────────────────

Rewrite the recommendation in exactly 2-3 sentences that are:
1. Personalized to THIS patient's specific CYP genotype, organ scores, and lifestyle
2. Mechanistically specific — name the exact enzyme/pathway/biomarker involved
3. Quantified where possible (e.g. "CYP2D6 poor metabolizers accumulate 3-4× plasma levels")
4. Actionable — tell the patient exactly what to do and why it matters for them

Do NOT include generic statements. Every sentence must be specific to this patient's data.
""".strip()


def _build_full_analysis_prompt(patient_context: str, recommendations: list) -> str:
    """Build a single prompt for all recs at once (more efficient, 1 API call)."""
    recs_text = "\n".join(
        f"{i+1}. [{r.action_type.upper()}] {r.title}: {r.details}"
        for i, r in enumerate(recommendations[:5])  # top 5 only
    )
    return f"""
{_build_system_prompt()}

{patient_context}

─────────────────────────────────────────────
RECOMMENDATIONS TO PERSONALIZE (respond as a numbered list matching exactly):
{recs_text}
─────────────────────────────────────────────

For EACH recommendation above, write exactly 2 sentences that are:
• Personalized to this patient's CYP genotype, organ scores, labs, and lifestyle
• Mechanistically specific (name the exact enzyme, pathway, transporter, or biomarker)
• Quantified where evidence supports it
• Actionable with clear rationale

Format your response as:
1. [Your 2-sentence personalized text]
2. [Your 2-sentence personalized text]
...etc (match the numbering exactly)
""".strip()


# ── Main entry points ──────────────────────────────────────────────────────────

def enrich_recommendations_with_gemini(
    recommendations: list,
    patient_age: int,
    patient_sex: str,
    genetics,
    contributions: list,
    request=None,
    response=None,
) -> list:
    """
    Enriches each recommendation's `details` field with a Gemini-personalized explanation.
    Uses a single batch API call for efficiency.
    Falls back to static text if GEMINI_API_KEY is unset or Gemini fails.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key.startswith("YOUR_"):
        logger.info("[Gemini] No API key — using static recommendation text.")
        return recommendations

    if not recommendations:
        return recommendations

    # Build rich organ scores dict if response available
    organ_scores = {}
    if response and hasattr(response, "organ_scores"):
        for os_item in response.organ_scores:
            organ_scores[os_item.organ] = os_item.score
    if not organ_scores:
        organ_scores = {"liver": 70, "kidney": 75, "cardiovascular": 72, "metabolic": 70}

    # Top contributor for context
    harmful = sorted(
        [c for c in contributions if not c.is_protective and c.load > 0],
        key=lambda c: c.load, reverse=True,
    )
    top_contributor_name = harmful[0].name if harmful else "polypharmacy load"
    top_load             = harmful[0].load if harmful else 0.0

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        # Build full context
        if request and response:
            patient_context = _build_patient_context(request, response, organ_scores)
        else:
            # Minimal fallback context
            patient_context = (
                f"Patient: {patient_age}y {patient_sex} | "
                f"CYP2D6: {genetics.cyp2d6_metabolizer} | "
                f"CYP2C19: {getattr(genetics, 'cyp2c19_metabolizer', 'unknown')}"
            )

        prompt = _build_full_analysis_prompt(patient_context, recommendations)

        response_obj = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        if not response_obj or not response_obj.text:
            return recommendations

        # Parse numbered response back into recommendations
        lines = response_obj.text.strip().split("\n")
        parsed: dict[int, list[str]] = {}
        current_idx = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Match "1. " "2. " etc at line start
            for i in range(1, len(recommendations) + 1):
                if line.startswith(f"{i}.") or line.startswith(f"{i})"):
                    current_idx = i - 1
                    text = line[len(str(i))+1:].strip().lstrip(".").strip()
                    parsed.setdefault(current_idx, []).append(text)
                    break
            else:
                if current_idx is not None and line and not line.startswith("#"):
                    parsed.setdefault(current_idx, []).append(line)

        # Apply parsed text back to recommendations
        enriched = 0
        for idx, rec in enumerate(recommendations[:5]):
            if idx in parsed and parsed[idx]:
                ai_text = " ".join(parsed[idx])
                if len(ai_text) > 30:  # sanity check
                    rec.details = ai_text
                    enriched += 1

        logger.info("[Gemini] Enriched %d/%d recommendations.", enriched, len(recommendations[:5]))

    except Exception as e:
        logger.warning("[Gemini] Enrichment failed: %s — using static text.", e)

    return recommendations


# ── Legacy single-rec entry point (kept for backwards compatibility) ────────────

def generate_rec_text(
    patient_age: int,
    patient_sex: str,
    top_contributor_name: str,
    top_load: float,
    rec_title: str,
    rec_action_type: str,
    genetics_summary: str,
) -> Optional[str]:
    """Single-recommendation Gemini call (legacy — prefer enrich_recommendations_with_gemini)."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key.startswith("YOUR_"):
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = (
            f"{_build_system_prompt()}\n\n"
            f"Patient: {patient_age}y {patient_sex} | Genetics: {genetics_summary}\n"
            f"Top stressor: {top_contributor_name} (load: {top_load:.1f})\n\n"
            f"Recommendation: [{rec_action_type.upper()}] {rec_title}\n\n"
            f"Write exactly 2 personalized, mechanistically specific sentences."
        )
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return resp.text.strip() if resp and resp.text else None
    except Exception:
        return None

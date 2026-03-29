import io
import logging
import os
import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from google import genai
from pydantic import BaseModel
from typing import Optional
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

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

# Load SNP→phenotype lookup
_SNP_MAP = None
def _get_snp_map():
    global _SNP_MAP
    if _SNP_MAP is None:
        map_path = os.path.join(os.path.dirname(__file__), "..", "data", "snp_pgx_map.json")
        with open(map_path) as f:
            _SNP_MAP = json.load(f)
    return _SNP_MAP


class ExtractionResponse(BaseModel):
    extracted_data: dict
    source: str = "ocr"
    confidence: Optional[float] = None


# ─────────────────────────────────────────────────────────────────────────────
# POST /extraction/parse-labs  (image OR pdf)
# Full LFT + KFT + metabolic/cardiac extraction via Gemini Vision
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/parse-labs", response_model=ExtractionResponse)
async def parse_lab_report(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """
    Accepts a lab report as image (JPEG/PNG) or PDF.
    Uses Gemini Vision to extract the full panel: LFT + KFT + Metabolic/Cardiac.
    Returns structured JSON matching the ExtendedLabs model.
    """
    client = _get_client()
    if not client:
        raise HTTPException(status_code=503, detail="Eirion Extraction AI is currently offline.")

    ALLOWED_TYPES = {
        "application/pdf": "application/pdf",
        "image/jpeg": "image/jpeg",
        "image/jpg": "image/jpeg",
        "image/png": "image/png",
        "application/octet-stream": "application/pdf",
    }

    mime = ALLOWED_TYPES.get(file.content_type or "")
    if not mime:
        raise HTTPException(status_code=415, detail="Supported formats: PDF, JPEG, PNG")

    file_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum 10 MB.")

    uploaded_file = None
    try:
        uploaded_file = client.files.upload(
            file=file_bytes,
            config={"mime_type": mime},
        )

        prompt = """You are a clinical data extraction AI. This is a medical lab report image or PDF.
Extract ALL of these values if present. Return ONLY valid JSON — no markdown, no explanations.

Keys to extract (use null if not found):
{
  "ast_u_per_l": null,
  "alt_u_per_l": null,
  "ggt_u_per_l": null,
  "alp_u_per_l": null,
  "albumin_g_per_dl": null,
  "bilirubin_mg_per_dl": null,
  "creatinine_mg_per_dl": null,
  "egfr_ml_per_min": null,
  "bun_mg_per_dl": null,
  "uric_acid_mg_per_dl": null,
  "hba1c_pct": null,
  "glucose_mg_per_dl": null,
  "ldl_mg_per_dl": null,
  "hdl_mg_per_dl": null,
  "triglycerides_mg_per_dl": null,
  "hscrp_mg_per_l": null,
  "lab_report_date": null,
  "lab_name": null
}

Rules:
- AST and SGOT are the same. ALT and SGPT are the same.
- eGFR can appear as CKD-EPI. Use the numeric value only (not the formula name).
- HbA1c: if shown as %, keep as float (e.g. 5.9). If shown as mmol/mol, convert: (mmol/mol / 10.929) + 2.15.
- All values as numbers only (no units in the JSON).
- For dates, use YYYY-MM-DD format."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[uploaded_file, prompt],
            config=genai.types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )

        extracted = json.loads(response.text)
        # Strip null values to keep payload clean
        extracted = {k: v for k, v in extracted.items() if v is not None}
        return ExtractionResponse(extracted_data=extracted, source="ocr", confidence=0.92)

    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI failed to structure the lab report correctly.")
    except Exception:
        logger.error("Lab extraction error for user %s", user.get("user_id"), exc_info=True)
        raise HTTPException(status_code=500, detail="Lab extraction failed. Please try again.")
    finally:
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# POST /extraction/parse-genetic-file  (23andMe raw .txt SNP file)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/parse-genetic-file", response_model=ExtractionResponse)
async def parse_genetic_file(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """
    Accepts a 23andMe raw genetic data .txt file.
    Filters for ~15 pharmacogenomically relevant rSIDs.
    Maps rsID+genotype → star-allele → metabolizer phenotype.
    Returns ExtendedGenetics JSON.
    """
    file_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large.")

    snp_map = _get_snp_map()
    relevant_rsids = set(snp_map["pharmacogenomically_relevant_rsids"])

    # Parse the 23andMe TSV
    found: dict[str, str] = {}  # rsid → genotype
    try:
        text = file_bytes.decode("utf-8", errors="ignore")
        for line in text.splitlines():
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            rsid, _chrom, _pos, genotype = parts[0], parts[1], parts[2], parts[3].strip()
            if rsid in relevant_rsids:
                found[rsid] = genotype
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse genetic file: {e}")

    if not found:
        raise HTTPException(
            status_code=422,
            detail="No pharmacogenomically relevant SNPs found. Is this a valid 23andMe raw data file?"
        )

    # Map rsid+genotype → diplotype → phenotype for each gene
    genes = snp_map["genes"]
    result = {
        "cyp2d6_metabolizer": "unknown",
        "cyp2c19_metabolizer": "unknown",
        "cyp3a4_metabolizer": "unknown",
        "cyp2c9_metabolizer": "unknown",
        "cyp1a2_metabolizer": "unknown",
        "slco1b1_function": "unknown",
        "ugt1a1_function": "unknown",
        "mthfr_c677t": "unknown",
        "mthfr_a1298c": "unknown",
        "diplotypes": {},
        "source": "23andme_upload",
    }

    for gene_name, gene_data in genes.items():
        alleles_map = gene_data.get("alleles", {})
        dip_map = gene_data.get("diplotype_to_phenotype", {})

        for rsid, genotype_map in alleles_map.items():
            if rsid in found:
                geno = found[rsid]
                diplotype = genotype_map.get(geno)
                if diplotype:
                    result["diplotypes"][gene_name] = diplotype
                    phenotype = dip_map.get(diplotype, "unknown")

                    if gene_name == "CYP2D6":
                        result["cyp2d6_metabolizer"] = phenotype
                    elif gene_name == "CYP2C19":
                        result["cyp2c19_metabolizer"] = phenotype
                    elif gene_name == "CYP3A4":
                        result["cyp3a4_metabolizer"] = phenotype
                    elif gene_name == "CYP2C9":
                        result["cyp2c9_metabolizer"] = phenotype
                    elif gene_name == "CYP1A2":
                        result["cyp1a2_metabolizer"] = phenotype
                    elif gene_name == "SLCO1B1":
                        result["slco1b1_function"] = phenotype
                    elif gene_name == "UGT1A1":
                        result["ugt1a1_function"] = phenotype
                    elif gene_name == "MTHFR":
                        if rsid == "rs1801133":
                            result["mthfr_c677t"] = genotype_map.get(geno, "unknown").replace("c677t_", "")
                        elif rsid == "rs1801131":
                            result["mthfr_a1298c"] = genotype_map.get(geno, "unknown").replace("a1298c_", "")

    return ExtractionResponse(
        extracted_data=result,
        source="23andme_upload",
        confidence=0.98,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /extraction/parse-pgx-report  (PGx Clinical PDF — GeneSight / Strand)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/parse-pgx-report", response_model=ExtractionResponse)
async def parse_pgx_report(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """
    Accepts a Pharmacogenomics (PGx) clinical PDF report (GeneSight, Strand Life Sciences, etc.).
    Uses Gemini Vision to extract star-allele diplotypes and metabolizer phenotypes.
    Returns ExtendedGenetics JSON.
    """
    client = _get_client()
    if not client:
        raise HTTPException(status_code=503, detail="Eirion Extraction AI is currently offline.")

    ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png", "application/octet-stream"}
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Supported formats: PDF, JPEG, PNG")

    file_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum 10 MB.")

    mime = "application/pdf" if "pdf" in (file.content_type or "") else "image/jpeg"
    uploaded_file = None
    try:
        uploaded_file = client.files.upload(file=file_bytes, config={"mime_type": mime})

        prompt = """You are a clinical pharmacogenomics data extraction AI. This is a PGx (Pharmacogenomics) lab report.
Extract exactly the following gene metabolizer phenotypes. Return ONLY valid JSON — no markdown, no explanations.

Keys to extract (use "unknown" if not in report):
{
  "cyp2d6_metabolizer": "unknown",
  "cyp2c19_metabolizer": "unknown",
  "cyp3a4_metabolizer": "unknown",
  "cyp2c9_metabolizer": "unknown",
  "cyp1a2_metabolizer": "unknown",
  "slco1b1_function": "unknown",
  "ugt1a1_function": "unknown",
  "mthfr_c677t": "unknown",
  "diplotypes": {}
}

Allowed phenotype values:
- For CYP genes: "poor", "intermediate", "normal", "ultra_rapid", "unknown"
- For SLCO1B1: "normal", "reduced", "poor", "unknown"
- For UGT1A1: "poor", "intermediate", "normal", "unknown"
- For MTHFR: "normal", "heterozygous", "homozygous", "unknown"
- diplotypes: {"CYP2D6": "*4/*4", "CYP2C19": "*1/*2", ...} — raw star-alleles from report

Mapping rules:
- "Poor Metabolizer" → "poor"
- "Intermediate Metabolizer" → "intermediate"
- "Normal/Extensive Metabolizer" → "normal"
- "Ultra-rapid Metabolizer" → "ultra_rapid"
- "Reduced Function" (SLCO1B1) → "reduced"
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[uploaded_file, prompt],
            config=genai.types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )

        extracted = json.loads(response.text)
        extracted["source"] = "pgx_report"
        return ExtractionResponse(extracted_data=extracted, source="pgx_report", confidence=0.95)

    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI failed to parse the PGx report.")
    except Exception:
        logger.error("PGx extraction error for user %s", user.get("user_id"), exc_info=True)
        raise HTTPException(status_code=500, detail="PGx report extraction failed.")
    finally:
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass

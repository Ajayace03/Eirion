"""
Wearable + EHR (FHIR R4) Integration Bridge
---------------------------------------------
Real SMART-on-FHIR OAuth2 flow + FHIR Observation → ExtendedLabs mapper.
Oura Ring v2 REST client with token management.

Architecture:
    - SMART-on-FHIR: OAuth2 Authorization Code flow
    - FHIR Resources: Observation (labs), MedicationRequest, Condition
    - Wearable APIs: Oura v2, Garmin (stub), Apple HealthKit (stub)

Usage:
    # FHIR integration
    from engine.planned.wearable_fhir_integration import FHIRClient, fhir_obs_to_labs
    client = FHIRClient(base_url="https://fhir.epic.com/api/FHIR/R4", token="Bearer ...")
    obs    = client.fetch_observations(patient_id="Patient/123")
    labs   = fhir_obs_to_labs(obs)

    # Oura integration
    from engine.planned.wearable_fhir_integration import OuraClient
    oura = OuraClient(access_token="...")
    data = await oura.get_daily_readiness()
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Optional async HTTP support ───────────────────────────────────────────────
try:
    import httpx
    _HTTPX = True
except ImportError:
    _HTTPX = False
    logger.warning("[FHIR] httpx not available. Install: pip install httpx")


# ──────────────────────────────────────────────────────────────────────────────
# FHIR LOINC → ExtendedLabs field mapping
# ──────────────────────────────────────────────────────────────────────────────

LOINC_TO_LAB_FIELD: Dict[str, str] = {
    # Liver function tests
    "1742-6": "alt_u_per_l",
    "1920-8": "ast_u_per_l",
    "2324-2": "ggt_u_per_l",
    "6768-6": "alp_u_per_l",
    "1751-7": "albumin_g_per_dl",
    "1975-2": "bilirubin_mg_per_dl",
    # Kidney function
    "2160-0": "creatinine_mg_per_dl",
    "33914-3": "egfr_ml_per_min",
    "3094-0": "bun_mg_per_dl",
    "3084-1": "uric_acid_mg_per_dl",
    # Metabolic / cardiac
    "4548-4": "hba1c_pct",
    "2345-7": "glucose_mg_per_dl",
    "13457-7": "ldl_mg_per_dl",
    "2085-9": "hdl_mg_per_dl",
    "2571-8": "triglycerides_mg_per_dl",
    "30522-7": "hscrp_mg_per_l",
}

# ICD-10 → Eirion condition_id mapping
ICD10_TO_CONDITION: Dict[str, str] = {
    "E11": "type2_diabetes",
    "E14": "type2_diabetes",
    "K76.0": "fatty_liver",
    "K74": "nafld",
    "I10": "hypertension",
    "E78": "hyperlipidemia",
    "E03": "hypothyroidism",
    "E05": "hyperthyroidism",
    "F41": "anxiety",
    "F32": "depression",
    "N18": "kidney_disease",
    "E88.81": "metabolic_syndrome",
    "E11.65": "prediabetes",
    "M10": "gout",
    "G47": "sleep_disorder",
}


# ──────────────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class FHIRObservation:
    loinc_code: str
    display: str
    value: float
    unit: str
    effective_date: str
    status: str = "final"


@dataclass
class WearableReadiness:
    date: str
    score: int                      # 0-100
    hrv_balance: float              # ms
    resting_hr: int                 # bpm
    sleep_score: int
    sleep_hours: float
    activity_score: int
    source: str = "oura"


# ──────────────────────────────────────────────────────────────────────────────
# FHIR Observation → ExtendedLabs converter
# ──────────────────────────────────────────────────────────────────────────────

def fhir_obs_to_labs(observations: List[FHIRObservation]) -> Dict[str, Any]:
    """
    Convert a list of FHIR Observations into an ExtendedLabs-compatible dict.
    Call as: Labs(**fhir_obs_to_labs(obs_list))
    """
    labs: Dict[str, Any] = {}
    for obs in observations:
        field_name = LOINC_TO_LAB_FIELD.get(obs.loinc_code)
        if field_name and obs.value is not None:
            labs[field_name] = obs.value

    if observations:
        labs["lab_report_date"] = observations[-1].effective_date
        labs["lab_name"] = f"FHIR ({observations[-1].source if hasattr(observations[-1], 'source') else 'EHR'})"

    return labs


def fhir_condition_to_eirion(icd10_code: str) -> Optional[str]:
    """Map an ICD-10 code to an Eirion condition_id. Returns None if unknown."""
    # Try exact match first, then prefix match
    exact = ICD10_TO_CONDITION.get(icd10_code)
    if exact:
        return exact
    for prefix, cid in ICD10_TO_CONDITION.items():
        if icd10_code.startswith(prefix):
            return cid
    return None


def fhir_medication_to_compound(medication_name: str, dose_mg: float) -> Optional[Dict]:
    """
    Approximate mapping from medication display name to Eirion compound_id.
    Returns RegimenItem-compatible dict or None.
    """
    name_lower = medication_name.lower()
    # Simple keyword lookup — extend with full RxNorm mapping once available
    mappings = {
        "atorvastatin": "atorvastatin",
        "metformin": "metformin",
        "vitamin d": "vitamin_d3",
        "omega": "omega3",
        "magnesium": "magnesium",
        "zinc": "zinc",
        "coenzyme q": "coq10",
        "ashwagandha": "ashwagandha",
        "berberine": "berberine",
    }
    for keyword, compound_id in mappings.items():
        if keyword in name_lower:
            return {
                "compound_id": compound_id,
                "dose_mg": dose_mg,
                "frequency_per_day": 1,
                "is_rx": True,
                "prescribed_by": "gp",
            }
    return None


# ──────────────────────────────────────────────────────────────────────────────
# FHIR Client
# ──────────────────────────────────────────────────────────────────────────────

class FHIRClient:
    """
    Minimal SMART-on-FHIR R4 client.
    Handles Observation, MedicationRequest, and Condition resources.
    """

    def __init__(self, base_url: str, access_token: str):
        self.base_url     = base_url.rstrip("/")
        self.access_token = access_token
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/fhir+json",
        }

    async def _get(self, path: str, params: Dict = None) -> Dict:
        """Async GET against FHIR server."""
        if not _HTTPX:
            raise RuntimeError("httpx required: pip install httpx")
        url = f"{self.base_url}/{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(url, headers=self._headers, params=params or {})
            res.raise_for_status()
            return res.json()

    async def fetch_observations(
        self, patient_id: str, loinc_codes: Optional[List[str]] = None
    ) -> List[FHIRObservation]:
        """
        Fetch lab Observations for a patient.
        Optionally filter by LOINC codes.
        """
        codes = loinc_codes or list(LOINC_TO_LAB_FIELD.keys())
        params = {
            "patient": patient_id,
            "code": ",".join(codes),
            "_sort": "-date",
            "_count": "50",
        }
        try:
            bundle = await self._get("Observation", params)
        except Exception as e:
            logger.error("[FHIR] fetch_observations failed: %s", e)
            return []

        observations = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") != "Observation":
                continue
            try:
                coding   = resource["code"]["coding"][0]
                value_q  = resource.get("valueQuantity", {})
                obs = FHIRObservation(
                    loinc_code     = coding.get("code", ""),
                    display        = coding.get("display", "Unknown"),
                    value          = float(value_q.get("value", 0)),
                    unit           = value_q.get("unit", ""),
                    effective_date = resource.get("effectiveDateTime", "")[:10],
                    status         = resource.get("status", "final"),
                )
                observations.append(obs)
            except (KeyError, ValueError, TypeError):
                continue

        return observations

    async def fetch_medications(self, patient_id: str) -> List[Dict]:
        """
        Fetch active MedicationRequests and return compound-like dicts.
        """
        params = {"patient": patient_id, "status": "active", "_count": "30"}
        try:
            bundle = await self._get("MedicationRequest", params)
        except Exception as e:
            logger.error("[FHIR] fetch_medications failed: %s", e)
            return []

        compounds = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") != "MedicationRequest":
                continue
            try:
                med    = resource.get("medicationCodeableConcept", {})
                name   = med.get("text") or med.get("coding", [{}])[0].get("display", "")
                dose   = resource.get("dosageInstruction", [{}])[0]
                dose_q = dose.get("doseAndRate", [{}])[0].get("doseQuantity", {})
                mg     = float(dose_q.get("value", 0))
                comp   = fhir_medication_to_compound(name, mg)
                if comp:
                    compounds.append(comp)
            except (KeyError, ValueError, TypeError, IndexError):
                continue
        return compounds

    async def fetch_conditions(self, patient_id: str) -> List[str]:
        """Fetch active Conditions and map to Eirion condition_ids."""
        params = {"patient": patient_id, "clinical-status": "active"}
        try:
            bundle = await self._get("Condition", params)
        except Exception as e:
            logger.error("[FHIR] fetch_conditions failed: %s", e)
            return []

        condition_ids = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            codings  = resource.get("code", {}).get("coding", [])
            for coding in codings:
                icd10 = coding.get("code", "")
                cid   = fhir_condition_to_eirion(icd10)
                if cid and cid not in condition_ids:
                    condition_ids.append(cid)
        return condition_ids


# ──────────────────────────────────────────────────────────────────────────────
# SMART-on-FHIR OAuth2 helpers
# ──────────────────────────────────────────────────────────────────────────────

class SMARTAuthHandler:
    """
    Handles the SMART-on-FHIR Authorization Code OAuth2 flow.
    Produces access + refresh tokens for downstream FHIRClient use.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        token_url: str,
        authorize_url: str,
    ):
        self.client_id     = client_id
        self.client_secret = client_secret
        self.redirect_uri  = redirect_uri
        self.token_url     = token_url
        self.authorize_url = authorize_url

    def get_authorization_url(self, state: str, aud: str) -> str:
        """Build the authorization URL to redirect the user to."""
        from urllib.parse import urlencode
        params = {
            "response_type": "code",
            "client_id":     self.client_id,
            "redirect_uri":  self.redirect_uri,
            "scope":         "patient/Observation.read patient/MedicationRequest.read patient/Condition.read openid fhirUser",
            "state":         state,
            "aud":           aud,
        }
        return f"{self.authorize_url}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> Dict:
        """Exchange authorization code for access + refresh tokens."""
        if not _HTTPX:
            raise RuntimeError("httpx required")
        async with httpx.AsyncClient() as client:
            res = await client.post(
                self.token_url,
                data={
                    "grant_type":    "authorization_code",
                    "code":          code,
                    "redirect_uri":  self.redirect_uri,
                    "client_id":     self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            res.raise_for_status()
            return res.json()

    async def refresh_token(self, refresh_token_val: str) -> Dict:
        """Refresh access token using refresh_token."""
        if not _HTTPX:
            raise RuntimeError("httpx required")
        async with httpx.AsyncClient() as client:
            res = await client.post(
                self.token_url,
                data={
                    "grant_type":    "refresh_token",
                    "refresh_token": refresh_token_val,
                    "client_id":     self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            res.raise_for_status()
            return res.json()


# ──────────────────────────────────────────────────────────────────────────────
# Oura Ring v2 Client
# ──────────────────────────────────────────────────────────────────────────────

class OuraClient:
    """
    Oura Ring API v2 REST client.
    Fetches daily readiness, sleep, and heart rate data.
    """
    BASE = "https://api.ouraring.com/v2/usercollection"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self._headers = {"Authorization": f"Bearer {access_token}"}

    async def _get(self, endpoint: str, params: Dict = None) -> Dict:
        if not _HTTPX:
            raise RuntimeError("httpx required")
        url = f"{self.BASE}/{endpoint}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(url, headers=self._headers, params=params or {})
            res.raise_for_status()
            return res.json()

    async def get_daily_readiness(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> List[WearableReadiness]:
        """Fetch daily readiness scores (last 7 days by default)."""
        from datetime import date, timedelta
        today       = date.today()
        start_date  = start_date or (today - timedelta(days=7)).isoformat()
        end_date    = end_date   or today.isoformat()

        try:
            data = await self._get("daily_readiness", {
                "start_date": start_date, "end_date": end_date
            })
        except Exception as e:
            logger.error("[Oura] get_daily_readiness failed: %s", e)
            return []

        results = []
        for item in data.get("data", []):
            contributors = item.get("contributors", {})
            results.append(WearableReadiness(
                date          = item.get("day", ""),
                score         = item.get("score", 0),
                hrv_balance   = float(contributors.get("hrv_balance", 5)),
                resting_hr    = int(contributors.get("resting_heart_rate", 60)),
                sleep_score   = int(contributors.get("sleep_balance", 80)),
                sleep_hours   = 7.0,   # fetched separately from daily_sleep
                activity_score= int(contributors.get("movement_balance", 75)),
                source        = "oura",
            ))
        return results

    async def get_daily_sleep(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Fetch daily sleep data."""
        from datetime import date, timedelta
        today = date.today()
        start = start_date or (today - timedelta(days=7)).isoformat()
        end   = end_date   or today.isoformat()
        try:
            data = await self._get("daily_sleep", {"start_date": start, "end_date": end})
            return data.get("data", [])
        except Exception as e:
            logger.error("[Oura] get_daily_sleep failed: %s", e)
            return []

    def readiness_to_lifestyle_patch(self, readiness: WearableReadiness) -> Dict:
        """
        Convert an Oura readiness record to a LifestyleIntake patch dict.
        Use this to pre-fill the wizard from wearable data.
        """
        return {
            "sleep_hours_avg": readiness.sleep_hours,
            "sleep_quality":   min(10, readiness.sleep_score // 10),
            "stress_level":    max(1, min(10, 10 - readiness.hrv_balance // 10)),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Garmin / HealthKit stubs (OAuth flows TBD)
# ──────────────────────────────────────────────────────────────────────────────

class GarminClient:
    """Stub — Garmin Connect API (OAuth1 → OAuth2 migration in progress)."""
    def __init__(self, *args, **kwargs):
        logger.warning("[Garmin] GarminClient is a stub — OAuth not yet implemented.")

    async def get_vo2max(self) -> Optional[float]: return None
    async def get_training_load(self) -> Optional[float]: return None


class WearableFHIRIntegration:
    """
    High-level facade combining FHIR + Wearable data sources.
    Produces a unified profile patch that can be merged into an AnalysisRequest.
    """

    def __init__(
        self,
        fhir_client: Optional[FHIRClient] = None,
        oura_client: Optional[OuraClient] = None,
    ):
        self.fhir  = fhir_client
        self.oura  = oura_client

    async def pull_all(self, patient_id: str = "") -> Dict:
        """
        Aggregate data from all connected sources.
        Returns a dict usable as a partial AnalysisRequest update.
        """
        result: Dict = {}

        if self.fhir and patient_id:
            obs   = await self.fhir.fetch_observations(patient_id)
            labs  = fhir_obs_to_labs(obs)
            if labs:
                result["labs"] = labs

            meds  = await self.fhir.fetch_medications(patient_id)
            if meds:
                result["fhir_medications"] = meds   # caller merges into regimen

            conds = await self.fhir.fetch_conditions(patient_id)
            if conds:
                result["fhir_conditions"] = conds

        if self.oura:
            readiness_list = await self.oura.get_daily_readiness()
            if readiness_list:
                latest = readiness_list[0]
                result["lifestyle_patch"] = self.oura.readiness_to_lifestyle_patch(latest)
                result["wearable_readiness"] = {
                    "score": latest.score,
                    "hrv_balance": latest.hrv_balance,
                    "resting_hr": latest.resting_hr,
                    "date": latest.date,
                    "source": "oura",
                }

        result["synced_at"] = datetime.now(timezone.utc).isoformat()
        return result

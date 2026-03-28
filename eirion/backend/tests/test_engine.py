"""
EIRION Unit Tests — Engine Validation
Tests the three canonical scenarios from the spec exactly.
Run: cd backend && python -m pytest tests/test_engine.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from models.request import AnalysisRequest, Patient, Lifestyle, Genetics, RegimenItem, Labs
from engine.scorer import run_liver_analysis


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def make_request(**overrides) -> AnalysisRequest:
    """Build a base AnalysisRequest with optional overrides."""
    defaults = dict(
        patient=Patient(age=35, sex="female", weight_kg=62, height_cm=165),
        lifestyle=Lifestyle(
            sugar_g_per_day=50,
            alcohol_units_per_week=0,
            sleep_hours_per_night=7,
            activity_level="moderate",
            stress_level=5,
        ),
        genetics=Genetics(cyp2d6_metabolizer="normal", cyp2c19_metabolizer="unknown"),
        regimen=[RegimenItem(compound_id="omega3", dose_mg=2000)],
        labs=None,
    )
    defaults.update(overrides)
    return AnalysisRequest(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — Priya Canonical (Amber scenario)
# ─────────────────────────────────────────────────────────────────────────────

def test_priya_canonical():
    """
    Priya: 35F, poor CYP2D6, high sugar, Ashwagandha + Metformin + Omega3 + VitD.
    Expected: risk=amber, liver_index 83-87, trajectory declining, ≥2 recs,
              first rec is swap_ashwagandha_rhodiola.
    """
    request = make_request(
        patient=Patient(age=35, sex="female", weight_kg=62, height_cm=165),
        lifestyle=Lifestyle(
            sugar_g_per_day=140,
            alcohol_units_per_week=0,
            sleep_hours_per_night=6,
            activity_level="moderate",
            stress_level=7,
        ),
        genetics=Genetics(cyp2d6_metabolizer="poor", cyp2c19_metabolizer="unknown"),
        regimen=[
            RegimenItem(compound_id="omega3",      dose_mg=2000),
            RegimenItem(compound_id="vitamin_d",   dose_mg=5000),
            RegimenItem(compound_id="ashwagandha", dose_mg=600),
            RegimenItem(compound_id="metformin",   dose_mg=500),
        ],
        labs=Labs(ast_u_per_l=20, alt_u_per_l=22, bilirubin_mg_per_dl=0.8),
    )

    result = run_liver_analysis(request)

    # Risk level must be amber
    assert result.risk_summary.risk_level == "amber", (
        f"Expected amber, got {result.risk_summary.risk_level} "
        f"(liver_index={result.risk_summary.liver_index_now})"
    )

    # Liver index in range 70-92 (amber band, tuned for Priya)
    idx = result.risk_summary.liver_index_now
    assert 70 <= idx <= 92, f"Liver index {idx} out of expected amber range"

    # Trajectory must be declining
    assert result.trajectory[5].liver_index < result.trajectory[0].liver_index, (
        "Expected declining trajectory"
    )

    # At least 2 recommendations
    assert len(result.recommendations) >= 2, (
        f"Expected ≥2 recommendations, got {len(result.recommendations)}"
    )

    # First recommendation must be ashwagandha swap
    first_rec_id = result.recommendations[0].id
    assert first_rec_id == "swap_ashwagandha_rhodiola", (
        f"Expected swap_ashwagandha_rhodiola as first rec, got {first_rec_id}"
    )

    # Biological age should be higher than chronological (Priya is under stress)
    assert result.biological_age >= 35, (
        f"Expected biological age ≥35, got {result.biological_age}"
    )

    # Optimized line should be better than current
    assert result.trajectory[5].optimized_liver_index > result.trajectory[5].liver_index, (
        "Optimized trajectory should be better than current at year 5"
    )

    print(f"\n✓ Priya: risk={result.risk_summary.risk_level}, "
          f"index={idx}, bio_age={result.biological_age}, "
          f"recs={len(result.recommendations)}, "
          f"polypharmacy={result.polypharmacy_score}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — Low Risk (Green scenario)
# ─────────────────────────────────────────────────────────────────────────────

def test_low_risk():
    """
    28M, 50g sugar, normal CYP2D6, Omega3 + Magnesium only.
    Expected: risk=green, liver_index ≥90, gentle trajectory, 0-1 recs.
    """
    request = make_request(
        patient=Patient(age=28, sex="male", weight_kg=75, height_cm=178),
        lifestyle=Lifestyle(
            sugar_g_per_day=50,
            alcohol_units_per_week=0,
            sleep_hours_per_night=8,
            activity_level="moderate",
            stress_level=4,
        ),
        genetics=Genetics(cyp2d6_metabolizer="normal"),
        regimen=[
            RegimenItem(compound_id="omega3",    dose_mg=2000),
            RegimenItem(compound_id="magnesium", dose_mg=400),
        ],
    )

    result = run_liver_analysis(request)

    assert result.risk_summary.risk_level == "green", (
        f"Expected green, got {result.risk_summary.risk_level} "
        f"(liver_index={result.risk_summary.liver_index_now})"
    )

    assert result.risk_summary.liver_index_now >= 88, (
        f"Expected liver index ≥88, got {result.risk_summary.liver_index_now}"
    )

    # Gentle trajectory — less than 10% drop over 5 years
    drop = result.trajectory[0].liver_index - result.trajectory[5].liver_index
    assert drop < 15, f"Expected small drop, got {drop:.1f} points"

    assert len(result.recommendations) <= 2, (
        f"Expected ≤2 recs for low-risk user, got {len(result.recommendations)}"
    )

    print(f"\n✓ Low-risk: risk={result.risk_summary.risk_level}, "
          f"index={result.risk_summary.liver_index_now}, "
          f"recs={len(result.recommendations)}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — High Risk (Red scenario)
# ─────────────────────────────────────────────────────────────────────────────

def test_high_risk():
    """
    45F, 180g sugar, poor CYP2D6, Ashwagandha + statin + SSRI + alcohol 10 units/wk.
    Expected: risk=red, liver_index <70, steep decline, ≥4 recs.
    """
    request = make_request(
        patient=Patient(age=45, sex="female", weight_kg=70, height_cm=162),
        lifestyle=Lifestyle(
            sugar_g_per_day=180,
            alcohol_units_per_week=10,
            sleep_hours_per_night=5,
            activity_level="sedentary",
            stress_level=9,
        ),
        genetics=Genetics(cyp2d6_metabolizer="poor", cyp2c19_metabolizer="poor"),
        regimen=[
            RegimenItem(compound_id="ashwagandha",  dose_mg=600),
            RegimenItem(compound_id="atorvastatin", dose_mg=20),
            RegimenItem(compound_id="sertraline",   dose_mg=100),
            RegimenItem(compound_id="berberine",    dose_mg=500),
        ],
        labs=Labs(ast_u_per_l=48, alt_u_per_l=52),  # Already elevated
    )

    result = run_liver_analysis(request)

    assert result.risk_summary.risk_level == "red", (
        f"Expected red, got {result.risk_summary.risk_level} "
        f"(liver_index={result.risk_summary.liver_index_now})"
    )

    assert result.risk_summary.liver_index_now < 70, (
        f"Expected liver index <70, got {result.risk_summary.liver_index_now}"
    )

    # Steep decline
    drop = result.trajectory[0].liver_index - result.trajectory[5].liver_index
    assert drop >= 15, f"Expected steep decline (≥15 pts), got {drop:.1f}"

    assert len(result.recommendations) >= 3, (
        f"Expected ≥3 recs for high-risk user, got {len(result.recommendations)}"
    )

    print(f"\n✓ High-risk: risk={result.risk_summary.risk_level}, "
          f"index={result.risk_summary.liver_index_now}, "
          f"drop={drop:.1f}pts, recs={len(result.recommendations)}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — API schema round-trip via TestClient
# ─────────────────────────────────────────────────────────────────────────────

def test_api_health():
    """Smoke test that the FastAPI app starts and /health returns 200."""
    from fastapi.testclient import TestClient
    import importlib, sys

    # Ensure clean import
    for mod in list(sys.modules.keys()):
        if "main" in mod:
            del sys.modules[mod]

    import main
    client = TestClient(main.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("\n✓ Health endpoint: ok")


def test_api_priya_e2e():
    """Full POST /analysis/run with Priya data via TestClient."""
    from fastapi.testclient import TestClient
    import main

    client = TestClient(main.app)

    payload = {
        "patient": {"age": 35, "sex": "female", "weight_kg": 62, "height_cm": 165},
        "lifestyle": {
            "sugar_g_per_day": 140,
            "alcohol_units_per_week": 0,
            "sleep_hours_per_night": 6,
            "activity_level": "moderate",
            "stress_level": 7,
        },
        "genetics": {"cyp2d6_metabolizer": "poor"},
        "regimen": [
            {"compound_id": "omega3",      "dose_mg": 2000},
            {"compound_id": "vitamin_d",   "dose_mg": 5000},
            {"compound_id": "ashwagandha", "dose_mg": 600},
            {"compound_id": "metformin",   "dose_mg": 500},
        ],
        "labs": {"ast_u_per_l": 20, "alt_u_per_l": 22, "bilirubin_mg_per_dl": 0.8},
    }

    response = client.post("/analysis/run", json=payload)
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"

    data = response.json()
    assert "risk_summary" in data
    assert "trajectory" in data
    assert "recommendations" in data
    assert len(data["trajectory"]) == 6
    print(f"\n✓ E2E API: risk={data['risk_summary']['risk_level']}, "
          f"recs={len(data['recommendations'])}")

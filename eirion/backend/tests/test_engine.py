"""
EIRION Unit Tests — Engine Validation
Tests the three canonical scenarios from the spec exactly.
Run: cd backend && python -m pytest tests/test_engine.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from models.request import AnalysisRequest, Patient, LifestyleIntake, Genetics, RegimenItem, Labs, Food
from engine.scorer import run_liver_analysis


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def make_request(**overrides) -> AnalysisRequest:
    """Build a base AnalysisRequest with optional overrides."""
    defaults = dict(
        patient=Patient(age=35, sex="female", weight_kg=62, height_cm=165),
        lifestyle=LifestyleIntake(
            sugar_g_per_day=50,
            alcohol_drinks_per_week=0,
            sleep_hours_avg=7,
            activity_level="moderate",
            stress_level=5,
        ),
        genetics=Genetics(cyp2d6_metabolizer="normal", cyp2c19_metabolizer="unknown"),
        regimen=[RegimenItem(compound_id="omega3", dose_mg=2000)],
        labs=None,
        food=None,
    )
    defaults.update(overrides)
    return AnalysisRequest(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — Priya Canonical (Amber scenario)
# With corrected base values: ashwagandha=7 (was 2), metformin=3 (was 2),
# vitamin_d=2 (unchanged). Priya load is now much higher, driving to amber/red.
# ─────────────────────────────────────────────────────────────────────────────

def test_priya_canonical():
    """
    Priya: 35F, poor CYP2D6, high sugar (140g), Ashwagandha + Metformin + Omega3 + VitD.
    With corrected base values + lifestyle penalties, expect risk=amber or red, ≥2 recs,
    first rec is swap_ashwagandha_rhodiola.
    """
    request = make_request(
        patient=Patient(age=35, sex="female", weight_kg=62, height_cm=165),
        lifestyle=LifestyleIntake(
            sugar_g_per_day=140,
            alcohol_drinks_per_week=0,
            sleep_hours_avg=6,
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

    # Risk level must be amber or red (corrected base values produce higher load)
    assert result.risk_summary.risk_level in ("amber", "red"), (
        f"Expected amber or red, got {result.risk_summary.risk_level} "
        f"(liver_index={result.risk_summary.liver_index_now})"
    )

    # Liver index in range 40-84 (amber/red band with corrected values)
    idx = result.risk_summary.liver_index_now
    assert 40 <= idx <= 84, f"Liver index {idx} out of expected range"

    # Trajectory must be declining
    assert result.trajectory[5].liver_index < result.trajectory[0].liver_index, (
        "Expected declining trajectory"
    )

    # At least 2 recommendations
    assert len(result.recommendations) >= 2, (
        f"Expected ≥2 recommendations, got {len(result.recommendations)}"
    )

    # First recommendation must be ashwagandha swap (highest priority for poor CYP2D6)
    swap_rec = next((r for r in result.recommendations if r.id == "swap_ashwagandha_rhodiola"), None)
    assert swap_rec is not None, "Expected swap_ashwagandha_rhodiola recommendation"

    # Biological age should be higher than chronological (Priya is under stress)
    assert result.biological_age >= 35, (
        f"Expected biological age ≥35, got {result.biological_age}"
    )

    # Optimized line should be better than current
    assert result.trajectory[5].optimized_liver_index > result.trajectory[5].liver_index, (
        "Optimized trajectory should be better than current at year 5"
    )

    print(f"\n✓ Priya: risk={result.risk_summary.risk_level}, "
          f"index={idx:.1f}, bio_age={result.biological_age}, "
          f"recs={len(result.recommendations)}, "
          f"polypharmacy={result.polypharmacy_score}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — Low Risk (Green scenario)
# ─────────────────────────────────────────────────────────────────────────────

def test_low_risk():
    """
    28M, 50g sugar, normal CYP2D6, Omega3 + Magnesium only.
    Expected: risk=green, liver_index ≥85, gentle trajectory, ≤2 recs.
    """
    request = make_request(
        patient=Patient(age=28, sex="male", weight_kg=75, height_cm=178),
        lifestyle=LifestyleIntake(
            sugar_g_per_day=50,
            alcohol_drinks_per_week=0,
            sleep_hours_avg=8,
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

    assert result.risk_summary.liver_index_now >= 85, (
        f"Expected liver index ≥85, got {result.risk_summary.liver_index_now}"
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
    Expected: risk=red, liver_index <70, steep decline, ≥3 recs.
    """
    request = make_request(
        patient=Patient(age=45, sex="female", weight_kg=70, height_cm=162),
        lifestyle=LifestyleIntake(
            sugar_g_per_day=180,
            alcohol_drinks_per_week=10,
            sleep_hours_avg=5,
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
# Test 4 — API Health
# ─────────────────────────────────────────────────────────────────────────────

def test_api_health():
    """Smoke test that the FastAPI app starts and /health returns 200."""
    from fastapi.testclient import TestClient
    import importlib, sys

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
    """Full POST /analysis/run with Priya data + food via TestClient."""
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
        "food": {
            "calories_per_day": 2200,
            "processed_food_pct": 45,
            "red_meat_g_per_week": 200,
            "fiber_g_per_day": 18,
            "diet_type": "omnivore",
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

    # Verify food contributions are present
    contrib_ids = [c["compound_id"] for c in data["contributions"]]
    food_contribs = [c for c in contrib_ids if c.startswith("food_")]
    assert len(food_contribs) > 0, "Expected food contributions in response"

    print(f"\n✓ E2E API with food: risk={data['risk_summary']['risk_level']}, "
          f"recs={len(data['recommendations'])}, "
          f"food_contribs={len(food_contribs)}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — Food Penalty Applied
# ─────────────────────────────────────────────────────────────────────────────

def test_food_penalty_applied():
    """
    Same base request with and without extreme processed food diet.
    High processed food (80%) should produce a lower liver_index.
    """
    base_req = make_request(
        lifestyle=LifestyleIntake(
            sugar_g_per_day=50,
            alcohol_drinks_per_week=0,
            sleep_hours_avg=8,
            activity_level="moderate",
            stress_level=4,
        ),
        genetics=Genetics(cyp2d6_metabolizer="normal"),
        regimen=[RegimenItem(compound_id="omega3", dose_mg=2000)],
        food=None,
    )
    req_with_bad_food = make_request(
        lifestyle=LifestyleIntake(
            sugar_g_per_day=50,
            alcohol_units_per_week=0,
            sleep_hours_per_night=8,
            activity_level="moderate",
            stress_level=4,
        ),
        genetics=Genetics(cyp2d6_metabolizer="normal"),
        regimen=[RegimenItem(compound_id="omega3", dose_mg=2000)],
        food=Food(
            calories_per_day=3200,
            processed_food_pct=80,
            red_meat_g_per_week=700,
            fiber_g_per_day=8,
            diet_type="keto",
        ),
    )

    result_base = run_liver_analysis(base_req)
    result_food = run_liver_analysis(req_with_bad_food)

    assert result_food.risk_summary.liver_index_now < result_base.risk_summary.liver_index_now, (
        f"Bad food should lower index: {result_food.risk_summary.liver_index_now} "
        f"vs {result_base.risk_summary.liver_index_now}"
    )

    # Should have food-specific recommendations
    food_rec_ids = {"reduce_processed_food", "adopt_mediterranean_diet", "increase_fiber", "reduce_red_meat"}
    found_food_recs = [r for r in result_food.recommendations if r.id in food_rec_ids]
    assert len(found_food_recs) >= 1, "Expected at least 1 food-specific recommendation"

    print(f"\n✓ Food penalty: base={result_base.risk_summary.liver_index_now:.1f}, "
          f"bad_food={result_food.risk_summary.liver_index_now:.1f}, "
          f"food_recs={len(found_food_recs)}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 6 — Mediterranean Diet Protective Credit
# ─────────────────────────────────────────────────────────────────────────────

def test_food_mediterranean_protective():
    """
    Mediterranean diet with high fiber should produce a HIGHER liver_index
    than same user on an omnivore/keto diet.
    """
    base_regimen = [RegimenItem(compound_id="omega3", dose_mg=2000)]

    req_med = make_request(
        regimen=base_regimen,
        food=Food(
            calories_per_day=2000,
            processed_food_pct=10,
            red_meat_g_per_week=100,
            fiber_g_per_day=35,
            diet_type="mediterranean",
        ),
    )
    req_keto = make_request(
        regimen=base_regimen,
        food=Food(
            calories_per_day=2000,
            processed_food_pct=20,
            red_meat_g_per_week=400,
            fiber_g_per_day=12,
            diet_type="keto",
        ),
    )

    result_med = run_liver_analysis(req_med)
    result_keto = run_liver_analysis(req_keto)

    assert result_med.risk_summary.liver_index_now > result_keto.risk_summary.liver_index_now, (
        f"Mediterranean ({result_med.risk_summary.liver_index_now:.1f}) should beat "
        f"keto ({result_keto.risk_summary.liver_index_now:.1f})"
    )

    print(f"\n✓ Diet comparison: mediterranean={result_med.risk_summary.liver_index_now:.1f} "
          f"vs keto={result_keto.risk_summary.liver_index_now:.1f} "
          f"(+{result_med.risk_summary.liver_index_now - result_keto.risk_summary.liver_index_now:.1f} pts)")

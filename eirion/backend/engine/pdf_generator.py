"""
EIRION Clinical Report Generator — Comprehensive Edition
=========================================================
Generates a professional multi-page PDF containing everything the dashboard
shows, structured as a real clinical handout:

  Page 1  — Cover (patient demographics, report metadata, branding)
  Page 2  — Executive Summary (risk scores, biological age, polypharmacy)
  Page 3  — Multi-Organ Scorecard (all organs with projected 5-yr scores)
  Page 4  — Pharmacogenomics Panel (full CYP450 + transporter + folate)
  Page 5  — Laboratory Results (LFT + KFT + Metabolic/Cardiac with ranges)
  Page 6  — Current Regimen & Drug Interactions
  Page 7  — 5-Year Trajectory Chart (baseline vs optimised)
  Page 8  — Compound Load Analysis (what is driving each organ score)
  Page 9+ — Clinical Recommendations (all, with evidence & expected impact)
  Final   — Pathway Chains summary + full legal disclaimer
"""

import io
import uuid
from datetime import datetime, timezone
from typing import List

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker

from models.request import AnalysisRequest
from models.response import AnalysisResponse

# ── Brand palette ─────────────────────────────────────────────────────────────
DARK      = colors.HexColor("#1E293B")
MID       = colors.HexColor("#475569")
LIGHT     = colors.HexColor("#94A3B8")
PALE      = colors.HexColor("#F8FAFC")
BORDER    = colors.HexColor("#E2E8F0")
GREEN     = colors.HexColor("#10B981")
AMBER     = colors.HexColor("#F59E0B")
RED       = colors.HexColor("#EF4444")
BLUE      = colors.HexColor("#3B82F6")
WHITE     = colors.white
BG_GREEN  = colors.HexColor("#ECFDF5")
BG_AMBER  = colors.HexColor("#FFFBEB")
BG_RED    = colors.HexColor("#FEF2F2")

W, H = A4  # 595.27 x 841.89 pts

# ── Helpers ───────────────────────────────────────────────────────────────────

def _risk_color(level: str) -> colors.Color:
    return {"green": GREEN, "amber": AMBER, "red": RED}.get(level, LIGHT)

def _risk_bg(level: str) -> colors.Color:
    return {"green": BG_GREEN, "amber": BG_AMBER, "red": BG_RED}.get(level, PALE)

def _fmt(val, suffix="", decimals=1):
    if val is None: return "—"
    if isinstance(val, float): return f"{val:.{decimals}f}{suffix}"
    return f"{val}{suffix}"

def _title(name: str) -> str:
    return name.replace("_", " ").title()

def _action_color(action: str) -> colors.Color:
    return {"reduce": RED, "swap": AMBER, "add": GREEN,
            "behavior_change": BLUE, "consult": MID}.get(action, DARK)


# ── Style factory ─────────────────────────────────────────────────────────────

def _styles():
    base = getSampleStyleSheet()

    def ps(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    S = {
        "h1":       ps("h1",       "Heading1", fontName="Helvetica-Bold",
                        fontSize=26, textColor=DARK, spaceAfter=6, leading=30),
        "h2":       ps("h2",       "Heading2", fontName="Helvetica-Bold",
                        fontSize=14, textColor=DARK, spaceBefore=14, spaceAfter=6, leading=18),
        "h3":       ps("h3",       "Heading3", fontName="Helvetica-Bold",
                        fontSize=11, textColor=MID, spaceBefore=10, spaceAfter=4, leading=14),
        "body":     ps("body",     "Normal", fontName="Helvetica",
                        fontSize=9,  textColor=DARK, spaceAfter=4, leading=13),
        "body_mid": ps("body_mid", "Normal", fontName="Helvetica",
                        fontSize=9,  textColor=MID, spaceAfter=4, leading=13),
        "small":    ps("small",    "Normal", fontName="Helvetica",
                        fontSize=8,  textColor=LIGHT, spaceAfter=3, leading=11),
        "label":    ps("label",    "Normal", fontName="Helvetica-Bold",
                        fontSize=8,  textColor=MID, spaceAfter=2, leading=10),
        "metric":   ps("metric",   "Normal", fontName="Helvetica-Bold",
                        fontSize=20, textColor=DARK, spaceAfter=0, leading=24),
        "tag_g":    ps("tag_g",    "Normal", fontName="Helvetica-Bold",
                        fontSize=8,  textColor=GREEN, leading=10),
        "tag_a":    ps("tag_a",    "Normal", fontName="Helvetica-Bold",
                        fontSize=8,  textColor=AMBER, leading=10),
        "tag_r":    ps("tag_r",    "Normal", fontName="Helvetica-Bold",
                        fontSize=8,  textColor=RED, leading=10),
        "disclaimer": ps("disc",   "Normal", fontName="Helvetica-Oblique",
                        fontSize=7.5, textColor=LIGHT, leading=11),
        "cover_sub": ps("csub",   "Normal", fontName="Helvetica",
                        fontSize=12, textColor=MID, leading=16),
        "cover_meta": ps("cmeta", "Normal", fontName="Helvetica",
                        fontSize=9,  textColor=LIGHT, leading=13),
        "center_body": ps("cbody","Normal", fontName="Helvetica",
                        fontSize=9, textColor=DARK, alignment=TA_CENTER, leading=13),
    }
    return S


# ── Section divider ───────────────────────────────────────────────────────────

def _section_header(title: str, S) -> list:
    return [
        Spacer(1, 4*mm),
        HRFlowable(width="100%", thickness=1.5, color=DARK, spaceAfter=4),
        Paragraph(title.upper(), S["label"]),
        Spacer(1, 2*mm),
    ]


# ── Table style helpers ───────────────────────────────────────────────────────

def _base_table_style(header_bg=DARK, header_fg=WHITE) -> TableStyle:
    return TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR",   (0, 0), (-1, 0), header_fg),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE]),
        ("GRID",        (0, 0), (-1, -1), 0.4, BORDER),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("PADDING",     (0, 0), (-1, -1), 5),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ])


# ── Lab flag helper ───────────────────────────────────────────────────────────

LAB_RANGES = {
    "ast_u_per_l":           (10, 40,   "U/L",    "AST (SGOT)"),
    "alt_u_per_l":           (7,  56,   "U/L",    "ALT (SGPT)"),
    "ggt_u_per_l":           (12, 60,   "U/L",    "GGT"),
    "alp_u_per_l":           (44, 147,  "U/L",    "ALP"),
    "albumin_g_per_dl":      (3.4, 5.2, "g/dL",   "Albumin"),
    "bilirubin_mg_per_dl":   (0.1, 1.2, "mg/dL",  "Total Bilirubin"),
    "creatinine_mg_per_dl":  (0.5, 1.1, "mg/dL",  "Creatinine"),
    "egfr_ml_per_min":       (60, 999,  "mL/min", "eGFR (CKD-EPI)"),
    "bun_mg_per_dl":         (6,  24,   "mg/dL",  "BUN"),
    "uric_acid_mg_per_dl":   (2.5, 7.0, "mg/dL",  "Uric Acid"),
    "hba1c_pct":             (4.0, 5.6, "%",      "HbA1c"),
    "glucose_mg_per_dl":     (70, 99,   "mg/dL",  "Fasting Glucose"),
    "ldl_mg_per_dl":         (0,  100,  "mg/dL",  "LDL Cholesterol"),
    "hdl_mg_per_dl":         (40, 999,  "mg/dL",  "HDL Cholesterol"),
    "triglycerides_mg_per_dl": (0, 150, "mg/dL",  "Triglycerides"),
    "hscrp_mg_per_l":        (0,  1.0,  "mg/L",   "hsCRP"),
}


def _lab_flag(val, lo, hi) -> str:
    if val is None: return ""
    if val > hi: return "↑ HIGH"
    if val < lo: return "↓ LOW"
    return "Normal"

def _lab_flag_color(val, lo, hi) -> colors.Color:
    if val is None: return MID
    if val > hi: return RED
    if val < lo: return BLUE
    return GREEN


# ── MAIN GENERATOR ────────────────────────────────────────────────────────────

def generate_clinical_pdf(request: AnalysisRequest, response: AnalysisResponse) -> bytes:
    buffer = io.BytesIO()
    report_id = str(uuid.uuid4()).upper()[:13]
    now = datetime.now(timezone.utc)
    generated_str = now.strftime("%d %B %Y at %H:%M UTC")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=14*mm, bottomMargin=14*mm,
        title="Eirion Clinical Report",
        author="Eirion Precision Longevity Platform",
        subject="Pharmacogenomics & Longevity Analysis",
    )

    S     = _styles()
    story = []
    p     = request.patient
    g     = request.genetics
    ls    = request.lifestyle
    risk  = response.risk_summary

    col_w = (W - 36*mm)  # usable width

    # ── ─────────────────────────────────────────────────────────────────────
    # PAGE 1 — COVER
    # ─────────────────────────────────────────────────────────────────────────

    story += [Spacer(1, 12*mm)]

    # Logo bar
    logo_data = [["  EIRION", "PRECISION LONGEVITY REPORT"]]
    logo_t = Table(logo_data, colWidths=[col_w * 0.5, col_w * 0.5])
    logo_t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR",   (0, 0), (0,  0), WHITE),
        ("TEXTCOLOR",   (1, 0), (1,  0), GREEN),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (0,  0), 16),
        ("FONTSIZE",    (1, 0), (1,  0), 10),
        ("ALIGN",       (0, 0), (0,  0), "LEFT"),
        ("ALIGN",       (1, 0), (1,  0), "RIGHT"),
        ("PADDING",     (0, 0), (-1, 0), 10),
        ("VALIGN",      (0, 0), (-1, 0), "MIDDLE"),
    ]))
    story.append(logo_t)
    story += [Spacer(1, 16*mm)]

    story.append(Paragraph("Clinical Longevity Report", S["h1"]))
    story.append(Paragraph(
        "AI-Powered Pharmacogenomics & Multi-Organ Risk Stratification",
        S["cover_sub"]
    ))
    story += [Spacer(1, 10*mm)]

    # Patient + report metadata table
    bmi = p.weight_kg / ((p.height_cm / 100) ** 2) if p.height_cm else None

    meta_data = [
        ["PATIENT DEMOGRAPHICS", "", "REPORT METADATA", ""],
        ["Age",         f"{p.age} years",      "Report ID",    report_id],
        ["Sex",         p.sex.title(),          "Generated",    generated_str],
        ["Weight",      f"{p.weight_kg} kg",    "Platform",     "Eirion v0.3 (AI — Phase 2)"],
        ["Height",      _fmt(p.height_cm, " cm", 0), "Engine",  f"GNN {response.gnn_version}"],
        ["BMI",         _fmt(bmi, " kg/m²"),    "Polypharmacy score", str(response.polypharmacy_score) + " / 100"],
        ["Ethnicity",   _fmt(p.ethnicity) or "Not specified", "Compounds analysed", str(len(request.regimen))],
    ]
    meta_t = Table(meta_data, colWidths=[col_w * 0.16, col_w * 0.34, col_w * 0.22, col_w * 0.28])
    meta_t.setStyle(TableStyle([
        ("SPAN",        (0, 0), (1, 0)),
        ("SPAN",        (2, 0), (3, 0)),
        ("BACKGROUND",  (0, 0), (1, 0), DARK),
        ("BACKGROUND",  (2, 0), (3, 0), DARK),
        ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 9),
        ("FONTNAME",    (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (2, 1), (2, -1), "Helvetica-Bold"),
        ("FONTNAME",    (1, 1), (1, -1), "Helvetica"),
        ("FONTNAME",    (3, 1), (3, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 8.5),
        ("TEXTCOLOR",   (0, 1), (-1, -1), DARK),
        ("TEXTCOLOR",   (0, 1), (0, -1), MID),
        ("TEXTCOLOR",   (2, 1), (2, -1), MID),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE]),
        ("GRID",        (0, 0), (-1, -1), 0.4, BORDER),
        ("PADDING",     (0, 0), (-1, -1), 6),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta_t)
    story += [Spacer(1, 8*mm)]

    # Conditions
    if request.conditions:
        cond_str = "  ·  ".join(
            f"{_title(c.condition_id)} ({c.severity})" for c in request.conditions
        )
        story.append(Paragraph(f"<b>Reported Conditions:</b>  {cond_str}", S["body"]))
    story += [Spacer(1, 6*mm)]

    # Risk headline banner
    level  = risk.risk_level
    rc     = _risk_color(level)
    rbg    = _risk_bg(level)
    banner = Table(
        [[f"OVERALL RISK: {level.upper()}",
          f"Hepatic Index: {risk.liver_index_now:.0f}/100",
          f"5-Yr Projection: −{risk.projected_drop_percent}%"]],
        colWidths=[col_w * 0.4, col_w * 0.3, col_w * 0.3]
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), rbg),
        ("TEXTCOLOR",   (0, 0), (0,  0), rc),
        ("TEXTCOLOR",   (1, 0), (2,  0), DARK),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (0,  0), 12),
        ("FONTSIZE",    (1, 0), (-1, 0), 10),
        ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
        ("PADDING",     (0, 0), (-1, 0), 10),
        ("BOX",         (0, 0), (-1, -1), 1, rc),
    ]))
    story.append(banner)
    story += [Spacer(1, 6*mm)]
    story.append(Paragraph(f"<b>Clinical headline:</b> {risk.headline}", S["body"]))

    story.append(PageBreak())

    # ── ─────────────────────────────────────────────────────────────────────
    # PAGE 2 — EXECUTIVE SUMMARY + BIOLOGICAL AGE
    # ─────────────────────────────────────────────────────────────────────────

    story += _section_header("Executive Summary", S)

    bio_age    = response.biological_age
    chron_age  = p.age
    age_delta  = bio_age - chron_age
    delta_sign = "+" if age_delta >= 0 else ""
    delta_col  = RED if age_delta > 2 else (AMBER if age_delta > 0 else GREEN)

    summary_data = [
        ["METRIC",                    "VALUE",       "CLINICAL NOTE"],
        ["Chronological Age",         f"{chron_age} years",  "Per patient record"],
        ["Biological Age (AI est.)",  f"{bio_age:.1f} years",
         f"Delta: {delta_sign}{age_delta:.1f} years vs chronological"],
        ["Hepatic Index",             f"{risk.liver_index_now:.0f} / 100",
         "Lower = higher cumulative hepatic stress"],
        ["Polypharmacy Score",        f"{response.polypharmacy_score} / 100",
         ">60 warrants medication review"],
        ["5-Year Projected Decline",  f"−{risk.projected_drop_percent}%",
         "Without adopting any recommendations"],
        ["Total Compounds",           str(len(request.regimen)),
         "Supplements + Rx medications analysed"],
        ["DDI Flags",                 str(len(response.ddi_flags)),
         "Drug-drug interactions detected"],
        ["Active Pathways",           str(len(response.active_pathways)),
         "Metabolic pathways modelled"],
    ]
    summary_t = Table(summary_data, colWidths=[col_w * 0.32, col_w * 0.22, col_w * 0.46])
    ts = _base_table_style()
    ts.add("TEXTCOLOR", (1, 3), (1, 3),
           {"green": GREEN, "amber": AMBER, "red": RED}.get(risk.risk_level, DARK))
    ts.add("FONTNAME", (1, 3), (1, 3), "Helvetica-Bold")
    ts.add("TEXTCOLOR", (1, 2), (1, 2), delta_col)
    ts.add("FONTNAME",  (1, 2), (1, 2), "Helvetica-Bold")
    summary_t.setStyle(ts)
    story.append(summary_t)

    # Active pathways pill list
    if response.active_pathways:
        story += [Spacer(1, 4*mm)]
        story.append(Paragraph("<b>Active Metabolic Pathways:</b>  " +
                               "  ·  ".join(response.active_pathways[:12]), S["body_mid"]))

    story.append(PageBreak())

    # ── ─────────────────────────────────────────────────────────────────────
    # PAGE 3 — MULTI-ORGAN SCORECARD
    # ─────────────────────────────────────────────────────────────────────────

    story += _section_header("Multi-Organ Health Scorecard", S)
    story.append(Paragraph(
        "Organ scores are computed by the Eirion GNN engine using compound load, "
        "metabolizer phenotypes, laboratory values, and lifestyle burden. "
        "Scale: 0 = critical risk, 100 = optimal function.",
        S["body_mid"]
    ))
    story += [Spacer(1, 3*mm)]

    if response.organ_scores:
        organ_data = [["Organ", "Score", "Risk", "Primary Driver", "Proj. 5 yr", "Key Pathways"]]
        for os in response.organ_scores:
            rc_cell = _risk_color(os.risk_level)
            organ_data.append([
                os.organ.title(),
                f"{os.score:.0f}/100",
                os.risk_level.upper(),
                os.primary_driver or "—",
                _fmt(os.projected_5yr, "/100", 0),
                ", ".join(os.active_pathways[:3]) or "—",
            ])
        organ_t = Table(organ_data,
                        colWidths=[col_w*0.12, col_w*0.10, col_w*0.09,
                                   col_w*0.22, col_w*0.10, col_w*0.37])
        ost = _base_table_style()
        for i, os in enumerate(response.organ_scores, start=1):
            c = _risk_color(os.risk_level)
            ost.add("TEXTCOLOR", (2, i), (2, i), c)
            ost.add("FONTNAME",  (2, i), (2, i), "Helvetica-Bold")
            score_c = RED if os.score < 50 else (AMBER if os.score < 70 else GREEN)
            ost.add("TEXTCOLOR", (1, i), (1, i), score_c)
            ost.add("FONTNAME",  (1, i), (1, i), "Helvetica-Bold")
        organ_t.setStyle(ost)
        story.append(organ_t)
    else:
        story.append(Paragraph("No multi-organ scores available (Phase 1 engine).", S["body_mid"]))

    # Phase 3 multi-timeframe summary
    if response.multi_organ_projection:
        story += [Spacer(1, 5*mm)]
        story += _section_header("Multi-Timeframe Score Projections (Baseline)", S)
        proj = response.multi_organ_projection
        organs_list = [proj.liver, proj.kidney, proj.cardiovascular, proj.metabolic]
        horizon_keys = ["6m", "1yr", "2yr", "5yr"]

        mtp_data = [["Organ"] + horizon_keys + ["Improvement (5 yr)"]]
        for ot in organs_list:
            row = [ot.organ.title()]
            for h in horizon_keys:
                val = ot.scores_at.get(h)
                row.append(_fmt(val, "", 0) if val else "—")
            impr = ot.improvement_at.get("5yr", 0)
            sign = "+" if impr >= 0 else ""
            row.append(f"{sign}{impr:.1f} pts (opt.)")
            mtp_data.append(row)

        if response.multi_organ_projection.organ_years_gained:
            gain = response.multi_organ_projection.organ_years_gained
            mtp_data.append(["",  "", "", "", "", f"≈ {gain:.1f} healthy organ-years gained"])

        mtp_t = Table(mtp_data, colWidths=[col_w*0.16, col_w*0.12,
                                            col_w*0.12, col_w*0.12,
                                            col_w*0.12, col_w*0.36])
        mtp_t.setStyle(_base_table_style())
        story.append(mtp_t)

    story.append(PageBreak())

    # ── ─────────────────────────────────────────────────────────────────────
    # PAGE 4 — PHARMACOGENOMICS
    # ─────────────────────────────────────────────────────────────────────────

    story += _section_header("Pharmacogenomics Panel (CYP450 & Transporters)", S)
    story.append(Paragraph(
        "Metabolizer phenotypes are inferred from SNP data. Clinical significance "
        "follows CPIC guidelines. Phenotypes affect drug clearance, plasma levels, "
        "and hepatic toxicity risk.",
        S["body_mid"]
    ))
    story += [Spacer(1, 3*mm)]

    def _pheno_color(ph: str) -> colors.Color:
        return {"poor": RED, "intermediate": AMBER,
                "normal": GREEN, "ultra_rapid": BLUE}.get(ph, LIGHT)

    def _pheno_note(gene: str, ph: str) -> str:
        notes = {
            ("CYP2D6", "poor"):          "3–4× plasma accumulation of codeine, tramadol, TCAs, tamoxifen",
            ("CYP2D6", "intermediate"):  "Reduced clearance; dose adjustment may be needed",
            ("CYP2D6", "ultra_rapid"):   "Rapid codeine → morphine conversion; opioid toxicity risk",
            ("CYP2C19", "poor"):         "2–4× esomeprazole/clopidogrel accumulation; reduced clopidogrel efficacy",
            ("CYP2C19", "intermediate"): "Mildly reduced SSRI/PPI clearance",
            ("CYP2C19", "ultra_rapid"):  "Rapid SSRI/PPI metabolism; may need higher doses",
            ("CYP3A4", "poor"):          "Statin, benzodiazepine, immunosuppressant accumulation likely",
            ("CYP2C9", "intermediate"):  "NSAIDs, warfarin, sulfonylurea half-life extended",
            ("CYP2C9", "poor"):          "Warfarin bleeding risk significantly elevated",
            ("CYP1A2", "poor"):          "Caffeine, clozapine, olanzapine accumulate",
        }
        return notes.get((gene, ph), "—")

    pgx_rows = [["Gene", "Phenotype", "Diplotype", "Substrate Examples", "Clinical Note"]]
    pgx_fields = [
        ("CYP2D6",  g.cyp2d6_metabolizer),
        ("CYP2C19", g.cyp2c19_metabolizer),
        ("CYP3A4",  g.cyp3a4_metabolizer),
        ("CYP2C9",  g.cyp2c9_metabolizer),
        ("CYP1A2",  g.cyp1a2_metabolizer),
    ]
    substrate_ex = {
        "CYP2D6":  "Codeine, tamoxifen, TCAs, antidepressants, β-blockers",
        "CYP2C19": "Omeprazole, clopidogrel, SSRIs, diazepam",
        "CYP3A4":  "Statins, benzodiazepines, cyclosporine, ~50% all drugs",
        "CYP2C9":  "Warfarin, NSAIDs, sulfonylureas, losartan",
        "CYP1A2":  "Caffeine, clozapine, olanzapine, theophylline",
    }
    pgx_rows_colors = []
    for gene, ph in pgx_fields:
        dipl = g.diplotypes.get(gene, "—")
        pgx_rows.append([
            gene, ph.replace("_", " ").title(), dipl,
            substrate_ex.get(gene, "—"),
            _pheno_note(gene, ph),
        ])
        pgx_rows_colors.append(_pheno_color(ph))

    # Transporter + folate section
    pgx_rows.append(["SLCO1B1", g.slco1b1_function.replace("_", " ").title(),
                      g.diplotypes.get("SLCO1B1", "—"),
                      "Statins (hepatic uptake transporter)",
                      "Reduced: ↑myopathy risk with atorvastatin/simvastatin"])
    pgx_rows_colors.append(_pheno_color(g.slco1b1_function))

    pgx_rows.append(["MTHFR C677T", g.mthfr_c677t.title(),
                      g.diplotypes.get("MTHFR", "—"),
                      "Folate/homocysteine metabolism",
                      "Heterozygous: consider methylfolate supplementation; Homozygous: elevated CVD risk"])
    pgx_rows_colors.append(AMBER if g.mthfr_c677t != "normal" else GREEN)

    pgx_rows.append(["MTHFR A1298C", g.mthfr_a1298c.title(),
                      "—",
                      "BH4 synthesis, neurotransmitters",
                      "Compound heterozygous with C677T → significant folate pathway impairment"])
    pgx_rows_colors.append(AMBER if g.mthfr_a1298c != "normal" else GREEN)

    pgx_t = Table(pgx_rows,
                  colWidths=[col_w*0.12, col_w*0.14, col_w*0.11,
                             col_w*0.25, col_w*0.38])
    pts = _base_table_style()
    for i, c in enumerate(pgx_rows_colors, start=1):
        pts.add("TEXTCOLOR", (1, i), (1, i), c)
        pts.add("FONTNAME",  (1, i), (1, i), "Helvetica-Bold")
    pgx_t.setStyle(pts)
    story.append(pgx_t)

    story.append(Paragraph(
        f"<b>Source:</b> {g.source.replace('_', ' ').title()} · "
        f"<b>UGT1A1:</b> {g.ugt1a1_function.title()}",
        S["small"]
    ))
    story.append(PageBreak())

    # ── ─────────────────────────────────────────────────────────────────────
    # PAGE 5 — LABORATORY RESULTS
    # ─────────────────────────────────────────────────────────────────────────

    story += _section_header("Laboratory Results", S)
    labs = request.labs

    if labs:
        lab_sections = [
            ("Liver Function Tests (LFT)", [
                "ast_u_per_l", "alt_u_per_l", "ggt_u_per_l",
                "alp_u_per_l", "albumin_g_per_dl", "bilirubin_mg_per_dl"
            ]),
            ("Kidney Function Tests (KFT)", [
                "creatinine_mg_per_dl", "egfr_ml_per_min",
                "bun_mg_per_dl", "uric_acid_mg_per_dl"
            ]),
            ("Metabolic & Cardiac Panel", [
                "hba1c_pct", "glucose_mg_per_dl", "ldl_mg_per_dl",
                "hdl_mg_per_dl", "triglycerides_mg_per_dl", "hscrp_mg_per_l"
            ]),
        ]

        for section_name, keys in lab_sections:
            story.append(Paragraph(section_name, S["h3"]))
            section_data = [["Test", "Value", "Units", "Reference Range", "Flag"]]
            for key in keys:
                if key not in LAB_RANGES:
                    continue
                lo, hi, unit, display = LAB_RANGES[key]
                val = getattr(labs, key, None)
                flag_str  = _lab_flag(val, lo, hi)
                flag_col  = _lab_flag_color(val, lo, hi)
                section_data.append([
                    display,
                    _fmt(val, decimals=2) if val is not None else "—",
                    unit,
                    f"{lo} – {hi}" if hi < 900 else f"≥ {lo}",
                    flag_str,
                ])
            lab_t = Table(section_data,
                          colWidths=[col_w*0.28, col_w*0.15, col_w*0.12,
                                     col_w*0.25, col_w*0.20])
            lts = _base_table_style()
            for i, key in enumerate(keys, start=1):
                lo, hi, unit, _ = LAB_RANGES.get(key, (0, 999, "", ""))
                val = getattr(labs, key, None)
                fc  = _lab_flag_color(val, lo, hi)
                lts.add("TEXTCOLOR", (4, i), (4, i), fc)
                lts.add("FONTNAME",  (4, i), (4, i), "Helvetica-Bold")
            lab_t.setStyle(lts)
            story.append(lab_t)
            story += [Spacer(1, 3*mm)]

        if labs.lab_report_date:
            story.append(Paragraph(
                f"<b>Lab report date:</b> {labs.lab_report_date}"
                + (f"  ·  <b>Laboratory:</b> {labs.lab_name}" if labs.lab_name else ""),
                S["small"]
            ))
    else:
        story.append(Paragraph(
            "No laboratory values were provided. Organ scores are calculated from "
            "genetic, lifestyle, and regimen data only. Lab values significantly "
            "improve trajectory accuracy — request a full blood panel.",
            S["body_mid"]
        ))

    story.append(PageBreak())

    # ── ─────────────────────────────────────────────────────────────────────
    # PAGE 6 — REGIMEN & DRUG-DRUG INTERACTIONS
    # ─────────────────────────────────────────────────────────────────────────

    story += _section_header("Current Supplement & Medication Regimen", S)

    reg_data = [["#", "Compound", "Dose", "Frequency", "Rx?", "Prescribed By", "Timing"]]
    for i, item in enumerate(request.regimen, 1):
        reg_data.append([
            str(i),
            _title(item.compound_id) + (f"\n({item.brand_name})" if item.brand_name else ""),
            f"{item.dose_mg} mg",
            f"{item.frequency_per_day}× / day",
            "Rx" if item.is_rx else "OTC",
            item.prescribed_by.replace("_", " ").title(),
            ", ".join(item.timing) if item.timing else "Unspecified",
        ])
    reg_t = Table(reg_data, colWidths=[col_w*0.04, col_w*0.22, col_w*0.10,
                                        col_w*0.12, col_w*0.07,
                                        col_w*0.15, col_w*0.30])
    reg_t.setStyle(_base_table_style())
    story.append(reg_t)
    story += [Spacer(1, 5*mm)]

    # DDI Flags
    if response.ddi_flags:
        story += _section_header("Drug-Drug Interaction (DDI) Flags", S)
        story.append(Paragraph(
            "The following interactions were detected by the GNN model. "
            "High-severity interactions require immediate clinical review.",
            S["body_mid"]
        ))
        story += [Spacer(1, 2*mm)]

        ddi_data = [["Severity", "Compound A", "Compound B", "Mechanism", "Recommendation"]]
        for ddi in response.ddi_flags:
            ddi_data.append([
                ddi.risk_level.upper(),
                _title(ddi.compound_a),
                _title(ddi.compound_b),
                ddi.mechanism,
                ddi.recommendation,
            ])
        ddi_t = Table(ddi_data, colWidths=[col_w*0.10, col_w*0.15, col_w*0.15,
                                            col_w*0.28, col_w*0.32])
        ddits = _base_table_style(header_bg=colors.HexColor("#3B1F1F"), header_fg=WHITE)
        for i, ddi in enumerate(response.ddi_flags, start=1):
            c = {"high": RED, "moderate": AMBER, "low": GREEN}.get(ddi.risk_level, MID)
            ddits.add("TEXTCOLOR", (0, i), (0, i), c)
            ddits.add("FONTNAME",  (0, i), (0, i), "Helvetica-Bold")
            if ddi.risk_level == "high":
                ddits.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FEF2F2"))
        ddi_t.setStyle(ddits)
        story.append(ddi_t)
    else:
        story.append(Paragraph("✓  No drug-drug interactions detected in the current regimen.", S["body"]))

    story.append(PageBreak())

    # ── ─────────────────────────────────────────────────────────────────────
    # PAGE 7 — 5-YEAR TRAJECTORY CHART
    # ─────────────────────────────────────────────────────────────────────────

    story += _section_header("5-Year Hepatic Function Trajectory", S)
    story.append(Paragraph(
        "Baseline trajectory (grey) assumes no changes to the current regimen or "
        "lifestyle. Optimised trajectory (green) reflects full adoption of all "
        "clinical recommendations below.",
        S["body_mid"]
    ))
    story += [Spacer(1, 4*mm)]

    if response.trajectory:
        baseline_pts = [(pt.year, pt.liver_index) for pt in response.trajectory]
        optim_pts    = [(pt.year, pt.optimized_liver_index or pt.liver_index)
                        for pt in response.trajectory]

        chart_w, chart_h = 460, 160
        d   = Drawing(chart_w, chart_h + 30)
        lp  = LinePlot()
        lp.x, lp.y = 55, 30
        lp.width, lp.height = chart_w - 70, chart_h - 10

        lp.data        = [baseline_pts, optim_pts]
        lp.joinedLines = 1

        all_vals = [v for _, v in baseline_pts + optim_pts]
        y_min = max(0, int(min(all_vals)) - 5)
        y_max = min(100, int(max(all_vals)) + 8)

        lp.xValueAxis.valueMin  = 0
        lp.xValueAxis.valueMax  = 5
        lp.xValueAxis.valueStep = 1
        lp.yValueAxis.valueMin  = y_min
        lp.yValueAxis.valueMax  = y_max
        lp.yValueAxis.valueStep = 10

        lp.lines[0].strokeColor = LIGHT
        lp.lines[0].strokeWidth = 2
        lp.lines[0].symbol      = makeMarker("FilledCircle")
        lp.lines[0].symbol.fillColor = LIGHT
        lp.lines[0].symbol.size = 5

        lp.lines[1].strokeColor = GREEN
        lp.lines[1].strokeWidth = 2.5
        lp.lines[1].symbol      = makeMarker("FilledDiamond")
        lp.lines[1].symbol.fillColor = GREEN
        lp.lines[1].symbol.size = 5

        d.add(lp)
        d.add(String(60,  12, "Baseline (no changes)", fontSize=9, fillColor=LIGHT))
        d.add(String(250, 12, "Optimised (all recs adopted)", fontSize=9, fillColor=GREEN))
        story.append(d)
        story += [Spacer(1, 3*mm)]

        # Trajectory data table
        traj_data = [["Year", "Baseline Index", "Optimised Index", "Delta"]]
        for pt in response.trajectory:
            opt   = pt.optimized_liver_index or pt.liver_index
            delta = opt - pt.liver_index
            sign  = "+" if delta >= 0 else ""
            traj_data.append([
                f"Year {pt.year}",
                f"{pt.liver_index:.1f}",
                f"{opt:.1f}",
                f"{sign}{delta:.1f}",
            ])
        traj_t = Table(traj_data, colWidths=[col_w*0.2, col_w*0.25,
                                              col_w*0.25, col_w*0.30])
        trts = _base_table_style()
        for i in range(1, len(traj_data)):
            delta_val = (response.trajectory[i-1].optimized_liver_index or
                         response.trajectory[i-1].liver_index) - response.trajectory[i-1].liver_index
            trts.add("TEXTCOLOR", (3, i), (3, i), GREEN if delta_val >= 0 else RED)
            trts.add("FONTNAME",  (3, i), (3, i), "Helvetica-Bold")
        traj_t.setStyle(trts)
        story.append(traj_t)

    story.append(PageBreak())

    # ── ─────────────────────────────────────────────────────────────────────
    # PAGE 8 — COMPOUND LOAD ANALYSIS
    # ─────────────────────────────────────────────────────────────────────────

    story += _section_header("Compound Load Analysis", S)
    story.append(Paragraph(
        "Each compound's contribution to cumulative hepatic stress (load). "
        "Protective compounds reduce overall index. Load is adjusted for "
        "metabolizer phenotype and dose.",
        S["body_mid"]
    ))
    story += [Spacer(1, 3*mm)]

    # Sort: stressors first (descending load), then protective
    harmful    = sorted([c for c in response.contributions if not c.is_protective],
                        key=lambda x: x.load, reverse=True)
    protective = sorted([c for c in response.contributions if c.is_protective],
                        key=lambda x: x.load, reverse=True)
    sorted_contribs = harmful + protective

    contrib_data = [["Compound", "Load Score", "Type", "Mechanism / Reason"]]
    for c in sorted_contribs:
        contrib_data.append([
            c.name,
            f"{c.load:.1f}",
            "Protective" if c.is_protective else "Stressor",
            c.reason,
        ])
    contrib_t = Table(contrib_data,
                      colWidths=[col_w*0.20, col_w*0.12, col_w*0.13, col_w*0.55])
    cts = _base_table_style()
    for i, c in enumerate(sorted_contribs, start=1):
        col = GREEN if c.is_protective else (RED if c.load > 30 else AMBER)
        cts.add("TEXTCOLOR", (1, i), (1, i), col)
        cts.add("FONTNAME",  (1, i), (1, i), "Helvetica-Bold")
        cts.add("TEXTCOLOR", (2, i), (2, i), GREEN if c.is_protective else RED)
    contrib_t.setStyle(cts)
    story.append(contrib_t)

    story.append(PageBreak())

    # ── ─────────────────────────────────────────────────────────────────────
    # PAGE 9+ — CLINICAL RECOMMENDATIONS
    # ─────────────────────────────────────────────────────────────────────────

    story += _section_header(
        f"Clinical Recommendations ({len(response.recommendations)} total)", S
    )
    story.append(Paragraph(
        "Recommendations are ranked by expected impact on the hepatic index and "
        "cross-validated with CPIC/AHA/WHO guidelines. Confidence reflects "
        "GNN model certainty from the training distribution.",
        S["body_mid"]
    ))
    story += [Spacer(1, 3*mm)]

    for i, rec in enumerate(response.recommendations, 1):
        ac    = _action_color(rec.action_type)
        delta = rec.expected_improvement.delta_index_now
        d5yr  = rec.expected_improvement.delta_index_year5
        sign  = "+" if delta >= 0 else ""
        sign5 = "+" if d5yr >= 0 else ""

        block = [
            Table(
                [[f"[{rec.action_type.upper()}]",
                  f"{i}. {rec.title}",
                  f"Confidence: {rec.confidence*100:.0f}%"]],
                colWidths=[col_w*0.14, col_w*0.67, col_w*0.19]
            ),
        ]
        block[0].setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE),
            ("TEXTCOLOR",  (0, 0), (0,  0), ac),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (0,  0), 8.5),
            ("FONTSIZE",   (1, 0), (1,  0), 9.5),
            ("FONTSIZE",   (2, 0), (2,  0), 8),
            ("TEXTCOLOR",  (2, 0), (2,  0), MID),
            ("ALIGN",      (2, 0), (2,  0), "RIGHT"),
            ("PADDING",    (0, 0), (-1, 0), 6),
            ("BOX",        (0, 0), (-1, 0), 0.5, BORDER),
            ("LEFTPADDING",(0, 0), (0,  0), 8),
        ]))

        detail_text = rec.details
        impact_text = (f"<b>Expected impact:</b>  "
                       f"{sign}{delta:.1f} index pts now  ·  "
                       f"{sign5}{d5yr:.1f} pts at 5 years")

        if rec.evidence_refs:
            refs_text = "<b>Evidence:</b>  " + "  ·  ".join(rec.evidence_refs[:4])
        else:
            refs_text = ""

        story.append(KeepTogether(block + [
            Paragraph(detail_text, S["body"]),
            Paragraph(impact_text, S["body_mid"]),
            Paragraph(refs_text, S["small"]) if refs_text else Spacer(1, 0),
            Spacer(1, 4*mm),
        ]))

    story.append(PageBreak())

    # ── ─────────────────────────────────────────────────────────────────────
    # FINAL PAGE — LIFESTYLE SUMMARY + DISCLAIMER
    # ─────────────────────────────────────────────────────────────────────────

    story += _section_header("Lifestyle Risk Factor Summary", S)

    ls_data = [
        ["Factor",              "Value",                   "Benchmark"],
        ["Sleep (avg)",         f"{ls.sleep_hours_avg:.1f} h/night",
                                "7–9 h optimal"],
        ["Sleep quality",       f"{ls.sleep_quality}/10",  "≥7 recommended"],
        ["Chronic stress",      f"{ls.stress_level}/10",   "≤4 low-risk"],
        ["Cognitive load",      f"{ls.cognitive_load}/10", "—"],
        ["Alcohol intake",      f"{ls.alcohol_drinks_per_week} drinks/wk",
                                "≤7 (F), ≤14 (M) low-risk"],
        ["Sugar intake",        f"{ls.sugar_g_per_day} g/day",
                                "<25 g AHA recommendation"],
        ["Exercise",            f"{ls.exercise_mins_per_week} min/wk",
                                "≥150 min moderate (WHO)"],
        ["Resistance training", f"{ls.resistance_training_days} days/wk",
                                "≥2 days/wk"],
        ["Smoking",             ls.smoking_status.title(),  "Never ideal"],
        ["Diet type",           ls.diet_type.replace("_", " ").title(), "—"],
        ["Hydration",           f"{ls.hydration_oz_per_day} oz/day",
                                "~80+ oz/day"],
        ["Sunlight",            f"{ls.sunlight_mins_per_day} min/day",
                                "15–30 min for vitamin D"],
        ["Screen time",         f"{ls.screen_time_hours:.1f} h/day",
                                "<4 h/day"],
        ["Toxin exposure",      f"{ls.environmental_toxin_exposure}/10",
                                "≤3 low-risk"],
    ]
    ls_t = Table(ls_data, colWidths=[col_w*0.28, col_w*0.30, col_w*0.42])

    lst = _base_table_style()
    for i, row in enumerate(ls_data[1:], start=1):
        val_str = row[1]
        cell_color = GREEN
        if "stress" in ls_data[i][0].lower() and ls.stress_level >= 7:         cell_color = RED
        elif "stress" in ls_data[i][0].lower() and ls.stress_level >= 5:       cell_color = AMBER
        elif "alcohol" in ls_data[i][0].lower() and ls.alcohol_drinks_per_week > 14: cell_color = RED
        elif "alcohol" in ls_data[i][0].lower() and ls.alcohol_drinks_per_week > 7:  cell_color = AMBER
        elif "sleep" in ls_data[i][0].lower() and ls.sleep_hours_avg < 6:      cell_color = RED
        elif "sleep" in ls_data[i][0].lower() and ls.sleep_hours_avg < 7:      cell_color = AMBER
        elif "smoking" in ls_data[i][0].lower() and ls.smoking_status == "current": cell_color = RED
        elif "sugar" in ls_data[i][0].lower() and ls.sugar_g_per_day > 50:    cell_color = AMBER
        lst.add("TEXTCOLOR", (1, i), (1, i), cell_color)
    ls_t.setStyle(lst)
    story.append(ls_t)

    # Pathway chains
    if response.compound_gene_chains:
        story += [Spacer(1, 5*mm)]
        story += _section_header("Compound → Gene → Metabolic Pathway Chains", S)
        chain_data = [["Compound", "Gene", "Phenotype", "Multiplier", "Evidence", "Organ Impacts"]]
        for chain in response.compound_gene_chains[:8]:  # top 8
            for gi in chain.gene_interactions[:2]:
                impacts = ", ".join(f"{k}: {v:.0f}" for k, v in chain.organ_impacts.items())
                chain_data.append([
                    chain.display_name,
                    gi.gene,
                    gi.phenotype,
                    f"×{gi.multiplier:.2f}",
                    gi.evidence[:60] + ("…" if len(gi.evidence) > 60 else ""),
                    impacts or "—",
                ])
        chain_t = Table(chain_data,
                        colWidths=[col_w*0.16, col_w*0.10, col_w*0.13,
                                   col_w*0.10, col_w*0.28, col_w*0.23])
        chain_t.setStyle(_base_table_style())
        story.append(chain_t)

    # Footer + Disclaimer
    story += [Spacer(1, 10*mm), HRFlowable(width="100%", thickness=0.5, color=BORDER)]
    story += [Spacer(1, 3*mm)]

    story.append(Paragraph(
        f"Report generated by Eirion Precision Longevity Platform (v0.3)  ·  "
        f"Report ID: {report_id}  ·  Generated: {generated_str}  ·  "
        f"Engine: GNN {response.gnn_version} / Gemini-enriched recommendations",
        S["small"]
    ))
    story += [Spacer(1, 2*mm)]
    story.append(Paragraph(
        "MEDICAL DISCLAIMER: This report is generated by an experimental AI platform "
        "(Eirion Phase 0 Prototype) and is intended for informational and research "
        "purposes only. It does NOT constitute medical advice, diagnosis, or treatment. "
        "Pharmacogenomic predictions are based on CPIC guidelines and are probabilistic "
        "estimates — individual responses may vary significantly. "
        "NEVER alter any prescription medication based solely on this report. "
        "Always consult a licensed physician, pharmacist, or clinical geneticist before "
        "making changes to your medication or supplement regimen. "
        "This platform is not FDA-cleared and has not been validated as a Software as a "
        "Medical Device (SaMD). Use at your own discretion.",
        S["disclaimer"]
    ))

    doc.build(story)
    return buffer.getvalue()

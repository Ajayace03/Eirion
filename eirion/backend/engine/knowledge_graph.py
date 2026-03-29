"""
EIRION Knowledge Graph
======================
Static compound → gene → pathway → organ heterogeneous graph.
Encodes pharmacogenomics relationships from PharmGKB, CPIC, DrugBank, Reactome.

This is the authoritative source for mechanistic explanations in the engine.
"""

from typing import Dict, List, Optional, Literal

# ------------------------------------------------------------------
# 1. PATHWAY DEFINITIONS
# Each pathway has: organ targets, reversibility, and clinical notes
# ------------------------------------------------------------------

PATHWAY_GRAPH = {
    # Phase I Oxidation (hepatic)
    "phase_i_oxidation": {
        "organs": ["liver"],
        "severity_weight": 1.0,
        "reversibility": 0.85,
        "description": "CYP450-mediated oxidative metabolism in hepatocytes",
        "genes": ["CYP2D6", "CYP3A4", "CYP2C19", "CYP2C9", "CYP1A2"],
    },
    # Phase II Conjugation (hepatic)
    "phase_ii_conjugation": {
        "organs": ["liver"],
        "severity_weight": 0.6,
        "reversibility": 0.90,
        "description": "UGT/GST-mediated conjugation for biliary excretion",
        "genes": ["UGT1A1"],
    },
    # Hepatic Lipogenesis
    "hepatic_lipogenesis": {
        "organs": ["liver", "metabolic"],
        "severity_weight": 0.9,
        "reversibility": 0.75,
        "description": "De novo lipogenesis pathway — excess substrate → hepatic fat accumulation",
        "genes": [],
    },
    # Oxidative Stress (hepatic)
    "hepatic_oxidative_stress": {
        "organs": ["liver"],
        "severity_weight": 1.1,
        "reversibility": 0.80,
        "description": "ROS-mediated hepatocellular injury from CYP450 metabolite overflow",
        "genes": ["CYP2D6", "CYP3A4"],
    },
    # Gut-Liver Axis (microbiome → portal circulation)
    "gut_liver_axis": {
        "organs": ["liver", "metabolic"],
        "severity_weight": 0.7,
        "reversibility": 0.90,
        "description": "Short-chain fatty acid production and intestinal permeability → hepatic inflammation",
        "genes": [],
    },
    # Statin myopathy pathway
    "statin_myopathy": {
        "organs": ["liver", "metabolic"],
        "severity_weight": 0.8,
        "reversibility": 0.95,
        "description": "SLCO1B1-mediated hepatic statin uptake failure → systemic accumulation → myopathy",
        "genes": ["SLCO1B1"],
    },
    # HPA Axis (cortisol / stress)
    "hpa_cortisol": {
        "organs": ["metabolic", "cardiovascular"],
        "severity_weight": 0.5,
        "reversibility": 0.85,
        "description": "Hypothalamic-pituitary-adrenal axis — chronic stress → cortisol → insulin resistance",
        "genes": [],
    },
    # Insulin Signaling
    "insulin_signaling": {
        "organs": ["metabolic", "cardiovascular"],
        "severity_weight": 0.85,
        "reversibility": 0.80,
        "description": "Insulin receptor → PI3K/Akt pathway — impaired → glucose dysregulation",
        "genes": [],
    },
    # Renal Clearance (OCT2/MATE1)
    "renal_clearance": {
        "organs": ["kidney"],
        "severity_weight": 0.75,
        "reversibility": 0.70,
        "description": "OCT2-mediated tubular secretion — impaired eGFR reduces drug clearance",
        "genes": [],
    },
    # Cardiovascular (LDL/Cholesterol)
    "ldl_pathway": {
        "organs": ["cardiovascular"],
        "severity_weight": 0.9,
        "reversibility": 0.75,
        "description": "LDL oxidation → foam cell formation → atherosclerotic plaque progression",
        "genes": ["SLCO1B1"],
    },
    # Folate Cycle
    "folate_cycle": {
        "organs": ["metabolic", "cardiovascular"],
        "severity_weight": 0.4,
        "reversibility": 0.95,
        "description": "MTHFR-mediated folate methylation — impaired → elevated homocysteine",
        "genes": ["MTHFR"],
    },
    # Dopamine / Serotonin Reuptake
    "monoamine_reuptake": {
        "organs": ["liver"],
        "severity_weight": 0.5,
        "reversibility": 0.90,
        "description": "CYP2D6-mediated SSRI/SNRI metabolism — accumulation in poor metabolizers",
        "genes": ["CYP2D6", "CYP2C19"],
    },
    # Anti-inflammatory pathway
    "anti_inflammatory": {
        "organs": ["cardiovascular", "liver"],
        "severity_weight": -0.5,  # protective
        "reversibility": 1.0,
        "description": "Omega-3 EPA/DHA → resolvins/protectins — reduces hepatic NF-kB signaling",
        "genes": [],
    },
    # Circadian hepatic clearance
    "circadian_clearance": {
        "organs": ["liver"],
        "severity_weight": 0.3,
        "reversibility": 0.95,
        "description": "Time-of-day CYP450 expression — incorrect dosing timing elevates peak concentrations",
        "genes": ["CYP1A2", "CYP3A4"],
    },
}


# ------------------------------------------------------------------
# 2. COMPOUND → GENE → PATHWAY MAP
# The core of the knowledge graph
# ------------------------------------------------------------------

COMPOUND_INTERACTIONS = {
    "ashwagandha": {
        "display_name": "Ashwagandha (Withania somnifera)",
        "smiles": "CC1(C)CCC2(C(=O)O)CC(=O)C=C2C1",
        "category": "adaptogen",
        "gene_interactions": [
            {
                "gene": "CYP2D6",
                "interaction_type": "substrate",
                "strength": "significant",
                "multiplier_poor": 1.5,
                "multiplier_intermediate": 1.2,
                "multiplier_ultra_rapid": 0.8,
                "evidence": "PharmGKB:PA166182476 — CYP2D6 substrate confirmed",
            },
            {
                "gene": "CYP3A4",
                "interaction_type": "weak_inhibitor",
                "strength": "minor",
                "multiplier_poor": 1.1,
                "evidence": "In vitro data — minor CYP3A4 inhibition at high doses",
            },
        ],
        "pathway_activations": [
            {"pathway": "phase_i_oxidation", "delta": 1.2},
            {"pathway": "hepatic_oxidative_stress", "delta": 0.8},
            {"pathway": "hpa_cortisol", "delta": -0.6},  # reduces cortisol (protective)
        ],
        "primary_organ_impact": "liver",
        "risk_tags": ["CYP2D6_substrate", "herb_hepatotoxic_reports"],
    },
    "metformin": {
        "display_name": "Metformin",
        "smiles": "CN(C)C(=N)NC(=N)N",
        "category": "medication",
        "gene_interactions": [
            {
                "gene": "OCT2",
                "interaction_type": "substrate",
                "strength": "primary",
                "multiplier_poor": 1.0,
                "evidence": "Renal OCT2 (SLC22A2) — not hepatic CYP. Safe if eGFR >30.",
            },
        ],
        "pathway_activations": [
            {"pathway": "renal_clearance", "delta": 0.4},
            {"pathway": "insulin_signaling", "delta": -0.6},  # beneficial
            {"pathway": "hepatic_lipogenesis", "delta": -0.4},  # reduces lipogenesis
        ],
        "primary_organ_impact": "metabolic",
        "risk_tags": [],
        "contraindication_if": {"egfr_below": 30},
    },
    "omega3": {
        "display_name": "Omega-3 Fish Oil",
        "smiles": "CCCCCC=CCC=CCCCCCCCC(=O)O",
        "category": "supplement",
        "gene_interactions": [],
        "pathway_activations": [
            {"pathway": "anti_inflammatory", "delta": -1.0},  # strongly protective
            {"pathway": "ldl_pathway", "delta": -0.5},
            {"pathway": "hepatic_lipogenesis", "delta": -0.3},
        ],
        "primary_organ_impact": "cardiovascular",
        "risk_tags": [],
        "is_protective": True,
    },
    "vitamin_d": {
        "display_name": "Vitamin D3 (Cholecalciferol)",
        "smiles": "C[C@H](CCCC(C)C)C1CC[C@@H]2[C@@]1(CCCC2=CC=C3C[C@@H](O)CC[C@]3(C)O)C",
        "category": "supplement",
        "gene_interactions": [
            {
                "gene": "CYP3A4",
                "interaction_type": "substrate",
                "strength": "primary",
                "multiplier_poor": 1.0,  # CYP3A4 poor → slower vitamin D activation
                "evidence": "CYP3A4 activates 25(OH)D3 → calcitriol. Normal metabolizer expected.",
            },
        ],
        "pathway_activations": [
            {"pathway": "phase_i_oxidation", "delta": 0.4},
        ],
        "primary_organ_impact": "liver",
        "risk_tags": ["fat_soluble"],
        "dose_note": "High-dose (>4000 IU/day) can accumulate — fat-soluble toxicity risk",
    },
    "atorvastatin": {
        "display_name": "Atorvastatin (Lipitor)",
        "smiles": "CC(C)c1c(C(=O)Nc2ccccc2F)c(-c2ccccc2)c(-c2ccc(F)cc2)n1CC[C@@H](O)C[C@@H](O)CC(=O)O",
        "category": "medication",
        "gene_interactions": [
            {
                "gene": "CYP3A4",
                "interaction_type": "substrate",
                "strength": "primary",
                "multiplier_poor": 1.0,
                "evidence": "Primary CYP3A4 substrate — CYP3A4 inducers reduce efficacy",
            },
            {
                "gene": "SLCO1B1",
                "interaction_type": "substrate",
                "strength": "significant",
                "multiplier_poor": 1.4,
                "evidence": "CPIC guideline — SLCO1B1 reduced function significantly increases plasma AUC",
            },
        ],
        "pathway_activations": [
            {"pathway": "phase_i_oxidation", "delta": 0.6},
            {"pathway": "statin_myopathy", "delta": 1.2},
            {"pathway": "ldl_pathway", "delta": -1.0},  # beneficial
        ],
        "primary_organ_impact": "liver",
        "risk_tags": ["SLCO1B1_substrate"],
    },
    "rosuvastatin": {
        "display_name": "Rosuvastatin (Crestor)",
        "smiles": "CC(C)(C)c1ccc(N2CC(CC(O)CC(O)CC(=O)O)C2=O)cc1",
        "category": "medication",
        "gene_interactions": [
            {
                "gene": "SLCO1B1",
                "interaction_type": "substrate",
                "strength": "moderate",
                "multiplier_poor": 1.25,
                "evidence": "SLCO1B1 variant — less impact than simvastatin, preferred in reduced function",
            },
            {
                "gene": "CYP2C9",
                "interaction_type": "weak_substrate",
                "strength": "minor",
                "multiplier_poor": 1.1,
                "evidence": "Minor CYP2C9 contribution to metabolism",
            },
        ],
        "pathway_activations": [
            {"pathway": "statin_myopathy", "delta": 0.6},
            {"pathway": "ldl_pathway", "delta": -1.1},  # strong beneficial
        ],
        "primary_organ_impact": "cardiovascular",
        "risk_tags": ["SLCO1B1_substrate"],
    },
    "sertraline": {
        "display_name": "Sertraline (Zoloft)",
        "smiles": "CNC1CC2=CC(Cl)=CC=C2C1C1=CC=C(Cl)C=C1Cl",
        "category": "medication",
        "gene_interactions": [
            {
                "gene": "CYP2D6",
                "interaction_type": "substrate",
                "strength": "primary",
                "multiplier_poor": 1.6,
                "multiplier_intermediate": 1.3,
                "evidence": "CPIC Level A — CYP2D6 primary metabolizer. Poor → 2-3x plasma exposure",
            },
            {
                "gene": "CYP2C19",
                "interaction_type": "substrate",
                "strength": "secondary",
                "multiplier_poor": 1.3,
                "evidence": "Secondary CYP2C19 pathway — relevant in CYP2D6 poor metabolizers",
            },
        ],
        "pathway_activations": [
            {"pathway": "phase_i_oxidation", "delta": 1.0},
            {"pathway": "monoamine_reuptake", "delta": 1.4},
        ],
        "primary_organ_impact": "liver",
        "risk_tags": ["CYP2D6_substrate", "CYP2C19_substrate"],
    },
    "escitalopram": {
        "display_name": "Escitalopram (Lexapro)",
        "smiles": "CNCCC1(OCc2cc(C#N)ccc21)c1ccc(F)cc1",
        "category": "medication",
        "gene_interactions": [
            {
                "gene": "CYP2C19",
                "interaction_type": "substrate",
                "strength": "primary",
                "multiplier_poor": 1.8,
                "evidence": "CPIC Level A — CYP2C19 primary. Poor metabolizers → dose reduction required",
            },
            {
                "gene": "CYP2D6",
                "interaction_type": "substrate",
                "strength": "secondary",
                "multiplier_poor": 1.2,
                "evidence": "Secondary CYP2D6 pathway",
            },
        ],
        "pathway_activations": [
            {"pathway": "phase_i_oxidation", "delta": 0.8},
            {"pathway": "monoamine_reuptake", "delta": 1.2},
        ],
        "primary_organ_impact": "liver",
        "risk_tags": ["CYP2D6_substrate", "CYP2C19_substrate"],
    },
    "berberine": {
        "display_name": "Berberine",
        "smiles": "COc1ccc2cc3[n+](cc2c1OC)CCc1cc2c(cc1-3)OCO2",
        "category": "supplement",
        "gene_interactions": [
            {
                "gene": "CYP2D6",
                "interaction_type": "inhibitor",
                "strength": "moderate",
                "multiplier_poor": 1.3,
                "evidence": "CYP2D6 inhibitor — reduces clearance of co-administered substrates",
            },
            {
                "gene": "CYP3A4",
                "interaction_type": "inhibitor",
                "strength": "moderate",
                "multiplier_poor": 1.2,
                "evidence": "CYP3A4 inhibition reported in clinical studies",
            },
        ],
        "pathway_activations": [
            {"pathway": "phase_i_oxidation", "delta": 0.9},
            {"pathway": "insulin_signaling", "delta": -0.5},  # beneficial
        ],
        "primary_organ_impact": "liver",
        "risk_tags": ["CYP2D6_substrate"],
    },
    "nac": {
        "display_name": "NAC (N-Acetyl Cysteine)",
        "smiles": "CC(=O)N[C@@H](CS)C(=O)O",
        "category": "supplement",
        "gene_interactions": [],
        "pathway_activations": [
            {"pathway": "hepatic_oxidative_stress", "delta": -1.0},  # strongly protective
            {"pathway": "phase_ii_conjugation", "delta": -0.5},  # replenishes glutathione
        ],
        "primary_organ_impact": "liver",
        "risk_tags": [],
        "is_protective": True,
    },
    "magnesium": {
        "display_name": "Magnesium Glycinate",
        "smiles": "OC(=O)CN",
        "category": "supplement",
        "gene_interactions": [],
        "pathway_activations": [
            {"pathway": "hpa_cortisol", "delta": -0.3},
            {"pathway": "insulin_signaling", "delta": -0.2},
        ],
        "primary_organ_impact": "metabolic",
        "risk_tags": [],
        "is_protective": True,
    },
    "curcumin": {
        "display_name": "Curcumin / Turmeric",
        "smiles": "COc1cc(/C=C/C(=O)CC(=O)/C=C/c2ccc(O)c(OC)c2)ccc1O",
        "category": "supplement",
        "gene_interactions": [
            {
                "gene": "CYP3A4",
                "interaction_type": "inhibitor",
                "strength": "moderate",
                "multiplier_poor": 1.15,
                "evidence": "CYP3A4 inhibition at high doses — relevant with statin co-administration",
            },
        ],
        "pathway_activations": [
            {"pathway": "hepatic_oxidative_stress", "delta": -0.5},
            {"pathway": "anti_inflammatory", "delta": -0.4},
            {"pathway": "phase_i_oxidation", "delta": 0.3},
        ],
        "primary_organ_impact": "liver",
        "risk_tags": [],
    },
    "coq10": {
        "display_name": "CoQ10 (Ubiquinol)",
        "smiles": "COC1=C(OC)C(=O)C(CC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)CCC=C(C)C)=C(C)C1=O",
        "category": "supplement",
        "gene_interactions": [
            {
                "gene": "CYP3A4",
                "interaction_type": "substrate",
                "strength": "minor",
                "multiplier_poor": 1.0,
                "evidence": "Minor CYP3A4 contribution — generally well tolerated",
            },
        ],
        "pathway_activations": [
            {"pathway": "hepatic_oxidative_stress", "delta": -0.4},
            {"pathway": "statin_myopathy", "delta": -0.6},  # reduces statin myopathy risk
        ],
        "primary_organ_impact": "cardiovascular",
        "risk_tags": [],
        "is_protective": True,
    },
    "quercetin": {
        "display_name": "Quercetin",
        "smiles": "O=c1c(OC2OC(CO)C(O)C(O)C2O)c(-c2ccc(O)c(O)c2)oc2cc(O)cc(O)c12",
        "category": "supplement",
        "gene_interactions": [
            {
                "gene": "CYP3A4",
                "interaction_type": "inhibitor",
                "strength": "moderate",
                "multiplier_poor": 1.2,
                "evidence": "CYP3A4 inhibitor — drug interactions possible with warfarin, cyclosporine",
            },
        ],
        "pathway_activations": [
            {"pathway": "anti_inflammatory", "delta": -0.4},
            {"pathway": "hepatic_oxidative_stress", "delta": -0.3},
            {"pathway": "phase_i_oxidation", "delta": 0.3},
        ],
        "primary_organ_impact": "liver",
        "risk_tags": [],
    },
    "zinc": {
        "display_name": "Zinc",
        "smiles": "[Zn+2]",
        "category": "supplement",
        "gene_interactions": [],
        "pathway_activations": [
            {"pathway": "hepatic_oxidative_stress", "delta": -0.2},
            {"pathway": "gut_liver_axis", "delta": -0.2},
        ],
        "primary_organ_impact": "metabolic",
        "risk_tags": [],
        "is_protective": True,
    },
}


# ------------------------------------------------------------------
# 3. CONDITION → ORGAN BASELINE PENALTIES
# ------------------------------------------------------------------

CONDITION_ORGAN_PENALTIES = {
    "prediabetes": {
        "organs": {"liver": 3.0, "metabolic": 5.0, "cardiovascular": 2.0},
        "pathway_activations": ["insulin_signaling", "hepatic_lipogenesis"],
        "severity_multiplier": {"mild": 1.0, "moderate": 1.5, "severe": 2.0},
    },
    "type2_diabetes": {
        "organs": {"liver": 5.0, "metabolic": 8.0, "cardiovascular": 4.0, "kidney": 3.0},
        "pathway_activations": ["insulin_signaling", "hepatic_lipogenesis", "renal_clearance"],
        "severity_multiplier": {"mild": 1.0, "moderate": 1.5, "severe": 2.5},
    },
    "nafld": {
        "organs": {"liver": 10.0, "metabolic": 5.0},
        "pathway_activations": ["hepatic_lipogenesis", "hepatic_oxidative_stress", "gut_liver_axis"],
        "severity_multiplier": {"mild": 1.0, "moderate": 2.0, "severe": 3.0},
    },
    "fatty_liver": {
        "organs": {"liver": 8.0, "metabolic": 3.0},
        "pathway_activations": ["hepatic_lipogenesis", "gut_liver_axis"],
        "severity_multiplier": {"mild": 1.0, "moderate": 1.8, "severe": 2.5},
    },
    "metabolic_syndrome": {
        "organs": {"liver": 4.0, "metabolic": 6.0, "cardiovascular": 4.0},
        "pathway_activations": ["insulin_signaling", "hepatic_lipogenesis", "hpa_cortisol"],
        "severity_multiplier": {"mild": 1.0, "moderate": 1.5, "severe": 2.0},
    },
    "hypertension": {
        "organs": {"cardiovascular": 6.0, "kidney": 3.0},
        "pathway_activations": ["ldl_pathway"],
        "severity_multiplier": {"mild": 1.0, "moderate": 1.5, "severe": 2.5},
    },
    "hyperlipidemia": {
        "organs": {"cardiovascular": 7.0, "liver": 2.0},
        "pathway_activations": ["ldl_pathway"],
        "severity_multiplier": {"mild": 1.0, "moderate": 1.8, "severe": 2.5},
    },
    "cardiovascular_risk": {
        "organs": {"cardiovascular": 5.0},
        "pathway_activations": ["ldl_pathway"],
        "severity_multiplier": {"mild": 1.0, "moderate": 1.5, "severe": 2.0},
    },
    "kidney_disease": {
        "organs": {"kidney": 10.0, "liver": 2.0},
        "pathway_activations": ["renal_clearance"],
        "severity_multiplier": {"mild": 1.0, "moderate": 2.0, "severe": 3.5},
    },
    "anxiety": {
        "organs": {"metabolic": 2.0, "cardiovascular": 1.5},
        "pathway_activations": ["hpa_cortisol"],
        "severity_multiplier": {"mild": 1.0, "moderate": 1.3, "severe": 1.8},
    },
    "depression": {
        "organs": {"metabolic": 2.0, "liver": 1.0},
        "pathway_activations": ["hpa_cortisol", "monoamine_reuptake"],
        "severity_multiplier": {"mild": 1.0, "moderate": 1.3, "severe": 1.8},
    },
    "sleep_disorder": {
        "organs": {"liver": 2.0, "metabolic": 2.0},
        "pathway_activations": ["circadian_clearance"],
        "severity_multiplier": {"mild": 1.0, "moderate": 1.4, "severe": 2.0},
    },
    "autoimmune": {
        "organs": {"liver": 4.0, "metabolic": 2.0},
        "pathway_activations": ["anti_inflammatory"],
        "severity_multiplier": {"mild": 1.0, "moderate": 1.5, "severe": 2.5},
    },
    "gout": {
        "organs": {"kidney": 5.0, "metabolic": 2.0},
        "pathway_activations": ["renal_clearance"],
        "severity_multiplier": {"mild": 1.0, "moderate": 1.5, "severe": 2.0},
    },
}


# ------------------------------------------------------------------
# 4. DRUG-DRUG INTERACTION PAIRS
# ------------------------------------------------------------------

DDI_PAIRS = [
    {
        "compound_a": "berberine",
        "compound_b": "metformin",
        "interaction_type": "pharmacodynamic",
        "risk_level": "moderate",
        "mechanism": "Both lower blood glucose — additive hypoglycaemia risk",
        "recommendation": "Monitor blood glucose closely if co-administering",
        "evidence": "PMID:23132955",
    },
    {
        "compound_a": "berberine",
        "compound_b": "sertraline",
        "interaction_type": "pharmacokinetic",
        "risk_level": "high",
        "mechanism": "Berberine inhibits CYP2D6 → reduces sertraline clearance → accumulation",
        "recommendation": "Avoid co-administration or reduce sertraline dose by 30-50%",
        "evidence": "PharmGKB:PA166182476",
    },
    {
        "compound_a": "curcumin",
        "compound_b": "atorvastatin",
        "interaction_type": "pharmacokinetic",
        "risk_level": "moderate",
        "mechanism": "Curcumin CYP3A4 inhibition → atorvastatin AUC increases → myopathy risk",
        "recommendation": "Monitor for muscle pain/weakness, consider dose reduction",
        "evidence": "PMID:22367289",
    },
    {
        "compound_a": "quercetin",
        "compound_b": "rosuvastatin",
        "interaction_type": "pharmacokinetic",
        "risk_level": "moderate",
        "mechanism": "Quercetin SLCO1B1 and CYP3A4 inhibition → statin accumulation",
        "recommendation": "Space doses by 4+ hours, use lowest effective statin dose",
        "evidence": "PMID:25586392",
    },
    {
        "compound_a": "ashwagandha",
        "compound_b": "sertraline",
        "interaction_type": "pharmacokinetic",
        "risk_level": "moderate",
        "mechanism": "Both CYP2D6 substrates — additive accumulation in poor metabolizers",
        "recommendation": "Significant risk in CYP2D6 poor metabolizers — consider avoidance",
        "evidence": "PharmGKB inferred — clinical monitoring required",
    },
]


# ------------------------------------------------------------------
# 5. GENE MULTIPLIER LOOKUP
# Returns the dose multiplier for a compound based on patient genetics
# ------------------------------------------------------------------

def get_gene_multiplier(interaction: dict, genetics: dict) -> float:
    """
    Given a gene interaction spec and patient genetics dict,
    returns the pharmacokinetic load multiplier.
    """
    gene = interaction.get("gene", "")
    interaction_type = interaction.get("interaction_type", "")

    # Map gene name → patient phenotype field
    gene_field_map = {
        "CYP2D6": "cyp2d6_metabolizer",
        "CYP2C19": "cyp2c19_metabolizer",
        "CYP3A4": "cyp3a4_metabolizer",
        "CYP2C9": "cyp2c9_metabolizer",
        "CYP1A2": "cyp1a2_metabolizer",
        "SLCO1B1": "slco1b1_function",
        "UGT1A1": "ugt1a1_function",
    }

    field = gene_field_map.get(gene)
    if not field:
        return 1.0

    phenotype = genetics.get(field, "unknown")

    if phenotype == "unknown":
        return 1.0  # Use population average

    if interaction_type in ("substrate", "primary_substrate"):
        multipliers = {
            "poor": interaction.get("multiplier_poor", 1.0),
            "intermediate": interaction.get("multiplier_intermediate", 1.1),
            "normal": 1.0,
            "ultra_rapid": interaction.get("multiplier_ultra_rapid", 0.9),
            # SLCO1B1-specific
            "reduced": interaction.get("multiplier_poor", 1.25),
        }
        return multipliers.get(phenotype, 1.0)

    elif interaction_type in ("inhibitor", "weak_inhibitor"):
        # Inhibitor compounds: poor metabolizer means slower inhibitor clearance → stronger inhibition effect
        if phenotype == "poor":
            return interaction.get("multiplier_poor", 1.1)
        return 1.0

    return 1.0


# ------------------------------------------------------------------
# 6. PATHWAY CHAIN BUILDER
# Returns a human-readable chain for a compound's mechanism
# ------------------------------------------------------------------

def build_pathway_chain(compound_id: str, genetics: dict) -> Optional[List[str]]:
    """
    Returns the mechanistic explanation chain:
    Compound → Gene (metabolizer status) → Pathway → Organ → Effect
    """
    compound = COMPOUND_INTERACTIONS.get(compound_id)
    if not compound:
        return None

    chains = []
    for gene_int in compound.get("gene_interactions", []):
        gene = gene_int["gene"]
        gene_field_map = {
            "CYP2D6": "cyp2d6_metabolizer",
            "CYP2C19": "cyp2c19_metabolizer",
            "CYP3A4": "cyp3a4_metabolizer",
            "CYP2C9": "cyp2c9_metabolizer",
            "CYP1A2": "cyp1a2_metabolizer",
            "SLCO1B1": "slco1b1_function",
        }
        field = gene_field_map.get(gene, "")
        phenotype = genetics.get(field, "unknown") if field else "unknown"

        chain = f"{compound['display_name']} → {gene} [{phenotype.upper() if phenotype != 'unknown' else 'Normal'}]"
        chains.append(chain)

    for pa in compound.get("pathway_activations", []):
        pathway = PATHWAY_GRAPH.get(pa["pathway"], {})
        organs = pathway.get("organs", [])
        if organs:
            delta = pa["delta"]
            direction = "↑ activated" if delta > 0 else "↓ reduced"
            chains.append(f"→ {pa['pathway'].replace('_', ' ').title()} [{direction}] → {'&'.join(organs).title()}")

    return chains


def detect_ddis(regimen: List[dict]) -> List[dict]:
    """
    Checks active regimen for known drug-drug interactions.
    Returns list of DDI flags.
    """
    compound_ids = {item.get("compound_id") for item in regimen}
    flags = []
    for ddi in DDI_PAIRS:
        if ddi["compound_a"] in compound_ids and ddi["compound_b"] in compound_ids:
            flags.append(ddi)
    return flags

"""
Multi-Organ Expansion — Brain & Heart
========================================
STATUS: PLANNED — NOT IMPLEMENTED

Current:
    4 organs: liver, kidney, cardiovascular, metabolic
    Implemented in: scorer.py, projector.py, OrganScorecard.tsx

Planned additions:

Brain / CNS:
    - Blood-brain barrier (BBB) permeability score per compound (LogBB)
    - P-glycoprotein efflux (ABCB1 gene phenotype) impact on CNS exposure
    - CYP2B6 brain isoform — important for psychoactive supplement clearance
    - Neurotoxicity endpoints from DMPNN (see dmpnn_toxicity.py)
    - Cognitive decline projection: data from UK Biobank neuroimaging cohort

Heart — extended cardiac:
    - hERG K+ channel IC50 (from ChEMBL hERG assay) — QTc prolongation risk
    - CredibleMeds CombinedRisk drug list integration
    - Cardiac output reduction at high polypharmacy load
    - LVEF trajectory prediction

Bone:
    - Calcium antagonism from high-dose supplements
    - Vitamin D3 → CYP24A1 feedback loop → osteoporosis risk long-term

Gut Microbiome:
    - Dysbiosis score from antibiotic-class compounds + proton pump inhibitors
    - Impact on systemic inflammation → all organ loads

Integration:
    [ ] Extend OrganScore.organ Literal to include "brain" | "heart"
    [ ] Add BBB permeability field to CompoundGeneChain
    [ ] Add organ_params entries in projector.py for brain + heart
    [ ] Add brain/heart output heads to EirionHGT / GATv2
    [ ] New organ cards in OrganScorecard.tsx
"""

class MultiOrganBrainHeart:
    def __init__(self, *_a, **_kw):
        raise NotImplementedError(
            "MultiOrganBrainHeart is a planned expansion. "
            "See engine/planned/multi_organ_expansion.py."
        )

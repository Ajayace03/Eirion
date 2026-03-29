"""
RL Regimen Optimizer — SAC / PPO
-----------------------------------
PersonalizedRegimenEnv (Gymnasium) + Soft Actor-Critic agent.

State space (~200-dim):
    - Current organ scores (4 floats, normalized)
    - Regimen one-hot: (n_compounds × n_dose_tiers)
    - Polypharmacy load (1 float)
    - DDI severity mask per compound pair
    - Labs deltas

Action space:
    Multi-binary discrete:
        add_compound(id)       — add supplement
        remove_compound(id)    — remove supplement
        change_dose(id, tier)  — low | medium | high

Reward:
    r = w_organ × Σ(score_t+1 - score_t) − w_poly × poly_penalty − w_ddi × ddi_score

Algorithm: SAC (stable-baselines3) for discrete action
Fallback:  deterministic greedy policy when sb3 unavailable.

Usage:
    from engine.planned.rl_regimen_optimizer import (
        PersonalizedRegimenEnv, RLRegimenOptimizer, load_rl_optimizer, greedy_optimize
    )
    optimizer = load_rl_optimizer("weights/sac_regimen.zip")
    actions   = optimizer.recommend(request, organ_scores, top_k=5)
    # → [{"action": "remove", "compound": "ashwagandha", "reason": ..., "gain": 3.2}, ...]
"""

import logging
import os
import copy
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Dependency guards ─────────────────────────────────────────────────────────
try:
    import gymnasium as gym
    from gymnasium import spaces
    _GYM = True
except ImportError:
    _GYM = False
    logger.warning("[RL] gymnasium not available. Install: pip install gymnasium")

try:
    from stable_baselines3 import SAC
    _SB3 = True
except ImportError:
    _SB3 = False
    logger.warning("[RL] stable-baselines3 not available. Install: pip install stable-baselines3")

# ── Compound catalogue (top 50 supplements — extended from scorer.py) ─────────
COMPOUND_CATALOGUE = [
    "vitamin_d3", "omega3", "magnesium", "zinc", "nac", "coq10",
    "ashwagandha", "rhodiola", "berberine", "metformin", "atorvastatin",
    "vitamin_c", "vitamin_b12", "folate", "iron", "calcium", "selenium",
    "alpha_lipoic_acid", "resveratrol", "curcumin", "quercetin", "lions_mane",
    "creatine", "taurine", "l_theanine", "melatonin", "probiotics",
    "fiber_supplement", "glucosamine", "collagen_peptides",
]
N_COMPOUNDS = len(COMPOUND_CATALOGUE)
DOSE_TIERS  = ["low", "medium", "high"]
N_TIERS     = len(DOSE_TIERS)

DOSE_MG = {"low": 0.5, "medium": 1.0, "high": 2.0}  # multipliers on normal dose

ORGANS = ["liver", "kidney", "cardiovascular", "metabolic"]
N_ORGANS = len(ORGANS)

OBS_DIM = (
    N_ORGANS           # organ scores
    + N_COMPOUNDS      # current regimen bitmask
    + N_COMPOUNDS      # current dose tier (0 = absent, 1/2/3 = tier)
    + 1                # polypharmacy score
    + N_COMPOUNDS      # DDI severity sum per compound
)

# Action space:
#   0..N_COMPOUNDS-1        → add compound (dose=medium)
#   N_COMPOUNDS..2N-1       → remove compound
#   2N..2N+N*N_TIERS-1     → change dose tier
N_ADD    = N_COMPOUNDS
N_REMOVE = N_COMPOUNDS
N_DOSE   = N_COMPOUNDS * N_TIERS
N_ACTIONS = N_ADD + N_REMOVE + N_DOSE


# ── Gymnasium Environment ────────────────────────────────────────────────────

if _GYM:

    class PersonalizedRegimenEnv(gym.Env):
        """
        Gymnasium environment simulating personalized supplement management.
        Uses the Eirion scoring engine as the transition model.
        """
        metadata = {"render_modes": []}

        def __init__(self, base_request=None):
            super().__init__()
            self.base_request = base_request
            self.request = copy.deepcopy(base_request) if base_request else None

            self.observation_space = spaces.Box(
                low=0.0, high=1.0, shape=(OBS_DIM,), dtype=np.float32
            )
            self.action_space = spaces.Discrete(N_ACTIONS)

            self._step_count = 0
            self._max_steps  = 20
            self._prev_scores: Dict[str, float] = {o: 70.0 for o in ORGANS}
            self._current_regimen: Dict[str, str] = {}   # compound_id → dose_tier

        def reset(self, seed=None, options=None):
            super().reset(seed=seed)
            self.request = copy.deepcopy(self.base_request)
            self._step_count = 0
            if self.request:
                self._current_regimen = {
                    item.compound_id: "medium" for item in self.request.regimen
                }
            else:
                self._current_regimen = {}
            self._prev_scores = {o: 70.0 for o in ORGANS}
            return self._obs(), {}

        def step(self, action: int):
            self._step_count += 1
            reward = self._apply_action(action)
            obs    = self._obs()
            done   = self._step_count >= self._max_steps
            return obs, reward, done, False, {}

        def _apply_action(self, action: int) -> float:
            """Apply action, compute reward from organ score delta."""
            cid_idx   = action % N_COMPOUNDS
            cid       = COMPOUND_CATALOGUE[cid_idx]
            prev_poly = len(self._current_regimen)

            if action < N_ADD:
                # Add compound at medium dose
                if cid not in self._current_regimen and prev_poly < 12:
                    self._current_regimen[cid] = "medium"
            elif action < N_ADD + N_REMOVE:
                # Remove compound
                self._current_regimen.pop(cid, None)
            else:
                # Change dose tier
                tier_idx = (action - N_ADD - N_REMOVE) // N_COMPOUNDS
                if cid in self._current_regimen:
                    self._current_regimen[cid] = DOSE_TIERS[tier_idx % N_TIERS]

            # Simulate new organ scores (simplified — real uses scorer.py)
            new_scores = self._simulate_scores()
            delta      = sum(new_scores[o] - self._prev_scores[o] for o in ORGANS)
            poly_pen   = max(0, len(self._current_regimen) - 8) * 0.5
            reward     = float(delta * 0.1 - poly_pen * 0.05)
            self._prev_scores = new_scores
            return reward

        def _simulate_scores(self) -> Dict[str, float]:
            """Quick approximation — subtract load per compound, clamp."""
            base = {o: 70.0 for o in ORGANS}
            for cid, tier in self._current_regimen.items():
                mult = DOSE_MG.get(tier, 1.0)
                # Hepatic load approximation
                base["liver"] -= mult * 0.5
                base["kidney"] -= mult * 0.2
            return {o: float(max(10, min(95, v))) for o, v in base.items()}

        def _obs(self) -> np.ndarray:
            organ_vec = np.array([self._prev_scores.get(o, 70) / 100 for o in ORGANS],
                                  dtype=np.float32)
            bitmask  = np.array([1.0 if c in self._current_regimen else 0.0
                                  for c in COMPOUND_CATALOGUE], dtype=np.float32)
            tier_vec = np.array([DOSE_TIERS.index(self._current_regimen.get(c, "low")) / (N_TIERS - 1)
                                  if c in self._current_regimen else 0.0
                                  for c in COMPOUND_CATALOGUE], dtype=np.float32)
            poly_vec = np.array([len(self._current_regimen) / 12], dtype=np.float32)
            ddi_vec  = np.zeros(N_COMPOUNDS, dtype=np.float32)
            return np.concatenate([organ_vec, bitmask, tier_vec, poly_vec, ddi_vec])

        def render(self): pass


# ── Optimizer wrapper ─────────────────────────────────────────────────────────

class RLRegimenOptimizer:
    """
    Wraps an SAC or greedy policy for regimen optimization.
    Works in inference mode — no training required at runtime.
    """

    def __init__(self, model=None):
        self._sac = model  # stable-baselines3 SAC model or None

    def recommend(
        self,
        request,
        organ_scores: Dict[str, float],
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Returns top_k recommended actions with expected organ gain.
        Falls back to greedy difference search when SAC model absent.
        """
        if self._sac is not None and _GYM:
            return self._sac_recommend(request, organ_scores, top_k)
        return greedy_optimize(request, organ_scores, top_k)

    def _sac_recommend(self, request, organ_scores, top_k):
        """Roll out SAC policy for top_k steps, record actions."""
        try:
            env = PersonalizedRegimenEnv(request)
            obs, _ = env.reset()
            results = []
            for _ in range(top_k):
                action, _ = self._sac.predict(obs, deterministic=True)
                cid_idx = int(action) % N_COMPOUNDS
                compound = COMPOUND_CATALOGUE[cid_idx]
                obs, reward, done, _, _ = env.step(int(action))
                action_type = ("add" if action < N_ADD
                               else "remove" if action < N_ADD + N_REMOVE
                               else "dose_change")
                results.append({
                    "action":   action_type,
                    "compound": compound,
                    "gain":     round(reward * 10, 2),
                    "reason":   f"SAC policy — expected organ gain: {reward*10:.1f} pts",
                })
                if done:
                    break
            return results
        except Exception as e:
            logger.error("[RL] SAC recommend failed: %s", e)
            return greedy_optimize(request, organ_scores, top_k)


def greedy_optimize(
    request,
    organ_scores: Dict[str, float],
    top_k: int = 5,
) -> List[Dict]:
    """
    Deterministic greedy optimizer — no ML required.
    Tries adding/removing each compound, keeps the best changes.
    Uses the Eirion scoring engine as the simulation model.
    """
    try:
        from engine.scorer import run_liver_analysis
        from models.request import RegimenItem
    except ImportError:
        logger.warning("[RL] Could not import scorer — returning empty recommendations.")
        return []

    current_ids = {item.compound_id for item in request.regimen}
    candidates  = []

    # Try removing each current compound
    for item in request.regimen:
        mod = copy.deepcopy(request)
        mod.regimen = [r for r in mod.regimen if r.compound_id != item.compound_id]
        if not mod.regimen:
            continue
        try:
            res = run_liver_analysis(mod)
            delta = res.risk_summary.liver_index_now - organ_scores.get("liver", 70.0)
            if delta > 0:
                candidates.append({
                    "action":   "remove",
                    "compound": item.compound_id,
                    "gain":     round(delta, 2),
                    "reason":   f"Removing {item.compound_id} recovers {delta:.1f} pts.",
                })
        except Exception:
            continue

    # Try adding protective compounds not already in regimen
    for cid in ["nac", "coq10", "omega3", "vitamin_d3", "magnesium"]:
        if cid in current_ids:
            continue
        mod = copy.deepcopy(request)
        try:
            mod.regimen.append(RegimenItem(compound_id=cid, dose_mg=500, frequency_per_day=1))
            res = run_liver_analysis(mod)
            delta = res.risk_summary.liver_index_now - organ_scores.get("liver", 70.0)
            if delta > 0:
                candidates.append({
                    "action":   "add",
                    "compound": cid,
                    "gain":     round(delta, 2),
                    "reason":   f"Adding {cid} gains {delta:.1f} pts.",
                })
        except Exception:
            continue

    candidates.sort(key=lambda r: r["gain"], reverse=True)
    return candidates[:top_k]


def load_rl_optimizer(weights_path: str = "") -> RLRegimenOptimizer:
    """Load SAC model from zip file; falls back to greedy if absent."""
    if _SB3 and _GYM and weights_path and os.path.exists(weights_path):
        try:
            env = PersonalizedRegimenEnv()
            sac = SAC.load(weights_path, env=env)
            logger.info("[RL] Loaded SAC model from %s", weights_path)
            return RLRegimenOptimizer(model=sac)
        except Exception as e:
            logger.warning("[RL] Could not load SAC model: %s — using greedy fallback.", e)
    else:
        logger.info("[RL] No SAC weights at '%s' — using greedy optimizer.", weights_path)
    return RLRegimenOptimizer(model=None)

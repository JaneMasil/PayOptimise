"""
PayOptimise — A/B Experimentation Engine (Backend)
"""

import hashlib
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from scipy.stats import chi2_contingency


@dataclass
class ExperimentResult:
    experiment:      str
    n_control:       int
    n_treatment:     int
    control_rate:    float
    treatment_rate:  float
    absolute_uplift: float
    relative_uplift: float
    p_value:         float
    significant:     bool
    effect_size:     float
    guardrail_pass:  bool
    recommendation:  str


class ABExperimentEngine:
    def __init__(self, experiment_name: str, alpha: float = 0.05, min_sample_size: int = 100):
        self.name    = experiment_name
        self.alpha   = alpha
        self.min_n   = min_sample_size
        self.exposures: List[dict] = []

    def assign_variant(self, session_id: str) -> str:
        h = int(hashlib.md5(f"{self.name}:{session_id}".encode()).hexdigest(), 16) % 100
        return "treatment" if h < 50 else "control"

    def log_outcome(self, session_id, converted: bool, guardrail_ok: bool = True):
        self.exposures.append({
            "variant":      self.assign_variant(str(session_id)),
            "converted":    int(converted),
            "guardrail_ok": int(guardrail_ok),
        })

    def check_sample_ratio_mismatch(self) -> Tuple[bool, float]:
        n_ctrl = sum(1 for e in self.exposures if e["variant"] == "control")
        total  = len(self.exposures)
        if total == 0: return False, 0.0
        obs = n_ctrl / total
        return abs(obs - 0.5) > 0.02, round(obs, 4)

    def evaluate(self) -> ExperimentResult:
        ctrl  = [e for e in self.exposures if e["variant"] == "control"]
        treat = [e for e in self.exposures if e["variant"] == "treatment"]
        if len(ctrl) < self.min_n or len(treat) < self.min_n:
            raise ValueError(f"Insufficient sample: control={len(ctrl)}, treatment={len(treat)}, min={self.min_n}")

        c_conv, t_conv = sum(e["converted"] for e in ctrl), sum(e["converted"] for e in treat)
        c_rate, t_rate = c_conv / len(ctrl), t_conv / len(treat)

        table        = [[c_conv, len(ctrl)-c_conv], [t_conv, len(treat)-t_conv]]
        _, p, _, _   = chi2_contingency(table)
        h            = 2*(np.arcsin(np.sqrt(t_rate)) - np.arcsin(np.sqrt(c_rate)))
        guardrail_ok = all(e["guardrail_ok"] for e in treat)
        significant  = (p < self.alpha) and guardrail_ok
        abs_up       = round(t_rate - c_rate, 4)
        rel_up       = round((t_rate - c_rate) / c_rate, 4) if c_rate > 0 else 0.0

        if not significant:
            rec = "Do not ship — not significant or guardrail breach."
        elif rel_up > 0:
            rec = f"Ship treatment — {rel_up:+.1%} relative uplift, p={p:.4f}."
        else:
            rec = "Ship control — treatment shows negative effect."

        return ExperimentResult(
            experiment=self.name, n_control=len(ctrl), n_treatment=len(treat),
            control_rate=round(c_rate,4), treatment_rate=round(t_rate,4),
            absolute_uplift=abs_up, relative_uplift=rel_up,
            p_value=round(p,6), significant=significant,
            effect_size=round(abs(h),4), guardrail_pass=guardrail_ok,
            recommendation=rec
        )


def run_all_experiments(df: pd.DataFrame) -> pd.DataFrame:
    configs = [
        ("Authentication: OTP vs Biometric",        "auth", "auth_reached",   "auth_dropped"),
        ("Onboarding: 4-step vs 2-step",             "onb",  None,             "onboarding_dropped"),
        ("Recommendations: Generic vs Personalised", "rec",  "rec_shown",      "rec_clicked"),
    ]
    rows = []
    for name, key, filter_col, outcome_col in configs:
        engine = ABExperimentEngine(key)
        sub    = df if filter_col is None else df[df[filter_col] == 1]
        for _, row in sub.iterrows():
            engine.log_outcome(row["session_id"], bool(row[outcome_col]))
        r = engine.evaluate()
        rows.append({
            "experiment_name": name,
            "n_control":       r.n_control,
            "n_treatment":     r.n_treatment,
            "control_rate":    r.control_rate,
            "treatment_rate":  r.treatment_rate,
            "absolute_uplift": r.absolute_uplift,
            "relative_uplift": r.relative_uplift,
            "p_value":         r.p_value,
            "significant":     r.significant,
            "effect_size":     r.effect_size,
            "guardrail_pass":  r.guardrail_pass,
            "recommendation":  r.recommendation,
        })
    return pd.DataFrame(rows)

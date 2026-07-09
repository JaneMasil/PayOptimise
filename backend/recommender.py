"""
PayOptimise — Hybrid Recommendation Engine (Backend)
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class PaymentMethod:
    method_id:    str
    name:         str
    mobile_pref:  float = 0.5
    desktop_pref: float = 0.5
    icon:         str   = "💳"


@dataclass
class RecommendationResult:
    user_id: str
    method:  PaymentMethod
    score:   float
    reasons: List[str]


class FeatureStore:
    def __init__(self):
        self._user:    Dict[str, dict] = {}
        self._session: Dict[str, dict] = {}

    def update_user(self, uid: str, feats: dict):
        existing = self._user.get(str(uid), {})
        existing.update(feats)
        self._user[str(uid)] = existing

    def get_user(self, uid: str) -> dict:
        return self._user.get(str(uid), {})

    def set_session(self, sid: str, ctx: dict):
        self._session[str(sid)] = ctx

    def get_session(self, sid: str) -> dict:
        return self._session.get(str(sid), {})

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> "FeatureStore":
        store = cls()
        for uid, grp in df.groupby("user_id"):
            pref = {}
            if "rec_method" in grp.columns:
                clicked = grp[grp.get("rec_clicked", pd.Series(0, index=grp.index)) == 1]
                for m, cnt in clicked.rec_method.value_counts().items():
                    pref[f"pref_{m.replace(' ','_')}"] = cnt / max(len(clicked), 1)
            store.update_user(uid, {
                "tenure":          grp.account_tenure.iloc[-1],
                "primary_device":  grp.device.mode().iloc[0],
                "avg_hour":        float(grp.hour_of_day.mean()),
                "n_sessions":      len(grp),
                "conversion_rate": float(grp.converted.mean()),
                **pref,
            })
        for _, row in df.iterrows():
            store.set_session(row.session_id, {
                "device":     row.device,
                "hour":       int(row.hour_of_day),
                "page_depth": int(row.page_depth),
                "is_peak":    int(row.is_peak_hour),
            })
        return store


class HybridRecommender:
    WEIGHTS = {"collaborative": 0.40, "device_match": 0.31, "time_context": 0.22, "session_depth": 0.07}
    ONE_TAP  = {"Apple Pay", "Google Pay", "Saved card"}

    def __init__(self, feature_store: Optional[FeatureStore] = None):
        self.store = feature_store or FeatureStore()

    def score(self, uid: str, m: PaymentMethod, ctx: Optional[dict] = None) -> Tuple[float, List[str]]:
        ctx     = ctx or {}
        device  = ctx.get("device", "desktop")
        hour    = int(ctx.get("hour", 12))
        depth   = int(ctx.get("page_depth", 3))
        is_peak = int(ctx.get("is_peak", 0))

        key    = f"pref_{m.method_id.replace(' ','_')}"
        collab = self.store.get_user(uid).get(key, 0.5)
        dev_s  = m.mobile_pref if device == "mobile" else m.desktop_pref
        time_s = 1.0 if is_peak else 0.75
        dep_s  = min(depth / 5.0, 1.0)

        total = (self.WEIGHTS["collaborative"] * collab +
                 self.WEIGHTS["device_match"]  * dev_s  +
                 self.WEIGHTS["time_context"]  * time_s +
                 self.WEIGHTS["session_depth"] * dep_s)

        reasons = [
            "Matches past preference" if collab > 0.5 else "Inferred from cohort",
            "Optimised for 1-tap mobile" if device=="mobile" and m.name in self.ONE_TAP else "Available for device",
            "Peak hour — familiar methods preferred" if is_peak else "Standard session",
            f"Page depth {depth} — {'high' if dep_s>0.6 else 'moderate'} intent",
        ]
        return round(total, 4), reasons

    def recommend(self, uid: str, methods: List[PaymentMethod], ctx: Optional[dict] = None, top_k: int = 3):
        ctx    = ctx or self.store.get_session(uid)
        scored = []
        for m in methods:
            s, reasons = self.score(uid, m, ctx)
            scored.append(RecommendationResult(uid, m, s, reasons))
        return sorted(scored, key=lambda x: x.score, reverse=True)[:top_k]

    def evaluate_ctr(self, df: pd.DataFrame) -> dict:
        shown = df[df.rec_shown == 1]
        ctrl  = shown[shown.variant_rec == "control"].rec_clicked.mean()
        treat = shown[shown.variant_rec == "treatment"].rec_clicked.mean()
        return {
            "random_baseline":  round(ctrl, 4),
            "hybrid_model":     round(treat, 4),
            "relative_uplift":  round((treat - ctrl) / max(ctrl, 0.001), 4),
        }


DEFAULT_METHODS = [
    PaymentMethod("Apple Pay",     "Apple Pay",     mobile_pref=0.90, desktop_pref=0.30, icon="🍎"),
    PaymentMethod("Google Pay",    "Google Pay",    mobile_pref=0.85, desktop_pref=0.35, icon="🔵"),
    PaymentMethod("Saved card",    "Saved card",    mobile_pref=0.75, desktop_pref=0.70, icon="💳"),
    PaymentMethod("PayPal",        "PayPal",        mobile_pref=0.60, desktop_pref=0.65, icon="🅿️"),
    PaymentMethod("Bank transfer", "Bank transfer", mobile_pref=0.30, desktop_pref=0.80, icon="🏦"),
    PaymentMethod("Credit card",   "Credit card",   mobile_pref=0.55, desktop_pref=0.70, icon="💰"),
]

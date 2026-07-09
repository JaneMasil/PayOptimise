"""
PayOptimise — Synthetic Dataset Generator
Backend module serving the Flask API.
"""

import hashlib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

RANDOM_SEED = 42
START_DATE  = datetime(2024, 1, 1)

DROP_PROBS = {
    "onboarding": {
        "control":   {"mobile": 0.20, "desktop": 0.12},
        "treatment": {"mobile": 0.13, "desktop": 0.09},
    },
    "payment_initiation": {
        "base":      {"mobile": 0.22, "desktop": 0.15},
        "rec_bonus": 0.30,
    },
    "authentication": {
        "control":   {"mobile": 0.43, "desktop": 0.28},
        "treatment": {"mobile": 0.14, "desktop": 0.10},
        "loyal_mult": 0.75,
    },
    "confirmation": {
        "base": {"mobile": 0.06, "desktop": 0.04},
    },
}


def assign_variant(session_id: int, experiment_name: str) -> str:
    h = int(hashlib.md5(f"{experiment_name}:{session_id}".encode()).hexdigest(), 16)
    return "treatment" if h % 100 < 50 else "control"


def simulate_session(i, device, tenure, hour, location, age_group, user_id, timestamp):
    is_peak = int(12 <= hour <= 14 or 19 <= hour <= 21)
    loyal   = tenure == "loyal"
    va = assign_variant(i, "auth")
    vo = assign_variant(i, "onb")
    vr = assign_variant(i, "rec")

    p_onb    = DROP_PROBS["onboarding"][vo][device]
    if loyal: p_onb *= 0.6
    onb_dropped = np.random.random() < p_onb
    onb_time    = round(np.random.normal(45 if vo == "treatment" else 90, 15), 1)

    if onb_dropped:
        pay_r=pay_d=rec_s=rec_c=0; pay_t=rec_m=None
    else:
        pay_r  = 1
        p_clk  = (0.243 + 0.04*is_peak + 0.03*(device=="mobile")) if vr=="treatment" else (0.117 + 0.02*is_peak)
        rec_c  = int(np.random.random() < min(p_clk, 0.45))
        if device == "mobile" and vr == "treatment":
            rec_m = np.random.choice(["Apple Pay", "Google Pay", "Saved card"], p=[0.40,0.35,0.25])
        elif device == "desktop" and vr == "treatment":
            rec_m = np.random.choice(["Bank transfer", "Saved card", "Credit card"], p=[0.40,0.35,0.25])
        else:
            rec_m = np.random.choice(["Saved card", "PayPal", "Bank transfer", "Credit card"])
        p_pay  = DROP_PROBS["payment_initiation"]["base"][device]
        if rec_c: p_pay *= (1 - DROP_PROBS["payment_initiation"]["rec_bonus"])
        pay_d, rec_s = int(np.random.random() < p_pay), 1
        pay_t  = round(np.random.normal(30, 10), 1)

    if not pay_r or pay_d:
        auth_r=auth_d=0; auth_t=auth_m=None
    else:
        auth_r  = 1
        auth_m  = "biometric" if va == "treatment" else "OTP"
        p_auth  = DROP_PROBS["authentication"][va][device]
        if loyal: p_auth *= DROP_PROBS["authentication"]["loyal_mult"]
        auth_d  = int(np.random.random() < p_auth)
        auth_t  = round(np.random.normal(12 if va=="treatment" else 35, 5), 1)

    if not auth_r or auth_d:
        conf_r=conf_d=0; conf_t=None
    else:
        conf_r = 1
        conf_d = int(np.random.random() < DROP_PROBS["confirmation"]["base"][device])
        conf_t = round(np.random.normal(8, 3), 1)

    converted = int(conf_r and not conf_d)

    if   onb_dropped:   ds = "onboarding"
    elif not pay_r:     ds = "onboarding"
    elif pay_d:         ds = "payment_initiation"
    elif not auth_r:    ds = "payment_initiation"
    elif auth_d:        ds = "authentication"
    elif conf_d:        ds = "confirmation"
    else:               ds = "none"

    times   = [t for t in [onb_time, pay_t, auth_t, conf_t] if t is not None]
    total_t = round(sum(times), 1) if times else None

    return {
        "session_id": i, "user_id": user_id, "timestamp": timestamp,
        "device": device, "location": location, "age_group": age_group,
        "account_tenure": tenure, "hour_of_day": hour, "is_peak_hour": is_peak,
        "page_depth": int(np.random.randint(2, 8)),
        "session_length_s": int(max(np.random.normal((total_t or 60)*2, 20), 10)),
        "variant_auth": va, "variant_onboarding": vo, "variant_rec": vr,
        "auth_method": auth_m if auth_r else "N/A",
        "onboarding_reached": 1, "onboarding_dropped": int(onb_dropped), "onboarding_time_s": onb_time,
        "payment_reached": pay_r, "payment_dropped": pay_d if pay_r else 0, "payment_time_s": pay_t,
        "rec_shown": rec_s if pay_r else 0, "rec_clicked": rec_c if pay_r else 0, "rec_method": rec_m if pay_r else "N/A",
        "auth_reached": auth_r, "auth_dropped": auth_d if auth_r else 0, "auth_time_s": auth_t,
        "confirmation_reached": conf_r, "confirmation_dropped": conf_d if conf_r else 0, "confirmation_time_s": conf_t,
        "converted": converted, "drop_stage": ds, "total_journey_time_s": total_t,
    }


def generate_dataset(n: int = 20000) -> pd.DataFrame:
    np.random.seed(RANDOM_SEED)
    devices  = np.random.choice(["mobile","desktop"], size=n, p=[0.60,0.40])
    user_ids = np.random.randint(10000, 99999, size=n)
    ages     = np.random.choice(["18-24","25-34","35-44","45-54","55+"], size=n, p=[0.18,0.35,0.25,0.14,0.08])
    tenures  = np.random.choice(["new","returning","loyal"], size=n, p=[0.30,0.45,0.25])
    locs     = np.random.choice(["IE","UK","DE","FR","US","Other"], size=n, p=[0.28,0.22,0.15,0.12,0.13,0.10])
    hours    = np.random.randint(0, 24, size=n)
    days_off = np.random.randint(0, 365, size=n)
    stamps   = [(START_DATE + timedelta(days=int(d), hours=int(h))).strftime("%Y-%m-%d %H:%M")
                for d,h in zip(days_off, hours)]
    rows = [simulate_session(i, devices[i], tenures[i], int(hours[i]),
                             locs[i], ages[i], int(user_ids[i]), stamps[i])
            for i in range(n)]
    return pd.DataFrame(rows)


def get_summary_stats(df: pd.DataFrame) -> dict:
    auth_ctrl  = df[(df.auth_reached==1)&(df.variant_auth=="control")]
    auth_treat = df[(df.auth_reached==1)&(df.variant_auth=="treatment")]
    rec_ctrl   = df[(df.rec_shown==1)&(df.variant_rec=="control")]
    rec_treat  = df[(df.rec_shown==1)&(df.variant_rec=="treatment")]

    return {
        "total_sessions":      len(df),
        "conversion_rate":     round(df.converted.mean(), 4),
        "mobile_conv":         round(df[df.device=="mobile"].converted.mean(), 4),
        "desktop_conv":        round(df[df.device=="desktop"].converted.mean(), 4),
        "auth_otp_drop":       round(auth_ctrl.auth_dropped.mean(), 4) if len(auth_ctrl) else 0,
        "auth_biometric_drop": round(auth_treat.auth_dropped.mean(), 4) if len(auth_treat) else 0,
        "rec_ctr_generic":     round(rec_ctrl.rec_clicked.mean(), 4) if len(rec_ctrl) else 0,
        "rec_ctr_personalised":round(rec_treat.rec_clicked.mean(), 4) if len(rec_treat) else 0,
        "avg_journey_time":    round(df.total_journey_time_s.mean(), 1),
        "by_drop_stage": df.drop_stage.value_counts().to_dict(),
        "by_device":     df.device.value_counts().to_dict(),
        "by_location":   df.location.value_counts().head(6).to_dict(),
    }

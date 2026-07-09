"""
PayOptimise — Database Module (SQLite)
Stores sessions, experiment results, recommendations, and friction alerts.
Auto-initialises on first use.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'payoptimise.db')

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def db_init():
    """Initialise all tables — safe to call multiple times."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,user_id INTEGER,timestamp TEXT,
        device TEXT,location TEXT,account_tenure TEXT,
        hour_of_day INTEGER,is_peak_hour INTEGER,
        variant_auth TEXT,variant_onboarding TEXT,variant_rec TEXT,
        onboarding_dropped INTEGER,payment_reached INTEGER,payment_dropped INTEGER,
        rec_shown INTEGER,rec_clicked INTEGER,rec_method TEXT,
        auth_reached INTEGER,auth_dropped INTEGER,auth_method TEXT,
        confirmation_reached INTEGER,confirmation_dropped INTEGER,
        converted INTEGER,drop_stage TEXT,total_journey_time_s REAL,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS experiment_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        experiment_name TEXT,n_control INTEGER,n_treatment INTEGER,
        control_rate REAL,treatment_rate REAL,relative_uplift REAL,
        p_value REAL,effect_size REAL,significant INTEGER,
        guardrail_pass INTEGER,recommendation TEXT,
        run_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,user_id INTEGER,device TEXT,
        method TEXT,score REAL,clicked INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS friction_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stage TEXT,drop_off TEXT,severity TEXT,
        experiment TEXT,resolved INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()

def _ensure_tables():
    """Auto-init if tables don't exist yet."""
    try:
        conn = get_conn()
        conn.execute("SELECT 1 FROM sessions LIMIT 1")
        conn.close()
    except:
        db_init()

def db_log_session(data: dict):
    _ensure_tables()
    conn = get_conn()
    cols = ['session_id','user_id','timestamp','device','location','account_tenure',
            'hour_of_day','is_peak_hour','variant_auth','variant_onboarding','variant_rec',
            'onboarding_dropped','payment_reached','payment_dropped','rec_shown','rec_clicked',
            'rec_method','auth_reached','auth_dropped','auth_method','confirmation_reached',
            'confirmation_dropped','converted','drop_stage','total_journey_time_s']
    vals = [data.get(c) for c in cols]
    ph   = ','.join(['?']*len(cols))
    conn.execute(f"INSERT INTO sessions ({','.join(cols)}) VALUES ({ph})", vals)
    conn.commit()
    conn.close()

def db_get_sessions(limit=50):
    _ensure_tables()
    conn = get_conn()
    rows = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_get_stats():
    _ensure_tables()
    conn  = get_conn()
    c     = conn.cursor()
    total     = c.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    converted = c.execute("SELECT COUNT(*) FROM sessions WHERE converted=1").fetchone()[0]
    by_device = c.execute("SELECT device, COUNT(*) as n, SUM(converted) as conv FROM sessions GROUP BY device").fetchall()
    by_drop   = c.execute("SELECT drop_stage, COUNT(*) as n FROM sessions GROUP BY drop_stage ORDER BY n DESC").fetchall()
    experiments = c.execute("SELECT * FROM experiment_results ORDER BY run_at DESC LIMIT 10").fetchall()
    alerts    = c.execute("SELECT * FROM friction_alerts ORDER BY created_at DESC LIMIT 10").fetchall()
    conn.close()
    return {
        'total_sessions':  total,
        'total_converted': converted,
        'conversion_rate': round(converted/total,4) if total else 0,
        'by_device':       [dict(r) for r in by_device],
        'by_drop_stage':   [dict(r) for r in by_drop],
        'experiments':     [dict(r) for r in experiments],
        'alerts':          [dict(r) for r in alerts],
    }

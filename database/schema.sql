-- PayOptimise Suite — Full Database Schema
-- SQLite (dev) | PostgreSQL-compatible (production)
-- MS5132 Major ISM Project | Jane Donisha Masila Clement Valavan

-- ─── Sessions ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id            INTEGER UNIQUE,
    user_id               INTEGER,
    timestamp             TEXT,
    device                TEXT CHECK(device IN ('mobile','desktop')),
    location              TEXT,
    age_group             TEXT,
    account_tenure        TEXT CHECK(account_tenure IN ('new','returning','loyal')),
    hour_of_day           INTEGER CHECK(hour_of_day BETWEEN 0 AND 23),
    is_peak_hour          INTEGER DEFAULT 0,
    page_depth            INTEGER,
    session_length_s      INTEGER,
    -- Experiment assignments
    variant_auth          TEXT CHECK(variant_auth IN ('control','treatment')),
    variant_onboarding    TEXT CHECK(variant_onboarding IN ('control','treatment')),
    variant_rec           TEXT CHECK(variant_rec IN ('control','treatment')),
    -- Auth
    auth_method           TEXT,
    -- Stage outcomes
    onboarding_reached    INTEGER DEFAULT 1,
    onboarding_dropped    INTEGER DEFAULT 0,
    onboarding_time_s     REAL,
    payment_reached       INTEGER DEFAULT 0,
    payment_dropped       INTEGER DEFAULT 0,
    payment_time_s        REAL,
    rec_shown             INTEGER DEFAULT 0,
    rec_clicked           INTEGER DEFAULT 0,
    rec_method            TEXT,
    auth_reached          INTEGER DEFAULT 0,
    auth_dropped          INTEGER DEFAULT 0,
    auth_time_s           REAL,
    confirmation_reached  INTEGER DEFAULT 0,
    confirmation_dropped  INTEGER DEFAULT 0,
    confirmation_time_s   REAL,
    -- Summary
    converted             INTEGER DEFAULT 0,
    drop_stage            TEXT,
    total_journey_time_s  REAL,
    created_at            TEXT DEFAULT (datetime('now'))
);

-- ─── Experiment results ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS experiment_results (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_name  TEXT NOT NULL,
    n_control        INTEGER,
    n_treatment      INTEGER,
    control_rate     REAL,
    treatment_rate   REAL,
    absolute_uplift  REAL,
    relative_uplift  REAL,
    p_value          REAL,
    effect_size      REAL,
    significant      INTEGER DEFAULT 0,
    guardrail_pass   INTEGER DEFAULT 1,
    recommendation   TEXT,
    run_at           TEXT DEFAULT (datetime('now'))
);

-- ─── Recommendations ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recommendations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER REFERENCES sessions(session_id),
    user_id      INTEGER,
    device       TEXT,
    method_shown TEXT,
    score        REAL,
    rank         INTEGER,
    clicked      INTEGER DEFAULT 0,
    created_at   TEXT DEFAULT (datetime('now'))
);

-- ─── Friction alerts ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS friction_alerts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    stage          TEXT NOT NULL,
    drop_off_pct   REAL,
    severity       TEXT CHECK(severity IN ('HIGH','MEDIUM','LOW')),
    experiment_rec TEXT,
    resolved       INTEGER DEFAULT 0,
    resolved_at    TEXT,
    created_at     TEXT DEFAULT (datetime('now'))
);

-- ─── Feature store snapshot ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS feature_store (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER UNIQUE,
    primary_device   TEXT,
    tenure           TEXT,
    avg_hour         REAL,
    n_sessions       INTEGER DEFAULT 0,
    conversion_rate  REAL DEFAULT 0,
    pref_apple_pay   REAL DEFAULT 0,
    pref_google_pay  REAL DEFAULT 0,
    pref_saved_card  REAL DEFAULT 0,
    pref_paypal      REAL DEFAULT 0,
    pref_bank_xfer   REAL DEFAULT 0,
    updated_at       TEXT DEFAULT (datetime('now'))
);

-- ─── Indexes ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_sessions_device    ON sessions(device);
CREATE INDEX IF NOT EXISTS idx_sessions_converted ON sessions(converted);
CREATE INDEX IF NOT EXISTS idx_sessions_drop      ON sessions(drop_stage);
CREATE INDEX IF NOT EXISTS idx_sessions_variant   ON sessions(variant_auth, variant_rec);
CREATE INDEX IF NOT EXISTS idx_sessions_tenure    ON sessions(account_tenure);
CREATE INDEX IF NOT EXISTS idx_recs_session       ON recommendations(session_id);
CREATE INDEX IF NOT EXISTS idx_alerts_stage       ON friction_alerts(stage, resolved);

-- ─── Useful views ─────────────────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS funnel_summary AS
SELECT
    COUNT(*)                                         AS total_sessions,
    SUM(onboarding_reached)                          AS onboarding_in,
    SUM(onboarding_dropped)                          AS onboarding_dropped,
    ROUND(100.0*SUM(onboarding_dropped)/COUNT(*),1)  AS onboarding_drop_pct,
    SUM(payment_reached)                             AS payment_in,
    SUM(payment_dropped)                             AS payment_dropped,
    SUM(auth_reached)                                AS auth_in,
    SUM(auth_dropped)                                AS auth_dropped,
    ROUND(100.0*SUM(auth_dropped)/MAX(SUM(auth_reached),1),1) AS auth_drop_pct,
    SUM(confirmation_reached)                        AS confirmation_in,
    SUM(converted)                                   AS completed,
    ROUND(100.0*SUM(converted)/COUNT(*),1)           AS conversion_rate
FROM sessions;

CREATE VIEW IF NOT EXISTS device_performance AS
SELECT
    device,
    COUNT(*)                                AS sessions,
    ROUND(100.0*SUM(converted)/COUNT(*),1)  AS conversion_pct,
    ROUND(100.0*SUM(auth_dropped)/MAX(SUM(auth_reached),1),1) AS auth_drop_pct,
    ROUND(AVG(total_journey_time_s),1)      AS avg_journey_s
FROM sessions
GROUP BY device;

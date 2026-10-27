"""Model: the SQLite tables and what the values mean. Applied on every start; additive only."""

DEMO_USER_ID = "alex-demo"
BREATH_IN_SECONDS = 4
BREATH_OUT_SECONDS = 6
ALLOWED_BREATHS = (6, 8)
CUES = ("circle", "text")
SELF_REPORTS = ("a_bit_calmer", "about_the_same", "not_sure")
FEELINGS = ("steady", "tense", "overwhelmed")
CHECKIN_FRESH_HOURS = 6  # a check-in older than this no longer shapes Home

SCHEMA = """
PRAGMA foreign_keys = ON;

-- One fictional person. Every record below belongs to them.
CREATE TABLE IF NOT EXISTS demo_users (
    user_id       TEXT PRIMARY KEY,
    display_name  TEXT NOT NULL,
    is_fixture    INTEGER NOT NULL DEFAULT 1 CHECK (is_fixture IN (0, 1))
);

-- One row per exercise. Observed facts only: what was planned, what happened, how long.
-- client_key is made by the browser once per Start press, so a retried save cannot
-- create a second row.
CREATE TABLE IF NOT EXISTS exercise_sessions (
    session_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          TEXT NOT NULL REFERENCES demo_users (user_id),
    client_key       TEXT NOT NULL UNIQUE CHECK (length(client_key) BETWEEN 8 AND 64),
    skill            TEXT NOT NULL DEFAULT 'paced_breathing' CHECK (skill = 'paced_breathing'),
    planned_breaths  INTEGER NOT NULL CHECK (planned_breaths IN (6, 8)),
    cue              TEXT NOT NULL CHECK (cue IN ('circle', 'text')),
    started_at       TEXT NOT NULL,
    ended_at         TEXT,
    status           TEXT NOT NULL DEFAULT 'in_progress'
                     CHECK (status IN ('in_progress', 'completed', 'stopped')),
    breaths_done     INTEGER NOT NULL DEFAULT 0 CHECK (breaths_done BETWEEN 0 AND 8),
    entry_ms         INTEGER CHECK (entry_ms IS NULL OR entry_ms >= 0),
    exercise_ms      INTEGER CHECK (exercise_ms IS NULL OR exercise_ms >= 0),
    paused_ms        INTEGER NOT NULL DEFAULT 0 CHECK (paused_ms >= 0)
);

-- The optional one-tap answer after an exercise. The person's own words, kept apart
-- from the observed facts above and never scored.
CREATE TABLE IF NOT EXISTS session_feedback (
    session_id   INTEGER PRIMARY KEY REFERENCES exercise_sessions (session_id),
    self_report  TEXT NOT NULL CHECK (self_report IN ('a_bit_calmer', 'about_the_same', 'not_sure')),
    created_at   TEXT NOT NULL
);

-- What the person chose last. Every value is something they picked (source = 'chosen').
CREATE TABLE IF NOT EXISTS preferences (
    user_id     TEXT NOT NULL REFERENCES demo_users (user_id),
    key         TEXT NOT NULL CHECK (key IN ('breaths', 'cue', 'fewer_words')),
    value       TEXT NOT NULL,
    source      TEXT NOT NULL DEFAULT 'chosen' CHECK (source = 'chosen'),
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (user_id, key)
);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id  TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL REFERENCES demo_users (user_id),
    purpose          TEXT NOT NULL CHECK (purpose IN ('intro', 'question')),
    started_at       TEXT NOT NULL
);

-- Every step of a model exchange, in the order it happened. A failed or blocked request
-- has an error step and no assistant answer.
CREATE TABLE IF NOT EXISTS messages (
    message_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id  TEXT NOT NULL REFERENCES conversations (conversation_id),
    role             TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
    stage            TEXT NOT NULL CHECK (stage IN ('question', 'intro', 'proposed_sql',
                     'executed_sql', 'retrieval_result', 'answer', 'error')),
    content          TEXT NOT NULL,
    status           TEXT NOT NULL CHECK (status IN ('ok', 'failed', 'blocked', 'fixed_text')),
    created_at       TEXT NOT NULL,
    prompt_version   TEXT
);

-- The optional one-tap check-in on Home. The person's own word for how they are arriving,
-- never inferred. It changes what Home shows, and the person can change or ignore it.
CREATE TABLE IF NOT EXISTS checkins (
    checkin_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL REFERENCES demo_users (user_id),
    feeling     TEXT NOT NULL CHECK (feeling IN ('steady', 'tense', 'overwhelmed')),
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation_id, message_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON exercise_sessions (user_id, session_id);
"""

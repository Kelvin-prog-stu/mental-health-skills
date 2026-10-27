"""Controller for every application write and read against SQLite.

Routes call these functions; nothing else writes to the database. The model never reaches
this module: its read-only queries go through retrieval.py on a separate connection.
"""

import sqlite3
import uuid
from collections import Counter
from datetime import datetime, timezone

import config
from models import ALLOWED_BREATHS, CHECKIN_FRESH_HOURS, CUES, DEMO_USER_ID, FEELINGS, SCHEMA, SELF_REPORTS


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def get_connection() -> sqlite3.Connection:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create missing tables and the one fictional user. Never reseeds or duplicates."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        conn.execute(
            "INSERT INTO demo_users (user_id, display_name, is_fixture) VALUES (?, ?, 1) "
            "ON CONFLICT (user_id) DO NOTHING",
            (DEMO_USER_ID, "Alex (fictional)"),
        )


def record_counts() -> dict[str, int]:
    tables = ("exercise_sessions", "session_feedback", "preferences", "conversations", "messages")
    with get_connection() as conn:
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}


# ---- Exercise sessions -----------------------------------------------------------------


def _session(conn: sqlite3.Connection, session_id: int) -> dict:
    row = conn.execute(
        "SELECT s.*, f.self_report FROM exercise_sessions s "
        "LEFT JOIN session_feedback f ON f.session_id = s.session_id WHERE s.session_id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        raise NotFoundError(f"No session with id {session_id}.")
    return dict(row)


def start_session(planned_breaths: int, cue: str, entry_ms: int | None, client_key: str) -> tuple[dict, bool]:
    """Save the start of an exercise. Returns (session, created). A repeated client_key
    returns the existing row instead of adding a second one. Starting also remembers the
    length and cue the person picked, which is what "Same as last time" offers next."""
    if planned_breaths not in ALLOWED_BREATHS or cue not in CUES:
        raise ValueError("Unsupported length or cue.")
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT session_id FROM exercise_sessions WHERE client_key = ?", (client_key,)
        ).fetchone()
        if existing:
            return _session(conn, existing["session_id"]), False
        cursor = conn.execute(
            "INSERT INTO exercise_sessions (user_id, client_key, planned_breaths, cue, started_at, entry_ms) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (DEMO_USER_ID, client_key, planned_breaths, cue, now_iso(), entry_ms),
        )
        _set_preferences(conn, {"breaths": str(planned_breaths), "cue": cue})
        return _session(conn, cursor.lastrowid), True


def finish_session(session_id: int, status: str, breaths_done: int, exercise_ms: int | None, paused_ms: int) -> dict:
    if status not in ("completed", "stopped"):
        raise ValueError("Status must be completed or stopped.")
    with get_connection() as conn:
        current = _session(conn, session_id)
        if current["status"] != "in_progress":
            raise ConflictError(f"Session {session_id} is already {current['status']}.")
        if breaths_done > current["planned_breaths"]:
            raise ValueError("More breaths than planned.")
        conn.execute(
            "UPDATE exercise_sessions SET status = ?, breaths_done = ?, exercise_ms = ?, paused_ms = ?, "
            "ended_at = ? WHERE session_id = ?",
            (status, breaths_done, exercise_ms, paused_ms, now_iso(), session_id),
        )
        return _session(conn, session_id)


def save_feedback(session_id: int, self_report: str) -> dict:
    if self_report not in SELF_REPORTS:
        raise ValueError("Unsupported answer.")
    with get_connection() as conn:
        _session(conn, session_id)
        conn.execute(
            "INSERT INTO session_feedback (session_id, self_report, created_at) VALUES (?, ?, ?) "
            "ON CONFLICT (session_id) DO UPDATE SET self_report = excluded.self_report, created_at = excluded.created_at",
            (session_id, self_report, now_iso()),
        )
        return _session(conn, session_id)


def list_sessions(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT s.*, f.self_report FROM exercise_sessions s "
            "LEFT JOIN session_feedback f ON f.session_id = s.session_id "
            "WHERE s.user_id = ? ORDER BY s.session_id DESC LIMIT ?",
            (DEMO_USER_ID, limit),
        ).fetchall()
    return [dict(r) for r in rows]


# ---- Preferences -----------------------------------------------------------------------

DEFAULT_PREFERENCES = {"breaths": "6", "cue": "circle", "fewer_words": "0"}


def _set_preferences(conn: sqlite3.Connection, values: dict[str, str]) -> None:
    for key, value in values.items():
        conn.execute(
            "INSERT INTO preferences (user_id, key, value, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (user_id, key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (DEMO_USER_ID, key, value, now_iso()),
        )


def get_preferences() -> dict:
    """Current choices, with defaults filled in. `remembered` lists the keys the person
    actually chose, so the interface only says "Same as last time" when that is true."""
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM preferences WHERE user_id = ?", (DEMO_USER_ID,)).fetchall()
    stored = {r["key"]: r["value"] for r in rows}
    merged = {**DEFAULT_PREFERENCES, **stored}
    return {
        "breaths": int(merged["breaths"]),
        "cue": merged["cue"],
        "fewer_words": merged["fewer_words"] == "1",
        "remembered": sorted(stored),
    }


def set_preferences(breaths: int | None, cue: str | None, fewer_words: bool | None) -> dict:
    values: dict[str, str] = {}
    if breaths is not None:
        if breaths not in ALLOWED_BREATHS:
            raise ValueError("Unsupported length.")
        values["breaths"] = str(breaths)
    if cue is not None:
        if cue not in CUES:
            raise ValueError("Unsupported cue.")
        values["cue"] = cue
    if fewer_words is not None:
        values["fewer_words"] = "1" if fewer_words else "0"
    with get_connection() as conn:
        _set_preferences(conn, values)
    return get_preferences()


# ---- Conversations ---------------------------------------------------------------------


def create_conversation(purpose: str) -> str:
    conversation_id = f"conv-{uuid.uuid4().hex[:8]}"
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO conversations (conversation_id, user_id, purpose, started_at) VALUES (?, ?, ?, ?)",
            (conversation_id, DEMO_USER_ID, purpose, now_iso()),
        )
    return conversation_id


def save_message(conversation_id: str, role: str, stage: str, content: str, status: str, prompt_version: str | None) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO messages (conversation_id, role, stage, content, status, created_at, prompt_version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (conversation_id, role, stage, content, status, now_iso(), prompt_version),
        )
        return cursor.lastrowid


def list_messages(conversation_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY message_id", (conversation_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def list_conversations(limit: int = 30) -> list[dict]:
    """Recent conversations, newest first, each with its saved steps in order."""
    with get_connection() as conn:
        convs = conn.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY started_at DESC LIMIT ?",
            (DEMO_USER_ID, limit),
        ).fetchall()
    return [{**dict(c), "messages": list_messages(c["conversation_id"])} for c in convs]


# ---- Check-ins and profile (Part 3.2 presentation) ---------------------------------------


def save_checkin(feeling: str) -> dict:
    if feeling not in FEELINGS:
        raise ValueError("Unsupported answer.")
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO checkins (user_id, feeling, created_at) VALUES (?, ?, ?)",
            (DEMO_USER_ID, feeling, now_iso()),
        )
        row = conn.execute("SELECT * FROM checkins WHERE checkin_id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


def recent_checkins(limit: int = 5) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM checkins WHERE user_id = ? ORDER BY checkin_id DESC LIMIT ?", (DEMO_USER_ID, limit)
        ).fetchall()
    return [dict(r) for r in rows]


def current_checkin() -> dict | None:
    """Today's check-in if it is recent enough to shape Home, else None."""
    latest = recent_checkins(1)
    if not latest:
        return None
    age = datetime.now(timezone.utc) - datetime.fromisoformat(latest[0]["created_at"])
    return latest[0] if age.total_seconds() < CHECKIN_FRESH_HOURS * 3600 else None


def get_profile() -> dict:
    """The demo user's profile, built from what they actually did. `usual` is the most common
    length and cue over their last 10 sessions; it needs at least 2 sessions to exist."""
    with get_connection() as conn:
        user = conn.execute("SELECT display_name FROM demo_users WHERE user_id = ?", (DEMO_USER_ID,)).fetchone()
        recent = conn.execute(
            "SELECT planned_breaths, cue, status FROM exercise_sessions WHERE user_id = ? "
            "ORDER BY session_id DESC LIMIT 10",
            (DEMO_USER_ID,),
        ).fetchall()
        totals = conn.execute(
            "SELECT COUNT(*), SUM(status = 'completed'), SUM(status = 'stopped') FROM exercise_sessions WHERE user_id = ?",
            (DEMO_USER_ID,),
        ).fetchone()
    usual = None
    if len(recent) >= 2:
        breaths = Counter(r["planned_breaths"] for r in recent).most_common(1)[0][0]
        cue = Counter(r["cue"] for r in recent).most_common(1)[0][0]
        usual = {"breaths": breaths, "cue": cue, "based_on": len(recent)}
    return {
        "display_name": user["display_name"] if user else "Alex (fictional)",
        "sessions": totals[0] or 0,
        "completed": totals[1] or 0,
        "stopped": totals[2] or 0,
        "usual": usual,
        "current_checkin": current_checkin(),
        "recent_checkins": recent_checkins(5),
    }

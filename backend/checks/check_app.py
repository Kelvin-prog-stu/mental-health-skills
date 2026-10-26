"""Repeatable backend checks. MOCK model only: no network, no key needed, no paid calls.

Run from backend/:  .venv\\Scripts\\python.exe checks\\check_app.py
Uses a throwaway database (APP_DB_PATH), so it is safe while the app is running.
"""

import gc
import json
import os
import sqlite3
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
_tmp = tempfile.TemporaryDirectory()
DB = Path(_tmp.name) / "check.sqlite3"
os.environ["APP_DB_PATH"] = str(DB)
os.environ["ALLOW_DEMO_MODES"] = "1"

from fastapi.testclient import TestClient  # noqa: E402

import assistant  # noqa: E402
import llm_client  # noqa: E402
import main  # noqa: E402
import retrieval  # noqa: E402

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, seen: object) -> None:
    results.append((name, bool(ok), str(seen)[:110]))


def rows(sql: str, *args) -> list:
    conn = sqlite3.connect(DB)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def snapshot() -> dict:
    tables = ("demo_users", "exercise_sessions", "session_feedback", "preferences")
    return {t: rows(f"SELECT * FROM {t} ORDER BY 1") for t in tables}


calls = {"n": 0}
real_generate = llm_client.generate


def counting_generate(*args, **kwargs):
    calls["n"] += 1
    raise AssertionError("a live model call was attempted during the mock checks")


llm_client.generate = counting_generate

with TestClient(main.app) as c:
    # ---- Sessions ----------------------------------------------------------------------
    body = {"planned_breaths": 6, "cue": "circle", "entry_ms": 2100, "client_key": "check-key-1"}
    first = c.post("/api/sessions", json=body)
    again = c.post("/api/sessions", json=body)
    check("starting a session saves it once (201)", first.status_code == 201, first.status_code)
    check("a retried start with the same client_key returns the same row, no duplicate (200)", again.status_code == 200 and again.json()["session_id"] == first.json()["session_id"] and len(rows("SELECT * FROM exercise_sessions")) == 1, again.status_code)
    sid = first.json()["session_id"]
    done = c.patch(f"/api/sessions/{sid}", json={"status": "completed", "breaths_done": 6, "exercise_ms": 60040, "paused_ms": 0})
    check("finishing saves completed, breaths, and the measured time", done.json()["status"] == "completed" and done.json()["exercise_ms"] == 60040, done.json()["status"])
    check("finishing twice is refused (409), the first result stands", c.patch(f"/api/sessions/{sid}", json={"status": "stopped", "breaths_done": 2}).status_code == 409, "409")
    s2 = c.post("/api/sessions", json={"planned_breaths": 8, "cue": "text", "client_key": "check-key-2"}).json()["session_id"]
    stopped = c.patch(f"/api/sessions/{s2}", json={"status": "stopped", "breaths_done": 3, "exercise_ms": 31000, "paused_ms": 4500}).json()
    check("stopping saves stopped, not completed, with breaths done and paused time apart", stopped["status"] == "stopped" and stopped["breaths_done"] == 3 and stopped["paused_ms"] == 4500, stopped["status"])
    check("an invalid length is refused (422)", c.post("/api/sessions", json={"planned_breaths": 7, "cue": "circle", "client_key": "check-key-3"}).status_code == 422, "422")
    check("more breaths than planned is refused", c.patch(f"/api/sessions/{s2}", json={"status": "completed", "breaths_done": 8}).status_code in (409, 422), "refused")
    # ---- Self-report kept apart ----------------------------------------------------------
    fb = c.post(f"/api/sessions/{sid}/feedback", json={"self_report": "not_sure"})
    check("the optional answer is saved in its own table", fb.status_code == 201 and rows("SELECT self_report FROM session_feedback WHERE session_id = ?", sid) == [("not_sure",)], fb.status_code)
    check("the answer does not change the observed record", rows("SELECT status, breaths_done FROM exercise_sessions WHERE session_id = ?", sid) == [("completed", 6)], "unchanged")
    # ---- Preferences ---------------------------------------------------------------------
    prefs = c.get("/api/preferences").json()
    check("starting remembers the last chosen length and cue", prefs["breaths"] == 8 and prefs["cue"] == "text" and "cue" in prefs["remembered"], prefs)
    prefs = c.put("/api/preferences", json={"fewer_words": True}).json()
    check("the person can change a preference directly", prefs["fewer_words"] is True, prefs["fewer_words"])
    # ---- Introduction --------------------------------------------------------------------
    mock_intro = c.get("/api/intro", params={"mode": "mock"}).json()
    check("the mock introduction is labelled mock", mock_intro["source"] == "mock", mock_intro["source"])
    failed_intro = c.get("/api/intro", params={"mode": "fail"}).json()
    check("a failed model gives the fixed introduction, not an error", failed_intro["source"] == "fixed" and failed_intro["text"] == assistant.FIXED_INTRO, failed_intro["source"])
    steps = rows("SELECT role, stage, status FROM messages WHERE conversation_id = ? ORDER BY message_id", failed_intro["conversation_id"])
    check("the failed intro is saved as an error plus the fixed text, never as a model reply", steps == [("user", "question", "ok"), ("tool", "error", "failed"), ("assistant", "intro", "fixed_text")], steps)
    # ---- Questions (RAG) -----------------------------------------------------------------
    before = snapshot()
    ok = c.post("/api/ask", json={"question": "How many sessions did I finish?", "mode": "mock"}).json()
    check("a question about saved sessions is answered from retrieved rows", ok["status"] == "answered" and ok["rows"] == [[1, ok["rows"][0][1]]], ok["rows"])
    trace = [r[0] for r in rows("SELECT stage FROM messages WHERE conversation_id = ? ORDER BY message_id", ok["conversation_id"])]
    check("each step is saved in order: question, proposed, executed, records, answer", trace == ["question", "proposed_sql", "executed_sql", "retrieval_result", "answer"], trace)
    bad = c.post("/api/ask", json={"question": "delete all my sessions", "mode": "mock"}).json()
    check("a model-proposed write query is refused and not run", bad["status"] == "rejected", bad["status"])
    check("the refused write changed nothing", snapshot() == before, "identical")
    calls["n"] = 0
    crisis = c.post("/api/ask", json={"question": "I want to end my life", "mode": "live"}).json()
    check("crisis wording opens Support and makes NO model call", crisis["status"] == "blocked" and crisis["open_support"] and calls["n"] == 0, f"{crisis['status']} calls={calls['n']}")
    blocked = rows("SELECT role, stage, status FROM messages WHERE conversation_id = ? ORDER BY message_id", crisis["conversation_id"])
    check("a blocked question is saved with an error step and no assistant answer", blocked == [("user", "question", "ok"), ("tool", "error", "blocked")], blocked)
    down = c.post("/api/ask", json={"question": "How many sessions did I finish?", "mode": "fail"}).json()
    down_steps = [r[0] for r in rows("SELECT role FROM messages WHERE conversation_id = ?", down["conversation_id"])]
    check("a model outage is reported as failed with no invented reply", down["status"] == "failed" and "assistant" not in down_steps, down_steps)
    off_topic = c.post("/api/ask", json={"question": "what is the weather", "mode": "mock"}).json()
    check("an off-topic question gets an honest 'cannot answer'", off_topic["status"] == "insufficient_data", off_topic["status"])
    check("a too-short question is refused before any work (400 or 422)", c.post("/api/ask", json={"question": "hi"}).status_code in (400, 422), "refused")
    # ---- Retrieval scope -----------------------------------------------------------------
    refused = []
    for sql in ("SELECT * FROM exercise_sessions", "SELECT * FROM messages", "SELECT * FROM my_sessions, exercise_sessions",
                "SELECT name FROM sqlite_master", "UPDATE exercise_sessions SET status = 'completed'",
                "SELECT 1; DELETE FROM preferences", "WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM r) SELECT n FROM r"):
        try:
            retrieval.run_query(sql)
            refused.append(False)
        except retrieval.QueryRejectedError:
            refused.append(True)
    check("base tables, messages, the catalogue, writes, two statements and recursion are all refused", all(refused), refused)
    scoped = retrieval.run_query("SELECT COUNT(*) FROM my_sessions")
    check("the user-scoped view is readable", scoped.rows == ((2,),), scoped.rows)
    check("nothing changed after all the refused queries", snapshot()["exercise_sessions"] == before["exercise_sessions"], "identical")
    # ---- Health and persistence --------------------------------------------------------
    health = c.get("/api/health").json()
    check("health reports key status, never the key", "status" in health["model"] and "AIza" not in json.dumps(health), health["model"]["status"])

with TestClient(main.app) as c2:  # a second app start on the same file: no reseeding, no duplicates
    check("records survive a restart with no duplicates", len(c2.get("/api/sessions").json()["sessions"]) == 2 and len(rows("SELECT * FROM demo_users")) == 1, "2 sessions, 1 user")

llm_client.generate = real_generate
gc.collect()
_tmp.cleanup()
width = max(len(n) for n, _, _ in results)
for name, ok, seen in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {seen}")
failed = sum(1 for _, ok, _ in results if not ok)
print(f"\n{len(results) - failed} of {len(results)} checks passed (mock model, throwaway database)")
sys.exit(1 if failed else 0)

"""Adds four fictional earlier sessions for Alex through the running app's own API, so the Part 3.3
demo has a history to show (usual choice, profile, the reply's facts). Run against a fresh database.

Run with the backend on :8100:  backend\\.venv\\Scripts\\python.exe docs\\evidence\\seed_demo.py
"""

import httpx

API = "http://127.0.0.1:8100/api"
# (breaths, status, breaths done, measured ms, answer or None). All fictional.
SESSIONS = [
    (6, "completed", 6, 60010, "about_the_same"),
    (6, "completed", 6, 60004, "about_the_same"),
    (6, "stopped", 3, 30500, "not_sure"),
    (6, "completed", 6, 60008, None),
]

if httpx.get(f"{API}/profile").json()["sessions"]:
    raise SystemExit("This database already has sessions; seed a fresh one only.")
for i, (breaths, status, done, ms, answer) in enumerate(SESSIONS):
    sid = httpx.post(f"{API}/sessions", json={"planned_breaths": breaths, "cue": "circle", "client_key": f"demo-seed-{i}", "entry_ms": 2400}).json()["session_id"]
    httpx.patch(f"{API}/sessions/{sid}", json={"status": status, "breaths_done": done, "exercise_ms": ms, "paused_ms": 0})
    if answer:
        httpx.post(f"{API}/sessions/{sid}/feedback", json={"self_report": answer})
profile = httpx.get(f"{API}/profile").json()
print({k: profile[k] for k in ("sessions", "completed", "stopped", "usual")})

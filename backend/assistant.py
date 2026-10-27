"""Controller for the model's two jobs: the introduction on Home, and questions about the
person's own saved sessions. The model never runs the exercise, and nothing here can change
the timer, Stop, or the Support panel.

Contracts:

- `intro(mode)` -> dict(text, source, conversation_id). `source` is "model" or "fixed".
  It never raises for a model problem: the fixed text is used and the failure is saved.
- `ask(question, mode)` -> dict(status, answer, proposed_sql, columns, rows, conversation_id,
  open_support). Status is answered, no_match, insufficient_data, rejected, query_failed,
  blocked (crisis wording), or failed (model unavailable). A failed or blocked request is
  saved with an error step and no assistant answer is invented.

`mode` is "live" (Gemini), "mock" (fixed replies, for repeatable checks), or "fail" (always
fails, for demonstrating the failure path). Mock and fail only work when ALLOW_DEMO_MODES=1.
"""

import hashlib
import json
import re

import config
import database as db
import llm_client
import retrieval

FIXED_INTRO = "Breathe in for 4, out for 6. Six breaths, about a minute. Stop whenever you like."
INTRO_MAX_WORDS = 45
ANSWER_MAX_WORDS = 110
MIN_QUESTION, MAX_QUESTION = 3, 300

# Checked before any model call. A word list misses indirect wording and flags some innocent
# text; that is acceptable only because Support is always one tap away regardless of this.
CRISIS_PATTERNS = [
    r"\bkill (?:my ?self|me)\b", r"\bsuicid", r"\bend (?:my|it all|my life)\b", r"\bself[- ]?harm",
    r"\bhurt(?:ing)? my ?self\b", r"\bwant to die\b", r"\boverdose\b", r"\bcut(?:ting)? my ?self\b",
    r"\bno reason to live\b", r"\bcan'?t go on\b",
]
CRISIS_REPLY = (
    "This app can't help with that, and nobody is monitoring it. The Support panel is open with "
    "people you can reach right now. If you are in danger, call 911."
)
BANNED = re.compile(r"diagnos|therap|disorder|you seem|stress level|anxiety level|great job|!", re.I)


class InvalidQuestionError(Exception):
    pass


class DemoModeNotAllowedError(Exception):
    pass


def _load_prompts() -> tuple[dict[str, str], str]:
    raw = config.PROMPT_FILE.read_bytes()
    sections: dict[str, str] = {}
    name = None
    for line in raw.decode("utf-8").splitlines():
        if line.startswith("## "):
            name = line[3:].strip().lower()
            sections[name] = ""
        elif name:
            sections[name] += line + "\n"
    missing = {"purpose", "intro", "query", "answer"} - set(sections)
    if missing:
        raise RuntimeError(f"{config.PROMPT_FILE.name} is missing sections: {', '.join(sorted(missing))}")
    purpose = sections["purpose"].strip()
    prompts = {k: f"{purpose}\n\n{sections[k].strip()}" for k in ("intro", "query", "answer")}
    return prompts, hashlib.sha256(raw).hexdigest()[:12]


PROMPTS, PROMPT_VERSION = _load_prompts()


def _check_mode(mode: str) -> str:
    if mode not in config.MODEL_MODES:
        raise DemoModeNotAllowedError(f"Unknown model mode '{mode}'.")
    if mode != "live" and not config.demo_modes_allowed():
        raise DemoModeNotAllowedError("Mock and fail modes are turned off on this backend.")
    return mode


def _words(text: str) -> int:
    return len(text.split())


# ---- Mocked replies: fixed, so checks are repeatable. Labelled as mock wherever shown. ----

def _mock_generate(stage: str, user: str) -> str:
    if stage == "intro":
        return "Breathe in for 4 and out for 6, following the circle. Your last choice is ready. (mock reply)"
    if stage == "query":
        q = user.lower()
        if "delete" in q or "drop" in q:
            return json.dumps({"sql": "DELETE FROM exercise_sessions", "reason": "mock: unsafe proposal"})
        if "weather" in q:
            return json.dumps({"sql": None, "reason": "mock: not about saved sessions"})
        if "stop" in q:
            sql = "SELECT COUNT(*) AS stopped_sessions FROM my_sessions WHERE status = 'stopped'"
        else:
            sql = "SELECT COUNT(*) AS completed_sessions, MAX(started_at) AS last_started FROM my_sessions WHERE status = 'completed'"
        return json.dumps({"sql": sql, "reason": "mock: counts saved sessions"})
    records = user.split("Records:", 1)[-1].strip()
    return f"From your saved records: {records[:160]} (mock reply)"


def _generate(mode: str, stage: str, system: str, user: str, json_output: bool = False) -> str:
    if mode == "fail":
        raise llm_client.LlmServiceError("demo failure mode")
    if mode == "mock":
        return _mock_generate(stage, user)
    return llm_client.generate(system, user, json_output)


# ---- Introduction ----------------------------------------------------------------------

def _intro_context() -> str:
    prefs = db.get_preferences()
    remembered = {k: prefs[k] for k in prefs["remembered"]} if prefs["remembered"] else "none yet"
    last = db.list_sessions(limit=1)
    last_fact = (
        f"last session: {last[0]['planned_breaths']} breaths, {last[0]['cue']} cue"
        if last else "no sessions saved yet"
    )
    profile = db.get_profile()
    usual = profile["usual"]
    usual_fact = (
        f"usual choice over the last {usual['based_on']} sessions: {usual['breaths']} breaths, {usual['cue']} cue"
        if usual else "no usual choice yet"
    )
    checkin = profile["current_checkin"]
    words = {"steady": "steady", "tense": "a bit tense", "overwhelmed": "overwhelmed"}
    checkin_fact = f"today's check-in, in their own words: '{words[checkin['feeling']]}'" if checkin else "no check-in today"
    return f"Name: Alex. Remembered choices: {remembered}. {last_fact}; {usual_fact}; {checkin_fact}."


def intro(mode: str = "live") -> dict:
    mode = _check_mode(mode)
    conversation_id = db.create_conversation("intro")
    context = _intro_context()
    db.save_message(conversation_id, "user", "question", f"(app request for the Home introduction) {context}", "ok", PROMPT_VERSION)
    try:
        text = _generate(mode, "intro", PROMPTS["intro"], context).strip()
        if not text or _words(text) > INTRO_MAX_WORDS or BANNED.search(text.replace("(mock reply)", "")):
            raise llm_client.LlmBadOutputError("The model's introduction broke a length or wording rule.")
    except llm_client.LlmError as exc:
        db.save_message(conversation_id, "tool", "error", str(exc), "failed", PROMPT_VERSION)
        db.save_message(conversation_id, "assistant", "intro", FIXED_INTRO, "fixed_text", PROMPT_VERSION)
        return {"text": FIXED_INTRO, "source": "fixed", "conversation_id": conversation_id, "note": str(exc)}
    db.save_message(conversation_id, "assistant", "intro", text, "ok", PROMPT_VERSION)
    return {"text": text, "source": "mock" if mode == "mock" else "model", "conversation_id": conversation_id, "note": None}


# ---- Questions about saved sessions (the class SQL RAG pattern) --------------------------

def _parse_proposal(text: str) -> tuple[str | None, str | None]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    try:
        proposal = json.loads(cleaned)
    except ValueError:
        raise llm_client.LlmBadOutputError("The model did not reply with a usable query.") from None
    if not isinstance(proposal, dict):
        raise llm_client.LlmBadOutputError("The model did not reply with a usable query.")
    sql = proposal.get("sql")
    return (sql if isinstance(sql, str) and sql.strip() else None), proposal.get("reason")


def is_crisis_text(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in CRISIS_PATTERNS)


def ask(question: str, mode: str = "live") -> dict:
    question = (question or "").strip()
    if not MIN_QUESTION <= len(question) <= MAX_QUESTION:
        raise InvalidQuestionError(f"Ask a question between {MIN_QUESTION} and {MAX_QUESTION} characters.")
    mode = _check_mode(mode)
    conversation_id = db.create_conversation("question")
    save = lambda role, stage, content, status="ok": db.save_message(conversation_id, role, stage, content, status, PROMPT_VERSION)
    save("user", "question", question)
    result = {"conversation_id": conversation_id, "proposed_sql": None, "reason": None, "columns": [], "rows": [], "open_support": False}

    if is_crisis_text(question):
        save("tool", "error", "Crisis wording matched before any model call. No model request was made.", "blocked")
        return {**result, "status": "blocked", "answer": CRISIS_REPLY, "open_support": True}

    try:
        sql, reason = _parse_proposal(_generate(mode, "query", PROMPTS["query"].replace("<<SCHEMA>>", retrieval.schema_for_model()), question, True))
        result.update(proposed_sql=sql, reason=reason)
        save("assistant", "proposed_sql", json.dumps({"sql": sql, "reason": reason}))
        if sql is None:
            answer = "Your saved sessions can't answer that. " + (reason or "")
            save("assistant", "answer", answer.strip())
            return {**result, "status": "insufficient_data", "answer": answer.strip()}
        try:
            found = retrieval.run_query(sql)
        except retrieval.QueryRejectedError as exc:
            save("tool", "error", f"Query refused, not run: {exc}", "blocked")
            return {**result, "status": "rejected", "answer": f"That query was not allowed, so it was not run and nothing changed. ({exc})"}
        except retrieval.QueryFailedError as exc:
            save("tool", "error", str(exc), "failed")
            return {**result, "status": "query_failed", "answer": "The question could not be looked up. Try asking it another way."}
        save("tool", "executed_sql", sql)
        rows = [list(r) for r in found.rows]
        save("tool", "retrieval_result", json.dumps({"columns": list(found.columns), "rows": rows}, default=str))
        result.update(columns=list(found.columns), rows=rows)
        if not rows or all(v in (None, 0) for v in rows[0]) and len(rows) == 1:
            answer = "No saved sessions match that yet."
            save("assistant", "answer", answer)
            return {**result, "status": "no_match", "answer": answer}
        records = json.dumps([dict(zip(found.columns, r)) for r in rows], default=str)
        answer = _generate(mode, "answer", PROMPTS["answer"], f"Question: {question}\nQuery: {sql}\nRecords: {records}").strip()
        if not answer or _words(answer) > ANSWER_MAX_WORDS or BANNED.search(answer.replace("(mock reply)", "")):
            raise llm_client.LlmBadOutputError("The model's answer broke a length or wording rule.")
    except llm_client.LlmError as exc:
        save("tool", "error", str(exc), "failed")
        return {**result, "status": "failed", "answer": f"The question could not be answered right now. {exc}"}
    save("assistant", "answer", answer)
    return {**result, "status": "answered", "answer": answer}

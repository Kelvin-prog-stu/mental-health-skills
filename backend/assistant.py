"""Controller for the model's two jobs: the introduction on Home, and questions about the
person's own saved sessions. The model never runs the exercise, and nothing here can change
the timer, Stop, or the Support panel.

Contracts:

- `intro(mode)` -> dict(text, source, conversation_id). `source` is "model" or "fixed".
  It never raises for a model problem: the fixed text is used and the failure is saved.
- `reflect(session_id, mode)` -> dict(text, source, conversation_id, records). The reply after
  "How was that?", grounded in that answer and the person's saved sessions, which are read
  with a fixed, app-owned query through the same read-only scoped views as `ask`. Like the
  intro, a model problem gives fixed text for that answer, and the failure is saved.
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

import breathing_tips
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


# The reply after "How was that?" must not turn the person's answer into a claim of effect.
REFLECTION_MAX_WORDS = 85
REFLECTION_BANNED = re.compile(
    r"improv|progress|getting better|feel(?:ing)? better|\bworse\b|calmer than|it work|is working|"
    r"help(?:ed|s|ing) you|well done|proud",
    re.I,
)
SELF_REPORT_WORDS = {"a_bit_calmer": "a bit calmer", "about_the_same": "about the same", "not_sure": "not sure"}
FIXED_REFLECTIONS = {
    "a_bit_calmer": "You said a bit calmer. It's saved with this session, and your sessions are in History whenever you want them.",
    "about_the_same": "You said about the same. That's a fine answer, and it's saved with this session.",
    "not_sure": "You said not sure. That's a fine answer, and it's saved with this session.",
}
# Fixed by the app, not proposed by the model, and still run through the read-only scoped views.
REFLECTION_QUERY = (
    "SELECT s.session_id, s.planned_breaths, s.cue, s.status, s.breaths_done, s.exercise_ms, "
    "s.started_at, f.self_report FROM my_sessions s LEFT JOIN my_feedback f ON f.session_id = s.session_id "
    "ORDER BY s.session_id DESC LIMIT 50"
)


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
    missing = {"purpose", "intro", "query", "answer", "reflection"} - set(sections)
    if missing:
        raise RuntimeError(f"{config.PROMPT_FILE.name} is missing sections: {', '.join(sorted(missing))}")
    purpose = sections["purpose"].strip()
    prompts = {k: f"{purpose}\n\n{sections[k].strip()}" for k in ("intro", "query", "answer", "reflection")}
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
    if stage == "reflection":
        answer = re.search(r"answer to this session: '([^']+)'", user)
        count = re.search(r"Saved sessions in total: (\d+)", user)
        suggestion = re.search(r"Suggestion chosen by the app: (.+)", user)
        return (f"You said {answer.group(1) if answer else 'something'}. You have "
                f"{count.group(1) if count else 'some'} sessions saved. {suggestion.group(1) if suggestion else ''} (mock reply)")
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


# ---- Reply after "How was that?" -------------------------------------------------------

def _reflection_context(session: dict, plan: dict) -> str:
    profile = db.get_profile()
    usual = profile["usual"]
    checkin = profile["current_checkin"]
    words = {"steady": "steady", "tense": "a bit tense", "overwhelmed": "overwhelmed"}
    tips = "\n".join(f"- ({SOURCE_SHORT[t['source']]}) {t['text']}" for t in plan["tips"])
    return "\n".join([
        f"Name: Alex. Their answer to this session: '{SELF_REPORT_WORDS[session['self_report']]}'.",
        "Facts from their saved sessions:",
        *(f"- {f}" for f in plan["facts"]),
        "- Usual choice: " + (f"{usual['breaths']} breaths, {usual['cue']} cue" if usual else "none yet") + ".",
        "- Today's check-in, their own words: " + (f"'{words[checkin['feeling']]}'" if checkin else "none") + ".",
        f"Suggestion chosen by the app: {plan['suggestion']}",
        "Reviewed tips (name the source if you use one):",
        tips,
    ])


SOURCE_SHORT = {"nhs": "NHS", "cleveland": "Cleveland Clinic", "balban": "2023 Stanford study"}


def _numbers_grounded(text: str, context: str) -> bool:
    """Every number in the reply must appear in the facts it was given."""
    known = set(re.findall(r"\d+(?:\.\d+)?", context))
    return all(n in known for n in re.findall(r"\d+(?:\.\d+)?", text))


def reflect(session_id: int, mode: str = "live") -> dict:
    mode = _check_mode(mode)
    session = db.get_session(session_id)
    if not session["self_report"]:
        raise ValueError("Answer 'How was that?' before asking for a reply.")
    conversation_id = db.create_conversation("question")
    save = lambda role, stage, content, status="ok": db.save_message(conversation_id, role, stage, content, status, PROMPT_VERSION)
    save("user", "question", f"(app request: reply to the 'How was that?' answer for session {session_id})")
    word = SELF_REPORT_WORDS[session["self_report"]]
    plan = None
    try:
        found = retrieval.run_query(REFLECTION_QUERY)
        rows = [dict(zip(found.columns, r)) for r in found.rows]
        save("tool", "executed_sql", REFLECTION_QUERY)
        save("tool", "retrieval_result", json.dumps({"columns": list(found.columns), "rows": [list(r) for r in found.rows]}, default=str))
        plan = breathing_tips.build(session, rows)
        context = _reflection_context(session, plan)
        text = _generate(mode, "reflection", PROMPTS["reflection"], context).strip()
        plain = text.replace("(mock reply)", "")
        if not text or _words(text) > REFLECTION_MAX_WORDS or BANNED.search(plain) or REFLECTION_BANNED.search(plain):
            raise llm_client.LlmBadOutputError("The model's reply broke a length or wording rule.")
        if not _numbers_grounded(plain, context):
            raise llm_client.LlmBadOutputError("The model's reply used a number that is not in the saved records or tips.")
    except (llm_client.LlmError, retrieval.QueryRejectedError, retrieval.QueryFailedError) as exc:
        # The fixed text still carries the app's own suggestion, so a model failure loses only the wording.
        fixed = f"You said {word}. {plan['suggestion']}" if plan else FIXED_REFLECTIONS[session["self_report"]]
        save("tool", "error", str(exc), "failed")
        save("assistant", "answer", fixed, "fixed_text")
        return {"text": fixed, "source": "fixed", "conversation_id": conversation_id, "records": [],
                "action": plan["action"] if plan else None, "sources": plan["sources"] if plan else [], "note": str(exc)}
    save("assistant", "answer", text)
    return {
        "text": text,
        "source": "mock" if mode == "mock" else "model",
        "conversation_id": conversation_id,
        "records": [r["session_id"] for r in rows],
        "action": plan["action"],
        "sources": plan["sources"],
        "note": None,
    }


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

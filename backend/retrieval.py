"""Runs a model-proposed SQL query safely, limited to the demo user's own records.

Adapted from my Assignment 2 project (expedia-lite, retrieval_controller.py). The model
proposes SQL as text; this module decides whether it runs. Layers that all have to agree:

1. **A read-only connection** (`mode=ro`, then `PRAGMA query_only`).
2. **User scope.** Before the query, the connection gets three TEMP views filtered to the
   demo user: `my_sessions`, `my_feedback`, `my_preferences`. The model is only told about
   these views, and the authorizer only lets the base tables be read *through* them, so a
   query cannot reach another user's rows or the conversation messages.
3. **SQLite's authorizer:** SELECT, reads through the views, and a short list of plain
   functions. Everything else (writes, PRAGMA, ATTACH, other tables, the catalogue,
   recursion) is refused while the statement is prepared, before anything runs.
4. **Shape and bounds:** one statement, SELECT or WITH, no comments, at most MAX_ROWS rows,
   a 3 second limit.

Contract for `run_query(sql)`: returns a `Retrieval` (columns, rows, truncated). Raises
`QueryRejectedError` when not allowed (not run) and `QueryFailedError` when allowed but broken.
"""

import sqlite3
import time
from dataclasses import dataclass

import config
from models import DEMO_USER_ID

VIEWS = {
    "my_sessions": (
        "SELECT session_id, planned_breaths, cue, started_at, ended_at, status, breaths_done, "
        "exercise_ms FROM main.exercise_sessions WHERE user_id = :user"
    ),
    "my_feedback": (
        "SELECT f.session_id, f.self_report, f.created_at FROM main.session_feedback f "
        "JOIN main.exercise_sessions s ON s.session_id = f.session_id WHERE s.user_id = :user"
    ),
    "my_preferences": "SELECT key, value, updated_at FROM main.preferences WHERE user_id = :user",
}
BASE_TABLES = {"exercise_sessions", "session_feedback", "preferences"}
ALLOWED_FUNCTIONS = frozenset(
    {
        "count", "sum", "min", "max", "avg", "total", "round", "abs", "coalesce", "ifnull",
        "nullif", "iif", "lower", "upper", "length", "trim", "substr", "date", "datetime",
        "julianday", "strftime", "cast", "like", "printf",
    }
)
MAX_ROWS = 50
MAX_SQL_CHARACTERS = 2000
TIME_LIMIT_SECONDS = 3.0
_SELECT, _READ, _FUNCTION = 21, 20, 31


class QueryRejectedError(Exception):
    """The query is not allowed. It was not run."""


class QueryFailedError(Exception):
    """The query is allowed but could not run."""


@dataclass(frozen=True)
class Retrieval:
    columns: tuple[str, ...]
    rows: tuple[tuple, ...]
    truncated: bool


def _scoped_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH.resolve().as_uri() + "?mode=ro", uri=True)
    # The user id is ours, not the model's, and is inlined only after this check.
    if not DEMO_USER_ID.replace("-", "").isalnum():
        raise RuntimeError("Unexpected user id.")
    for name, body in VIEWS.items():
        conn.execute(f"CREATE TEMP VIEW {name} AS {body.replace(':user', repr(DEMO_USER_ID))}")
    conn.execute("PRAGMA query_only = ON")
    return conn


def _check_shape(sql: object) -> str:
    if not isinstance(sql, str) or not sql.strip():
        raise QueryRejectedError("The proposed query was empty.")
    statement = sql.strip().rstrip(";").strip()
    if len(statement) > MAX_SQL_CHARACTERS:
        raise QueryRejectedError("The proposed query is too long.")
    if "--" in statement or "/*" in statement:
        raise QueryRejectedError("Comments are not allowed in a proposed query.")
    if ";" in statement:
        raise QueryRejectedError("Only one statement is allowed.")
    if statement.split(None, 1)[0].lower() not in ("select", "with"):
        raise QueryRejectedError("Only a SELECT query is allowed.")
    return statement


def _authorizer(denials: list[str]):
    def authorize(action, arg1, arg2, database, source):
        if action == _SELECT:
            return sqlite3.SQLITE_OK
        if action == _READ:
            if database == "temp" and arg1 in VIEWS:
                return sqlite3.SQLITE_OK
            if arg1 in BASE_TABLES and source in VIEWS:
                return sqlite3.SQLITE_OK
            denials.append(f"Reading '{arg1}' is not allowed. Only {', '.join(VIEWS)} can be read.")
            return sqlite3.SQLITE_DENY
        if action == _FUNCTION:
            if (arg2 or "").lower() in ALLOWED_FUNCTIONS:
                return sqlite3.SQLITE_OK
            denials.append(f"The function '{arg2}' is not allowed.")
            return sqlite3.SQLITE_DENY
        denials.append("Only reading is allowed. This assistant cannot change anything.")
        return sqlite3.SQLITE_DENY

    return authorize


def run_query(sql: object) -> Retrieval:
    statement = _check_shape(sql)
    denials: list[str] = []
    conn = _scoped_connection()
    try:
        conn.set_authorizer(_authorizer(denials))
        deadline = time.monotonic() + TIME_LIMIT_SECONDS
        conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 20_000)
        try:
            cursor = conn.execute(statement)
            fetched = cursor.fetchmany(MAX_ROWS + 1)
            columns = tuple(c[0] for c in cursor.description or ())
        except sqlite3.DatabaseError as exc:
            if denials:
                raise QueryRejectedError(denials[0]) from None
            if "interrupted" in str(exc):
                raise QueryFailedError("The query took too long and was stopped.") from None
            raise QueryFailedError(f"The query could not run: {exc}.") from None
        except sqlite3.Warning:
            raise QueryRejectedError("Only one statement is allowed.") from None
    finally:
        conn.close()
    if denials:
        raise QueryRejectedError(denials[0])
    return Retrieval(columns=columns, rows=tuple(tuple(r) for r in fetched[:MAX_ROWS]), truncated=len(fetched) > MAX_ROWS)


def schema_for_model() -> str:
    """What the model is told it may query: the three views and what their columns mean."""
    return "\n".join([
        "my_sessions(session_id, planned_breaths, cue, started_at, ended_at, status, breaths_done, exercise_ms)",
        "  planned_breaths is 6 or 8. cue is circle or text. started_at and ended_at are ISO 8601 UTC text.",
        "  status is in_progress, completed or stopped. breaths_done is how many breaths were finished.",
        "  exercise_ms is the measured length of the exercise in milliseconds.",
        "my_feedback(session_id, self_report, created_at)",
        "  self_report is a_bit_calmer, about_the_same or not_sure: the person's own optional answer.",
        "my_preferences(key, value, updated_at)",
        "  key is breaths, cue or fewer_words; value is what the person last chose.",
    ])

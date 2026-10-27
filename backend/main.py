"""FastAPI routes. Each one validates input, makes one controller call, and returns the result.

Run from backend/:  .venv\\Scripts\\python.exe -m uvicorn main:app --port 8100
"""

import sqlite3
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import assistant
import config
import database as db
import llm_client

ModelMode = Literal["live", "mock", "fail"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Breathe 60 API", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5180"], allow_methods=["*"], allow_headers=["*"])


class SessionStart(BaseModel):
    planned_breaths: Literal[6, 8]
    cue: Literal["circle", "text"]
    entry_ms: int | None = Field(default=None, ge=0, le=3_600_000)
    client_key: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


class SessionFinish(BaseModel):
    status: Literal["completed", "stopped"]
    breaths_done: int = Field(ge=0, le=8)
    exercise_ms: int | None = Field(default=None, ge=0, le=3_600_000)
    paused_ms: int = Field(default=0, ge=0, le=3_600_000)


class Feedback(BaseModel):
    self_report: Literal["a_bit_calmer", "about_the_same", "not_sure"]


class PreferenceUpdate(BaseModel):
    breaths: Literal[6, 8] | None = None
    cue: Literal["circle", "text"] | None = None
    fewer_words: bool | None = None


class CheckIn(BaseModel):
    feeling: Literal["steady", "tense", "overwhelmed"]


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=300)
    mode: ModelMode = "live"


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "records": db.record_counts(),
        "model": {"provider": "gemini", "name": config.gemini_model(), "status": config.key_status()},
        "demo_modes": config.demo_modes_allowed(),
        "prompt_version": assistant.PROMPT_VERSION,
    }


@app.get("/api/intro")
def intro(mode: ModelMode = "live") -> dict:
    return assistant.intro(mode)


@app.post("/api/sessions", status_code=201)
def start_session(body: SessionStart):
    session, created = db.start_session(body.planned_breaths, body.cue, body.entry_ms, body.client_key)
    return session if created else JSONResponse(status_code=200, content=session)


@app.patch("/api/sessions/{session_id}")
def finish_session(session_id: int, body: SessionFinish) -> dict:
    return db.finish_session(session_id, body.status, body.breaths_done, body.exercise_ms, body.paused_ms)


@app.post("/api/sessions/{session_id}/feedback", status_code=201)
def feedback(session_id: int, body: Feedback) -> dict:
    return db.save_feedback(session_id, body.self_report)


@app.get("/api/sessions")
def sessions(limit: int = 50) -> dict:
    return {"sessions": db.list_sessions(min(max(limit, 1), 200))}


@app.get("/api/preferences")
def preferences() -> dict:
    return db.get_preferences()


@app.put("/api/preferences")
def update_preferences(body: PreferenceUpdate) -> dict:
    return db.set_preferences(body.breaths, body.cue, body.fewer_words)


@app.post("/api/checkins", status_code=201)
def checkin(body: CheckIn) -> dict:
    return db.save_checkin(body.feeling)


@app.get("/api/profile")
def profile() -> dict:
    return db.get_profile()


@app.post("/api/ask")
def ask(body: Question) -> dict:
    return assistant.ask(body.question, body.mode)


@app.get("/api/conversations")
def conversations(limit: int = 30) -> dict:
    return {"conversations": db.list_conversations(min(max(limit, 1), 100))}


def _error(status: int, code: str):
    async def handle(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status, content={"error": {"code": code, "message": str(exc)}})

    return handle


app.add_exception_handler(db.NotFoundError, _error(404, "not_found"))
app.add_exception_handler(db.ConflictError, _error(409, "already_finished"))
app.add_exception_handler(ValueError, _error(422, "invalid"))
app.add_exception_handler(assistant.InvalidQuestionError, _error(400, "invalid_question"))
app.add_exception_handler(assistant.DemoModeNotAllowedError, _error(403, "demo_mode_off"))
app.add_exception_handler(llm_client.LlmError, _error(502, "model_failed"))


@app.exception_handler(sqlite3.Error)
async def storage_error(request: Request, exc: sqlite3.Error) -> JSONResponse:
    # Logged details stay on the server; the person gets an honest, plain message.
    print(f"storage error: {type(exc).__name__}: {exc}")
    return JSONResponse(status_code=500, content={"error": {"code": "storage_error", "message": "Your data could not be read or saved."}})

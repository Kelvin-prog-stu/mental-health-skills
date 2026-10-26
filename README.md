# Mental Health Skills App

IST 402 - Assignment 3 (Kelvin Asiedu). Working name: **Breathe 60**.

## Purpose

Build a local application that lets someone practice a short skill, stop at any
point, and return to useful session history. The interface should ask for little
reading or typing and keep the person in control. A conversational model can
help introduce the skill and explain the app, using reviewed content and saved
context.

This is a coursework prototype, tested only with fictional scenarios. It must
not diagnose, provide therapy, imply human monitoring, or be offered as a real
mental health support service.

## Status (Part 3.2, 2026-10-26)

A working version: someone can complete paced breathing in the running interface,
stop at any moment, open Support from every screen, and look back at saved sessions.
The model writes the Home introduction and answers questions about saved sessions.
What is finished and what is not: [docs/verification.md](docs/verification.md) and
[handoffs/current.md](handoffs/current.md). Design and its changes since Part 3.1:
[docs/design-pipeline.md](docs/design-pipeline.md).

## Run it (Windows, checked on this machine on 2026-10-26)

Requirements: Python 3.12, Node.js 20 or newer, Google Chrome (only for the browser check).

Backend, from `backend/`:

```
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Put a Gemini key after `GEMINI_API_KEY=` in `backend/.env` (it is ignored by Git). Without a
key the app still runs: the introduction falls back to fixed text and questions report that
the model is not configured. Then start it:

```
.venv\Scripts\python.exe -m uvicorn main:app --port 8100
```

Frontend, from `frontend/`:

```
npm install
npm run dev
```

Open http://localhost:5180. The database is created at `data/app.sqlite3` on first start
(fictional data only; not committed). Stop either server with Ctrl+C.

Checks:

- `backend\.venv\Scripts\python.exe backend\checks\check_app.py`: 28 backend checks with the
  mocked model on a throwaway database. No key or network needed.
- `node docs\evidence\e2e_check.mjs <output folder>`: drives the running app in headless
  Chrome with the mocked model and saves screenshots and a log (add `--live` for the live model).

The **Demo controls** at the bottom of the page switch the model between Live, Mock (fixed
replies), and Fail (a simulated outage). They exist for testing with fictional scenarios and
only work when `ALLOW_DEMO_MODES=1` is set in `backend/.env`.

## Design guidelines

Class principles carried into the design:

- Keep the guided skill within 90 seconds at its intended pace. Show one clear
  action at a time and keep reading, typing, and configuration demands low.
- Let people start, stop, skip, and change their choices. Keep support information
  visible and usable independently of model responses.
- Use calm, readable language, sufficient contrast, visible keyboard focus,
  a narrow-screen layout, and an alternative to motion.
- Make personalization understandable and changeable. Keep self-report,
  observed behavior, and interpretation distinct; clicks do not establish an
  emotional state or diagnosis.
- Explain how a design choice follows from a class finding, what alternative
  I considered, and what tradeoff I accepted. Check the running result later.

My project-specific decisions (the reasoning is in `docs/design-pipeline.md`):

- **Chosen skill and fictional user/task:** paced breathing, 4 seconds in and
  6 seconds out. Six cycles take 60 seconds; an eight-cycle option takes 80.
  Fictional user: Alex, a student with a few minutes between classes, who opens
  the app on a phone or laptop and wants to slow down before the next thing.
- **Main interaction flow and user controls:** one screen with one main button,
  "Start breathing (60 s)". The exercise screen shows only the pacing cue, the
  current phase in words, and Stop. Stop works at any moment, needs no
  confirmation, and costs nothing. A Support button is in the top bar of every
  screen. After the exercise: one optional tap ("How was that?") and a way home.
- **Interface guidelines and their class/research rationale:** at most one
  primary action per screen (D2); no typing needed to do the skill (D3); muted
  colors, no flashing, plain words such as "Breathe in" and "Breathe out" (D6);
  the support route never leaves the top bar (R2, D4); leaving is never
  questioned or scored (R3); the length and cue are offered, never forced (R4);
  a text-only cue replaces the animation when the system asks for reduced motion
  or the person picks it.
- **Model's role, saved context, and useful personalization:** the model writes
  a one or two sentence introduction before the exercise, and answers optional
  questions about the person's own saved sessions afterwards, using the class's
  SQL retrieval pattern over their records. It never speaks during the exercise
  and cannot change the timer, the steps, Stop, or Support. The app remembers the
  last length and cue the person chose and offers them as "Same as last time",
  with a visible way to change (D5).
- **Alternative designs and reasons for the selected direction:** a skill menu
  (rejected: D2, D3), a chat-first app where the model leads the exercise
  (rejected: timing and safety must not depend on the model), automatic
  "distress detection" from clicks (rejected: the class readings show clicks do
  not establish emotional state). Details in the design notes.

## Technology and separation

- Frontend: Vue with JavaScript, HTML, and CSS. It presents the interface,
  responds to input, and sends HTTP requests to the backend. Node.js provides
  the frontend development tools.
- Backend: Python with FastAPI. It exposes the API, validates requests, applies
  business rules, calls the conversational model, and reads/writes the database.
- Database: SQLite. The planned database is `data/app.sqlite3`. Only the Python
  backend accesses it; the frontend receives data through the API.

The application runs on localhost. Planned model provider: Gemini, as in my
Assignment 2 chatbot, with mocked responses for routine checks.

## Secrets and APIs

Store model-provider API keys and other secrets in `backend/.env`. Keep this
file out of Git with `.gitignore` before adding credentials. Provide a
`backend/.env.example` containing variable names and empty or dummy values so
another developer knows what to configure. The backend must explicitly load its
configuration; placing a file in the folder does not load it automatically.
Never put private keys in Vue code, browser-exposed environment variables,
API responses, logs, screenshots, prompts, or Figma.

Vue calls our FastAPI endpoints using HTTP and JSON. FastAPI validates requests,
calls the external model API, and reads or writes SQLite. Each endpoint's input,
response, and failure behavior is planned in `docs/design-pipeline.md`. Use
finite timeouts, clear loading and failure states, and a bounded number of
provider calls. A configured key, a mocked response, and a successful live API
call are different checks. Ordinary history browsing should not require a
model call.

## Conversations, RAG, and data views

Save submitted user messages and actual model replies in SQLite, linked by a
conversation ID. Keep a message ID, role, content, timestamp, and request status
so the app can reconstruct the conversation in order. Store exercise outcomes
and preferences in related records. A failed model request must not create a
fabricated reply, and a failed database write must not appear as a successful
save. Saved records should survive refresh and backend restart without duplicates.

Retrieval-augmented generation (RAG) follows the SQL-based pattern from class:
the model proposes a read-only query over the person's own records, FastAPI
checks and runs it with limits, and a second model call answers from the rows
it returned. The model never connects to SQLite. Details and the planned tables
are in `docs/design-pipeline.md`.

## Project folders

```text
project-root/
|-- README.md            Project purpose and design guidelines
|-- AGENTS.md            Instructions for the coding agent
|-- AI-USE.md            Tools, models, and the AI-use evidence log
|-- .gitignore           Local files to exclude from Git
|-- frontend/            Vue interface (App.vue, components/, api.js, support.js)
|-- backend/             FastAPI (main.py), models.py, database.py, assistant.py, retrieval.py, llm_client.py
|-- data/                Local SQLite database and fictional fixtures
|-- docs/
|   |-- design-pipeline.md  Architecture, behavior, and design decisions
|   |-- design/             Screen sketch and flow
|   `-- verification.md     Checks to run and evidence of what happened
|-- prompts/             Reusable instructions given to the agent
|-- handoffs/current.md  Current state and next step
`-- reports/             One report.md per assignment part
```

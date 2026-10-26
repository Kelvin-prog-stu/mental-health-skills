# Verification

**MOCK** means the model was replaced by fixed replies (repeatable, no network). **LIVE** means
real requests to Gemini `gemini-3.5-flash-lite`. All data is fictional (demo user `alex-demo`).

## Part 3.2 (2026-10-26)

### Backend checks, MOCK, throwaway database

`backend\.venv\Scripts\python.exe backend\checks\check_app.py`: **28 of 28 passed.** The
check replaces the live client with one that fails the run if called, so a live call cannot
slip in. Highlights: a retried start with the same `client_key` returns the same row; finishing
twice is refused (409); stopped and completed are saved differently with breaths done and
paused time apart; the optional answer lives in its own table and does not change the observed
record; starting remembers the length and cue; a failed model gives the fixed introduction and
is saved as `error` then `fixed_text`, never as a model reply; a question is saved step by step
(question, proposed SQL, executed SQL, records, answer); a model-proposed `DELETE` is refused
and the tables are unchanged; crisis wording is blocked with **zero** model calls; a model
outage is saved as failed with no assistant row; base tables, `messages`, the catalogue,
writes, two statements and recursion are all refused by the retrieval guard while the
user-scoped view is readable; a second app start keeps the records with no duplicates.

### Browser checks: the real interface in headless Chrome

Script: [e2e_check.mjs](evidence/e2e_check.mjs). MOCK run log and screenshots:
[mock-run/](evidence/mock-run/). LIVE run (history and questions): [live-run/](evidence/live-run/).

| # | Input or action | Expected | Observed | Evidence |
| --- | --- | --- | --- | --- |
| 1 | Open Home, press Enter | Start is focused; Enter starts; Stop gets focus | Start focused; exercise started; Stop focused | mock log `home`, `exercise-in`; `01-home.png` |
| 2 | Let 6 breaths run | "Breathe in" then "Breathe out"; ends on "That was 6 breaths." within 90 s | Ended at **60.0 s** measured by the app; the check's own clock saw 60.06 s | `02-exercise-inhale.png`, `03-done.png` |
| 3 | Tap "Not sure" | Saved as the person's answer | "Saved: Not sure"; row in `session_feedback` | `db-inspection.txt` |
| 4 | Text cue, open Support at breath 2, wait 4 s | Exercise pauses, panel focused, counter holds | "Breath 2 of 6 · paused" before and after 4 s; focus on the panel heading | `04-support-paused.png` |
| 5 | Resume, then Stop | Continues; Stop ends at once; saved as stopped | "Stopped after 2 breaths. That is fine." Measured 21.7 s plus 4.5 s paused, reported apart | `05-text-cue.png`, `06-stopped.png` |
| 6 | Model mode Fail, open Home | Fixed introduction; Start and Support still work | Fixed text labelled "Fixed text"; Support lists all four entries | `07-model-fail-home.png` |
| 7 | History | Sessions from SQLite, completed and stopped shown differently | Rows match the database exactly (see below) | `08-history.png` |
| 8 | Ask "How many sessions did I finish, and when was the last one?" | Answer from the rows; trace saved | Answered from `[[1, ...]]` (MOCK and LIVE) | `09-ask-answered.png` (both runs) |
| 9 | Ask "I want to end my life" | No model call; Support opens; fixed reply | Status blocked; Support panel open (MOCK and LIVE) | `10-crisis-input.png` |
| 10 | Ask "delete all my sessions" (MOCK proposes a DELETE) | Refused, not run | "That query was not allowed, so it was not run and nothing changed." | mock log `ask-write` |
| 11 | 375 x 740 screen, start | Stop and Support visible without scrolling | Both within the viewport | `11-narrow-exercise.png` |
| 12 | Backend stopped, open Home, start, open Support, stop | Fixed intro; exercise runs; Support works; honest "not saved" | All four observed; "This session was not saved. The app could not reach its backend." | `12-backend-down-not-saved.jpg` |
| 13 | Restart the backend, `GET /api/sessions` | The same sessions, no duplicates | Sessions 1 to 3 unchanged after restart | command output in the Part 3.2 report |

### Database inspection (read-only)

[db-inspection.txt](evidence/db-inspection.txt): read-only queries of `data/app.sqlite3`.
Session 1 is `completed`, 6 breaths, `exercise_ms` 60006, answer `not_sure`; the History row
shows "Completed, 60.0 s, Not sure". Session 2 is `stopped`, 2 breaths, 21659 ms, 4500 ms
paused; History shows "Stopped after 2, 21.7 s". The live question's conversation has five
saved steps in order with the same prompt version, and the crisis conversation has only the
question and a `blocked` error step.

### Live model

[live-model-calls.md](evidence/live-model-calls.md): three live questions and an introduction,
with the query, rows and answer for each, compared with the database.

### Measured timing

| Measure | Value | How |
| --- | --- | --- |
| Guided sequence, 6 breaths, no pause | 60.0 s (60006 ms saved) | App clock (`performance.now`), first "Breathe in" to the final line |
| Same, with a 5 s Support pause (demo video) | 60.0 s plus 5.0 s paused, reported apart | App clock |
| App delays inside the sequence | none observed | Nothing in the sequence waits on the network |
| Entry time (Home shown to Start) | 0.1 to 0.25 s in the scripted runs | `entry_ms`; a script presses Start at once, so this says nothing about a person. A human entry time has not been measured |

### Not verified yet

A clean checkout on another machine; a screen reader; Firefox or Safari; a real phone; a
human's entry time; the browser's handling of the request sent when a tab closes mid-exercise.

## Part 3.1 (2026-10-15)

Design only: the timing arithmetic (60 s and 80 s), that `backend/.env` and the database were
ignored by Git before either existed, and that the sketch renders.

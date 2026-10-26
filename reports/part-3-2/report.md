# Assignment 3, Part 2: Working Application and Safety (Breathe 60)

Kelvin Asiedu, IST 402. Submitted 2026-10-26.

## Project access

- Repository: https://github.com/Kelvin-prog-stu/mental-health-skills (public)
- Submitted commit: `70f1a76f68d8b442d26f594ba5bc868176b442c8` on `main` (the merge of branch `part-3-2`). This report was added
  in the commit after it and changes nothing else.
- Run it: [README.md](https://github.com/Kelvin-prog-stu/mental-health-skills/blob/70f1a76f68d8b442d26f594ba5bc868176b442c8/README.md), section "Run it". Backend on port 8100, frontend on
  5180, Gemini key in `backend/.env` (ignored by Git; `backend/.env.example` lists the names).
  Without a key the app still runs and says the model is not configured.

| Evidence | Link |
| --- | --- |
| Demo video, 2:08, captioned, no audio | [docs/demo/a3-part2-demo.mp4](https://github.com/Kelvin-prog-stu/mental-health-skills/blob/70f1a76f68d8b442d26f594ba5bc868176b442c8/docs/demo/a3-part2-demo.mp4) |
| Verification record (expected versus observed) | [docs/verification.md](https://github.com/Kelvin-prog-stu/mental-health-skills/blob/70f1a76f68d8b442d26f594ba5bc868176b442c8/docs/verification.md) |
| Browser screenshots and logs, MOCK model | [docs/evidence/mock-run/](https://github.com/Kelvin-prog-stu/mental-health-skills/blob/70f1a76f68d8b442d26f594ba5bc868176b442c8/docs/evidence/mock-run/) |
| Browser screenshots and log, LIVE model | [docs/evidence/live-run/](https://github.com/Kelvin-prog-stu/mental-health-skills/blob/70f1a76f68d8b442d26f594ba5bc868176b442c8/docs/evidence/live-run/) |
| Live model calls compared with the database | [docs/evidence/live-model-calls.md](https://github.com/Kelvin-prog-stu/mental-health-skills/blob/70f1a76f68d8b442d26f594ba5bc868176b442c8/docs/evidence/live-model-calls.md) |
| Read-only database inspection | [docs/evidence/db-inspection.txt](https://github.com/Kelvin-prog-stu/mental-health-skills/blob/70f1a76f68d8b442d26f594ba5bc868176b442c8/docs/evidence/db-inspection.txt) |
| Backend checks (28, MOCK) | [backend/checks/check_app.py](https://github.com/Kelvin-prog-stu/mental-health-skills/blob/70f1a76f68d8b442d26f594ba5bc868176b442c8/backend/checks/check_app.py) |
| Design, endpoints as built, and changes since Part 3.1 | [docs/design-pipeline.md](https://github.com/Kelvin-prog-stu/mental-health-skills/blob/70f1a76f68d8b442d26f594ba5bc868176b442c8/docs/design-pipeline.md), section 13 |
| The model's instructions | [prompts/breathing-guide.md](https://github.com/Kelvin-prog-stu/mental-health-skills/blob/70f1a76f68d8b442d26f594ba5bc868176b442c8/prompts/breathing-guide.md) |
| AI use and evidence log | [AI-USE.md](https://github.com/Kelvin-prog-stu/mental-health-skills/blob/70f1a76f68d8b442d26f594ba5bc868176b442c8/AI-USE.md) |

## What is complete

Someone can complete paced breathing in the running interface: one tap (or Enter) starts six
breaths, 4 seconds in and 6 out, with a circle cue or a text-only cue for reduced motion. Stop
works at every moment with no confirmation. A **Support** button sits in the top bar of every
screen; it opens static, verified crisis information and pauses the exercise until Resume.
Each session is saved in SQLite with its measured length, and History shows completed and
stopped sessions differently. The app remembers the last length and cue and offers them as
"Same as last time", with Change beside it.

| Part 3.2 requirement | Where it is shown |
| --- | --- |
| Complete a skill through the running interface | Video 0:12 to 1:17; verification rows 1 and 2 |
| The model's contribution | Home introduction written by the live model (video 0:00); questions about saved sessions answered from retrieved rows (video 1:28; `live-model-calls.md`) |
| Conversation and session persistence in SQLite | `db-inspection.txt` matched to the API and History; records survive a backend restart (row 13); 28 backend checks |
| Measured exercise duration | 60.0 s for six breaths, measured by the app from the first "Breathe in" to the final line, saved as `exercise_ms` 60006. With a Support pause: 60.0 s plus 5.0 s paused, reported separately. Entry time is saved separately as `entry_ms` |
| Independent crisis-support route | Static content in the page; works with the model failing (row 6) and with the backend stopped (row 12); opens on crisis wording without any model call (row 9) |
| What happens when a request fails | Model outage: fixed introduction, honest "could not be answered right now", saved as failed with no invented reply (video 1:45; row 6). Backend down: the exercise still runs and says it was not saved (row 12) |
| What happens when the user leaves | Stop: saved as stopped with breaths done (video 1:57; row 5). Support: pauses. Hidden tab: pauses with Resume |

## Timing (R1: no more than 90 seconds)

| Measure | Planned | Observed |
| --- | --- | --- |
| Six breaths, first instruction to final line | 60 s | 60.0 s (app clock); the check's own clock saw 60.06 s |
| Eight breaths | 80 s | not run in a recorded check |
| App delays inside the sequence | 0 s: the timer runs in the browser and nothing waits on the network | none observed |
| Pauses for Support | excluded | reported apart (4.5 s and 5.0 s in two runs) |
| Entry time | about 2 to 5 s for a person (assumption) | 0.1 to 0.25 s in scripted runs, which says nothing about a person; a human entry time is not yet measured |

Assumptions: the person does not have to respond during the sequence, so there is no response
time in it. Nothing forces the person to finish or to leave when it ends.

## The model's role and limits

The model has two jobs, both outside the exercise. **Before:** one or two sentences on Home,
from a reviewed description of the skill and the person's remembered choices (live example:
"Your last choice, the text cue, is ready. Breathe in for a count of 4, breathe out for a
count of 6, and repeat."). **After:** questions about the person's own saved sessions, using
the class SQL retrieval pattern. The model proposes one query; the backend checks it and runs
it on a read-only connection that can only read three views filtered to the demo user; a
second call answers from the returned rows only. The app checks each reply's length and
wording and falls back to fixed text if a rule is broken. The model cannot change the timer,
the steps, Stop, or Support, and never sees the conversation messages table. Asked "Did
breathing fix my anxiety?", the live model wrote no query, and the app answered that the saved
sessions cannot answer that.

**Crisis-related input (deliberate decision):** the question box is the only free text. Before
any model call, the backend checks the text against a short list of crisis phrases. On a
match it makes no model call, returns a fixed message, and the interface opens Support. The
check counted zero model calls (backend check 19). A word list misses indirect wording and
catches some innocent text; that is acceptable only because Support is one tap away on every
screen regardless.

## What the evidence shows

- **Backend, MOCK:** 28 of 28 checks on a throwaway database, with any live call set to fail
  the run.
- **Browser, MOCK and LIVE:** 13 checks of the real interface in headless Chrome, with
  screenshots. Rows 1 to 13 in `docs/verification.md`.
- **Database:** read-only queries match the API and History for the same sessions and
  conversations, by id.
- **Restart:** after stopping and restarting the backend, `GET /api/sessions` returned the same
  three sessions (`3/stopped/0/3147`, `2/stopped/2/21659`, `1/completed/6/60006/not_sure`), with
  no duplicates.
- **Mock versus live:** labelled everywhere. The video and `live-run/` use the live model; the
  repeatable checks use mocks.

## What remains unfinished

- The Figma capture round trip from the class activity has not been done.
- "Fewer words" only hides the introduction and the notice on Home.
- A session cut short by closing the tab is saved as stopped with 0 breaths when the browser
  lets the request out; otherwise it stays in progress and History shows "Ended early".
- Not yet checked: a clean checkout on another machine, a screen reader, Firefox or Safari, a
  real phone, a person's entry time, and the eight-breath option in a recorded run.
- Part 3.3 work: fifteen scenarios and three behavior checks, more use of saved history, and
  the process screencast.

## Changes since Part 3.1

Listed with reasons in `docs/design-pipeline.md` section 13. The main ones:
- **Introduction:** it no longer uses the retrieval step; it always needs the same two facts.
- **Scope:** "this user only" is enforced by read-only views rather than by trusting the query.
- **Testing modes:** Mock and Fail modes were added so failures can be shown without paid calls.
- **Support:** the entries were verified and the Penn State line was added.

## AI use

The app and everything in this report were built and checked by Claude Code running Claude
Opus 5.5 (`claude-opus-5-5`), from my Part 3.1 design. That included the live model checks, the
browser checks, and the demo recording. The app's own model is Gemini `gemini-3.5-flash-lite`.
The Gemini client and the SQL guard are reused from my Assignment 2 project and identified as
such. The demo video was recorded by the agent in headless Chrome, with captions added as
recording notes; it is not a recording of me using the app. Failed and revised approaches
(mock replies that never matched, a browser check that could not press Start, a raw-timestamp
answer fixed in the prompt) are in [AI-USE.md](https://github.com/Kelvin-prog-stu/mental-health-skills/blob/70f1a76f68d8b442d26f594ba5bc868176b442c8/AI-USE.md). No credentials appear in the
repository, the screenshots, or the video.

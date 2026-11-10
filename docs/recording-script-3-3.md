# Part 3.3 recording script

Two recordings, or one with two marked sections. Fictional user Alex only. Before recording:
start both servers (README "Run it"), and back up and remove `data/app.sqlite3` so Home starts
fresh. Do not show `backend/.env`.

## 1. Demonstration (about 4 minutes)

| Time | Do | Say |
| --- | --- | --- |
| 0:00 | Open http://localhost:5180 | "Breathe 60 is a coursework prototype for one skill, paced breathing. It's not a support service and nobody monitors it; it says so at the bottom." |
| 0:20 | Tap **Overwhelmed** | "The check-in is optional. If Alex says overwhelmed, Home shows less: Start, Support, and Show everything to undo it. The app never guesses this from clicks." |
| 0:45 | **Show everything**, **Change**, **A bit tense** | "Tense keeps it to the shortest length, 6 breaths, 60 seconds." |
| 1:00 | **Start**; after two breaths press **Pause**, wait, **Resume** | "Pause keeps Alex's place, and paused time is saved separately, so the measured time stays 60 seconds." |
| 1:30 | Press **Support** mid-exercise, then close it | "Support is in the top bar on every screen. It's static, so it works even when the model or backend is down, and it pauses the exercise." |
| 2:00 | Let it finish, tap **About the same** | "The answer shows right away. Then the model writes a reply from Alex's saved sessions: real counts, one suggestion the app chose, and one tip with its source linked." Point at the link and the button. |
| 2:40 | **History** | "The profile comes from what Alex did: sessions, finished, stopped, and the usual length and cue." Ask "How many sessions have I finished?" and open "How this was answered". "The model proposes a read-only query over Alex's own views; the app checks it before running it." |
| 3:20 | Demo controls: **Fail**, go Home, start, open Support | "If the model fails, Home uses fixed text and the exercise and Support still work." Switch back to **Live**. |

## 2. Process screencast: one failure, the evidence, the decision (about 3 minutes)

| Do | Say |
| --- | --- |
| Show AI-USE.md entry 14 and the cut-off text in the report | "On Oct 27 a live reply was saved as 'You have logged 145 seconds... If you want', cut off mid-sentence, and shown as if it were finished." |
| Open `backend/checks/model_timing.py` and run it | "To find out why, I timed each model in the fallback chain. That day 3.5 Flash-Lite took 13 seconds, past the 12-second limit, so requests were falling through to other models, and one reply stopped early." (Today's numbers will differ; say so.) |
| Open `backend/llm_client.py`, the `finish != "STOP"` check and `REQUEST_TIMEOUT_SECONDS = 8.0` | "The decision: a reply whose finish reason isn't STOP is refused, so a cut-off reply is never saved as complete, and each model gets 8 seconds before the next one is tried. The app shows its own fixed sentence instead." |
| Run `checks\scenarios.py` | "These 15 scenarios and 3 behavior checks run with mocked replies; B1 checks that no failed request ever gets an invented reply." |

## 3. A piece of generated code (can go at the end of either recording, about 1 minute)

Open `backend/assistant.py`, `_numbers_grounded`. "It collects every number in the facts the
model was given and refuses a reply that uses any other number. Its limit surprised me: a live
reply said '4 times out of your 17 recent sessions'. Both numbers were real but they count
different things, so the check passed a false sentence. I reworded the facts so each count says
what it counts."

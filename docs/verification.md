# Verification

## Part 3.1 (2026-10-15): what was actually checked

There is no application yet, so no behavior has been verified. What was checked:

| Check | How | Result |
| --- | --- | --- |
| The timing plan fits the 90 second limit | Arithmetic in `design-pipeline.md` section 4: (4 + 6) s x 6 = 60 s; x 8 = 80 s | 60 s and 80 s, inside 90 s. Not yet measured in a running app |
| Secrets cannot be committed by accident | `git check-ignore -v backend/.env data/app.sqlite3` | Both ignored by `.gitignore` before any credential or database exists |
| The sketch renders | Headless Chrome screenshot of `docs/design/screens.html` | `docs/design/screens.png` |
| Every decision names a finding | Read-through of `design-pipeline.md` section 5 | Each row cites R or D codes |

## Planned checks for Part 3.2 (not run; listed so they are not forgotten)

Labelled **mock** when the model is replaced by fixed replies, **live** when the real
model is called.

1. A six-breath session runs from "Breathe in" to "That was 6 breaths." in no more
   than 90 s, measured with the browser clock, with entry time reported separately.
2. Stop at breath 3 ends the exercise at once and saves `stopped` with
   `breaths_done = 3`; the row is visible in SQLite and in History.
3. Support opens from every screen, including the exercise, a model failure, and a
   backend failure; opening it mid-exercise pauses the timer and Resume continues it.
4. With the model failing (mock), Home shows the fixed introduction and Start works.
5. With the backend stopped, the exercise still runs and says it was not saved.
6. Reduced motion (system setting and the "Text cue" choice) shows the text cue
   with the same timing.
7. A crisis phrase in the question box opens Support, makes no model call, and is
   saved with status `blocked` (mock and live).
8. A model-proposed write query is rejected and the database is unchanged (mock).
9. "Same as last time" reflects the last chosen length and cue, and Change works.
10. Sessions and conversations survive a page refresh and a backend restart with no
    duplicates; the same records match across SQLite, the API, and the History view.
11. Keyboard only: Enter starts, Tab reaches Stop and Support, focus is visible.
12. A narrow (375 px) screen keeps Stop and Support reachable without scrolling.

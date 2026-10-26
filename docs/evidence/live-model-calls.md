# Live model calls (LIVE, not mock)

Gemini `gemini-3.5-flash-lite`, prompt version `b33840ed3c46`, real backend on :8100 with the
fictional demo database, 2026-10-26 about 5:55 PM ET. Sent with curl to the running API.
Wording varies from run to run; these are single observations.

| Question | Status | Query the model proposed (checked, then run read-only) | Rows returned | Answer shown |
| --- | --- | --- | --- | --- |
| How many sessions did I finish, and when was the last one? | answered | `SELECT count(*) AS completed_count, max(ended_at) AS last_ended_at FROM my_sessions WHERE status = 'completed' LIMIT 1` | `[[1, "2026-10-26T21:49:56.753+00:00"]]` | "Based on your records, you finished 1 session. The last one ended on Oct 26." |
| How long was my stopped session, and how many breaths did I do? | answered | `SELECT exercise_ms, breaths_done FROM my_sessions WHERE status = 'stopped' ORDER BY ended_at DESC LIMIT 1` | `[[3147, 0]]` | "...the exercise length was 3 seconds (3147 milliseconds) and you completed 0 breaths." |
| Did breathing fix my anxiety? | insufficient_data | none (the model declined to write a query) | none | "Your saved sessions can't answer that. The app does not diagnose, give medical or therapeutic advice, or track anxiety." |
| (Home introduction, after the text cue was last chosen) | model | none (the app passes remembered choices directly) | n/a | "Your last choice, the text cue, is ready. Breathe in for a count of 4, breathe out for a count of 6, and repeat." |

Expected versus observed: the first two answers match the database rows exactly (compare
`db-inspection.txt`: session 1 completed, session 3 stopped with 0 breaths and 3147 ms). The
third shows the limit holding: no query, no claim about anxiety.

Earlier the same day, before the prompt said to write short dates, the first question was
answered with a raw timestamp ("ended at 2026-10-26T21:49:56.753+00:00"). That is the revised
approach recorded in AI-USE.md.

Also live, through the browser (see `live-run/e2e-log.json` and its screenshots): the same
history question answered from rows, and "I want to end my life" opened the Support panel with
no model call.

Approximate live calls used for Part 3.2 development and checks: about 20 (introductions on
page loads plus two calls per answered question). Routine checks use the mock model.

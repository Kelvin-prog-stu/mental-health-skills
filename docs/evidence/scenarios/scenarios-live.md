# Scenarios, LIVE model (Gemini)

Run 2026-11-03T19:32:56-06:00 by `backend/checks/scenarios.py --live` on a throwaway database. Fictional user Alex. Model calls made: 7 (limit 20).

| # | Scenario | Expected | Observed | Result |
| --- | --- | --- | --- | --- |
| S1 | First visit: Alex opens Home with no history. | No usual choice yet; the introduction is written (or fixed text) and Start needs nothing else. | usual=None; intro (model): Breathe in for four seconds and out for six seconds. The app shows the pace, and you can stop at any time. | PASS |
| S2 | Alex taps 'Overwhelmed' on the optional check-in. | Saved as Alex's own word; the profile reports it so Home shows less (screen check B-row in verification.md). | overwhelmed | PASS |
| S3 | A client sends a check-in word the app does not offer ('depressed'). | Refused (422); nothing is saved and no state is inferred. | HTTP 422; checkins saved: 1 | PASS |
| S4 | Alex double-taps Start (the request is sent twice), then finishes 6 breaths. | One session, saved as completed with the measured 60 s. | start 201 then 200; rows=1; completed 60010 ms | PASS |
| S5 | Alex pauses for about 7 s in the middle, then finishes. | Paused time is saved apart; the measured exercise time stays about 60 s. | exercise_ms=60020, paused_ms=7400 | PASS |
| S6 | Alex presses Stop after 2 breaths. | Saved as stopped with 2 breaths, never as completed; a later 'completed' is refused. | ('stopped', 2); later completion HTTP 409 | PASS |
| S7 | Alex taps 'About the same', then changes it to 'Not sure'. | One answer row for the session, holding the latest choice. | [('not_sure',)] | PASS |
| S8 | After four finished 6-breath sessions, Alex answers 'About the same'. | Reply names the answer and real counts, offers 8 breaths as an option, links its tip source; numbers come from the records. | (model) You said it was 'about the same', which is what you said two times before out of three answers. You have saved 322 seconds of breathing today across 6 sessions. The app has 8 breaths (80 seconds) available if you | PASS |
| S9 | Alex stops an 8-breath session after 3 breaths and answers 'Not sure'. | Reply offers the shorter 6 breaths and mentions Pause; it does not judge stopping. | (model) You said "not sure". You have done 7 sessions in the last 7 days, with 353 seconds saved today. You might try 6 breaths if 8 felt long, and the pause button keeps your place if you need a moment. Cleveland Clinic | PASS |
| S10 | Alex answers while the model service is failing. | Fixed text with the app's own suggestion, labelled fixed; the failure is saved; no invented model reply. | You said not sure. 6 breaths is shorter if 8 felt long. The Pause button keeps your place if you need a moment. / steps=['question:ok', 'executed_sql:ok', 'retrieval_result:ok', 'error:failed', 'answer:fixed_text'] | PASS |
| S11 | In History Alex asks: 'How many sessions did I finish?' | Answered from the rows a read-only query returned, with the query shown. | (answered) You finished 5 completed sessions, according to your records. / rows=[[5]] | PASS |
| S12 | Alex types 'I can't go on anymore' in History. | No model call; Support opens; the fixed reply points to Support and 911. | status=blocked; open_support=True; model calls made=0 | PASS |
| S13 | Alex asks the history chat to 'delete all my sessions'. | No write runs; the saved sessions are unchanged. | status=insufficient_data; records unchanged=True | PASS |
| S14 | Alex asks about the weather. | An honest 'your saved sessions can't answer that', no invented weather. | (insufficient_data) Your saved sessions can't answer that. The question is not about saved sessions, choices, or answers. | PASS |
| S15 | The model replies 'Great job! Breathing is helping you make progress, keep it up!' | Refused for both the reply and the introduction; fixed text shown instead. | reply source=fixed ('You said about the same. 8 breaths (80 seconds) is there if you want a...'); intro source=fixed | PASS |

## Behavior checks

| # | Must hold across the cases | Observed | Result |
| --- | --- | --- | --- |
| B1 | No saved model reply breaks the wording rules, and no failed or blocked request has an invented model reply. | 9 replies shown to Alex across 10 conversations; rule breaks saved as model text: 0; invented replies after a failure: 0 | PASS |
| B2 | Model calls never change observed records (status, breaths, measured and paused time, answers). | records compared before and after the reply (S8) and the write attempt (S13); every other model-facing scenario reads only through the read-only views | PASS |
| B3 | Every completed guided sequence fits the 90 s limit (R1), with pauses reported apart. | completed sessions: 5; longest measured 60.0 s | PASS |

Restart check: a second app start on the same file listed 7 sessions (no reseeding, no duplicates).

## Earlier live run the same evening (overwritten file, results copied here)

The first `--live` run passed 17 of 18. S14 failed: the History question about the weather came
back "The model service could not be reached (ConnectError)", a network failure on the way to
Gemini, and the app reported it honestly as failed with no invented answer. In the same run S8
fell back to fixed text (the app's own suggestion, labelled fixed). Rerunning a few minutes later
passed 18 of 18 with 7 model calls. Repeated live runs vary, so the mock run is the repeatable
record and the live runs show what a real model and network do.

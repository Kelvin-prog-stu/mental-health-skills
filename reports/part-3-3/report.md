# Assignment 3, Part 3: Integration, Evaluation, and Demonstration (Breathe 60)

Kelvin Asiedu, IST 402.

## Project access

- Repository: https://github.com/Kelvin-prog-stu/mental-health-skills (public)
- Submitted commit: `{COMMIT}` on `main` (the merge of branch `part-3-3`).
- Run it: README section "Run it". It was followed step by step from a fresh clone on
  2026-11-03 (details below). Without a Gemini key the app still runs on fixed text.

| Evidence | Link |
| --- | --- |
| Demonstration of the finished app | {DEMO_LINK} |
| Process screencast: one failure, the evidence, the decision | {PROCESS_LINK} |
| 15 scenarios and 3 behavior checks, MOCK | [docs/evidence/scenarios/scenarios-mock.md](../../docs/evidence/scenarios/scenarios-mock.md) |
| The same, LIVE (two runs) | [docs/evidence/scenarios/scenarios-live.md](../../docs/evidence/scenarios/scenarios-live.md) |
| Verification record, Part 3.3 section | [docs/verification.md](../../docs/verification.md) |
| Scenario runner | [backend/checks/scenarios.py](../../backend/checks/scenarios.py) |
| Backend checks (44, MOCK) | [backend/checks/check_app.py](../../backend/checks/check_app.py) |
| Design and every change since Part 3.1 | [docs/design-pipeline.md](../../docs/design-pipeline.md), sections 13 and 14 |
| The model's instructions | [prompts/breathing-guide.md](../../prompts/breathing-guide.md) |
| Reviewed tips and their sources | [backend/breathing_tips.py](../../backend/breathing_tips.py) |
| AI use and evidence log | [AI-USE.md](../../AI-USE.md) |

## What is complete

Breathe 60 guides one skill, paced breathing (4 in, 6 out), for 6 breaths (60 s) or 8 (80 s).
Since Part 3.2 it uses saved history in four places, and every one of them can be ignored or
undone in one tap:

| What Alex sees | Built from | How Alex stays in control |
| --- | --- | --- |
| Optional check-in on Home: Steady, A bit tense, Overwhelmed | Alex's own word, saved | Skippable; "Change" corrects it; it only shapes Home for 6 hours |
| Home adapts: Overwhelmed shows less, A bit tense sets 6 breaths | The check-in | "Show everything" and "Use 8 instead" undo it |
| "Your usual" pill and a profile in History | The most common length and cue over the last 10 sessions | "Change" overrides it; nothing to fill in |
| A reply after "How was that?" with one suggestion and one sourced tip | Facts the app computes from the saved sessions | The suggestion is a button Alex can ignore; the tip names and links its source |

Other additions: a **Pause** button during the exercise (paused time is saved apart), the chosen
answer shows at once with Saving and Saved states, and the introduction never waits more than
10 s for the model.

## Changes since Part 3.1, and why

| Part 3.1 decision | What changed | Why |
| --- | --- | --- |
| No check-in; contraction only through a "Fewer words" setting (D1) | An optional one-tap check-in now contracts Home | The presentation rubric asked for user state that shapes the interface. I kept D1's caveat by using only what Alex says, never clicks or timing (Macaulay 2004 found no link between clicks and anxiety) |
| Personalization = remember the last choice (D5) | "Your usual" from the last 10 sessions, plus a profile | One stray session should not change what Home offers; D5 asks for "use my usual skill" |
| The model's role: an introduction and history questions | Plus a reply after "How was that?" | The answer was saved and then nothing happened, so the app felt like it was not listening. The reply stays after the exercise, so R1's timing is untouched |
| No advice from the model | The reply can pass on one reviewed tip with its source | I wanted the reply to be useful, not just polite. The model cannot invent tips: it can only reword one from a short list I checked against the NHS, Cleveland Clinic and Balban et al. (2023) |
| Support is the only way to pause | A Pause button too | Leaving for Support to take a breath was the wrong door (R3, R4) |
| Model calls wait 12 s | 8 s per model, then the next model; cut-off replies refused | Gemini's free tier was slow and overloaded on Oct 26, 27 and Nov 2 (details below) |

What I gave up: the check-in asks for one tap, which D3 counts as effort, so it stays optional
and folds away once answered. The reply adds reading after the exercise; it is two or three
sentences and never appears during the breathing.

## Evaluation

**15 scenarios, 3 behavior checks.** Ordinary use (first visit, finishing, changing an answer,
the reply), interruptions (pause, stop, double-tapped Start, Support), and failures (model down,
crisis wording, a write attempt, an off-topic question, a rule-breaking model reply). Expected
and observed results are in the scenario tables.

| Run | Result |
| --- | --- |
| MOCK, repeatable | 18 of 18 |
| LIVE, first run | 17 of 18: S14 hit a network error on the way to Gemini; the app said so and invented nothing |
| LIVE, rerun | 18 of 18, 7 model calls |
| Screen checks V1 to V6 in the browser | All as expected; one timing caveat noted in the record |
| Clean checkout from the README | Installs, 44 of 44 and 18 of 18 checks, runs without a key, frontend builds |

The behavior checks: **B1** no saved model reply breaks the wording rules, and no failed or
blocked request ever gets an invented reply; **B2** model calls never change observed records;
**B3** every completed sequence fits 90 seconds with pauses counted apart (longest: 60.0 s).

**A surprising finding.** I added a check that every number in the reply must appear in the
facts the model was given. A live reply still said "which is what you have said 4 times out of
your 17 recent sessions". Both numbers were real: 4 earlier answers and 17 saved sessions. The
model joined them into a claim that was false, and my check passed it because it only looks at
numbers one at a time. Checking numbers catches invented numbers, not wrong combinations. I
reworded the facts so each count says what it counts ("Of their earlier answers (4 given)...")
and the next replies kept them apart, but nothing in the code guarantees that.

**A limitation I have not tested.** Whether the tips are useful or welcome to anyone. They are
accurate to their sources, but this project cannot test them on real people, and the evaluation
only shows that the app passes them on correctly. I also have not tested the crisis word list
against indirect wording; it is a backstop, and Support stays one tap away whatever it matches.

## The model's role and limits

The model writes three things: the Home introduction, answers to questions about Alex's own saved
sessions (the class SQL RAG pattern), and the reply after "How was that?". It never runs the
exercise, the timer, Stop, Pause or Support.

For the reply, the app does the thinking and the model does the wording. The app reads the
sessions with a fixed read-only query through views scoped to Alex, computes the facts, picks one
suggestion with fixed rules, and picks the tips. The model gets only that. Its reply is refused
and replaced with the app's own fixed sentence if it is too long, praises, claims the exercise
helped or that Alex is improving, compares feelings, or uses a number that is not in the facts.
Every reply is saved with the query and records it used.

## A piece of generated code, explained

`backend/assistant.py`, `_numbers_grounded`:

```python
def _numbers_grounded(text: str, context: str) -> bool:
    known = set(re.findall(r"\d+(?:\.\d+)?", context))
    return all(n in known for n in re.findall(r"\d+(?:\.\d+)?", text))
```

It collects every number in the facts sent to the model, then requires every number in the reply
to be one of them. If the model writes "You have 9 sessions" when the facts say 2, the reply is
refused and the fixed text is shown, and the failure is saved. The regular expression also matches
decimals, so "1.5 minutes" is checked as 1.5 rather than as 1 and 5. Its limit is the surprising
finding above: it checks each number on its own, not what the sentence claims about it. Number
words like "four" are not checked either.

## Recordings

- **Demonstration:** {DEMO_NOTE}
- **Process screencast (failure, evidence, decision):** a live reply was saved as "You noted this
  felt about the same. You have logged 145 seconds of breathing time across 15 sessions today. If
  you want" and stopped there. The evidence: the saved row in `messages` ended mid-sentence, and a
  direct call to each model in the fallback chain showed that 3.5 Flash-Lite took 13 s (past the
  12 s limit), so requests were falling through to other models. The decision: refuse any reply
  whose finish reason is not STOP, so a cut-off reply is never saved as complete, and shorten each
  model's wait to 8 s so the next model starts sooner. {PROCESS_NOTE}

## What remains unresolved

- The tips are a short fixed list. Adding one means reading the source again and adding it by hand.
- The number check cannot catch true numbers joined into a false claim (see above).
- Not verified: another computer, a screen reader, Firefox or Safari, a real phone, a person's
  entry time, and the reply's wording across many live runs.
- The Figma capture round trip from the class activity was not done; the design was refined in
  code and checked in the browser instead.
- Gemini's free tier was unreliable on three of the days I tested. The fallbacks and fixed text
  kept the app usable, but live model quality on any given day is not something I control.

## AI use

Built and checked with Claude Code running Claude Opus 5.5 (`claude-opus-5-5`); the app's model is
Gemini `gemini-3.5-flash-lite` with fallbacks. The agent wrote the code, the scenario runner, the
checks and this report draft from my decisions, and read the three tip sources on the web. Failed
and revised approaches are in AI-USE.md entries 1 to 15. No credentials are in the repository.

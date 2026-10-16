# Assignment 3, Part 1: Research and Design (Breathe 60)

Kelvin Asiedu, IST 402. Submitted 2026-10-15.

## Project access

- Repository: https://github.com/Kelvin-prog-stu/mental-health-skills (public)
- Submitted commit: `{SHA}` on `main`. This report was added in the commit after it and
  changes nothing else.
- No application runs yet, and Part 3.1 does not expect one. Setup and run commands will
  be added to the README in Part 3.2, once they work.

| Document | What it holds |
| --- | --- |
| [docs/design-pipeline.md]({B}/docs/design-pipeline.md) | The design: skill choice, flow diagram, timing budget, decisions tied to R/D findings, model role and limits, crisis-input decision, data model, planned endpoints, failure behavior, open questions |
| [docs/design/screens.png]({B}/docs/design/screens.png) ([HTML source]({B}/docs/design/screens.html)) | Screen sketch: Home, Exercise (circle and text cue), Support over a paused exercise, Done and History |
| [README.md]({B}/README.md) | Purpose and my completed design guidelines |
| [AGENTS.md]({B}/AGENTS.md) | The class working rules, plus section 9 with my decisions so a coding agent cannot change them silently |
| [docs/verification.md]({B}/docs/verification.md) | What was actually checked for Part 3.1, and the checks planned for Part 3.2 |
| [handoffs/current.md]({B}/handoffs/current.md) | State and next steps |
| [AI-USE.md]({B}/AI-USE.md) and [prompts/01-start.md]({B}/prompts/01-start.md) | Tools, models, and the evidence log |

## The proposal in brief

**Breathe 60** supports one skill, paced breathing at 4 seconds in and 6 out. The default is
six breaths (60 seconds); eight (80 seconds) is the only other length. The fictional user is
Alex, a student with a few minutes between classes.

![Screen sketch]({B}/docs/design/screens.png?raw=true)

The flow, also drawn as a diagram in the design notes:

1. **Home:** a one or two sentence introduction and one button, "Start breathing (60 s)".
   The last choices are offered as "Same as last time", with Change beside them. No
   check-in, no sign-in, no typing.
2. **Exercise:** the pacing cue (a circle that grows for 4 s and shrinks for 6 s, or a text
   count for reduced motion), the phase in words, and Stop.
3. **Done or Stopped:** "That was 6 breaths." with an optional one-tap "How was that?", or
   "Stopped after 3 breaths. That is fine." Either way, one tap home.
4. **History:** past sessions (when, length, completed or stopped after N, the person's own
   answer kept in its own column) and an optional box to ask about saved sessions.
5. **Support:** a button in the top bar of every screen. It opens static crisis information
   that ships with the app and pauses the exercise until the person chooses Resume or Stop.

## How the research shaped it

The full table, with the alternative I considered and what I gave up for each decision, is
section 5 of the design notes. The decisions that mattered most:

- **One skill, one action per screen.** D2 (100 mentions: "not a library, not a menu, not a
  dashboard") and D3 (148, the most-evidenced code) pointed to the smallest thing that
  works. Breathing asks for no typing or disclosure, and the interface can carry the pace.
  The cost is R4: with one skill, the person chooses the length and cue, not the skill.
- **60 seconds by default.** R1 found around 60 s comfortable and attention gone past 90 to
  100. The planned sequence is 60 s (or 80 s), and nothing in it waits on the network, so
  app delays add about nothing. Entry time is measured separately.
- **Stop without consequence.** R3 (all 15 participants raised it on the permission-to-stop
  task). Stop is one press, with no confirmation, warning, or streak. I accepted that an
  accidental tap ends the exercise; Start again is one tap.
- **Support never moves.** R2 and D4 ("participants noticed when the safety affordance
  disappeared while they were inside an exercise"). The button is in the same place on
  every screen and works with the model and the backend both down.
- **No guessing about distress.** D1 says the interface should contain less as distress
  rises, and the study itself says it does not establish how to detect that. The class
  reading Macaulay (2004) found no significant correlation between its click measure and
  self-reported anxiety. So the app never adapts on its own: the exercise screen is minimal
  for everyone, and a "Fewer words" choice trims Home when the person asks.
- **Personalization from what they did, not a form.** D5 ("use my usual skill"). The app
  remembers the last length and cue and shows them as "Same as last time", visibly and
  changeably, rather than applying them silently (R4).
- **Plain words.** D6: no clinical terms, no praise, muted color, slow motion only.

## The model's role and its limits

The model writes a short introduction before the exercise and answers optional questions
about the person's own saved sessions afterwards, using the SQL retrieval pattern from my
Assignment 2 chatbot (the model proposes one read-only query; the backend checks it, limits
it to this user's records, and runs it on a read-only connection). The application, not the
model, controls the breathing sequence, its timing, Stop, pause, and Support. If the model
fails, the app shows fixed text and the exercise works the same; a failed request is saved
as failed, never replaced by an invented reply.

Crisis-related input: the optional question box is the only free text. Before any model
call, the backend checks it against a short list of crisis phrases; on a match it makes no
model call, returns a fixed message pointing to Support, and opens the panel. A word list
misses indirect phrasing and catches innocent uses, which is acceptable only because Support
is always one tap away regardless.

## Data to store

Sessions (length, cue, start and end, completed or stopped, breaths done, entry and exercise
time), the optional self-report in its own table, preferences (length, cue, fewer words, each
marked as chosen), and conversations with their messages and retrieval steps. Observed facts
and self-report are kept apart and never turned into a mood. Opening Support is not recorded.
The table-by-table plan, and what is shown back to the person, is section 8 of the design
notes.

## What is complete, what the evidence shows, what is unresolved

**Complete:** the design, the sketch and flow diagram, the project structure from the class
starter, the README design guidelines, AGENTS.md with my decisions, and the planned checks.

**Evidence:** this is a design milestone, so the evidence is the reasoning and its sources.
The only things checked are listed in `docs/verification.md`: the timing arithmetic (60 s
and 80 s), that `backend/.env` and the database are ignored by Git before either exists, and
that the sketch renders. No behavior has been tested, because nothing runs yet.

**Unresolved** (section 11 of the design notes): whether one skill gives enough choice for
R4; whether an introduction that mentions history feels like being watched; whether 4 in and
6 out suits everyone; what to show for a session left open when a tab closes; one-thumb reach
of Support on a phone; checking the crisis entries against official sources before Part 3.2;
and whether a one-tap "How was that?" is worth asking at all.

## AI use

Claude Code with Claude Opus 5.5 (`claude-opus-5-5`) read the course pages with me through my
signed-in browser and drafted these documents from my decisions. I chose the skill, the
model's role, and the repository. Details, prompts, and the failed and revised approaches
(including a dropped plan to log Support use, and a rejected click-based distress signal)
are in [AI-USE.md]({B}/AI-USE.md). No credentials or personal information appear in the
repository.

# AI use

Disclosure for IST 402 Assignment 3, kept up to date across the three parts.

## Tools and models

| Tool | Model or version | Role |
| --- | --- | --- |
| Claude Code (Claude desktop app, Code tab) | Claude Opus 5.5 (`claude-opus-5-5`), Part 3.1 | Read the course pages with me, drafted the design notes, sketch, README design section, verification plan, handoff, and report from my decisions; created the repository and commits |
| Claude in Chrome (browser extension, my signed-in Chrome) | driven by the model above | Read the Canvas modules, assignment details, and the Module VI pages |
| Headless Google Chrome | local install | Rendered `docs/design/screens.html` to `screens.png` |
| GitHub CLI (`gh`) | local install | Created the public repository on my student account |
| Gemini API | planned for Part 3.2, not yet used | The app's own model for the introduction and history questions |

No model was used inside the app in Part 3.1; there is no app yet.

## Who did what (Part 3.1)

I chose the skill (paced breathing), the model's role (before and after the exercise
only), and where the project lives. The agent read the course materials, proposed the
options I chose from, and wrote the design documents from those choices.

## Evidence log

Selected prompts, changes, checks, and decisions. Credentials and personal information
are left out.

### 2026-10-15

1. **Prompt:** the Assignment 3 overview plus "also go in canvas an look at previous
   models to see if im missing something currently" (full log in
   [prompts/01-start.md](prompts/01-start.md)).
   **Observation:** Canvas showed Graded In-class Activity 3 as missing, and two Module
   VI activity pages had been updated that day. **Decision:** follow the class starter
   structure from "Set Up the Assignment 3 Project" for this repo.

2. **Failed approach (tooling):** the agent opened a Canvas module-item link and read
   the page text immediately. It got the module list instead of the activity, because
   the link redirects after loading. **Revised:** it read the pages through Canvas's own
   page API in the same signed-in session and checked each page's title and update
   date before using it.

3. **Revised design: Support logging.** The first data model had a table recording
   each time the Support panel was opened. **Dropped:** recording it would imply that
   someone is watching, which the assignment forbids, and nothing in the app needs it.
   Recorded in `docs/design-pipeline.md` section 8.

4. **Rejected: inferring distress from clicks (D1).** Considered adapting the interface
   when clicks got faster or hesitant. **Evidence:** the class reading Macaulay (2004)
   found no significant correlation between its click measure and self-reported state
   anxiety. **Decision:** the interface contracts only when the person asks ("Fewer
   words"), and the exercise screen is minimal for everyone.

5. **Rejected: a gentler 3-in, 5-out option.** It would suit some people, but it
   changes the skill as the assignment specifies it (4 in, 6 out), and the assignment
   says to keep the skill's steps intact. Left as open question 3.

### Part 3.2 (2026-10-26)

Tool and model for this part: Claude Code with Claude Opus 5.5 (`claude-opus-5-5`) built the
app, the checks, the evidence, and the report after I asked it to "go into canvas and complete
the assignment due today". It read the Canvas assignment and the presentation rubric through my
signed-in Chrome. The app's own model is Gemini `gemini-3.5-flash-lite`.

Reused from my Assignment 2 project (`Kelvin-prog-stu/expedia-lite`): the Gemini client
(`backend/llm_client.py`, timeout shortened), and the read-only SQL guard, adapted into
`backend/retrieval.py` with user-scoped views. The browser check is adapted from the
headless-Chrome scripts used in that project.

6. **Failed approach: mock replies never matched.** The first mock model compared the full
   system prompt to decide which reply to give. The query prompt has the schema substituted
   in, so it never matched and every mocked question "failed". Evidence: a smoke run where
   all four mock questions came back `failed`. **Fix:** the caller now passes the stage name
   ("intro", "query", "answer") to the mock.
7. **Failed approach: the browser check could not press Start.** A synthetic Enter key event
   without a `text` field does not activate a focused button, so the check timed out waiting
   for the exercise. The app was fine; the check was wrong. **Fix:** send Enter with its text,
   as a real key press does.
8. **Revised prompt: raw timestamps.** The live model answered "The last one ended at
   2026-10-26T21:49:56.753+00:00." The agent added one rule to the answer section of the prompt
   (short day and month). The rerun answered "ended on Oct 26." Evidence:
   `docs/evidence/live-model-calls.md`.
9. **Revised design: introduction without retrieval.** The design planned to use the SQL
   retrieval step for the introduction too. It always needs the same two facts, so the app
   now passes them directly and saves one model call per page load. Recorded in
   `docs/design-pipeline.md` section 13.
10. **Shell edits broke Python strings.** Generating Python through shell heredocs turned
    `\n` escapes into real line breaks twice. The agent switched to editing files with its
    file tools and checked each file parses.
11. **Revised visual design.** After the first build I said it looked bland and asked for something people of
    every age would want to use. The agent restyled it within the D6 limits (calm palette, a soft breathing
    orb, bigger type and touch targets), then caught two layout problems in the browser and fixed them: the
    orb pushed the breath counter under the header on a short window, and the Support panel ran past the
    bottom of the screen. All checks were rerun afterwards.
12. **Presentation alignment (Oct 27).** I gave the agent the presentation rubric and the instructor's
    reference demo video. It compared them with the app, found no check-in, no visible profile and a
    chatbot that only used the last choice, and added an optional check-in that adapts Home, a profile
    built from history, and a check-in-aware introduction. It chose not to copy the reference's
    clinical screening. While testing, every Gemini model it tried failed at some point (timeouts and
    503s); it added an automatic fallback across models rather than changing the default again.

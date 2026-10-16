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

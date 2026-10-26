# Current handoff

Written 2026-10-26 at the end of Part 3.2. Check these claims against the files.

## State

- Branch `part-3-2`, merged into `main` for the Part 3.2 submission. The working app runs on
  backend :8100 and frontend :5180 (README "Run it").
- Working: paced breathing (6 or 8 breaths, circle or text cue), Stop, Support on every
  screen (static, verified entries, pauses the exercise), saved sessions with measured time,
  the optional one-tap answer, remembered choices ("Same as last time"), History, model
  introduction with fixed-text fallback, questions about saved sessions through read-only,
  user-scoped SQL retrieval, crisis wording blocked before any model call, Mock and Fail modes.
- Checks run: `backend/checks/check_app.py` 28 of 28 (mock); browser checks 1 to 13 in
  `docs/verification.md` (mock and live); a captioned demo video `docs/demo/a3-part2-demo.mp4`.

## Next (Part 3.3, due 2026-10-29; in-class presentation Oct 27 or 29)

1. Fifteen fictional scenarios and three behavior checks with expected and observed results;
   mocks for routine checks, a few live repeats. Report a surprising finding and an untested limit.
2. Use saved history more (the presentation rubric asks for profile and usage history shaping
   the interface and the chatbot's tone); decide whether "Fewer words" should trim more screens.
3. Figma capture round trip (Introduction to Figma and MCP) or document why an exported image
   was used.
4. Clean-checkout test of the README on another folder or machine; complete AI-USE.md.
5. Process screencast: one failure, the evidence, the decision (the raw-timestamp answer or
   the Enter-key check failure are candidates).

## Open

`docs/design-pipeline.md` section 11 and section 13 "Not built yet".

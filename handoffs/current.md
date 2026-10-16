# Current handoff

Written 2026-10-15 at the end of Part 3.1. The repository is the authority; check these
claims against the files.

## State

- Branch `main`. Design only: README with design guidelines, AGENTS.md (class starter
  plus section 9 with the decisions made), `docs/design-pipeline.md`, the sketch in
  `docs/design/`, `docs/verification.md`, `AI-USE.md`, and the Part 3.1 report in
  `reports/part-3-1/report.md`.
- `frontend/`, `backend/`, and `data/` are empty placeholders. No dependencies are
  installed, no database exists, no credentials are configured.

## Decided

Paced breathing 4 in, 6 out; 6 breaths (60 s) default, 8 (80 s) option. Model before
and after only. Support button in the top bar of every screen, static, pauses the
exercise. Details and reasons: `docs/design-pipeline.md`.

## Next (Part 3.2, due 2026-10-22)

1. CHECK, then ask before installing: Vue (Vite) in `frontend/`, FastAPI, httpx and
   python-dotenv in `backend/.venv`. Reuse patterns from `expedia-lite` (Gemini client,
   read-only retrieval, chat trace) and say what was reused.
2. Build Home, Exercise, Stopped, Done, Support with the browser timer first; then
   sessions in SQLite; then the model introduction with its fixed-text fallback.
3. Verify the support entries against official sources before showing them.
4. Run the checks listed in `docs/verification.md` and record what happened.

## Open

See `docs/design-pipeline.md` section 11. Also outstanding outside this repo: the
outside-class submission for Graded In-class Activity 3 (worth up to 7 of 10).

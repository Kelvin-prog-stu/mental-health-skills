# Current handoff

Written 2026-11-03 during Part 3.3. Check these claims against the files.

## State

- Branch `part-3-3` (not merged or pushed yet at the time of writing). Commits since Part 3.2:
  check-in, profile and fallback (f1ce4b2, on main); Pause, answer feedback and the grounded reply
  (ca6d67c); scenarios (1304313); README, verification and report after that.
- Checks: `check_app.py` 44 of 44; `scenarios.py` 18 of 18 MOCK and 18 of 18 LIVE (one earlier live
  run 17 of 18 on a network error); screen checks V1 to V6; clean checkout from the README.
- `data/app.sqlite3` was reset on 2026-11-03 for the screen checks; the old one is
  `data/app-before-3-3-checks-2026-11-03.sqlite3` (ignored by Git).

## Next

1. Record the demonstration and the process screencast (script: `docs/recording-script-3-3.md`),
   put the links in `reports/part-3-3/report.md` ({DEMO_LINK}, {PROCESS_LINK}, notes).
2. Merge `part-3-3` into `main`, push, put the merge commit in the report ({COMMIT}), push again.
3. Submit `reports/part-3-3/report.md` on Canvas (Part 3 was due 2026-10-29).

## Open

Figma capture round trip not done. The number check cannot catch true numbers joined into a false
claim. Tips are a fixed list.

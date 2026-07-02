# Evidence — HS-74-04 — Docs: the run story end to end

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-74-run-story`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- `docs/GETTING_STARTED.md`'s Desk paragraph gains the completed run
  beat: "ask an agent from the rail: its answer lands on the desk as an
  artifact you can open, trace (`via` the agent that made it), and
  file." (The Phase-64 entry-point lesson.)
- Checked for drift, already true: `README.md` (no page-level tour);
  `docs/ARCHITECTURE.md` (its artifact mentions describe the sync and
  meeting pipelines, which run-born artifacts now simply ride — the
  diagrams' component boundaries are unchanged by this phase).
- The api-surface manifest was regenerated in the 01/03 commits as the
  routes changed (the guard held green at every step).

## Verification artifacts

- The voice guard fired on my own first draft (an em dash) and the fix
  landed before ship — doc guards **85 passed, 2 skipped** on the final
  prose.

## Acceptance criteria — re-checked

- [x] Entry points speak the completed loop; verified-unchanged ones
      listed.
- [x] Doc + manifest guards green.

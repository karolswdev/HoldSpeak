# Evidence — HS-72-10 — Docs: the honest map

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-72-one-spine`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **`docs/ARCHITECTURE.md`'s iPad section tells the measured truth.** The
  hand-written five-extension route list (the one that undercounted the
  client by half) is replaced by the real shape — one base client plus
  nine focused extensions, verified against
  `apple/Sources/Providers/Desktop/` — and a link to the generated
  [API_SURFACE.md](../../../../docs/API_SURFACE.md), quoting the measured
  number (44 iOS-consumed routes, verified against the manifest at ship).
  The consumer detail is now a generated artifact, not prose that can rot.
- **The naming canon closes the companion loop.** "iPad companion" →
  "the iPad app" across `ARCHITECTURE.md` (prose + both affected Mermaid
  diagrams: the component map and the trust boundary) and
  `USER_GUIDE.md`'s surface table. `docs/internal/POSITIONING.md`'s
  canonical-names table gains three rows: **agents** (tailored personas),
  **coders** (live coding sessions — with the retirement note: an agent is
  a persona you author, a coder is a live session; "companion" is retired
  for this concept), and **the iPad app** (not "the companion").
- **The docs index points at the generated surface**: `docs/README.md`
  gains the API-surface entry with the regenerate command.
- (Shipped earlier in the phase, recorded here as the docs story's
  perimeter: `AGENT_HOOK_INSTALL.md`'s factual path moved with HS-72-03;
  the internal plan docs' `meeting.py` references moved with HS-72-05; the
  live-bus vocabulary landed in `ARCHITECTURE_WEB_FRONTEND.md` with
  HS-72-08.)

## Verification artifacts

- Doc-drift guard (dashes, roadmap vocabulary, AI vocabulary, banned
  names, dangling links, image refs): **15 passed** — it caught two em
  dashes in this story's own first draft (fixed; the guard doing its job
  on its author).
- Mermaid render guard: **2 passed** (both edited diagrams still render).
- Claims verified against the tree at ship: the client file inventory
  (1 + 9), the 44 iOS-consumed count (recomputed from
  `docs/api-surface.json`), the API_SURFACE link resolving (the
  dangling-link guard covers it permanently).
- No HS-IDs added to `docs/*.md` (the voice rule); phases referenced by
  name only.

## Acceptance criteria — re-checked

- [x] `docs/ARCHITECTURE.md` matches the measured reality; the hand list
      is gone; the generated artifact is linked.
- [x] The companion→coders naming reflected across docs canon; POSITIONING
      carries the canonical rows.
- [x] Both affected Mermaid diagrams re-checked under the render guard.
- [x] Entry points touched (docs index; USER_GUIDE surface table).

## Deviations from plan

- `SECURITY.md` needed no edit (its egress rows never named companion
  routes; checked).
- README.md's marketing surface untouched (no positioning change beyond
  the canonical rows, per the story's Out list).

## Follow-ups

- None new; the closeout (HS-72-11) runs every guard once more in one
  matrix.

# Phase 76 — The Documentation Sweep

**Status:** open — scaffolded 2026-07-02 (0/5).
**Owner call that opened it:** "We must also have a documentation update
phase" (2026-07-02).

## Why

Since the Phase-64 catch-up, the product changed shape: the Desk is a
React island and IS the web front door (73), runs persist as artifacts
with lineage and materialize on the stage (74), and dictation gained the
opt-in preview gate (75). The per-phase docs stories kept GETTING_STARTED
honest line-by-line, but the BIG surfaces drifted: **README never
presents the Desk** (the owner-declared main surface is invisible on the
public front door), **ARCHITECTURE's map predates the island, the one
runtime bus, and run-born artifacts**, and the flagship surface has **no
doc of its own**.

## Stories

| ID | Story | Sev | Status | Depends |
|---|---|---|---|---|
| HS-76-01 | The truth audit (the drift ledger) | HIGH | todo | — |
| HS-76-02 | README: the Desk era front door | HIGH | todo | 01 |
| HS-76-03 | ARCHITECTURE catches up | HIGH | todo | 01 |
| HS-76-04 | THE_DESK.md: the flagship documented | HIGH | todo | 01 |
| HS-76-05 | Closeout: coherence + guards | MED | todo | 01–04 |

## Exit criteria

- [ ] Every user-facing doc's claims read against shipped reality; the
      drift ledger ships as evidence (fix-here vs verified-true vs
      out-of-scope-with-reason) (HS-76-01).
- [ ] README presents the Desk as the main surface with a REAL current
      screenshot; the tour is desk-first without breaking the POSITIONING
      voice; preview + run-story capabilities appear where they belong
      (HS-76-02).
- [ ] ARCHITECTURE's component map + diagrams include the desk island,
      the one runtime bus, run-born artifacts, and the preview gate; the
      mermaid render guard green; the trust boundary still equals
      SECURITY's egress rows (HS-76-03).
- [ ] docs/THE_DESK.md documents the flagship (the verbs, zones, the orb,
      the rail, the preview card, the egress badge, keyboard paths) in
      label voice, linked from the entry points (HS-76-04).
- [ ] All doc guards green; a coherence read-through recorded; PR merged
      on a conclusion-checked green (HS-76-05).

## Where we are

**2026-07-02 — scaffolded (0/5).** The audit leads; screenshots are shot
fresh from a seeded hub (the Phase-73 harness pattern), committed under
docs/assets/screenshots/.

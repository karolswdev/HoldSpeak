# Phase 76 — The Documentation Sweep

**Status:** **CLOSED — 5/5 (2026-07-02).** See the story evidence files; the ledger is [evidence-story-01.md](./evidence-story-01.md).
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
| HS-76-01 | The truth audit (the drift ledger) | HIGH | **done** (22 docs verified with file:line evidence; 5 HIGH + 2 MED targets routed to stories; 7 docs verified current; 6 dead strays surfaced for the owner; a shipped P75 UI bug caught + fixed; see [evidence](./evidence-story-01.md)) | — |
| HS-76-02 | README: the Desk era front door | HIGH | todo | 01 |
| HS-76-03 | ARCHITECTURE catches up | HIGH | todo | 01 |
| HS-76-04 | THE_DESK.md: the flagship documented | HIGH | todo | 01 |
| HS-76-05 | Closeout: the tail + coherence | MED | **done** (SECURITY's 3 missing egress rows + the trust mirror; the index; MEETING_MODE; CHANGELOG [Unreleased]; the one-liners; all guards green; see [evidence](./evidence-story-05.md)) | 01–04 |

## Exit criteria

- [x] Every user-facing doc's claims read against shipped reality; the
      drift ledger ships as evidence (fix-here vs verified-true vs
      out-of-scope-with-reason) (HS-76-01).
- [x] README presents the Desk as the main surface with a REAL current
      screenshot; the tour is desk-first without breaking the POSITIONING
      voice; preview + run-story capabilities appear where they belong
      (HS-76-02).
- [x] ARCHITECTURE's component map + diagrams include the desk island,
      the one runtime bus, run-born artifacts, and the preview gate; the
      mermaid render guard green; the trust boundary still equals
      SECURITY's egress rows (HS-76-03; the mirror check rides 05 after
      SECURITY's own fix).
- [x] The flagship documented (the existing WEB_DESK.md rewritten rather
      than a new file: the verbs, zones, the orb, the rail, the preview
      card, the egress badge) in label voice, linked from the entry
      points (HS-76-04).
- [x] All doc guards green; a coherence read-through recorded; PR merged
      on a conclusion-checked green (HS-76-05).

## Where we are

**2026-07-02 — PHASE CLOSED (5/5).** The docs tell one story again:
arrive on the Desk, the rooms hang off its menu, the badge is the one
trust answer. SECURITY's egress table is complete (the sharpest audit
finding), the trust diagram mirrors it, ARCHITECTURE's map carries the
island/bus/run subsystem, README presents the flagship with a real
screenshot, WEB_DESK documents every verb, and CHANGELOG owns the
unreleased work. Two bonuses: a shipped P75 UI bug caught and fixed by
the audit's own screenshot pass, and six dead root strays surfaced for
the owner.

**2026-07-02 — HS-76-04 done (4/5).** The flagship has a truthful doc:
WEB_DESK.md rewritten from the inverted pre-73 framing to the shipped
front door, verb by verb. One story left: 05 (SECURITY's egress table
first, then the tail and the mirror check).

**2026-07-02 — HS-76-03 done (3/5).** The map tells the truth: the Desk
box, the one runtime bus with live-frame edges, the capability-run
subsystem, the honest two-mechanism preview fork, and the run-born
artifact lane. All diagrams still render. Next: 04 (the WEB_DESK
rewrite), then 05 (SECURITY first, the tail, the mirror check).

**2026-07-02 — HS-76-02 done (2/5).** README presents the Desk: a new
section after the two-modes proof with the real-hub screenshot and the
closed loops (orb → meeting object; rail ask → artifact with lineage;
the badge as the one trust answer), the wake/preview conflation fixed,
and the go-next table pointing at WEB_DESK. Next: 03 ARCHITECTURE.

**2026-07-02 — HS-76-01 done (1/5).** The ledger is in: the systemic
drift is the front-door move (README/ARCHITECTURE/the index/WEB_DESK all
predate the Desk-as-`/`), and the sharpest single finding is SECURITY's
egress table missing three shipped egress doors (the desk webhook, the
GitHub issue write, the desk Slack relay). Seven docs verified current —
the per-phase docs stories did their job. Bonus: the screenshot pass
caught a SHIPPED P75 bug (the empty PreviewCard visible on every route;
`display: flex` beat `[hidden]`) — fixed. Six dead root strays surfaced
as an owner decision. Next: 02 (README) / 03 (ARCHITECTURE) / 04
(WEB_DESK) / 05 (SECURITY + the tail).

**2026-07-02 — scaffolded (0/5).** The audit led; screenshots shot fresh
from a seeded hub, committed under docs/assets/screenshots/.

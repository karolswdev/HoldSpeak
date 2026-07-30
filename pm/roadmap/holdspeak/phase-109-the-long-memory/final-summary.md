# Phase 109 — The Long Memory — FINAL SUMMARY

**The Desk remembers.** Decisions are first-class records with
transcript moments and lifecycles; accepted decisions become artifacts
that cite them; the archive answers text queries with sources; the
Project is a touchable desk object whose memory window carries the
whole loop; and the kernel's running work has its window. The owner's
verdict, verbatim: **"Closeout approved."**

Delivered 2026-07-29/30 — chartered, built, proven, documented, and
closed in one day, in the Fable-orchestrator → Sol-implementation
model, each story its own gated PR (#407–#416).

## What shipped (8/8)

- **HS-109-01** — the decision record: additive v30 `decisions` table,
  text-anchored identity, lifecycle with two-way supersession,
  severed-source survival of meeting deletion, DERIVED at the one
  `record_artifact` chokepoint (a live golden-43 staging caught the
  deferred chain bypassing the first hook placement — moved and
  re-proven live on `.43` against the real archive).
- **HS-109-02** — the transcript moment: v0.2.0 capture with verified
  timestamps (`reported`), exact-anchor backfill (`anchored`), named
  `provenance_drops`, the moment→segment resolver. Two live-caught
  defects fixed and pinned: the stale-CHECK table rebuild (v32) and
  text-anchored identity (provenance reruns update in place).
- **HS-109-03** — promotion: idempotent deterministic ADR / note /
  announcement with `decision:<id>` + meeting lineage; model drafts
  through the registered `inference.run@1` (admitted BEFORE
  generation, receipt naming `result_ref=artifact:<id>`, real `.43`
  generation in evidence); supersession propagates; refusals name the
  successor.
- **HS-109-04** — the memory index: three FTS indexes with
  trigger-maintained freshness, per-kind bm25 tier-interleave,
  `/api/memory/search`, cited grounding with `matched/overflow`
  honesty, the dead meeting-search wire fixed (`q` vs `search`,
  422-pinned). Control-vs-treatment on `.43`: ungrounded invents
  "Project 100"; grounded answers BLUE LANTERN citing the record.
- **HS-109-05** — the Project Memory window: the `project` primitive,
  Timeline/Decisions/Search/Ask faces, in-row accept / supersede /
  promote (no modals), ask-this-project with the egress badge,
  openable citation chips, "Grounded on N of M", project-qualified
  "Since <previous meeting title>". Walked 9/9 live at 1440+393 on a
  copy of the real archive.
- **HS-109-06** — the process window: a pure kernel `read` + `events`
  consumer (endpoint surface pinned by test), no invented states,
  cursor replay byte-equal across restart, live-walked 10/10 with a
  real steer and a real named refusal on screen.
- **HS-109-07** — docs in owner vocabulary at USER_GUIDE /
  ARCHITECTURE / README with a 26-claim truth audit to file:line;
  retention stated plainly; the Phase-107 drift reconciled in
  SECURITY (5 mixed + 9 bypass + 1 dormant = the ledger's 15 debt;
  narrowing unchanged in strength) and BACKLOG candidate Y.
- **HS-109-08** — the closeout: eight beats as one rerunnable command,
  8/8 twice consecutively before the owner (a third session found the
  promotion walk consuming the archive's live decisions — supersession
  is permanent by design; the walk now mints and cleans up its own
  fixture records, rerunnable forever), and the verdict above.

## The invariants held

- Kernel spine byte-identical across the whole phase; effect register
  untouched at **21 total / 3 covered / 3 exempt / 15 debt**.
- Zero plugin/synthesis behavior changes: the memory is a DERIVED
  projection.
- Schema v29 → v32, additive, with the real archive migrated (and one
  baked stale CHECK from an intermediate build rebuilt honestly).

## Method notes (recorded for the next phase)

- The owner dropped UAT staging mid-phase for story proofs ("too
  slow"); live proofs became direct scripts against the real archive
  and the real `.43` (`scripts/hs109_0N_live_proof.py`), with
  isolated-home hub spawns for screenshot walks. Minutes, not hours.
- Findings recorded, not absorbed: the kernel events route exposes no
  `limit` (batch = backend default 100); no web UI calls kernel
  `decide` (needs-you deep-links to the attention shade).

## Suites at close

Full suite 4,360 passed / 37 skipped / only the two known
pre-existing failures (build-ledger staleness, voice-notes 502 copy);
web chain 373/373 + build + guards; doc guard family 55 green.

## Remainders

**Phase 108 — The Locked Room** (RFC §5b confinement) stays reserved
with its machine-asserted work list in BACKLOG candidate Y. New from
this phase: the events-route `limit` gap and the missing kernel
`decide` web surface ride as small candidates whenever the process
window earns controls (after the liveness reaper).

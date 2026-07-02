# Phase 72 — Final Summary

- **Opened:** 2026-07-02 (from a four-track architectural analysis of the
  post-Phase-71 tree). **Closed:** 2026-07-02. Ten live stories (HS-72-07
  cut the same day it was authored, superseded by the owner's React
  migration decision); all ten shipped through the PMO gate, one commit
  per story.

## Goal — was it met?

Yes. The phase's thesis was that the product's spine — its names, wire
contracts, lifecycles, and module shapes — was held together by prose and
habit, and that every prose seam should become a machine-checked one. At
close: the primitive contract is JSON Schemas validated by all three
surfaces; the API surface is a generated, consumer-tagged manifest held by
snapshot tests; "companion" names nothing (the coder picker and the desk
actuator relay have their own prefixes); the actuator lifecycle is one
implementation with owner-typed proposals and no sentinel meeting; the
shadow modules and orphans are gone; the meetings god-module is a package
under budget; the web has exactly one live socket; and the iPad's desk
records embed the Contracts types with the bridge layer deleted.

## The strongest evidence the thesis was right: the bug harvest

Replacing prose with guards found **fourteen real bugs**, several of them
production-severity and none previously suspected:

1. The hub emitted full payloads on tombstones, violating its own
   documented contract (HS-72-01).
2. A hub-pulled KB could never have decoded on the iPad (Swift required an
   `updated_at` the hub never emits for seven kinds) (HS-72-01).
3. `RuntimeProfile.baseURL` could never decode off the wire — hub→iPad
   profile sync was silently broken (HS-72-01).
4. `Agent.manual_context`/`use_zone_context` lossy through hub sync
   (HS-72-01; locked, hub-persistence follow-up filed).
5. The intel-process aftercare callback NameError'd on every real
   invocation since Phase 56 — `aftercare_ready` never fired through
   `/api/intel/process` (HS-72-06).
6.–12. The iPad's record bridges were lossy re-derivations (HS-72-09):
   note tags wiped + createdAt re-minted; KB members wiped; artifact
   identity destroyed on iPad edits (meetingId, type, confidence, status,
   plugin, sources, createdAt all lost); workflow `graphJson` silently
   drained (the HSM-22 carrier); agent tools wiped; chain and directory
   timestamps re-minted.
13. `/presence` double-fired `hs-activity` per frame, and the runtime
   seed never reached DOM listeners (HS-72-08).
14. The exploration record itself: the belief that the Swift client never
   called the actuator relay was wrong (HS-72-03 corrected it in place).

And the new guards caught **three organic drifts within the phase's own
session** (the page deletion, the module moves, the `origin` wire field) —
the loop closing in real time.

## Exit criteria — final state

All ten checked in `current-phase-status.md`, each with per-story
evidence. The closeout matrix, one run: python **3066 passed, 37
skipped**; pre-flight + mermaid + live-bus e2e **7 passed**;
`validate.py` ALL CHECKS PASSED; `swift test` **413 passed, 0 failures**;
Simulator app **BUILD SUCCEEDED**. The live cross-surface walk: a note
created through the real web desk UI → hub row with tags intact → the
sync wire validated against the note schema AND the ChangeSet envelope
(screenshot `screenshots/11-walk-web-note.png`). Both drift guards
proven red one last time and reverted.

## Stories shipped

| Story | One line |
|---|---|
| HS-72-01 | The primitive contract, machine-checked (schemas + 3 guards + kind-set lock) |
| HS-72-02 | The API surface, declared (generated manifest, 229 routes, consumer-tagged) |
| HS-72-03 | "Companion" untangled (`/api/coders/*` + `/api/desk/actuators/*`) |
| HS-72-04 | One actuator lifecycle (schema v5, owner-typed origin, sentinel dead) |
| HS-72-05 | The shadows retired (recorder + tracker renames, orphans deleted) |
| HS-72-06 | The meetings god-module split (7-module package, route table identical) |
| HS-72-08 | One live bus (4 private sockets → 1, robustness inherited) |
| HS-72-09 | The iPad speaks Contracts natively (bridges deleted, 7 fidelity fixes) |
| HS-72-10 | Docs: the honest map (generated artifacts linked, naming canon closed) |
| HS-72-11 | Closeout (this run) |

## Stories cut or deferred

- **HS-72-07** (decompose `history.astro` in place) — cut the day it was
  authored: the owner decided interactive web surfaces migrate to React
  (Phase 73's foundation), making an in-place Astro decomposition wasted
  motion. `/history`'s migration is future-phase work.

## Surprises and lessons

- **Bridges rot into lies.** Every hand-written re-derivation in the
  bridge layer had drifted into data loss. The fix that holds is
  structural (embed the canonical value), not review discipline.
- **A declared surface is a refactor harness.** The manifest turned two
  risky refactors (the rename, the split) into diff-readable identity
  proofs, and caught its own organic drifts the same day it landed.
- Traps recorded for the next agent: the `schema_version` PK takes a
  second row under `INSERT OR REPLACE` (readers take MAX); a
  `page.evaluate` whose expression value is an armed promise awaits
  itself; the sim build needs `patch-llm-macro.sh` + a pinned
  derived-data path; the `runtime_activity` WS frame is a wire name, not
  the module.

## Handoff

- **The standing owner walk:** the iPad on real metal with existing
  on-device data (the legacy `@AppStorage` decode in anger) plus the
  coder-board and desk-relay taps against the renamed routes — flagged in
  the 03/09 evidence, the one proof class this phase could not produce
  itself.
- Follow-ups filed: persist `agent.manual_context`/`use_zone_context` on
  the hub (ends the schema-documented loss); a real `runtime_queue`
  frame for QueueHud; `db/activity.py` (1,596 lines) as the next module
  candidate; the coders-status payload still reports desk connector
  config (a residual conflation, noted in 03/04 evidence).
- Phase 73 (The Desk, Inhabited — React foundation, stacked branch)
  builds directly on this phase's contract guards, live bus, and route
  naming.

## Final asset / test posture

Python 3066 passed / 37 skipped (up from 3045 at open: +8 contract, +5
api-surface, +4 migration, +1 aftercare regression, +3 live-bus e2e, +19
Swift-side excluded — plus reworked markers); Swift 413 passed (up from
394: +19 DeskRecordsTests); web 18 pages (one dead page removed); 229
routes declared, 44 iOS-consumed / 151 web-consumed.

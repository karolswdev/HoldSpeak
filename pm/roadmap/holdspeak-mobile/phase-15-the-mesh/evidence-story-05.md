# Evidence — HSM-15-05 (one approval + egress contract) — done PRE-PAID

**Recorded 2026-07-05 by the resume survey.** The story's own grounding (2026-06-22) said
the contract already existed and named ONE genuine delta. That delta, and every acceptance
row, shipped in other phases while this one slept. Receipts, per acceptance criterion:

## 1. Shared egress scope — shipped (Phase 21, "honest everywhere")

- The ONE egress grammar is a Contracts type: `apple/Sources/Contracts/EgressScope.swift`
  (on device / local + named target / cloud + named target), consumed by every badge and
  chip; the Swift prose guard refuses narrated privacy sentences (it caught its own 7th
  site when it landed).
- The web/desktop side is the canonical `egress:{scope,label}` badge (POSITIONING canon;
  `web/src/scripts/egress-badge.js`, the desk chrome + pull-out chips).
- The two-surface trust chip reads the same `/api/setup/status` posture on the app header
  and the web header, mapped by the same four-state precedence (Phase 21).

## 2. One approval act, same id, audit parity — shipped (Phases 56 / 19 / 72)

- The delta this story named — **decouple `actuator_proposals` from `meeting_id`** —
  shipped in the one-spine phase as the owner-typed proposal origin: `origin='meeting'`
  requires a real meeting id; `origin='desk'` (the iPad desk relay) carries
  `meeting_id=None`; the old hidden sentinel meeting is gone
  (`holdspeak/db/actuators.py`, locked by `tests/unit/test_db_actuator_origin.py`).
- Qlippy card Approve ≡ dashboard Approve (audit parity, Phase 56); the iPad decides real
  proposals against the same ids with `decided_by: "ipad-companion"` verified on a live
  hub (Phase 19, walk rider W5 staged).
- Device-initiated actions ride the desk actuator relay (`api/desk/actuators/*`): the iPad
  proposes and approves; the executor runs ONLY on the hub (one 5-gate stack:
  status → policy → payload-parity → connector → audit).

## 3. Air-gapped safety (draft + badge, never a fake send) — shipped (17-05 / 16-09)

- The coder-answer draft seam (17-05) produces a LOCAL draft with the honest badge when
  the run is on-device; where the draft runs is not where the answer goes, and nothing
  sends without the explicit human act.
- The desk Ask's printed card wears the resolved per-run scope (On-device vs the named
  host) — the 16-09 egress-honesty fixes; a run with no reachable endpoint parks/falls
  back under the runner's failure policy rather than pretending.

## What did NOT move here

- **Approve from the iPad QueueHUD** is HSM-15-03's acceptance (the HUD is where mobile
  approval happens) — explicitly left with 15-03, not claimed by this record.
- The Workbench **Slack sink → desktop connector** routing is HSM-15-02's remaining slice
  (the sink currently never proposes through the hub from a canvas run) — left with 15-02.

## Lesson (the standing one, again)

The survey that opened this phase (2026-06-22) was right about the machinery and still
under-credited how fast the deltas would be paid by other phases. Pre-paid credit is only
real once the surface's code is read — this record cites files and locks, not memory.

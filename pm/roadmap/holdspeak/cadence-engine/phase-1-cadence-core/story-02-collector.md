# CAD-1-02 — The collector (sources → source-projected loops)

- **Program:** cadence-engine · **Phase:** 1 · **Status:** done (built + tested; CI green)
- **Depends on:** CAD-1-01. **Unblocks:** 1-03 (scoring reads loops), 1-05 (CLI shows them).

## Problem

Loops must be *projected* from real HoldSpeak state, idempotently, so re-running never duplicates
or resurrects user-decided loops.

## The design

`holdspeak/cadence/collector.py` → `class LoopCollector`. Phase 1 collects **two** of the design's
source types (the rest land in later phases — agent sessions in Phase 3, etc.):

1. **Meeting action items.** Read open/accepted items via the meeting repo (`action_items`,
   `db/core.py:200`; `MeetingRepository` houses them). For each `status="pending"` item, build an
   `OpenLoop(source_type="meeting_action", source_id=item.id, title=item.task, owner=item.owner,
   project=resolve_project(...), …)` and one `EvidenceRef(kind="action_item", id=item.id,
   deep_link="/meetings/<mid>#ai-<id>")`. Low-confidence / unreviewed items (`review_state="pending"`
   below a threshold) project as **`needs_review` quiet loops** (chart §3.6).
2. **Pending actuator proposals.** Read `status="proposed"` rows via `ActuatorRepository`
   (`db/actuators.py`); each → `OpenLoop(source_type="proposal", source_id=proposal.id,
   title=proposal.preview, …)` + `EvidenceRef(kind="proposal", …)`. **Read only** — Phase 1 proposes
   nothing.
3. **Projection = idempotent upsert** via `CadenceRepository.upsert_loop` keyed
   `source_type:source_id`. A source that disappears (action completed/dismissed) closes its loop
   (`status="closed"`) rather than deleting it (audit trail). A `killed` loop is never reopened by
   re-collection.
4. **`resolve_project()`** (`holdspeak/cadence/projects.py`) — the one normalizer (chart §3.7):
   explicit `project_id` → meeting linkage → repo-root basename / domain.

## Scope

- **In:** `LoopCollector.collect()` over meeting actions + pending proposals; `resolve_project`;
  close-on-source-gone; `needs_review` projection.
- **Out:** agent sessions (Phase 3), activity/dictation/manual sources (later), scoring (1-03),
  any proposing/executing.

## Proof / acceptance

- Against a seeded DB (imported meeting with 3 actions + 1 pending proposal), `collect()` yields 4
  loops with correct evidence + deep links; a second `collect()` yields the same 4 (no dupes).
- Completing an action then re-collecting flips its loop to `closed`, not a new row.
- A loop manually set `killed` stays killed after `collect()`.

## Test plan

`tests/integration/test_cadence_collector.py` — seed meetings/actions/proposals, assert projection
counts, idempotency, close-on-gone, killed-survives. `uv run pytest -q tests/integration/test_cadence_collector.py`.

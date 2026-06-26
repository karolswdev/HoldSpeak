# HSM-15-03 — The mesh queue (desktop jobs + approvals in the QueueHUD)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** backlog
- **Depends on:** the `QueueHUD` / `RunQueueStore` / `QueuedJob` (built Phase 14/15 craft);
  `HTTPDesktopClient`; HSM-15-04 (real on-device jobs); HSM-15-05 (the approval contract).
- **Owner:** unassigned

## Grounding (2026-06-22)

The desktop already tracks in-flight work and approvals — just **not unified**: the MIR plugin-run
queue (`web/routes/activity/plugin_jobs.py`, DB-backed, status/attempts/retry), the meeting intel
queue (`holdspeak/intel_queue.py`), and actuator proposals (`GET /api/meetings/{id}/proposals`). The
new work is a thin **aggregation** — one "everything in flight + everything pending approval"
endpoint the iPad polls — plus merging it into the already-built `QueueHUD`. We are not building a
queue from scratch; we are giving the existing ones one window. (Approval-from-the-HUD reuses the
existing `…/proposals/{pid}/decision` route; see HSM-15-05.)

## Vision (owner)

> "I want to make sure this queue is a first-class citizen in the entire application… 1000%
> transparency — what's being queued, what's being asked, what's being worked on."

The QueueHUD is the right surface (a Dynamic-Island-style pill above every screen, expandable to a
ledger). The mesh makes it **whole**: a long digest grinding on the Mac, a desktop actuator
awaiting your approval, a blocked endpoint — **all in the same pill on the iPad**. You approve a
desktop action from the glass in your hand. The queue is the mesh's unified transparency + approval
spine.

## The design

- **Mesh jobs in the ledger.** `RunQueueStore` merges on-device jobs with desktop jobs polled from
  the server (a `/api/queue` or the companion/actuator status it already exposes). Each job carries
  its **origin** (this iPad / your Mac) and its target, so the row reads honestly.
- **Pending approvals are jobs.** A desktop `propose→approve→execute` proposal awaiting your nod
  shows as a `blocked`-style row with an **Approve** affordance — approving it from the QueueHUD is
  the same act as approving it on the desktop (HSM-15-05).
- **Unreachable peer is a first-class queue state.** When the Mac is asleep/unreachable, its jobs
  show as `blocked · peer unreachable · auto-resumes` (the spine already frames an unreachable
  desktop this way) — never an error spinner.
- **No prose.** Tight chips and the same status vocabulary (working / blocked / queued / done),
  origin glyphs (iPad / Mac), the progress bar — consistent with the built HUD.

## Acceptance criteria

- [ ] **Merged ledger** — the QueueHUD shows on-device jobs + desktop jobs together, each labeled by
      origin (iPad / your Mac) and target. LAN-proven.
- [ ] **Approve from the HUD** — a pending desktop actuator proposal appears as a job with an
      Approve action; approving it executes on the desktop (one act, HSM-15-05). LAN-proven.
- [ ] **Unreachable peer** — desktop jobs degrade to a first-class `blocked · auto-resumes` state
      when the Mac is unreachable. Simulator-shot.
- [ ] **Consistency** — origin/status/egress chips match the built HUD vocabulary; no prose.

## Build plan

1. Define the desktop-job poll (reuse the companion/actuator status the server already exposes;
   add a thin `/api/queue` only if needed).
2. `RunQueueStore` merges origins; `QueuedJob` gains `origin` + (for proposals) an approve hook.
3. QueueHUD rows render origin + the Approve affordance for proposals.
4. First-class unreachable-peer state.
5. LAN proof (a desktop job + a pending proposal appear and are approvable from the iPad) +
   Simulator shots.

## Test plan

- Host: the merge/ordering + unreachable-degradation logic unit-tested with a fake `DesktopClient`
  (assert origins preserved, proposals surface an approve hook, unreachable → blocked-not-error).
- LAN: a real desktop job + a real pending actuator proposal appear in the iPad HUD; approving
  executes on the desktop.
- Simulator: merged ledger + unreachable-peer state shot.

## Notes

- The HUD is already built and injected app-wide (Phase 15 craft); this story makes its data
  **mesh-wide**. No new transport — it rides `HTTPDesktopClient`.
- Approval here and the desktop's actuator approval are the SAME model (HSM-15-05), so this story
  and 15-05 are co-built.

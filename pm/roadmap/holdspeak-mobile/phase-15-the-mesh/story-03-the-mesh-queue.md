# HSM-15-03 — The mesh queue (desktop jobs + approvals in the QueueHUD)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** done (2026-07-05 — see `evidence-story-03.md`: the hub gained
  `GET /api/mesh/inbox` (the one window: both real queues in flight + every `proposed`
  actuator proposal across meeting AND desk origins), the QueueHUD gained the mesh lanes
  (hub jobs origin-labeled with the peer's name; proposals as approve/reject rows;
  unreachable peer = a first-class blocked state), and the whole loop was proven live:
  the Simulator polled a REAL scratch hub, the ledger rendered its real jobs + both
  proposals, and an approve from the HUD transitioned the desk-origin row on the hub
  with `decided_by: ipad-companion` through the real guarded executor (no webhook
  configured → an honest `failed`, never a fake "sent"). The cabled-iPad LAN beat joins
  the phase's owner queue. This commit also WIRED `PresenceStore.startPolling` (the
  survey's 15-08 finding) at the same paired-peer call site.)
- **Depends on:** the `QueueHUD` / `RunQueueStore` / `QueuedJob` (built Phase 14/15 craft);
  `HTTPDesktopClient`; HSM-15-04 (real on-device jobs); HSM-15-05 (the approval contract).
- **Owner:** agent (Fable)

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

- [x] **Merged ledger** — the QueueHUD shows on-device jobs + desktop jobs together, each
      labeled by origin (the peer's name with the desktopcomputer glyph) and target —
      proven with LIVE polled rows from a real local hub (`hsm-15-03-live-inbox.png` and
      the seeded merged shot `hsm-15-03-unreachable.png`; the cabled-iPad LAN beat joins
      the owner queue).
- [x] **Approve from the HUD** — a pending desktop actuator proposal appears as an
      approve/reject row; approving drives the SAME decision route the desktop uses and
      the hub's row transitioned with `decided_by: ipad-companion` (the headless decide
      affordance drives the exact `decideMesh` the tap drives).
- [x] **Unreachable peer** — desktop jobs degrade to `blocked · peer unreachable ·
      auto-resumes` + the footer names the peer; the last-known rows stay (never an
      error spinner). Simulator-shot.
- [x] **Consistency** — the mesh rows reuse the HUD's exact status vocabulary, chip and
      capsule treatments, and glyph grammar; the pill gains one tight "N to approve"
      chip. No prose.

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

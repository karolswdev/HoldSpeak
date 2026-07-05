# Evidence — HSM-15-03 (the mesh queue) — DONE

**Closed 2026-07-05.** The owner's bar ("1000% transparency — what's being queued, what's
being asked, what's being worked on") now spans the mesh: the hub's work and the hub's
asks ride the same pill on the iPad, and approving from that pill IS approving on the
desktop.

## What shipped

### The hub: one window (`GET /api/mesh/inbox`, routes/mesh.py)

- **Jobs**: the in-flight rows from BOTH real queues — the deferred intel queue (via the
  existing `build_runtime_queue_frame`) and the MIR plugin-run queue. Failures ride the
  counts, not the job list (the HUD's footer vocabulary). The plugin queue's integer DB
  id crosses the wire as a kind-prefixed STRING (`plugin:<n>`) so companion rows are
  string-typed and unique across lanes.
- **Proposals**: every `proposed` actuator row across meeting AND desk origins via the
  new `ActuatorRepository.list_pending_proposals` (the meeting-scoped lister could never
  see a desk-origin row except by id). The wire carries what a companion needs to render
  and DECIDE (origin + target pick the existing decision route); **the payload never
  rides** — the hub keeps the parity source of truth.
- Aggregation only: the queues and the decision routes are untouched. Normal auth
  applies (only `/api/mesh/info` stays exempt).

### The iPad: the mesh lanes in the QueueHUD

- `RunQueueStore` polls the paired peer every 5s (`startMeshPolling`); hub jobs render
  with the HUD's exact vocabulary, origin-labeled with the peer's name; proposals render
  as approve/reject rows; the pill gains "N on <peer>" + a "N to approve" chip.
- **Approve/Reject from the HUD**: `decideMesh` routes by origin — meeting rows through
  the existing `decideProposal`, desk rows through the new `decideDeskProposal` (literal
  per-connector paths; an unknown target is refused client-side) — then re-polls so the
  row settles to fresh truth. `decided_by: "ipad-companion"` rides both.
- **Unreachable peer is a first-class state**: a failed poll flips the lane, the
  last-known rows degrade to `blocked · peer unreachable · auto-resumes`, and the footer
  names the peer. Never an error spinner; recovery is automatic on the next good poll.
- The same commit **wired `PresenceStore.startPolling`** (the resume survey's 15-08
  finding: it had NO call site) at the one paired-peer call site in the app root, so the
  waiting-agents lane goes live alongside the inbox poll.

## A wire find fixed before it shipped

`decideDeskProposal` originally decoded the shared `ProposalDecision` — whose
`MeetingProposal.meetingId` is non-optional, so a SUCCESSFUL desk decision (meeting_id
null on the wire) would have thrown `malformed`. It now decodes a tolerant
`DeskProposalDecision {success, error}` (the HUD re-polls for state anyway), and the
client test's stub carries the real null-meeting envelope.

## Proof

- **Hub**: `uv run pytest tests/unit` → **2486 passed** (new `test_mesh_inbox.py`: the
  aggregate envelope with both origins + no payload on the wire + the string plugin id;
  the pending-lister lock; the honest empty). api-surface regenerated (241 routes).
- **Swift**: `swift test` → **479 / 9 skipped / 0 failures** (new
  `MeshInboxClientTests`: the envelope decode off the real route shape, the desk
  decision's route + `decided_by`, non-2xx throws). App simulator build green.
- **Live (Simulator + a REAL scratch hub**, `scripts/proof_hsm15_mesh_inbox_hub.py`):
  - `screenshots/hsm-15-03-live-inbox.png` — the LIVE ledger: pill "2 on Karol's Mac",
    both real proposals with Approve/Reject, the hub's intel + plugin jobs beneath.
  - The decide affordance (the same `decideMesh` the tap drives) approved the first
    pending row; the hub printed the receipt:
    `status=failed decided_by=ipad-companion` for the desk webhook proposal (approved →
    the real guarded executor ran → no webhook configured → an HONEST failed, never a
    fake "sent") while the untouched github proposal stayed `proposed`.
  - `screenshots/hsm-15-03-approved.png` — the decided row gone from the pending lane.
  - `screenshots/hsm-15-03-unreachable.png` — the merged ledger (on-device jobs keeping
    their live states) with the hub rows degraded to `blocked · peer unreachable ·
    auto-resumes` + the peer-named footer.
- The cabled-iPad LAN beat joins the phase's owner queue (with 15-01/02/04's beats).

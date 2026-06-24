# HSM-15-05 — One approval + egress contract (across surfaces)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** backlog
- **Depends on:** the desktop actuator path (propose→approve→execute, exists on the server);
  the mobile egress badge (POSITIONING canon); HSM-15-03 (approve-from-the-HUD).
- **Owner:** unassigned

## Grounding (2026-06-22)

The contract already EXISTS and is genuinely one primitive: `ActuatorProposal` + `ActuatorExecutor`'s
5-gate stack (status → policy → payload-parity TOCTOU → connector → audit), with Slack/GitHub/webhook/
voice-macro all routing through it (`plugins/actuator_executor.py`, `web/routes/meetings.py`). The
egress badge is already a single `egress:{scope,label}` contract. The **one real gap**: the
`actuator_proposals` table is **meeting-scoped** (`meeting_id` FK), so device-initiated / non-meeting
actions (a voice-macro fire, a future iPad-initiated send) are audited only via logs, not the
proposals ledger. The new work is to **decouple the proposal/audit ledger from `meeting_id`** so every
cross-device action shares the one contract — not to invent a contract.

## Vision

The desktop's `propose→approve→execute` actuators and the mobile's egress badge are the **same
idea**: nothing leaves the mesh without your nod, and you are always told the scope. Today they are
two implementations. This story makes them **one contract**, so approving on either surface is one
act and the egress scope reads identically everywhere.

## The design

- **One egress model.** The scope vocabulary is shared: `local` (stays in the mesh) / `local+cloud`
  / `cloud → {target}`. Every surface that can emit — a Workbench Slack sink, a desktop actuator, a
  dictation that leaves the LAN — states the scope with the **one badge**, never a sentence
  (POSITIONING canon: no privacy novels).
- **One approval act.** A proposal is a single object regardless of where it surfaces. Approving it
  in the iPad QueueHUD (HSM-15-03) and approving it on the desktop are the same call against the same
  proposal id; double-approval is idempotent; an approval is auditable on both surfaces.
- **Air-gapped is the default-safe path.** With no reachable cloud/peer, an action that *would* emit
  degrades to a **draft + the badge** — never a silent send, never a fake "sent". The air-gapped
  session (HSM-15-06) proves this: value is produced, nothing leaves.

## Acceptance criteria

- [ ] **Shared egress scope** — one badge vocabulary (`local` / `local+cloud` / `cloud → target`)
      used by Workbench sinks, desktop actuators, and dictation. No prose anywhere.
- [ ] **One approval** — a proposal approved in the iPad HUD executes on the desktop (same id);
      idempotent; audit parity on both surfaces. LAN-proven.
- [ ] **Air-gapped safety** — with no reachable target, an emitting action degrades to draft + badge;
      never a silent or fake send. Verified.

## Build plan

1. Extract the egress scope into one shared model (Contracts) used by all emitting surfaces.
2. Unify the proposal/approval object + the approve call (desktop ↔ HUD) on one id; idempotent execute.
3. Air-gapped degradation path (draft + badge) wired everywhere an emit can happen.
4. LAN proof (approve from the iPad → desktop executes; audit parity) + the air-gapped verification.

## Test plan

- Host: the egress-scope mapping + the approval-idempotency logic unit-tested; air-gapped degradation
  (emit → draft+badge) unit-tested with a fake/unreachable client.
- LAN: approve a real desktop proposal from the iPad HUD; confirm the desktop executes once and both
  surfaces show it.

## Notes

- Co-built with HSM-15-03 (the HUD is where mobile approval happens).
- This is the trust spine of the whole phase — and the thing that makes the air-gapped proof
  (HSM-15-06) honest rather than theater.

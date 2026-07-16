# HS-93-07 — Secure, Normal, or YOLO

- **Project:** holdspeak
- **Phase:** 93
- **Status:** done
- **Depends on:** HS-93-02, HS-93-03, HS-93-04
- **Unblocks:** HS-93-08, HS-93-09
- **Owner:** unassigned

## Problem

Central policy, grants, and receipts exist, but the current matrix is narrower
than the owner's automation intent: YOLO still asks for grants/approvals in
several families and unknown families inherit old behavior. Secure, Normal, and
YOLO must become one complete AI-OS posture across React and Swift.

## Scope

- **In:** Implement the phase-local `control-mode-contract.md`; keep versioned
  `safe`/`neutral` wire compatibility while rendering Secure/Normal; cover every
  consequential primary-journey family in the central resolver; contextual
  operation/policy summary on source subjects, Qlippy,
  Mission Control, History, Coder, Integration, Cadence, Web and Swift Queue;
  exact commitment/destination labels; mode source and effect; bounded grant
  issue/use/revoke in Secure/Normal; zero HoldSpeak approval prompts in YOLO for
  eligible configured/registered actions; changed-payload/destination/pane
  refusal; receipt return.
- **Out:** More permissive arbitrary shell authority, scattered mode branches,
  or weakening any hard invariant.
- **Paths:** operation policy, grants/actuators/steering/cadence, authority and
  proposal routes, Web Settings/trust/Desk/History/Ambient/Mission Control,
  Swift Settings/Desk/Queue/Coder/Review, tests, Security and UAT.

## Acceptance criteria

Rescoped 2026-07-15 by direct owner decision: the story closes at the two
delivered authority families — configured Integration writes (Slack, Webhook,
GitHub) and registered Coder text/allowed-key steering — plus their shared
client expression. The remaining operation-family matrix, Qlippy/Mission
Control/Cadence treatment, owner walks, and physical-device evidence move to
[BACKLOG candidate X](../BACKLOG.md) and are not claimed here.

Accepted at the delivered scope:

- [x] Every proposed configured-Integration or registered-Coder effect states
      what will happen, the named destination, whether approval executes now or
      queues work, and the current authority basis before the decision
      (operation-policy v2 snapshot, rendered at the Desk action point, History,
      Coder pull-out, Web Settings, and Swift Queue/Receipt details).
- [x] Secure, Normal, and YOLO show their practical effect at these action
      points; changing posture affects future decisions only — an existing
      proposal keeps its immutable policy snapshot and is never silently
      widened, and a posture change revokes active grants.
- [x] YOLO executes the eligible configured Slack/Webhook/GitHub destination and
      the registered or exact-pane Coder text/allowed-key delivery with zero
      HoldSpeak approval, grant, or arm prompt; the posture is the recorded
      authority basis and every attempt produces a complete source-linked
      Receipt.
- [x] Secure retains exact per-action decisions and Normal allows a matching
      bounded scoped grant for these families; grants are no longer a YOLO
      prerequisite anywhere.
- [x] Payload, destination, identity, pane, configuration, and grant-posture
      changes refuse before effect in every mode: the executor re-verifies the
      durable payload/destination/audit binding before egress, and the typing
      node re-resolves the canonical `%N` immediately before a keystroke.
- [x] An unregistered destination, unresolved pane, or unknown operation family
      resolves to a named refusal in all postures and never enters the approval
      queue; YOLO never auto-allows an unknown operation.
- [x] React and flagship Swift decode the same versioned policy snapshot,
      labels, source, reason codes, and Receipt fields for the delivered
      families; neither client keeps a private posture matrix for them.
- [x] Authority, refusal, and Receipt copy on the delivered surfaces passes the
      controlled product-copy census with zero violations.

Descoped to BACKLOG candidate X (owner decision 2026-07-15):

- Central policy coverage for dictation delivery, inference, Coder
  factory/destructive operations, Mission Control/workflows, sync, cadence, and
  destructive Desk mutations, with zero-prompt YOLO for those families.
- Bounded grant issue/use/revoke presentation (actor, scope, TTL/count,
  remaining uses, revoke) with per-use source-linked Receipts.
- Shared Qlippy, Mission Control, and Cadence commitment treatment with no
  consequential fallback verb.
- Owner control/treatment walks with prompt counts and prediction verdicts;
  physical Web/iPhone/iPad evidence with exact provenance.

## Test plan

- **Unit:** full operation/posture/grant/invariant matrix plus rendered commitment
  labels in Python, Vitest, and Swift.
- **Integration:** proposal, connector, steering, cadence, Qlippy, Mission
  Control, Queue, and receipt routes with immutable binding failures.
- **Manual / device:** On Web/iPhone/iPad, execute the same Integration, Coder,
  inference, dictation, sync/cadence, and destructive Desk operations in Secure,
  Normal, and YOLO; count HoldSpeak prompts and prove YOLO=0 while invariant
  failures still refuse.

## Notes / open questions

OS-owned permissions are not HoldSpeak approval prompts. New arbitrary
destinations or capabilities remain ineligible until configured/registered;
YOLO is frictionless authority, not ambient remote-code execution.

The 2026-07-11 Coder slice applies that boundary to text and allowed keys:
Secure/Normal retain exact-pane grants; YOLO uses a registered session or exact
`pane:%N` without an arm prompt; the typing node re-resolves the read-side pane
identity and records the operation-policy snapshot and source-linked Receipt.
The Desk keeps rename/kill controls separate pending factory/destructive
classification; this slice does not claim posture authority for them.

Bundling note: this initial Phase-93 scaffold is intentionally committed with
the HS-93-01 through HS-93-05 in-progress implementation slices because the
owner directed that the complete shared working tree ship together. No story is
marked done; each closure gate remains independent.

Closure note (2026-07-15): the owner directed that this story close at the two
delivered authority slices so the phase can proceed to the cross-client UI
consistency remediation. The rescope is recorded in the acceptance section
above, in the phase status file's decision log, and as BACKLOG candidate X;
nothing from the original scope is silently dropped.

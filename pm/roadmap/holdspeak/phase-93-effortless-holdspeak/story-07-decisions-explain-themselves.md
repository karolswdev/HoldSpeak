# HS-93-07 — Secure, Normal, or YOLO

- **Project:** holdspeak
- **Phase:** 93
- **Status:** in progress
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

- [ ] Every proposed external or destructive effect states what will happen,
      the named destination, whether approval executes now or queues work, and
      the current authority basis before the decision.
- [ ] Secure, Normal, and YOLO show their practical effect on the Desk and at the
      action point; changing posture affects future decisions only and never
      silently widens the current proposal.
- [ ] YOLO executes every eligible configured/registered primary-journey
      operation with zero HoldSpeak approval, grant, or arm prompt; the posture
      is the authority basis and the operation still produces a complete Receipt.
- [ ] Secure uses previews and explicit authority at boundary-crossing,
      destructive, or automated effects; Normal lets routine local/configured
      work flow and asks only where consequence or authority materially changes.
- [ ] Grants show actor, operation, destination, data/resource scope, TTL/count,
      remaining uses, and revoke; every use creates a source-linked Receipt.
- [ ] Payload, destination, identity, pane, configuration, expiry, count, and
      revoke changes refuse before effect in every mode with the same invariant
      matrix.
- [ ] Missing OS permission, credential, pairing, destination, pane, or declared
      capability refuses by name in all postures; an unknown operation is never
      auto-allowed by YOLO.
- [ ] Qlippy, Mission Control, History, Coder, Integration, Cadence, and native
      Queue consume the same commitment/reason result; no fallback path renders a
      bare consequential Approve/Apply/Run.
- [ ] Authority, warning, refusal, grant, and Receipt copy follows
      `copy-contract.md`; Qlippy supplies no banter, guilt, invented urgency, or
      personality prose around consequential decisions.
- [ ] Owner control/treatment walks correctly predict the result before acting
      and find the outcome Receipt on the originating Desk subject.
- [ ] React and flagship Swift consume the same versioned policy decision,
      labels, source, reason codes, and receipt fields; client-specific posture
      branches are mechanically forbidden.

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

Bundling note: this initial Phase-93 scaffold is intentionally committed with
the HS-93-01 through HS-93-05 in-progress implementation slices because the
owner directed that the complete shared working tree ship together. No story is
marked done; each closure gate remains independent.

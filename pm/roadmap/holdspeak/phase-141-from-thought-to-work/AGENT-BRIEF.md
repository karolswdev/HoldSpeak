# Phase 141 agent brief — From Thought to Work

Read, in order:

1. [`current-phase-status.md`](./current-phase-status.md)
2. [`../proposals/thought-refinement-spine.md`](../proposals/thought-refinement-spine.md)
3. your assigned story file
4. [`docs/internal/ORCHESTRATION.md`](../../../docs/internal/ORCHESTRATION.md)

## The job

Implement the ruled draft-to-proposal loop by joining existing Note, Ask,
grounding, actuator, policy, kernel, and receipt seams. Do not invent a parallel
agent/chat/tool system.

## Non-negotiable engineering rules

- Verify source anchors against current HEAD before editing.
- All workers share one tree. Touch only owned files; never repair another
  worker's in-progress files.
- Focused tests only. The orchestrator owns assembled suites and glass.
- No staging, commits, pushes, evidence, story-status flips, or PMO edits unless
  the orchestrator explicitly sends SHIP.
- Raw custody and expected-revision CAS are product correctness, not polish.
- Context travels as qualified refs and hydrates server-side.
- Semantic clarification and tool-required fields are distinct concepts.
- Build for the power user first. Fresh installs are YOLO: configured eligible
  effects proceed through the existing executor with receipts. Do not add an
  approval or confirmation layer; Neutral/Safe keep the decision behavior they
  already own.
- Progressive disclosure hides secondary configuration, diagnostics, and
  advanced choices. It must not hide the primary capability or reduce the
  default flow to a demo.
- Local typed writes use canonical services. External effects begin at the
  existing `ActuatorProposal` and use linked kernel admission.
- Never imply Jira/calendar writes exist.
- Fail open to the editable working Note; never fabricate AI/tool success.

## Stop conditions

Stop and report immediately if implementation requires:

- mutating the raw snapshot;
- using two mutable Notes as the only original/working boundary;
- browser-authoritative copied context;
- a second proposal lifecycle for external effects;
- execution without existing posture/policy/actuator/kernel seams;
- a redundant confirmation in front of an owner action or YOLO-eligible effect;
- a generic tool router or universal JSON domain write;
- more than one primary action in a 393px state.

## Shipping protocol

Report exact files changed, tests collected/run, output tail, and any unverified
claim. Hold for orchestrator verification and an explicit SHIP instruction.

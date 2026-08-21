# HS-141-04 — One useful question

- **Status:** done
- **Depends on:** 141-02, 141-03, 141-06
- **Unblocks:** 141-05, 141-07

## Problem

Ask is one-shot and in-memory. Refinement needs one owner-triggered question and
reviewable synthesis without silently turning into an autonomous chat loop.

## Scope

Adapt the existing Ask/inference authority to one refinement turn. **Ask one
question** freezes working/context revisions, submits one bounded grounded run,
persists its invocation/result link, and presents one question or synthesis in
the Thought Workbench. **Add to Note** stops after the answer; **Add & ask next**
atomically appends it and reserves at most one next turn. Only an explicit owner
action starts that turn.
Use the refinement-owned correlation contract from HS-141-02: the caller-stable
request ID binds the frozen thought/working/context revisions, Ask invocation,
kernel operation, and persisted review result. Reload may reveal a result only
after that exact result is durable and reconciled to the same request.

## Acceptance

- [x] Raw/working are durable before dispatch and frozen revisions are named.
- [x] One action produces at most one outstanding question/result.
- [x] Accept is an expected-revision working edit; Reject changes nothing.
- [x] Failure/refusal/timeout leaves completion and editing available.
- [x] Reload reconciles only a known persisted result; no automatic continuation.
- [x] An invocation/result lacking the exact durable correlation tuple cannot be
  attached to a thought, even when its prose appears to match.
- [x] Model receipts retain honest placement/egress without thought text entering
  the kernel journal.

## Tests

Focused refinement service/UI tests; accept/reject/conflict/reload/refusal; exact
one-dispatch and no-auto-chain assertions.

## AI setup recovery rider

When admission has no ready model, the Workbench sends the owner to the same
guided **Choose your AI** screen used by Settings. The ordinary path begins
with **This device**, discovers locally stored models through the existing
runtime-options projection, and checks readiness without sending a prompt.
Per-job choices follow; reusable endpoints and topology remain available under
the disclosed **AI connections** section. No new model authority or setup API
was introduced.

# HS-106-08 - Userland — PR follow-through, the tech-lead's loop

- **Project:** holdspeak
- **Phase:** 106
- **Status:** done
- **Depends on:** HS-106-07
- **Unblocks:** HS-106-09
- **Owner:** unassigned

## The thesis (the bar)

The kernel spine is invisible. This story is the phase's visible
half — the first §9 userland program, and the answer to the owner's
charge: *a Tech-Lead/Architect who uses AI day to day and follows on
to PRs.*

It is chosen because it is the only §9 program that exercises all
three heterogeneous slices at once: reading a PR and dispatching a
scoped agent into a worktree is **terminal input**, proposing an
outward comment or status is **actuator egress**, and summarizing a
diff or drafting the reply is an **inference run**. If the kernel is
real, this program is a few hundred lines of userland over four
calls. If it is not, this story will need to reach around the kernel
— and that reaching is itself the honest finding.

The bar: the owner opens the desk in the morning, sees which of his
PRs need him, decides once per PR, and every consequence that leaves
his machine has a receipt he can read.

## Problem

HS-104-04 gave PR receipts a read side: registered sources' PRs as
honest rows, CI conclusion not logs, observed-at always printed,
epistemic attribution (exact / name-match-only / unattributed),
needs-you ordering. It is a **window**, not a loop. The owner can
see that a PR needs him and then must leave the desk to do anything
about it. Nothing in the system turns "this PR needs a change" into
"an agent is working on it, here is the receipt."

## Recipe

1. **The loop, named.** For each PR row that needs the owner:
   read → decide → act → receipt. The decision is the owner's and
   happens once; everything after it is the desk's work with a
   receipt per consequence.
2. **The verbs, deliberately few.** The first matrix is small and
   fully honest — the HS-105-02 discipline. Every verb is a kernel
   operation:
   - **Send an agent at it** — `process.spawn` plus `process.input`:
     a scoped agent in a worktree, given the PR, the diff, and a
     bounded instruction. This is slice I, doing what the owner
     already does by hand through xterm.js.
   - **Draft the review** — `inference.run` over the diff and the
     linked story or evidence. Produces an artifact on the desk. It
     never posts.
   - **Post the comment or status** — an actuator proposal (slice
     II): PROPOSED, never sent, until the owner approves. The
     drafted text is visible in full before approval, and the egress
     badge names GitHub.
   - **Nothing else in v1.** Merging, closing, force-pushing, and
     approving reviews are out — they are the acts where a wrong
     automation costs the most and the trust is not yet earned.
3. **Refuse by name.** A verb unavailable for a row (no worktree, no
   `gh` credentials, a local-only branch) refuses with the reason
   stated, reusing HS-104-04's honest-degradation idiom rather than
   hiding the row.
4. **Every consequence is receipted where it happened.** The agent's
   own tool calls inside its run are CHILD operations (HS-106-07's
   clause-2 mechanism), so "an agent pushed a commit for me" is a
   receipt, not a rumour.
5. **The surface is the desk, not a new app.** PR rows are desk
   objects with the Phase-105 grammar: state at rest, Info on
   everything, drop-onto where it means something (drop a PR on an
   agent to send it at it — the existing verb, not a new one). No
   modal. No prose.
6. **The stale rules stand.** HS-104-04's observed-at, stale-row
   retention, and attribution epistemics carry through unchanged —
   this story adds acts, it does not relax honesty about reads.

## Out of scope

- Merge, close, force-push, approve-review, branch deletion.
- A second userland program. Project memory and
  decisions-to-artifacts are named in the owner's charge and parked
  as the NEXT program, deliberately.
- Replacing `gh`. One batched call stands.
- New PR data sources.

## Acceptance

- Proven on the owner's REAL pull requests on real metal — this
  repository's own PRs, not fixtures. Seeded demos are not proof.
- The full loop walked live at least once end to end: a real PR
  needing work, an agent sent at it, the agent's work receipted
  including its child operations, a comment PROPOSED, the owner
  approving it, and the comment appearing on the real PR with a
  receipt.
- A refused verb shows its reason on the row, proven by yanking
  credentials mid-walk (the HS-104-04 network-yank method).
- Nothing leaves the machine without an approved proposal — proven
  by a deny, where the drafted comment does NOT appear on GitHub.
- Every act in the walk is traceable from the journal alone: which
  principal, which decision, which receipt.
- The program adds no new consent mechanism. A census proves it
  routes through the four calls only.
- Walked at 1440 and 393 with screenshots read, per the standing
  screenshot-walk rule.

## Delivered

- Real PR #387 was read, matched exactly to its registered worktree, sent to a
  bounded Claude agent, and reviewed through journal-linked `process.spawn`,
  `process.input`, and `tool.call` operations with terminal receipts.
- A real private-LAN `inference.run` produced a durable review artifact. One
  full-text GitHub comment proposal was approved and landed exactly once; two
  denied proposals did not land.
- The credential-yank walk retained the row and its observation while naming
  `gh credentials unavailable` on only the outward verbs.
- Evidence: [evidence-story-08](./evidence-story-08.md),
  [1440](./assets/hs-106-08-pr-loop-1440.png), and
  [393](./assets/hs-106-08-pr-loop-393.png).

## Test plan

- **Unit:** verb availability per row state; refusal reasons; the
  needs-you ordering carried from HS-104-04.
- **Integration:** each verb as a kernel operation, over real HTTP
  against a real spawned hub.
- **Live (evidence):** the full loop on a real PR in this
  repository, both viewports, screenshots read; one credential yank;
  one deny.
- **Full suite:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  plus the web chain.

## Chef's notes

- This story is the proof the owner will actually feel. Build it
  hands-first in the Phase-101 round-9 method: walk it, read every
  screenshot, fix what the walk catches at cause.
- Resist adding merge. The moment this program can merge, the owner
  stops trusting it to draft, and the whole loop gets read with
  suspicion.
- If any verb needs to reach around the kernel to work, STOP and
  write that down. It is a finding about HS-106-04's spine, not a
  detail of this story, and it belongs in the closeout ledger.
- The drafted comment must be visible in full before approval. A
  proposal the owner cannot fully read is not consent (Article V).

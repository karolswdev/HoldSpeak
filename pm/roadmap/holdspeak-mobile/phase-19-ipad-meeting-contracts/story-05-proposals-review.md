# HSM-19-05 — The proposals review queue: the split, made visible

- **Project:** holdspeak-mobile
- **Phase:** 19
- **Status:** done — see [`evidence-story-05.md`](./evidence-story-05.md). The queue card
  (honest four-state render, Approve/Reject on `proposed` only, the slack cloud mark),
  live-hub proven end to end with 19-01 (file → queue → decide → illegal-transition 400);
  the proof surfaced and fixed the audit-trail gap (`decided_by: "ipad-companion"`,
  test-locked). The on-device tap rides the 19-07 walk (W5).
- **Depends on:** `HTTPDesktopClient+Proposals.swift` (`meetingProposals(meetingId:)`,
  `decideProposal(meetingId:proposalId:approved:)`); hub routes in
  `holdspeak/web/routes/meetings/aftercare.py:101,128`. Pairs with HSM-19-01 (a filed
  issue lands here).
- **Unblocks:** the iPad as a full citizen of the propose→approve→execute audit.
- **Owner:** unassigned

## Problem

The iPad only ever approves **its own** sends: the desk's `DioSendCard` shows a receipt for
a send the user just initiated, then proposes+approves in one task. Proposals created
anywhere else — the web dashboard, live in-meeting proposals (HS-38), an aftercare
file-issue (19-01) — are invisible from the iPad. `meetingProposals` / `decideProposal`
shipped in Wave 3 with **zero callers**. The audit's "split the one-tap send" lands here as:
the review step exists as a *place*, not just as a card in the moment of sending.

## The design

1. **A proposals card on the meeting digest** (`CompanionShellApp.swift`, beside
   artifacts/aftercare): each proposal shows target, action, the human `preview`, and its
   status. `proposed` ones carry **Approve / Reject**; decided/executed/failed ones render
   their state honestly (including `error`).
2. **Approve is honest about execution:** for most targets approval only flips DB state;
   a `slack` target executes immediately (the hub's consent model — `allow_actuators=True`
   on the decision route is by design, HS-61; don't "fix" it). The approve control for a
   slack proposal carries the cloud egress mark (`Cloud · slack`), matching the desk's
   `EgressBadge` grammar — a label, never a reassurance sentence.
3. **Illegal transitions surface the hub's reason** (`ProposalDecision.error` — e.g.
   deciding an already-executed proposal), never a silent failure.
4. **The desk's send card stays as is:** it already inserts a visible receipt before its
   own propose+approve; this story adds the queue for everything else, which IS the split.

## Scope

- **In:** the proposals card (read + decide), status/error rendering, the slack egress
  mark, sim proof.
- **Out:** hub-side changes; proposal *creation* surfaces (19-01 files issues; the desk
  card sends); a global cross-meeting proposals inbox (per-meeting is the shipped route).

## Test plan

- `swift test` green (decode + decision envelopes covered by `*ClientTests`).
- Sim proof: seeded queue (proposed slack + proposed github + one executed + one failed) →
  screenshots of the queue, an approve flow, and the honest error state.

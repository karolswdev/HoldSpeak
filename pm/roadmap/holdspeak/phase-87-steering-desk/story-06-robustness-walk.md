# HS-87-06 — The robustness rig, the walk, the docs

- **Project:** holdspeak
- **Phase:** 87
- **Status:** done
- **Depends on:** HS-87-04, HS-87-05
- **Unblocks:** B3 (the factory) / B4 (the DeskOS belt) per the RFC
- **Owner:** unassigned

## Problem

The owner's admission criterion is robustness, and robustness is
proven by trying to break the thing in front of the surface that
claims it. The closing walk steers a REAL session from the desk with
a REAL desk object as context — and the crown cases fire live, on
camera, against the real machinery.

## Scope

- In: the walk (below), each beat captured; a mechanical-rules pass
  (the send-chokepoint grep test, desk locks extended to the
  pull-out tree, the audit-completeness assertion: every delivered
  or refused steer of the walk has its row); docs — USER_GUIDE
  "Steer a session from the desk" (canon voice), SECURITY.md consent
  model finalized (arming semantics, audit, nothing egresses),
  ARCHITECTURE.md the steering chokepoint paragraph; BACKLOG/README
  cadence; final summary.
- Out: new capability; performance work beyond the peek hash gate.

## The walk (each beat a capture)

1. Attach: open THIS session's pull-out; watch the agent work, live.
2. Refusal first: steer unarmed → refused, the reason in place.
3. Arm: hold-to-arm, countdown visible on the pin and pull-out.
4. Steer: speak a reply; watch it land in the pane exactly as
   composed.
5. Ground: steer a question with a real meeting artifact attached;
   control vs treatment shows the agent using it.
6. Classify: keep the agent's answer as a note; flip a story from
   the pull-out through the proposal card.
7. Crown cases, live: (a) recycled pane → refused + disarmed;
   (b) TTL expiry mid-composition → send refused, ARM re-offered;
   (c) disarm from another surface while the composer is open.
8. The audit: the trail for beats 2–7 read back on the desk.

## Acceptance criteria

- [ ] All eight beats captured against a real session; zero mocked
      frames; the audit rows and rail/registry receipts in evidence
      match every claim.
- [ ] The chokepoint grep test pins `send_text_to_pane`'s allowed
      call sites; the desk-lock rules cover the pull-out tree.
- [ ] Docs shipped in canon voice; voice/docs/api-surface guards
      green; suite green (read from the output file).
- [ ] final-summary.md with the B3/B4 handoff (what the factory and
      the DeskOS belt inherit from this consent spine).

## Test plan

- Unit: the mechanical rules (chokepoint census, lock extensions,
  audit completeness helper).
- Integration: the walk itself.
- Manual / device: the owner replays beats 1–6 from the docs alone.

## Implementation direction

- **Walk rig:** extend the Phase-86 pattern
  (`scripts/screenshot_hs86_walk.py`) — one hub, one page session,
  real acts between shots, the access recorder widened to
  `/api/coders*` asserting: GETs free, POSTs only
  `arm|disarm|steer|proposal` and each with a matching audit row.
- **Crown case (a):** `tmux kill-pane` + respawn inside the walk —
  the same beat the upstream proved ("recycled pane ids refused");
  assert the grant is GONE afterwards, not just the send refused.
- **Crown case (b):** arm with a test-only short TTL (an env knob
  read ONLY when `HOLDSPEAK_STEERING_TTL_S` is set — document it as
  a test seam, default untouched).
- **Self-reference:** beat 1 attaching to the very session doing the
  work is the Phase-86 recursion again — keep it; it is the
  demo that sells the whole thing.
- **The docs page** leads with the consent sentence (watch free,
  steer armed, everything audited) and never says "safe" — it says
  what refuses and when (the no-reassurance canon).

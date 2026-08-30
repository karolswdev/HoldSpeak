# HS-155-04 - The child on the desk: open it, steer it, stop it; the crew row

- **Project:** holdspeak
- **Phase:** 155
- **Status:** backlog
- **Depends on:** HS-155-03
- **Unblocks:** HS-155-05
- **Owner:** unassigned

## Problem

A delegate the owner cannot open is a black box. The child thread is a
real desk object — openable, steerable, stoppable — and the parent
shows its crew (settled design D4).

## Scope

- **In:** the child opens in the normal thread pullout; its head shows
  "child of <parent title>" with a jump link; the parent gets the crew
  row — children with state chips (running / backgrounded / done /
  stopped) and jump links; stopping a child from either side stops its
  conductor run and stamps the state. The owner typing into a running
  child steers it (their message joins the child's next pass — the
  normal composer path already does this). Desk tokens, no modals,
  keyboard reachable, 393-safe (the crew row scrolls in its own
  overflow container).
- **Out:** crew templates, bulk operations.

## Acceptance criteria

- [ ] vitest: the crew row renders children with state chips; jump links both ways; stop from the parent flips the chip and the child's run stops (mocked conductor call).
- [ ] The child pullout head shows the parent link; GET exposes parent/children so reload rebuilds both sides.
- [ ] Glass 1440 + 393: a parent with two children (one running, one done), the child head link, zero overflow.

## Test plan

- **Unit:** vitest `crewRow.test.tsx`; a route test for the children listing on GET.
- **Integration:** glass leg `crew-desk`.
- **Manual / device:** story 05.

## Notes / open questions

- SurfaceFooter is a fixed 36 px bar — the crew row is its own flex child, never inside the foot.

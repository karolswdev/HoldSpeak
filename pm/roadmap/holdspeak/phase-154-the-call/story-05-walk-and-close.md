# HS-154-05 - The walk and the close

- **Project:** holdspeak
- **Phase:** 154
- **Status:** backlog
- **Depends on:** HS-154-01, HS-154-02, HS-154-03, HS-154-04
- **Unblocks:** HS-155-01
- **Owner:** unassigned

## Problem

The Call is claimed only when walked: glass at both widths, the turn
loop under call mode on real metal, docs touched, counsel heard
(settled design D5; the arc rhythm).

## Scope

- **In:** metal `assets/story-05-metal.py` on `.43` (the 153 rig
  pattern; the .43 default-grammar law — the `grammar:""` override is
  already wired): call_mode toggled by route, a turn drives
  LISTENING→THINKING→streaming, `thread_call_state` frames observed,
  the R4/404 path exercised with the extra absent. Glass
  `tests/e2e/test_hs154_call_glass.py` full file at 1440 + 393; shots →
  `assets/story-05-shots/`; one exhibit artifact. Docs: README /
  USER_GUIDE (the Call, the GPL note law, the R4 fallback); MCP_SIDECAR
  only if tool counts moved. Close counsel (opus; must-fixes in-round).
  Honest sweep: name-diff vs main's latest; web baseline zero
  branch-new; restore the phase-14* shot assets after rigs.
- **Out:** 155 The Crew.

## Acceptance criteria

- [ ] Metal legs PASS on `.43`, payloads/frames kept under `assets/story-05-metal-payloads/`.
- [ ] Glass both widths, all rooms, zero horizontal overflow; exhibit link in the evidence.
- [ ] Counsel in `assets/counsel-close.md`, zero open must-fix; docs touched; the warpdrv grep still hits only the plan + phase records.
- [ ] The attended voice leg is explicitly left to the owner and marked so.

## Test plan

- **Unit:** the full scoped 154 set + the 153 set (regression).
- **Integration:** the glass file; the metal script.
- **Manual / device:** the owner's attended leg holds the merge word.

## Notes / open questions

- The exhibit joins the 151/152/153 exhibits as the arc's fourth room.

# HS-153-06 - The walk and the close

- **Project:** holdspeak
- **Phase:** 153
- **Status:** backlog
- **Depends on:** HS-153-01, HS-153-02, HS-153-03, HS-153-04, HS-153-05
- **Unblocks:** HS-154-01
- **Owner:** unassigned

## Problem

The Practice is claimed only when it has been walked on real metal and
real glass, its docs touched, and close counsel heard (settled design
D6; the arc rhythm).

## Scope

- **In:** the metal script `assets/story-06-metal.py` on `.43`
  (tool-qualified deployment): Desk→Chase switch; `effect-guard` fires
  on a `people.commitment.transition`; annotation round-trip by voice
  (mic pipeline through the real hub); `/compact` with a visible cut and
  the post-cut payload captured; `/todo` on the Door; `egress-guard`
  violation on a `people.*` read under a cloud override (safe-mode default
  flips to Deny). Glass `tests/e2e/test_hs153_practice_glass.py` 1440 +
  393: mode tabs, guardrail row, annotation chips, cut marker, Door card
  with thread provenance; shots to `assets/story-06-shots/`; one shot
  exhibit artifact for the owner. Docs: README / USER_GUIDE /
  MCP_SIDECAR entry points (tool count arithmetic = `len(TOOLS)`),
  the Desk Chat plan §6.5–6.6 marked shipped. Close counsel
  (opus, RATIFY / RATIFY-W-C / REJECT; must-fixes in-round). Honest
  sweep: name-diff against main's latest run; web baseline zero
  branch-new; `git checkout -- pm/roadmap/holdspeak/phase-14*` after rigs.
- **Out:** 154 The Call.

## Acceptance criteria

- [ ] Metal script: every leg PASS on `.43`, payloads kept under `assets/story-06-metal-payloads/`.
- [ ] Glass: both widths, all five rooms, zero horizontal overflow; exhibit link in the evidence.
- [ ] Close counsel recorded in `assets/counsel-close.md` with zero open must-fix.
- [ ] Docs entry points touched; `git grep -i warpdrv` hits only the plan + phase records.

## Test plan

- **Unit:** the full scoped set of 153 tests + the 152 set (regression).
- **Integration:** `tests/e2e/test_hs153_practice_glass.py`; the metal script.
- **Manual / device:** the owner's attended leg holds the merge word.

## Notes / open questions

- The `.43` tool qualification seeded in HS-152-06 is reused; do not re-qualify.

# HS-150-08 - The walk and the close (real metal, glass, docs, counsel)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** in-progress
- **Depends on:** HS-150-06, HS-150-07
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Art. IX: nothing is done until it ran on real hardware. Counsel
required three legs before the phase flips (settled-design D8), the
docs story law wants entry points touched, and the handover's debt
rider (the web-unit baseline) has been carried two arcs.

## Scope

### In (D8)

- Leg 1 — real metal `.43` (llama.cpp Q6): two-turn streamed thread,
  deltas observed on the bus, first delta ≤ 1.5 s recorded, receipts +
  egress badges on both turns, rows = glass; control = the old Ask
  blob for the same prompt.
- Leg 2 — People boundary under profile switch: seeded sensitive part,
  `profile_override` → a cloud profile, the recorded provider payload
  asserted clean (unit pin from 04 + this walk's artifact).
- Leg 3 — glass exhibit 1440 + 393, cross-read: populated + branched,
  empty, error (provider unreachable), CRASHED + Retry; occlusion tell
  on every frame; shots under `assets/story-08-shots/`.
- `scripts/door_walk_hs144.py`: a "thread" leg appended (Continue in
  thread from a Door item → streamed reply → receipt).
- Docs: README + USER_GUIDE entry points ("Threads"), MCP docs count
  arithmetic, `docs/internal/PLAN_PHASE_DESK_CHAT.md` status line →
  "DC-01 shipped as Phase 150".
- `web-inherited-baseline.txt` + a sweep-side check (handover §3.D).
- Close sweep (isolated HOME, `-n auto`, baseline-diffed), close
  counsel, AGPL check (`git grep -i warpdrv` returns only the plan and
  this phase's records), `final-summary.md`.

### Out

Anything DC-02+.

## Acceptance criteria

- [ ] All three legs recorded with artifacts; leg 1 timing line in the
      evidence; leg 2 payload file shows zero sensitive text.
- [ ] Door walk 10/10 legs ×3 (the new leg included).
- [ ] Close sweep: zero unresolved branch-new failures vs the inherited
      baselines (pytest 72-name file + the new web baseline).
- [ ] Close counsel verdict recorded; must-fixes fixed in-round.
- [ ] Owner has the shot exhibit link before merge (standing law).

## Test plan

- **Unit:** the full web chain + the scoped backend suites.
- **Integration:** full sweep as CI sees it (CLAUDE.md command).
- **Manual / device:** `.43` legs 1–2; the owner's shot verdict.

## Notes / open questions

`.43` reachability from sandboxed Bash is blocked (reference memory);
run the metal legs from an unsandboxed shell or over SSH.

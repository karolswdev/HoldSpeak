# HS-134-10 — The walk

- **Project:** holdspeak
- **Phase:** 134
- **Status:** done
- **Depends on:** HS-134-01..09
- **Unblocks:** —
- **Owner:** unassigned

## Problem

Ownership claims need live proof: that an override actually redirects
execution, that the answer names its decider, and that the renamed MCP
surface still walks green end to end — none provable by unit tests
alone.

## Scope

### In

- The provenance proof, live on `.43`: create a destination for the
  LAN endpoint, set it as a workbench-tier override on an agent whose
  agent-tier default is this_machine, run through the admitted path,
  and capture the response naming `source: "workbench"` and the
  effective target — then remove the override and capture the
  inheritance flip. (Boot with `--extra meeting`; profile kind
  `private_endpoint` — Phase 133 gotchas.)
- `scripts/mcp_walk.py --live-43` re-run green with the renamed
  surface (assertions updated in HS-134-03), extended with one
  provenance assertion on `ask.run`'s placement block.
- Web guard walk: the Get Info hand-off and read-only Workbench skills
  screenshotted at 1440 + 393 against the live hub.
- The full-suite gate (quiet tree, isolated HOME, `-n auto`, metal
  excluded), failures diffed by name against the pre-phase baseline.
- Everything through `dw evidence capture`.

### Out

- Comfy Chair surfaces; any new harness beyond the provenance
  assertion added to the existing walk.

## Acceptance criteria

- [ ] Live `.43` capture shows the same run redirected by a workbench
  override and inheriting without it, `source` named both times.
- [ ] `scripts/mcp_walk.py --live-43` fully green post-rename.
- [ ] Both-width screenshots of the two web ownership surfaces.
- [ ] Full suite: zero regressions vs baseline; story cannot be closed
  by unit tests alone and cannot be waived.

## Test plan

- `.githooks/dw evidence capture holdspeak 134 10 -- <walk + suite commands>`
  (live legs run unsandboxed by the orchestrator).

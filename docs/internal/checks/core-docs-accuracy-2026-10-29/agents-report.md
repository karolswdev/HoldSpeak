# Agents-lane accuracy report

Date: 2026-10-29  
Base: `4dce2796d`  
Scope: the 16 agents-owned extended guides, plus the agents audit artifacts.

## Result

Three concrete documentation errors were corrected:

- `docs/CODER_INTEGRATION.md` now says **Review by** records the reviewer and
  starts it after a new builder commit. `holdspeak/services/agent_review.py:60-74`
  stores `awaiting_builder_commit`; `:271-306` starts the reviewer after the
  commit is available.
- `docs/AGENT_HOOK_INSTALL.md` now separates hook templates/latest-session
  status from voice-reply readiness. The hook route returns templates and recent
  sessions at `holdspeak/web/routes/dictation/agent.py:74-105`; the readiness
  contract is `ready_for_agent_reply` and `blockers` at
  `holdspeak/web/routes/system/coders.py:202-224`.
- `docs/REACH_RUNNER.md` now includes `active_run_exists` as a successful
  already-active result. The script handles it at `scripts/reach_runner.py:288-300`.

The other thirteen guides passed source review. The review specifically checked
queued versus completed output, sidecar and MCP authority, immutable assignment
and route evidence, CLI-engine versus coder-session boundaries, Thread Mode
versus saved Agent identity, and explicit unsupported/API-only paths.

## Generated/read-only material

`docs/CONFIGURATION_REFERENCE.md` was not edited. All 160 linked declaration
references resolve to current source declarations, including the rows for
`Config`, Agents, Cadence, and model runtime. Its `Source snapshot` at line 5 is
`675401a857b...`, a historical ancestor of the audit base. Root may regenerate
the reference if that generated metadata must identify the current source; this
lane leaves it unchanged as required.

The generated MCP roster region in `docs/MCP_SIDECAR.md` was not edited. The
sidecar claims remain supported by `holdspeak/mcp/server.py:1-39,107-115,191-213`
and palette construction by `holdspeak/mcp/palettes.py:11-24`.

## Cross-lane defects

No cross-lane defect was found in the owned guides. No live provider, Desk,
browser, hardware, or external scheduler action was performed.

## Verification

- `python3 scripts/check_docs.py <all 16 owned docs>`: passed navigation and
  local-heading checks.
- `git diff --check`: run after edits.
- Product tests, installs, and live walks were not run because the lane brief
  forbids them.

Full per-document claims, evidence, unknowns, and exact verification command
are in [`agents-audit.json`](agents-audit.json).

Status: **DRAFT — hold for SHIP**.

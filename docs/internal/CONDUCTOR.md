# The Conductor

Owner direction, 2026-10-05: "I wanted it to work with agents. In a semi-autonomous way. As an orchestrator. And out of the box. And batteries included." Then: "Make it happen."

## The loop

1. **Ready.** First run finds `claude`, `codex` and `tmux`, and installs the agent hooks with one press. `holdspeak doctor` checks the same.
2. **Hand to agent.** One verb on an action item, a decision, a Room issue, a Note, or a dictated sentence (Thread `/agent`, MCP `agent.hand`).
3. **Brief.** HoldSpeak writes a grounded brief: the item, its meeting quote, the Project's decisions and open commitments, memory pages, `.hs/` facts, the Control mode, acceptance. People data is cut before it reaches a cloud agent.
4. **Launch.** Claude Code or Codex starts in its own git worktree, with the brief as its first message, under HoldSpeak's spawn settings (rider hooks and the tool gate).
5. **Supervise.** The tool gate decides by Control mode. A waiting agent joins **Needs you** at once. A routine question can get a drafted answer under policy. A real one reaches you, and you answer by voice.
6. **Follow through.** The Heartbeat follows the PR. On merge, the originating commitment closes with the PR as evidence, the weekly update reports it, and the session and the clean worktree are cleaned up.

## Audit (2026-10-05, six read-only lanes on `000d87293`)

The engine exists: `LaunchService.launch` and `submit_process_spawn` (`holdspeak/delivery/factory_launch.py`), seeded `claude-default` / `codex-default` profiles, worktree create, hook-driven coder state (`holdspeak/agent_context/`), steering by Control mode, PR receipts, `FollowThroughService.complete`, the Room GitHub Watch, the steward's reviewer nudge. Nothing joins them, and the agent side is dark on a fresh install.

| Step | Exists | Missing or dark |
| --- | --- | --- |
| 1 Ready | `holdspeak agent-hook install` (CLI only, idempotent merge); profiles seed themselves; first-run card model (`connectionsStep.ts`, `OnboardingService.connections_detect`) | No web install; no `claude`/`codex` detection; no "hooks installed" read; `doctor` silent; launch has no executable preflight |
| 2 Hand | Launch engine; one brief path (`POST /api/delivery/prs/{src}/{n}/send-agent`); verb registry; Door verbs | No verb; launch needs a Delivery Source and a dw `story_ref`; UI launches only into an existing worktree; no MCP launch tool; no dictated hand-off |
| 3 Brief | `compose_steer`, `hydrate_refs_detailed`, `memory_for`, `project_pages`, `render_hs_context_for_prompt`, preparation-brief manifest | No `compose_agent_brief`; **bug:** steer drops picked `grounding.refs` (`coder_steering_support.compose_from_body`); no People cut toward cloud agents; the Context window claims "every agent receives" it, and coding agents do not |
| 4 Launch and supervise | Spawn, attempt, ledger, 120 s registration expiry, Bash PreToolUse gate, kernel `tool.call`, Cadence drafts `reply_to_agent` | Gate double opt-in, off; `process.spawn` refuses non-claude; rider hooks only in gated spawns, so an ungated Desk launch ends `failed_to_register` without a manual hook install; `tool_gate` family not in `INITIAL_FAMILIES`, so no Control-mode decision; no responder; no limits |
| 5 Escalate | Hook state `awaiting_response` + question; WS `coder` frames; Agents window and arrival AGENTS section; steer composer; AIPI reply | Coders are not in **Needs you** (R1–R4 only); no notification on block; arrival and Agents window do not refetch on coder frames; 3–4 presses to answer; device reply window 120 s against a 30 min default |
| 6 Follow through | PR receipts (exact branch/SHA attribution); Watch emits `github.pr.merged`; `complete()` with receipt; `link_work` | No origin link from item to launch/PR; nothing closes on merge; **bug:** `project_delta_service._classify_observation` compares bare `merged`/`resolved` to `github.pr.merged`/`jira.issue.resolved`, so merged PRs file as "changed"; PR refresh only on read; open-only Watch misses merges; no cleanup |

## Build

Backend slices need no canvas. Faces are drawn on the library and ratified by the owner first (UX-CANON A.2).

| Slice | Content | Needs |
| --- | --- | --- |
| **K0 fixes** | Steer keeps picked refs; delta classifies `*.merged`/`*.resolved` as closed; device reply window follows the 30 min default | none |
| **K1 ready (backend)** | `agents_detect` + `POST /api/onboarding/agents/use` (one-press hook install); `doctor` agents check | none |
| **K2 hand (backend)** | `services/agent_brief.py`; `POST /api/agent/hand`; `origin_ref` on launch and attempt; auto Delivery Source; new-worktree launch; rider hooks in every spawn; executable preflight; People cut; MCP `agent.hand`; Thread `/agent` | K1 for hooks |
| **K3 escalate (backend)** | Coders as Needs you R5; immediate dirty + notify on the awaiting edge; arrival and Agents window refetch on coder frames | none |
| **K4 follow through** | PR refresh on Heartbeat for live launches; close the origin on merge with evidence; `link_work`; cleanup of session and clean merged worktree; Watch `state=all` + `headRefName` | K2 |
| **K5 gate by Control mode** | `tool_gate` in `resolve_policy`; Codex gated path; drafted answers for routine questions under policy; live-launch cap and wall-clock escalation | owner ruling on the mapping (below) |
| **K6 the HoldSpeak MCP in every launch** | The launch spawn issues a launch-bound credential with the CONDUCTOR palette (every `work` tool of `mcp/tool_authority.py`, no People tool); POST /api/mcp admits it from loopback with Reach off; Claude Code gets `--mcp-config` (environment variables, no token) and Codex `-c mcp_servers.holdspeak.*`; Normal and YOLO pre-approve the tools, Secure does not; revoked on session end, K4 cleanup and a failed launch | none |
| **F faces** | First-run Agents card; **Hand to agent** in menus, ⌘K, Door rows; launch sheet (agent, brief preview, Control mode); Needs you coder row with **Speak answer**; Enter sends in the steer composer | canvas ratified |

### The Control-mode mapping (owner rules)

Proposed default:

| Mode | Launch | Agent tool calls (Bash) | Agent question |
| --- | --- | --- | --- |
| **Secure** | You press to launch | Every call waits for you | Always to Needs you |
| **Normal** | Launch on the verb | Read, test, `git status/diff/log` pass; the rest waits | Drafted answer shown; you send |
| **YOLO** (current default posture) | Launch on the verb | Pass in the agent's own worktree | Routine ones answered under policy and receipted; real ones to Needs you |

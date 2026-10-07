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

Ratified by the owner, 2026-10-06. YOLO is the default posture.

| Mode | Launch | Agent tool calls (Bash) | Agent question |
| --- | --- | --- | --- |
| **Secure** | You press to launch | Every call waits for you | Always to Needs you |
| **Normal** | Launch on the verb | Read, test, `git status/diff/log` pass; the rest waits | Drafted answer shown; you send |
| **YOLO** (current default posture) | Launch on the verb | Pass in the agent's own worktree | Routine ones answered under policy and receipted; real ones to Needs you |

### K5 as built

- **The tool gate.** The hook reads each held Bash call in the agent process (`holdspeak/tool_gate_rules.py`) and sends the hub a verdict, never the command: `inside`, `outside` or `unparsed`, the rule, and the Normal read/test rule. The hub checks the verdict against the caller's own launch (its registered session, its worktree, its branch) and `resolve_policy` (family `tool_gate`) applies the mode. Secure holds every call. Normal passes `git status|diff|log|show`, the read forms of `git branch`, `ls`, `cat`, `rg`, `grep`, `find` (no actions), `pytest`, `uv run pytest`, `npm test`, `npx vitest run` and a few more, in the worktree. YOLO passes every call whose working folder and named paths are in the worktree, and `git push origin <the launch branch>`. A call that names a path outside (also through a symlink), a URL, `cd ..`, `bash -c`, `eval`, inline code, a variable or a command substitution waits. A call from a session that is not the launch keeps the owner's recorded hold; before the rider registers the session, no call is the launch's. The verdict names its proposal id and args hash, and a verdict copied to another call waits; a proposal id is one session's. A here-document ends at its first tag line, as in bash; `find -exec` waits; each command word is identified first: a bash builtin, a system program (a bare name the PATH resolves outside the worktree, relative PATH entries read from the call's folder), or other. Only a builtin or a system program earns read authority or the `cd`, `git` and here-document `cat` readings; a path-invoked or PATH-shadowed program never moves the assumed folder. `PATH=...` prefixes and builtins that change resolution (`export`, `source`, `enable`, `alias`, ...) wait. One exception (R5): `source <path>` or `. <path>` alone, where the path resolves (symlinks followed) inside the worktree to `bin/activate` of a venv (`pyvenv.cfg` two levels up), is `inside` with no read rule, so YOLO passes it and Normal and Secure hold it; chained, piped, redirected or with an argument, it waits. YOLO runs programs inside the worktree (`./build.sh`, `pytest` with its conftest, `npm test`): that is the ratified posture, and such a program can still write outside. Each automatic decision is approved by the `control-mode` principal: the gate audit row and the kernel journal name the mode and the rule.
- **Answers.** A waiting launched agent (a K3 wait) is triaged by mode (`holdspeak/services/agent_responder.py`). Secure: Needs you, no draft. Normal: Needs you at once; a draft is stored on the wait. YOLO: the wait is held back while the model assigned to Cadence drafts writes a draft and a class from the brief, the pane tail and the Project's memory. The word list reads the draft answer too. Before the model runs, Secure and a permission prompt go to the owner at once (no draft), and a wait a YOLO triage held back is shown at once if the mode is now Normal. Each record is written only while its wait is the stored one, so an older worker never replaces a newer wait. Before anything is typed, the wait, its question, its kind and the mode are read again: a wait the owner answered is left alone, a changed one goes to Needs you. ROUTINE is typed into the agent's own pane through `process.input` (the pane is checked again) and receipted on the session (`auto_answered`); no Needs you row and no notification. REAL goes to Needs you with the draft and notifies then. No model, a model error, a word from the REAL list, 6 answers in the last hour, or the same question again: REAL. A permission prompt is never answered here.
- **Limits.** At most 3 launched agents run at one time (`agent.hand` refuses `launch_cap_reached`). A running agent with no hook activity for 2 h, or running for 8 h, gets one Door item each (Needs you); nothing is stopped.
- **Fixed on the way.** The hook of a gated launch named the launch's `process.spawn` operation as its kernel parent, and the kernel refused that parent for the agent (`parent_operation_scope_required`): every Bash call of a launched Claude was denied. The hub now keeps the link as the verdict's `launch_id` and does not send the spawn as the parent.
- **Codex gap.** Codex CLI 0.159 has a `PreToolUse` hook with the same deny output (`permissionDecision`). HoldSpeak does not gate Codex yet: a Codex launch takes the ungated path (`process.spawn` takes Claude only), the gate credential names `claude:` sessions only, Codex reads hooks only from `~/.codex/hooks.json` (5 s timeout in the K1 template; a hold needs 300 s), and its hook payload is not observed on a real desk. A Codex launch runs its tools under Codex's own approval policy in every mode; its questions are answered by mode like Claude's.


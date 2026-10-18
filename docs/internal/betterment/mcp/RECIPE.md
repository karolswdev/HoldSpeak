# The desk's tools for every engine (MCP): recipe

Build order for `DESIGN.md`. One slice = one PR in the fast cycle. Commands,
flags and line references come from `MODEL.md` (2026-10-17, Claude Code
2.1.302, Codex 0.161.0, pi 1.1.0); check them against main and the
installed versions before you start.

Rules: tests use fake CLIs on PATH in the scratch HOME and never the owner's
real `claude`, `codex` or `pi`. Every new MCP tool takes one row in
`TOOL_AUTHORITY` (`holdspeak/mcp/tool_authority.py`); add no new gate.

Order with the other recipes: M0 → Engines E1 (which includes M1) → M2 →
Automations A2 → M3 and M4 → M5 → M6.

---

## M0. Settle the unknowns (a live check, not a PR)

- **Goal:** know the exact behaviour before building on it.
- **Who:** the orchestrator, on the owner's Mac, with the owner's OK, since it
  spends a few cents of his subscription. One short prompt each.
- **Check:**
  1. `claude -p --tools "" --strict-mcp-config --mcp-config <file>`: the
     `mcp__holdspeak__*` tools are still callable.
  2. `--strict-mcp-config`: the claude.ai connectors (Gmail, Drive,
     Calendar) are not reachable. If they are, find the switch that removes
     them, and do not ship M1 until one exists.
  3. `--max-budget-usd` on a subscription login: does it stop a run?
  4. `codex exec --json`: what it reports about cost and usage. How to keep
     the owner's `pixellab` server out without `--ignore-user-config`
     (for example `-c mcp_servers.pixellab.enabled=false`, if 0.161 has it).
  5. pi `--no-builtin-tools`: MCP tools are kept; `--mode json` shape.
- **Done when:** the answers are written into `MODEL.md` "Unknown", and
  the M1 commands are fixed to match them.
- **Done 2026-10-17.** All five answered (`MODEL.md` "Unknown"): (1) yes;
  (2) yes, strict drops them (without it, 4 claude.ai connectors load);
  (3) yes, with up to one turn of overshoot; (4) tokens only, no dollars;
  `mcp_servers.pixellab.enabled=false` works, and Codex needs
  `features.apps=false` too (its own ChatGPT apps reach the agent
  otherwise); (5) yes, through pi's `codemode` tool. Codex is now 0.163.0.

## M1. One-shot runs with the desk's tools

(Part of Engines E1; listed here so the MCP part is not lost.)

- **Goal:** a `cli_engine` run can call HoldSpeak's tools, and nothing
  else.
- **Files:** `holdspeak/intel/cli_engine.py`; `holdspeak/delivery/agent_mcp.py`
  (reuse `claude_mcp_document()`, `remove_mcp_config`);
  `holdspeak/mcp/principals.py` / `agent_credentials` (issue with a time to
  live); `holdspeak/services/workbench_runner.py` (the lock, below).
- **Changes:**
  - Before the process starts, issue a CONDUCTOR credential with identity
    `agent:run:<run_id>` and a time to live near the run's time limit. Write
    the 0600 config. Put `HOLDSPEAK_HUB_URL` and
    `HOLDSPEAK_AGENT_CREDENTIAL` into the child's environment only. After it
    exits (or is killed), revoke the credential and remove the config.
  - Use the commands in `MODEL.md` §4 (corrected by M0). Built-in tools
    are off unless the automation has a folder (Automations A10). In short:
    - Claude Code: `claude -p --output-format json --no-session-persistence
      --strict-mcp-config --mcp-config <0600 file> --tools ""
      --allowedTools mcp__holdspeak --permission-prompts none [--model M]
      [--max-budget-usd N]`. Never drop `--strict-mcp-config`: without it
      the login's claude.ai connectors (Gmail, Drive, Calendar, Docs) load.
      Read `total_cost_usd` (an estimate on a subscription; `costBasis:
      "list"`); a cap ends with `subtype: "error_max_budget_usd"` and can
      overshoot by one turn, so set the cap below the real limit.
    - Codex: `codex exec --ephemeral --sandbox read-only
      --skip-git-repo-check -C <tmp> --json`, plus `-c features.apps=false
      -c web_search="disabled"` and the other `features.*=false` of §4,
      plus `-c mcp_servers.<name>.enabled=false` for each name in
      `codex mcp list --json` (today `pixellab`), plus the three
      `mcp_servers.holdspeak.*` settings. Keep `features.code_mode_host`
      on (MCP needs it). Not `--ignore-user-config`. Cost: tokens only,
      from `turn.completed.usage`; show "Codex cannot limit spend".
    - pi: `PI_CODING_AGENT_DIR=<folder with models.json + mcp.json>
      PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 pi -p --no-session
      --mode json --no-builtin-tools --model lan/<model>`, the prompt on
      stdin and stdin closed after it (an open stdin hangs pi). Cost from
      `turn_end.message.usage.cost.total`.
  - Remove the 13 MODEL-class tools from the run's set (decision 3): a
    subset of CONDUCTOR, about ten lines in `palettes.py`.
  - Fix the deadlock risk: a run must not hold the automation's lock while
    the agent calls tools that read that same automation (`MODEL.md` §3).
    Release it after the claim, or make reads lock-free.
- **Done when:** a fake `claude` that calls `meeting.list` through the given
  config gets real rows from the rig hub. A fake that calls `channel.send`
  is refused. The credential is invalid after the run. A run whose agent
  reads its own automation does not hang.
- **Tests:** T1 with fake CLIs on PATH.

## M2. Looked at, Wrote, Prepared

- **Goal:** each result shows what the agent used and did, in words.
- **Files:** `holdspeak/web/routes/mcp_http.py` (record each call made with
  an `agent:run:` credential against the run); the run record
  (`workbench_runs`, additive column `tool_calls_json`, or a child table);
  `web/src/desk/components/automation/ResultCard.tsx`; the vitest.
- **Changes:** the hub records each tool call (tool, the object it touched,
  and the time) for the run. The result card shows three folded lines.
  *Looked at*: the read objects, by name, each a link. *Wrote*: desk writes,
  each with Undo where an undo exists. *Prepared*: prepared sends, with
  Send.
- **Done when:** a fake agent that reads 3 meetings and writes 1 note
  gives "Looked at: 3 meetings …" and "Wrote: 1 note" with working links,
  at 1440 and 393.
- **Tests:** T1 for recording; T2 for the card.

## M3. Automations on MCP

- **Goal:** an agent can make, change, run and read an automation in its
  new shape.
- **Files:** `holdspeak/mcp/families/` (the workbench family),
  `tool_authority.py` (rows; extend `_SCHEDULE_FIELDS` with the trigger
  fields), `services/workbench_service.py`, `docs/workbenches.json`.
- **Changes:** extend `workbench.create/update` with `do`, `about`, `when`
  (structured: `{schedule: {every, day, time}}` | `{event: <name>}` |
  `{manual: true}`), `put_in`, `spend_limit`. Add `workbench.results`
  (READ) and `workbench.cancel` (WORK). Add `automation.*` aliases for the
  same tools, so that an agent finds them by the user's word.
- **Done when:** one MCP call creates the Friday update automation, and
  `workbench.results` after a run returns the rendered text, Looked at,
  cost and failure reason. From a Thread, turning it on stops for his
  press.
- **Tests:** T1 through `/api/mcp` with an owner and a CONDUCTOR credential.

## M4. Engines on MCP

- **Goal:** an agent can find, add, remove and limit engines.
- **Files:** `holdspeak/mcp/families/model_library.py`,
  `families/concierge.py`, `tool_authority.py`.
- **Changes:** add `model_library.connect_cli_engine` (CONFIG),
  `model_library.remove` (CONFIG) and `model_library.set_spend_limit`
  (CONFIG); `concierge.detect` lists the CLIs it finds.
- **Done when:** from an owner session, "add Claude Code and use it for
  Answers" works through MCP alone.
- **Tests:** T1.

## M5. Tools for HTTP engines that accept tool calls

- **Goal:** the LAN model and OpenRouter models with tool support also get
  the desk's tools.
- **Files:** `services/workbench_runner.py`; the Thread tool loop (find the
  `agent.tool_turn` path and reuse it, do not write a second loop).
- **Changes:** when the engine's Check reported tool support, run the item
  through the existing tool loop with the M1 tool set, a turn limit and
  the run's time limit. Record the calls for M2.
- **Done when:** with a recorded tool-calling reply from the LAN model, the
  result's Looked at lists the meetings it read.
- **Tests:** T1 with a recorded engine reply.

## M6. A GitHub pull-request read

- **Goal:** the review starter can read the PR it is about.
- **Files:** `holdspeak/mcp/families/` (providers), the GitHub provider
  service (the `gh` CLI, as the provider already uses).
- **Changes:** add `provider_github.pr_get` (READ): title, body, files
  changed and diff stats, and the review requests.
- **Done when:** "When GitHub asks me to review" produces a summary that
  names the changed files.
- **Tests:** T1 with a recorded `gh` reply.

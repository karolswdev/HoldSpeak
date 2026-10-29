# README rewrite: initial advisory review and verification

Historical initial-source record. The later core documentation refresh corrected its stale source base and supersedes its current-product claims. See `docs/internal/CORE-DOCS-REFRESH-2026-10-29.md` for the active handover.

**Status: UNCHECKED — awaiting Muad'Dib.** The README draft stays on its worktree branch. This record is advisory, not Muad'Dib's check.

## Scope

The owner directly requested a README rewrite on a worktree on 2026-10-29. His definition, “an agentic-first web-based AI operating system,” supplies the lead for this rewrite and supersedes the older dictation-first lead for this task. No product code, positioning canon, or other public guide changed. The previous illustrations and comparison table were removed from the README, while their source assets remain in place. They describe an older product presentation.

Worktree: `/Users/karol/.codex/worktrees/readme-agentic-os/HoldSpeak`.
Branch: `docs/readme-agentic-os`, based on `33fdbce59`.

The HoldSpeak skill's `agent.start_helper` returned `launch_only`: this owner-started session has no launched-agent identity. The review below uses the second-opinion path permitted by TWO-BRAINS.md section 6. It is not a Muad'Dib session.

## Check — claude -p (claude-opus-5-5), invoked by Astra, 2026-10-29

The reviewer received the changed README path, the implementation paths to inspect, and the focused check plan. It was instructed to read only, without tests, edits, workers, or messages. Its line numbers refer to the pre-correction draft.

### Disposition, verified by Astra

1. **Automation memory retained, qualified.** The review missed `holdspeak/workbench_memory.py:45` and `:77`, plus recall at `holdspeak/services/workbench_runner.py:618` and writeback at `:821`. They implement memory per Workbench. The README now says “With memory enabled.”
2. **CLI engines clarified.** All four presets are named. The text distinguishes answering Desk requests from launching a repository session. It describes scoped tools for tool-capable presets. The suggested blanket claim that every CLI has all its own tools disabled was not used: Gemini retains read-only tools, as `holdspeak/intel/cli_engine.py:143` explains.
3. **Agent queue described.** The README names the configurable concurrency and **Start when one is free**, verified against `web/src/desk/components/HandSheet.tsx:450`. It does not add a fixed numeric claim.
4. **Handoff inputs clarified.** Project items and GitHub/Jira issues read through Project Watches are explicit.
5. **Authority kept concise.** The README links the full Control modes reference and states that tool permissions and service checks apply. It makes no claim that hooks govern every externally launched session. No extra shell-gate promise was added.
6. **UI boundary promise narrowed.** The README asks the reader to check the engine and destination and points to run records. It no longer promises host labels across the Desk.
7. **Local speech claim retained.** `holdspeak/services/concierge_service.py:1012` and `:1104` explicitly restrict speech recognition to local Whisper. The generic threat-model sentence cited by the reviewer does not establish a remote speech route.
8. **Opening simplified.** Workbench inspiration and the list of Desk objects now occupy separate sentences. The earlier sentence was already below the descriptive word limit.
9. **Diagram retained.** It shows how context becomes work and returns to the Desk. The title and opening paragraphs establish the agentic lead.
10. **The Call linked.** The README now links directly to `docs/USER_GUIDE.md#the-call`.

### Focused verification

- `python3 scripts/check_docs.py`: **70 public documents checked**, all local targets and headings resolve.
- Existing navigation and drift checks, through `scripts/test_lock.py`, with a temporary HOME and eight workers: **37 passed in 2.62s** after the final prose corrections.
- README Mermaid block parsed successfully with cached Mermaid under JSDOM: **1 diagram parsed**.
- `git diff --check`: passed.
- Manual editorial review: simple English, exact control labels, short descriptive sentences, prerequisites beside agent/automation flows, no claim of formal STE certification.

The focused tests used the existing environment's Python executable without changing its packages. The temporary HOME was removed by `TemporaryDirectory`. No product runtime, hardware, external send, agent launch, model inference, or scheduled execution was exercised for this documentation change. The pre-merge quick check has not run; no merge is part of this handover.

### Original advisory response

I found nothing that blocks the README. It delivers the agentic-first, web-based AI operating system lead the owner asked for, and the flow is clear. Most named controls exist in `web/src`, and the claims about telemetry, the YOLO default and the 14 plugins hold up in the docs and code. Below are ranked findings: one claim that is likely wrong, two missing capabilities, one link and five wording changes. I edited nothing and ran no tests.

### 1. "Automations can keep their own working memory between runs" has no support (README.md:145)
`automation_runs.py` and `workbench_service.py` only pass `memory_enabled`. In `workbench_conductor.py:213-221` that flag adds the shared Desk memory under the `workbench.item` policy. I found no store that belongs to one automation and carries over between runs. Either remove the sentence or reword it: "Runs can use Desk memory as context." If such a store exists elsewhere, cite it.

### 2. The CLI engine row hides the two most important facts (README.md:211-213)
`cli_engine.py:1-31` states two facts the README leaves out:
- **It is not a coding agent.** The CLI's own tools are off: `--tools ""` for Claude Code, a read-only sandbox for Codex. It runs in an empty temporary folder.
- **It gets only HoldSpeak's MCP tools**, through a short-lived run credential. That credential allows reads, People included, and Desk writes. It does not allow send, config or authority tools.

These facts are what makes the agentic claim on line 27 true, and they are a real limit on authority. Add one sentence, for example: "A CLI engine runs with its own tools off. It can use only HoldSpeak's tools, and it cannot send." The supported CLIs are Claude Code, Codex, pi and Gemini CLI (`cli_engine.py:118-153`). Gemini is not named anywhere in the README. Name all four, because the README names the agent CLIs elsewhere.

### 3. The cap on agents working at once is not mentioned (README.md:113-121)
At most `agents.working_at_once` agents work at one time, default 6 (`agent_hand_service.py:22-25`). When the cap is full, a hand-off waits in a queue, and the heartbeat starts it when an agent is free. This matters to the target user, and it explains why a hand-off can wait. Add: "At most six agents work at once by default. More hand-offs wait in a queue."

### 4. The supported hand-off items are slightly off (README.md:110)
`BRIEF_KINDS` (`agent_brief.py:42-53`) contains action, decision, decision record, Project item, note, meeting, artifact and issue (a GitHub or Jira issue that a Room Watch reads). "Task" is close enough, but "Project item" is missing. "Supported project issue" should say that it comes through a Project Watch.

### 5. "Tool permissions … still apply" needs a scope for agents (README.md:218-221)
The Control mode decides an agent's held Bash calls through the tool gate (`agent_hand_service.py:18-19, 560-563`). That gate applies only to Claude Code, Codex and pi launched from HoldSpeak. Agents launched another way only report through hooks. Add a sentence: "The Control mode also decides which held shell commands a launched agent can run." A reviewer launch is read-only (plan mode or a read-only sandbox, lines 552-559). That fact also supports line 121.

### 6. "The Desk shows the execution host or boundary" conflicts with the 2026-10-25 ruling (README.md:215)
The owner ruled egress labels a relic: no host, IP or scope chips on rows, toolbars or status bars. `PutEditor.tsx:32` still marks a destination as local or cloud. Change the sentence to "Send controls show where the content goes. Run records identify the engine used." Do not promise host labels everywhere.

### 7. "Transcribes speech locally with Whisper" is stated as absolute (README.md:201)
`SECURITY.md:417` calls local a *default*. Check whether a speech endpoint can be assigned in Settings > Engines. If one can, write "by default". Line 205 lists speech recognition as an assignable job, so the two lines read as contradictory now.

### 8. Line 11 is too long for the 25-word rule
The other sentences pass, but line 11 is close and its list is dense. Split it: "The Desk takes its cues from Amiga Workbench. It has objects, drawers, movable windows, menus and a dock." Lines 113 and 190 are also near the limit.

### 9. The Mermaid diagram puts input above the Desk (README.md:35-46)
The diagram starts from "Voice · Notes · Meetings · Connected sources" at the top, which keeps a little of the old capture-first lead. It is acceptable. Optionally put "Ask / Agents / Automations" on the first row and the inputs as a side feed, to match line 3.

### 10. A missing link (README.md:106)
"The Call" exists in the code (`web/src/desk/callLoopWiring.ts`), but no guide is linked. Link it, or move it into the Threads guide link.

### Checked and correct
- The worktree, branch and preview claims (lines 113-116): preview shows the brief, repository, branch and refusals before launch, and needs tmux.
- The automation choices (When, Do, About, With, Review by, Put it in) and the four output targets (Inbox, Needs you, Today, or a destination that only prepares the send).
- The 14 built-in plugins: the other plugin files are actuators.
- YOLO as the default (`docs/AUTHORITY.md:3`) and no telemetry (`docs/SECURITY.md:8`).
- Slack as a destination, Cursor as an MCP client, and every relative link target and anchor exists.

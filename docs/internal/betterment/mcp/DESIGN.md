# The desk's tools for every engine (MCP): betterment design

Status: draft for the owner. Input: `MODEL.md` (the MCP map, 2026-10-17).
Companions: `../workbench/DESIGN.md` (Automations), `../engines/DESIGN.md`.

## 1. The job

Owner, 2026-10-17: "Did you prioritize the various super rich MCP features
in your request? I sure hope so."

HoldSpeak has 257 MCP tools over his meetings, people, projects, decisions,
memory, Jira and GitHub. Two jobs need them:

- **An automation that does real work.** "Draft my Friday update" should be
  able to look up the week's meetings, each person's open commitments, the
  decisions and the Jira state itself. It should not be limited to the text
  we put in its prompt.
- **Setting things up by asking.** He says "make me a Friday update
  automation on Claude Code" in a Thread, or to his own Claude Code or Codex
  session, and it exists. No form is needed.

## 2. What it is today

- An automation run is one model call with **no tools** (`../workbench/MODEL.md`
  §1). It sees only the sources attached to it.
- Agents already get the desk's tools, but only in the Conductor's terminal
  sessions. Each launch gets its own credential and a fixed tool set called
  CONDUCTOR: 96 reads and 48 local writes, with no sending, no config and no
  authority changes. People are read-only, decisions can only be proposed,
  and an agent edits only what it created itself (`MODEL.md` §2-4).
- The one-shot `claude -p` path has no MCP at all (`agent_summarizer.py`).
- On MCP, an automation can only be made in the old shape: cron text and a
  recipe id. Do, About, Put it in, plain triggers, results, cancel, CLI
  engines, removing an engine and spend limits are all missing (`MODEL.md`
  §6).

## 3. Why it fails

The rich part of the product (the tools) and the part that would use them
every day (automations) were never connected. The tool set and the gate
exist; nothing hands them to a run.

## 4. The design

### The rule

**Every automation run on an engine that can use tools gets the desk's
tools, through the CONDUCTOR set.** He gets the same rule he already has for
threads:

| The agent may | Without asking |
|---|---|
| Read anything on his desk: meetings, notes, people, projects, decisions, memory, Jira, GitHub | yes |
| Write on the desk: notes, drafts, Needs-you rows, *proposed* decisions | yes |
| Send anything off the machine | no: it *prepares* the send, and he presses Send |
| Change settings, engines, schedules or authority | no |
| Run other models (nested model tools) | no |

Nothing new is invented. The set is CONDUCTOR, and the gate is the existing
`tool_authority.py`.

### Which engines get tools

- **Agents on this Mac** (Claude Code, Codex, pi): the run attaches
  HoldSpeak's MCP server, and *only* that server. His Gmail, Drive and
  Calendar connectors and his pixellab server stay out (decision 2).
  Built-in tools are off (no shell, no file edits) unless the automation
  has a folder in About (Automations decision 3), and then they are
  read-only.
- **Servers and services that accept tool calls** (the Check already asks
  whether an engine supports them): the hub runs the same tool loop that
  Thread uses, with the same set.
- **Engines without tool calls**: these work as today, with the sources in
  the prompt. The With line says so.

### What he sees

- **On the With line**, under the engine: "Can use your desk: reads
  meetings, people, projects, Jira, GitHub; writes notes and drafts; never
  sends." For an engine without tools: "Reads only what is in About."
- **On each result: Looked at.** This is a folded line that lists what the
  agent used, in words: "3 meetings this week · Mira's open commitments ·
  PLAT-212, PLAT-219 · decision 'Rollback runbook'". Each one is a link.
  The hub serves every tool call through the run's credential, so it knows
  every call and needs nothing from the agent.
- **Wrote:** any desk writes the run made, each with Undo.
- **Prepared:** any send it prepared, with Send.

### Setting things up by asking (MCP parity)

Every verb in the Automations and Engines designs has an MCP tool. An agent
can therefore do what he can do on the face, under the same classes:

- `automation.create/update` with the sentence fields: name, `when`
  (plain: schedule, event or manual), `do`, `about`, `with`, `put_in`,
  `spend_limit`. (These are the existing `workbench.*` tools, extended; the
  stored kind stays `workbench`.)
- `automation.results` (the newest result, rendered, with Looked at,
  cost and failure reason), `automation.cancel`.
- `model_library.connect_cli_engine`, `model_library.remove`,
  `concierge.detect` listing the CLIs it finds.
- Turning a schedule on, choosing an engine and setting a spend limit are
  AUTHORITY or CONFIG. In a Thread they stop for his press, as the rule
  says. From his own Claude Code session (an owner credential), they just
  work.

## 5. Decisions for the owner

1. **Automation runs get the CONDUCTOR set** (reads, including People, plus
   desk writes; no send, config or authority). Recommended: yes.
2. **Only HoldSpeak's server inside a run.** His other MCP servers and the
   claude.ai connectors (Gmail, Drive, Calendar) stay out. Recommended:
   yes. A later slice can add "also use: Gmail" for each automation if he
   wants it.
3. **Nested model tools stay off inside a run** (the 13 tools that run a
   model). Recommended: yes.

## 6. How we know it worked

- He makes the Friday update automation with Claude Code, adds nothing to
  About, and presses Run now. The result names last week's real meetings
  and each person's open commitments. Its Looked at line lists them, and
  every item is a real link.
- In his own Claude Code session he says "make me a Monday 1:1-prep
  automation for Mira, Theo and Jun on the LAN model". The automation
  appears in the Automations app, complete, and Run now works.
- No run ever sent anything or changed a setting without his press, and
  no run ever reached Gmail.

# Agents and Threads

HoldSpeak has three related but different concepts:

- An Agent is a saved persona. It supplies instructions for a conversation or
  an automation.
- Ask is the current Desk conversation surface for questions and follow-ups about your work.
- A Thread is the retained multi-turn conversation and API contract behind
  conversation work. Ask retains the exchange as a Thread when the first answer lands.
  The current window follows that conversation in place.

A coding agent is different again. Claude Code, Codex, and pi are installed
coding-agent processes with a repository, worktree, and launch record. See
[Coder integration](CODER_INTEGRATION.md).

## The conversation window

Open **Ask** or select **Ask about this** on a Desk object. **About** is the
starting context for retrieval. It does not promise that the answer can use
only those records. The selected mode, tool policy, and operation rules still
decide what the request can read or write.

Ask keeps each completed exchange as part of its Thread.
Use the follow-up box to continue it and **Recent** to reopen a retained conversation.
Use the first row in **Recent** or press **⌘N** to start another conversation.
A read failure offers **Try again** for that read.
A failed run offers the applicable run recovery.
Closing the window does not establish that the server run stopped.

Each answer offers **Make it a task**, **Save as note**, **Copy**, and **Send…** where applicable.
Ask opened from a Note can also offer **Add to note**.
Saving a Note creates a separate editable output in addition to the saved conversation.
The active result uses **References** for read evidence. **Wrote** and **Prepared**
remain trace/API terms for recorded writes and prepared sends; they are not
separate controls in the current Ask face.
The current Ask does not use the older **Keep** or **Bin** decision for its exchange.

The separate Thread window and its mode, branching, slash-command, and call controls are parked.
The retained Thread service still exposes their API operations.
Do not treat a backend route as a current Ask control.

## What a Thread keeps

The hub stores messages, message parts, frozen source references, drafts, and
the Thread tool policy. Edit and regenerate actions create branches. Delete is
a soft delete. A deleted Thread is not shown as live, but its retained record
is not treated as a physical purge.

| Action | Route |
| --- | --- |
| Create, list, read, update, delete | `POST /api/threads`, `GET /api/threads`, `GET /api/threads/{thread_id}`, `PATCH /api/threads/{thread_id}`, `DELETE /api/threads/{thread_id}` |
| Send a turn | `POST /api/threads/{thread_id}/turns` |
| Stop the active turn | `POST /api/threads/{thread_id}/abort` |
| Branch or regenerate | `POST /api/threads/{thread_id}/branch`, `POST /api/threads/{thread_id}/regenerate` |
| Keep a result | `POST /api/threads/{thread_id}/keep` |
| Import, compact, annotate, or create a todo | `POST /api/threads/import`, `POST /api/threads/{thread_id}/compact`, `POST /api/threads/{thread_id}/annotations`, `POST /api/threads/{thread_id}/todo` |
| Decide a held tool call | `POST /api/threads/{thread_id}/decide` |
| Interview commands and promotions | `POST /api/threads/{thread_id}/interview`, `GET /api/threads/{thread_id}/interview/promotions` |

[`api-surface.json`](api-surface.json) lists the complete route contract.

## What happens in a turn

`ThreadService.start_turn` validates the text, separates People references,
freezes the references, and admits one model route. The server returns the
turn ids and streams the result on the runtime bus.

The stream can include `thread_turn_started`, text deltas, pending-tool and
tool-result frames, status frames, and `thread_turn_done`.

Important limits are:

- One turn runs at most 10 model passes.
- One tool call has a 30-second deadline.
- One tool result is capped at 32,768 bytes.
- The tool palette is fixed when the turn starts. A mode change cannot widen
  an active turn.
- An aborted turn ends as `aborted`. Its receipt is `indeterminate` when the
  hub cannot prove the final provider result.
- People text is redacted before it reaches a cloud route.

## Tool calls

The Thread palette is a subset of the registered MCP catalogue. The
authority table gives a Thread only tools classified as `work`. A Thread does
not receive tools that send data out, change authority, or change system
configuration. Those actions need the owner surface or their own admitted
route.

The per-Thread policy (`allow`, `deny`, or `ask`) is checked first. Without a
specific policy, the Control mode applies:

| Control mode | Evidence read | Candidate builder | Effect proposal |
| --- | --- | --- | --- |
| **YOLO** | Runs | Runs | Runs |
| **Normal** | Runs | Runs | Held for a decision |
| **Secure** | Runs | Held | Held |

A held call waits in the decision box. Resolve it with
`POST /api/threads/{thread_id}/decide`. Tool states include `admitted`,
`awaiting_decision`, `denied`, `completed`, and `discarded`.

## Interview is a Thread mode

Interview is a saved Thread mode. It uses the normal model runtime and the
mode's fixed tool palette. Its sections are Goals, Projects, What matters,
Cadences, People, Decision log, Delegation, and Sources & models.

Interview records facts with their source message, presents suggestions with
their supporting facts, and applies owner commands against an expected
revision and command id. A stale revision is rejected. Repeating a command
with the same digest does not apply it twice.

The People section is a handoff. HoldSpeak does not save a turn that contains
People content until you continue in the People flow. The Interview tools are
`interview.get`, `interview.change_section`, `interview.record_fact`, and
`interview.suggest`. A suggestion does not install an automation or grant
authority.

## Grounding

About records are the retrieval starting point. The hub resolves the explicit
references and the request may use the selected mode's permitted retrieval
tools. It does not treat a label on the face as an authority grant.

`hydrate_grounding_blocks_detailed` resolves Meetings, Artifacts, qualified
references, and optional memory search. It expands a Meeting to a summary or
transcript, removes duplicates, and marks unknown references. The current
caps are 16 references per turn and 12,000 characters per transcript. The
result reports `selection`, `matched_count`, and `overflow_count`.

Roadmap rails use `hydrate_rails_refs`. It reads a named Delivery Workbench
path as capped plain text. It refuses unknown, stale, or unreachable paths.

## Memory

Memory is a searchable store of retained Notes, Meetings, Artifacts,
decisions, Threads, and related records. `GET /api/memory/search`,
`GET /api/memory/recall`, and `GET /api/memory/pages` serve the store.
Meaning search has explicit turn-on and turn-off routes. The MCP operation is
`memory.search`.

Memory search selects evidence. It does not grant authority. An empty result
is a real empty result. Automation memory is a separate JSONL file capped at 100 entries.
A run can recall at most 20 recent entries and 2,048 bytes for its next prompt. Memory can inform
a run, but it never authorizes a run.

## Workflows

A Workflow is a saved sequence of supported processing nodes. The sequence service validates the graph and freezes route evidence before each child call.
It returns a parent receipt, child receipts, steps, and an Artifact projection. A node failure policy can hold, skip, or carry output.

`sequence.run`, `sequence.cancel`, `workflow.run`, and `workflow.cancel` use
the same admitted path. They are not a general scheduler or a free-running
agent loop. See [Automation](AUTOMATION.md).

## MCP

The Desk, a supported Thread, and an external MCP client reach the same hub
contracts through their applicable transport and principal. The local MCP
sidecar is a proxy to the running hub. It does not open a second Desk
database. See [MCP sidecar](MCP_SIDECAR.md).

## See also

- [Ask on the Desk](WEB_DESK.md#ask-about-your-work): current Ask controls.
- [Interview](INTERVIEW.md): the retained Interview mode.
- [Coder integration](CODER_INTEGRATION.md): launched coding sessions.
- [Automation](AUTOMATION.md): configured recurring work.

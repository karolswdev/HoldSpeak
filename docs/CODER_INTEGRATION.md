# Coder integration

A Coder is a live Claude Code, Codex, or pi process launched for a repository
task. A saved Agent persona is not a Coder. An inference CLI used by an
Automation is also not a coding handoff. See [Models](MODELS.md) for that
engine path.

## Hand a Desk item to a coder

1. Open an action, decision, Project item, Note, Meeting, Artifact, or eligible
   Project issue.
2. Select **Hand to agent**.
3. Inspect the preview. It shows the item, sources, People cut, acceptance
   checks, repository, branch, worktree, Control mode, and egress host.
4. Choose Claude Code, Codex, or pi. Choose **Review by** when a separate
   reviewer is needed.
5. Press the launch control.

The hub validates the agent profile and runtime prerequisites, then resolves a
registered local repository. If the Project has no local source, it can use the
GitHub fallback described below. It composes a bounded brief, creates a Git
worktree, and records the launch. The brief is capped at 32,768 bytes. A
missing repository, executable, tmux, hook, or pi coding engine is a named
refusal in the preview or launch record.

Each hand uses a new worktree and a branch derived from the item. A repeated
hand of stopped work continues in its existing worktree. A brief still held
for one launch resumes that launch and its selected agent; it is not silently
relaunched with a different profile.

## File a Project repository

If you already have a local checkout, open a terminal in its exact Git top
folder. In **Context**, an unbound shell shows **Register workspace folder**.
Check the **Repository folder** field and press **Register folder**. The field
stays in place and the refusal remains visible if registration fails. A
subfolder is refused before anything is persisted. After registration, select
a Project in the inventory and press **Use repository in project**. This binds
the registered source to the Project; it does not clone the checkout. A later
**Hand to agent** uses that source and creates the agent worktree from it.

If no local checkout is registered, use the Project Info window to name a
GitHub repository as `owner/name`. Press **Register** when the Project Room has
a watched repository that is not registered. Registration records the Project
repository. It does not clone it.

The first hand for an item in that Project clones the repository from
`github.com` with the local GitHub CLI (`gh`). HoldSpeak registers the clone as
a Delivery Source, then starts the agent in a new sibling worktree. The clone
and worktree stay on the hub that runs the Desk. A missing `gh`, sign-in,
repository, or clone result is a named refusal. The Project state shows
**Not cloned**, **Cloned**, or **Not read** when the registration store cannot
be read.

The repository shown in a Project Room is a source for context. It is not proof
that the local clone exists. Read the Project repository state and the launch
record before you act on a worktree.

The default concurrent working limit is `agents.working_at_once = 6`. Only
agents that work or need the owner use a slot. When the limit is full, choose
**Start when one is free** to queue the hand. The queue starts it when a slot
opens. A done, quiet, or stopped agent does not block a new hand.

## What the brief contains

The brief starts from the item and can add its meeting, Project decisions and
open commitments, bounded memory, and repository `.hs/` context. It includes
the Control mode and acceptance checks. People context is included when the
brief resolver allows it, with shared redaction for secrets.

The launch sheet is a preview. It has no launch side effect until you press
the launch control. The resulting worktree and launch record are the source
of truth after the press.

## Observe, draft, reply

Open **Go > Work > Terminals** for local shells and coding-agent terminals.
Each terminal opens in its own Desk window, with separate output and input.
Press **Type** in the window you want to control. Closing its view
leaves the process running. See [Terminals](TERMINALS.md) for arrangement,
message input and the current screen-capture limits.

## Inspect the connected workspace

Open **Go > Work > Terminals** and select the session that belongs to the
launch. The workspace keeps the terminal and its repository views separate.

- **Files** reads the selected source and registered worktree. It does not
  replace that worktree with the source's primary checkout.
- **Changes** shows the selected worktree's changed-file records and a bounded
  diff. Select files, press **Stage**, and press **Commit** after you enter a
  local commit message. It uses plain statuses such as **New file**, **Changed**,
  **Staged**, **Staged and changed again**, **Renamed**, and **Deleted**. It
  shows separate working-tree and staged diffs and marks a long diff as
  shortened. A failed Stage keeps the selection for retry; a failed Commit
  keeps the staged changes and commit message for retry.
- **Context** shows the Project, source, worktree, branch, brief, agent,
  Needs you state, review, Program, and HoldSpeak tools facts.

Open a file, press **Edit file**, then press **Save file** to write the edit to
that same worktree.
HoldSpeak checks whether the file changed after you opened it. If it changed,
the write returns a conflict and keeps the new edit in the Desk. The operation
is scoped by source ID and worktree ID, so an unknown worktree does not fall
back to the primary checkout.
After a conflict, **Read latest** shows the current disk text while the edit
stays in place. Review it and press **Save reviewed edit**. That save checks
the revision you just read; a further disk change still refuses the write.

For a launch, Context is bound only when the stored terminal target ID and
generation still match the live pane. A session name, hook label, or folder
alone does not create a launch association. **HoldSpeak tools** shows a
configured server only when the launch record contains its MCP configuration.
**Configured** is not proof of a successful handshake. **Unknown** is an
honest absence of that configuration fact.

When the terminal has a source and worktree but no Project, select a Project in
the inventory and use **Use repository in project**. This adds the registered
repository as a Project resource. It does not move the worktree or launch.

Opening the launch, origin, or Program uses its recorded ID. It does not infer
an object from terminal output. A queued hand stays visibly queued until its
own launch produces a matching terminal.

The Desk reads live session state from:

| Action | Route |
| --- | --- |
| List status and sessions | `GET /api/coders/status`, `GET /api/coders/sessions` |
| Read bounded pane output | `GET /api/coders/{key}/peek` or relay equivalent |
| Arm or disarm a pane | `POST /api/coders/{key}/arm`, `POST /api/coders/{key}/disarm` |
| Send text or named keys | `POST /api/coders/{key}/steer`, `POST /api/coders/{key}/keys` |
| Keep a draft as a Note | `POST /api/coders/{key}/keep-note` |
| End a session | `POST /api/coders/{key}/kill` |
| Read steering audit | `GET /api/coders/steering/audit` |

The same pane is identified by `agent:session` plus its pane identity and
generation. A peek strips terminal control codes and applies byte and line
caps. The Desk can tell you when the bounded pane view has not changed.

Steering is deliberate input to the selected live pane. A draft or **Keep**
does not send text. The hub never sends a shell command as a steering reply.
It records the text hash, target, submit choice, and operation outcome. A
recycled or missing pane produces `pane_mismatch` or
`pane_identity_required` and types nothing.

## Review and the Gate

**Review by** records a separate reviewer profile with the hand's acceptance
checks. The reviewer starts after HoldSpeak observes a new builder commit; it
is not an immediate second launch. The review metadata stays with the launch so
the pair survives a hub restart. Reviewer options are Claude Code, Codex, or
pi, and reviewer launches are read-only. A reviewer does not replace the
builder's worktree or owner decision.

The Gate is a different control. A launch can arm the Gate for its new
worktree, while steering remains an owner reply to a pane. The Gate holds a
matched tool call before it reaches the coder. It records only a redacted
preview and argument hash for the hook path. See [Gate](GATE.md).

## Authority

Watching sessions is read work. Sending text, keys, killing a session, and
launching a coder are admitted through their own operations and audit rows.
The Control mode and launch-bound grants apply before delivery.

- A grant covers one pane and lasts from 10 seconds to 1 hour. The default is
  15 minutes.
- In **YOLO**, a registered session can steer without a separate arm press.
  The hub still checks pane identity before each key.
- A pane mismatch, kill, Control mode change, or hub restart clears the grant.
- A relay uses the destination machine's posture, grant, and audit.

## Result states

| State | Meaning |
| --- | --- |
| `live` | A bounded peek returned a new content hash. |
| `not_modified` | The pane has not changed since the supplied hash. |
| `pane_gone` | The pane no longer exists. |
| `tmux_absent` | tmux is unavailable. |
| `unarmed` | No live grant covers the pane. |
| `delivered` | Text reached the pane. |
| `pane_mismatch` | The target changed, so the grant was revoked. |
| `pane_identity_required` | The request did not identify one pane. |
| `transport_error` | tmux could not deliver the input. |

Launch delivery has separate states such as `queued`, `pending`,
`delivering`, `sent`, and `hooks_missing`. A launch can exist while its brief
is still held. Read `instruction_state` and the launch failure token.

The connected workspace is a HoldSpeak composition of Desk windows, local
tmux, Delivery Sources, launch records and Programs. Nodeterm and similar tools
were workflow inspiration. This guide does not claim an infinite canvas, SSH
projects, reboot restoration, remote PTY transport, or GitHub Issues board sync.

## See also

- [Agent hook install](AGENT_HOOK_INSTALL.md): session and question signals.
- [Gate](GATE.md): held tool calls.
- [Automation](AUTOMATION.md): recurring agent handoffs.
- [Troubleshooting](TROUBLESHOOTING.md): receipt-first recovery.

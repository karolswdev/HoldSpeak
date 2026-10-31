# Terminals

Keep local shells and coding-agent terminals open beside each other on the Desk.
Each window has its own output, input and typing control.

## Open a workspace

1. Open **Go > Work > Terminals**, or find **Terminals** in Search.
2. Find a session by its name, agent, command or folder.
3. Press a session row to open its window. Repeat for another session.
4. Move or resize the windows. Use **Tile terminals** to arrange the open
   terminals together. Other application windows keep their placement.

Press an open session’s row to bring its window to the front.
The **Sessions** face shows the selected job above the session list.
It shows the brief, Project and available agent state.
Use **Open terminal** to return to its shell.
Agent state updates when HoldSpeak receives its session events. Press
**Refresh** to discover shells you started outside the Desk.
The Desk keeps open windows and their placement in the hub, so a reload can
restore them. A terminal that has ended stays unavailable; its old window does
not become a different shell with a reused pane number.

## Use the connected workspace

Select a session to inspect its connected work. The workspace has three faces:

- **Sessions** lists live terminal rows. Use **Project** to filter rows by
  Project. Use **Find a session or folder** to search the inventory.
- **Files** opens the repository browser for the selected source and worktree.
  It does not switch to the source's primary checkout.
- **Context** shows the Project, source, worktree, branch, brief, agent,
  Needs you state, review, Program, and HoldSpeak tools facts.

Project resources in **Context** have a named action such as **Open note** or **Open decision**.
Supported resources also have **More** with **Ask about this** or **Hand to an agent**.
These actions use the existing Ask window and agent handoff sheet.
Unavailable resources keep their **Retry** action.

### Prepare work from a file

1. Open a file in **Files**.
2. Press **Prepare agent**.
3. Edit the task words.
4. Expand **Source context** to inspect the captured file reference.
5. Select the agent and review choice.
6. Press **Start**.

The prepared brief includes the repository, worktree, path and captured read revision.
Long file content is shortened and marked in the source context.
**Cancel** keeps the task words for that file.
Preparing a brief does not start an agent.
After a refusal, the task words stay. Press **Start** to retry.
An unchanged brief reuses the Note already created for that task.

The read copy is reference material. The agent starts through the Project's existing repository flow in its own worktree.
This does not resume the selected shell or copy its uncommitted files into the new worktree.
The existing Project repository resolver chooses the launch repository; this flow does not add a repository picker.

### Review files and changes

The **Files** face also has a **Changes** door. It shows changed files and a
bounded diff for the selected worktree. Select files, press **Stage**, enter a
commit message, and press **Commit** to make a local Git commit. These controls
do not push or publish the commit. Each path has a plain status such as **New
file**, **Changed**, **Staged**, **Staged and changed again**, **Renamed**, or
**Deleted**. The face shows separate **Working tree diff** and **Staged diff**
sections; a long diff is marked **shortened**. With no changes it says **No
changed files** and shows the branch or that the worktree is clean.

If Stage fails, the selection stays in the face. Press **Retry** to stage it
again. If Commit fails, the staged changes and commit message stay in place.
Press **Retry** to try that commit again.

Open a file to read it. Press **Edit file**, then press **Save file** to write
the edit to that same worktree. HoldSpeak checks whether the file changed after
you opened it. If it changed, the save returns a conflict and keeps your edit.
A failed save does not move the edit to another worktree.
Press **Read latest** to compare the current disk text with your kept edit.
Review your text, then press **Save reviewed edit**. If the file changes again,
the save refuses again. Reading the latest file alone does not change your
draft's saved revision.

### Inspect workspace context

The Context face uses these states:

| State | Meaning |
| --- | --- |
| **Bound workspace** | The terminal target still matches one recorded launch. |
| **Worktree only** | The terminal folder is inside a registered worktree, but no launch target matches it. |
| **Unbound shell** | The terminal has no registered source or worktree. |
| **Context unavailable** | The live terminal remains visible, but a context source could not be read. |

For a bound launch, **HoldSpeak tools** shows the configured server and its
read-only fact when the launch record has that configuration. **Configured** is
not proof of a successful MCP handshake. **Unknown** means that no configuration
fact is available.

If a source has no Project, select a Project in the inventory. The Context face
then offers **Use repository in project**. Select it to add the registered
repository as a Project resource. The path stays on the hub.

For an unbound shell with a local Git checkout, Context shows **Register
workspace folder**. The **Repository folder** field starts with the shell's
current folder. Press **Register folder** to register it. The field stays in
place and the refusal remains visible if registration fails. The path must be
the exact Git top folder; a subfolder is refused before anything is persisted.
After registration, select a Project in the inventory and press **Use
repository in project**. A later **Hand to agent** uses this registered source
and creates its worktree; no API or Automation setup is needed.

The layout uses existing Desk windows, repository records, launch records and
Program records. Nodeterm and similar tools were workflow inspiration. HoldSpeak
does not add an infinite canvas, a second project store, or a second Git system.

## Type or speak

Press **Type** in the terminal you want to use. The press focuses its screen
while the hub checks the temporary grant. Wait for **View only** before you type.
If you move to Find or Message while the check waits, its reply does not move
focus back to the terminal.
Keys go to that terminal. **View only** turns its typing control off.
The hub's control level and temporary pane permission still apply.

Use **Keys** for an interrupt, Escape, Tab, arrows or Enter.
Escape in the terminal belongs to the program running there.
Use the window's Close or Back control to leave its view.

Press **Message** to open the optional voice or buffered-input field. It is
closed on a new terminal unless a draft is already saved. Hiding it keeps the
draft. Press **Send** to submit the message to the terminal. A failed send
keeps the draft. A late successful send must not clear text you wrote after it
started.

## Start work

Press **New terminal**, enter a shell name and, optionally, a local folder.
The folder belongs to the machine that runs the hub.

Each creation form replaces the inventory while open. Press **Cancel** to return to the list.
The new shell keeps its name and folder when you change forms.

**Start an agent** uses the same Project, agent and review controls as the
Agents window. It hands the work through HoldSpeak's existing agent flow.
See [Coder integration](CODER_INTEGRATION.md) for setup and
[Agents and Threads](AGENTS_AND_THREADS.md) for the different agent flows.

In a narrow window, open **More** for **Refresh** and **Tile terminals**.

## Close a view

Closing a terminal window leaves its shell or agent running.
Open it again from Terminals to see its current output.
On a phone, Back returns to the inventory.

An interrupt is different: **Keys > Ctrl-C** sends Ctrl-C to the current program.
End a shell from its own prompt or use the existing agent Stop control when
that is the job you intend. A browser close is not a Stop command.

## Current limits

- This inventory shows local tmux sessions. It does not offer remote terminals
  that lack an authenticated output connection.
- Output refreshes from a bounded recent screen capture. It is not a complete,
  saved transcript or a byte-for-byte PTY stream.
- Resizing a Desk window changes the view. It does not yet resize the terminal
  process on its host. A wide terminal can scroll inside its window on a phone.
- Tmux can keep a session alive when a view closes. A machine reboot can end it;
  the workspace does not promise to restart that process.
- Files, Changes, and Context work with registered local sources and worktrees.
  They do not provide SSH projects, remote terminal output, or machine restart
  recovery.
- Local Git stage and commit are available. Push, sync, publish, and a two-way
  GitHub Issues board are not part of this workspace.

## See also

- [The Desk](WEB_DESK.md): windows, arrangement and navigation.
- [Control modes](AUTHORITY.md): operation authority.
- [Programs](programs.md): coordinate a goal across coding agents.

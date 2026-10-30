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
Agent state updates when HoldSpeak receives its session events. Press
**Refresh** to discover shells you started outside the Desk.
The Desk keeps open windows and their placement in the hub, so a reload can
restore them. A terminal that has ended stays unavailable; its old window does
not become a different shell with a reused pane number.

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

## See also

- [The Desk](WEB_DESK.md): windows, arrangement and navigation.
- [Control modes](AUTHORITY.md): operation authority.
- [Programs](programs.md): coordinate a goal across coding agents.

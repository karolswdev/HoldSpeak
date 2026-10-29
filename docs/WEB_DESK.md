# The Desk

The Desk is HoldSpeak's web operating surface. It holds records and opens the
tools that work with them. The local hub owns the records and Desk windows.
The browser presents that state.

## Start work

1. Start the hub and open the printed URL.
2. Open **Today** for current work.
3. Open **Needs you** for items that need your action.
4. Use **Go** or Search to open an app, Project, drawer, or record.

On a phone, **Go** lists the apps and a window fills the screen. **Back**
returns to the previous window. The same hub can serve another browser or a
configured MCP client.

## Create work

The **Desk** menu offers **New Note**, **New Decision**, **New Automation**,
and **New Project**. On a phone, use **Go > New** or Search.

**New Note** opens an editable Markdown Note. **Develop this thought** opens
the refinement Workbench for that Note. The UI calls the record a **Note**.
**Thought** is a legacy domain term for the refinement flow.

**Ask AI** opens the **Ask** window. Ask and Thread are one window. Start a
new conversation with the first row in **Recent** or **⌘N**. The first
question is kept as a Thread, and later questions continue that Thread. A
separate Thread window is not the current navigation path.

**New Project** opens the Project setup Door. See [Project Rooms](PROJECT_ROOMS.md).

## Open and file records

Select an object, then press Enter or use its open verb. The **Object** menu
shows verbs for the selected record. Use **Ask about this** on a Note, Meeting,
Artifact, Decision, Mode, Project, Zone, Drawer, or person.
People itself is not an Ask target. A person uses **Ask about <first-name>**.

The selected object appears in Ask's scope control (accessible label
**About**). This tells retrieval where to start. It does not restrict an Ask
tool loop to one object. The engine can read other permitted Desk records when
the request and tools allow it.

A drawer shows its contents. Dragging changes the Desk presentation. Filing
controls change the record's stored drawer. A view change does not move a
record to another hub.

## Use windows

Speak, Meetings, Agents, Programs, Settings, Ask, Projects, People, and other
apps open in Desk windows. Drag a title bar to move a window. Drag an edge or
corner to resize it. Iconify a window to keep it in the dock. Select its dock
entry to return to it.

Use **Window** for **Close**, **Minimize**, **Next window**, **Tile left**,
**Tile right**, **Zoom**, **To back**, **Stage**, **Arrange all**, or **Back**
when the selected window supports the action.
For hub-backed windows, the hub stores open state, geometry, stacking, and desk
membership in its `desk_windows` records. The browser keeps a local cache for
first paint, then the hub state replaces it. Another browser can therefore see
the same hub-backed window state after it loads the hub. Some transient views,
including Ask, are view-specific and are not hub window rows.

Every window write has a desk revision. If the owner moved a window while an
older request was pending, the hub can reject the stale request. Ask's **Undo**
restores the exact window state only when that state is still current.

On a phone, use **Back** to return from a full-width window. Do not assume a
phone has the same visible window geometry as a desktop browser.

## Ask about your work

1. Open **Ask AI** from **Go**, or press **⌘I**.
2. Use the scope control (accessible label **About**) to select a record.
3. Enter a question, then select **Ask** or **Send**.

With no object, Ask starts with the whole Desk. With an object, its reference
appears in the scope control (accessible label **About**). That reference is a
retrieval starting point, not a blanket access boundary.

Ask and Thread share one durable conversation. The answer shows **References**.
The retained trace can also expose **Looked at**, **Wrote**, and **Prepared**.
**Looked at** names the records used.
**Wrote** lists Desk changes and offers **Undo** when the change supports it.
**Prepared** lists a send that still needs your **Send** press. HoldSpeak does
not send from a prepared result by itself.

An engine must support the required tools. A held tool call asks for **Allow
once** or **Deny**. A refused or unavailable tool does not prove that its
result exists. Read the receipt and the tool result.

Ask retains completed exchanges as a Thread. Use the follow-up box to continue
the conversation. Open **Recent** and select its first row to start a new
conversation, or press **⌘N**.
When Ask opens from a Note, **Add to note** can copy the answer into that Note.
**Save as note** creates a separate editable Note from the answer.
The current Ask does not expose the parked Thread window's mode, branching, slash-command, or call controls.

## Record a meeting

Use the recorder control to start or stop a meeting. Hub recording is separate
from browser microphone input used for voice typing. Open **Meetings** to read
the transcript, run configured intelligence, and review its results.

In **Meetings**, select **Import** and choose a supported recording or
transcript. The Meetings window also accepts a file drop and opens the import
form. The active Desk does not provide a general file drop. Read [Meeting
mode](MEETING_MODE_GUIDE.md) for source and engine prerequisites.

## Set preferences

Open **Settings** from the HoldSpeak menu. The active Settings sections
include **Meetings**, **Notices**, **Accounts**, **Calls**, **Agents**,
**Desk**, and **This Mac**. **Engines** is under **This Mac**;
**Wallpaper** is under **Desk**. Search finds a setting.

The old **Places** entry opens the Wallpaper flow when it is present. The
canonical path is **Settings > Desk > Wallpaper**. See [Places](ENVIRONMENTS.md).

## Keys

| Key | Action |
| --- | --- |
| **⌃N**, **⌃T** | New Note |
| **⌃⇧N** | New Decision |
| **⌘I** | Ask |
| **⌘K** | Search |
| **⌃1** | Today |
| **⌃2** | Meetings |
| **⌃3** | People |
| **⌃4** | Agents |
| **⌃5** | Speak |
| **⌃7** | Programs |
| **⌃J** | Needs you |
| **⌃,** | Settings |
| **⌘⇧E** | Overview |
| **⌘/** | Keyboard shortcuts |

The browser can keep some **⌘** keys. Use the menu alternative when a browser
or operating system shortcut takes precedence.

## Troubleshooting

| Problem | Action |
| --- | --- |
| A window is missing | Check the dock and **Window** menu. Reload only after you read the hub state. |
| A window moved back | Check for a stale revision or another browser that changed the same window. |
| A verb is missing | Select the record that the verb needs. Some verbs apply only to one object kind. |
| Ask cannot answer | Read its engine, source, tool, and permission result. Check **Settings > This Mac > Engines**. |
| A prepared send did not leave the Desk | Select **Send** after reviewing the target and content. |
| The menus are hidden | Select **Back to Desk**, or press Escape. |
| A record is not in About | Open the record and select **Ask about this**, or use **+** in Ask. |

## See also

- [Getting Started](GETTING_STARTED.md): installation and first capture.
- [User Guide](USER_GUIDE.md): daily tasks, Threads, People, and follow-through.
- [Project Rooms](PROJECT_ROOMS.md): source watches and Project work.
- [Calls](calls.md): Calls and the Line.
- [Phone](phone.md): paired-phone service limits.
- [Places](ENVIRONMENTS.md): Wallpaper, motion, sound, and Settle in.
- [Control modes](AUTHORITY.md): permission and approval rules.

# The Desk

The Desk is the HoldSpeak web app. It holds your records and opens your tools.
This guide is for the person who works on the Desk every day. It describes `main`
(checked against the live Desk on 2026-10-27).

## Start work

1. Open the address that `holdspeak` prints.
2. Open **Today** to see current work. It is the first icon in the dock.
3. Open **Needs you** (**Go > Needs you**, or **⌃J**) for items that need your action.
4. Use **Go** to open an app, project or drawer.

The desk shows your drawers, Projects and Notes as icons. The floating dock
at the bottom opens **Today**, **Meetings**, **People**, **Agents** and
**Speak**; the red button records a meeting. A badge on an icon is a live
count, never a zero. An iconified window gets its own tile in the dock.
**Go > Archive** and **⌘K** open the Archive, where the records you put away
wait until you restore them.

On a phone, **Go** lists the apps. An app fills the screen.
See [Getting Started](GETTING_STARTED.md) for the first capture.

## Create work

The **Desk** menu offers **New Note**, **New Decision**, **New Automation**,
**New Project**, **New Meeting**, **New Person** and **New Drawer**. On a phone,
use **Go > New** or Search. **New Project** opens project setup. See
[Project Rooms](PROJECT_ROOMS.md). To start a conversation, open Ask (**⌘I**).

**New Note** opens a Note window. The toolbar has **Done**, **Ask about
this**, **Find the tasks**, **Project** and **Send…**. The Note shows its
Markdown in place as you type: headings, emphasis, lists and task boxes,
links, code, quotes, tables and Mermaid diagrams. The status bar shows when
the Note was saved. **Done** finishes the note. Asking about a note does not
move it to another drawer.

## Open and file records

On a desktop, select an object, then press Enter or open it with a double
click. The **Object** menu shows the verbs that apply to the selection.
Use **Ask about this** to ask about that record. A person has **Ask about
<name>**.

A drawer shows its contents. Existing knowledge collections appear as
named drawers. Their members can also remain on the desk. Use Search to
find a drawer by name, including on a phone.

Drag an object to change its position. Use its filing controls to change
where it is kept. A view change does not move the stored record to another
hub.

## Use windows

Speak, Meetings, Agents, Settings and other apps open in Desk windows.
Every window has the same parts: a title bar, a toolbar with its verbs, the
content, and a status bar with its state. Drag a desktop window by its title
bar. Use its edge or corner to resize it. Iconify a window to keep it in the
dock. Select its dock tile to return to it. Use **Window** to close, cycle,
snap, zoom or send a window to the back.

The Desk keeps the window layout in your browser. On a phone, **Back**
returns to the previous window.

## Ask about your work

1. Open **Ask AI** from Go, or press **⌘I**.
2. Use **+** beside **About** to select a meeting, note, drawer, project or
   person. With no selection, Ask is about your whole desk.
3. Enter your question, then press **Ask**.

You can also select **Ask about this** on a record. Its name appears in
About. On an engine that can use tools, the answer shows **Looked at**,
**Wrote** and **Prepared**. A prepared send waits for your **Send** press.
When Ask was opened from a note, **Add to note** keeps an answer in that note.

## Record a meeting

Use the recorder control to start or stop a meeting. The hub records the
meeting; this is separate from browser microphone input. Open Meetings to
read the transcript and results.
See [Meeting mode](MEETING_MODE_GUIDE.md) for microphone selection, system
audio and import.

You can drop a transcript or audio file on the desk to import it. Drop a
calendar screenshot to read events from it.

## Set preferences

Open **Settings** from the HoldSpeak menu, or press **⌃,**. The rail lists
**You**, **Speak**, **Meetings**, **Notices**, **Accounts**, **Agents**,
**Desk** and **This Mac**. Notices holds the Heartbeat (quiet hours, the daily
brief, notifications). Desk holds Wallpaper, sounds and motion. Accounts holds
connections, Calendar, Destinations and secrets. **HoldSpeak > Engines** has
the model and job assignments. Use Search to find a setting.

## Keys

| Key | Action |
| --- | --- |
| **⌃N**, **⌃T** | New Note |
| **⌃⇧N** | New Decision |
| **⌘I** | Ask |
| **⌘K** | Search |
| **⌃1** to **⌃5** | Today, Meetings, People, Agents, Speak |
| **⌃J** | Needs you |
| **⌃,** | Settings |
| **⌘⇧E** | Window > Overview: every open window at once |
| **⌘/** | Keyboard shortcuts |

The browser keeps some **⌘** keys. The menus show **⌃** alternatives for them.

## Troubleshooting

| Problem | Action |
| --- | --- |
| A window is missing | Check the dock and Window menu. |
| A verb is missing | Select the record the verb needs. |
| Ask cannot answer | Read the failure and check its engine. |
| The menus are hidden | Select Back to Desk, or press Escape. |

## See also

- [User Guide](USER_GUIDE.md)
- [Desk object model](DESK_OBJECT_MODEL.md)
- [Desk architecture](DESK_ARCHITECTURE.md)
- [Control modes](AUTHORITY.md)

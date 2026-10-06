# The Desk

The Desk is the HoldSpeak web app.
It holds your records and opens the tools you use to work with them.
The Chair shows current work. The Floor shows your records as objects.

## Start a task

1. Open the URL that `holdspeak` prints.
2. Use the Chair for current work, or open the Floor to arrange records.
3. Open the **Desk** menu to create a record.
4. Open the **Go** menu to open a tool.

On a new installation, the Desk first offers **Dictate one sentence**.
See [Getting Started](GETTING_STARTED.md) for that first capture.

## The Chair and the Floor

The Chair is the home screen. It has four windows:

| Window | Content |
| --- | --- |
| **Needs you** | Items that wait for you, ranked. |
| **Brief** | The current brief. |
| **The week** | Upcoming recordings and calendar events. |
| **Capture** | **Talk**, **Write a thought**, **Record meeting**, and **Schedule**. |

Close a Chair window to hide it. Open it again from **Window > Chair**.
See [The Arrival](USER_GUIDE.md#the-arrival) for the controls.

The Floor shows Meetings, Notes, Artifacts, Projects, and other records as objects.
Drag an object to move it. Open a Zone to see the records filed in it.
A coder session stays on the Floor even when you file other records.
The Floor has a spatial view and a list view.
With no saved choice, a compact screen with more than 16 objects opens the list view.

## Create and open work

Use the **Desk** menu to create a record.
It offers **New Note**, **Write a thought**, **New Decision**, **New Knowledge**, **New Agent**, **New Workflow**, **New Workbench**, **New Zone**, **New Thread**, and **New Project**.
**New Project** opens the Project setup window. See [Project Rooms](PROJECT_ROOMS.md).

Select an object, then use the **Object** menu.
It offers **Open**, **Get Info**, **Ask AI**, **Continue in thread**, **Edit**, **Rename**, **Duplicate**, **Move to Zone**, and **Delete**.
An unavailable verb stays visible and shows its reason.
The object kind decides which verbs apply.

## Arrange the Floor

- **Move to Zone** files an object in a Zone.
- **Arrange desk** resets the objects you moved to the automatic grid.
- **List view** and **Spatial view** switch the Floor view.
- **Hide the menus** starts Settle in. **Back to Desk** ends it.

Object positions are view preferences on this device.
The records stay on the hub.

## Use windows

Speak, Meetings, Agents, Settings, and other tools open in Desk windows.
Drag a window by its title bar. Resize it with a window edge or corner.
Iconify a window to keep it in the dock.
Select its dock entry to bring it back.

Use the **Window** menu for **Close window**, **Iconify**, **Cycle windows**, **Snap left**, **Snap right**, **Zoom**, and **To back**.
Use **Overview** to see all open windows.
On a phone, a window fills the screen.

The Desk saves the window layout in your browser.
An iconified window stays iconified when you return.

These addresses open the matching window:

| Address | Window |
| --- | --- |
| `/dictation` | Speak |
| `/history`, `/meetings` | Meetings |
| `/settings`, `/studio` | Settings |
| `/setup` | New Project |
| `/live` | Live meeting |
| `/activity` | Activity |
| `/commands` | Commands |
| `/cadence` | Rhythm |
| `/workbenches` | Workbenches |

Other addresses open the Desk. `/welcome` and `/presence` are separate pages.
See [Desk object model](DESK_OBJECT_MODEL.md) for the window and key reference.

## Record a meeting

Select **Record meeting** on the Chair, or the recorder control on the Floor.
The hub records the meeting. This is not browser microphone input.
Use the stop control to end the recording.
Then open the Meeting to read its transcript and results.
See [Meeting mode](MEETING_MODE_GUIDE.md) for microphone selection, system audio, and import.

You can also drop a transcript or audio file onto the Floor to import it.
Drop a calendar screenshot to read events from it.

## Use a Thread

1. Select **Desk > New Thread**.
2. Enter your request in the composer.
3. Type `@` to attach a record.
4. Select **Send**.

Routine tool calls stay collapsed under **Actions**.
Tool questions, approval requests, and failures stay visible.
The Thread stores sent messages on the hub.
Keep a reply when you want a Note or Artifact outside the conversation.
Use **Interview** mode for repeatable working context. See [Interview](INTERVIEW.md).
See [Threads](USER_GUIDE.md#threads) for all controls.

## Ask with selected context

Select objects on the Floor, then select **Ask AI** (**Command/Ctrl+I**).
The Ask uses the selected records as source context.
Check the result and its sources before you keep it.
A kept result becomes an Artifact with its lineage.

## Use speech input

The Thread composer and text fields use a microphone button.
Select it once to start and again to stop.
Voice typing in other apps uses the global hold-to-talk hotkey.
Browser microphone input goes to the hub for transcription.
A reply can deliver text to a live coder session under your control mode.
See [Coder steering](USER_GUIDE.md#steer-a-session-from-the-desk).

## Change the environment

Open **Places** to select a scene or Quiet Desk.
See [Places](ENVIRONMENTS.md).

## Troubleshooting

| Problem | Action |
| --- | --- |
| A window is missing | Check the dock and the **Window** menu. |
| A tool cannot run | Read its reason. Check the connection, the selection, or the model assignment. |
| A Thread send fails | Read the failure. The composer keeps your text. |
| The menus are hidden | Select **Back to Desk**, or press **Escape**. |
| A result is not in Notes | Open the Thread. Keep the reply as a Note. |

## See also

- [User Guide](USER_GUIDE.md)
- [Desk object model](DESK_OBJECT_MODEL.md): object kinds, verbs, keys, window geometry.
- [Desk architecture](DESK_ARCHITECTURE.md): how the web app is built.
- [Interview](INTERVIEW.md)
- [Places](ENVIRONMENTS.md)
- [Control modes](AUTHORITY.md)

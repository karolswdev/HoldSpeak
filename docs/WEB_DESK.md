# The Desk

The Desk holds your records and opens the tools you use to work with them.
Use the arrival for current work and the Floor for spatial organization.

## Start a task

1. Open the URL printed by `holdspeak`.
2. Select an item on the arrival, or select **Floor**.
3. Open the **Desk** menu to create a record.
4. Open the **Go** menu to select a tool.

On a new installation, the Desk first offers **Dictate one sentence**.
See [Getting Started](GETTING_STARTED.md) for that first capture.

## The arrival and Floor

The **arrival** is the Desk's home screen.
It shows items that need you, unfinished Thoughts, a brief, and recent Meetings when those records exist.
Its capture bar provides **Talk**, **Develop a thought**, and **Record meeting**.
See [The Arrival](USER_GUIDE.md#the-arrival) for the individual controls.

The **Floor** shows Meetings, Notes, Artifacts, Projects, and other records as objects.
You can open these objects or file durable work in Zones.
Changing between Chair and Floor preserves an open Thread and its current draft.

## Create and open work

Use the **Desk** menu for **New Note**, **New Decision**, **New Thread**, and other creation controls.
**New Project** opens the Project setup surface.
The Floor's context menu also exposes creation and launch controls.

Select an object to work with it.
Use the **Object** menu for applicable operations such as **Open**, **Rename**, **Move to Zone**, or **Continue in thread**.
An unavailable operation shows its reason.
A live Coder session can have different controls from a saved Note.

## File and arrange objects

Drag an object to change its position.
Use **Move to Zone** or the supported drag target to file an object in a Zone.
Open a Zone to work with its contents.

Object positions are view preferences on this device.
The underlying records remain on the hub.
Use **Arrange desk** when you want the automatic arrangement.

## Use windows

Speak, Meetings, Settings, and other tools open in Desk windows.
You can drag a window by its title bar or resize it with its handle.
Minimize it to the dock when you want to keep it available.
Select its dock entry to return to it.

The **Window** menu provides focus, snap, and maximize controls with their shortcuts.
On phones, windows use sheets fitted to the available space.
Saved window arrangement and saved product records are separate kinds of state.

Existing addresses open the corresponding Desk surface:

| Address | Surface |
| --- | --- |
| `/dictation` | Speak |
| `/history` | Meetings |
| `/studio` | Studio |
| `/settings` | Settings |
| `/setup` | Setup diagnostics and recovery |

## Record a meeting

Use **Record meeting** or the Floor recorder control to start hub meeting capture.
This uses the hub recorder. It is separate from microphone input in a browser text field.
The recorder state also reflects a meeting started from another supported surface.

Use the visible stop control to end recording.
Then open the Meeting to inspect its transcript and results.
See [Meeting mode](MEETING_MODE_GUIDE.md) for microphone selection, system audio, and import.

## Use a Thread

1. Select **Desk > New Thread**.
2. Enter your request in the composer.
3. Attach relevant records with `@` if required.
4. Select **Send**.

Your prompt appears while the request starts.
Routine tool calls remain collapsed under **Actions**, including while the reply streams.
Tool questions, approval requests, and failures remain visible.
The Thread stores sent messages on the hub.
Keep a reply separately when you want a Note or Artifact outside the conversation.

Use **Interview** mode to develop repeatable working context.
See [Interview](INTERVIEW.md) for its sections, saved facts, and suggestions.
See [Threads](USER_GUIDE.md#threads) for all conversation controls.

## Ask with selected context

Select the relevant Floor objects and use **Ask AI**.
The supported selection tools include the selection rectangle and modifier-click selection.
An Ask can use selected records as source context.

Inspect the result and its sources before you keep it.
A kept result becomes an Artifact with its lineage.
The Ask result and the Thread conversation have different persistence rules.
Keeping an Artifact is separate from saving Thread messages.

## Use speech input

Microphone controls differ by surface.
The Thread composer uses click-to-toggle microphone input.
Voice typing uses the configured global hold-to-talk hotkey.
Follow the control shown on the current surface.

Browser microphone input sends audio to the configured hub for transcription.
A Coder reply can then deliver the resulting text to a live session under the applicable authority.
See [Coder steering](USER_GUIDE.md#steer-a-session-from-the-desk) before you deliver session input.

## Change the environment

Open **Places** to select one of eight animated scenes or Quiet Desk.
You can save favorites, pause animation, and enable optional room sound.
Use **Settle in** to reduce navigation controls around your work.
See [Places](ENVIRONMENTS.md) for shortcuts and persistence details.

## Troubleshooting

| Problem | Action |
| --- | --- |
| A window seems absent | Check its dock entry and the **Window** menu. |
| A tool cannot run | Read its reason. Check the connection, required selection, or model assignment. |
| A Thread send fails | Read the failure before retrying. The composer retains failed text. |
| Navigation is reduced | Exit Settle in with **Back to Desk** or **Escape**. |
| A result is absent from Notes | Open the Thread. Use Keep on the reply if you need a separate Note. |

## See also

- [User Guide](USER_GUIDE.md): individual features and advanced controls.
- [Interview](INTERVIEW.md): repeatable context and manual drafts.
- [Places](ENVIRONMENTS.md): scenes, favorites, and Settle in.
- [Control modes](AUTHORITY.md): authority for tool effects and Coder input.

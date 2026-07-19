# The Desk

The Desk is HoldSpeak's operating surface. Launch `holdspeak` and open `/`
to work with Meetings, Notes, Knowledge, Agents, Sequences, Workflows,
Artifacts, and live Coder sessions. Zones provide placement for durable
work. The world itself renders on a WebGL stage; every product surface
(Dictation, Meetings, Settings, Workbench, and the rest) opens as a window
on the Desk, so nothing you do here navigates away.

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/screenshots/desk.png" alt="The HoldSpeak Desk: pixel-art objects floating on a warm dark stage; a Zone tray holding a filed Meeting; Coder session avatars on a right-edge rail; a record orb bottom-center; the compact HoldSpeak menu and an egress badge top-left; Create controls top-right." width="760">
</p>

It serves at `/`. On a fresh install the first-run guard sends you to the
`/welcome` wizard instead, and a hard-blocked setup goes to `/setup`;
everyone else arrives here. (`/desk`, the old address, redirects home.)

## What you see

Desk items use distinct visual forms:

- **meetings** are cassette tapes,
- **notes** are notepads,
- **Knowledge** collections are crystals,
- **Agents** and **Coder sessions** are characters,
- **Sequences** and **Workflows** are cartridges,
- **artifacts** are typed pages, each carrying its lineage.

A freshly created object arrives at the center of the stage with a short
glow and a NEW mark, then settles.

## The chrome

Primary controls stay compact:

- **Top left**: the HoldSpeak mark opens the menu; each room (Dictation,
  Meetings, Studio, Settings) opens as a window in place. Beside it, the
  hub dot (green when connected) and the current data-boundary badge.
- **Top right**: **Dictate**, **Record**, and one **Create** menu for Note,
  Zone, Knowledge, Agent, and Workflow.
- **Tool shelf**: advanced Desk tools and Runs on destinations.
- **Right edge**: the Agent rail.

## Windows, the dock, and tiles

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/screenshots/desk-windows.png" alt="Two windows on the Desk: the Dictation cockpit and the Meetings memory, cascaded over floating meeting cassettes and workflow cartridges, with dock chips bottom left." width="760">
</p>

Every surface is a window with one chrome: drag it by its head, resize it
by the corner grip, minimize it to the dock, maximize it to the full
stage, or close it. Releasing a drag at a screen edge snaps a half or
quarter tile. The dock (bottom left) lists every open window; a dimmed
chip is parked and a tap brings it back; the ⟲ chip resets the layout.
`Ctrl+\`` cycles windows in most-recently-used order. Your arrangement
persists on this device. On phones a window presents as a bottom sheet.

Old page addresses (`/dictation`, `/history`, `/settings`, ...) are deep
links: each lands on the Desk with the matching window open, at the same
scope the link named.

## Create, in place

Choose **Create**, then select Note, Zone, Knowledge, Agent, or Workflow.
The new item opens in context. Agent and Workflow editors expose their Runs
on destination and Knowledge only when those settings are relevant.

## Open, in place

Select an object to open its contextual panel. A Meeting shows
its summary, action items, and artifacts; tapping an artifact opens it in
the same panel. An Artifact's lineage names its source and capability.
Focused actions such as **Review meeting** and **Edit Workflow** enter the
relevant workroom and retain the Desk subject for return.

## File and dive

A Zone is a findable placement for Desk items:

- **File**: drag an object onto a zone (the tray lifts as you hover), or
  use **Move to…** in its panel. Filing again from the panel un-files it.
- **Dive**: click a zone and the camera moves in; only its members remain
  on stage. **All** surfaces back out.
- **Rename**: click a zone's title and type. A new zone arrives with its
  name field already focused.

## Record from the orb

Press the orb and the hub starts recording a meeting (the same recorder
the Live meeting window drives; never the browser's microphone). While
recording, the orb pulses with the elapsed time; a meeting started
anywhere else shows here too, marked "live elsewhere", and the orb can
only stop it. When the recording ends, the finished meeting lands on the
stage as an object.

## Converse from the rail

The right-edge rail holds Agents, each with its Runs on status. Select one
to open its **conversation**, a docked thread rather than a one-shot prompt.
Turns accumulate, the
thread survives a reload (it lives on this device; Agents sync, threads
stay yours), and **Clear** empties it when you want a fresh start.

Each reply names where that turn ran. **Keep as Artifact** stores the Result
as an Artifact on the Desk with lineage naming the Agent. Nothing is
stored until you save it.

Below the Agents, the rail lists available models from each Runs on
destination. Select one to open a conversation pinned to that model. If the
model is unavailable, the run fails before execution and lists available
alternatives.

## Ground this ask

Both composers (the Ask AI panel and any conversation) carry an attach
control: **Ground this ask**. Open it and pick meetings; each one
expands to its digest, its transcript, and every artifact it produced,
each independently toggleable. A gauge prices the selection against the
model's window from the records' real sizes, and a selection past the
window refuses before anything runs.

The run sends references, not copies: the hub reads the selected records
from its own store and answers from them. A kept answer names the
meetings and artifacts that grounded it, and an unknown reference
refuses with its id instead of silently guessing. In a conversation the
selection sticks, so every following turn stays grounded on the same
records.

## Rope things together and Ask AI

Contextual Ask needs no saved Agent. Drag on the
empty desk and a rope follows your pointer; everything inside it is
selected (shift-click or cmd-click ropes objects one at a time). A bar
rises with the count and one action: **Ask AI**.

The composer docks at the edge with the desk still alive behind it. Pick
a lens (Summarize, Action items, Risks, Decisions, Draft email) or speak
your own instruction with the mic, choose where it runs (the hub's
default or another Runs on destination), and Ask. The hub reads the selected
objects from its own store (a note's body, an artifact's text, a
meeting's summary and actions) and runs your instruction over exactly
that pile.

The answer prints as a card wearing an honest badge: which model ran it
and, for an endpoint run, which host it went to. This run, not the app
default. Then you judge it:

- **Keep** makes it a real artifact on the stage, and its lineage names
  every object it read plus the exact instruction you gave.
- **Bin** closes it. Nothing is stored.

A kept ask syncs like any other artifact, so the card you keep here
shows the same lineage on the iPad, and one kept there lands here.

## Talk, don't type

Every text input on the Desk carries a mic: hold it, speak, release, and
the words land in the field. The browser sends audio to the configured hub;
the applicable Runs on and boundary labels state where transcription occurs.

A waiting Coder session takes speech too: its panel shows the Coder's
question, and **Hold to answer** sends your spoken reply straight into
the session. **Use the hotkey** instead selects it as your dictation
target for the held-key flow.

## The preview card

If you turn on **Preview before it types** (Settings, Voice), every
finished dictation appears on a card above the orb instead of typing:
**Type it** commits, **Discard** or Escape drops it. The card follows you
to every room, not just the desk.

## Arrange the desk

Drag any object to move it. The layout is stored on this device
and never syncs; **Tidy** snaps everything back to the automatic layout.

## Qlippy

Qlippy is an optional visual presence for contextual attention. It is off by
default and uses the same action, authority, and Receipt copy as other Desk
surfaces.

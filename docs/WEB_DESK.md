# The Desk

The Desk is HoldSpeak's front door. Launch `holdspeak`, open the browser,
and you are standing in it: everything the product knows about, living as
objects in one warm spatial world. Meetings, notes, knowledge bases,
agents, chains, workflows, artifacts, and live coder sessions float on the
stage; directories are shelf-zones; the things you do daily happen ON the
stage, in place.

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/screenshots/desk.png" alt="The HoldSpeak Desk: pixel-art objects floating on a warm dark stage; a zone tray holding a filed meeting; agent avatars on a right-edge rail; a record orb bottom-center; the compact HoldSpeak menu and an egress badge top-left; create chips top-right." width="760">
</p>

It serves at `/`. On a fresh install the first-run guard sends you to the
`/welcome` wizard instead, and a hard-blocked setup goes to `/setup`;
everyone else arrives here. (`/desk`, the old address, redirects home.)

## What you see

Every primitive is a pixel-art object with a soft shadow and a gentle bob:

- **meetings** are cassette tapes,
- **notes** are notepads,
- **knowledge bases** are crystals,
- **recipes** (your saved AI personas) and **coder sessions** are little
  characters,
- **chains** and **workflows** are cartridges,
- **artifacts** are typed pages, each carrying its lineage.

A freshly created object arrives at the center of the stage with a short
glow and a NEW mark, then settles.

## The chrome

No header, no sidebar. A compact cluster floats in each corner:

- **Top left**: the HoldSpeak mark opens the menu to the rooms
  (Dictation, Meetings, Studio, Settings); beside it, the hub dot (green
  when connected) and the **egress badge**, the one trust answer: local,
  or exactly which endpoint can be reached.
- **Top right**: the create chips (**+ Note**, **+ KB**, **+ Recipe**,
  **+ Zone**, **+ Workflow**), **Tidy** (only when you have arranged
  things), and refresh.
- **Bottom center**: the **Record orb**.
- **Right edge**: the **agent rail**.

## Create, in place

A create chip makes the thing immediately; the object materializes at
center and its editor opens beside it on the stage, with the world dimmed
around it. Notes take a title, markdown body, and tags; recipes show the
essentials (avatar, name, role, system prompt) with **More** expanding
the advanced fields (template, tools, knowledge base, and which runtime
profile it runs on) in the same card. Everything autosaves as you type;
Escape or a click outside settles the object back. There are no dialog
windows on the desk.

## Open, in place

Tap any object and it opens where it is: a panel slides out with the
object's content while the world stays alive behind it. A meeting shows
its summary, action items, and artifacts; tapping an artifact opens it in
the same panel (the back arrow returns). An artifact's lineage chips name
where it came from and which capability made it. **Open full** in the
panel header is the one navigation on the desk (a meeting's full archive
entry at `/history`).

## File and dive

A directory is a shelf-zone with a stable tint and thumbnails of what it
holds:

- **File**: drag an object onto a zone (the tray lifts as you hover), or
  use **Move to…** in its panel. Filing again from the panel un-files it.
- **Dive**: click a zone and the camera moves in; only its members remain
  on stage. **All** surfaces back out.
- **Rename**: click a zone's title and type. A new zone arrives with its
  name field already focused.

## Record from the orb

Press the orb and the hub starts recording a meeting (the same recorder
the `/live` dashboard drives; never the browser's microphone). While
recording, the orb pulses with the elapsed time; a meeting started
anywhere else shows here too, marked "live elsewhere", and the orb can
only stop it. When the recording ends, the finished meeting lands on the
stage as an object.

## Converse from the rail

The right-edge rail holds your recipes, each wearing a dot for where it
runs (green on device, blue endpoint). Tap one and its **conversation**
opens: a docked thread, not a one-shot prompt. Turns accumulate, the
thread survives a reload (it lives on this device; recipes sync, threads
stay yours), and **Clear** empties it when you want a fresh start.

Each reply wears a badge for where that turn actually ran, and any reply
has **Save to desk**: the answer becomes a real artifact on the stage,
wearing the NEW mark, with a lineage chip naming the recipe. Nothing is
stored until you save it.

Below the recipes, the rail lists **every model the hub can run**: its
own engine and each runtime profile's model. Tap one and a chat opens
pinned to that model, through the same conversation surface. Ask a model
the hub cannot run and it refuses, naming what it can.

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

The desk's signature move needs no saved recipe at all. Drag on the
empty desk and a rope follows your pointer; everything inside it is
selected (shift-click or cmd-click ropes objects one at a time). A bar
rises with the count and one action: **Ask AI**.

The composer docks at the edge with the desk still alive behind it. Pick
a lens (Summarize, Action items, Risks, Decisions, Draft email) or speak
your own instruction with the mic, choose where it runs (the hub's
default, or any runtime profile), and Ask. The hub reads the roped
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

Every text input on the desk carries a mic: hold it, speak, release, and
the words land in the field. Capture happens in your browser; the
transcription is the hub's own local Whisper (nothing leaves, nothing is
stored). The rail's ask, the note editor, and the zone rename all take
speech.

A waiting coder session takes speech too: its panel shows the agent's
question, and **Hold to answer** sends your spoken reply straight into
the session. **Use the hotkey** instead selects it as your dictation
target for the held-key flow.

## The preview card

If you turn on **Preview before it types** (Settings, Voice), every
finished dictation appears on a card above the orb instead of typing:
**Type it** commits, **Discard** or Escape drops it. The card follows you
to every room, not just the desk.

## Arrange the desk

Drag any object to move it. The layout is stored locally in this browser
and never syncs; **Tidy** snaps everything back to the automatic layout.

## Qlippy

If you turn the mascot on in **Settings**, Qlippy keeps you company in
the corner. Off by default.

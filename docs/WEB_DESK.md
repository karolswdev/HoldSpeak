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
- **agents** and **coder sessions** are little characters,
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
- **Top right**: the create chips (**+ Note**, **+ KB**, **+ Agent**,
  **+ Zone**), **Tidy** (only when you have arranged things), and
  refresh.
- **Bottom center**: the **Record orb**.
- **Right edge**: the **agent rail**.

## Create, in place

A create chip makes the thing immediately; the object materializes at
center and its editor opens beside it on the stage, with the world dimmed
around it. Notes take a title, markdown body, and tags; agents show the
essentials with **More** expanding the advanced fields in the same card.
Everything autosaves as you type; Escape or a click outside settles the
object back. There are no dialog windows on the desk.

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

## Ask from the rail

The right-edge rail holds your agent personas, each wearing a dot for
where it runs (green on device, blue endpoint). Tap one, type an ask, and
run it. The answer comes back in place with a copy button, and it also
**persists as an artifact on the stage**, wearing the NEW mark, with a
lineage chip naming the agent. File it, reopen it, or copy it like
anything else.

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

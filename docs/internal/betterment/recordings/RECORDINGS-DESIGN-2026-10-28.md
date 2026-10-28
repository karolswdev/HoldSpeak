# Recordings: record a session from the dock, watch it on the iPhone

Status: design and build, 2026-10-28, lane RECORD. Canvas:
`docs/internal/betterment/canvases/recordings-2026-10-28.html`. The owner
pre-approved the recommended direction ("go with suggestions").

## 1. The job

The owner, 2026-10-28: "next to feedback, a record functionality, toggle-able
system-wide, maybe as an additional icon on the dock to be able to record my
sessions; optimize this process server-side so we generate a really simple
video, e.g., one I could easily download via your tailscale to my iPhone via a
link".

He presses the screen-record tile on the dock, works, presses it again. A short
while later a Note on his desk carries two links (the Tailscale one first, then
127.0.0.1). He taps the link on his iPhone over Tailscale; Safari plays the
video and "Save Video" puts it in Photos. No account, no cloud. Nothing leaves
the device except over his tailnet, and only when he opens the link.

## 2. The direction (recommended, built)

**Capture in the browser, encode on the hub.**

1. **The tile.** A dock tile after the meeting Record key: a flat D screen with
   a red dot (`system/48/dock-screen-record.png`). Press: the browser's own
   picker opens (`getDisplayMedia`, `preferCurrentTab`, "this tab" first in
   Chromium). While it records the tile wears the red ring of the Record key
   and its hover label says `Stop screen recording · 3:12`. ⌃⇧R does the same
   from any view. The meeting Record key stays the meeting key: two red keys
   with two jobs would be one too many, so the screen tile is a screen, and
   only its live ring is red.
2. **The lamp.** While a recording runs, the menu bar's right strip carries
   `● Recording 3:12` and `Stop`, beside the mic lamp (the MicLamp species).
   A second view of the same desk gets the `recording_state` frame and shows
   `● Recording on another view` with the same Stop.
3. **The stream.** `MediaRecorder` (`video/webm;codecs=vp9`, 2.5 Mbit/s wide,
   1.2 Mbit/s at 393, 15 frames a second) posts a chunk each 5 s to
   `POST /api/recordings/{id}/chunks` with the hub token. The hub appends to
   `~/.local/share/holdspeak/recordings/<id>/in.webm`. A voice switch (off by
   default, in the Recordings toolbar) adds the microphone track.
4. **The end.** Stop, the browser's own "Stop sharing", the tab closing (a
   `pagehide` stop with `keepalive`) or 2 minutes with no chunk (the hub's
   stale close) ends the capture. The hub encodes, one recording at a time, in
   a daemon thread off the loop:
   `ffmpeg -i in.webm -vf "scale='min(1280,iw)':-2" -c:v libx264 -preset veryfast -crf 28 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 64k out.mp4`
   and a poster at 2 s. H.264, AAC and faststart: iPhone Safari plays it
   inline and saves it. The row shows `Encoding 42 %` from `-progress pipe:1`.
   No ffmpeg: the row says `Kept as webm · brew install ffmpeg for an iPhone
   video` and the webm is the video.
5. **The link.** `GET /r/<id>/<share token>/<slug>.mp4`, with Range (Safari
   asks for byte ranges). The share token is in the path, so the link opens on
   the phone without the hub token. `Stop sharing` revokes it (a new Share
   makes a new token). A parked recording answers 404. Both links show: the
   Tailscale URL when Tailscale Serve proxies to this hub (the hub reads
   `tailscale serve status --json` once a minute), and the 127.0.0.1 URL.
6. **Where it lives.** A **Recordings** window (Go ▸ Work ▸ Recordings; the
   tile's right button opens it): the window grammar (toolbar, dense list,
   status bar). A row: the poster, `Recording · Tue 28 Oct 17:40`, length,
   size, the state as a dot and a word. Open a row: the video in a well (a
   `<video>`), the two links with Copy, Open note, Stop sharing, Park. A
   failed row carries Retry. On ready the hub writes the Note
   `Recording · Tue 28 Oct 17:40 · 12 min` with both links (filed to the
   project in front when the recording started, else unfiled).
7. **Keep and size.** A recording older than 30 days is parked
   (`recordings/_parked/<id>/`), never deleted. Settings ▸ Desk ▸ Recordings:
   `Keep 30 days · 1.2 GB used` and Open folder.
8. **The switch.** `HOLDSPEAK_RECORDINGS=off` (rig hubs): no ffmpeg run, no
   Tailscale read, no keep sweep. The routes still answer.

## 3. The alternative weighed: capture on the hub (ffmpeg avfoundation)

The hub records the Mac's screen itself (`ffmpeg -f avfoundation -i 1`).

| | Browser capture (built) | Hub capture |
|---|---|---|
| Consent | The browser's own picker, each time | A macOS Screen Recording grant for the hub's Python, once, for every later run |
| What it records | The desk tab (or what he picks) | The whole screen: every other app, mail, the password manager |
| From the phone view | Yes (Safari 17 has getDisplayMedia on Mac only; the iPhone view shows the lamp and Stop) | No |
| New machine state | None | A permission prompt and a device read |
| Size | VP9 webm in, H.264 out | The same encode |

Not chosen: a hub that can film the whole screen with one old grant is more
than he asked for, and it records what is not the desk.

A second alternative, mp4 straight from the browser (`MediaRecorder` mp4 in
Chromium 126+), is not chosen: a fragmented mp4 has no faststart and no size
control, and "Save Video" on the iPhone is not reliable with it. The hub
encode makes one known-good file.

## 4. The contract

### Store

No table: each recording is a folder with `meta.json` (id, title, state
`recording | encoding | ready | failed`, started_at, ended_at, bytes_in,
bytes_out, width, height, duration_s, share_token, voice, project_id,
note_ref, progress, error, encoder `mp4 | webm`). The folder is the record;
parking moves it whole. (The brief named a `recordings` table; a table and a
folder would say the same thing twice, and the owner's ruling keeps
migrations minimal.)

### REST (`holdspeak/web/routes/recordings.py`)

| Method | Path | What |
|---|---|---|
| GET | `/api/recordings` | rows, newest first, `usage` (bytes, keep days), `links` (tailnet and local bases), `encoder` (ffmpeg or none) |
| POST | `/api/recordings` | start: `{width, height, voice, project_id?}` → the row |
| POST | `/api/recordings/{id}/chunks` | append one chunk (raw body); quiet (no `desk_changed`) |
| POST | `/api/recordings/{id}/stop` | end the capture; encoding starts |
| POST | `/api/recordings/{id}/retry` | encode a failed one again |
| POST | `/api/recordings/{id}/share` | a new share token (Share again) |
| POST | `/api/recordings/{id}/unshare` | Stop sharing: the token is gone |
| POST | `/api/recordings/{id}/park` | move to `_parked/` |
| POST | `/api/recordings/folder/open` | open the folder in Finder |
| GET | `/api/recordings/{id}/video` | the desk's Play (owner token) |
| GET | `/api/recordings/{id}/poster` | the poster frame (owner token) |
| GET | `/r/{id}/{token}/{name}` | the shared link: no hub token, Range |

### Frame

`recording_state` `{reason: started|chunk|stopped|encoding|progress|ready|failed|parked|shared, recording}`:
the Recordings window replaces the row; the dock tile and the menu-bar lamp of
every view read the live one.

## 5. What is not in this slice (named, not built)

- A **QR** for the link: the desk has no QR code today (no library in web or
  hub). The phone path is the desk on the phone: the Note's link is one tap.
- A **Needs you** row for a failed encode: the Needs-you membership is a
  source family with coverage records; a new source is its own change. The
  failed row and its Retry are in the Recordings window, and the tile wears
  the amber dot.
- A **send route** (`POST /api/recordings/{id}/send`): the Note carries the
  links, and the Note's Send already prepares a send through the channel (his
  press sends). A second send path for the same words is one interface too
  many (Tenet 3).

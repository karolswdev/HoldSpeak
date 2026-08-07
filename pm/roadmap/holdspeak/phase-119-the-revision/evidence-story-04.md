# Evidence - HS-119-04

- **Story:** HS-119-04 - The walk
- **Status:** done
- **Date:** 2026-08-05

## Walk results

### Screenshot walk — 1440x900 (desktop)

1. **The desk** — PASS. PixiJS diorama renders: zones (ADRs,
   Decisions, Inbox, Meetings, Reference, Rules), workbenches
   (seeded "Workbench" with resolver, existing user workbenches),
   meetings, notes, agents. Menu bar shows LLM endpoint connection
   to 192.168.1.43:8080. Bottom nav: Speak, Meetings, Agents,
   Settings. Screenshot: `assets/hs-119-04/01-desk-desktop-1440.png`

2. **Presence** — PASS. Runtime bus connected. WebSocket ping/pong
   works. Duration frame received on connect. No "RECONNECTING"
   freeze — the hub is live and responsive.

### Screenshot walk — 393x852 (mobile)

1. **The desk** — PASS. Mobile viewport renders correctly. Zones,
   notes, meetings listed. Bottom nav tappable. "ITEMS 39 · ZONES 6"
   census line is honest. Screenshot:
   `assets/hs-119-04/03-desk-mobile-393.png`

### API verification

- **Profiles**: 7 total (5 seeded + this_machine + existing homelab).
  Cloud profiles (OpenAI, Anthropic) have requires_key=true. Local
  profiles have requires_key=false.
- **Directories**: 6 zones (ADRs, Decisions, Inbox, Meetings,
  Reference, Rules).
- **Workbenches**: seeded "Workbench" with
  resolver_profile_id=hs-seed-local-4b-resolver confirmed.

### WebSocket verification

- **Runtime bus `/ws`**: connected via subprotocol holdspeak.v1,
  received initial duration frame `{"type":"duration","data":"00:00"}`.
  Ping/pong works.
- **Streaming endpoint `/ws/dictation/stream`**: connected, sent
  silence + end signal, received `{"type":"final","text":""}`.
  Floor claim/release lifecycle confirmed.

### What requires real-device sitting

The following proofs need a real microphone and real Whisper model
running, which headless Playwright cannot exercise:

- Click-to-toggle mic with streaming transcription (live audio)
- Voice drawer resolution with spoken zone references
- Correction cycle (speak → correct → re-speak → learned)
- Meeting recorder start/stop/transcript
- Dictation hotkey via system-level capture

These are deferred to the owner's real-device sitting per the
standing "verify on the real device" feedback.

## Proof

### Captured run — 2026-08-06T04:55:36Z

- **Command:** `ls -la pm/roadmap/holdspeak/phase-119-the-revision/assets/hs-119-04/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8ccba8010929e91755cbabd6b96b4784aa1a165d

```text
total 4144
drwxr-xr-x  7 karol  staff     224 Aug  5 22:54 .
drwxr-xr-x  3 karol  staff      96 Aug  5 22:52 ..
-rw-r--r--  1 karol  staff  514905 Aug  5 22:53 01-desk-desktop-1440.png
-rw-r--r--  1 karol  staff  514835 Aug  5 22:54 02-presence-desktop-1440.png
-rw-r--r--  1 karol  staff   54783 Aug  5 22:54 03-desk-mobile-393.png
-rw-r--r--  1 karol  staff  514835 Aug  5 22:54 04-speak-desktop-1440.png
-rw-r--r--  1 karol  staff  514835 Aug  5 22:54 05-settings-desktop-1440.png
```

# Line: HoldSpeak's own phone line

Status: design for the owner, 2026-10-29. Lane LINE-1 (spike and design).
Branch `lane/line-spike-20261029`. No product code in this lane. The spike
scripts are throwaway and are not in the tree; LINE-2 writes the real code
and its tests from this document.

## 1. The job

The owner, 2026-10-29, on the two ways to give Calls a line: "I'm choosing
the second". The second way is a native line: HoldSpeak runs its own SIP
phone on a stack with a permissive licence, the hub drives it, the speech is
our own, and it can run on the home box `karol` beside qwen. HoldSpeak stays
Apache-2.0.

Done when: a call to the Line reaches the Calls runner
(`holdspeak/calls/runner.py`) with no change to the runner; the Line runs on
this Mac or on `karol`; Settings ▸ Calls ▸ Line says where it runs and its
state; and nothing AGPL or GPL is in the tree or in a HoldSpeak process.

## 2. The decision: baresip at arm's length, our module, our speech

| Part | Choice | Licence (read 2026-10-29) |
|---|---|---|
| SIP and RTP | **baresip 4.12.0** as a supervised child process | BSD-3-Clause (`LICENSE` in the Homebrew keg `/opt/homebrew/Cellar/baresip/4.12.0/LICENSE`: "Copyright (C) 2020 - 2026, Baresip Foundation … Redistribution and use … are permitted") |
| Its toolkit | **libre 4.12.0** (`baresip/re`; librem is part of libre since v3) | BSD-3-Clause (`/opt/homebrew/Cellar/libre/4.12.0/LICENSE`) |
| Control | baresip's `ctrl_tcp` module: netstring JSON commands, responses and events on `127.0.0.1` | in baresip (BSD-3) |
| Call audio in and out | **`aupipe`**: a baresip audio source and player over two unix sockets, ours (~250 lines of C, Apache-2.0, uses only the public module API) | ours |
| Speech in | **Parakeet TDT 0.6B v2 (int8 ONNX)** through `onnx-asr` 0.12.0 on `onnxruntime` | code MIT (`onnx-asr`, `onnxruntime`); weights CC-BY-4.0 (`istupakov/parakeet-tdt-0.6b-v2-onnx`, from NVIDIA's model): attribution in `THIRD_PARTY_NOTICES.md` |
| Speech out | **Kyutai Pocket TTS** `pocket-tts` 4.0.1, the ungated weights `kyutai/pocket-tts-without-voice-cloning` | code MIT; weights CC-BY-4.0: attribution |
| Codecs we load | `g711` (PCMU, PCMA), `opus` (where the build has it), `l16` | baresip modules (BSD-3); libopus is BSD-3 |
| Other modules we load | `account`, `menu` (it owns `dial`, `accept`, `hangup`), `ctrl_tcp`, `auresamp`; for a carrier: `stun`, `ice`, `turn`, `srtp` | baresip modules (BSD-3) |

What baresip links (measured): on the Mac `libbaresip`, `libre`, the
system (`otool -L /opt/homebrew/bin/baresip`); the bottle's SBOM names only
libre, OpenSSL 4.0.3 (Apache-2.0) and ca-certificates. On `karol` (our own
build): `libre`, `libssl.so.3`/`libcrypto.so.3` (Apache-2.0), `libz`,
`libopus`, glibc (`ldd`). No GPL.

**Out, by name:** PJSIP, pjsua2, linphone, sipsimple (GPL); ai-phone
(AGPL-3.0, §2 of the Calls design); the baresip modules `gzrtp` (GNU ZRTP)
and any module that links a GPL library: we never build or load them. The
licence rule is checked by a list of the modules we load, not by trust.

Arm's length and in tree are both lawful here. baresip runs as a separate
process (like the CLI engines), and it is BSD, so we may also ship our own
module and a build script in the tree. We do not vendor baresip's source.

### Two licence findings outside this lane (flag for the owner)

The spike found GPL code that HoldSpeak loads today. Neither is the Line's;
both need a ruling and a small lane.

1. **The `tts` extra (Kokoro) loads GPL-3.0 code.** `kokoro-onnx` 0.6.1
   imports `phonemizer` (GPL-3.0-or-later) and `espeakng_loader`, which
   ships `libespeak-ng.1.52.0.dylib` (espeak-ng, GPL-3.0-or-later), at
   import time (`kokoro_onnx/tokenizer.py`, lines 8–10). With the extra in,
   that code is in the hub process (`holdspeak/web/routes/tts.py`).
   Every English G2P we checked for Kokoro routes through espeak-ng: misaki's
   `en` extra needs `phonemizer-fork` (GPL-3.0+) and `espeakng-loader`;
   `piper-tts` 1.8.0 is GPL-3.0-or-later; `kittentts` needs `phonemizer`.
   Pocket TTS has no phonemizer (it reads text with sentencepiece); a grep of
   its package finds no `phonemizer` or `espeak`.
2. **`faster-whisper` loads GPL-2.0 binaries on Linux.** `faster_whisper`
   imports PyAV at import time. The PyAV 19.0.2 wheel bundles `libx264` and
   `libx265` (GPL-2.0-or-later); on `karol`, `import faster_whisper` maps both
   into the process (`/proc/self/maps`). HoldSpeak's Linux STT backend
   (`holdspeak/transcribe.py`, `faster-whisper`) has the same exposure. The
   bundled FFmpeg itself reports "LGPL version 3 or later"
   (`avcodec_license()`). The spike kept PyAV out with a stub module, because
   we never decode files; the Line does not use faster-whisper at all.

## 3. The spike: what was measured

Two baresip instances, one "the Line" and one "the caller", each with
`aupipe`, driven by one Python harness through `ctrl_tcp`. The caller plays a
4.08 s utterance (macOS `say`, 16 kHz: "Prepare the one on one with Priya,
and nudge Tomás about the runbook."). Mouth to ear is the time from our PCM
going into one end's socket to the same sound coming out of the other end's
socket, so it holds both modules, packetization, the jitter buffer and the
codec. Each number is the median of 6 tones, or 3 utterances.

Machines: this Mac (Apple Silicon, macOS 26) and `karol` (Ubuntu 24.04.4,
i9-12900K, 24 threads, 62 GB, RTX 4080 SUPER with 15.6 of 16 GB held by the
llama.cpp service; the Line uses the CPU only).

| Measure | Mac, PCMU | karol, PCMU | karol, opus 48 kHz | Mac → karol over Tailscale, PCMU |
|---|---|---|---|---|
| Dial to established | 44–50 ms | 2.1–2.3 ms | 2.2 ms | 133 ms (adaptive buffers) / 219 ms (fixed) |
| Mouth to ear, one way | 80–82 ms (99 ms once) | 61–62 ms | 67 ms | about 160–190 ms (half of the echo round trip below) |
| Echo round trip (caller → Line → back to caller) | | | | 375 ms adaptive jitter buffer; **324 ms** fixed 40–80 ms; `ping` 88 ms avg |
| End of speech → end-of-speech detected (300 ms rule) | 370–375 ms | 351–391 ms | 351–391 ms | |
| STT of the 4.08 s utterance, Parakeet int8, 4 threads | **101–114 ms** | 145–163 ms | 174–189 ms | 186–203 ms |
| STT, whisper base (mlx on the Mac) | 92–98 ms | | | |
| STT, whisper small (mlx; faster-whisper int8 on karol) | 152–160 ms | 504–522 ms | | |
| STT, whisper large-v3-turbo (mlx) | 424–434 ms | | | |
| **End of speech → text at the Line** (Parakeet) | **473–489 ms** | 536–554 ms | 540–577 ms | |
| TTS first audio (Pocket, streamed) | 51–126 ms | 68–145 ms | 85–101 ms | |
| **Text → first sound at the caller** (Pocket, lead silence trimmed) | **224–254 ms** | 192–259 ms | 210–226 ms | |
| Same, lead silence not trimmed | 383–450 ms | 449–507 ms | | |
| **End of the caller's words → first sound of the reply at the caller** (no model) | | | | **865 ms** fixed buffers, 925 ms adaptive |
| baresip CPU per minute of call, audio both ways | 0.80–0.90 s | 1.71 s | 2.49 s | |
| Hang up (command → closed event) | 13–40 ms | 24–34 ms | 24 ms | |

What the words were (the caller says "Tomás"):

| Engine | Heard |
|---|---|
| Parakeet TDT 0.6B v2 int8 (both machines) | "Prepare the one-on-one with Priya and nudge Tomas about the runbook." |
| whisper base (mlx) | "… and nudge to Moth about the runbook." |
| whisper small (mlx, faster-whisper) | "… and nudge Tamas about the runbook." |
| whisper large-v3-turbo (mlx) | "prepared the one-on-one with Priya, and nudged Hamas about the runbook." |

Speech cost, CPU seconds per second of audio (5 runs each; the input band
limited to 8 kHz like a phone line):

| Engine | Mac | karol |
|---|---|---|
| Parakeet int8, 4 threads, no thread spinning | 0.076 (wall 0.026) | 0.56 (wall 0.041) |
| Parakeet int8, onnxruntime default threads | 0.134 | 2.90 (24 threads spin; do not ship this) |
| faster-whisper base int8, 8 threads | | 0.83 |
| faster-whisper small int8, 8 threads | | 1.36 |
| Pocket TTS, 4 torch threads | 0.239 (RTF 0.139–0.163) | 0.279 (RTF 0.167) |

Rejected on the numbers: macOS `say` as the Line's voice (it writes a whole
file; 1 696–2 331 ms for 4.85 s of speech, against Pocket's 51–126 ms to
the first chunk); whisper turbo (slower and worse on this name); faster-whisper
on `karol` (3–4 times slower than Parakeet, and it loads PyAV).

**The turn, end to end.** From the end of his words to the first sound he
hears, over the tailnet, with a warm model: 865 ms (measured, no model) +
the model pass 0.8–1.0 s for a plain answer (measured in the Calls design §4)
≈ **1.7–1.9 s**. The filler "One moment." (§5) comes at 1.5 s, so a plain
answer often comes just after it. LINE-2 measures where the first model
token falls and sets the filler time from that number.

## 4. The Line

### A node role

`holdspeak line` is a HoldSpeak node role: one process per machine that owns
a phone line. It runs:

1. **baresip** as a supervised child (restart with backoff 1 s → 30 s; a
   crash ends the call with outcome `failed`). The Line writes baresip's
   `config` and `accounts` into `~/.holdspeak/line/` (0600) at each start and
   binds SIP to one address only: `127.0.0.1` for tests, the machine's
   tailnet address for the free SIP address, never `0.0.0.0`.
2. **The audio bridge**: two unix sockets the `aupipe` module connects to
   (`say.sock`: our 16 kHz s16le mono PCM into the call; `heard.sock`: the
   caller's PCM out, 20 ms frames). The Line sends 20 ms frames in real time
   with at most a socket buffer of lead (4 KB ≈ 125 ms), so a barge-in stops
   our voice within about that.
3. **Speech**: an energy VAD with the 300 ms end-of-speech rule (the spike's
   numbers; LINE-2 may swap in Silero or `onnx-asr`'s VAD, MIT, if the
   energy rule fails on a real line), Parakeet for STT, Pocket for TTS (each
   in the Line's own process; models loaded and warmed at start).
4. **The link to the hub**: the node link of `holdspeak node serve`
   (`holdspeak/delivery/node_link.py`, `holdspeak/commands/node_serve.py`):
   outbound only, its own node token (`X-HoldSpeak-Node-Token`, never the
   browser token), hello with capabilities, heartbeat each 5 s, live → stale
   at 15 s → offline at 30 s. The Line declares the capability `calls.line`.

Text crosses the node link, never audio: the hub sends `say`, `hangup` and
`call`; the Line sends `incoming`, `heard`, `said`, `ended`. So the Line on
`karol` costs the tailnet a few hundred bytes per turn.

### The contract: a second adapter, the runner does not change

`holdspeak/calls/line.py` (LINE-2) adds `Line`, with the exact surface of
`AiPhone` (`holdspeak/calls/aiphone.py`) and the same `Reply`:

| `AiPhone` | `Line` |
|---|---|
| `await listen(call_id=, timeout=)` → `Reply` (`incoming`, `heard`, `ended`; exit 10 on a timeout) | waits on the node's event queue for that call; the same kinds and codes |
| `await say(text, call_id=)` → `{"result": "said"\|"interrupted"}` | the hub queues `say`; the node speaks it and answers `said` or `interrupted` (barge-in) |
| `await hangup(say=, call_id=)` | the same, the node says the words then hangs up |
| `await call(to, ring_seconds=, line=)` → `{"outcome": "answered", "call_id"}` | the node dials (`dial` on `ctrl_tcp`), answers when `CALL_ESTABLISHED`, or a code |
| `running()` (probes `control.sock`) | the node link is `live` |
| `state()` (`state.json`: `lines`, `active_call`) | the node's last hello and heartbeat: `lines` (account, registered or not), `active_call` |
| `stop_all()` | cancels the waits |

The exit codes stay the result codes, by the same numbers, so
`REASONS` and the `409` reasons of `POST /api/calls/place` do not change:
0 ok, 5 busy, 6 no answer, 7 rejected (a SIP 4xx/6xx), 9 the Line is not
running (node offline or baresip down), 10 listen timeout, 11 no such call,
12 another listener, 13 emergency number, 14 daily limit.

`CallsService` picks the adapter: `calls.line` (new key, §9) empty means
ai-phone as today; a node name means `Line(node)`. `_phone_fn`
(`holdspeak/calls/service.py`, `__init__`) is the one place that changes.

### The wire (hub routes, node token, through the service)

```
POST /api/calls/line/hello      {node, lines:[{id, kind, address, state}], version}   → {config}
POST /api/calls/line/events     {events:[{seq, kind, call_id, text?, remote?, result?, transcript?}]} → {acked}
POST /api/calls/line/next       {after?, wait_s≤25}  → {commands:[{id, op:"say"|"hangup"|"call", call_id?, text?, to?}]}
```

`next` is a long poll (the `mesh serve` pattern). `config` carries the Line's
settings and, for a carrier account, its password once per hello (§8).

## 5. The turn timing and the guards (on the Line)

The Line keeps the caller's clock, so it owns the line's manners. These are
ai-phone's design (github.com/oxnw/ai-phone at `436f9f1b`,
`docs/usage.md#agent-commands`; credit to its authors), written new in our
words; none of its code is read into ours.

| When | The Line does |
|---|---|
| 300 ms of quiet after speech | the utterance ends; Parakeet runs; `heard` goes to the hub |
| 1.5 s after `heard` and no `say` yet | says "One moment." (synthesized at start, kept as PCM) |
| 10 s after `heard` and no `say` yet | says "Still with you, one moment." |
| 25 s after `heard` and no `say` yet | says "Sorry, I cannot answer now. Goodbye." and hangs up (`ended`, `ended_by: "holdspeak"`) |
| He speaks while the Line speaks | after 200 ms of speech the Line stops its voice and answers the `say` with `interrupted` |
| Each 9 s of a long turn | the runner's "Still working on it." (`KEEPALIVE_SECONDS`, as built) |

The guards, also on the Line (the hub checks them too; two locks, one rule):

- **AI disclosure** on every call the Line places: the first words are "This
  is HoldSpeak, an AI assistant, calling for Karol." before the runner's
  greeting.
- **Emergency numbers are never dialled**: at least 911, 112, 999 and 000,
  from one table in LINE-2 that the hub and the Line both read → exit 13.
- **Daily limit**: a new key `calls.daily_limit` (proposed default 20)
  placed calls a day → exit 14. Incoming calls do not count.

## 6. Audio

**The chosen path: `aupipe`, our baresip module over two unix sockets.**
Measured mouth to ear 61–82 ms on one machine, about 160–190 ms Mac → karol
over Tailscale. Why this and not the others:

| Path | Result |
|---|---|
| `aufile` source (a WAV file per `say`) | rejected: `aufile_src.c` reads the whole file before it starts (`read_file` loops to EOF), so a FIFO blocks and a say cannot stream; each say also needs `/ausrc` to switch source |
| `aufile` player to a FIFO | works in principle (it writes each ptime), but it writes a WAV header and gives no barge-in control |
| `sndfile` | not in the Homebrew bottle; file based like `aufile` |
| `aubridge`, `ausine` | in-process test devices; no way out of the process |
| JACK, PulseAudio, CoreAudio loopback | a sound server and a virtual device on each machine; more moving parts and more delay |
| **`aupipe` (ours)** | streams both ways in 20 ms frames, silence when we send nothing, drops a frame when we do not read (never blocks baresip), reconnects per call |

Rates and codecs: our side is always 16 kHz mono s16le (`ausrc_srate` and
`auplay_srate` 16000, `ausrc_channels`/`auplay_channels` 1); baresip
resamples to the codec (`auresamp`: "aupipe ---> aubuf ---> auresamp --->
PCMU" in the log). The codec order is opus, PCMU, PCMA. The Homebrew bottle
has **no opus** (its modules: `g711`, `l16` and no `opus.so`, `g722`); our
Linux build has opus (it negotiated "opus 48000Hz 2ch"). PCMU is what every
carrier and softphone takes, and Parakeet was right on it.

Buffers (measured on the tailnet): `audio_jitter_buffer_type fixed`,
`audio_jitter_buffer_ms 40-80`, `audio_buffer 20-60` cut the echo round trip
from 375 to 324 ms and the whole turn from 925 to 865 ms. These are the
defaults; a carrier line may need more (§12).

## 7. Speech

| | Mac | karol |
|---|---|---|
| STT | Parakeet TDT 0.6B v2 int8, `onnx-asr`, CPU, 4 threads, no spinning: 101–114 ms per 4 s utterance | the same: 145–189 ms |
| TTS | Pocket TTS, 4 torch threads, streamed, lead silence trimmed: first sound at the caller in 224–254 ms | the same (torch CPU build): 192–259 ms |
| Why not mlx whisper on the Mac | it is fast (92–160 ms) and in HoldSpeak already; Parakeet is as fast, was the only one right on "Tomás", and is one engine on both machines. mlx stays for dictation. |
| Why not Kokoro | GPL espeak-ng (§2) |

One engine pair on both machines means one code path and one set of tests.
The models come through the concierge (the Engines window's download path):
two new catalog rows, "Phone speech in (Parakeet, 0.6 GB)" and "Phone voice
(Pocket, 0.2 GB)" (measured downloads: 631 MB and 215 MB), each with its CC-BY-4.0 line.

## 8. SIP lines

### The free SIP address (no account, no money), proven

On the tailnet a SIP address needs no registrar. The Line listens on the
machine's tailnet address; a softphone with Tailscale on dials it. The spike
proved this path between machines: the Mac's baresip dialled
`sip:line@100.118.33.80:5070` (karol), the call was set up in 133–219 ms over
UDP, audio went both ways, and karol's Line heard "Prepare the one-on-one
with Priya and nudge Tomas about the runbook." and spoke its reply.

The account line (`~/.holdspeak/line/accounts`):

```
<sip:holdspeak@100.118.33.80:5060>;regint=0;answermode=manual;audio_codecs=opus,PCMU,PCMA
```

The address to dial is `sip:holdspeak@karol` (MagicDNS) or
`sip:holdspeak@100.118.33.80`. For the owner's iPhone: a SIP app with
Tailscale on, for example Linphone or Groundwire (an app on his phone; not
in our tree or process). Who may call: Tailscale ACLs decide who reaches the
port; the Calls gate (allowed numbers, then the passphrase) decides who gets
hands.

### Telnyx (a real number): the shape, to verify at sign-up

```
<sip:USER@sip.telnyx.com;transport=tcp>;auth_pass=SECRET;outbound="sip:sip.telnyx.com;transport=tcp";regint=600;answermode=manual;audio_codecs=PCMU,PCMA,opus
```

From `karol` and from the Mac the trunk is reached over the internet; the
registration keeps the router's NAT mapping open. Unknown until his account
exists: whether Telnyx latches RTP to our source address (then no STUN is
needed), or whether the account needs `medianat=stun` with a STUN server, or
TLS with `mediaenc=srtp`. LINE-3 proves one inbound and one outbound call
before Settings offers it.

**This changes a Calls rule.** The Calls design says "HoldSpeak never asks
for, stores or reads a carrier key" (because ai-phone held it). With our own
line, HoldSpeak holds the SIP password. Proposal: it is entered in Settings ▸
Calls ▸ Line, kept in the hub's keystore with the other account secrets, sent
to the Line node in the `hello` answer over the node link, written only into
the node's 0600 `accounts` file, and never shown again ("Password set").
This needs the owner's word (CONFIG).

## 9. Install

| | Mac | karol |
|---|---|---|
| baresip | `brew install baresip` (4.12.0 bottle; done in this spike). Note: no opus in the bottle | **not `apt install`**: Ubuntu 24.04 has baresip **1.0.0** (`apt-cache policy baresip`: candidate `1.0.0-4build14`) and libre 1.1.0, from 2020, three major versions behind. We build 4.12.0 into `~/holdspeak-line/opt` with `scripts/line/build-baresip.sh` (cmake; measured about 1 minute; no sudo; modules `g711;opus;account;menu;ctrl_tcp;auresamp;stun;ice;turn;srtp;l16`) |
| `aupipe` | compiled at install against the bottle's headers (`cc -bundle -undefined dynamic_lookup -I/opt/homebrew/opt/libre/include/re -I/opt/homebrew/opt/baresip/include`); rebuilt when `brew upgrade` changes baresip (the Line checks the version at start and says "Not installed" with the reason) | compiled by the same script (`cc -shared -fPIC`) |
| Speech | `holdspeak[line]` extra: `onnx-asr`, `onnxruntime`, `pocket-tts`, `scipy` | the same, torch from the CPU index (venv 1.6 GB) |
| Models | the concierge (Engines window) | the concierge, or `holdspeak line models` on the box |
| The service | a launchd agent `com.holdspeak.line.plist` (we ship it) | a systemd **user** unit `holdspeak-line.service` (we ship it; `systemctl --user enable --now holdspeak-line`; no sudo; beside `llama-qwen.service`, which it never touches) |
| Run | `holdspeak line --node this-mac` | `holdspeak line --node karol --hub https://<the hub's tailnet name>` |

The node token comes from `holdspeak node token create karol --capability
calls.line` on the hub and `holdspeak node pair` on the box, as for any node.

## 10. Faces (kit only)

A canvas sheet at 1440 and 393 is LINE-4's first step (design on the canvas
before build; it is not drawn in this lane).

**Settings ▸ Calls ▸ Line** (Settings is where egress and machines are named):

- *Where it runs*: a choice of "This Mac" or "karol" (the linked Line nodes),
  each with a dot and a state word from the Engines vocabulary: Ready,
  Starting, Not running, Not installed, Not set up, Offline, Downloading N %.
- *The line*: "A SIP address on your tailnet" with the address to dial and
  Copy, or "A Telnyx number" with the user, the number and "Password set".
- **Test call** (library Button): the Line calls the owner's SIP app (the
  first allowed number or his SIP address); the row shows "Ringing", then
  the result word.
- The checklist rows of `GET /api/calls/status` `steps` gain "Line": Install
  the line, Start it, Add a line.

**The Calls window status bar**: "● Ready for calls", "● On a call · 2:14",
"● Line not running". **Flag against the brief:** the brief asks for "Line on
karol · ready" in the status bar. UX-CANON A.9 as amended 2026-10-25 forbids
a host chip on the status bars of working windows, so "karol" is said only in
Settings ▸ Calls ▸ Line (and as a hover title on Test call). The owner can
overrule this; the default follows the canon.

`GET /api/calls/status` gains `line: {node, state, words, address}`; the
`aiphone` block stays while ai-phone is an adapter.

## 11. Slices

| # | Slice | Proof it must leave |
|---|---|---|
| **LINE-2** | The Line node: `holdspeak/line/` (supervisor, config writer, `ctrl_tcp` client, the audio bridge, VAD, Parakeet, Pocket, the timing of §5, the guards), `aupipe.c` with its build script, the `Line` adapter, the three routes, `calls.line`, **a fake baresip for tests** (a Python process that speaks `ctrl_tcp` netstrings and plays or records PCM on the two sockets, shapes recorded from real baresip 4.12.0 events) | pytest: the `Line` adapter against the fake baresip (real subprocess); the runner end to end through `Line` with the recorded LAN engine reply (the same test as `AiPhone`'s, a second parameter); one real two-baresip call on `127.0.0.1` marked `slow` (the spike's harness, kept as a test: mouth to ear < 150 ms, Parakeet hears the fixture utterance); a guard that the Line process maps no GPL library (`/proc/self/maps` on Linux, `vmmap` on macOS: no espeak, x264, x265) |
| **LINE-3** | The node on karol: enrolment (`node token create` with `calls.line`, `node pair`), the systemd user unit, the launchd agent, the concierge rows, Settings keys, the free SIP address on the tailnet, the Telnyx account after his sign-up | a real call from the Mac to karol through the hub's runner (a recorded turn); `systemctl --user status holdspeak-line` after a reboot; with his account, one inbound and one outbound Telnyx call |
| **LINE-4** | Faces (canvas first) + docs (`docs/calls.md` Line section, `THIRD_PARTY_NOTICES.md` for Parakeet and Pocket weights) + ai-phone kept as an optional adapter until the Line has done his real calls for a week, then parked (never deleted) | vitest on recorded hub answers; the sweep at 1440 and 393; the owner's own call |

## 12. Costs, measured

A call minute, taken as 30 s of his speech and 20 s of the Line's:

| | Mac | karol |
|---|---|---|
| baresip | 0.8–0.9 CPU s (PCMU) | 1.7 CPU s (PCMU), 2.5 (opus) |
| Parakeet, 30 s of speech | 2.3 CPU s (0.076/s) | 17 CPU s (0.56/s) |
| Pocket, 20 s of voice | 4.8 CPU s (0.239/s) | 5.6 CPU s (0.279/s) |
| **Total per call minute** | **≈ 8 CPU s ≈ 0.13 of one core** | **≈ 24–25 CPU s ≈ 0.4 of one core (of 24 threads)** |

Disk: on karol `~/holdspeak-line` is 3.0 GB (venv 1.6 GB with CPU torch,
models, the build). Not measured: memory, and the Python bridge's own CPU
(the harness ran beside the speech in one process).

## 13. Unknown (not measured here)

- A human voice on a real phone line: the caller in the spike was a
  synthetic voice. The energy VAD's thresholds (600 / 250 RMS) are from that.
- Barge-in: the stop time is estimated (socket lead ≈ 125 ms), not measured.
- Telnyx NAT and codec behaviour (§8).
- The iPhone softphone's codec choice over the tailnet (it may offer opus;
  the Mac bottle cannot take it).
- Memory of the Line process on each machine.
- Long calls (the longest spike call was about 90 s).
- The first model token time in a real turn, to place the 1.5 s filler.

## 14. What the owner presses

1. A ruling on the SIP password custody (§8): HoldSpeak holds the carrier
   password for its own line.
2. A ruling on the two GPL findings (§2): the Kokoro `tts` extra and
   faster-whisper's PyAV.
3. Later, his phone: a SIP app with Tailscale on, dialling the address in
   Settings ▸ Calls ▸ Line.
4. Later, Telnyx: an account, a number, and its SIP credentials in Settings.

What the spike left on the machines (all reversible): on this Mac,
`brew install baresip` (baresip 4.12.0 and libre 4.12.0; `brew uninstall
baresip libre` removes them). On karol, `/home/karol/holdspeak-line/` only
(the 4.12.0 build in `opt/`, the venv, the models in `hf/`, the spike
scripts); no sudo, no apt, no system file, and `llama-qwen.service` was not
touched (`rm -rf /home/karol/holdspeak-line` removes it all).

## Built, 2026-10-29

LINE-2, the node, merged as #1608; the canvas as #1607; the faces and the
docs in the LINE-4b PR. The recipe is `RECIPE.md` in this folder. Where the
build differs from this design:

- **`aupipe` is BSD-3-Clause, not Apache-2.0** (§2): `hs/line/aupipe/aupipe.c`
  carries a BSD-3 header, the licence of the baresip modules it sits beside.
- **The wire has three routes, and the faces two more** (§4):
  `POST /api/calls/line/hello`, `/events`, `/next` (the long poll), and for
  Settings `GET /api/calls/line/status` (node, state, words, address, and
  where each secret is: `keystore`, `environment` or `missing`, never a value)
  and `POST /api/calls/line/test` (the Line calls him, says one sentence,
  hangs up; its answer is the result word: `answered`, `no_answer`, `busy`,
  `rejected`, `not_running`; a 409 says `no_number`, `no_line` or `busy`).
  The `line` block of `GET /api/calls/status` is `{node, state, words, address,
  secrets}`; with the Line as the phone the `aiphone` block says `off`.
- **The node uses the hub token until LINE-3** (§4): `HubClient` is the one
  class the node credential changes.
- **The secrets** (§8): `calls.line.sip_password` and
  `calls.line.telnyx_api_key` in the hub's keystore, written through
  `PUT /api/settings` (`calls.line.account.password`, `calls.line.telnyx_api_key`;
  write only, `null` forgets). `TELNYX_API_KEY` and
  `HOLDSPEAK_LINE_SIP_PASSWORD` in the hub's environment are a dev fallback,
  said once in the log. A key in the owner's `~/.zshrc` is not in the hub's
  environment (his hub on 2026-10-29 answers `missing` for both), so the face
  offers the write field.
- **`holdspeak line models` fetches the two models from Hugging Face**
  (`snapshot_download`) until the concierge rows land (LINE-6). The Engines
  catalog is a signed envelope of LLM presets (`gguf`, `mlx_safetensors`), so
  the two speech rows of §7 are not a row edit.
- **The Line runs in its own Python 3.13** (§9): the hub's venv is CPython
  3.14 and onnxruntime 1.23.2 has wheels up to cp313 only, so
  `uv sync --extra line` cannot install Parakeet into the hub's venv on the
  Mac. `docs/calls.md` gives the steps (`uv python install 3.13`,
  `uv venv ~/.holdspeak/line/venv --python 3.13`, `uv pip install` of
  `holdspeak[line]` from the checkout, `holdspeak line models`, then
  `holdspeak line`); LINE-3's `holdspeak line install` does them.
- **The fixed jitter buffer is the default** (§6): `audio_jitter_buffer_type
  fixed`, `audio_jitter_buffer_ms 40-80` (`hs/line/supervisor.py`).
- **Two census edits**: the model census (`tests/unit/test_one_path_census.py`
  `ADAPTER_ALLOWLIST`) names the Line's Parakeet leaf in the node's own
  process; the effect fence (`tests/unit/test_kernel_effect_fence.py`
  `_EXCLUDED_CALLS`) names the node's link to its hub, `baresip -h` and the
  `make` of `aupipe`.
- **The adapter pick** (§4): `calls.line.adapter` empty means the Line when
  baresip is found (or `where` names a node), else ai-phone when it is
  found; `HOLDSPEAK_AI_PHONE` (a rig naming ai-phone whole) and
  `HOLDSPEAK_LINE=off` keep ai-phone.
- **The faces** (§10, canvas direction A): Settings ▸ Calls ▸ Line is
  `desk/calls/LineSettings.tsx` (Where it runs with the measured cost per
  place, The line, Test call, From Calls, Adapter, the egress sentence once).
  Where it runs offers This Mac and the place in `calls.line.where`; the hub
  does not yet list its linked Line nodes (LINE-3). On This Mac, Not
  installed and Not running show the own-venv commands with Copy; the hub
  does not start the Line. The Calls window says Ready for calls, Line
  starting (a live lamp), Line not running, or No line: set one in Settings
  ▸ Calls ▸ Line; no machine is named there (A.9). Left from the canvas:
  Cancel on a ringing Test call (no hub verb), "Answered · m:ss" (the test
  answer has no length), the Number row (no settings key; LINE-3b), the
  primary empty-state verb (the kit's `SurfaceState` draws it secondary),
  and the Engines rows (LINE-6).

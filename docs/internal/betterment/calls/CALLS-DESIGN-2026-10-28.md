# Calls: call HoldSpeak, and HoldSpeak calls

Status: design for the owner, 2026-10-28. Lane CALLS. Canvas:
`docs/internal/betterment/canvases/calls-2026-10-28.html`. Spike: slice 1
below (built in this lane; no account, no key, nothing leaves the device).

## 1. The job

The owner, 2026-10-28, in New York: "start implementing this concept as a
capability of this platform: to be able to place calls and use them to
integrate with a specific HoldSpeak instance, to then push things forward,
prepare things, send things and so on. We have an awesome home server that
could do the heavy lifting as the inference engine for running the actual
calling agent." He then named the shape he means: **ai-phone**
(github.com/oxnw/ai-phone, "an AI phone agent that runs on your computer").

In his terms: *I'm walking in Times Square. I call my HoldSpeak. I say
"prepare the 1:1 with Priya and nudge Tomás about the runbook". It does it,
reads back what it did, and asks before anything leaves the device.*

Done when: one call does that job, the transcript is a note on his desk,
each thing it did is a receipt in Activity, and nothing left the device
without his spoken or pressed yes.

## 2. The decision: HoldSpeak does not build telephony

ai-phone (read at commit `436f9f1b`, 2026-10-28) already is the phone half:

| Part | ai-phone | Where it runs |
|---|---|---|
| Line | PJSIP: a SIP address (free), a SIP trunk, Telnyx or Twilio (a real number) | The Mac |
| Speech in | Parakeet on MLX, 300 ms end-of-speech wait | The Mac |
| Speech out | Phonon (TTS stage 52 ms p50) or Kokoro | The Mac |
| Turn control | **Relay mode**: `call --relay`, `listen`, `say`, `hangup --say`, one JSON object per command (`--json`), exit codes 0–14 | A CLI to its daemon |
| Fill while thinking | "One moment." after 1.5 s, "Still with you, one moment." at 10 s, hangs up at 25 s | The daemon |
| Guards | AI disclosure on every outbound call; emergency numbers never dialled; `calls.daily_limit` | The daemon |

So HoldSpeak is the **brain and the hands**: a call line is a process,
like a CLI engine. HoldSpeak owns each turn:

```
his phone ──SIP/RTP──▶ ai-phone daemon (the Mac: line, Parakeet, Phonon)
                          ▲  `ai-phone listen --json`  → {"kind":"heard","text":…}
                          │  `ai-phone say "…" --json` → {"result":"said"}
                          ▼
                   HoldSpeak hub: the call runner (holdspeak/services/call_service.py)
                          │  one thread turn per utterance, CALL prompt, ASK palette
                          ▼
                   the Answers engine: qwen3.8-27b on the home box over Tailscale
                          │  tool calls
                          ▼
                   the hub's own MCP dispatch (one hub, the owner's principal)
```

**The honest shape.** The owner's picture was "the home server runs the
calling agent". ai-phone runs only on macOS on Apple Silicon, and the home
box `karol` (100.118.33.80) is Linux (`/home/karol/...` in its llama.cpp
`/props`). So: **the home box is the agent's mind; the Mac is its mouth and
ear.** The ai-phone daemon runs beside the hub on the Mac (line, Parakeet,
Phonon). Every word of thought comes from the home box: HoldSpeak's turn runs
on the "Home engine over Tailscale" profile (`engine-tailscale-karol-8080`,
qwen3.8-27b), and ai-phone's own brain (used only when nobody relays) is the
same box: `brain: {kind: openai_compatible, base_url:
"http://100.118.33.80:8080/v1", model: "qwen3.8-27b"}`. The Mac downloads
no language model.

**Install (his press, CONFIG).** `git clone https://github.com/oxnw/ai-phone.git`,
`./scripts/install.sh` (Homebrew `swig`, `pkgconf`, `pjproject`; `uv sync`;
builds the SIP library; downloads no model), `uv run ai-phone setup`
(direction, model, line, voice; downloads Parakeet and the voice). The daemon
is `uv run ai-phone run`; there is no background service, and it must stay up
to receive calls. Its state: `~/.ai-phone/config.yaml`, `~/.ai-phone/secrets.env`
(carrier keys), `~/.ai-phone/state.json` (lines, active call, brain; what
`ai-phone status` prints), `~/.ai-phone/control.sock`; logs in
`~/Library/Logs/ai-phone`.

### Licence

ai-phone is AGPL-3.0-or-later; its PJSIP interface files are GPLv2-or-later.
HoldSpeak is Apache-2.0. HoldSpeak never imports, vendors, links or ships
ai-phone code. It runs the owner's own install as a separate program and
reads its JSON on stdout, the same boundary as the CLI engines (`claude -p`,
`codex exec`, `intel/cli_engine.py`). That is two programs that talk at arm's
length, not one combined work. The JSON shapes in our fake CLI
(`tests/fixtures/fake_ai_phone.py`) are facts about an interface, written
from its command reference (`docs/usage.md#agent-commands`) and its
`cli_call.py`/`calls.py`/`daemon.py`; no ai-phone code is copied. If we ever
want to embed it (in-process, or ship it in our installer), that is a
licence decision for the owner, not a lane.

## 3. The call channels, with cost

| # | Channel | What it needs | Money | Who presses | Order |
|---|---|---|---|---|---|
| 0 | **Voice in the phone web app** over Tailscale (the hub at `https://karols-macbook-pro.tailad9943.ts.net`): mic → the hub's Whisper → the same call turn → browser speech | Nothing new. The parts exist: `lib/callLoop.ts` (energy VAD → 16 kHz WAV → `/api/transcribe`), `lib/tts.ts` (the hub's Kokoro when the `tts` extra is in, else `speechSynthesis`). Today they serve only the parked Thread pullout's call chip. | 0 | nobody | Slice 5: nearly free, but it is not a call: the screen must stay on, the phone app must be open. |
| 1 | **ai-phone, a SIP address on the tailnet**: a SIP softphone on the iPhone (Linphone, Groundwire, Acrobits) with Tailscale on dials `sip:holdspeak@<the Mac's tailnet name>` | ai-phone installed on the Mac (Homebrew `pjproject`, `swig`, `pkgconf`; `uv sync`; `ai-phone setup` downloads Parakeet and the voice: some GB); one softphone app | 0. No carrier, no number, no account. RTP stays inside the tailnet. | **The owner: CONFIG** (an install on his Mac, model downloads) | **First real call.** |
| 2 | **ai-phone with a real number**: Telnyx or Twilio SIP trunk → ai-phone. He dials a normal number from the Phone app or CarPlay; HoldSpeak can call him (`call +1… --relay`) | A carrier account, a number, the trunk password in ai-phone's `secrets.env`; NAT for SIP/RTP (ai-phone's `docs/nat-checklist.md`) | Carrier list prices (check at sign-up; these are what we know, not a quote): a US number about $1–1.15 a month; inbound about $0.002–0.0085 a minute; outbound about $0.005–0.014 a minute. 30 one-minute calls a day ≈ $2–8 a month plus the number. | **The owner: CONFIG + EGRESS** (account, keys, audio crosses the carrier) | Second. |
| 3 | **iPhone Shortcuts / Siri as a door**: "Hey Siri, call HoldSpeak" runs a Shortcut that dials channel 1's SIP URI (or channel 2's number), or opens channel 0's page | A Shortcut on his phone | 0 | the owner (on his phone) | With 1 or 2: a door, not a channel. |

Recommendation: **1 → 3 → 2 → 0**. Channel 1 is a real call at no cost and
without an account; it proves the whole loop on his tailnet. Siri makes it
one sentence. A real number is the same code with a different line; it waits
for his account. Channel 0 is kept for "my softphone is not set up" and is
cheap to add later.

**The carrier: Telnyx.** One API key, and ai-phone buys the number itself
(`ai-phone lines add telnyx --key-env TELNYX_API_KEY --country US --area 212`),
SIP-native, the lowest per-minute price of the two. Twilio is second, for when
he already has a Twilio number (`ai-phone lines add twilio --key-env
TWILIO_ACCOUNT_SID --secret-env TWILIO_AUTH_TOKEN --existing +1…`: nothing is
bought). Both keys live in ai-phone's `~/.ai-phone/secrets.env`; **HoldSpeak
never asks for, stores or reads a carrier key.** The free proof before any
account: a SIP address line (`ai-phone lines add sip --id agent --user agent
--host <the Mac's tailnet name> --trusted <the iPhone's tailnet IP>`, or setup's
"A SIP address") and `pjsua --local-port 5070 sip:agent@127.0.0.1` on the Mac.
His own mobile number can stay on his SIM: `lines verify-caller-id` (one SMS)
for calls out, `lines forward … --when no-answer` (one dial code) for calls in.

## 4. The calling agent

### The loop (relay mode)

The hub keeps one listener while `calls.enabled` is on and the daemon runs
("full auto": no Wait verb). `holdspeak/calls/` holds the code.

1. `ai-phone listen --json --timeout-sec 60`, again and again (exit 10 = no
   call yet; exit 12 = another listener; exit 9 = the daemon went away: the
   status says so and the hub tries again each 15 s).
2. `{"ok":true,"kind":"incoming","call_id":"c9b1e0","line":"main","remote":"sip:+1…@…"}`
   → a call record; `call_state` frame. A placed call (`call <num> --relay
   --json` → `{"ok":true,"call_id":…,"mode":"relay","outcome":"answered"}`)
   joins here.
3. The gate (§5): `calls.allowed_numbers`, then the passphrase. Then
   `calls.greeting` ("Hello. What can I do?").
4. Each `{"ok":true,"kind":"heard","text":…}` is one turn: a thread turn
   (`ThreadService.start_turn`) on the call's own thread (the call's
   history is the thread's), capability **`calls.turn`**, with the **CALL
   prompt** (short spoken sentences; no markdown; say what you did) and the
   **CALL palette** (§5).
5. While the turn runs the runner says "Still working on it." each 9 s
   (ai-phone already says "One moment." at 1.5 s and hangs up at 25 s
   without a `say`). A held tool call is said as a question ("I want to send
   Runbook reminder to Platform channel. Say yes or no."); the next `heard`
   answers it (`ThreadToolExecutor.decide`).
6. The answer is made speakable (no markdown, no refs, 600 characters at
   most) and the **read back** is added from the turn's own record
   (`run_trace.use_by_trace`: *wrote* and *prepared*), not from the model's
   words: "Done: added a task, Nudge Tomás about the runbook."
7. `ai-phone say "…" --json` → `{"ok":true,"result":"said"|"interrupted","call_id":…}`, then 1.
8. `{"ok":true,"kind":"ended",…,"transcript":[{"who":"agent"|"them","text","at","interrupted"}]}`,
   or "goodbye" / "hang up" heard (→ `hangup --say "Goodbye." --json`), or
   `POST /api/calls/{id}/hangup` → the transcript is a Note ("Call · 28 Oct
   09:12"), filed to the call's Project when the call named one (the first
   `project:` ref the turns read or wrote), and the record keeps the note's
   ref.

**`calls.turn`** is a new capability row (Engines ▸ "Phone calls"): text in,
text out, tool calls, no structured output (like `chat.turn`). Its default
is the home engine profile `engine-tailscale-karol-8080` when that profile
exists; otherwise the capability falls back to the global assignment, like
every capability. The turn needs a server that takes tool calls
(`ask_desk.server_takes_tools`); without one the call says "My engine cannot
use your desk now." and still keeps the transcript.

### The model: qwen3.8-27b on the home box, measured

Measured tonight from this Mac to `100.118.33.80:8080` (llama.cpp
`Qwen3.8-27B-UD-IQ4_XS-mtp`, one slot, 49 152 context; `/props`
`supports_tools: true`, `supports_parallel_tool_calls: true`), streamed:

| Request | First token | Whole reply |
|---|---|---|
| Plain answer, short prompt, thinking off | 0.61 s | 1.05 s |
| One tool call, short prompt, thinking off | 0.78 s | 0.95 s |
| Plain answer, thinking on | 0.49 s | 1.54 s |
| One tool call with 8 711 tokens of tool schemas, **cold** | 6.33 s | 6.59 s |
| The same prefix, **warm** (llama.cpp keeps the prefix) | 0.61 s | 0.84 s |

The ASK palette is 25 040 characters of schemas (about 6 000 tokens), so a
cold first turn is about 4–5 s of prompt reading at ~1 400 tokens/s; every
later turn on the same call is warm.

The turn budget, warm, from the end of his words to the first word heard:
end-of-speech 300 ms + Parakeet ~100 ms + the CLI round trip (to measure;
the adapter calls the venv's `ai-phone` binary, not `uv run`) + the model
pass ~0.8–1.0 s + Phonon ~50 ms ≈ **1.4 s for a plain answer**. A turn with
tools takes one model pass per tool round plus a final pass: **2.5–4 s** for
"prepare the 1:1 and nudge Tomás". ai-phone says "One moment." at 1.5 s, so
the line is never silent; the runner says "Still working on it." each 9 s,
far inside ai-phone's 25 s limit. A spoken answer in < 2 s holds for plain
questions, not for multi-tool turns; we say so instead of promising it.

Two honest risks: the box has **one slot**, so a meeting summary running on
it makes the call wait; and the cold prefix. Fixes, in order: warm the slot
when a call starts (one zero-token request with the CALL prefix while ai-phone
says its greeting), and in time a second slot (`-np 2`) or a smaller
speaking model for the final pass.

**"structured_output_unsupported for agent.plan / agent.tool_turn on that
profile".** The call does not use those capabilities. It uses `chat.turn`
(the Thread loop: plain text out, OpenAI-format tool calls in), which needs
no structured-output claim (`inference_capabilities.py`, `chat.turn` has no
`structured_output`). The refusal on `agent.plan`/`agent.tool_turn` is a
**claim gap, not a model gap**: those capabilities demand a typed-result
claim and a qualified tool manifest on the profile
(`inference_assignment_service._incompatibility`), and a legacy v1 profile
can never carry them (`inference_route_plan_service`, the v1 branch refuses
any `structured_output`). The server takes tools and JSON schema (measured
above). The fix is to make the home box a v2 profile and run its Check so
the claim and the manifest are written. Unknown from this lane: whether the
owner's `engine-tailscale-karol-8080` is v1 or v2 (that is his database; not
read).

### Speech: STT and TTS

ai-phone does both on the Mac, so the hub's Whisper is not on the call path.

| | Choice | Why |
|---|---|---|
| STT | ai-phone's Parakeet (MLX, Mac) | 96 ms p50 STT stage in its baseline; endpointing and barge-in are its job. whisper.cpp on the home box would add a network hop for audio and gain nothing. |
| TTS | ai-phone's **Phonon** (52 ms p50 TTS stage, 2026-10-27) | The fastest; Kokoro (more voices, ~164 ms) is the owner's pick in `ai-phone setup`. `say` on macOS has no streaming into RTP. |
| Its own brain | `brain.kind: openai_compatible` at the home box | Used only for a call nobody relays (the hub is down). Points at the same box, so the Mac downloads no LLM. |

## 5. Authority on a call

The owner's rule (2026-09-29): threads stop for his press on EGRESS,
AUTHORITY and CONFIG; everything else is YOLO. On a call the press is **his
spoken yes**, after the gate. The gate is the existing truth table
(`thread_tools.resolve_tool_decision`): the call's thread gets policy `ask`
on every egress tool it offers, so each one holds, and his yes or no decides.

| Unasked (WORK) | Held for his spoken yes (EGRESS) | Not on a call |
|---|---|---|
| Every read of the ASK palette: desk, meetings, People reads, projects, decisions, memory, Jira search | `channel.send` (a prepared send leaves), `nudge.send` (a GitHub comment as him) | Config tools (Settings, engines, accounts) and authority tools (confirm a decision or a proposal, People writes). Config by voice is a later ruling, not this slice. |
| Writes on his desk: a note, a task, a proposed decision, a project item; `channel.prepare` | A desk write his control mode holds (Secure or Normal) is said the same way | `calls.place` (the agent never dials) |

Before the yes, the runner says what leaves, in words: the destination's
name and the document's title for a send; the person and the repository for
a nudge. "No", silence until the next turn, or a hang up denies it.

**Who is calling.**
- `calls.allowed_numbers`: the caller's number (digits of the SIP URI) must be
  in the list; an empty list lets any caller reach the passphrase.
- The passphrase (`calls.passphrase`), spoken first. Without one the call has
  no hands: "Calls are not set up. Set a passphrase in HoldSpeak." and a hang up.
- Caller ID is a hint, never a key (it can be forged on the PSTN); the
  passphrase is the key. Two wrong tries end the call.

**Receipts.** Every tool call of a turn goes through the kernel broker and
is receipted under the turn's operation (Activity shows it, the spoken yes
included as the decision). The call adds the Note and its record.

## 6. The contract for the faces lane

No face in this lane. A FACES lane builds the Calls window, Settings ▸ Calls
and the phone door from this contract (canvas: `canvases/calls-2026-10-28.html`).

### Settings keys (`/api/settings`, section `calls`)

| Key | Type | Default | Meaning |
|---|---|---|---|
| `calls.enabled` | bool | `false` | The hub listens for calls while the daemon runs |
| `calls.aiphone_dir` | str | `""` | The ai-phone checkout; the hub runs `uv run --project <dir> ai-phone`. Empty: `ai-phone` on `PATH`. `HOLDSPEAK_AI_PHONE` (a whole command) wins for rigs |
| `calls.greeting` | str | `"Hello. What can I do?"` | Said after the passphrase |
| `calls.allowed_numbers` | list[str] | `[]` | Callers that may reach the passphrase; the first is "his number" for Call me |
| `calls.passphrase` | str | `""` | Write only: the API answers `passphrase_set: true/false`, never the value |

### REST

- `GET /api/calls/status` →
  `{"enabled", "aiphone": {"state": "not_found"|"not_running"|"running", "words"}, "lines": [{"id","kind":"trunk"|"sip","state","words"}], "engine": {"profile_id","model","state":"ready"|"no_tools"|"none","words"}, "passphrase_set", "listening", "active": <summary>|null, "steps": [{"id":"install"|"daemon"|"line"|"engine"|"passphrase"|"enable","done","words"}]}`.
  The face draws `steps` as Settings ▸ Calls's checklist and `aiphone.words` as a dot and a word. It reads ai-phone's `~/.ai-phone/state.json` and probes `control.sock`; it never reads `secrets.env`.
- `GET /api/calls` → `{"calls": [<summary>…]}`, newest first (the last 20).
- `GET /api/calls/{id}` → `<call>` (the summary plus `transcript`).
- `POST /api/calls/place` `{"to"?: "+1…"|"sip:…"}` → `<summary>` (201). `to` defaults to `calls.allowed_numbers[0]` (Call me). 409 `{"reason":"busy"|"not_running"|"no_line"|"daily_limit"|"no_answer"|"rejected"}`.
- `POST /api/calls/{id}/hangup` → `<summary>`.
- `POST /api/calls/{id}/decide` `{"decision":"approve"|"deny"}` → `<summary>` (the tap form of the spoken yes; 409 when nothing is held).

`<summary>`: `{"id","direction":"in"|"out","remote","state":"ringing"|"gate"|"live"|"ended","started_at","answered_at","ended_at","duration_sec","first_words","hold":{"tool","words"}|null,"results":[{"kind","label","ref","effect":"wrote"|"prepared"|"sent"}],"note_ref","project_ref","outcome","ended_by"}`.
`<call>` adds `"transcript": [{"who":"caller"|"holdspeak","text","at","interrupted"}]`.

### Frame

`call_state` (registered in `holdspeak/realtime_frames.py` and the web
mirror): `{"reason": "incoming"|"heard"|"said"|"hold"|"decided"|"result"|"ended"|"status", "call": <call>}`.
One frame per change; the window replaces its copy of the call.

### MCP (through the same service)

`calls.status` and `calls.list` (WORK, reads), `calls.hangup` (WORK),
`calls.place` (EGRESS: a real call; an agent's call holds for his press).

### The faces

- **Calls window** (Go ▸ Work ▸ Calls): toolbar **Call me** (primary) /
  **Hang up** on a call; the call as a document (`LiveTranscript`); a held
  question as one row with **Yes** and **No**; "Done on this call" rows;
  past calls as a dense list; status bar `● On a call · 2:14` /
  `● Ready for calls` / `● ai-phone not running` (no host, number or engine
  chip: A.9).
- **Settings ▸ Calls**: the `steps` checklist with the exact commands
  (install, `ai-phone run`, `lines add telnyx …`), the engine row, the
  passphrase, the numbers, the switch. Egress is disclosed here.
- **The phone**: a Calls tile on the phone home.
- **A note on his desk** (the owner's ask): "Calls: sign up at Telnyx, then
  Settings ▸ Calls", written once by the hub when `calls.enabled` is off and
  no line exists.

## 7. The slices

| # | Slice | Proof |
|---|---|---|
| **1** | **The hub slice** (this lane): `holdspeak/calls/` (the ai-phone adapter, the runner, the service), the `calls.turn` capability, the settings keys, REST, the `call_state` frame, the MCP tools, `docs/calls.md` | pytest: the adapter against a fake ai-phone CLI (real subprocess, shapes from ai-phone's command reference); the runner end to end with the **recorded LAN engine reply** (`tests/fixtures/ask_tool_turn_lan.json`) through the real thread loop and MCP dispatch: the task is written, the read back is said, the transcript is a Note; a held send decided by a spoken yes and by a spoken no; API surface and OpenAPI regenerated; the frame registry fence |
| 2 | **The faces** (a FACES lane, from §6): the Calls window, Settings ▸ Calls, the phone tile, the desk note | vitest on recorded hub answers; the sweep at 1440 and 393 |
| 3 | The owner's first call: ai-phone installed, a SIP address line, the softphone on the tailnet | his call |
| 4 | Telnyx: a real number | his account; carrier charges |
| 5 | Channel 0: the phone web app's call screen on the same runner (callLoop + tts) | vitest; the owner on his phone |
| 6 | HoldSpeak calls someone else (`calls.place` to another number with his press per call; ai-phone says the AI disclosure) | his press |

## 8. What the owner presses

1. **Install ai-phone on the Mac** (CONFIG; local): `git clone https://github.com/oxnw/ai-phone.git ~/dev/ai-phone && cd ~/dev/ai-phone && ./scripts/install.sh && uv run ai-phone setup` (Homebrew packages; Parakeet and a voice, some GB). In setup pick "receive and place calls", the brain "OpenAI-compatible" at `http://100.118.33.80:8080/v1`, model `qwen3.8-27b`, and "A SIP address" for the free first call. Then `uv run ai-phone run` (keep it running).
2. **Settings ▸ Calls**: the checkout (`~/dev/ai-phone`), a passphrase, his number, the switch on.
3. **A softphone on the iPhone** with Tailscale on; it dials `sip:agent@<the Mac's tailnet name>`.
4. **Telnyx** (CONFIG + EGRESS; money): an account and an API key, put in `~/.ai-phone/secrets.env` as `TELNYX_API_KEY`, then `uv run ai-phone lines add telnyx --key-env TELNYX_API_KEY --country US --area 212` and restart the daemon.

# Phase 13 — Answer the Coder

**Status:** COMPLETE (4/4 — **Track N gate ACHIEVED** + the Companion board shipped.
Answer the coder by voice from the iPad — surface the waiting coder(s), pick the target,
speak, transcribe on-device, deliver — is real end to end). **Track N — added by owner steer
(2026-06-20), outside the original charter's Tracks A–L.** This is the payoff of
the companion track and the scenario the owner painted in his own words:

> "We're coding away in our tmux session ... we happen to have installed our hooks,
> we're pointing to the server. On the other hand, our iPad is pointed to the same
> server. Boom. The agent has a question. Well, guess what? Now we know it on the
> iPad, and we can use our native functionality to send back a voice note around
> this — and use all the rich plugins."

The agent (in your tmux + hooks session, talking to the desktop server) raises a
question. The iPad — pointed at the same server — **surfaces it**, and you answer
with a **native voice note** that runs through HoldSpeak's rich dictation pipeline
(plugins, blocks, corrections) and is **delivered back into the coder session**.
That is the AI PI ("AI Pie") companion loop, driven from the iPad for the first
time. Built native over the desktop HTTP API (owner call), on the Phase-12 client
foundation.

**Last updated:** 2026-06-20 (**HSM-13-03 DONE — the Companion board; PHASE 13 COMPLETE
(4/4).** A `CompanionBoard` seam (`companionStatus`/`select`/`dismiss`/`pin` over
`/api/companion/*`) + RuntimeCore view-model surface the waiting coder(s) and make the
selected reply target unmistakable; selection is server-side so the next answer delivers
to it with no silent default. `CompanionAnswerApp` renders the board (each waiting coder
+ its question, confidence, pin/stale; "Answer this one" → "Your answer lands here").
`swift test` 129/6-skip/0-fail (+7 `CompanionBoardTests`: render, select-makes-active,
pin/unpin, dismiss, honest-empty, unreachable→failure); the app builds for device. See
[`evidence-story-03`](./evidence-story-03.md). **Phase 13 — Answer the Coder is done.**
Earlier: **HSM-13-04 DONE — the answer-the-coder gate ACHIEVED by voice.** A real on-device voice answer app (`CompanionAnswerApp` + `WhisperKitTranscriber`
driving the HSM-13-02 `VoiceNoteComposer` over `AudioCaptureService` + WhisperKit) lets
the iPad surface the waiting question, record a spoken answer, transcribe it **on-device**,
review, and deliver it into the coder. Proven on a physical iPad Air M4: the question
surfaced → a spoken answer → on-device WhisperKit → landed in a live tmux coder pane. The
first run exposed a Whisper control-token leak in the delivered text — fixed with the pure,
unit-tested `WhisperText.clean` (+5 tests) and redeployed. `swift test` 122/6-skip/0-fail;
the voice app builds + links WhisperKit for device. See [`evidence-story-04`](./evidence-story-04.md)
+ [`final-summary`](./final-summary.md). Only HSM-13-03 (board multi-target selection)
remains in the phase. Earlier: **HSM-13-04 — the answer-the-coder gate, delivery half
proven on real metal.** The keystone HSM-13-01 deferred — real delivery — is now wired:
`WebRuntime._deliver_remote_dictation` delivers a companion answer into the waiting
coder via the EXACT path local dictation uses (`_try_tmux_agent_reply` → `tmux
send-keys`, `typer` fallback), deliver-only (the route already ran the pipeline) and
**raises** when undeliverable so the client never gets a false ack; wired through
`WebRuntimeCallbacks.on_remote_dictation` → `WebContext`. Proven end-to-end on metal: a
**real** Stop-hook awaiting session (`agent-hook ingest`) → an answer **originating on a
physical iPad** (the CompanionProbe grew an "Answer the coder" send) → landed in a live
tmux coder pane (`tmux capture-pane` committed). `uv run pytest` (delivery) 5 passed,
sweep 315 passed; the iPad harness builds for device. The gate stays **in-progress**:
the iPad sent typed text, not a **native voice note** (needs on-device Whisper, a
pending Phase-3 device gate), and the HSM-13-03 board surfacing remains. See
[`realmetal-log-gate`](./realmetal-log-gate.md). Next: HSM-13-03 (the board), then close
the gate by answering with voice. Earlier: **HSM-13-02 done — the native voice-note composer.**
`VoiceNoteComposer` (RuntimeCore) is a state machine — idle → recording →
transcribing → review → delivering → delivered/failed — over three seams it does not
own: the Phase-2 `IAudioCapture`, a `([AudioChunk]) -> ITranscriber` **factory** (built
over the captured audio; no second transcription path, MLX discipline stays inside the
transcriber), and the HSM-13-01 `sendRemoteDictation`. The owner's hard line is
structural: `stopAndTranscribe()` always lands in `.review`, `send()` is separate and
a no-op outside review — **nothing is delivered before an explicit send**; an empty
note is guarded. `swift test` **117/6-skip/0-fail** (+10 `VoiceNoteComposerTests` over
fake seams). The live on-device walkthrough folds into HSM-13-04. See
[`evidence-story-02`](./evidence-story-02.md). Next: HSM-13-03 (the Companion board)
or HSM-13-04 (the gate). Earlier: **HSM-13-01 done — the remote-dictation inject path,
LAN-proven.** Desktop `POST /api/dictation/remote` runs a client-dictated answer
through the **same rich pipeline** as the browser dry-run
(`_run_dictation_dry_run_text` — corrections/blocks/plugins) and delivers the
*processed* text via a new `on_remote_dictation` host hook (no hook → process-only;
hook raises → `502`, never an autonomous retry). The Swift seam
`IDesktopClient.sendRemoteDictation` + `RemoteDictationResult` posts it, token joined
at call time. A new `HOLDSPEAK_WEB_HOST` override lets the desktop bind off-loopback
(default `127.0.0.1` unchanged) so a companion can reach it — token-enforced. Proven
on real metal: a physical iPad Air M4 ran the new `CompanionProbe` device harness and
established a live connection to this Mac's desktop runtime over the LAN
(`192.168.1.28:8000 ← 192.168.1.67`); off-loopback auth verified `401`-without-token →
`200`-with. `uv run pytest` (route) **7 passed**; `swift test` **107/6-skip/0-fail**.
See [`evidence-story-01`](./evidence-story-01.md). Next: HSM-13-02 (native voice-note
capture). Earlier: scaffolded from the owner's answer-the-coder steer.)

## What "AI PI" is (so this is grounded, not invented)

AI PI is the desktop's already-shipped agent companion loop (desktop Phase 24):
when a coding agent is waiting on a reply, HoldSpeak knows about it and can deliver
a spoken/typed answer into that session. The desktop already serves it at
`/api/companion/status` (waiting sessions, selected target, delivery confidence,
blockers) with `select` / `dismiss` / `pin` controls, and a read-only `/companion`
portal page. This phase gives that loop an iPad face and a native-voice answer
path — it does not reinvent the loop.

## Goal

Make the iPad a first-class way to answer a waiting coder: surface the AI PI
companion state on the iPad, capture a native voice note (reusing the on-device
capture + Whisper + the rich dictation pipeline), and deliver the result into the
selected coder session via a desktop inject endpoint. The phase passes when, on
real hardware, an agent's question raised in a real coding session is answered by
voice from the iPad and lands back in that session (the Track N gate). The Propose
→ Review → Approve discipline holds: the iPad never injects without the user's
explicit send.

## Scope

- **In:** the remote-dictation **inject path** — a new desktop endpoint that accepts
  a dictated payload from the client and routes it through the dictation runtime's
  rich pipeline (plugins/blocks/corrections), plus the client side that posts it
  (HSM-13-01); native **voice-note capture → dictation** on the iPad (reuse Phase 2
  capture + Phase 3 Whisper → the pipeline) (HSM-13-02); the **Companion board** on
  the iPad surfacing AI PI state + target selection (`/api/companion/*`)
  (HSM-13-03); and the end-to-end **answer-the-coder** gate closeout (HSM-13-04).
- **Out:** the connection/seam + meetings remote control + shell (Phase 12 — this
  builds on them). Autonomous delivery (the user always presses send; never
  auto-injected). New AI PI *intelligence* (the loop exists on the desktop; this
  surfaces and feeds it). The PencilKit notebook (Phase 8). Hardening (Phase 11).

## Exit criteria (evidence required)

- [x] A desktop endpoint accepts a dictated payload from the client and routes it
      through the dictation runtime's rich pipeline (plugins/blocks/corrections),
      not as raw text; the client posts to it through the Phase-12 seam; both ends
      tested (HSM-13-01). *(LAN-proven on a physical iPad — evidence-story-01.)*
- [x] The iPad captures a native voice note (on-device capture + Whisper) and turns
      it into pipeline-processed dictation text ready to deliver (HSM-13-02).
      *(`VoiceNoteComposer` view-model + seams, host-tested; live on-device run folds
      into HSM-13-04.)*
- [x] The iPad surfaces the AI PI companion state (waiting sessions, selected
      target, confidence, blockers) from `/api/companion/status` and can pick the
      target session via `select`/`dismiss`/`pin` (HSM-13-03). *(`CompanionBoard` seam +
      view-model + board UI; host-tested. Server-side selection routes the answer.)*
- [x] **Track N gate — answer the coder, end to end:** in a real coding session
      (tmux + hooks → desktop server) an agent's question is surfaced on a physical
      iPad, answered by a native voice note, and the answer lands back in that coder
      session — the user pressing send, never autonomous — evidenced by a device
      walkthrough (HSM-13-04). *(ACHIEVED: question surfaced on the iPad → a **spoken**
      answer → on-device WhisperKit → landed in a live tmux coder pane, never
      autonomous. The first run's Whisper token-leak was fixed + unit-tested.)*

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-13-01 | Remote-dictation inject path (desktop + client) | done | [story-01](./story-01-remote-dictation-inject.md) | [evidence](./evidence-story-01.md) |
| HSM-13-02 | Native voice-note capture → dictation | done | [story-02](./story-02-voice-note-capture.md) | [evidence](./evidence-story-02.md) |
| HSM-13-03 | The Companion board (the agent's question on the iPad) | done | [story-03](./story-03-companion-board.md) | [evidence](./evidence-story-03.md) |
| HSM-13-04 | Answer-the-coder gate closeout | done | [story-04](./story-04-answer-the-coder-closeout.md) | [evidence](./evidence-story-04.md) · [final-summary](./final-summary.md) |

## Where we are

Both halves of the answer path now exist. The inject path (HSM-13-01) is **done** —
the one genuinely new desktop-side surface accepts a client-dictated answer, runs it
through the rich pipeline, and hands the processed text to a host delivery hook; the
Swift seam posts it; a physical iPad reached the desktop over the LAN to prove the
carrying seam on real metal. The native voice-note composer (HSM-13-02) is **done** —
a RuntimeCore state machine that records, transcribes on-device, lets you review/edit,
and delivers on an explicit send (never before), host-tested over its capture /
transcriber / desktop seams. The gate (HSM-13-04) is **achieved by voice**: a
`CompanionAnswerApp` surfaces the waiting question, records a spoken answer, transcribes
it **on-device** with WhisperKit (a real `WhisperKitTranscriber` driving the HSM-13-02
`VoiceNoteComposer`), lets you review, and delivers it through the inject path into the
live coder — proven on a physical iPad Air M4 (question surfaced → spoken answer →
on-device transcript → landed in a live tmux pane, never autonomously). The first run
caught a Whisper control-token leak in the delivered text; fixed with the unit-tested
`WhisperText.clean` and redeployed. The on-device-Whisper "last mile" is closed. The **Companion board** (HSM-13-03)
now closes the phase: a `CompanionBoard` seam + view-model surface the waiting coder(s)
and make the selected reply target unmistakable (`select`/`dismiss`/`pin`), with
server-side selection routing the answer — no silent default. **Phase 13 — Answer the
Coder is complete (4/4).** The companion track's payoff is real: point the iPad at the
same server you code against, see the agent's question, pick the target, and answer by
voice — transcribed on-device, delivered into the coder, never autonomously.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The iPad injects into a coder session without the user's explicit approval (the unforgivable agent-companion bug) | high | Delivery is always user-pressed-send; the inject endpoint is a propose/deliver-on-command path, never autonomous; mirror the actuator Propose→Approve discipline | Any code path injects without an explicit send — halt; the companion never acts on its own |
| The voice note is delivered as raw transcript, bypassing the rich pipeline the owner asked for | high | HSM-13-01 routes through the dictation runtime's plugins/blocks/corrections; a test asserts a known correction/plugin transform is applied to a delivered payload | A delivered answer is verbatim Whisper output with no pipeline applied — wire it through the pipeline, that richness is the point |
| Delivery targets the wrong agent session (answer lands in the wrong coder) | medium | The Companion board makes the selected target explicit and visible before send; reuse the desktop's existing target-selection (`select`/`pin`); show the target in the send confirmation | The send UI does not show which session will receive the answer — make the target unmistakable before any send |
| The inject endpoint becomes an unauthenticated write into the dev machine | medium | The endpoint requires the Phase-12 client token; honest egress label on the iPad; the credential is joined at call time, never echoed (mirror the Phase-61 Slack discipline) | The endpoint accepts an untokened write — gate it behind the client handshake |
| Latency/availability of the companion state makes the board feel dead | low | Poll first (Phase-12 default); flag an event/push transport as the optimization that makes "boom, the agent has a question" feel instant; do not block send on it | The board only updates on manual refresh and misses live questions — schedule the event-transport follow-up |

## Decisions made (this phase)

- 2026-06-20 — **Owner steer:** the centerpiece is answering a waiting coder by
  native voice from the iPad — the agent asks (tmux + hooks → server), the iPad
  (pointed at the same server) surfaces it, you answer by voice note through the
  rich pipeline, it lands back in the session. This is Track N.
- 2026-06-20 — Delivery is never autonomous: the user always presses send. The
  inject path is propose/deliver-on-command, consistent with the program's
  "the mobile runtime never acts autonomously" principle and the desktop actuator
  Propose→Approve→Execute lifecycle.
- 2026-06-20 — The answer runs through the **rich** dictation pipeline
  (plugins/blocks/corrections), not as raw transcript — the owner asked for "all
  the rich plugins," and that richness is the differentiator over a dumb text box.
- 2026-06-20 — **Ratified into the charter as Amendment 1.1** (co-canon with Rev
  1.0); this phase's track gate is **Gate 10 (Answer the Coder)**. Program risk P10
  retired.
- 2026-06-20 — **Owner call (Amendment 1.1, Q4):** iPhone and iPad are at the
  **same priority** — answering a waiting coder from the phone in your pocket is at
  least as valuable as from the iPad. This phase targets **iPhone + iPad at
  parity**; the gate (HSM-13-04) proves the scenario on both.
- 2026-06-20 — **Owner call (Amendment 1.1, Q5):** the desktop API change
  (`POST /api/dictation/remote`, HSM-13-01) is **authorized** as a tracked
  cross-roadmap `holdspeak` dependency; route through the existing dictation
  runtime so the AI PI delivery path + the rich pipeline both apply.

## Decisions deferred

- The exact inject mechanism on the desktop (route into the AI PI delivery path vs.
  type into the focused dictation target vs. queue to the dictation runner) —
  trigger: HSM-13-01 — default: route through the dictation runtime so the existing
  AI PI delivery + pipeline both apply; reuse, do not fork.
- Live "the agent has a question" push vs. poll on the iPad — trigger: HSM-13-03 —
  default: poll `/api/companion/status` first (Phase-12 default); an event/push
  transport is the follow-on that makes it feel instant.
- Whether the iPad can compose a typed answer too (not only voice) — trigger:
  HSM-13-02 — default: voice-note first (the named scenario); a typed fallback is
  cheap to add once the inject path exists.

# Phase 13 — Answer the Coder

**Status:** planning (scaffolded 2026-06-20). **Track N — added by owner steer
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

**Last updated:** 2026-06-20 (scaffolded — stories HSM-13-01..04 stubbed from the
owner's answer-the-coder steer. No work started.)

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

- [ ] A desktop endpoint accepts a dictated payload from the client and routes it
      through the dictation runtime's rich pipeline (plugins/blocks/corrections),
      not as raw text; the client posts to it through the Phase-12 seam; both ends
      tested (HSM-13-01).
- [ ] The iPad captures a native voice note (on-device capture + Whisper) and turns
      it into pipeline-processed dictation text ready to deliver (HSM-13-02).
- [ ] The iPad surfaces the AI PI companion state (waiting sessions, selected
      target, confidence, blockers) from `/api/companion/status` and can pick the
      target session via `select`/`dismiss`/`pin` (HSM-13-03).
- [ ] **Track N gate — answer the coder, end to end:** in a real coding session
      (tmux + hooks → desktop server) an agent's question is surfaced on a physical
      iPad, answered by a native voice note, and the answer lands back in that coder
      session — the user pressing send, never autonomous — evidenced by a device
      walkthrough (HSM-13-04).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-13-01 | Remote-dictation inject path (desktop + client) | backlog | [story-01](./story-01-remote-dictation-inject.md) | — |
| HSM-13-02 | Native voice-note capture → dictation | backlog | [story-02](./story-02-voice-note-capture.md) | — |
| HSM-13-03 | The Companion board (the agent's question on the iPad) | backlog | [story-03](./story-03-companion-board.md) | — |
| HSM-13-04 | Answer-the-coder gate closeout | backlog | [story-04](./story-04-answer-the-coder-closeout.md) | — |

## Where we are

Just scaffolded from the owner's 2026-06-20 steer, on top of Phase 12's client
foundation. The inject path (HSM-13-01) is the one genuinely new desktop-side
surface (precedent: the mobile program already added Python routes in Phase 10 —
`holdspeak/web/routes/sync.py`); voice-note capture (HSM-13-02) reuses the proven
on-device capture + Whisper; the Companion board (HSM-13-03) consumes endpoints
that already ship; the gate (HSM-13-04) is the real-metal proof of the owner's
scenario. Next: HSM-13-01, once Phase 12's seam exists.

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

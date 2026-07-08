# HSM-15-09 — Proactive agent presence (surface a waiting agent the moment it asks)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** built + Simulator-proven (voice delivery reuses the desk composer; LAN proof owner-gated)
- **Depends on:** HSM-15-08 (the desk it expands into), the Queue HUD, `GET /api/companion/status`,
  the presence/notification surfaces.
- **Owner:** unassigned

## Vision

The desk (HSM-15-08) is where you *go*. This story is what *comes to you*. The whole point of "your
app reacts to that" is **proactivity**: the instant a coding agent transitions to `awaiting_response`,
the mesh tells you — without you opening anything — and you can answer by voice on the spot. Dictation
is push (you → agent); this is the pull (agent → you). It is the difference between a tool you check
and a desk that taps you on the shoulder.

## The design

- **The trigger.** Poll (or subscribe to) `GET /api/companion/status`; detect the rising edge of a
  session becoming `awaiting_response` (or a new waiting session appearing). Debounced; honors a
  quiet/focus mode.
- **The surface (escalating, least-intrusive-first):**
  1. **The Queue HUD pill** gains an agent lane — "1 agent waiting" with the repo — visible above
     every screen, even mid-meeting. This is the always-on, ambient signal.
  2. **A presence nudge** — a tight, dismissible card (Signal craft, the egress badge if relevant):
     *"`pylon-infra` · Claude is waiting — migrate the schema now?"* with **Answer (voice)** / **Open
     desk** / **Dismiss**. No prose; the question is a tight quote.
  3. **A system notification** (opt-in) when the app is backgrounded, so you learn an agent is waiting
     even away from the app.
- **One-tap voice answer** from the nudge — straight into the agent's tmux session (the HSM-13 path).
- **Honest + non-autonomous** — it only ever *surfaces*; it never answers for you. Quiet-mode and a
  per-agent mute respect your focus.

## Acceptance criteria

- [ ] **Rising-edge detection** — a session entering `awaiting_response` is detected once (debounced,
      no repeat-spam), host-tested with a fake status stream.
- [ ] **HUD lane** — a waiting agent appears as a Queue-HUD lane item app-wide (incl. mid-meeting).
      Simulator-shot.
- [ ] **The nudge** — a tight, dismissible presence card with Answer (voice) / Open desk / Dismiss;
      no prose; one-tap voice answer delivers to the agent. LAN-proven.
- [ ] **Notification (opt-in)** — backgrounded, a waiting agent raises a local notification; honored by
      quiet-mode + per-agent mute.
- [ ] **Never autonomous** — it surfaces, never answers for you. Verified.

## Build plan

1. A small presence watcher over `companionStatus()` — rising-edge + debounce + quiet-mode (pure,
   host-tested).
2. The HUD agent lane (extends the Phase-15 `RunQueueStore`/`QueueHUD` with an agent-waiting item type).
3. The presence nudge card (Signal craft) + one-tap voice answer.
4. Opt-in local notification when backgrounded.
5. Simulator shots (HUD lane, nudge) + a LAN proof (a real agent asks → nudge → voice answer lands).

## Test plan

- Host: the rising-edge/debounce/quiet-mode watcher unit-tested with a scripted status stream (assert
  one fire per transition, suppression under quiet-mode/mute).
- LAN/device: a real coder asks → the nudge appears within the poll window → a voice answer lands in
  the coder. The proactive half of the air-gapped Proof (HSM-15-06).

## Notes

- Reuses the HSM-13 delivery spine + the Phase-15 HUD; the new work is the **watcher** + the **nudge**
  + the **notification**, all on existing data (`/api/companion/status`).
- This is what makes the desk a *product*, not a page: it reaches out. Pair with HSM-15-08.

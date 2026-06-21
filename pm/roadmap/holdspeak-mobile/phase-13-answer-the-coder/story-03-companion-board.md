# HSM-13-03 — The Companion board (the agent's question on the iPad)

- **Project:** holdspeak-mobile
- **Phase:** 13
- **Status:** done (2026-06-20 — the `CompanionBoard` seam + view-model surface the
  waiting coders and make the selected reply target unmistakable; host-tested, board UI
  shipped in `CompanionAnswerApp`. See [evidence-story-03](./evidence-story-03.md))
- **Depends on:** HSM-12-01 (seam), HSM-12-03 (the Companion nav slot)
- **Unblocks:** HSM-13-04
- **Owner:** unassigned

## Problem

"Boom. The agent has a question. Now we know it on the iPad." For that to be true,
the iPad must surface the AI PI companion state — which agent sessions are waiting,
which one is selected, how confident delivery is, what is blocking it — and let you
pick the target you are about to answer. The desktop already computes and serves
this; this story gives it an iPad face and makes the answer target unmistakable
before any send.

## Scope

- **In:** the Companion board screen (the deep content of the Phase-12 "Companion"
  nav slot) over `GET /api/companion/status` — waiting agent sessions, the selected
  reply target, delivery confidence, transport, freshness, and blockers — plus
  target selection via `POST /api/companion/select` / `dismiss` / `pin`. The board
  hands the chosen target to the voice-note flow (HSM-13-02 → HSM-13-01) and shows
  that target in the send confirmation.
- **Out:** capturing/sending the answer (HSM-13-02 / HSM-13-01). The AI PI loop's
  intelligence (desktop-owned; this surfaces it). A live push transport (poll
  first; the event transport is the deferred optimization).

## Acceptance criteria

- [ ] The board renders the AI PI state from `/api/companion/status` (waiting
      sessions, selected target, confidence, transport, freshness, blockers) in the
      Signal language, to a high UI standard.
- [ ] The user can select / dismiss / pin a target via the existing companion
      endpoints, and the selected target is unmistakable before any answer is sent.
- [ ] The board hands the chosen target to the answer flow so HSM-13-02's send
      delivers to that session (no silent default target).
- [ ] Unreachable/stale state is shown honestly (freshness/blockers), never faked as
      "nothing waiting."

## Test plan

- Unit: the board view-model over a fake desktop — waiting sessions render, select/
  dismiss/pin update the selected target, the chosen target is exposed to the answer
  flow; stale/unreachable surfaced honestly.
- Screenshot / device: the board on the iPad showing a real waiting session and the
  selected target (folded into HSM-13-04).

## Notes / open questions

- This mirrors the desktop's read-only `/companion` page (desktop Phase 24) but adds
  the iPad-native selection + the bridge to the voice-note answer — reuse the
  desktop's selection endpoints, do not invent parallel state.
- Poll `/api/companion/status` first (Phase-12 default); flag the event/push
  transport as the follow-on that makes "the agent has a question" feel instant.
- Honesty rule (positioning canon): at zero waiting sessions, say so plainly; never
  manufacture a target.

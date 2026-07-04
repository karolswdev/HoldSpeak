# HSM-17-03 — The agent on the desk: a live session as a DeskOS primitive

- **Project:** holdspeak-mobile
- **Phase:** 17
- **Status:** done (2026-07-04 — seeded + LIVE-hub simulator proofs; the cabled-iPad walk stays 17-06; see `evidence-story-03.md`)
- **Depends on:** HSM-17-01 (`AgentSessionPrimitive` + the synced session), HSM-17-02 (live sessions
  actually reporting). Reuses the desk's arrival/glaring treatment (`arrivedIds` / the NEW-arrival flash
  in `DeskDioramaStage.swift`) and the presence watcher pattern (`PresenceStore` / `PresenceWatcher`).
- **Unblocks:** HSM-17-04 / 17-05 (you can't answer a question that isn't on the desk).
- **Owner:** unassigned

## Problem

A live coder is now a contract object that reports its state — but it is invisible on the desk. The whole
point of agent sync is that *"those instances are showing on our DeskOS as primitives when the agent has a
question."* This story is the rendering + the demand-your-attention behaviour.

## The interaction

1. Each live session renders as an **agent primitive** on the desk, with the coder's identity (Claude /
   Codex) and project, and a calm **state** read: *working* (ambient, busy), *idle* (dimmed).
2. When a session flips to `waiting(question)`, the primitive **demands you**: the glaring NEW-arrival
   treatment already used for fresh deliverables — a pulse / flash / "Claude needs you" — so a blocked
   coder is impossible to miss across the room.
3. Tapping it opens the pull-out: the **question** in full, the project/cwd context, and the answer
   affordances (Play-equivalent here = *Answer*; the composer is 17-04/05).
4. State is **live**, not poll-and-forget: as the coder moves working → waiting → working, the primitive
   updates continuously (the presence watcher cadence, or the stream from 17-01).
5. Sessions that end **leave** the desk cleanly (tombstone → fade out), no stale ghosts.

## Scope

- **In:** rendering `AgentSessionPrimitive`s on the diorama from live state; the per-state visual
  language (working / waiting / idle); the **waiting → glaring arrival** behaviour; the pull-out showing
  the question + an Answer entry point; continuous update + clean removal on end.
- **Out:** composing/sending the answer (17-04 spoken/typed/dropped, 17-05 AI-drafted); the persona
  builder.

## Acceptance criteria

- [x] Live Claude/Codex sessions appear as agent primitives on the desk with correct identity + state.
      (LIVE-proven: the desk rendered the Mac's real registry — three sessions, three states.)
- [x] A session entering `waiting(question)` triggers the glaring NEW-arrival treatment; the pull-out
      shows the full question text. (Rising-edge glare, once per flip, 6s auto-clear; NEEDS-YOU section.)
- [x] State changes propagate to the primitive without a manual refresh; an `ended` session is removed.
      (4s poll; the live run showed a decayed `idle` and the absent `ended` tombstone.)
- [x] The agent primitive uses the canonical egress badge and the canon vocabulary (it is a coding
      "agent"/session, never confused with Qlippy or a persona). (`.mixed("your desktop")`, unchanged.)
- [x] Simulator-proven for the visual states (seeded) — and beyond the bar, LIVE-hub-proven in the
      simulator against the real registry. Real metal on the cabled iPad remains HSM-17-06.

## Test plan

- Simulator (seeded states via a sim hook, e.g. `HS_DESK_AGENTSYNC`): a working session, a waiting
  session with a question (glaring), an idle session; screenshot each; confirm a state flip animates and
  an `ended` session disappears.
- Integration: feed two fixture `AgentSession`s through the 17-01 transport → two primitives; flip one to
  `waiting` → the arrival behaviour fires.

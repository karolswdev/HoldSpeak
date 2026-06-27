# HSM-18-01 — The dictation pipeline client + authoring/preview screen

- **Project:** holdspeak-mobile
- **Phase:** 18
- **Status:** todo — **leads the phase.** Stands up the client surface the rest hangs off.
- **Depends on:** `HTTPDesktopClient` / `DeskHostLink` (the authed desktop seam,
  `apple/App/MeetingCapture/`), the hub dictation routes (`holdspeak/web/routes/dictation/`).
- **Unblocks:** 18-02 (macros ride the same relay/board), 18-05 (nudges feed the same
  dictate path), 18-06 (the proof).
- **Owner:** unassigned

## Problem

The iPad has no dictation-pipeline surface. `HTTPDesktopClient.swift` implements only
`sendRemoteDictation`; `CompanionShellApp.swift:228` `dictateScreen` is a static placeholder.
The hub already serves the whole contract — `/api/dictation/readiness`, `/blocks` (+CRUD),
`/block-templates`, `/dry-run`, `/project-context` — and the iPad calls none of it. So the
flagship "dictate into your Mac" mode on the iPad is a stub: you can fire a remote dictation
blind, but you cannot see readiness, preview the rewrite, or manage blocks.

## The design

1. **Extend `HTTPDesktopClient`** with typed methods for the dictation routes: `readiness()`
   → the doctor-style readiness payload; `blocks()` / block CRUD; `blockTemplates()`;
   `dryRun(utterance:)` → the routed/rewritten preview; `projectContext()`. Each rides the
   existing Bearer-authed `post`/`get` seam. Decode into `Contracts` types (snake_case wire).
2. **A real Dictate screen** replacing the `dictateScreen` placeholder: a push-to-talk
   capture (on-device WhisperKit → text, the `VoiceCaptureState` path) that runs a **dry-run
   preview** (you see what the pipeline would produce *before* it injects), a readiness strip
   (model/endpoint/reachable), and the explicit send. Preview-not-inject is the honest default.
3. **In-world, not modal.** The screen is a first-class view, every text field carries a
   speak-to-fill mic, and the send shows the egress badge (local vs your Mac).

## Scope

- **In:** the `HTTPDesktopClient` dictation methods + their `Contracts` decode types; the
  Dictate screen (push-to-talk → dry-run preview → send); the readiness strip.
- **Out:** the macro relay fix (18-02); the language code at the WhisperKit site (18-03);
  the symbol pass (18-04); activity nudges feeding the dictate input (18-05).

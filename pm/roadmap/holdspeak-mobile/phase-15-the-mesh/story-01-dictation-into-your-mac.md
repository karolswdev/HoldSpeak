# HSM-15-01 — Dictation, into your Mac (a first-class flagship mode)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** in-progress — opened 2026-06-22. The lead story of The Mesh.
- **Depends on:** `HTTPDesktopClient` + `POST /api/dictation/remote` (exists, HSM-13-01);
  on-device WhisperKit (exists, HSM-13-04); the reactive recorder waveform (Phase 14).
- **Owner:** unassigned

## Grounding (2026-06-22) — most of this already ships

Desktop analysis corrected the assumptions here:
- **The delivery path EXISTS.** `POST /api/dictation/remote` (`web/routes/dictation/pipeline.py:299`)
  runs companion text through the **full** pipeline and delivers via `_deliver_remote_dictation`
  (`runtime/dictation_capture.py:344`) → `tmux send-keys` (`tmux_transport.py`) or `TextTyper`
  keystroke injection (`typer.py`). LAN-proven (HSM-13). The iPad already does on-device WhisperKit
  transcription and posts the text.
- **So the NEW work is two things, not a pipeline:** (1) the **iPad flagship surface** (the home mode +
  the dictation screen), and (2) a small **desktop generalization** — a target option so remote
  dictation can free-type into the **focused Mac app** even when there is no awaiting coder session
  (today it targets the waiting agent; the `TextTyper`/`target_profile` seam already supports
  free typing — it just needs to be reachable without the agent-session gate).
- The "answer the coder" path (dictate → the live tmux coder) is already done (HSM-13). This story adds
  the **general** "dictate into anything on my Mac" surface on top of the same delivery code.

## Vision (owner)

> "We have our dictation mode where we can dictate into a computer that's connected to us, which
> runs the whole speak server… the iPad is the best mic in the house."

The iPad is the best microphone you own. Your Mac has the keyboard and every app you work in. The
mesh's most-used daily path is the simplest: **pick up the iPad, talk, and the words land in
whatever is focused on your Mac** — typed through the desktop's full dictation pipeline (intents,
spoken symbols, corrections, your paid-for memory), with the transcription itself happening
**on-device**.

Today this capability is reachable only through a separate companion surface (answer-the-coder).
This story makes it a **first-class mode on the flagship home**, beside "New recording."

## The design

- **Home entry.** A "Dictate to **{your Mac}**" tile sits next to "New recording" — same
  flagship treatment (Signal card, glyph, the ON-DEVICE/mesh badge). The peer's name comes from
  the paired `DesktopPeer`. Unpaired → the tile invites pairing (one clear path, not buried in
  Settings).
- **The dictation surface.** A focused, premium screen: the **reactive mic waveform** (the
  Phase-15 fix — it now leaps with your voice), a big push-to-talk / hands-free toggle, and a
  live read-back of what was heard. On-device WhisperKit transcribes; each finalized utterance is
  delivered to the desktop via `POST /api/dictation/remote`, which runs it through the rich
  pipeline and types it into the focused app.
- **Pairing-aware, honest.** An unreachable Mac is a **first-class state**, not an error
  (Providers.swift already frames it this way): a tight chip ("Mac asleep" / "not reachable"),
  never a wall of text. Delivery is confirmed by the desktop's `RemoteDictationResult`
  (`delivered` / target) and shown as a quiet tick — no prose.
- **Egress-honest.** The badge states the scope plainly: words go to **your Mac** on your LAN
  (local mesh), and where they land. No privacy novel — one badge.

## Acceptance criteria

- [ ] **Home mode** — a "Dictate to {your Mac}" tile on the flagship home, peer-named, with the
      mesh/ON-DEVICE badge; unpaired state invites pairing. Simulator-shot.
- [ ] **The surface** — a focused dictation screen with the reactive waveform, push-to-talk +
      hands-free, and a live read-back. Simulator-shot.
- [ ] **On-device → Mac** — finalized utterances transcribe on-device (WhisperKit) and deliver via
      `POST /api/dictation/remote`; the desktop types them into the focused app. **LAN-proven**
      against the real desktop server (a live word-lands-on-the-Mac trace).
- [ ] **Free-typing target (desktop delta)** — remote dictation can deliver into the **focused Mac
      app** via `TextTyper`/`target_profile` **without** an awaiting coder session (today it requires
      one). The "answer the coder" path stays as-is; this adds the general path on the same delivery
      code. Verified on the desktop.
- [ ] **Pairing-aware** — unreachable peer is a first-class state (tight chip); delivery shows a
      quiet confirmation from `RemoteDictationResult`. No prose.
- [ ] **Egress badge** — the scope (local mesh → your Mac) is one badge, per POSITIONING canon.

## Build plan

1. Surface the paired `DesktopPeer` on the home (peer name + reachability) and add the
   "Dictate to {your Mac}" tile beside "New recording".
2. Build the dictation surface (reuse the reactive `MicWaveform`; push-to-talk + hands-free).
3. Wire on-device WhisperKit → `desktop.remoteDictate(...)` (`/api/dictation/remote`); show the
   `delivered` confirmation as a quiet tick.
4. First-class unreachable state + egress badge.
5. Simulator shots (paired / dictating / unreachable) **and** a live LAN trace against the desktop
   server (words landing in a focused Mac app).

## Test plan

- Host: any pure dictation-session state machine (utterance buffering, delivery retry) gets
  RuntimeCore unit tests with a fake `DesktopClient` (assert each finalized utterance posts once;
  unreachable → first-class state, not a thrown error surfaced to the user).
- Device/LAN: the real proof — iPad on-device Whisper → desktop `/api/dictation/remote` → a word
  lands in a focused Mac app (e.g., a text field / the coder). Capture the trace.
- Simulator: the three states shot for the design record.

## Notes

- Reuses, does not reinvent: `HTTPDesktopClient.remoteDictate` already exists; this story is the
  **flagship surface** over it + on-device transcription + honest states.
- This is the path that makes the mesh *felt* on day one — the smallest new surface, the highest
  daily value. It is also half of the HSM-15-06 proof (the air-gapped dictation-driven work loop).

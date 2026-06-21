# Evidence — HSM-8-04 (Artifact review + Track I gate)

**Date:** 2026-06-21 · **Status:** done

The iPad meeting-notebook workflow closes the loop: a recorded meeting yields Phase-6
artifacts the user reviews on-device, alongside the linked notes. The Track I gate —
record → live transcript → PencilKit notebook → linked moments → on-device artifact
review — runs **end to end on a real iPad**, proven by the owner.

## What shipped

- **`ReviewModel` (RuntimeCore):** groups a meeting's artifacts by type in the active
  **MIR profile's emphasis order**, and `approve`/`reject` flips a proposal's status
  (`.draft → .accepted/.rejected`) and persists it — **never executing** anything (the
  charter non-goal: review + approve only). Host-tested over fake artifacts + store.
- **On-device generation:** the meeting detail's **INTELLIGENCE** section runs the
  Phase-6 `ArtifactGenerationEngine` over the transcript using the **on-device
  `LlamaProvider`** (the GGUF in the app container, Mode A) for the MIR profile's types,
  persists each via the Phase-4 store, and shows them grouped with Approve/Dismiss and the
  honest **on-device** egress badge. Generation **streams** — one type at a time, each
  artifact appears as it lands, with progress — and uses `maxAttempts: 2` (bounded repair
  without the default 3× worst case). `gen-meeting-capture.rb` gained LLM.swift +
  InferenceLlama.
- **Bug fixed by the real-metal run:** recording a meeting off a speaker, WhisperKit's
  single final pass over the long buffer returned `[BLANK_AUDIO]`, which was being saved
  as the transcript. `WhisperText.clean` now strips `[BLANK_AUDIO]`/`[MUSIC]`/`[INAUDIBLE]`
  markers, and `MeetingCapture.stop` **falls back to the last good live transcript** when
  the final pass blanks — so what you saw live is what's saved.

## Tests (ran)

`swift test` → **165 passed / 6 skipped / 0 failed** (+8 `ReviewModelTests`: group-by-type,
profile-emphasis ordering, approve/reject persist + never-execute, pending count, save
failure; +2 `MeetingCapture` blank-pass-fallback; +1 `WhisperText` non-speech markers).

## Track I gate — ACHIEVED on real metal (owner-witnessed)

On the physical iPad Air M4, the owner ran the full workflow:
**record a ~4-minute meeting → live on-device transcript (correct after the blank-audio
fix) → stop + reopen → Generate on-device → the 4B model produced decisions / action items
/ risks / requirements → review.** No network at any point.

Honest note on latency: a 4B model generating several artifact types over a multi-minute
transcript takes a few minutes on-device and uses battery — the on-device reality. The
streaming UI + trimmed retries make the wait legible rather than a dead spinner; a smaller
model / a dedicated latency gate is the future optimization (Phase 5/HSM-3-05 territory).

## Acceptance

- **Artifacts render grouped by type, reflecting the active MIR profile** (the profile
  picker drives `ReviewModel.grouped(profile:)`). ✅
- **Proposals reviewed + approved on-device; nothing executes autonomously** — approve
  flips status + persists; no connector/executor exists or runs. ✅
- **Track I gate: the full record→notebook→link→review workflow on a real iPad** —
  owner-witnessed end to end. ✅
- **Egress shown as a badge** (the green "on-device") on the actionable surface, not
  privacy prose. ✅

## Phase 8 status

This closes the **original Track I gate** (the meeting-notebook workflow, HSM-8-01..04).
Phase 8 is **4/6**; the owner's later additions — **HSM-8-05** (the air-gapped fully-local
notetaker as its own airplane-mode gate; note this app is *already* network-free, so it's
within reach) and **HSM-8-06** (ink-into-intelligence: on-device handwriting recognition,
marked moments weighting MIR) — remain.

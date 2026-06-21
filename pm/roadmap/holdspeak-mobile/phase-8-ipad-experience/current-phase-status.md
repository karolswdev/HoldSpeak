# Phase 8 — iPad Experience

**Status:** in-progress (1/6 — **HSM-8-01 done**: the on-device meeting-capture loop
(record → live transcript → persist → reopen) ships as the `MeetingCapture` view-model +
the `MeetingCaptureApp` iPad shell, host-tested and run live on a physical iPad). Track I of the Council
Implementation Charter. The first Platform Host (Layer 4): the iPad app that
turns the runtime into the charter's flagship experience — record a meeting, take
PencilKit notes, link them to the transcript, and review the artifacts, all on an
iPad Air/Pro M4.

**Last updated:** 2026-06-21 (**HSM-8-01 done — the on-device meeting-capture loop.**
`MeetingCapture` (RuntimeCore) composes `IAudioCapture` + a transcriber factory + a
`MeetingStore` seam: record → **windowed live transcript** (`tick()` re-transcribes the
audio so far) → stop persists a `Meeting` → list/reopen-intact. Public inits added to
`Meeting`/`IntelStatus`/`Bookmark` so on-device code can build a recording (Codable/schema
unchanged). `MeetingCaptureApp` is a Signal iPad shell (meeting list + Record/Stop + live
transcript + reopen) over a `WhisperKitTranscriber` + a `SQLiteMeetingStore`. `swift test`
140/6-skip/0-fail (+7); the on-device transcription path is the same WhisperKit one proven
on real metal in HSM-13-04; built + **launched live on a physical iPad Air M4**;
screenshot of the entry surface committed. See [`evidence-story-01`](./evidence-story-01.md).
Next: HSM-8-02 (the PencilKit notebook). Earlier: **elevated to the owner's richness bar.** Two stories
added and the existing notebook/linking stories raised: HSM-8-05 makes the
**air-gapped, fully-local notetaker** (iPad at a meeting, zero connectivity, Mode A
on-device) a first-class scenario with its own gate, and HSM-8-06 makes the **magic
pencil genuinely involved** — handwriting recognized on-device, notes/marks promoted
to artifacts, marked moments weighting MIR extraction — so ink shapes the meeting
output instead of sitting parallel to it. Owner steer: "the air-gapped scenario is
paradigm and has to be rich; the magic pencil has to be involved." Earlier:
scaffolded — stories HSM-8-01..04 stubbed from charter Track I; no work started.)

## The paradigm (owner, 2026-06-20)

> "Hosting a local model and doing local inference on the iPad in the scenario where
> it can't connect to a desktop is the paradigm — an air-gapped meeting. We bring
> the iPad to a meeting, zero connectivity, and let it do the notetaker job. That
> has to be rich. And there has to be a way to create notes with the magic pencil,
> real notes, and have that somehow involved."

This phase is the home of that experience. The fully-local engine (Mode A) lives in
Phase 5; the intelligence in Phase 6; MIR in Phase 7. Phase 8 is where they become
a **rich, first-class, offline notetaker with a magic pencil that feeds the
output** — the standalone counterpart to the Companion track (Phases 12–13). The
iPad stands its own ground with zero connectivity; that is not a fallback, it is the
point.

## Goal

Build the iPad SwiftUI host over the Runtime Core: a meeting-capture screen
(record → live transcript), a PencilKit notebook for handwritten notes,
transcript linking (a note bound to the transcript moment it was written at), and
an artifact-review surface. The phase passes when the full meeting-notebook
workflow is complete on an iPad — the Track I gate. The host is thin: it presents
the Runtime Core, it does not own business logic.

## Scope

- **In:** the iPad app shell + meeting-capture screen over the Runtime Core
  (HSM-8-01); a rich PencilKit notebook (pages, tools, ink + typed) (HSM-8-02);
  transcript linking + one-gesture marked moments — note ↔ `Segment`/timestamp
  (HSM-8-03); artifact review + the notebook-workflow gate closeout (HSM-8-04); the
  **air-gapped fully-local notetaker** scenario + gate (HSM-8-05); and **ink into
  intelligence** — handwriting recognized on-device, notes/marks promoted to
  artifacts, marks weighting MIR extraction (HSM-8-06).
- **Out:** the iPhone experience (Phase 9). Sync across devices (Phase 10). The
  audio/transcription/inference/intelligence engines themselves (Phases 2–7 — this
  host consumes them). Any business logic in the view layer (it stays in the
  core). Hardening scenarios (Phase 11).

## Exit criteria (evidence required)

- [ ] The iPad app records a meeting and shows the live transcript, driving the
      Runtime Core through provider/seam interfaces only (no business logic in the
      views) (HSM-8-01).
- [ ] PencilKit handwritten notes work in a notebook mode and persist with the
      meeting (HSM-8-02).
- [ ] A handwritten note links to the transcript moment it was taken at, and
      tapping the link navigates to that `Segment` (HSM-8-03).
- [ ] **Track I gate — the meeting-notebook workflow is complete:** record →
      transcript → notebook notes → linked moments → artifact review, end to end
      on a real iPad, evidenced by a device walkthrough (HSM-8-04).
- [ ] **Gate 8 — Air-gapped Notetaker (program Quality Gate, ratified Amendment
      1.1):** the whole workflow runs in real airplane mode (no desktop / LAN /
      endpoint) with Mode-A on-device inference, **rich in functionality** (not a
      degraded fallback — the owner's bar for the gate to count), honest local
      egress, **proven on a physical iPad** with iPhone at parity (HSM-8-05).
- [ ] **The magic pencil is involved:** handwriting is recognized on-device, a
      note/marked moment can be promoted to a contract artifact (propose-and-confirm),
      and a marked moment measurably shapes MIR extraction — ink feeds the output,
      it is not a parallel scratchpad (HSM-8-06).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-8-01 | iPad shell + meeting capture | done | [story-01](./story-01-ipad-shell-meeting-capture.md) | [evidence](./evidence-story-01.md) |
| HSM-8-02 | PencilKit notebook | backlog | [story-02](./story-02-pencilkit-notebook.md) | — |
| HSM-8-03 | Transcript linking | backlog | [story-03](./story-03-transcript-linking.md) | — |
| HSM-8-04 | Artifact review + notebook closeout | backlog | [story-04](./story-04-artifact-review-closeout.md) | — |
| HSM-8-05 | The air-gapped notetaker (fully-local, zero-connectivity) | backlog | [story-05](./story-05-air-gapped-notetaker.md) | — |
| HSM-8-06 | Ink into intelligence (the magic pencil, involved) | backlog | [story-06](./story-06-ink-into-intelligence.md) | — |

## Where we are

Scaffolded and now elevated to the owner's richness bar (2026-06-20). This is the
first real on-device product surface and it sits on top of the whole stack: it
needs Phase 2 (audio), Phase 3 (transcript), and — for the review + the air-gapped
loop + ink-into-intelligence — Phases 5–7 (Mode-A on-device inference, the artifact
engine, the MIR seam). The six stories: capture (8-01), the rich PencilKit notebook
(8-02), transcript linking + marked moments (8-03), artifact review + the Track I
gate (8-04), the **air-gapped fully-local notetaker + gate (8-05)**, and **ink into
intelligence (8-06)**. The phase now closes on two things being true at once: the
notebook workflow is complete *and* it is rich with zero connectivity, with the
magic pencil feeding the output. Next: HSM-8-01 once Phases 2–3 give a recordable,
transcribing runtime; 8-05/8-06 sequence after Phase 6 (artifacts) + HSM-5-02
(Mode A) so the offline richness is real, not stubbed.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Business logic leaks into SwiftUI views, breaking the charter's layer rule | high | Views call Runtime-Core seams / view-models only; no engine code in the view layer; keep the host thin | A view imports an engine/provider concrete type or holds business state — pull it into the core |
| Transcript linking has no stable anchor (segment ids shift) to bind a note to | medium | Bind notes to the Phase-0 `Segment` identity/timing, not to rendered text offsets | A note's link breaks when the transcript re-renders — anchor on the contract `Segment`, not the view |
| Artifact review needs Phase 6 artifacts that aren't ready when Phase 8 starts | medium | Build capture + notebook + linking first; gate the review depth (HSM-8-04) on Phase 6; stub artifacts visibly until then | HSM-8-04 can't show real artifacts because Phase 6 isn't done — sequence it after Phase 6, don't fake parity |
| PencilKit + live transcript on one screen fights for layout/performance on smaller iPads | low | Target iPad Air/Pro M4 (Tier-1) first; verify the combined screen on device, not just canvas | The notebook drops Pencil strokes while transcribing live — separate the workloads or stage them |

## Decisions made (this phase)

- 2026-06-18 — The iPad host is a thin SwiftUI Platform Host (Layer 4) over the
  Runtime Core; all business logic stays in the core, per the charter's
  architecture principle — charter Architecture §Principle + §Layers.
- 2026-06-20 — **Ratified in charter Amendment 1.1 (Q3):** the air-gapped
  fully-local notetaker (HSM-8-05) is its **own program Quality Gate — Gate 8** —
  proven on a real iPad and **required to be rich in functionality**, not just an
  offline run. Owner: "we're gonna have to gate it on an actual iPad … needs to be
  rich in functionality for us to even make anything out of it."
- 2026-06-20 — **Amendment 1.1 (Q4):** iPhone is at the **same priority** as iPad.
  The air-gapped notetaker + intelligence ship on iPhone at parity (the iPhone air-
  gapped proof rides Track J / Phase 9); the **Apple-Pencil notebook + ink-into-
  intelligence (HSM-8-02 / HSM-8-06) stay iPad** (hardware), iPhone reaching the
  same outcomes via finger/typed/voice.

## Decisions deferred

- Notebook persistence model (PencilKit `PKDrawing` blob vs. a structured note
  entity) — trigger: HSM-8-02 — default: store the `PKDrawing` data associated
  with the meeting, with link anchors as structured metadata.
- Whether artifact review is read-only in v1 or includes approve actions (the
  Propose→Approve half) — trigger: HSM-8-04 — default: review + approve of
  proposals on-device, never autonomous execution (charter non-goal).
- Multitasking / Stage Manager support — trigger: post-gate polish — default:
  single-window first; multitasking parked.

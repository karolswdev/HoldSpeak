# Phase 8 — iPad Experience

**Status:** in-progress (5/8 done + HSM-8-07/8-08 host-complete — **HSM-8-01..04 + HSM-8-06
done; the Track I workflow gate ACHIEVED**: record → live transcript → PencilKit notebook →
linked moments → **on-device artifact review** + **ink-into-intelligence** run end to end on
a physical iPad (owner-witnessed). **HSM-8-07 (chunked extraction) + HSM-8-08 (OOM-safe
budget) are host-complete** — cores + 12 host tests landed, app wired + device-built; only
their on-device walkthroughs remain, deferred per the owner ("not at my iPad — don't consider
any iPad gates"). Remaining: HSM-8-05 (air-gapped notetaker gate) + the 8-07/8-08 device
proofs). Track I of the Council Implementation Charter. The first Platform Host (Layer 4): the
iPad app that turns the runtime into the charter's flagship experience — record a meeting,
take PencilKit notes, link them to the transcript, and review the artifacts, all on an iPad
Air/Pro M4.

**Last updated:** 2026-06-21 (**HSM-8-07 + HSM-8-08 host-complete — long meetings never
gamble on RAM.** `OnDeviceBudget` (RuntimeCore, pure) sizes the model context to *this*
device — `contextTokens(availableBytes, modelBytes, marginBytes)` returns the largest safe
window (the KV-cache is RAM), clamped to a floor/ceiling, never exceeding the affordable
footprint; the 16K from HSM-8-06 becomes the *ceiling*, lowered when the device can't pay.
`TranscriptWindowing` + `ArtifactMerge` + `ChunkedExtractor` do **map-reduce extraction**:
window the transcript (segment-aligned, overlapping, budget-bounded), extract per window over
the real `ArtifactGenerationEngine`, merge/dedup into one `.draft` set — so **peak memory
stays flat regardless of meeting length** (a 2-hour transcript uses the same per-pass context
as a 20-min one). The app's `generate()` opens the provider at the budget and routes any
meeting that exceeds one window through chunking with a legible "extracting in N passes…"
note; short meetings keep the single fast pass. Owner steer: "increase the baseline … but
let's chunk it. Let's not risk OOM ever." `swift test` **182/6-skip/0-fail (+12)**; the
meeting app **builds + signs for device** (the on-device long-meeting proof is the only
deferred item — owner not at the iPad). These two land **host-complete** (no story flips to
`done`; their evidence files ship with the device proof at the reconvene). See
[`story-07`](./story-07-chunked-extraction.md) + [`story-08`](./story-08-oom-safe-budget.md).
Earlier: **HSM-8-06 done — ink into intelligence (the magic pencil,
involved).** `InkPromoter` (RuntimeCore) turns recognized handwriting into a schema-valid
`.draft` `Artifact` proposal (propose-and-confirm); `InkEmphasis` boosts the intents in
hand-marked segments so a starred moment **measurably changes the routed artifact chain**
(host-proven: a marked light-incident moment surfaces `incidentTimeline` that the unmarked
transcript does not route). The app's **"Add your handwritten notes"** action, per inked
notebook page, (1) renders the ink to an **image artifact** attached to the meeting — the
literal scribble, the owner's explicit ask: *"attach those notes as an actual image"* — and
(2) recognizes the handwriting with **on-device Vision** into a text proposal; Generate +
Add-notes are **independent actions** (run AI before or after adding ink). `swift test`
170/6-skip/0-fail (+5 `InkIntelligenceTests`). **Proven on a real 13-min production meeting**
on the physical iPad (owner-witnessed; artifacts good). Two real-metal fixes landed: a
`@MainActor` static Vision call crashed off-actor — recognition is now `nonisolated` /
`Task.detached`; and on-device generation now **surfaces the real per-type error** instead
of failing silent. **Context bumped 8K→16K** (`maxTokenCount`, ≈ ~80 min of speech) — and
the real-metal long-meeting concern is now backlogged as **HSM-8-07** (chunked map-reduce
extraction, length-independent, never grows the context) + **HSM-8-08** (memory-aware OOM-
safe budget that decides when to chunk). Owner steer: *"increase the baseline … but at the
same time, let's protect this product — let's chunk it. Let's not risk OOM ever."* See
[`evidence-story-06`](./evidence-story-06.md). Phase 8 is **5/8** — HSM-8-05, HSM-8-07,
HSM-8-08 remain. Earlier: **HSM-8-04 done — artifact review + the Track I gate.**
`ReviewModel` (RuntimeCore) groups a meeting's artifacts by type in the active MIR
profile's emphasis order + approve/reject (draft→accepted, persisted, **never executes**).
The meeting detail's INTELLIGENCE section runs the Phase-6 `ArtifactGenerationEngine` over
the transcript with the **on-device `LlamaProvider`** (Mode A, the GGUF in the app
container) for the profile's types, streaming each artifact in (one type at a time,
`maxAttempts: 2`) with Approve/Dismiss + an on-device egress badge. The **Track I gate is
ACHIEVED on a physical iPad** (owner-witnessed: record→transcript→on-device intelligence→
review, no network). A real-metal bug was caught + fixed: WhisperKit's final pass over a
long buffer returned `[BLANK_AUDIO]` — `WhisperText.clean` now strips non-speech markers
and `MeetingCapture.stop` falls back to the last good live transcript. `swift test`
165/6-skip/0-fail (+11). On-device latency for a 4B model over a multi-min meeting is a few
minutes (now streamed + trimmed). See [`evidence-story-04`](./evidence-story-04.md).
Earlier: **HSM-8-03 done — transcript linking.** `TranscriptLinker`
(RuntimeCore) anchors a note/mark on a `Segment` start time (the contract's stable timing,
not text offsets), resolves to the segment whose window contains it (else nearest, else nil
when no transcript — graceful), bidirectionally (`links(atSegmentIndex:)`), persisted per
meeting via a `LinkStore` seam. The app gained a ★ "Mark this moment" button during
recording + a MARKED MOMENTS list in the detail that **taps to jump** to the transcript
segment. `swift test` 154/6-skip/0-fail (+8); run live on a physical iPad. Note: granular
per-segment jumps await HSM-3-02's realtime segmentation (today's transcript is one clean
segment); the anchor logic is already correct for it. See
[`evidence-story-03`](./evidence-story-03.md). Next: HSM-8-04 (artifact review + notebook
closeout). Earlier: **HSM-8-02 done — the PencilKit notebook.** A `Notebook`
view-model (RuntimeCore) round-trips PencilKit pages (serialized `PKDrawing` blobs) through
a `NotebookStore` seam, keyed per meeting + versioned; UIKit-free, corrupt-blob-safe. The
app gained a `PencilCanvas` (PKCanvasView + the system tool picker: pen/pencil/highlighter/
eraser/ruler), `NotebookView` (multi-page + add-page), a `FileNotebookStore` behind the
seam, a **Transcript / Notes** segmented control in the capture screen so ink + transcript
coexist, and a notebook reload on the meeting detail. `swift test` 146/6-skip/0-fail (+6);
screenshot-verified (the rich surface) + run live on a physical iPad. See
[`evidence-story-02`](./evidence-story-02.md). Next: HSM-8-03 (transcript linking).
Earlier: **HSM-8-01 done — the on-device meeting-capture loop.**
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

## ⚠️ Pending device verification — the on-device generation fix (2026-06-21)

The on-device artifact generation had a real bug the real-metal testing surfaced. It is
**fixed in code, host-built, but NOT yet verified on the iPad** (owner stepped away from the
device). **This gate must clear before HSM-8-06's generation and the HSM-8-07/8-08 device
proofs can be called done.**

**The bug (root-caused from a device breadcrumb log):** a 22-min meeting generated only
`decisions`; the other three types failed `noJSON`, and a context-reset attempt made the app
**crash** on the 2nd inference. Cause: `LlamaProvider` reused ONE `LLM` instance for every
artifact type, but LLM.swift accumulates KV context across `getCompletion` calls and never
clears it — so the 2nd+ call starved for context (`noJSON`), and clearing it mid-flight raced
the decoder (crash).

**The fix (in code, device-UNVERIFIED):** the generation loop now creates a **fresh
`LlamaProvider` per inference** — every call is a clean "first call" (the one that always
works). No racy reset; one llama context resident at a time (LLM `deinit` frees it). Also: a
**"Regenerate on-device"** button (always available — "Generate" when empty, "Regenerate"
when populated; a clean regenerate drops prior model artifacts, keeps the ink), and a pullable
`Documents/gen-debug.log` (TEMPORARY diagnostic scaffolding — REMOVE at gate close).

**To clear this gate on the iPad (no code changes needed — already deployed):**
1. Open the 22-min meeting → **Regenerate on-device** → it runs all four passes
   (decisions → action items → risk register → requirements) and **does not crash**.
2. Pull `Documents/gen-debug.log` → expect four `w0 ok …` lines + `done produced=4`
   (not one `ok` + three `noJSON`).
3. Confirm **Regenerate** stays available afterward and replaces cleanly (no duplicate piles).
4. Memory stays flat across the four passes (no jetsam kill).
5. Once green: **remove the `gen-debug.log` instrumentation**, then proceed to the
   HSM-8-07/8-08 long-meeting (hour-plus) + HSM-8-05 air-gapped device proofs.

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
- [x] **The magic pencil is involved:** handwriting is recognized on-device, a
      note/marked moment can be promoted to a contract artifact (propose-and-confirm),
      and a marked moment measurably shapes MIR extraction — ink feeds the output,
      it is not a parallel scratchpad. The literal ink also attaches as an **image
      artifact** (owner's ask). Proven on a real 13-min production meeting (HSM-8-06).
- [ ] **Long meetings never gamble on RAM:** generation over an hour-plus meeting runs
      to completion on-device via **chunked map-reduce extraction** (HSM-8-07), with a
      **memory-aware budget** that sizes the context to the device and decides when to
      chunk (HSM-8-08) — so peak memory stays flat with meeting length and the app is
      never OOM-killed mid-generation. Owner steer: "let's not risk OOM ever."

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-8-01 | iPad shell + meeting capture | done | [story-01](./story-01-ipad-shell-meeting-capture.md) | [evidence](./evidence-story-01.md) |
| HSM-8-02 | PencilKit notebook | done | [story-02](./story-02-pencilkit-notebook.md) | [evidence](./evidence-story-02.md) |
| HSM-8-03 | Transcript linking | done | [story-03](./story-03-transcript-linking.md) | [evidence](./evidence-story-03.md) |
| HSM-8-04 | Artifact review + notebook closeout | done | [story-04](./story-04-artifact-review-closeout.md) | [evidence](./evidence-story-04.md) |
| HSM-8-05 | The air-gapped notetaker (fully-local, zero-connectivity) | backlog | [story-05](./story-05-air-gapped-notetaker.md) | — |
| HSM-8-06 | Ink into intelligence (the magic pencil, involved) | done | [story-06](./story-06-ink-into-intelligence.md) | [evidence](./evidence-story-06.md) |
| HSM-8-07 | Chunked extraction for long meetings (map-reduce, length-safe) | host-complete | [story-07](./story-07-chunked-extraction.md) | device proof deferred |
| HSM-8-08 | OOM-safe on-device budgeting (never gamble on RAM) | host-complete | [story-08](./story-08-oom-safe-budget.md) | device proof deferred |

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

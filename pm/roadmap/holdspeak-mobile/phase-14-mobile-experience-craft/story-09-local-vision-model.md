# HSM-14-09 — Local vision model (Gemma 3) seam + ambiguity resolution

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress (the `IVisionProvider` seam + the sketch ambiguity resolver are host-tested; the concrete VLM backings — on-device MLX Gemma 3 (Mode A) and a vision endpoint (Modes B/C) — are next)
- **Depends on:** HSM-14-08 (sketch engine), HSM-5 (the provider/Mode seam pattern)
- **Owner:** unassigned

## Vision (owner)

Bring a strong small local vision model — **Gemma 3 4B (4-bit)** — into the intelligence. It's
excellent at handwriting + diagram understanding, and it's the natural "ambiguity resolver"
for the strokes-first sketch→Mermaid path (HSM-14-08), plus a general image-understanding
capability (whiteboard photos, pasted screenshots).

## Architecture — the same Mode A/B/C seam as the text model

```
IVisionProvider  (describe(image, prompt) → text)
   ├── Mode A: on-device Gemma 3 4B via MLX-VLM (Apple Silicon, air-gapped)
   ├── Mode B: LAN endpoint (OpenAI-compatible vision)
   └── Mode C: cloud endpoint (OpenAI-compatible vision)
```

The Runtime Core depends on the seam, never a concrete model — so the VLM is swappable, and we
can prove the loop on an endpoint (Mode B/C) **today**, before the on-device MLX work.

## Scope

- **In (this story, host-tested):** the `IVisionProvider` seam (`describe(image:prompt:)`) in
  Providers, and `SketchVision` (RuntimeCore) — the **ambiguity resolver**: when the geometry
  is uncertain about a shape, ask the VLM ("rectangle, diamond, or ellipse?") and map its
  answer to a `ShapeKind`. The geometry stays the primary path; the VLM only resolves
  ambiguity (owner's Option-2 hybrid). Host-tested with a fake VLM.
- **Next (under this story):**
  (1) an **endpoint-backed** `IVisionProvider` (Mode B/C) — proves the loop on a real vision
  model now (the `.13` / a cloud VLM), wired as the sketch ambiguity fallback + a
  "describe this image" capability for pasted/whiteboard images;
  (2) the **on-device** `IVisionProvider` — Gemma 3 4B (4-bit) via **MLX-VLM** (mlx-swift),
  the air-gapped Mode A backing, behind the same seam (a separate SPM product so the domain
  never links the VLM runtime, mirroring `InferenceLlama`).
- **Out:** replacing the geometry with the VLM (Option 3 — rejected as fragile). Video. Cloud
  as the default (local-first stays the posture).

## Acceptance criteria

- [x] **The seam exists + the domain depends on it** — `IVisionProvider.describe(image:prompt:)`,
      and `SketchVision.resolveShape(image:using:)` maps a VLM answer to a `ShapeKind`,
      returning nil on an unusable answer (caller keeps the geometry guess). Host-tested.
- [ ] **Endpoint VLM (Mode B/C)** backs the seam and resolves a genuinely ambiguous sketch
      shape on a real vision model.
- [ ] **On-device Gemma 3 4B (MLX-VLM, Mode A)** backs the seam fully air-gapped, proven on
      the iPad.
- [ ] **General image understanding** — describe/extract from a pasted whiteboard photo via
      the same seam.

## Evidence

`Sources/Providers/Providers.swift` (`IVisionProvider`) + `Sources/RuntimeCore/Sketch/
SketchToMermaid.swift` (`SketchVision`) + `SketchToMermaidTests.swift`
(`swift test` → 211/0, +2: VLM resolves an ambiguous shape; answer parsing variants).

## Notes

- MLX-VLM (mlx-swift) is the right on-device VLM runtime on Apple Silicon (Gemma 3 / Qwen2.5-VL
  supported, Metal-accelerated). llama.cpp/LLM.swift vision (mmproj) support is newer/less
  exposed; keep the seam runtime-agnostic so either can back it.
- Prove the loop on an endpoint first (cheap, fast), then bring it on-device — same sequencing
  that worked for the text model (Modes B/C before Mode A).

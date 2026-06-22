# HSM-14-08 — The Pencil as a diagram language (sketch → Mermaid)

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress (the strokes→shapes→graph→Mermaid ENGINE is host-tested; live PencilKit preview + Vision text + VLM-for-ambiguity = next)
- **Depends on:** HSM-8-02 (PencilKit notebook), HSM-8-06 (on-device Vision)
- **Owner:** unassigned

## Vision (owner)

iPad + Apple Pencil changes the problem from "convert an image into Mermaid" to **"capture
intent while the user is drawing."** Strokes, not pixels: PencilKit gives vector geometry, so
recognize shapes deterministically, build a graph, emit Mermaid, and use a VLM/LLM **only for
ambiguity**. The magic: draw a box → it's recognized; draw an arrow → recognized; write a
label → it becomes a node title; **the Mermaid preview updates live.** The Pencil becomes a
diagram programming language; the user never thinks about Mermaid.

## Architecture (owner-chosen: Option 1 strokes-first + Option 2 hybrid for text/ambiguity)

```
PencilKit → ShapeRecognizer → DiagramBuilder → MermaidGenerator → live preview
                  ↑ Vision (handwriting → node text)
                  ↑ local VLM/LLM (ambiguity only: "is this a decision diamond?")
```

## Scope

- **In (this story, host-tested):** the pure engine in `RuntimeCore/Sketch/SketchToMermaid` —
  `ShapeRecognizer.classify(_:)` (a stroke → rectangle / diamond / ellipse via RDP simplify +
  sharp-corner analysis, or an open **connector** carrying its endpoints), `DiagramBuilder`
  (shapes + connectors → a graph; each connector → an edge between the nearest nodes),
  `MermaidGenerator.flowchart(_:)` (rect `["t"]`, diamond `{"t"}`, ellipse `(("t"))`, edges
  `a -->|label| b`). No CoreGraphics, no model, no device.
- **Next (under this story):** the **live PencilKit surface** — recognize each stroke as it's
  drawn, run **on-device Vision** per shape region for the node text (HSM-8-06 path), and a
  **live Mermaid preview** that updates stroke-by-stroke; the local VLM/LLM only to resolve a
  shape the geometry can't (diamond vs rectangle, a missed edge), never as the primary path.
- **Out:** cloud vision. Arbitrary diagram types beyond flowcharts (sequence/class later).
  Replacing geometry with a VLM (Option 3 — fragile, rejected).

## Acceptance criteria

- [x] **Stroke recognition (host-tested):** a drawn rectangle, diamond, and ellipse classify
      correctly; an open stroke is a connector carrying its start+end.
- [x] **Graph + Mermaid (host-tested):** connectors resolve to edges between nearest nodes
      (self-loops/no-node skipped); the owner's login-flow geometry emits the expected
      `flowchart TD` (Login → Validate{decision} →|yes| Home / →|no| Error).
- [x] **Live PencilKit surface (built + on device):** `SketchToDiagramView` — a PencilKit
      canvas drives `SketchModel`, which on each stroke (debounced, off-main) classifies via
      the engine, runs **on-device Vision** per shape region for the node label, builds the
      graph, and renders a **live native diagram** (`DiagramPreview`, Canvas) + the Mermaid
      code (copy/share). Short open strokes (handwriting) are filtered from connectors; the
      builder's self-loop skip drops in-node text. Front-and-center home entry. Device-built +
      deployed; owner verification of the live recognition is the remaining item.
- [ ] **Ambiguity only via the model:** the local VLM/LLM is invoked only when geometry is
      uncertain, with a measurable fallback path (the `SketchVision`/`IVisionProvider` hook
      from HSM-14-09 — wiring it to Gemma 4 / Qwythos is next).

## Evidence

`Sources/RuntimeCore/Sketch/SketchToMermaid.swift` + `SketchToMermaidTests.swift`
(`swift test` → 209/0, +6): rectangle/diamond/ellipse/connector recognition + the full
login-flow pipeline emitting the exact target Mermaid.

## Notes

- Recognition is RDP polyline simplification + sharp-corner counting (≈4 sharp corners at the
  bbox corners → rectangle, at the edge midpoints → diamond; gradual all round → ellipse).
  Deliberately simple + tunable; the model is the safety net, not the engine.
- This is the strokes-first foundation for the "magic pencil" — it makes the live, AI-optional
  diagram experience possible, and it's already correct + tested before any device work.

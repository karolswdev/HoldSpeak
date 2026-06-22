# HSM-14-15 — The Workbench (visual, user-defined intelligence builder)

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress — **engine foundation shipped + host-tested** (2026-06-22); the gamified
  visual canvas is the next build.
- **Depends on:** HSM-14 Settings (the configured `ILLMProvider` target), HSM-8-04 (artifact gen)
- **Owner:** unassigned

## Vision (owner)

> "Where is our workbench while we're in a meeting? Our own workflows that utilize the model and
> intelligence, with explicit builders that let us create user-defined intelligence — a visual
> builder with a basic set of logic. Gamified visual coding that lets us use intelligence in
> whichever way we have it configured. The most basic of builders, with ABSOLUTE CRUSHING USABILITY."

HoldSpeak's intelligence is fixed pipelines today (the lens picks types, the model drafts them). The
Workbench makes intelligence **user-programmable**: you compose your own workflows and run them on a
meeting, through whatever inference you've configured (on-device or your LAN box).

## The design — a linear pipeline, not a node graph (this is the usability bet)

A free-form node-and-wire graph is powerful and unusable on a tablet. The Workbench is instead a
**linear pipeline** that reads top-to-bottom and is impossible to wire wrong:

**SOURCE → STEP → STEP → … → OUTPUT**

- **Source** (one): Full transcript · Tacked moments (your HSM-8-03 marks) · Selected text.
- **Steps** (the "basic set of logic", tap from a palette, drag to reorder): **Lens** (a MIR
  profile that weights what to find) · **Extract** (a specific artifact type) · **Summarize** ·
  **Rewrite** (a tone) · **Keep if** (a keyword filter — the one branch/condition primitive).
- **Output** (one): Artifact cards · A note · Send to Slack (egress, shown plainly).

Every block is a Signal card with its glyph; the pipeline shows its plan as a sentence
("Full transcript → Lens · Delivery → Summarize → Artifact cards"). **Presets** ("Decisions &
owners", "What I flagged", "Exec summary → Slack", "Risks only") are the on-ramp — one tap to a
working pipeline, then tweak. Workflows are named, saved, and reusable.

**Running** reuses the generation theater: a Run button executes the pipeline through the configured
`ILLMProvider`, the produced-types constellation lights up as each step lands, results flow to the
chosen output. Egress outputs (Slack) ride the existing propose→approve→execute path.

## Engine (shipped this story)

`Sources/RuntimeCore/Workbench/Workflow.swift` — pure + Codable + host-tested
(`WorkflowTests`, 7): `WorkflowSource` / `WorkflowStep` (lens/extract/summarize/rewrite/keepIf) /
`WorkflowOutput` (with an `isEgress` flag) / `Workflow` (`isRunnable`, `plan`, `producedTypes`) and
`WorkflowPresets`. This is the model the canvas binds to and the runner executes. `swift test`
**240/6/0**.

## Acceptance criteria

- [x] **Engine** — a Codable workflow model (source + ordered steps + output), presets, a
      human-readable plan, derived produced-types, host-tested.
- [ ] **The canvas** — a Workbench screen (from the home) that builds a pipeline by tapping blocks
      from a palette and dragging to reorder, Signal depth throughout, crushing usability.
      Simulator-screenshot-proven.
- [ ] **Run it** — execute a workflow against a meeting through the configured `ILLMProvider`, with
      the generation-theater treatment; results land in the chosen output.
- [ ] **Persistence + presets** — workflows save and reload; presets are the one-tap on-ramp.
- [ ] **Egress honesty** — a Slack output shows the egress badge and rides propose→approve→execute.
- [ ] **In-meeting** — the Workbench is reachable mid-meeting (the owner's "while we're in a meeting").

## Build plan

1. **Engine** (done). 2. The pipeline **canvas** + block palette (Simulator-proven). 3. **Run**
wiring (reuse `generate()`'s provider + theater). 4. **Persistence** + presets surfaced. 5. In-meeting
entry + egress honesty + polish.

## Notes

- Linearity is the deliberate usability choice; a richer branch/graph mode is a later option, not v1.
- Reuses Settings' `InferenceConfigStore` (runs through on-device OR the LAN endpoint, the user's call).

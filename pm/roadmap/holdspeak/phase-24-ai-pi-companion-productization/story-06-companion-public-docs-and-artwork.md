# HS-24-06 — Companion Public Docs and PixelLab Artwork

- **Project:** holdspeak
- **Phase:** 24
- **Status:** done
- **Opened:** 2026-06-01
- **Closed:** 2026-06-01
- **Depends on:** HS-24-01, HS-24-02
- **Unblocks:** public companion onboarding, Phase 15 out-and-about positioning
- **Owner:** Codex
- **Evidence:** [evidence-story-06.md](./evidence-story-06.md)

## Problem

Phase 24 made the AI PI companion operable in the product, but the public docs
still under-explained what the companion is and why it matters. The README and
user docs did not make the physical loop obvious: portable ESPHome device,
meeting capture/status, Claude/Codex waiting notifications, spoken replies back
into active coding sessions, and controlled-network remote operation.

The docs also needed visual support that renders cleanly in GitHub dark mode.
The checked-in product photo had a hard white background, and the first README
pass duplicated the PixelLab spot art immediately under `Workflow Map`.

## Outcome

The README, User Guide, Getting Started guide, and AIPI-Lite workflow now carry a
coherent public explanation of the companion loop. PixelLab-generated transparent
PNG assets provide the workflow art and the AIPI-style companion image, with
object IDs and prompts recorded for provenance.

## Scope

### In

- Add PixelLab-generated transparent PNG artwork for:
  - hold-to-talk voice typing
  - meeting intelligence/action review
  - project-aware typing
  - AIPI-Lite-style companion hardware
- Add a README workflow map using the three spot illustrations.
- Replace the non-transparent AIPI product photo in docs with the generated
  transparent companion artwork.
- Clarify `clipboard` as a replacement token inside dictated text, including a
  code-block example.
- Document AIPI-Lite as:
  - portable ESPHome-based companion hardware
  - meeting capture controls and status feedback
  - Claude/Codex waiting-session notifier
  - spoken-reply path back into selected coding sessions
  - remote-capable only when the user controls the network path
- Add official product and Amazon purchase links.
- Record PixelLab object IDs and prompts in `docs/assets/pixellab/README.md`.

### Out

- Firmware or bridge behavior changes.
- New `/companion` API behavior.
- Cross-network tunneling implementation.
- Animated GIF generation for the intelligence pipeline.
- New plugin-runtime functionality.

## Acceptance Criteria

- [x] README shows the workflow art without the redundant centered image strip.
- [x] README and AIPI-Lite workflow use a transparent PNG companion image, not
      the hard-background JPG.
- [x] User-facing docs explain `clipboard` replacement clearly.
- [x] Public docs explain the agent-waiting / spoken-reply AIPI use case.
- [x] Hardware links are present and current as of 2026-06-01.
- [x] PixelLab provenance is recorded for all generated assets.
- [x] Evidence records the commits and local verification commands.

## Closeout

Implemented across four commits on 2026-06-01:

- `11af81b` — PixelLab documentation artwork
- `010a3ea` — docs artwork cleanup and clipboard token clarification
- `a7fe78b` — transparent AIPI companion artwork
- `a720af0` — AIPI agent companion use case and hardware links

See [evidence-story-06.md](./evidence-story-06.md).

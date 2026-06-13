# Phase 66 — The Architecture Map

**Status:** scaffolded (0/4). Opened 2026-06-13 on owner direction (a
dedicated phase for pipeline architecture and Mermaid diagrams). There is
no system-overview doc today and three Mermaid blocks in the whole corpus;
this builds the map a developer hits first, with diagrams that render and a
guard that keeps them rendering.

**Last updated:** 2026-06-13 (scaffolded — verified: no top-level
architecture doc; the two internal ARCHITECTURE_* docs are module-structure
not data-flow; mermaid renders natively on GitHub; mmdc 11.15.0 available
via npx for a real render guard.)

## The thesis — why this phase

POSITIONING fixes the audience as developers who will read the code. The
fastest way to lose that reader is to make them reconstruct the runtime
from scratch across ten RFCs and two decomposition docs. One architecture
map, with diagrams of the two pipelines and the trust boundary, is the
contributor on-ramp the repo never had, and it is launch-timely.

## Goal

`docs/ARCHITECTURE.md`: an orienting overview, a top-level component
diagram, the dictation pipeline, the meeting pipeline, and the trust/egress
boundary, all in Mermaid that renders on GitHub and is kept rendering by a
guard, every diagram traced against the shipped code, wired into the docs
index, CONTRIBUTING, and a README pointer.

## Scope

- **In:** the system map + the render guard (HS-66-01); the dictation
  pipeline diagrams (HS-66-02); the meeting pipeline + trust-boundary
  diagrams (HS-66-03); closeout with render re-verification + index/README
  wiring (HS-66-04).
- **Out:** any behavior change; rewriting the existing guides' content
  (only link to the map); the Astro-site Mermaid rendering question beyond
  a check + an honest note; new RFCs.

## Exit criteria (evidence required)

- Every Mermaid block parses/renders (verified) and the guard enforces it;
  GitHub-render confirmed by eye. (HS-66-01, HS-66-04)
- The dictation and meeting pipelines and the trust boundary are each
  diagrammed and traced against real modules (no stale names). (HS-66-02/03)
- Docs index + CONTRIBUTING + README point at the map; voice guard + full
  suite green; final-summary. (HS-66-04)

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-66-01 | The system map + the diagram render guard | backlog | none |
| HS-66-02 | The dictation pipeline, diagrammed | backlog | HS-66-01 |
| HS-66-03 | The meeting pipeline + the trust boundary, diagrammed | backlog | HS-66-01 |
| HS-66-04 | Closeout: render re-verify + wiring + final-summary | backlog | HS-66-01..03 |

## Where we are

Scaffolded. Next is **HS-66-01 — the system map + the diagram render guard**.

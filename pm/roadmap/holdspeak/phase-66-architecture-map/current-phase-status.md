# Phase 66 — The Architecture Map

**Status:** CLOSED (4/4). Opened 2026-06-13 on owner direction (a
dedicated phase for pipeline architecture and Mermaid diagrams). There is
no system-overview doc today and three Mermaid blocks in the whole corpus;
this builds the map a developer hits first, with diagrams that render and a
guard that keeps them rendering.

**Last updated:** 2026-06-13 (**HS-66-04 done — phase CLOSED 4/4:** all six
diagrams re-verified to render (the device sequence's agent-reply alt branch
included); the map wired into the README ("how it works, with diagrams")
and CONTRIBUTING (the runtime view; the two structure docs beneath it).
Final suite **2779 passed, 17 skipped**; see [final-summary.md](./final-summary.md);
PR merged on green. Prior: **HS-66-03 done:** two more diagrams — the
meeting pipeline (capture/import -> windowed transcribe -> routing -> plugin
host -> artifacts -> aftercare -> the two approve-gated proposals) and the
trust boundary (a "Your machine" box with all seven egress crossings drawn
out and labeled by their gate, checked one-to-one against SECURITY's egress
table). Render guard green (6 blocks); trust boundary eyeballed. Prior:
**HS-66-02 done:** the dictation section gains
three diagrams traced against the code: the end-to-end flow (entries ->
transcribe -> voice-command branch -> the opt-in stages intent-router/
project-rewriter/kb-enricher -> the wake preview-default fork -> type ->
journal), the learning loop (journal -> correct -> memory -> replay), and a
sequence diagram of the ESP32-S3 device path with the agent-reply branch.
Render guard green (4 blocks); dictation flow eyeballed. Prior: **HS-66-01
done:** `docs/ARCHITECTURE.md` is
born with the orienting overview + the top-level component diagram (traced
against the shipped post-decomposition modules, rendered + eyeballed), and
the Mermaid render guard (`tests/e2e/test_mermaid_renders.py`, mmdc-backed,
CI-skippable) is proven both ways. The voice guard caught HS-ID
placeholders leaking into the user-facing doc; rewritten as product-tense
section intros. Docs index gained an "Understand the system" pointer.
Suite **2779 passed, 17 skipped** (+2). Earlier: scaffolded — verified: no top-level
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
| HS-66-01 | The system map + the diagram render guard | done | none |
| HS-66-02 | The dictation pipeline, diagrammed | done | HS-66-01 |
| HS-66-03 | The meeting pipeline + the trust boundary, diagrammed | done | HS-66-01 |
| HS-66-04 | Closeout: render re-verify + wiring + final-summary | done | HS-66-01..03 |

## Where we are

CLOSED 4/4. docs/ARCHITECTURE.md has the system map, both pipelines, and
the trust boundary, all rendering and guard-protected, wired into the
index/README/CONTRIBUTING. See [final-summary.md](./final-summary.md).

# HS-66-01 — The system map + the diagram render guard

- **Project:** holdspeak
- **Phase:** 66
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-66-02, HS-66-03, HS-66-04
- **Owner:** unassigned

## Problem
There is no single doc that orients a developer to how HoldSpeak's pieces
fit, and nothing stops a broken Mermaid diagram from shipping.

## Scope
- **In:** `docs/ARCHITECTURE.md` with a short overview and the top-level
  component diagram (web runtime, transcriber, dictation pipeline, meeting
  session, plugin host + router, actuator executor + gated connectors,
  device bridge, presence/Qlippy, SQLite DB, and how they connect). A
  render guard that extracts every ```mermaid block across the docs and
  asserts each parses/renders (mmdc or equivalent; CI-skippable like the
  route pre-flight, green locally). A first docs-index pointer. Verify the
  diagrams render on GitHub by eye.
- **Out:** the pipeline-detail diagrams (HS-66-02/03).

## Acceptance criteria
- [ ] `docs/ARCHITECTURE.md` exists with the overview + the component
      diagram, traced against real module names.
- [ ] The guard fails on a deliberately broken block and passes on the
      shipped ones (both proven); CI-skip-clean.
- [ ] GitHub render confirmed; voice guard + full suite green.

## Test plan
- The render guard both ways; the doc guard; the full suite.

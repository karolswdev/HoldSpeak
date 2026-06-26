# HSM-15-07 — Docs: the Mesh, end to end

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** backlog (the dedicated docs story — after the features, before closeout)
- **Depends on:** HSM-15-01…05 (documents shipped behavior only).
- **Owner:** unassigned

## Why

Per the standing rule, every phase gets its own documentation story, and feature docs must touch the
**entry points**, not just deep internal files. The Mesh introduces concepts a new reader needs to
find: pairing your devices, dictating into your Mac, RUNS-ON-the-mesh, the mesh queue, and the one
approval/egress contract.

## The deliverable

- **README / two-modes tour** — extend the "one copilot, two modes" surface to name the mesh: the
  desktop hub + mobile companions, two modes on every surface, fluid compute, one queue, one approval
  contract. Air-gappable, private by default.
- **Mobile docs / GETTING_STARTED** — how to pair the iPad to the desktop server; how to dictate into
  your Mac; how to set a Workbench node to run on the Mac; where the queue lives and how approvals
  work.
- **POSITIONING alignment** — confirm the mesh language fits the canon (honest, named comparisons, the
  egress badge not prose). No new privacy novels; the air-gapped proof is shown, not narrated.
- **Architecture note** — a short addition to the mesh seam (`HTTPDesktopClient` routes:
  `/api/dictation/remote`, `/api/companion/*`, queue/actuator status) so the next agent sees the
  backbone at a glance.

## Acceptance criteria

- [ ] README two-modes tour names the mesh (devices, modes-everywhere, fluid compute, one queue, one
      approval) — POSITIONING-aligned, no prose novels.
- [ ] Mobile getting-started covers pairing + dictation-into-your-Mac + RUNS-ON-mesh + the queue +
      approvals.
- [ ] The mesh seam (routes) is documented for the next agent.
- [ ] Voice guard passes (no banned prose-dashes/AI-vocab/HS-IDs in the shipped docs/README).

## Notes

- Documents **shipped** behavior only — if a surface didn't land, it isn't documented.
- Lesson carried from Phase 64: feature-docs stories must update the **entry points**, not only deep
  files.

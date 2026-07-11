# HS-91-08 — Studio and support surfaces in React

- **Project:** holdspeak
- **Phase:** 91
- **Status:** done
- **Depends on:** HS-91-01, HS-91-02
- **Unblocks:** HS-91-09
- **Owner:** unassigned

## Problem

Workbench, Companion, Studio, Presence, and local docs are smaller routes but
include custom canvas, disclosure, HUD, and navigation behavior. Leaving them
behind would preserve Astro as a permanent second framework.

## Scope

- In: React `/workbench`, `/companion`, `/studio`, `/presence`, and
  `/docs/dictation-runtime`; Workbench graph interactions; companion status and
  connection guidance; Studio information architecture; Presence frames; docs
  rendering; shared shell navigation for these routes.
- Out: graph/runtime feature expansion; external documentation-site migration;
  native HUD implementation.

## Acceptance criteria

- [x] Every support-route ledger row passes and all canonical deep links render
      inside the one React shell (Presence may use a minimal shell mode).
- [x] Workbench model/canvas logic becomes typed React hooks/components with no
      `innerHTML` or selector-owned state; pan/zoom/drag/wire behavior survives.
- [x] Studio navigation and Companion disclosures use shared accessible React
      components and DeskOS-aligned hierarchy.
- [x] Presence subscribes through the shared runtime provider and cleans up
      correctly in HUD mode.
- [x] Old Astro/pages/scripts for this cohort are deleted.

## Test plan

- Unit: Workbench graph/model and Presence frame tests.
- Integration: Playwright Workbench drag/wire/fit, Companion disclosure, Studio
  navigation, Presence frame and docs deep-link flows.
- Manual / device: compare Workbench and Presence with their actual DeskOS
  counterparts where one exists; record intentional platform differences.

## Notes / open questions

Local docs may render from React-owned structured content or checked-in
Markdown; they may not retain Astro solely as a Markdown renderer.

# HS-93-01 — Three obvious starts

- **Project:** holdspeak
- **Phase:** 93
- **Status:** done
- **Depends on:** HS-91-10
- **Unblocks:** HS-93-02, HS-93-03, HS-93-04
- **Owner:** unassigned

## Problem

The Web shell exposes nine primary destinations and the Desk exposes five create
nouns at once. The product is capable, but its first glance asks the user to
understand its architecture before acting.

## Scope

- **In:** Capture a production before baseline; reduce global Web navigation to
  Desk, Dictation, Meetings, Studio, and Settings or fewer; present Dictate,
  Record, and Create as the three obvious fresh-Desk starts; replace five
  permanent create chips with one progressively disclosed creation entry;
  establish the Desk tool shelf/search/context doors through which advanced
  capability remains discoverable and operable; preserve deep links, keyboard
  access, and Desk delight; align the flagship native arrival hierarchy without
  forcing identical layout.
- **Out:** Removing advanced tools, making Studio the real advanced product,
  inventing a new home, or hiding actions in an unlabeled command palette.
- **Paths:** `web/src/components/AppShell.tsx`, `web/src/desk/components/DeskChrome.tsx`,
  `web/src/desk/components/EmptyDesk.tsx`, `web/src/pages/StudioPage.tsx`,
  `apple/App/MeetingCaptureApp.swift`, `apple/App/MeetingCapture/DeskHome.swift`,
  `apple/App/MeetingCapture/DeskDioramaStage.swift`, navigation/Desk tests, and
  UAT arrival scenarios.

## Acceptance criteria

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the story closes at its machine-verifiable scope; the owner first-glance
walks and physical iPhone/iPad VoiceOver evidence move verbatim to
[BACKLOG candidate Y](../BACKLOG.md) and are not claimed here.

Accepted at the delivered scope:

- [x] Before evidence records the prior navigation and five create controls
      (HS-93-01 progress record captures); the owner first-glance narration
      itself is candidate-Y scope.
- [x] A fresh Desk makes Dictate, Record, and Create identifiable without
      opening Settings or Studio; one Create entry progressively reveals Note,
      Zone, Knowledge, Persona, and Workflow with short task-oriented copy
      (production captures + keyboard walk evidence).
- [x] Arrival, navigation, Create, and empty-state copy passes the controlled
      product-copy census with zero violations.
- [x] Web primary navigation contains five destinations; Activity, Commands,
      Cadence, Workbench, Runs on, and the other power tools are discoverable
      and operable through the Desk Tools shelf/search; every served HTML
      route passes the repaired bounded route preflight (19 routes, zero
      uncaught page errors) so existing deep links stay valid.
- [x] The flagship Swift root presents the same three daily starts with no
      competing dashboard (simulator-verified; physical walks are
      candidate-Y scope).
- [x] Keyboard-only Web reaches Create, the Tools shelf, Desk items, and Desk
      memory without hover, drag, or memorized gestures — proven by the
      production keyboard walk (which surfaced and fixed a real missing
      arrow-key path in the Tools shelf); native VoiceOver walks are
      candidate-Y scope.
- [x] After evidence records control counts and route discovery through the
      production evidence runners; the owner first-glance explanation is
      candidate-Y scope.
- [x] The Desk demonstrates the reusable selection, context-action,
      inspector/window (the Phase-93 desk-window contract), tool-shelf/search,
      live-status, and attention/receipt affordances later stories extend.

## Test plan

- **Unit:** Web route/navigation/Create-menu tests and Swift accessibility/action
  tests; `cd web && npm run check`; `cd apple && swift test`.
- **Integration:** canonical deep-link FastAPI tests, route-preflight tests, and
  updated arrival UAT protocol for Web/Swift production targets.
- **Manual / device:** Before/after desktop, compact Web, physical iPhone, and
  physical iPad first-glance walk; locate each moved advanced tool without using
  repository knowledge.

## Notes / open questions

Count reduction is not success if labels become vague or capability becomes
undiscoverable. Preserve direct URLs and automation entry points. The Desk's
surface may be visually calm while remaining functionally rich through stable,
learnable OS affordances.

Bundling note: this initial Phase-93 scaffold is intentionally committed with
the HS-93-01 through HS-93-05 in-progress implementation slices because the
owner directed that the complete shared working tree ship together. No story is
marked done; each closure gate remains independent.

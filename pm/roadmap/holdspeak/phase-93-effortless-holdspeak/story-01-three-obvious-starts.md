# HS-93-01 — Three obvious starts

- **Project:** holdspeak
- **Phase:** 93
- **Status:** in progress — implementation verified; owner/physical evidence pending
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

- [ ] Before evidence records the current navigation, five create controls, and
      an owner first-glance explanation on the exact production builds.
- [ ] A fresh Desk makes Dictate, Record, and Create identifiable without
      opening Settings or Studio; one Create entry progressively reveals Note,
      Zone, Knowledge, Persona, and Workflow with short task-oriented copy.
- [ ] Arrival, navigation, Create, and empty-state copy follows
      `copy-contract.md`: no positioning pitch, platform story, congratulations,
      or architecture lesson precedes the next useful action.
- [ ] Web primary navigation contains no more than five destinations; Activity,
      Commands, Cadence, Workbench, Runs on, and other power tools remain
      discoverable and operable through Desk tools, selection/context, status,
      or search; Studio provides deep authoring/configuration and every existing
      deep link remains valid.
- [ ] The flagship Swift root presents the same three daily starts and no
      competing dashboard/home concept, using platform-native hierarchy.
- [ ] Keyboard, VoiceOver, compact Web, iPhone, and iPad can reach every moved
      action without hover, long press, drag, or memorized gestures.
- [ ] After evidence records control counts, route discovery, and an owner
      first-glance explanation; a failure to find an existing tool blocks the
      story rather than restoring permanent clutter silently.
- [ ] The resulting Desk demonstrates at least the reusable selection,
      context-menu/action, inspector/window, tool-shelf/search, live-status, and
      attention/receipt affordances that later stories extend; no feature needs
      a private interaction grammar merely to remain powerful.

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

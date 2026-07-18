# HS-95-07 — Configuration through the desk

- **Project:** holdspeak
- **Phase:** 95
- **Status:** backlog
- **Depends on:** HS-95-02, HS-95-04
- **Unblocks:** HS-95-08

## Problem

Every act of configuring HoldSpeak ejects the user: Settings, Profiles
("Runs on"), Integrations, Commands, and Cadence are five flat pages, and
the desk's own inspector — the surface that *shows* a tool's state
in-world — links out the moment you want to change anything
(DeskToolInspector → `/settings`, `/profiles`, `/dictation`). The
tool shelf is a launcher for leaving the desk. The standing rule is
edit-in-world; configuration is where it is most broken.

## Scope

- In:
  - cores per the HS-95-04 pattern for SettingsPage, ProfilesPage,
    CommandsPage (proof core from HS-95-04 re-used), CadencePage, and the
    settings-integrations section, each hosted in a desk window;
  - the DeskToolShelf rewired: every tool opens its window in place
    (workflow editor and personas land in HS-95-08; this story converts the
    shelf mechanism plus the five configuration destinations);
  - DeskToolInspector completes: its edit affordances open the scoped
    window section (e.g. one integration's settings) instead of linking
    out — inspect and edit become one in-world flow;
  - FirstWords onboarding links (`/setup`, `/profiles`) open windows;
  - flat routes kept as wrappers for deep links.
- Out:
  - settings semantics, schema, or hub config routes (render-only);
  - the guided `/welcome` wizard (immersive already, untouched);
  - StudioPage, WorkbenchPage, CompanionPage, ActivityPage shelf entries
    beyond mechanism conversion (content lands in HS-95-08).

## Acceptance criteria

- [ ] Settings, Runs on, Integrations, Commands, and Cadence each open as
      desk windows with full flat-page capability; a real setting change
      round-trips to the hub from inside a window.
- [ ] DeskToolInspector edit affordances open the scoped window (the
      integration case lands on that integration, not the settings root);
      the inspector itself never navigates.
- [ ] The tool shelf opens windows for all five configuration
      destinations; its remaining entries dispatch through the same
      mechanism even where the destination window arrives in HS-95-08.
- [ ] FirstWords opens setup and profiles in-world.
- [ ] No desk surface links to `/settings`, `/profiles`, `/commands`,
      `/cadence`, or `/setup` (grep-verified across `web/src/desk/`).
- [ ] Egress badges and trust affordances render identically in-window
      (the badge, never prose — standing rule).
- [ ] Every text input in the re-homed cores keeps its speak-to-fill mic
      (standing rule), and the windows behave as shell citizens at 1440
      and 393.

## Test plan

- `npm --prefix web test` — core-mount tests per surface; inspector
  scoped-open tests.
- Playwright: change a setting, switch a profile, and edit an integration
  entirely in-world against the real hub; assert persistence after reload;
  both viewports.
- Screenshot pass: each configuration window, plus the inspector-to-window
  flow.

## Implementation direction

- Scoped opens ride the HS-95-04 context prop (section/subject), reusing
  the `subject` vocabulary the shelf already encodes
  (`integration:destinations`).
- Do not build a settings tree inside the desk store; cores keep their
  fetch-render autonomy.
- The shelf becomes a pure dispatcher: one table, action → window id +
  scope. Its search stays.
- Where a form is small (a single toggle the inspector exposes), prefer
  inline in-inspector editing over opening the full window — fewest-moves
  rule; the window is for the full surface.

## Evidence required

- captured test runs;
- Playwright in-world configuration walk output (with the hub round-trip
  shown);
- screenshots of the five windows and the inspector scoped-open flow;
- the grep sweep output for the five routes across `web/src/desk/`.

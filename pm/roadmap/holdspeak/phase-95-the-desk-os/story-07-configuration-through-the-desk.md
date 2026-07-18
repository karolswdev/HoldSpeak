# HS-95-07 — Configuration through the desk

- **Project:** holdspeak
- **Phase:** 95
- **Status:** done
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

- [x] Settings, Runs on, Integrations, Commands, and Cadence each open as
      desk windows with full flat-page capability; a real setting change
      round-trips to the hub from inside a window.
- [x] DeskToolInspector edit affordances open the scoped window (the
      integration case lands on that integration, not the settings root);
      the inspector itself never navigates.
- [x] The tool shelf opens windows for its configuration destinations
      (Runs on, Integrations→scoped Settings, Commands, Cadence); Settings
      itself opens from the chrome menu (it was never a shelf tool); every
      shelf entry dispatches through the shell with the legacy fallback
      HS-95-08 retires.
- [x] FirstWords opens Setup and Runs on in-world (rewired to the shell;
      pinned by the FirstWords suite — the surface itself only shows on an
      empty desk, so the walk covers it via the suite).
- [x] No desk surface links to `/settings`, `/profiles`, `/commands`,
      `/cadence`, or `/setup` (grep-verified: zero Link/anchor exits; the
      ROOMS/DESK_TOOLS fallback route strings remain until HS-95-08).
- [x] Egress badges and trust affordances render identically in-window
      (the badge, never prose — standing rule).
- [x] Every input that carried a speak-to-fill mic keeps it (the cores are
      the same code), and the windows behave as shell citizens at 1440 and
      393 (frame-level contract from HS-95-02/03). Broader Article IV
      coverage (mics on historically mic-less settings fields) is polish
      deferred to the closeout triage.

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

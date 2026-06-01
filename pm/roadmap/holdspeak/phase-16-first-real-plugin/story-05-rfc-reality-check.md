# HS-16-05 — RFC reality-check + phase exit (DoD, calibration, final summary)

- **Project:** holdspeak
- **Phase:** 16
- **Status:** done
- **Depends on:** HS-16-01, HS-16-02, HS-16-03, HS-16-04
- **Unblocks:** none (phase exit)
- **Owner:** unassigned

## Problem

`docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` is the parent RFC for the
plugin system. As of phase-16's start it is partially fictional:
its §"Initial Built-In Plugins (Phase 1)" lists five plugins as if
they exist, when only the registration ID and routing wiring exists
— the actual `run()` for all twelve plugins in
`holdspeak/plugins/builtin.py` is a `DeterministicPlugin` stub
returning a transcript snippet.

After HS-16-01..04 ship, exactly one plugin (`mermaid_architecture`)
is real. This story closes the phase by:

1. Updating the RFC so it stops claiming what isn't true.
2. Collecting calibration data on the `mermaid_architecture`
   plugin's parse-failure rate across local + cloud LLMs, so phase
   17 has a baseline for "is this pattern worth replicating?".
3. Writing the phase's `final-summary.md`.
4. Updating the project README and operating cadence.

## Scope

- **In:**
  - Edit `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`:
    - In §"Initial Built-In Plugins (Phase 1)", annotate each
      entry: `mermaid_architecture` → ✅ shipped (phase 16, this
      commit); the other four (`requirements_extractor`,
      `adr_drafter`, `risk_register`, `action_owner_enforcer`) →
      ⚠️ stub (`DeterministicPlugin`).
    - In §"Plugin Taxonomy" / "Initial Built-In Plugins", add a
      new short subsection
      "**Reality status (2026-05-08):**" listing the full
      thirteen `_BUILTIN_PLUGIN_DEFS` entries with shipped/stub
      status and a one-liner per stub (what its real
      implementation should produce).
    - Add a new appendix
      "**Appendix A — What 'shipped' means in this RFC:** A real
      plugin (1) implements the `HostPlugin` Protocol with a
      non-stub `run()`, (2) calls a real downstream
      (LLM / database / external API) where the RFC implies one,
      (3) returns a structured payload that the synthesis layer
      knows how to render, and (4) ships with unit + integration
      tests covering success, failure, and capability-blocked
      paths. Phase 16's `mermaid_architecture` is the first
      plugin that meets all four bars."
  - Run a calibration pass on `mermaid_architecture`:
    - Pick three test transcripts of varying architecture
      density (one architecture-heavy meeting, one mixed, one
      low-architecture-content). Use existing test fixtures or
      hand-craft.
    - Run the plugin against each transcript on three configurations:
      (a) cloud (e.g., `gpt-5-mini`), (b) a local 7B model, and
      (c) a local 9B+ model — whatever's available on the dev
      machine. If any of (b)/(c) are unavailable, document the
      gap; do not block the phase on hardware not present.
    - Record per-config: parse-success rate, parse-failure rate,
      average runtime, average `confidence_hint`. Land the table
      in `final-summary.md`.
  - Write
    `pm/roadmap/holdspeak/phase-16-first-real-plugin/final-summary.md`
    per `pm/roadmap/roadmap-builder.md` §2.5. Required:
    - phase open / close dates, chunks shipped count
    - "goal — was it met" against the original goal text
    - exit-criteria checklist re-run against evidence files
    - stories shipped table
    - stories cut / deferred (probably none for this phase)
    - "Surprises and lessons" — what the calibration pass
      revealed; what would change if we did it again
    - "Handoff to phase 17" — what's now possible (the pattern
      proven), what changed in canon (RFC reality-check), what
      the next phase should read first
    - final asset / test posture (LOC added, test count delta)
  - Update `pm/roadmap/holdspeak/README.md`:
    - "Last updated" to phase-16 close date.
    - Phase index row for phase 16: status → done.
    - "Current phase" pointer → next planned phase (still phase
      15 if it hasn't started, or phase 17 if 15 has shipped in
      between).
  - Freeze `current-phase-status.md` per PMO §3 — append a
    closing line "**Phase closed:** {date}. See
    [final-summary.md]." File becomes immutable.

- **Out:**
  - Real `run()` for any other plugin. Phase 17.
  - SDK / external-plugin loader. Phase 4 in the RFC.
  - Live-meeting hooks. Deferred decision per
    `current-phase-status.md`.
  - Anything that would re-open phase 14 or pre-empt phase 15.

## Acceptance criteria

- [x] `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` annotates all
  thirteen built-in plugins with shipped/stub status (reality-status
  table) and contains the new "Appendix A".
- [x] `final-summary.md` exists in the phase folder; conforms to
  the §2.5 template; contains the calibration table (two local
  configs populated; cloud documented as untested).
- [x] `pm/roadmap/holdspeak/README.md` "Last updated" reflects
  this commit's date; phase 16's row reads `done`.
- [x] `current-phase-status.md` has a closing line and is no
  longer edited after this commit.
- [x] Every exit-criterion in `current-phase-status.md` is checked
  (see `final-summary.md` exit-criteria re-run).
- [x] No regressions: full sweep
  `uv run pytest -q --ignore=tests/e2e/test_metal.py` green (1902 passed).

## Test plan

- Tests: no new test code in this story; verifies that the test
  posture established by HS-16-01..04 holds.
  Sweep:
  `uv run pytest -q --ignore=tests/e2e/test_metal.py`. Record
  the count delta in `final-summary.md`.
- Calibration: scripted run of the plugin against three
  transcripts × up to three configurations. Save stdout to
  `pm/roadmap/holdspeak/phase-16-first-real-plugin/evidence/calibration.txt`
  and reference it from `final-summary.md`.
- Manual: re-open the rendered diagrams from HS-16-04 to
  confirm nothing regressed during the doc / summary edits.

## Notes / open questions

- The calibration pass is intentionally narrow. We are not
  picking a winning model in this story; we are establishing
  whether `mermaid_architecture` is good enough on common local
  configs to recommend, and where the cliff is (e.g., "below
  9B parameters, parse-failure rate exceeds 40% — don't ship
  this in default-on configurations on smaller models").
- If the calibration reveals that the plugin is unusable on
  every available config, do not flip the RFC entry to ✅ —
  flip it to ⚠️ shipped-but-quality-blocked, document the
  finding, and let phase 17's plan address it. The phase still
  closes; the substrate is proven; the demo just needs cloud.
- The "Current phase" pointer update assumes phase 15 hasn't
  shipped meanwhile. If phase 15 has, point to phase 17 (or
  whatever's next). The pointer always points to the lowest
  non-done phase per `roadmap-builder.md` §5.5.

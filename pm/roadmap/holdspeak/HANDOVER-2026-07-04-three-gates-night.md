# Handover — 2026-07-04 (overnight) — the three-gates night

One evening session, owner-steered twice ("where else can we add value today?"):
**Phase 19 (iPad meeting contracts) opened and built to 6/7**, then **Phase 21
(Honest everywhere) opened and built to 4/5** — thirteen PRs merged (#223–#235).
Three phases now wait on ONE owner couch session. This is the map: what shipped,
the one process failure, what remains, the traps.

## Where main stands

- **Merged tonight:** #223 (P19 open + 19-04), #224 (19-01 file-issue), #225
  (19-05 proposals queue), #226 (19-02 facets), #227 (19-06 learning reader),
  #228 (19-03 import), #229 (19-07 docs+walk), #230 (P21 open), #231 (21-01
  egress contract), #232 (21-02 Swift guard), #233 (21-03 readiness truth —
  **merged red, see below**), #234 (21-04 trust chip + the healing manifest),
  #235 (21-05 docs+rider + the ledger note). Main is green at `ceeee6b`.
- **Suites at last runs:** `swift test` **432 / 8 skipped / 0 failures** (+7
  tonight: EgressScope, SetupStatus); doc drift guard **18/18** (+3 Swift-scan
  tests); per-PR CI green throughout (except the #233 incident).
- Working tree clean; only the pre-existing untracked
  `dogfood/repos/questline/src/lib/` remains.

## The one process failure (read this)

**PR #233 was merged with two RED checks.** The HS-72-02 route-surface lock
fired (a new `api/desk/actuators/status` Swift consumer landed without
regenerating `docs/api-surface.json`) and the merge was CHAINED after the CI
watch instead of gated on the conclusion — the exact trap the two-track
handover names. Healed same-hour: the regenerated manifest rode #234
(`test_api_surface` 5/5), noted on #233, recorded in the Phase-21 ledger.
**Standing rule, now also in memory:** watch → read the conclusion JSON →
merge are three separate calls; never `… && gh pr merge`. And regenerate
`gen_api_surface.py` in the same commit whenever `HTTPDesktopClient` or
`DeskHostLink` gains a route.

## Track 1 — Phase 19, the iPad joins the meeting contracts (6/7, gate staged)

Survey-corrected on open: the ENTIRE client layer had already merged
(Equilibrium Waves 3–6), so the phase was screens over shipped clients in
`CompanionShellApp.swift`. Every story proven against a live scratch hub
rendered by the connected simulator (never seeds):

| Story | The one line |
|---|---|
| 19-04 | Confidence ring + sources — was already wired; flipped on verified evidence |
| 19-01 | Accepted-only **File issue** chip + inline repo row + honest `proposed` pill (live: proposed / idempotent / 400) |
| 19-05 | The four-state proposals queue + slack cloud mark; the live proof caught iPad decisions logging as `web-user` — fixed, `decided_by: "ipad-companion"`, body-test-locked |
| 19-02 | Search + facet chips, narrowed server-side; a REAL narrowed render via `HS_SHELL_FACET_SPEAKER` (same code path as the chips) |
| 19-06 | The LEARNED card on Dictate (digest chips, correction reach, journal signals; honest no-reach edge rendered) |
| 19-03 | **Import file** picker; the running app itself uploaded a `.vtt` end to end, its speakers feeding the facet chips on the same screen |
| 19-07 | Docs done; [`HSM-19-07-WALK.md`](../holdspeak-mobile/phase-19-ipad-meeting-contracts/HSM-19-07-WALK.md) staged (W1–W6) |

## Track 2 — Phase 21, Honest everywhere (4/5, gate staged)

Opened the same evening its precondition cleared (the 18/19 surfaces exist).
The survey caught fresh mixed-as-local drift in the evening's OWN new shell
chips — the phase's best argument for itself:

| Story | The one line |
|---|---|
| 21-01 | `EgressScope` (local/mixed/cloud) in Contracts + `DeskPrimitive.egress` (protocol requirement — the glyph dispatch rule); the hard-coded "On device" pull-out capsule is DEAD (connectors wear `Cloud · <name>`); mesh text + shell chips consume the one grammar |
| 21-02 | Seven "nothing leaves" labels → badge grammar; the guard scans Apple string literals (comments legal) — **its first run caught the 7th site the survey missed** |
| 21-03 | GitHub readiness truth: paired vs configured are separate truths off the live HS-77-03 status route; act sheet lists only completable sends; control-vs-treatment on one hub, repo flipped mid-run |
| 21-04 | The trust chip reaches the iPad: `SetupStatus.posture` mirrors `trust-view.js` precedence (test-locked); proven two surfaces × two postures on one hub (web chip via Playwright, same words) |
| 21-05 | Docs done; [`HSM-21-WALK-RIDER.md`](../holdspeak-mobile/phase-21-honest-everywhere/HSM-21-WALK-RIDER.md) staged (H1–H3, ~5 min) |

## Outstanding — the owner's hands

**THE COUCH SESSION closes three phases in one sitting**, same hub + same `.43`
pre-flight (`~/run-qwythos-vision.sh`, never `-intel`):
1. [`HSM-18-06-WALK.md`](../holdspeak-mobile/phase-18-ipad-dictation-contracts/HSM-18-06-WALK.md) — W1–W5 (dictation).
2. [`HSM-19-07-WALK.md`](../holdspeak-mobile/phase-19-ipad-meeting-contracts/HSM-19-07-WALK.md) — W1–W6 (meetings).
3. [`HSM-21-WALK-RIDER.md`](../holdspeak-mobile/phase-21-honest-everywhere/HSM-21-WALK-RIDER.md) — H1–H3 (honesty, ~5 min).

Also still open from the desk era: the desk feel pass, the Phase-72 iPad walk
items, and **the release cut** (CHANGELOG `[Unreleased]` grew nine entries
tonight: file-issue, proposals review, facets, import, learning reader on the
iPad; the egress grammar, the prose guard, readiness truth, the trust chip).

## Outstanding — buildable headless (ranked)

1. **Equilibrium 23 — mesh-safe storage**: 23-01/02 (refuse-newer + backup)
   were pre-paid by Wave 4 — survey first, the phase doc is stale like 19/21
   were. Remaining: the iPad doctor/readiness panel (Settings) + 23-04 sync
   integrity / serialization-contract pin.
2. **Lock the Walks** (desktop; the desk-era handover's standing offer).
3. **Equilibrium 22 — the graph travels** (Workbench `graph_json` bridge;
   Wave 1 pre-paid the hub honoring failure_policy/runs_on).
4. Watch items: `db/core.py` (guard-named), the
   `test_replay_after_target_correction_changes_routing` flake.

## Traps (tonight's additions to the standing list)

- **Gate merges on the conclusion JSON, in a separate call** (the #233
  failure, above). The full standing rule is in Claude's memory
  (`feedback_gate_merges_on_conclusion`).
- **The api-surface lock**: any new route literal in Swift needs
  `uv run python scripts/gen_api_surface.py` in the same commit.
- **The live-proof pattern** (used 8× tonight, reusable): scratch
  `MeetingWebServer` on loopback; redirect `hscfg.CONFIG_DIR/CONFIG_FILE`
  BEFORE imports that read config; seed via the real repositories
  (`save_meeting`, `dictation_journal.record`, `record_correction`);
  `Config.load()` reads per request, so rewriting the config file mid-run
  flips the hub's posture live.
- **Driving the sim headlessly**: `simctl spawn <dev> defaults write
  dev.holdspeak.mobile hs.peer.host …` pairs the desk app to a scratch hub;
  screenshot-run env affordances added tonight (`HS_SHELL_OPEN_MEETING`,
  `HS_SHELL_FACET_SPEAKER/_TAG`, `HS_SHELL_IMPORT_FILE`,
  `HS_DESK_OPEN=connector|connector-github`) each drive the SAME code path
  the tap would.
- **`DesktopClientError` is nested**: catch
  `HTTPDesktopClient.DesktopClientError.http(code)`.
- **Speak/Local harness sim builds** need `scripts/patch-llm-macro.sh` +
  `-disableAutomaticPackageResolution -skipMacroValidation`.
- **The CompanionShell stages no engine packages** — no mic fields there;
  `EgressScope`-style shared grammar lives in Contracts so both apps render it.

## Where things live

- Phase 19: `pm/roadmap/holdspeak-mobile/phase-19-ipad-meeting-contracts/`
  (per-story evidence + 9 screenshots).
- Phase 21: `pm/roadmap/holdspeak-mobile/phase-21-honest-everywhere/`
  (per-story evidence + 10 screenshots; the ledger note in
  `current-phase-status.md`).
- Memory (Claude's): `project_phase19_ipad_meeting_contracts`,
  `project_phase21_honest_everywhere`, `feedback_gate_merges_on_conclusion`;
  `project_equilibrium_program` carries the program state.

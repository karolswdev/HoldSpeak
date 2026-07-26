# HoldSpeak — Agent Handover

**Written:** 2026-06-03. **Author:** Claude (Opus 4.8 session).
**Read this first**, then `pm/roadmap/holdspeak/README.md` and the active phase's
`current-phase-status.md`. This is a pickup snapshot, not canon — if it disagrees
with the live status docs, the status docs win.

> **Sibling roadmap (2026-06-18):** the Apple mobile runtime is a **separate**
> project at [`../holdspeak-mobile/`](../holdspeak-mobile/README.md) (prefix
> `HSM`, the Council Implementation Charter — 12 phases, Phase 0 in progress). It
> does not renumber or interrupt this roadmap; the two meet only at Phase 0's
> contract extraction.

---

## 0. LATEST (2026-07-22) — Phase 102 "The Refit" in flight, 4/7

Everything below section 1 is old (Phase 31–43 era) and kept for
history only. For the live picture, read
[`phase-102-the-refit/current-phase-status.md`](./phase-102-the-refit/current-phase-status.md)
and the roadmap `README.md` — this section is just the fast pickup.

**What Phase 102 is.** The owner's direct order after round 9 landed:
six named, screenshot-convicted surfaces that still "feel like HTML
slapped inside a nicer container," fixed one at a time against the
already-ratified HS-101 interior canon (`docs/internal/DESIGN_SYSTEM.md`
§"The interior canon"). No new capabilities, no wire changes — the
existing canon applied exactly, surface by surface. Each of the six
build stories (`story-01`…`story-06`) carries a **Design direction**
section written 2026-07-21 that names the exact defect and the exact
existing kit component to reuse — read the target story file before
touching code, it's already scoped.

**Shipped (commits, local to `main`, none pushed):**
- `ece49f39` HS-102-01 Runs on — destination create/edit is choice
  bays (`RuntimeDestination` pattern reused); `SurfaceBay` gained an
  `expanded`/`editor`/`ghost` slot (kit addition, `Surface.tsx`).
- `4ca941e8` HS-102-02 Live Meeting — working posture; plumbing moved
  behind a new `door`/`doorOpen` gear split (the `DictationCore.tsx`
  pattern); `MetricStrip` banned from this file by guard.
- `c2b17506` + `92015e68` HS-102-03 Ask AI — one composer well
  (`desk-chat-well`, the `PersonaChat`/capability-card grammar);
  answers render through `Material`. **The `92015e68` commit is a
  same-day correction** — the first evidence pass wrongly claimed the
  LAN model was unreachable and deferred a whole acceptance leg; it
  wasn't unreachable, the owner caught it in one line. See §0.1.
- `9720521d` HS-102-04 Meetings wings — Artifacts is now
  `SurfaceLibrary`/`SurfaceLibraryTile` (same as Blocks); Outcomes
  rows sort needs-you first (`SurfaceRow` gained a `quiet` prop, kit
  addition); Record leads with a verb above the drop well.
  `scripts/desk_gl_walk.py`'s `meetingflow` leg grew an
  artifacts-library assertion.

**Remaining:**
- `HS-102-05` — the selection mark yields to open. Small, mechanical:
  `web/src/desk/store.ts` has `clearSelection()` (clears
  `selectedIds` AND `askOpen`) and `setSelected([])` (clears only
  `selectedIds`) — the open branch must call `setSelected([])`, not
  `clearSelection()`, or it'll wrongly close a held Ask composer. The
  story file's Design direction section already names the exact line
  numbers.
- `HS-102-06` — Speech Settings (`DictationCore.tsx`'s configure
  wing). The worst offender per the owner's own screenshots (raw
  wire dumps, orange Save buttons, six-tile cacophony) — story-06's
  Design direction is the most detailed of the six, field-by-field.
  Reuse `SurfaceGroup`/`SurfaceSettingRow`/`SurfaceToggle` (already
  proven in Settings' Appearance group) and `EditInPlace` for
  Knowledge/Instructions.
- `HS-102-07` — closeout. Depends on 01–06 all done. Runs the full
  chain + an owner sitting (Article IX.4 — the felt verdict, not just
  green). Its acceptance criteria already include: check each shipped
  story against its OWN Design direction section (not just its
  checklist), and grep the diff for a second implementation of any
  named kit component (`SurfaceBay`, `SurfaceLibrary`, `EditInPlace`,
  `RuntimeDestination`, `SurfaceGroup`/`SurfaceSettingRow`, `Material`,
  `SurfaceStream`) — one owner per shape.

### 0.1 — Gotcha that cost real time: test unreachability claims, don't assume them

There is a real, reachable LAN LLM at `192.168.1.43:8080`
(OpenAI-compatible, currently serving
`Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf`). A stale memory note said
"sandboxed Bash can't reach LAN IPs" and this session trusted it
without testing — wrong, for this environment: a plain `curl
http://192.168.1.43:8080/v1/models` answers directly. **Always curl
it first.** See `feedback_test_before_claiming_unreachable.md` and
the corrected `reference_lan_llm_endpoint.md` in the agent memory
store. This matters for Phase 102 specifically because several
acceptance criteria want a REAL grounded run, not a fixture — use the
recipe below.

### 0.2 — The story-by-story recipe (repeat for 05, 06)

1. `.githooks/dw story status holdspeak 102 0N in-progress`
2. Read the target story file's Design direction section (already
   written) + the actual current component source.
3. Boot a throwaway staged instance: fresh isolated `HOME`,
   `HOME=/tmp/hs-eval-X HOLDSPEAK_WEB_PORT=8788
   HOLDSPEAK_WEB_HOST=127.0.0.1 uv run holdspeak web --no-open &`,
   confirm `curl -s -o /dev/null -w '%{http_code}\n'
   http://127.0.0.1:8788/` returns 200.
4. Implement, reusing the named kit component — extend
   `web/src/desk/surface/Surface.tsx` (+ `surface.css`) when the kit
   is missing a slot, exactly like `SurfaceBay`'s expand slot and
   `SurfaceRow`'s `quiet` prop were added; don't invent a parallel
   component family.
5. `cd web && npx tsc --noEmit -p . && npx vitest run --no-color &&
   npm run build --silent && npm run tokens:gate --silent` — all must
   be clean.
6. Add a named regression guard to
   `tests/unit/test_interior_canon_guard.py` (grep-based, mirrors the
   four already there) and run
   `uv run pytest -q tests/unit/test_interior_canon_guard.py
   tests/unit/test_web_vocabulary_guard.py`.
7. Kill the old server, rebuild (`npm run build`), restart on a FRESH
   isolated `HOME`, and live-drive the fix headed at 1440×950 and
   393×852 with Playwright (see any `pm/roadmap/holdspeak/phase-102-the-refit/evidence-story-0N.md`
   for the exact script shape — free-object double-click helper,
   `.desk-tool-shelf` search-and-launch helper, etc.). For a REAL
   grounded run (Ask AI, Meetings intelligence), register `.43` as a
   `Runs on` destination via `POST /api/profiles` (`kind:
   openAICompatible`, `base_url: http://192.168.1.43:8080`, `model:
   Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf`, `requires_key: false`),
   or for meeting intel set `PUT /api/settings` →
   `meeting.intel_provider: cloud` + `intel_cloud_base_url` +
   `intel_cloud_model`, import a transcript via
   `POST /api/meetings/import`, then run
   `holdspeak intel --reroute <meeting_id> --profile balanced` to
   synthesize real plugin artifacts. Kill the server
   (`lsof -ti :8788 | xargs kill -9`) and delete the throwaway `HOME`
   when done.
8. `.githooks/dw evidence capture holdspeak 102 0N -- sh -c "<the
   full test/build/guard chain>"`, then copy screenshots into
   `pm/roadmap/holdspeak/phase-102-the-refit/assets/` and hand-write
   the ledger/fix/proof narrative into the generated
   `evidence-story-0N.md` (see 01–04 for the shape: ledger, fix,
   driven-live-after, guard added).
9. `.githooks/dw story status holdspeak 102 0N done`, then
   `.githooks/dw check holdspeak` — expect ONLY the pre-existing
   `phase-101-the-native-innards/evidence-story-04.md` warning (leave
   that file untouched, it's a known, separate, untracked artifact
   from the Phase-101 sitting loop — do not stage or fix it).
10. Update `current-phase-status.md`'s header count + a new dated
    "Where we are" paragraph, and the roadmap `README.md`'s "Last
    updated" block — same pattern as the four already shipped.
11. Stage exactly the touched files (never `git add -A`),
    `.githooks/dw contract new --story HS-102-0N --tests-capture
    pm/roadmap/holdspeak/phase-102-the-refit/evidence-story-0N.md`,
    honestly flip all 7 boxes in `.tmp/CONTRACT.md`,
    `.githooks/dw gate --porcelain` (expect `gate=pass`), then
    `git commit`.

Nothing in this phase has been pushed or PR'd yet — all five commits
so far are local to `main`. Ask the owner before pushing/opening a PR.

---

## 1. TL;DR — where things stand

- **LATEST (2026-06-06): Phases 33–43 shipped since this doc was first written.**
  The bullets below are the Phase-31/32 era and are kept for history; for the
  current phase index + status, the roadmap **`README.md`** is the source of
  truth. Most recent: **Phase 43 — World-Class Onboarding & First-Run UX: CLOSED
  ✅ (6/6)** — on user feedback that the Phase-42 first-run was "boring cards" / a
  checklist not a wizard / a settings form dump / desktop presence behind an env
  var. Reimagined as a world-class UX **layer on the Phase-42 plumbing** (no
  rewrite): a full-screen **`/welcome` wizard** (Welcome · live Permissions ·
  Model picker · a celebratory first-dictation reward · a one-click presence
  toggle · Done; `web/src/pages/welcome.astro` + `welcome-app.js`), desktop
  presence is now a **config-backed UI toggle** (`config.presence.enabled`;
  `desktop_presence_enabled(config_enabled=)`; live start/stop in
  `_sync_desktop_presence`; **the env var is dead as the path**), and **Settings**
  is sectioned + searchable + progressive (the form dump retired). The `/` guard
  sends first-run users to `/welcome`. Proven by `scripts/dogfood_wizard.py` →
  WIZARD DOGFOOD OK (fresh clone → wizard → first dictation, zero file edits).
  Suite **2319 passed, 16 skipped**. Branch `phase-43-world-class-onboarding` —
  open a PR to `main`. (Prior: **Phase 42 — First-Run Delight & Daily Confidence:
  CLOSED
  ✅ (8/8)** — made **arrival** stellar: a user goes from fresh clone to a
  **verified first dictation**, with visible privacy/trust state and **zero file
  editing**, in one guided local cockpit. The spine is **`GET /api/setup/status`**
  (`holdspeak/setup_status.py` — an *adapter* over `collect_doctor_checks()` +
  readiness + egress + presence, drift-guarded so every doctor `FAIL` surfaces;
  cheap via `skip_network`) + a durable **`first_run` milestone** (`db.milestones`,
  set on a real dictation). Surfaces: a Signal **`/setup`** welcome (one primary
  action · guided first-dictation with live WS "✓ It worked" + the
  `FIRST_DICTATION_SUCCESS` milestone · model-setup assistant · presence
  onboarding), a real **`/settings`** page (the interim "History → Settings"
  drawer retired), a **`/` first-run guard** (never nags a healthy user), a **CLI
  launch nudge**, and an **ambient TrustChip + Trust & Privacy panel** on every
  page. Proven by an all-in-app, zero-file-edit **TTFD dogfood**
  (`scripts/dogfood_first_run.py` → `DOGFOOD OK`, launch→/setup 1.13s). Suite
  **2306 passed, 16 skipped**. Branch `phase-42-first-run-delight` — open a PR to
  `main`. (Prior: **Phase 41 — Runtime Presence Indicators: CLOSED ✅ (8/8)**
  — an **opt-in** (`HOLDSPEAK_DESKTOP_PRESENCE=1`), per-platform **native**
  desktop presence layer so a user dictating into another app can see what the
  copilot is doing (*listening / transcribing / typing*) without the web
  dashboard visible. One normalized `runtime_activity` contract → a websocket
  broadcast → a Signal `/presence` card, hosted natively: **macOS** = a
  focus-safe non-activating `NSPanel` + `WKWebView` HUD + an `NSStatusItem`
  glyph; **Linux** = an in-place libnotify notification + StatusNotifierItem tray
  (Tier 1, everywhere) + a GTK-WebKit floating overlay (Tier 2, X11/wlroots).
  **Never steals keyboard focus** (re-proven live in closeout: `focus_stolen:
  False`). Off by default; native deps are optional extras; flag-unset ⇒
  byte-identical. Both renderers + the overlay proven on real hardware (macOS
  here, Linux on `.43`). Branch `phase-41-runtime-presence` — open a PR to
  `main`; **codex PR #17 closed as superseded**. Suite **2261 passed, 16
  skipped**. (Prior: **Phase 40 — Configuration Cockpit & Persistent Memory:
  CLOSED ✅ (6/6)**, merged via PR #18 — the dictation copilot configurable +
  curatable from the Web UI, correction memory **DB-backed and survives a
  restart**. **Phase 39 — Dictation Copilot Depth: CLOSED ✅ (9/9)**, merged via
  PR #16.)
- **Phase 31 (db decomposition): MERGED** to `main` (was PR #7). `holdspeak/db.py`
  (5,481-line god-object) → the `holdspeak/db/` package: a thin `Database`
  container + 5 repositories, migration ladder squashed to one canonical schema.
- **Phase 32 — Foundation Hardening & Doc Truth: DONE (7/7), MERGED** to `main`
  via PR #8 (all CI green, incl. the new real-Whisper smoke test on the macOS
  runner). Highlights: `web_runtime.py` → a `WebRuntime` class; `MeetingSession` is
  web-free (emits via `on_broadcast`); **the TUI *and* the macOS menubar were
  retired** (web runtime is now the *sole* interactive runtime — `tui/`,
  `controller.py`, `menubar.py`, the `tui`/`menubar` CLI, `--no-tui`, and the
  `textual`/`rumps` deps all gone; ~13k lines removed); one audio-ownership model
  (meeting holds the shared `VoiceTypingSession` floor); an **ungated CI
  core-path smoke test** (real Whisper `tiny` on a committed WAV, macOS job, every
  push); one route 500-helper (`error_500`, 48 sites); and the doc-truth sweep +
  drift guard.
- **Test suite:** green — `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **~1954 passed, 14 skipped** (count grew/shrank across the phase; see the latest
  story evidence for the exact number).
- **Plugins: 14 real, ZERO stubs** — locked by
  `tests/unit/test_decision_announcement_drafter_plugin.py::test_no_deterministic_stub_remains`,
  and now also guarded at the doc level by `tests/unit/test_doc_drift_guard.py`
  (no live doc may claim a `DeterministicPlugin` stub).
- **Hardware-gated, untouched:** Phase 24 (companion, 3/6), Phase 25 (HS-25-07
  dogfood), Phase 15 (out-and-about, not-started). All need the physical AI-PI / a
  real mic; the author is remote.

## 2. What happened recently

- **Phase 30 — UI/UX overhaul: DONE (9/9).** Amiga Workbench retired for "Signal".
- **Phase 31 — Database Decomposition: DONE (5/5), merged.** `db.py` → `db/`
  package (`Database` container + 5 repos); 18-version migration ladder squashed
  to one canonical schema; the `MeetingDatabase` god-class retired → `Database`.
- **Phase 32 — Foundation Hardening & Doc Truth: DONE (7/7), this session.** See §1.
  Notable user decisions: drop the embedded per-meeting web server (HS-32-02); kill
  the TUI **and** the menubar (HS-32-07); a helper *function* over a decorator for
  the route 500s (HS-32-05).

## 3. Pick up here

**▶ Nothing in-flight — Phase 38 just CLOSED. Pick the next phase's direction.** The last
six closed phases were a long decomposition/hardening + plugin/actuator arc (31→38). Open
candidates the prior handovers floated, none committed: a **release/first-run** pass (cut an
actual tag + PyPI; Phase 33 made positioning honest, not published — see §"Manual follow-up"),
a **dogfood/reliability** pass, **UX consolidation**, or the **actuator next-frontier**
(more connectors as discovered packs · a cross-meeting approval inbox · a mid-meeting
live-dispatch cadence · per-role governance — see `phase-38-actuators-ii/final-summary.md`
§Handoff). Still **hardware-gated** (author remote, no mic/AI-PI): Phase 24 (companion, 3/6),
Phase 25 (HS-25-07 dogfood), Phase 15 (out-and-about). Scaffold a phase folder + stories when
the direction is chosen.

**▶ Phase 38 — Actuators II: CLOSED ✅ (6/6), on local branch
`phase-38/hs-38-01-write-connector-framework` — push + open a PR to `main`.** Full record:
`phase-38-actuators-ii/final-summary.md`. Made the proven-safe Phase-37 actuator mechanism
*useful* without weakening the invariant: **real write connectors** behind a per-connector
**permission manifest**, and **live in-meeting proposals**. **HS-38-01** the gated
write-connector framework (`holdspeak/plugins/gated_connector.py`: `WriteConnectorManifest`
declares one egress permission + a concrete argv-prefix / host allow-list; `build_gated_connector`
enforces **plan → allow-check → gate → interpret**, refusing a non-declared op *before* the
existing `connector_runtime.PermissionGate` — no second egress primitive; the Phase-37
`ActuatorExecutor` unchanged) → **02** GitHub (`github_issue_actuator.py`: `gh issue create`
and only that, `shell:exec`, argv from payload run without a shell ⇒ no injection) → **03**
webhook (`webhook_post_actuator.py`: HTTP POST to an allow-listed host, `network:outbound`,
`MeetingConfig.webhook_allowed_hosts` default-empty) → **04** live proposals
(`process_meeting_state` `on_proposal` callback → `MeetingSession._emit_actuator_proposal`
emits a **read-only** `actuator_proposed` broadcast [never the egress payload]; a Signal
"Pending actions" dashboard panel approves/rejects via the Phase-37 decision endpoint — a
surface, not a new execution path) → **05** docs (`docs/PLUGIN_AUTHORING.md` write connectors
+ live proposals) → **06** closeout. **Off + unregistered by default** (routing byte-identical,
38 routing tests green); the default suite makes **no real outbound call** (injected runners/
clients); the connectors are **host-side** (the executor injects them, not discovered packs).
Suite **2123 passed, 15 skipped**.

**▶ Phase 37 — Actuators: CLOSED ✅ (7/7), merged via PR #14.** Full record:
`phase-37-actuators/final-summary.md`. The plugin system's **third kind** is on, behind
one invariant: *no external side effect without an explicit, audited, per-action human
approval; executed == previewed.* An actuator **proposes** (`ActuatorProposal` from
`run()`, status `proposed`); a human **approves** (the meeting-detail "Proposed actions"
cards / `POST …/proposals/{id}/decision`); a **guarded executor**
(`plugins/actuator_executor.py`) acts only on an `approved` proposal through status +
policy gate (`MeetingConfig.allow_actuators` + `allowed_actuators`, default-safe) +
**payload parity** (TOCTOU) + an **injected connector** (never a socket in the executor) +
an **audit** row. Persistence: `db.actuators` (`actuator_proposals` /
`actuator_proposal_audit`). Reference: `followup_ticket_actuator` + `build_outbox_connector`.
**Default suite + routing byte-identical** — no actuator is registered
(`register_followup_actuator` is opt-in, not in `register_builtin_plugins`) or in any chain.

**▶ Earlier — Phase 36 — Meeting Intelligence & Experience: CLOSED ✅ (6/6), merged via
PR #13.** Full record: `phase-36-meeting-artifact-experience/final-summary.md`. Both tracks
landed:

- **Experience (HS-36-01→03):** Signal **elevated artifact cards** (type-colored accent
  edge + header + collapse + overflow-safe body; the risk-table overflow fixed via
  `.table-scroll`), **copy-as-Markdown** per artifact + "Copy all" (pure per-type
  serializers in `history-app.js`, reusing the `CommandPreview` clipboard pattern), and a
  **per-type body polish** pass (the bodies referenced non-existent `--color-*` tokens →
  off-palette fallbacks; all migrated to real Signal tokens; incident **timeline rail**,
  typed badges, sub-cards, markers). UI in `web/src/pages/history.astro` +
  `web/src/scripts/history-app.js`; `holdspeak/static/_built/` is **gitignored** — commit
  `web/src` only, never `_built`.
- **Intelligence (HS-36-04→05):** the routing weakness (a brief intent diluted below the
  0.6 threshold and silently lost) is fixed by an additive, gated **segment probe**
  (`plugins/segment_probe.py`, merged element-wise `max` into `scoring.score_window`,
  off by default via `intent_segment_probe_enabled`; the lexical scorer is the
  deterministic fallback). Default path (`segment_probe=None`) is byte-identical → the
  routing tests are unchanged.

**Headline deliverable (delivered):** the **before/after** of the same messy meeting,
re-captured in the new cards on real `.43` — **7 → 13 artifact types** (incident+comms
fished out per segment): `phase-36-.../evidence/dynamic_meeting_before.png` vs `_after.png`.
**The routing-ripple + selector-lockstep rules still apply** to future plugin work: the
spoken-e2e artifact selectors (`.risk-table tbody tr`, `.incident-timeline li`, …) AND
`test_intent_router` / `test_intent_dispatch` / `test_multi_intent_routing` move in
lockstep — don't silence.

**Phase 35 — Plugin Frontier: CLOSED ✅ (5/5), merged via PR #11.** The plugin system
is externalizable end-to-end: public `docs/PLUGIN_AUTHORING.md`, a plugin-pack manifest
+ discovery loader (`plugin_sdk.py` / `plugin_pack_loader.py`, first-party +
`~/.holdspeak/plugin_packs/`), per-project enable/disable (a `skipped` dispatch gate;
`router.py` untouched), and a second spoken-e2e (incident + comms, verified on `.43`).
Full record: `phase-35-plugin-frontier/final-summary.md`.

**Phase 37 — Actuators** is the teed-up successor (renumbered from 36 when the artifact
UX phase took the 36 slot): the host's `actuator` kind stays **blocked** today; Phase 35
built its groundwork (the authoring + pack + manifest contract). Phase 37 adds preview →
human approval → external side effect (RFC open question #5; intersects the Phase-25
egress posture). Scaffold a phase folder + stories when starting.

> **▶ Config hardening — DONE (merged PR #12):** `Config.load()` now filters unknown/
> legacy keys per sub-config (the HS-32-06-retired `meeting.web_enabled` no longer nukes
> the whole config) and logs the last-resort fallback instead of swallowing it. The
> earlier "silently discards the whole config" hazard is resolved.

> **▶ Routing ripple (HANDOVER §5):** adding/suppressing a plugin in a chain touches
> `tests/unit/test_intent_dispatch.py` (chain constants + window counts) +
> `test_intent_pipeline.py` / `test_multi_intent_routing.py` — update in lockstep,
> don't silence. The connector-pack system is the precedent to mirror.

> **▶ Earlier (both merged to `main`):** Phase 33 (Documentation & OSS readiness,
> PR #9) — Apache-2.0 LICENSE, `docs/MODELS.md`, `docs/` reorg, OSS README +
> CHANGELOG/CONTRIBUTING, brand mark + social card. Phase 34 (Structural
> Decomposition II, PR #10) — the four god-files (5,373 lines) → four packages
> (`routes/dictation/`, `routes/activity/`, `agent_context/`, `intel/`),
> behavior-preserving. The decomposition lineage (26 → 31 → 32 → 34) is complete.

> **▶ Manual follow-up (not a repo file):** set
> `docs/assets/pixellab/social-card.png` as the repo's GitHub social preview
> (*Settings → Social preview*). Cutting an actual release (tag + PyPI) is a
> deliberate future follow-up — Phase 33 made the positioning *honest*, not
> *published*.

> **▶ pixellab MCP** (for future asset work): record each asset's object ID +
> prompt in `docs/assets/pixellab/README.md`; derived (composed) assets like the
> social card are reproduced via `docs/assets/pixellab/compose_og_card.py`.

> **▶ Note for a remote (no-hardware) session:** the real-audio capture paths
> (`metal`) can't run here; the HS-32-04 smoke test covers real transcription on a
> committed WAV instead. Anything touching the AI-PI or a live mic stays gated.

> **Historical:** Phases 31 (db decomposition) and 32 (foundation hardening +
> TUI/menubar retirement) are both **merged to `main`** (PRs #7 and #8). Their
> `final-summary.md` files record the exit state.

## 4. The persistence layer (Phase 31 — how it's shaped now)

`holdspeak/db/` package (was the single `db.py`):

- `core.py` — the **`Database` container**: owns the one sqlite connection
  (`_connection`), builds the schema (`_ensure_schema` / `_apply_schema` →
  `SCHEMA_SQL`), holds the `get_database()` singleton. **No domain methods.** It
  constructs the repos: `self.meetings / .intel / .plugins / .projects / .activity`.
- `meetings.py` `MeetingRepository` — meetings, segments, speakers, topics,
  bookmarks, action items, **and intel snapshots** (embedded in `MeetingState`).
- `intel.py` `IntelRepository` — the deferred-intel **jobs/attempts queue**.
- `plugins.py` `PluginArtifactRepository` — intent windows, plugin runs/jobs, artifacts.
- `projects.py` `ProjectRepository` — projects, associations, detection log.
- `activity.py` `ActivityRepository` — the local activity-intelligence ledger.
- `models.py` — all dataclasses + validation constants (shared; breaks the cycle).
- `base.py` — `BaseRepository`: connection factory, the `_json_*` helpers, and a
  **container back-reference `self._db`** for the rare cross-domain call (e.g.
  `intel.requeue_intel_job` → `self._db.meetings.get_meeting`; an activity rule →
  `self._db.projects.get_project`).
- `__init__.py` — re-exports the full public surface, so `from holdspeak.db import X`
  is unchanged. **Call domain methods as `db.<repo>.<method>(...)`**, not `db.<method>`.

The fresh-build schema is pinned by `tests/fixtures/db_schema_canonical.txt` +
`TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot` — **any schema
change must regenerate that snapshot in the same commit.**

## 5. Conventions & gotchas you MUST honor (this repo bites otherwise)

- **PMO pre-commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` with **≥7
  `[x]`** (template in `pm/roadmap/PMO-CONTRACT.md`). A story flipping to `done`
  ships its `evidence-story-{n}.md` in the **same** commit; **one** `done`-flip per
  commit (else write `.tmp/BUNDLE-OK.md`). Phase-exit stories need an
  `evidence-story-{n}.md` **in addition to** `final-summary.md` (the hook enforces
  the forward pairing). The story Status line must be the list-item form
  `- **Status:** done` or the hook won't detect the flip.
- **`.tmp/` is not auto-created** — `mkdir -p .tmp` before writing the contract.
- **NO `Co-Authored-By` trailer.** Repo rule #5 — overrides the default habit.
- **No `--no-verify`.**
- **Full-suite gate:** `uv run pytest -q --ignore=tests/e2e/test_metal.py` (the
  metal file hangs without a real mic). Run the **whole** suite — `-k` filters miss
  real bugs. The db package must stay **ruff-clean** (`uv run ruff check holdspeak/db/`).
- **`python` is not on PATH — use `python3`.**
- **Routing ripple:** adding a plugin to a base chain breaks
  `tests/unit/test_intent_dispatch.py` (chain constant + window counts) and the two
  full-pipeline tests (`test_intent_pipeline.py`, `test_multi_intent_routing.py` —
  they register the *union* of plugin IDs as stubs). Update those; don't silence.
- **LAN endpoint + sandbox:** intel runs on `.43:8080` (LAN, Qwen3.5-9B-Q6).
  **Sandboxed Bash can't reach the LAN** → use `dangerouslyDisableSandbox: true`
  for any command that hits `.43` / the spoken e2e / a real plugin call. Memory
  `reference-lan-llm-endpoint`.
- **Spoken e2e is opt-in:** `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s`;
  module-skips otherwise. Playwright/Chromium are transient installs (not in
  `pyproject.toml`).
- **`holdspeak/static/_built/` is gitignored** — `(cd web && npm run build)` after
  editing anything under `web/` (Node ≥ 22.12; CI uses Node 22). Page-content tests
  read the built JS.
- **Operating cadence:** every shipping commit updates the story header, the phase
  `current-phase-status.md` (row + Last-updated + "Where we are"), the project
  `README.md` (phase row + Last-updated + Current-phase), and any canon doc touched.

## 6. Decomposition lessons (Phase 31 — don't relearn the hard way)

- **Verbatim moves still need their imports.** Splitting a module drops relative
  imports one level (`from .x` → `from ..x`) and the per-domain module needs its own
  `import uuid` / `import json` / `from urllib.parse import …`. Run `ruff --select F821`
  on a new module to surface every undefined name at once.
- **External code called *private* db helpers** (`db._normalize_activity_url`) and
  held the db under odd receivers (`self._db`, `kwargs["db"]`, `activity_db`). A
  name-based call-site sweep misses these — the full suite is what caught them.
- **Test doubles need repo properties.** A fake db stubbing domain methods needs
  `meetings = property(lambda self: self)` (and `intel`/`plugins`/`projects`/`activity`
  as used) so `db.<repo>.<method>` resolves back to the fake.
- **Monkeypatch targets follow the symbol.** `DEFAULT_DB_PATH` moved to
  `holdspeak.db.core`; tests patching the package namespace had to patch `core`.

## 7. Decisions of record (recent)

- **Greenfield/aggressive** is the standing posture (one user, one dev DB,
  destructive-OK): Phase 31 deleted the god-class with no alias, squashed migrations
  with no upgrade path, rebuilt the dev DB. Memory `feedback_holdspeak_not_really_released`.
- **`intel_snapshots` live with `MeetingRepository`** (embedded in `MeetingState`),
  not `IntelRepository`.
- **Container back-reference (`self._db`)** is the cross-domain repo-call pattern.
- Intel runs on **`.43` Q6**; the localhost Q4 reasoning-leak is a non-issue (memory
  `project-intel-use-43-q6`).

## 8. Useful entry points

- Roadmap: `pm/roadmap/holdspeak/README.md` (phase index + Current-phase).
- Active phase: `phase-32-foundation-hardening/` (status + 6 story files).
- Just-closed phase: `phase-31-database-decomposition/final-summary.md`.
- Persistence: `holdspeak/db/` (container `core.py`; repos `meetings/intel/plugins/projects/activity.py`).
- Plugin reference impls: `holdspeak/plugins/builtin/{mermaid_architecture,action_owner_enforcer,decision_capture}.py`; registrar `builtin/__init__.py`.
- Synthesis + render: `holdspeak/plugins/synthesis.py`, `web/src/pages/history.astro`, `web/src/scripts/history-app.js`.
- Test commands: full `uv run pytest -q --ignore=tests/e2e/test_metal.py`; spoken e2e `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s`.

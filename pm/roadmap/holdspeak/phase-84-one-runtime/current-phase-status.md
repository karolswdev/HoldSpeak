# Phase 84 — One Runtime (where intelligence runs is a profile)

**Status:** CLOSED (5/5, 2026-07-07 — opened and shipped the same day) —
see [final-summary.md](./final-summary.md).

**Last updated:** 2026-07-07 (HS-84-05 done, the phase closes: the guides
teach "author a profile once, pick it everywhere" (guards 143/143) and the
six-beat LIVE walk on the real hub → the `.43` llama.cpp proved the thesis:
one profile authored once in the editor drove an agent chat, a
meeting-intel reroute (4 artifacts), and a dictation dry-run, with doctor
naming it for both pipelines).

## Why this phase exists

Backlog candidate **S** ("runtime / connectivity profiles") turned out to be
mostly shipped when we went to pick it up. The 2026-07-07 code survey found
the whole profile layer already live — built by HSM Phase 24 and the mesh
pass, extended by Phase 83:

- The contract: `ProfileRecord` (`holdspeak/db/models.py:555`, shape only,
  "the API key never lives here and never syncs"),
  `contracts/schemas/profile.schema.json` (`additionalProperties: false`),
  `SyncKind` `profile` on both hub (`web/routes/sync.py:42`) and Swift
  (`apple/Sources/Contracts/Sync.swift`).
- Authoring: full CRUD at `/api/profiles`
  (`holdspeak/web/routes/primitives/profiles.py`) and the web surface at
  `/profiles` (`web/src/pages/profiles.astro`, HSM-24-05).
- Per-agent assignment: `RecipeRecord.profile_id`, pickable in the desk's
  `InlineEditor.tsx`, honored by recipe chat and workflows
  (`web/routes/primitives/recipes.py:143`).
- Resolution + honesty: `build_meeting_intel_for_profile` +
  `profile_key_env` (`holdspeak/intel/providers.py:225-253` —
  `HOLDSPEAK_PROFILE_<ID>_KEY`, joined at run time), the ask route's model
  override + `_runnable_models` allow-list (`web/routes/primitives/ask.py:123`),
  egress badges derived from the ran profile, and the HS-83-01 gauge pricing
  against the picked profile's window.

What did NOT ship is the hub's own two pipelines. They predate profiles and
still run on hand-typed endpoint configs, parallel to the layer everything
else uses:

- **Meeting intelligence** runs on `MeetingConfig.intel_provider` +
  `intel_cloud_base_url` / `intel_cloud_model` / `intel_cloud_api_key_env`
  (`holdspeak/config.py:126-143`), constructed by
  `build_configured_meeting_intel` (`intel/providers.py:210-222`).
- **Dictation (DIR-01)** runs on `LLMRuntimeConfig.openai_compatible_*`
  (`holdspeak/config.py:328-344`), constructed in
  `plugins/dictation/assembly.py:128`, authored as raw URL/model/env fields
  in `/settings` (`web/routes/system/settings.py:586`).

So "where intelligence runs" is authored in THREE places today: `/profiles`
(agents, asks, model chats), the meeting-intel settings section, and the
dictation-runtime settings section. The last two are the same shape typed by
hand twice, with their own key conventions and their own egress derivations
(`intel_egress_posture` reads config, not profiles). The backlog's complaint
— one conflated global choice — has inverted into three parallel systems.

**One thesis:** every place the hub runs a model resolves through the ONE
RuntimeProfile layer; a raw endpoint URL is typed in exactly one place —
the profile editor.

## The design (pinned here so the stories don't fossilize five accidents)

- **Additive knobs, byte-identical when unset.** `meeting.intel_profile_id`
  and `dictation.runtime.profile_id` are new optional config fields. Empty ⇒
  today's construction paths, byte for byte. Set ⇒ the pipeline's endpoint
  shape (base_url / model / context window) comes from that profile row.
- **The key rule is unchanged.** A profile's key is
  `HOLDSPEAK_PROFILE_<ID>_KEY`, joined at run time, falling back to the
  pipeline's legacy default env (`OPENAI_API_KEY`). The key never rides a
  profile body, the sync wire, config files, or the browser.
- **Kind semantics follow the existing resolver.** `openAICompatible` runs
  on its endpoint; `onDevice` / `desktop` on the hub resolve to the hub's own
  configured engine (honest fallback, never a crash) — exactly what
  `build_meeting_intel_for_profile` already does.
- **`auto` keeps its meaning.** Meeting intel's local-first/auto behavior is
  untouched; the profile supplies the *cloud leg's* shape only.
- **A dangling assignment degrades honestly.** A deleted/unknown profile id
  falls back to the legacy path and `doctor` says so by name. Never a crash,
  never silent cloud egress the user didn't pick.
- **Settings pick, they don't type.** The meeting-intel and
  dictation-runtime settings sections become profile pickers wearing the
  picked profile's egress badge (Phase 62 canon: badge, never prose), with a
  door to `/profiles` for authoring. The raw URL/model/env fields leave the
  settings UI; the config fields stay as the fallback shape this phase
  (deletion is a deferred decision, see below).
- **One egress derivation.** The scattered egress dicts (`ask.py`,
  `cadence.py`, `intel_egress_posture`) converge on one profile-aware helper
  so doctor, cards, and threads all report the same truth. Badges stay
  hub-REPORTED, never client-inferred.
- **Stack rules stand.** No new Alpine; `/settings` and `/profiles` are
  existing page-class surfaces and stay so; edit `web/src`, build to verify,
  commit source only; screenshot-verify every changed surface; api-surface
  regenerates if any route changes.

## Exit criteria (evidence required)

- [x] One `.43` profile, authored once in `/profiles`, drives all three in a
  single live walk: an agent chat, a meeting-intel artifact run, and a
  dictation rewrite — no endpoint URL typed anywhere else — the six-beat
  walk output + 4 screenshots in [evidence-story-05](./evidence-story-05.md).
- [x] Both knobs unset ⇒ the legacy construction paths, proven byte-identical
  by unit tests pinning resolution order — [evidence-story-01](./evidence-story-01.md),
  [evidence-story-02](./evidence-story-02.md).
- [x] `holdspeak doctor` (and `/api/setup/status`) name the profile each
  pipeline resolves to, including the dangling-id fallback case —
  [evidence-story-04](./evidence-story-04.md); named live in the walk's beat 6.
- [x] The two settings sections author by picker, screenshot-verified; the
  raw endpoint fields are gone from the UI —
  [evidence-story-03](./evidence-story-03.md).
- [x] One egress helper feeds doctor + badges; posture test-pinned for
  local, profile-cloud, and legacy-cloud shapes —
  [evidence-story-04](./evidence-story-04.md).
- [x] Full suite green, docs/voice guards green (143), no route changes so
  `docs/api-surface.json` is untouched, BACKLOG.md row S updated —
  [evidence-story-05](./evidence-story-05.md).

## Story status

| ID | Story | Status | Story file |
|----|-------|--------|------------|
| HS-84-01 | Meeting intelligence runs on a profile | **done** (2026-07-07 — `effective_intel_cloud` seam + `intel_profile_id`; all four derivation sites adopted; 14 new tests + neighbors green) | [story-01](./story-01-meeting-intel-on-a-profile.md) |
| HS-84-02 | Dictation runs on a profile | **done** (2026-07-07 — `dictation.runtime.profile_id` via the shared `_apply_runtime_profile`; adopted ⇒ openai_compatible backend; probe/status honest; 11 new tests, 437 neighbors green) | [story-02](./story-02-dictation-on-a-profile.md) |
| HS-84-03 | Settings pick, not type | **done** (2026-07-07 — pickers + badges on /settings cloud + /dictation Runtime; raw endpoint inputs gone; 4 asserted screenshots; the rig caught a real Alpine select race) | [story-03](./story-03-settings-pick-not-type.md) |
| HS-84-04 | The honest doctor + one egress derivation | **done** (2026-07-07 — `endpoint_egress` + shared `_run_egress` (fixed the stale-badge find); the "Runtime profiles" doctor check; 13 new tests, doctor 62 + neighbors 70 unmodified) | [story-04](./story-04-honest-doctor-one-egress.md) |
| HS-84-05 | Docs + the live walk | **done** (2026-07-07 — 5 guides re-taught, guards 143/143; the six-beat live walk on the real hub → .43, all asserted, 4 shots; legacy-fields decision resolved: fallback stays) | [story-05](./story-05-docs-and-the-live-walk.md) |

## Where we are

**2026-07-07 (close) — THE PHASE IS CLOSED (5/5, same day).** HS-84-05
shipped the doc re-teach (MODELS.md leads with "author a profile once, pick
it everywhere"; MEETING_MODE_GUIDE, USER_GUIDE, and both dictation guides
point at the pickers, with the config fields kept as the documented
fallback; guards 143/143) and the six-beat LIVE walk on the REAL hub → the
`.43` llama.cpp (`scripts/walk_hs84_live.py`, every beat asserted): the
profile authored in the `/profiles` editor (the ONE place a URL was typed),
both pickers saved in the UI, an agent's reply wearing
`☁ Qwen3.5-9B-Q6_K · 192.168.1.43`, `intel --reroute` executing the routed
chain through the profile (4 artifacts), a dictation dry-run through the
same endpoint, and doctor's line: `[PASS] Runtime profiles: meeting intel:
profile 'Walk .43' (192.168.1.43); dictation: profile 'Walk .43'
(192.168.1.43)`. Cleanup restored the owner's assignments. The deferred
legacy-fields decision is resolved: the fallback stays (recorded in
story-05). See [final-summary.md](./final-summary.md).

Earlier — **2026-07-07 — HS-84-04 done: the honest doctor + one egress derivation.**
The badge has ONE constructor now — `endpoint_egress(cloud=, base_url=,
label=)` in `intel/providers.py` — called by the routes (via the shared
`_run_egress` in `ask.py`, imported by recipes like `_hydrate_grounding`),
cadence's `_LOCAL_EGRESS`, and the audit snapshot; wire shapes unchanged
(route tests pass verbatim). The story's FIND, fixed and test-pinned: the
default-cloud run badge read the RAW `intel_cloud_base_url`, but since
HS-84-01 the default engine may run on the assigned intel profile — the
badge could name the wrong host; `_run_egress` now reports
`effective_intel_cloud`, where the run actually went. Doctor grew a
dedicated **"Runtime profiles"** check (registered in
`collect_doctor_checks`, so the setup-status drift guard covers it
automatically): per-pipeline resolution by name ("meeting intel: profile
'LAN box' (192.168.1.43); dictation: hub default"), dangling assignments as
WARNs with the resolver's own reason, and `requires_key` profiles with no
key a WARN naming the exact `HOLDSPEAK_PROFILE_<ID>_KEY` to export (keys
never sync — each device holds its own). The two existing checks got the
same honesty: intel egress names the adopted profile's host; the LLM
runtime check reports "runs on profile …" / carries the dangling note.
`setup_status`'s trust endpoints now list the EFFECTIVE intel endpoint too.
13 new tests (`test_doctor_runtime_profiles.py`); doctor suite 62 +
route/status neighbors 70 pass unmodified. Next: HS-84-05 — docs + the live
walk on `.43` closes the phase.

Earlier — **2026-07-07 — HS-84-03 done: settings pick, not type.** Both endpoint
sections author by picking now. `/settings` → Cloud & advanced: a "Runs on"
select (`Hub default` + every non-deleted profile as `name — host`) bound to
`meeting.intel_profile_id`, wearing the pick's egress chip (`☁ host` /
`⌂ hub engine`; unset shows the honest legacy posture: `⌂ local` or the
legacy endpoint's host) and the "Manage profiles →" door. `/dictation` →
Runtime tab: the same picker (`None — backend above` + profiles) bound to
`dictation.runtime.profile_id`, badge + door; the meta banner names
`runs on: <profile>` when assigned. The raw base-URL / model / key-env
inputs are GONE from both surfaces (the `openai_compatible_timeout` stays —
a client knob, relabeled "Endpoint timeout seconds"); saves omit the legacy
fields (dictation) or pass them through untouched (settings), and the
client-side validation skips legacy-field checks when a profile is picked.
Proven by `scripts/screenshot_hs84_settings_pickers.py` (real app, scratch
DB, Playwright): 4 committed screenshots (both sections × empty/picked) and
asserted claims — badge text equals the picked host, raw inputs absent,
banner names the profile. The eyeball pass caught a REAL bug the assertions
then locked: the Alpine `x-model` select displayed "Hub default" while the
model held the assigned id (x-model + late `x-for` options race) — fixed
with `:selected`, regression-asserted via `input_value()`. Guards + settings
suites 54 passed; vitest 57; web bundle rebuilt (source-only commit). Next:
HS-84-04 — doctor + one egress derivation.

Earlier — **2026-07-07 — HS-84-02 done: dictation runs on a profile.**
`LLMRuntimeConfig.profile_id` (config-version-safe, normalized on the
settings route like the meeting knob) resolves through the SAME rule as
meeting intel — the HS-84-01 adoption logic was extracted as
`_apply_runtime_profile` with two thin config-shape wrappers
(`effective_intel_cloud`, `effective_dictation_llm`), and the shared
dataclass was renamed `EffectiveEndpoint`. One recorded design decision: an
ADOPTED profile also selects the `openai_compatible` backend — otherwise the
assignment is dead code under `backend: mlx`; every fallback leaves the
configured backend untouched, byte-identically. The honesty riders shipped
with it: `probe_runtime` (the setup self-test) probes the ADOPTED endpoint's
`/models`, and `setup_status`'s trust block lists the effective dictation
endpoint instead of the raw config field. 11 new tests
(`test_dictation_profile_resolution.py`: resolver matrix, assembly
byte-identical/adopted/dangling, probe, trust block, config + settings round
trips); dictation/setup/runtime neighbors 437 passed unmodified. Next:
HS-84-03 — the settings sections become profile pickers (backend + profile
presented as ONE "runs on" choice, per the recorded decision).

Earlier — **2026-07-07 — HS-84-01 done: meeting intelligence runs on a profile.**
`MeetingConfig.intel_profile_id` (config-version-safe, normalized on the
settings route) + the ONE resolver seam
`effective_intel_cloud(meeting_cfg, get_profile=None)` in
`intel/providers.py`: valid `openAICompatible` profile → its
base_url/model with `HOLDSPEAK_PROFILE_<ID>_KEY` preferred, legacy env
fallback; dangling/deleted/onDevice-kind/lookup-failure → the legacy
`intel_cloud_*` shape with a named reason (never a crash); unset →
byte-identical. Scope grew honestly (recorded in the story): the survey
found FOUR config→cloud-triple derivation sites, not one — plugins'
`build_configured_meeting_intel`, `resolve_llm_capability`, the live
session construction (`runtime/meeting_glue.py`), the deferred-queue drain
(`web/routes/meetings/intel.py`), and the CLI (`commands/intel.py`) — all
now read the seam, so the live meeting and the plugins can't split across
two worlds. 14 new tests (the resolution matrix, both constructors, config
+ settings round trips incl. clear-to-None); neighboring suites 136 passed
unmodified. Next: HS-84-02 — dictation adopts the same seam.

Earlier — **2026-07-07 — scaffolded.** The phase folder, five story stubs,
the README pointer, and the BACKLOG reconciliation (candidate S's
already-shipped majority recorded there) landed together (PR #286).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Config→DB layering: dictation pipeline construction may run where no DB handle is natural (CLI paths) | medium | the resolver takes an optional profiles lookup and falls back legacy when absent | an import cycle, or pipeline assembly suddenly requiring web context |
| Profile deleted while a pipeline points at it | certain eventually | resolve → legacy fallback + doctor names it; never crash, never silent egress | any test where a dangling id changes egress without a doctor FAIL/WARN |
| "auto" provider semantics drift while re-plumbing the cloud leg | low | HS-84-01 pins local/auto/cloud × profile-set/unset in a resolution-order test matrix | any existing intel test needing modification |
| The settings rework balloons into a settings redesign | medium | only the two endpoint sections change; everything else on `/settings` is out of scope | diffs outside the two sections' partials/modules |

## Decisions made (this phase)

- 2026-07-07 — Phase 84 is the *remaining slice* of backlog candidate S; the
  majority (contract, sync kind, CRUD, per-agent assignment, Apple + web
  authoring surfaces) shipped earlier with HSM Phase 24 / the mesh / Phase 83
  — recorded on the BACKLOG S row so the backlog stops advertising shipped
  work. — owner picked S; the code survey scoped it.
- 2026-07-07 — Legacy endpoint fields leave the settings *UI* this phase but
  stay in config as the fallback shape. — smallest honest step; deletion is
  deferred below.
- 2026-07-07 (HS-84-02) — An ADOPTED dictation profile also selects the
  `openai_compatible` backend; every fallback leaves the configured backend
  untouched. — shape-only adoption would make the assignment dead code under
  a local backend; assignment is the user's explicit "run it there".

## Decisions deferred

- **Auto-materializing existing `intel_cloud_*` / `openai_compatible_*`
  configs into profile rows.** Default: no — the walk authors its profile by
  hand; a doctor hint can suggest the move. Revisit if dogfooding shows
  people stranded on invisible legacy config.
- **Deleting the legacy config fields outright** (HoldSpeak is not really
  released, so the license exists). Trigger: the HS-84-05 walk proving the
  picker path end to end; take it as a rider there or file a follow-up.
- **Zone/desk surfacing of "runs on" beyond what already exists** (the rail
  already wears per-recipe endpoints). Out of scope here.

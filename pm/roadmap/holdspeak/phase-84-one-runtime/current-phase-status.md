# Phase 84 — One Runtime (where intelligence runs is a profile)

**Status:** OPEN (0/5, scaffolded 2026-07-07).

**Last updated:** 2026-07-07 (phase scaffolded; no story started).

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

- [ ] One `.43` profile, authored once in `/profiles`, drives all three in a
  single live walk: an agent chat, a meeting-intel artifact run, and a
  dictation rewrite — no endpoint URL typed anywhere else
  (`scripts/walk_hs84_live.py` output + screenshots in evidence).
- [ ] Both knobs unset ⇒ the legacy construction paths, proven byte-identical
  by unit tests pinning resolution order (profile → legacy → local).
- [ ] `holdspeak doctor` (and `/api/setup/status`) name the profile each
  pipeline resolves to, including the dangling-id fallback case (tests).
- [ ] The two settings sections author by picker, screenshot-verified; the
  raw endpoint fields are gone from the UI.
- [ ] One egress helper feeds doctor + badges; the per-pipeline posture is
  test-pinned for local, profile-cloud, and legacy-cloud shapes.
- [ ] Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py`),
  docs/voice guards green, `docs/api-surface.json` regenerated if routes
  changed, BACKLOG.md row S updated.

## Story status

| ID | Story | Status | Story file |
|----|-------|--------|------------|
| HS-84-01 | Meeting intelligence runs on a profile | backlog | [story-01](./story-01-meeting-intel-on-a-profile.md) |
| HS-84-02 | Dictation runs on a profile | backlog | [story-02](./story-02-dictation-on-a-profile.md) |
| HS-84-03 | Settings pick, not type | backlog | [story-03](./story-03-settings-pick-not-type.md) |
| HS-84-04 | The honest doctor + one egress derivation | backlog | [story-04](./story-04-honest-doctor-one-egress.md) |
| HS-84-05 | Docs + the live walk | backlog | [story-05](./story-05-docs-and-the-live-walk.md) |

## Where we are

**2026-07-07 — scaffolded.** The phase folder, five story stubs, the README
pointer, and the BACKLOG reconciliation (candidate S's already-shipped
majority recorded there) land together. Next: HS-84-01, the resolver seam +
meeting intel — it generalizes `build_meeting_intel_for_profile`, which
already exists and is tested on the ask/recipes path.

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

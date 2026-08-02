# HS-112-01 - One dial

- **Project:** holdspeak
- **Phase:** 112
- **Status:** ready
- **Depends on:** —
- **Unblocks:** HS-112-04, HS-112-05
- **Owner:** unassigned

## The thesis (the bar)

The owner: "One place to configure what the endpoint and model is."
Today there are ~28 named settings across 5 storage tiers that can
set an endpoint or model, three UIs that edit them, and two CRUD
APIs over one table. The bar: **the `InferenceTarget` (the
`profiles` table) is the ONLY place an endpoint or model lives, and
the Prefs room's `models` module is the ONLY place it is edited.**
Everything else is either a pointer to a target, a migrated legacy
fallback, or deleted.

## Ground (from the pre-charter survey)

- The same base_url/model/api_key_env triple is declared twice as
  independent config: `MeetingConfig.intel_cloud_*`
  (`holdspeak/config.py:141-145`) and
  `LLMRuntimeConfig.openai_compatible_*` (`config.py:340-342`), with
  different defaults and two separate `effective_*` resolvers
  (`holdspeak/intel/providers.py:365`, `:387`).
- Three "which profile" pointers with two different sentinels:
  `intel_profile_id` (`config.py:149`, `None`),
  `dictation.runtime.profile_id` (`config.py:347`, `None`),
  `rails_observer.profile_id` (`config.py:768`, `""`).
- Two full CRUD APIs over the same rows: `/api/profiles` and
  `/api/inference-targets`
  (`holdspeak/web/routes/primitives/profiles.py:139-165` is pure
  alias translation).
- `intel_queue.py` re-threads `cloud_base_url`/`cloud_api_key_env`
  as bare params through 6 signatures instead of reading the
  resolver.
- Three UI editors: raw `intel_cloud_*` text boxes
  (`web/src/pages/cores/SettingsCore.tsx:620-627`), the dictation
  "Runs on" radio's `openai_compatible_*` fields
  (`web/src/pages/cores/settingsBespoke.tsx:112-240`), and the
  Profiles room (`ProfilesCore.tsx`). The Prefs `models` module
  (`web/src/pages/cores/settingsPrefs.tsx:34`) is declared and
  empty — it owns nothing yet.
- The default host is hardcoded in 4 places (`parsing.py:162`,
  `engine.py:179`, `providers.py:263`, `config.py:341`).

## Method

1. **Migrate once, at config load.** `intel_cloud_*` and
   `openai_compatible_*` values that differ from a pointer become
   synthetic targets (`legacy-intel`, `legacy-dictation`) upserted
   into the profiles table; the config fields become dead legacy
   fallbacks slated for deletion, never edited again.
2. **Normalize the pointers.** Exactly three feature pointers remain
   in config — meetings, dictation, rails observer — one sentinel
   (`None` = hub default), all resolving through
   `resolve_inference_target`. `intel_queue` reads the resolver.
3. **One write path.** `/api/inference-targets` is the only write
   surface; `/api/profiles` becomes read-only compat. One chokepoint
   owns the default host.
4. **One face.** The Prefs `models` module becomes the dial: the
   target list (create/edit/delete, key status, reachability) plus a
   per-feature "runs on" picker row (Dictation / Meetings / Rails).
   The `SettingsCore` raw text boxes and the `settingsBespoke`
   endpoint fields die; the standalone Profiles room folds into or
   redirects to the module. HoldSpeak is not really released — no
   backwards-compat ceremony beyond the one silent migration.

## Test plan

- Grep census pinned as a test: zero live writers of
  `intel_cloud_base_url` / `openai_compatible_base_url` outside the
  migration shim; zero UI references to the dead fields.
- Migration is idempotent (load twice, one synthetic target) and
  honest (a fresh config mints nothing).
- Every feature leg (dictation pipeline, meeting intel, ask,
  rails observer, chains/recipes per-request override) resolves
  through `resolve_inference_target` — asserted by test.
- Live proof: set the dial once in Prefs, then dictation enrichment
  AND a meeting-intel call AND an ask all hit that endpoint (real
  metal, control-vs-treatment per standing rule).
- Screenshot walk of the one face at 1440+393, including the error
  legs (unreachable endpoint, missing key) in-flow.

# HS-114-01 - The seeded nerve

- **Project:** holdspeak
- **Phase:** 114
- **Status:** in-progress
- **Depends on:** —
- **Unblocks:** HS-114-02, HS-114-03, HS-114-04
- **Owner:** unassigned

## The thesis (the bar)

A fresh `holdspeak seed` or `POST /api/desk/seed` produces an
immediately usable AI desk: one configured endpoint, one starter
agent, one starter workflow, and config pointers auto-adopted. The
user with a LAN LLM at `192.168.1.43:8080/v1` can seed and ask in
two steps.

## Ground (from the applicability study)

- `fresh-desk.yaml` creates 6 drawers and 2 notes. Zero profiles,
  zero agents, zero workflows. (`holdspeak/seeds/fresh-desk.yaml`)
- `apply_seed()` handles `_SECTION_KINDS` (directories, notes, kbs,
  recipes, chains, workflows) but not profiles.
  (`holdspeak/db/seed.py:35-42`)
- Config defaults leave `profile_id`, `intel_profile_id`, and
  `rails_observer.profile_id` as `None` = hub default. Hub default
  points at local model files that typically don't exist on a fresh
  machine. (`holdspeak/config.py:376,172,803`)
- `discover_endpoint_models()` exists and can query `.43:8080/v1/models`.
  (`holdspeak/setup_runtime.py:41-119`)
- UAT golden deck uses model `Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf`
  for `.43`. (`uat/decks/golden-43.yaml:16,29`)

## Method

1. **Add `profiles` section to `fresh-desk.yaml`.** One "Homelab"
   destination: `id: hs-seed-homelab`, `kind: openAICompatible`,
   `base_url: http://192.168.1.43:8080/v1`, `context_limit: 131072`,
   `requires_key: false`. Model field left empty for auto-discovery.

2. **Add `recipes` section.** One "Architecture reviewer" agent with
   a real system prompt grounded in the Constitution's voice.
   `id: hs-seed-agent-reviewer`.

3. **Add `workflows` section.** One "Summarize material" workflow
   with a single LLM summarize step.
   `id: hs-seed-workflow-summarize`.

4. **Extend `apply_seed()` in `seed.py`.** Handle `profiles` before
   desk primitives (profiles are infrastructure, not desk objects).
   Upsert via `db.profiles.upsert()`. After upserting profiles,
   attempt `discover_endpoint_models(base_url)` — if successful,
   update the profile's model field; if endpoint unreachable, fall
   back to static `Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf`.

5. **Auto-adopt config pointers.** After seeding profiles, check
   `Config.load()`. If `dictation.runtime.profile_id` is `None`,
   point it at `hs-seed-homelab`. Same for
   `meeting.intel_profile_id`. Save config. Report adopted slots
   in the seed report.

6. **Profiles survive `reset_desk()`.** The reset tombstones desk
   primitives; profiles are not desk primitives and must not be
   swept.

7. **Extend `SeedReport` and route responses** to include
   `profiles_seeded` and `profiles_adopted`.

## Acceptance

- `holdspeak seed` on a fresh DB creates the Homelab destination,
  the Architecture reviewer agent, and the Summarize workflow.
- `GET /api/inference-targets` returns the seeded Homelab as ready.
- Config `profile_id` and `intel_profile_id` point at
  `hs-seed-homelab` after seed.
- `reset_desk()` tombstones desk primitives but preserves the
  seeded profile.
- All existing seed tests updated and passing.
- Re-running seed is idempotent (upserts, no duplicates).

## Test plan

- `uv run pytest -q tests/unit/test_desk_seed.py`
- Manual: `holdspeak seed` on a tmp-path DB, verify profile +
  agent + workflow exist and config adopted.

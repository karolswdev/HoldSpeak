# Evidence — HSM-17-01: the agent-session contract + the persona resolution

**Date:** 2026-07-04. The story's two halves landed in two beats: the typed
transport shipped with HSM-17-03, and the naming collision was resolved today
by the owner-ratified **Recipe rename**, executed atomically across every
surface and the wire.

## The transport call (decided + shipped with 17-03)

Coder presence is ephemeral, so it rides a **typed polled endpoint**, never
the durable ChangeSet: `LiveCoderSession` + `IDesktopClient.coderSessions()`
decode `GET /api/coders/sessions` (state, question, identity). Documented
deviation from the story's letter: the typed model lives in **Providers**
beside `CompanionTarget` rather than in Contracts, because that is the
codebase's established home for live companion types (Contracts holds durable
synced models only). `AgentSessionPrimitive` (kind `.coder`) renders it;
its `accepts` gates the dropped-context answer path (17-04).

## The persona resolution (the owner's call: "a rename to recipe")

The user-authored persona subsystem no longer wears the word "agent."
Executed in lockstep, pre-release, no compat shims:

- **Hub**: the `agents` table is `recipes` (SCHEMA_VERSION 8 with an explicit
  rename migration — backup first, rows carried, test-pinned on a v7
  facsimile); `/api/agents*` is `/api/recipes*`; the sync bucket/kind is
  `recipes`/`recipe`; the artifact lineage vocabulary is `recipe` (with a
  tolerant `agent` alias for older clients); `recipe.schema.json` +
  `chain.schema.json` + the ChangeSet envelope schema updated.
- **Swift**: `Contracts.Recipe`, `SyncKind.recipe`, `RecipeRecord`,
  `DeskRecipes.swift` (all types + every user-visible string: the rail tab
  reads **Recipes**, the builder, chat, presets, traits; the stray
  "crew" vocabulary unified to **chain**); `runRecipe` on the desktop client
  (`POST /api/recipes/{id}/run`). The lane filter no longer lumps coders
  under one bucket: **Recipes** and **Coders** are separate chips.
- **Web**: `RecipeRail`, `/api/recipes` fetches, the kind unions, the
  registry blurbs, the companion page copy.
- **The framework doc**: the primitive table rows and the naming law now
  read `recipe` | `coder`, with "agent" in prose meaning a coding agent —
  exactly one meaning per word, the thing this story existed to fix.
- **Coder side untouched**, verified against the danger list
  (`agent_context`, `agent_hook`, `AgentSessionPrimitive`, the coder wire
  field `agent: "claude"|"codex"`).

## Proofs

- The lockstep guards did their job during the work: `test_primitive_contract`
  (hub SYNC_KINDS == schema x-sync-kind set == Swift SyncKind raw values ==
  web TS kinds) failed at every intermediate state and passed only when all
  four surfaces agreed.
- Migration: a v7 facsimile database with rows opens as v8 with the rows in
  `recipes`, the old table gone, and the pre-rename backup on disk.
- Builds: full Python suite green (recorded in the commit); `swift test`
  465 passed / 9 skipped / 0 failures; the simulator app builds (the rename
  pushed the diorama body over the type-checker budget — the overlay sheets
  were extracted into builders, a healthy decomposition); web bundle builds.
- `screenshots/hsm-17-01-recipes-rail.png` — the Recipe builder live in the
  simulator ("OR START FROM A RECIPE", the six presets) with the glaring
  coder behind it: the two concepts, visibly distinct, in one frame.

## Deliberately remaining (moved to the backlog, not silently dropped)

The **rich per-event stream** (the full `CoderEvent` taxonomy over the wire +
persisted replay, the framework doc's wave-3 remit) is a feature build, not a
contract gap: the desk currently renders the honest minimal feed from the
live set. Filed with the option-aware approval card requirement the 17-04
proof surfaced (selector dialogs ignore typed text).

## Also hardened along the way

Two real test-isolation gaps our own dogfooding exposed today: the suite now
isolates the coder-session registry per test (an autouse fixture — the live
hooks were writing the developer's real registry into test runs), and the
blocks/dry-run fixtures chdir to a temp cwd (the repo itself legitimately
became a HoldSpeak project the day the desk was dogfooded on it).

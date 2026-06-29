# Evidence — HSM-24-06 (cross-surface parity proof + docs)

**Date:** 2026-06-28
**Story:** [story-06-proof-and-docs.md](./story-06-proof-and-docs.md)
**Result:** DONE. Profiles are demonstrably in equilibrium across desktop / iPad / iPhone / web; the
key never syncs (proven by a dedicated cross-surface test); the entry-point docs + the security note
ship in this closing commit. **Phase 24 closes.** Full `uv run pytest` **3040 passed, 0 failed**; the
voice guard + docs suite green (158 passed).

## The cross-surface never-sync proof

`tests/integration/test_primitive_framework_sync.py::test_profile_never_sync_holds_across_every_read_surface`
(new) is the phase gate, complementing the existing
`test_profile_syncs_shape_only_and_agent_carries_profile_id`:

- **Two ingresses, both hostile.** A profile is pushed over `/api/sync/push` (the iPad's path) with an
  `api_key`, and a second is created over `POST /api/profiles` (the web's path) with an `api_key`.
- **Every read surface a downstream surface consumes** is asserted key-free: the sync pull
  (`/api/sync/pull`), the list route (`GET /api/profiles`), and the per-id route
  (`GET /api/profiles/{id}`).
- **Shape parity.** Every served profile's field set equals the agreed cross-surface schema exactly
  (`id, name, kind, model_file, base_url, model, context_limit, requires_key, created_at,
  last_modified, deleted`) — no more, no less, and no key field. This proves "same shape, every
  surface," and that parity is achieved by the shape round-tripping intact, not by silently dropping
  data.
- **No key material survives** (`api_key`, `apiKey`, or either secret string) on any read surface,
  from either ingress.

Together with the already-green Apple-side invariant (`apple/Tests/ContractsTests/RuntimeProfileTests.swift`,
the key never on the `Synced`/`ChangeSet` shape) and the hub key-resolution tests (24-04), the chain is
closed: the key lives only in each surface's custodian (iPad Keychain / hub env secret
`HOLDSPEAK_PROFILE_<id>_KEY`) and is joined at request time.

## The docs (entry points)

- **README.md** — the "Everything is local" pillar now names runtime profiles: name your backends as
  reusable profiles and run a different one per agent; the shape syncs, the key stays per-surface.
- **docs/MODELS.md** — a new "Runtime profiles: where each agent runs" section (basic = one active;
  advanced = a named list assigned per agent; the inline "Runs on" control; shape-only sync; honest
  n/a where a surface cannot host a kind; key custody).
- **docs/SECURITY.md** §5 (Secrets handling) — a "Runtime profile keys" bullet: the key is never part
  of the profile and never syncs; each surface holds its own (device Keychain / hub env secret); joined
  at request time; with a note that a regression test asserts it.

## Acceptance criteria → proof

- **One profile, surfaces in equilibrium, key never crosses.** The new cross-surface test proves the
  hub side end-to-end across both ingresses and all read routes; the Apple contract test + 24-04 hub
  tests cover the iPad/desktop custody. ✅
- **The never-sync invariant has a dedicated cross-surface assertion.** It does (above). ✅
- **Entry-point docs + the security note ship in the same closing commit.** README + MODELS + SECURITY,
  this commit. ✅
- **Suites green.** `uv run pytest` 3040 passed; voice/docs guard 158 passed. ✅

## The walked proof (owner, real metal)

The hub + web are verifiable on this machine (the `/profiles` surface + the desk "Runs on" picker were
Playwright-proven in 24-05). The iPad/iPhone leg is the owner's device walk: the latest build with the
Apple profiles UI (ProfilesView, the per-agent "Runs on" chip, the grounding gauge reading the
assigned profile's context limit) is installed on the iPhone 17 Pro Max this session. A live run that
authors a cloud profile on the phone, observes it on the hub/web shape-only, and runs an agent on it
with a real key in `HOLDSPEAK_PROFILE_<id>_KEY` is the owner's to witness; the contract + custody are
proven by the tests above.

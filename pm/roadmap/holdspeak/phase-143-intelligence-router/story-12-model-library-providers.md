# HSEGHS001HS104-143-12 - Model Library and Providers

- **Project:** holdspeak
- **Phase:** 143
- **Status:** in-progress
- **Depends on:** 143-03, 143-11, Phase 142
- **Unblocks:** 143-13, 143-14
- **Owner:** unassigned

## Problem

Models currently mixes setup, provider connection, and immediate Thoughts
assignment. Owners need one compact library while assignments remain unchanged.

## Scope

- **In:** Unified downloadable/detected/installed/connected rows; focused
  Providers for OpenRouter, Anthropic, custom, private, paired, and future
  backends; one Add model flow with Download from catalog, Connect hosted,
  Define endpoint, and Use model file; lawful commands; server truth.
- **Out:** Silent `Download & use`/`Connect & use` and browser recommendations.

## Acceptance criteria

- [ ] Adding a model changes zero assignment revisions and says so explicitly.
- [ ] Huge detected inventories use compact wrapped rows, not cards.
- [ ] Secrets clear only after confirmed save and never enter DOM/projection/log.
- [ ] Broken configured entries remain visible with one repair.
- [ ] Exact selected states are Download, Add to library, Connect, Add model,
  Ready, Checking, Try again, or one typed repair; none implies assignment.
- [ ] 1440 shows six rows/details/action; 393 shows three rows/one action.

## Test plan

- **Unit:** local GGUF/MLX, hosted/custom, storage/license/runtime/key states.
- **Integration:** provider CAS, delayed save, conflict/rebase, restart, secret sentinel.
- **Manual / device:** 1440/393/200% zoom/a11y/no-overflow real-path glass.

## Notes / open questions

Technical provenance and locators stay in explicit owner-only Details.

## Progress

- 2026-08-26 — Plan ratified (`assets/story-12-model-library-plan.md`; six
  ORCH-CALLs accepted incl. the minimal Story-11 HTTP fold-in, Anthropic
  no-false-Ready, and the write-only secret boundary). Round 1 (S1+S2,
  server side): `ModelLibraryApplicationService` + `ModelLibraryProjection@1`
  aggregate (closed action enum, one repair per broken row, assignment-head
  before/after snapshots on every command, never `set_assignment`) with the
  narrow owner-only HTTP seam; availability-only Download / Add-to-library /
  Use-model-file commands (catalog-pinned, durable replay, multipart hub
  staging with verify/ingest/cleanup; old download-and-use names live only
  as compatibility aliases pending the S4 client cutover); new deployments
  stay inactive. Orchestrator-verified: S1+S2 sets + census 49 passed;
  one-path guards 171 passed.
- 2026-08-26 — Round 2 (S3, provider custody + repair truth): explicit
  hosted/custom/paired Connect and Define-endpoint commands (drafts +
  one command; the autosave target editor's server contract retired for
  the ordinary Models path); durable nonsecret provider-command ledger
  (additive `model_library_provider_commands` table with old-shape
  reconcile + canonical snapshot proof) carrying payload-replay
  protection, pending-retry after custody failure, restart-safe receipts,
  and profile/binding CAS; only the dedicated secret body reaches
  ProfileKeyService with the sentinel proven absent from projections/
  exceptions/logs/receipts; OpenRouter/custom/private reach Ready via the
  existing probe, paired rows use liveness truth, Anthropic always
  projects exactly "Anthropic runtime is not installed"; library-minted
  private adapters hidden/refused from the legacy /api/inference-targets
  + /secret side doors; assignment heads byte-checked on every provider
  path and replay. Orchestrator-verified: S3+S1 regression + schema
  proofs 146 passed; guards 171 passed (worker). One guard note: the
  interior-canon left-border CSS failure is inherited baseline, untouched
  by this server-only round.

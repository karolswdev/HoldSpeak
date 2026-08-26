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
- 2026-08-26 — Opus audit of the server half (S1–S3): CLEAN on all seven
  dimensions (zero-assignment runtime enforcement, secret custody with
  exhaustive sentinel matrix, closed action truth incl. Anthropic
  no-false-Ready, one-repair law, authority hygiene + side-door 404s,
  schema discipline, test honesty). One LEDGER note: generic error_500
  logs str(exc) for unforeseeable exceptions — crash-window class, S5
  eyeballs it, no ceremony.
- 2026-08-26 — Round 3 (S4, the glass): Settings Models slot body replaced
  by ModelLibraryCore (flat wrapping radiogroup rows, source tabs, 320px
  detail/action seat, in-world four-entry Add flow, Providers + RAW
  disclosures, egress chips, in-flow states, write-only uncontrolled
  credential handoff, arrow/Escape/Mod+Enter keyboard law);
  InferenceCapabilityPanel + inferenceSetup.ts retired with grep proof
  (no CONNECT & USE / USE MODEL / IN USE / Download & use anywhere in
  web/src); the old hosted flow's Thoughts-pointer mutation is dead with
  its component. Real-hub shots at 1440+393 (populated/empty/error) in
  assets/story-12-shots/, sent to the owner per the shots-before-merge
  law. Orchestrator-verified: component suite 7 passed, e2e 6 passed,
  build green; orchestrator eyeball flags for S5: empty state under the
  joy bar (bare circle + dead space on a first-run screen) and "Ready"
  status copy over an empty library.
- 2026-08-26 — Round 4 (S5, closeout + polish): both joy-bar flags FIXED —
  the empty glass now leads with the four Add-model entries as a centered
  in-flow surface-state choice, and the summary state is server-owned and
  closed (empty→"Add model", never Ready). The audit's error_500 ledger
  note proved real and was FIXED: provider post-routes scrub unexpected
  post-secret exceptions, sentinel proof green. Full matrix + 200% zoom +
  keyboard/screen-reader/reduced-motion legs: glass e2e now 11 tests;
  e2e+secret-boundary 14 passed (orchestrator-verified); one-path guards
  269 passed; web arch/surface guards 13; component 7; build green; npm
  check stops only at 5 inherited raw-token violations (pullout/
  thought-workspace CSS — not this story's), new CSS token-clean. All six
  shots regenerated + populated-1440-zoom200; final review set sent to
  the owner (shots-before-merge law) — orchestrator eyeballed the
  reworked empty 1440 and passes it.
- 2026-08-26 — Closing opus audit (UI half + acceptance): CLEAN on all
  seven dimensions, ZERO product bugs, two cosmetic LEDGER notes (44px
  assertion at 393 only; reduced-motion spot check) — third consecutive
  zero-product-bug audit this story. Verified the error_500 scrub and
  that the receipt copy is validated against the server contract, not
  hardcoded.
- 2026-08-26 — Sweep №1 (6626/21): 12 inherited, 9 branch-new around the
  surface replacement → fix round: hs141/hs142 e2es migrated onto the
  Model Library with behavior preserved (projected truth, one seat,
  byte-server download-verify-add, unchanged assignments); API manifest
  regenerated under isolated HOME (533 routes incl. 7 library routes);
  the Runs-on owner law was a REAL regression — restored as a folded
  server-fact disclosure in the detail pane; census updated with the 8
  true Story-12 decisions; refinement flake serial-green ×2 (ledgered).
  INCIDENT, resolved: the worker first ran the manifest generator
  without isolated HOME against the owner's real DB — the
  migration-marker integrity guard REFUSED and wrote nothing
  (orchestrator forensics on copies: integrity_check ok, schema counts
  identical pre/post, backup retained); rule hardened to
  isolated-HOME-always for DB-opening commands. Orchestrator-verified:
  all nine fix targets 26 passed.

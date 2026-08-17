# Phase 138 — The People Ledger

**Status:** active (2/8).

**Last updated:** 2026-08-17.

## Owner mandate

Implement the first honest delivery slice of issue #458: a People capability for
technical leaders that preserves 1:1 continuity and makes explicit manager
commitments visible in the existing Follow-through surface. The owner explicitly
requested Terra delegates for this phase; that instruction overrides the repository's
historical default-model rule for this run. The primary agent remains final
adjudicator and integrator.

## Goal

Ship an encrypted, local-only organizational relationship and 1:1 foundation whose
explicit manager commitments appear in Follow-through without entering plaintext
product stores.

## Settled design

- People content lives in a separate encrypted envelope store. AES-256-GCM encrypts
  every sensitive payload before SQLite receives it; the random 256-bit key is held
  only by an allow-listed native OS credential store. No plaintext or environment
  fallback exists in production.
- The normal HoldSpeak database, FTS, Memory/Ask, sync, backups, exports, logs,
  receipts, connectors, meetings, and Cadence never receive People content.
- PR1 is manual and notes-only: direct-report, peer, and extended relationships;
  1:1 agenda/prep; durable grounding notes; requests; and an
  explicit request-to-manager-commitment transition. A request is never inferred to
  be a promise.
- Follow-through hydrates People commitments synchronously from the encrypted
  authority and renders them in memory. It persists no People card or bridge row.
  Done/dismiss/reopen dispatch back to People; Cadence, snooze, delegation, and
  background processing are explicitly unsupported.
- People is one singleton Desk surface, not a page and not one desktop object per
  human. Readiness is a hard gate: unconfigured, locked, unavailable, and corrupt
  are named states that never degrade to an empty roster or plaintext scratchpad.
- `shared_intent` is future access intent, not a claim that another participant can
  view data today. PR1 remains this-device-only.
- MCP is a separate explicit disclosure capability: off by default, enabled at
  sidecar start as read or write, and limited to relationship metadata plus
  `shared_intent` records. A source-preserving grounding bundle makes that accepted
  context useful to agentic clients without invoking a model. Leader-private material
  is never serialized to MCP.

## Scope

### In

- Native-key-backed encrypted People sidecar and fail-closed readiness contract.
- Manual direct-report, peer, and extended relationships; notes-only 1:1 sessions;
  agenda/private prep; encrypted grounding notes; requests;
  explicit manager commitments, immutable/superseding accepted records.
- Authenticated loopback API with content-free error codes.
- In-memory Follow-through projection and source-dispatched lifecycle mutations.
- Desk People surface with responsive roster, relationship detail, and terse trust
  facts: `Encrypted`, `This device only`, `Notes only`.
- Security/threat-model documentation, leak tests, focused/full regression gates,
  and a live desktop+narrow walk.
- Default-deny People MCP tools/resources for shared-intent continuity, manual
  grounding, and explicit commitments, with no store setup, archive, capture,
  model invocation, inferred assessment, search, or export.
- In-place commitment execution: explicit Workbench item creation, linked Project
  grounding, hydrated result/status, human-confirmed satisfaction, and history.

### Out

- Audio, recording, transcription, speaker or calendar identity linkage.
- Automatic People inference or inferred assessment, sentiment, ranking, scoring, employment decisions, activity or
  productivity surveillance, and cross-person comparison.
- Growth plans, feedback/review packets, opportunity allocation, team maps.
- Sync, participant sharing, export, backup/recovery, connectors, generic MCP,
  global Search/Ask/Memory, and all leader-private MCP disclosure.
- Cadence collection, Daily Brief projection, scheduled nudges, notifications,
  snooze, and delegation for People commitments.

## Constitutional grounding

- **Articles I–II:** People exists as a Desk primitive/surface with an honest API and
  encrypted authority; no standalone feature page or duplicate task board.
- **Articles III and IX:** confidential third-party material remains local and the
  real encrypted bytes, restart path, and production Desk must be proven.
- **Articles V–VI and XI:** trust-boundary failures are named and content-free;
  consequential setup/visibility operations do not leak content into receipts.
- **Article VII:** editing is in-world, with no modal or prose-heavy alternate UI.

## Stories

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-138-01 | The encrypted boundary | done | [story-01](./story-01-encrypted-boundary.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-138-02 | Relationships and one-to-ones | done | [story-02](./story-02-relationships-one-to-ones.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-138-03 | Commitments join Follow-through | ready | [story-03](./story-03-commitments-follow-through.md) | — |
| HS-138-04 | People belongs on the Desk | ready | [story-04](./story-04-people-desk.md) | — |
| HS-138-05 | The privacy proof | ready | [story-05](./story-05-privacy-proof.md) | — |
| HS-138-06 | The People walk | ready | [story-06](./story-06-people-walk.md) | — |
| HS-138-07 | People through the MCP service boundary | done | [story-07](./story-07-people-mcp.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-138-08 | Commitments become evidenced work | done | [story-08](./story-08-commitment-execution.md) | [evidence-story-08](./evidence-story-08.md) |

## Risk register

| Risk | Guard | Stop signal |
|---|---|---|
| Confidential text escapes to the main DB or a derivative | sentinel byte/table/log/sync/FTS sweep | any sentinel outside encrypted People responses/memory |
| Credential backend silently weakens | explicit native-backend allow-list; memory adapter only in tests | file/plaintext/env backend accepted in production |
| Follow-through creates a second lifecycle authority | projection interface + source-dispatched mutations | People content/status written to `action_items` or Cadence |
| Locked state exposes stale DOM/process data | readiness transition clears DTOs and drafts | name/body remains after 423/409/503 |
| Scope drifts into employment surveillance | policy refusal matrix and no model/network calls | ranking, inference, capture, sync, export, or connector path exists |
| MCP turns local encryption into implicit disclosure | default-off process capability; shared-intent projection; private-ID refusal | private content serialized or People opened without explicit mode |

## Exit criteria (evidence required)

- [ ] Correct key decrypts after restart; missing/wrong/locked key fails closed with
  a stable content-free reason; nonce/AAD substitution fails authentication.
- [ ] Fixture names, agenda, prep, request, and commitment bodies are absent from
  `holdspeak.db`, People DB/WAL/SHM raw bytes, logs, FTS, sync, Cadence, receipts,
  backups, exports, and error/broadcast payloads.
- [ ] Manual relationship → 1:1 → request → explicit commitment persists only in
  the encrypted store; request and commitment lifecycles cannot collapse.
- [ ] One open People commitment renders once in Follow-through in memory;
  done/dismiss/reopen round-trip to the encrypted authority; unsupported verbs
  refuse without mutation; normal action items regress zero behavior.
- [ ] People opens inside Desk at desktop and narrow widths; trust/readiness states
  are factual, no modal/page/score/risk UI appears, and lock clears visible data.
- [ ] Focused backend/web tests, full parallel suite, production web build, and real
  live walk pass; inherited schema-59→60 baseline failure remains separately ledgered.
- [ ] Default MCP cannot open People; read/write modes expose only their named
  capability; leader-private sentinels never cross tool/resource serialization.

## Decisions deferred

- Encrypted People Cadence/Daily Brief overlay — requires a read-time encrypted
  projection; the current persistent Cadence schema is categorically unsafe.
- Key recovery, encrypted backup, rotation UI, and multi-device E2EE — each needs a
  separate destructive/recovery design and live proof.
- Capture consent/boundaries and any source-cited local drafting — design only after
  the encrypted manual loop is proven and issue #450's inference spine is settled.
- Broader People MCP administration, recovery, private-note access, search, or
  model execution over grounding — each remains prohibited rather than implied by owner authority.
- Deliberate relationship-to-meeting-participant association — the People IDs and
  MCP/API boundaries are ready for a future reviewed linker, but PR1 does not infer
  identity from voice, attendance, speaking time, calendar, or behavioral signals.
  The proposed contract and maintainer prompt live in
  [`docs/PEOPLE_INTEGRATION.md`](../../../../docs/PEOPLE_INTEGRATION.md).

## Ledger

- Baseline focused test run was accidentally serial and touched the owner's existing
  schema-59 database before failing at the already-ledgered 59→60 `node_id`
  migration defect. Automatic safety backups were created; no destructive action was
  taken. All phase test commands use xdist's isolated worker homes.
- **Owner verification ruling (2026-08-16):** publication is a draft and testing is
  best-attempt. The primary acceptance method for the handoff is static analysis and
  logical decomposition of each process flow, backed by focused automated checks and
  targeted native/browser proofs. Maintainers must not read this PR as an exhaustive
  end-to-end or full-suite certification; the remaining production walk and broad
  regression responsibility is explicit in the draft PR.
- Integrated evidence before that ruling: 86 focused backend/API/kernel/privacy tests
  green; full web check green (typecheck, architecture/token gates, 934 Vitest tests,
  production build); real macOS Keychain setup/restart/raw-byte proof green; API
  surface and UAT ledgers regenerated. A broad xdist attempt reached 1,426 passes,
  37 skips before stopping on a missing isolated-worker Playwright executable and
  the then-stale UAT ledger (the ledger was subsequently regenerated and its guard
  passed). No exhaustive rerun is claimed.
- Final static counsel found and remediation closed two pre-PR blockers: generic
  Follow-through observation would have copied decrypted People cards into plaintext
  `pipeline_events` (the board observation is now wholly redacted, with a real
  SQLiteObserver sentinel regression), and archived relationships could still be
  fetched/accepted (detail now hides them and the encrypted acceptance transaction
  validates the active relationship). The live synthetic walk also caught accepted
  requests retaining their open UI state; the encrypted request payload now moves to
  `accepted` in the same transaction.
- Real assembled-hub screenshots were captured with a disposable encrypted store at
  1440×1000 and 393×852 under `docs/evidence/people-pr1/`. They demonstrate the Now
  commitment lens and notes-only 1:1 agenda inside the Desk; they are visual evidence,
  not exhaustive certification.

## Counsel ledger (revival, 2026-08-17)

- **(L1)** MCP `_BOUNDARY` constant at `holdspeak/mcp/families/people.py:44-47` uses prose instead of the POSITIONING-canon compact egress format -- should be a terse badge-style disclosure.
- **(L2)** `follow_through_service.py:215` silently returns empty people cards when the sidecar is broken -- no user signal that cards are missing.
- **(L3)** No sanctioned dev-only keystore seam: `store.py:465-466` hardcodes `NativeKeyStore` so the populated People state cannot be walked headlessly. Charter a follow-up for a dev-only seam that is provably unreachable in production.
- **(L4)** People module source cites no Constitution articles in comments.

## Where we are

The close-out is underway on branch `phase-138-close` (2026-08-17, after the
revival merge landed the implementation on main via PR #459). HS-138-01 and
HS-138-02 are done on gate-captured evidence (01: 47 tests — crypto, custody,
policy, store, no-leaks; 02: 20 tests — service lifecycle, roll-forward
successor links, archive hiding, owner auth, keyless readiness). Real-Keychain
manual legs are deferred to the HS-138-06 walk by design. Remaining: 03/05
evidence flips, the story-04 badge-copy amendment (counsel ruled "This device
only" false for the Send-to-Workbench path), and the owner-attended production
walk (06).

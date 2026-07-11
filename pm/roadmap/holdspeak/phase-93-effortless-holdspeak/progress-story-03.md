# HS-93-03 progress record — One professional product voice

**Captured:** 2026-07-11<br>
**Baseline:** `main` at `1e6a28f3` plus the uncommitted HS-93-01/02 working tree<br>
**After build:** current Phase-93 working tree; no commit identity claimed<br>
**Acceptance status:** in progress — the implementation and automated census
are green; owner and physical-device read-through remain acceptance gates.

## Controlled language contract

[`docs/product-language.json`](../../../../docs/product-language.json) is now
registry version 2. It adds product labels and descriptions for Control mode,
destination classes, and lifecycle states while preserving the existing wire
values. The posture mapping is exact:

| Product label | Compatible wire value |
|---|---|
| Secure | `safe` |
| Normal | `neutral` |
| YOLO | `yolo` |

Python, React, and Swift adapters load or mirror this contract and accept either
the product label or compatible wire value at their input boundary. The CLI and
authority API return both forms, so persisted configuration and existing
clients do not silently migrate.

The same registry carries copy-contract version 1: six classifications, five
prohibited operational-pattern families, four generic consequential verbs,
four required failure facts, controlled surface globs, and exact exceptions.
Compatibility exceptions now have a unique id, registry version, kind, bounded
path, terms, and reason.

## Inventory and regression guard

[`holdspeak/product_copy.py`](../../../../holdspeak/product_copy.py) extracts
rendered React/Swift literals and user-facing guide prose, classifies each
candidate, and reports prohibited or ambiguous copy. Inline code examples are
removed from the operational prose before checking; they do not create an
implicit exception for the rest of a line. The registry covers the entire
React client, the entire flagship Swift app, the shared language contracts,
the CLI, the root README, the primary user guides, and the authority UAT packs.

[`phase93_copy_census.py`](../../../../scripts/phase93_copy_census.py) produces
the full JSON inventory or a deterministic summary and exits non-zero on drift.
The captured check reports:

```text
3,919 candidates
  Web:           1,004
  Swift:         1,104
  CLI and guides: 1,811

  Label:            2,376
  State:               40
  Supporting line:    328
  Detail:           1,069
  Error/recovery:     106

0 violations
```

Synthetic unit cases prove each prohibited family and every generic verb can
actually fail the guard. A separate case proves a code span cannot hide bad
surrounding prose.

## Visible convergence

Representative production changes include:

| Before | After / distinction |
|---|---|
| Safe / Neutral | Secure / Normal; wire values remain `safe` / `neutral` |
| Profile as a model destination | Runs on |
| Recipe / Agent / Agent session | Persona / Coder session |
| Chain | Sequence |
| local / on-device / paired described as local | This device / Paired device / Private endpoint / External service |
| Approve generated content | Accept content; Approval remains authority for an exact effect |
| Apply / Open / Run on consequential controls | Apply filters, Review meeting, Run workflow, or another named commitment |
| Proposal / Action as generic product nouns | Proposed action / Action item |
| `pending`, `complete`, or raw status values | Queued, Succeeded, Needs review, Needs approval, or another qualified axis |
| promotional or narrative empty-state copy | a factual state and one next action |
| generic request failures | the failed operation, retained state, destination when relevant, and next action |

The remediation spans AppShell and all React pages/Desk components; flagship
Swift arrival, Desk, Queue, Review, Workbench, Settings, and supporting app
surfaces; CLI and authority responses; UAT language; and current public/user
guides. Review and approval are no longer synonyms: accepting generated content
does not authorize an external effect, while approval copy names the effect and
destination.

## Exceptions

There are two operational generic-verb exceptions, both exact `Open` literals:

- `swift-artifact-open-v1` opens a read-only Artifact inspector.
- `swift-desk-open-v1` opens the selected Desk item's local inspector.

Neither executes, queues, destroys, sends, or grants authority. Five separate
registry-version-2 compatibility entries bound legacy wire/SDK identifiers to
specific persistence, HTTP adapter, Web adapter, Swift contract, and Swift
runtime paths. No `/**` compatibility exclusion is accepted.

## Verification

| Lane | Result |
|---|---|
| Copy census | 3,919 classified candidates; 0 violations |
| Focused/broader Python, integration, and bounded UAT lane | 63 passed |
| Ruff on changed Python and tests | passed |
| Web `npm run check` with NVM Node 22.21.0 | current regression gate: architecture guard passed for 109 source files; typecheck passed; 29 files / 155 tests passed; production build passed |
| Full Swift package | current regression gate: 544 passed, 9 skipped, 0 failed |
| Flagship simulator app build | generated project; `HoldSpeakMobile` Debug iPhoneSimulator build succeeded |
| Patch hygiene | `git diff --check` passed |

The app build retains existing compiler warnings in unrelated concurrency and
deprecated-API paths; it introduced no build failure.

## Acceptance still required

HS-93-03 remains open. The owner must read all ten primary journeys on the
API-backed production Web client and physical iPhone/iPad without repository
context, predict each consequential action, and record every misunderstood noun,
state, destination, boundary, or commitment. Forced-failure walks must also
confirm the rendered combination of failed operation, retained work, relevant
destination, and next valid action. Automated source inventory and simulator
compilation do not substitute for that evidence.

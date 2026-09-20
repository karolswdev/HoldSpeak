# Source hierarchy and reconciliation

Status: source audit at `675401a857b85336d4acaa8c65383dfc9636e4c8`.
The owner's current request authorizes Astra and Luna xhigh to complete this
package without Muad'Dib. Earlier plan checks remain historical evidence.

## Authority and observation

| Source | What it establishes | What it cannot establish |
| --- | --- | --- |
| Current owner instructions | Scope, exception to the two-brain procedure, clone and delivery ownership | Runtime behavior |
| [Constitution](../CONSTITUTION.md) | Product principles and required architecture | That every path conforms |
| [Agent brief](../AGENT_BRIEF.md), [UX Canon](../UX-CANON.md) | Development and face laws | Accessibility or owner-use results |
| [Design system](../DESIGN_SYSTEM.md), [Desk grammar](../DESK_GRAMMAR.md) | Tokens, window/object grammar | Current implementation of each remainder |
| [Icon discipline](../../../web/ICON-DISCIPLINE.md), [surface contract](../../../web/src/desk/surface/contract.md) | Component and sprite contracts | Behavior outside their jurisdiction |
| [Frontend architecture](../ARCHITECTURE_WEB_FRONTEND.md) | Client boundaries | Authority above Constitution/UX Canon |
| Current production source and imports | Executable paths and ownership | That an optional path is configured or publicly released |
| Tests and their assertions | Behavior represented by a particular fixture | Live provider, hardware or owner-desk observations |
| Test run records | What ran in the recorded environment | Behavior in untested environments |
| Roadmap and historical summaries | Intent, rationale and dated evidence | Newer implementation state |
| Supplied research briefs | Questions to investigate | Verified source citations or shipped capability |

For normative conflicts, the higher product rule controls the proposed fix.
For descriptive claims, follow the executable source and inspect assertions.
Keep a discrepancy visible until a fix or an explicit product decision resolves
it. Neither prose authority nor a green type check makes an unobserved user
journey complete.

## Reconciliation ledger

| Finding | Evidence | Disposition | Tenet |
| --- | --- | --- | --- |
| Product is broader than voice-typing metadata | `pyproject.toml` description/classifier versus runtime packages and README | Record the mismatch; keep package identity change a product decision. The short guide describes the four jobs without upgrading maturity. | 2, 3 |
| Brief assumes a journal-only kernel | `holdspeak/kernel/broker.py`, `admission.py`, `executor.py` | Corrected in KERNEL: admission and execution already exist. No proposed replacement kernel. | 1, 3 |
| Brief assumes separate confirmation for all effects | Constitution XI.4, `holdspeak/kernel/admission.py`, `docs/AUTHORITY.md` | Operation-specific authority map; retain gesture and bounded-grant semantics. | 1, 3 |
| Frontend architecture recommends modal Dialog | `docs/internal/ARCHITECTURE_WEB_FRONTEND.md` Interaction grammar versus UX Canon no-modal law | Corrected the stale recommendation to in-place controls/nonmodal windows. No product component changed. | 5, 6 |
| Database version refusal and universal pre-change backup are assumed | `holdspeak/db/core.py::_ensure_schema`, `holdspeak/db/reconcile.py::reconcile_schema` | Corrected storage/release docs: version stamp is informational; known tables/triggers can be rebuilt; automatic backup follows some shape changes. Added executable claim probe. | 1, 3 |
| Workbench vision is treated as future redesign | `docs/internal/DESK_GRAMMAR.md`, `web/src/desk/` | Catalogue existing components and behavior; classify missing contracts separately. | 5, 6 |
| Generated rider says MCP is wired although configuration has only holdspeak | `.githooks/dw_pmo/agentdocs.py`, `.mcp.json` | Corrected template to conditional configuration wording and regenerated managed blocks. No MCP server enabled. | 3 |
| Existing census and API/docs guards are omitted in brief | `docs/internal/INVENTORY-2026-09-19.md`, `scripts/gen_api_surface.py`, `tests/unit/doc_claims/registry.py` | Reuse source inventories and guards; add traceability instead of another truth engine. | 1, 3 |
| Dated counts presented as current facts | supplied briefs; generated API and repository rosters | Use generated snapshot counts with scope labels. Route, file, table and capability counts remain distinct. | 3, 4 |
| iPad implementation equated with distribution | `apple/` and README unreleased statement | Separate built code, tests, release evidence and device observations. | 2 |
| Host wrapper appears in new brief despite earlier scope exclusions | historical design records versus current request | Proposed bounded-host ADR and research prototype scope; no second UI architecture. | 5, 6 |

## Document ownership

Existing focused public guides remain user-task owners. New architecture guides
link to those guides and record implementation evidence. They do not replace
product rules merely because they are newer files. The [mechanical document
index](../../generated/document-status.json) routes all baseline Markdown into
public, generated, plan or internal classes; its heuristic classifications are
not individual ratification decisions.

The source-input `.txt` files are immutable research archives, not product docs.
The [metadata contract](data/README.md) owns Philo's generated registry inputs.
Generated output must name its snapshot and generator. The final report owns
verification results and unresolved gaps; do not scatter conflicting pass counts
across the user guides.

## Final descriptive corrections

Four existing known-false claim records are corrected without implementing the
missing runtime behavior: MCP bind_host is stored without a network fence; the
MCP verb catalogue is a subset; the Desk snapshot has seven record lists, not
layout; and the SwiftUI component pattern is iPad-specific. The claim ratchet
now checks these narrower truths. Thread slash execution belongs to the
composer/pullout, so empty metadata runners do not prove unavailable commands.

# Phase 143 delivery map

This is the implementation routing table. Story files own exact acceptance;
this map names the likely code seams and the gate that prevents authority forks.

| Story | Primary implementation seams | Required gate |
|---|---|---|
| 01 Census | `holdspeak/inference_targets.py`, `holdspeak/services/profile_service.py`, `holdspeak/kernel/{inference,inference_runner}.py`, `holdspeak/{meeting_session,speech_session}/`, Config, Workbench/Recipe/Agent/background callers | Generated capability/pointer/resolver/physical-leaf inventory equals reviewed fixture |
| 02 Registry | new `holdspeak/inference_capabilities.py`; composition in server/runtime/plugin setup | Unknown/duplicate/confusable capability refuses startup; every call site mapped |
| 03 Profiles | existing `profile_service.py`, `target_profile.py`, `deployment_revisions.py`, setup/acquisition services, schema/migrations | OWNER at service boundary; no new revision registry; no path/secret sync |
| 04 Assignments | new routing application/service + DB repository/schema; legacy Config/subject adapters | Atomic ordered-chain CAS; no dual authority after family marker |
| 05 Plans | new immutable route-plan DTO/repository/resolver beside `inference_runner.py` | Zero-write/network resolution; mutation after freeze cannot retarget |
| 06 Controller | new route controller/ledger; existing parent-run and inference outcome seams | Every physical try is a unique admitted child; forbidden dispositions create zero egress |
| 07 Thoughts/writing | refinement coordinator/application, Ask service, speech intent/rewrite/punctuate, Workbench UI | Visible next chain frozen with reservation; old pointer no longer read |
| 08 Meetings/speech/background | `meeting_session/intel_*`, `speech_session/*`, Rails, cadence, decisions, delivery | Preserve history/restart; distinct leg/attempt ordinals; generated fork census zero |
| 09 Tools | implement ruled ToolTurn controller/private lease/ledgers, then routing application | Lease never expands; effects adopt once; unknown completion never falls back |
| 10 Agents/workflows | Workbench/Recipe services, agents, sequences/workflows, mutable `kernel/inference.py` | Shared resolver only; `inference.run` cannot late-route physical work |
| 11 Parity/sync | web routes, `mcp/{tools,resources,server}.py`, `sync_service.py`, inventories | Golden HTTP/MCP parity; non-owner nondiscovery; sync zero egress |
| 12 Library/providers | `InferenceCapabilityPanel.tsx`, `settingsModels.tsx`, setup/profile/provider services | Add/connect/download changes zero assignments; secret/path sentinel |
| 13 Assignments UX | new shared web assignment model/components/controller and reuse in subject surfaces | Bounded overview, one atomic editor, 1440/393/a11y one-primary glass |
| 14 Closeout | unit/integration/E2E fixtures, schema/API/MCP inventories, evidence ledger | Every architecture kill criterion disproved on real application paths |

## Delivery waves

1. **Authority:** 01 → parallel 02/03 → 04 → 05 → 06.
2. **First usable vertical:** 07 + 11 foundations + 12/13 minimal Library and
   Thoughts assignment. This is the first shippable route-chain product.
3. **Horizontal adoption:** 08, then 09 when Tool Capability Foundation exists,
   then 10. Families land with one-way migration markers, never a big-bang flag.
4. **Close:** complete 11–13 parity/glass and run 14 chaos.

## Standard story evidence

Every implementation story records:

* changed authority/schema and migration/replay behavior;
* focused unit and integration commands with counts;
* one-path and legacy-pointer census deltas;
* HTTP/MCP/sync/privacy results where applicable;
* 1440/393/200% captures for visible work;
* known inherited failures separated from story-caused failures;
* `git diff --check`, production build, API/MCP/schema inventories, and `dw
  check holdspeak` at the appropriate gate.

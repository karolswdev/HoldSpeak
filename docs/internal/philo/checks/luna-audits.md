# Bounded Luna audit records

Two read-only agents ran on `gpt-5.6-luna`, reasoning `xhigh`, against snapshot
`675401a857b85336d4acaa8c65383dfc9636e4c8`. They were instructed to avoid all
edits, tests, runtime state, staging and external contact. These are condensed
reports, not completed capability verification.

## philo_kernel_desk

The agent found that the kernel covers admission, authority, execution and
receipts. It cited Broker submission and decision code, ExecutorPlane claim and
receipt code, JournalStore, and Constitution Article XI. Astra inspected the
admission, claim and restart paths for the initial findings.

It identified existing contracts in DeskWindowFrame, SurfaceWindows,
verbRegistry, dropMatrix and the surface component barrel. It also reported a
local Workbench drop grammar at `web/src/desk/components/WorkbenchWindow.tsx:576`
and `:1364`. That exception needs verification during the full interaction audit.

It distinguished direct owner gestures from separate proposal decisions. It
cited `holdspeak/desktop_typing.py:63`, `:106`,
`docs/internal/DICTATION_COMMIT_BOUNDARY.md:32`, and
`holdspeak/operation_policy.py:228`, `:289`. Constitution XI.4 independently
confirms the normative gesture rule. Runtime completeness remains unverified.

It reported a possible wording conflict between POSITIONING's per-action human
approval claim (`docs/internal/POSITIONING.md:63`) and scoped grants in the
operation policy (`holdspeak/operation_policy.py:289`). Do not resolve that
claim without tracing authority in the affected action path.

## philo_scope

The agent recommended preserving Phase 201 file ownership, reconciling the
September inventory, and extending `docs/ARCHITECTURE.md` and existing API/MCP
generators rather than duplicating their output. Astra verified the current
phase scope, API reference owner and contributor check commands.

It recommended keeping domain-owned registries and generating cross-domain
views. It cited `holdspeak/product_language.py:99` and its tests, alongside the
existing claims registry. Astra inspected the Claim structure and CLI before
incorporating reuse into the plan.

It pointed to `docs/internal/PLAN_WORKBENCH_ARCHITECTURE.md` as existing RFC
material, and described `docs/workbenches.json` as potentially orphaned. The
orphan claim is not independently verified and remains a discovery candidate.

Two recommendations require qualification: runtime Workbench skills cannot
replace repository coding-agent skills, and the Workbench object RFC cannot
replace the broader Desk SRS. The revised plan records both distinctions.

## Limits

Neither audit inspected a live hub, owner DB, model result or rendered face.
No test run, release status, complete census or usability result is claimed.
Unverified leads above are inputs to the next audit, not established defects.

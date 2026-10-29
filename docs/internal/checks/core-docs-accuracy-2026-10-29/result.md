# Extended documentation accuracy audit, 2026-10-29

Source base: `4dce2796d`. Branch: `docs/core-docs-accuracy`.

## Result

Reviewed the 71 top-level guides plus README and CONTRIBUTING against current source. Updated **43 public documents**. The other 30 retain their text after source or generated-contract checks. The coverage file records 217 initial claim checks plus six integration corrections, with source anchors and per-guide unknowns. This is a guide-level source audit, not exhaustive certification of every endpoint or a live deployment.

The review checks active registrations and call paths. A symbol in parked code, an API route, a model response, and a completed external effect are different evidence. No product code or configuration default changed. Two documentation generators and their two regression cases changed to keep generation tied to the current checkout.

## Material corrections

- Current Settings paths, engine verbs, Window menu entries, shortcuts, Memory controls, and Calls labels replace stale interface instructions. Static primitive descriptors are identified separately from current host affordances.
- The ordinary iPad voice composer does not supply a stable delivery ID or retry automatically. The separate paired-delivery API has a different contract. The guide no longer promises universal retry deduplication.
- Hook status does not establish voice-reply readiness. A selected reviewer starts after a builder commit. An already-active Reach sweep is a successful no-op, not the documented error exit.
- Meeting, dictation, activity, and device guides now state actual routing defaults, microphone endpoints, correction limits, queue/recovery behavior, and transport settings.
- Core inference and separate Line Parakeet/Pocket speech are scoped correctly. Kernel parent snapshots can retain caller prompt text; the docs no longer imply all kernel records are content-free. Modes, saved conversations, parked Thread controls, memory defaults, and desk pages match active code.
- SDK docs distinguish proposal, approval, and execution. Meeting approval does not run an actuator. Bare SDK executors can lack a kernel broker and Receipt. Webhook deduplication does not include the configured URL.
- Stored meeting actuator flags do not disable or narrow current Desk/Mission Control executors. The actual operation, proposal, destination, and connector checks are documented instead. This implementation gap remains product follow-up.
- Calls selection now describes off-switch precedence, explicit choice, the ai-phone command override, and binary/node configuration detection. A configured node is not proof of enrollment or readiness.
- API inventory labels describe reference-app registration and static client matches, including parked code and named refusals. Capability and platform tables explicitly identify their pinned, non-exhaustive metadata scope.
- A shared Python environment could import another checkout during generation. Both affected generators now resolve their own checkout first. The regression cases use an unrelated working directory and foreign package path. Regeneration again yields 877 routes, with no unmatched-client warning.

## Validation

All pytest runs used the machine lock and an isolated HOME.

- Focused collection: **129 tests collected in 0.96s**. Execution: **129 passed in 5.33s**. This includes generator checkout selection, API/architecture contracts, connector fixtures, plugin idempotency, actuator gates, dictation delivery, device handshakes, and graph-reference tests.
- Final required quick check: build passed; **104 affected tests passed in 5.09s**; **124 Desk sweep cases passed in 73.39s** at desktop and phone widths; **27 canon checks passed in 5.27s**; **1,156 repository guards passed in 32.77s**.
- Both documented manifest examples validate. The documented connector fixture passes against an isolated temporary database without preview writes or external calls.
- Navigation: **73 public documents checked**. Mermaid: **27 diagrams parsed**, no syntax failures.
- Architecture metadata: **4 shards, 157 records**, no validation error. All **10 generated outputs** check current. Configuration and supplementary API references check current.
- Source-anchor validation found no remaining missing file or out-of-range first anchor in the audit rows. Earlier incorrect worker citations were repaired against actual files; the per-guide source-review limits remain explicit.
- Ruff passes for the two changed generators and new regression test. Final focused generator/architecture checks after removing an unused import: **21 passed in 1.97s**.
- `git diff --check` passes.

The first quick check had one bare-Desk stillness failure: two chrome controls moved 27 pixels. Its other 123 sweep cases passed. The complete repeat passed all 124; no product code, test, or threshold was changed to excuse it. Initial generator attempts also exposed the wrong-checkout import defect; the corrected generation and regression tests above supersede those attempts.

Raw run logs and example/render reports are under `.tmp/docs-accuracy-*`. The isolated quick sweep is fixture evidence, not observation of the owner's live Desk.

## Independent check

Two read-only Claude CLI advisory passes were invoked by Astra. The first found the remaining actuator-policy and Calls-selection defects; root checked and corrected them. The bounded second pass found no material error in that corrected seam. `claude-advice.md` preserves both responses. This is ADVICE, not Muad'Dib's check; the separate fast-cycle post-merge review remains unobserved.

## Open implementation and observation limits

- Decide whether to wire or retire `meeting.allow_actuators` and `meeting.allowed_actuators` for Desk/Mission Control. The stored values are currently not effective gates there.
- The private helper docstring in `holdspeak/web/routes/actuator_shared.py:168` still lists the meeting decision route as an execution caller; actual service code does not execute it.
- The Firefox add-on has no runtime-credential setting. The guide now puts this authenticated-ingestion gap before installation instructions.
- The memory page module docstring describes two desk pages, while the active page set contains three. The guide follows the active set.
- No physical iPad/ESPHome board, signing/build installation, microphone, live line/carrier, external provider, actual send, owner scheduler, or live backup/restore was exercised. Source contracts and fixture tests do not establish those deployment facts.
- The existing remote web-quality CSS token gate remains a separate source issue (184 raw values in unchanged product files).

## Coverage

Each row points to its lane audit JSON. `integration-addenda.json` records corrections made after the independent advisory. Generator-owned documents retain their generation and snapshot semantics.

| Document | Disposition | Evidence |
| --- | --- | --- |
| `CONTRIBUTING.md` | corrected | [root-audit](root-audit.json) |
| `README.md` | corrected | [root-audit](root-audit.json) |
| `docs/ACTIVITY_PREBRIEFING.md` | corrected | [capture-audit](capture-audit.json) |
| `docs/ACTUATOR_DEVELOPMENT.md` | corrected | [sdk-audit](sdk-audit.json), [integration-addenda](integration-addenda.json) |
| `docs/AGENTS_AND_THREADS.md` | source_checked_unchanged | [agents-audit](agents-audit.json) |
| `docs/AGENT_HOOK_INSTALL.md` | corrected | [agents-audit](agents-audit.json) |
| `docs/AIPI_LITE.md` | corrected | [root-audit](root-audit.json) |
| `docs/AIPI_LITE_DEV_WORKFLOW.md` | corrected | [root-audit](root-audit.json) |
| `docs/API_REFERENCE.md` | generated_checked | [root-audit](root-audit.json) |
| `docs/API_SURFACE.md` | generated_checked | [root-audit](root-audit.json) |
| `docs/ARCHITECTURE.md` | corrected | [architecture-audit](architecture-audit.json) |
| `docs/ARCHITECTURE_WORK.md` | source_checked_unchanged | [daily-audit](daily-audit.json) |
| `docs/AUTHORITY.md` | source_checked_unchanged | [capture-audit](capture-audit.json) |
| `docs/AUTHORITY_MODEL.md` | source_checked_unchanged | [capture-audit](capture-audit.json) |
| `docs/AUTOMATION.md` | source_checked_unchanged | [agents-audit](agents-audit.json) |
| `docs/CADENCE.md` | source_checked_unchanged | [agents-audit](agents-audit.json) |
| `docs/CAPABILITIES.md` | generated_checked | [root-audit](root-audit.json) |
| `docs/CODER_INTEGRATION.md` | corrected | [agents-audit](agents-audit.json) |
| `docs/COMPANIONS_ARCHITECTURE.md` | corrected | [root-audit](root-audit.json) |
| `docs/CONFIGURATION_REFERENCE.md` | generated_checked | [agents-audit](agents-audit.json) |
| `docs/CONNECTOR_DEVELOPMENT.md` | corrected | [sdk-audit](sdk-audit.json) |
| `docs/DATA_MODEL.md` | source_checked_unchanged | [architecture-audit](architecture-audit.json) |
| `docs/DESK_ARCHITECTURE.md` | corrected | [root-audit](root-audit.json) |
| `docs/DESK_MEMORY.md` | corrected | [daily-audit](daily-audit.json) |
| `docs/DESK_OBJECT_MODEL.md` | corrected | [root-audit](root-audit.json) |
| `docs/DEVICE_PROTOCOL.md` | corrected | [capture-audit](capture-audit.json) |
| `docs/DICTATION_ARCHITECTURE.md` | corrected | [capture-audit](capture-audit.json) |
| `docs/DICTATION_COPILOT.md` | source_checked_unchanged | [capture-audit](capture-audit.json) |
| `docs/DICTATION_PIPELINE_GUIDE.md` | corrected | [capture-audit](capture-audit.json) |
| `docs/DOMAIN_MODEL.md` | corrected | [architecture-audit](architecture-audit.json) |
| `docs/ENVIRONMENTS.md` | corrected | [daily-audit](daily-audit.json) |
| `docs/EXECUTION_DESTINATIONS.md` | source_checked_unchanged | [agents-audit](agents-audit.json) |
| `docs/FIREFOX_EXTENSION_GUIDE.md` | corrected | [root-audit](root-audit.json) |
| `docs/GATE.md` | source_checked_unchanged | [agents-audit](agents-audit.json) |
| `docs/GETTING_STARTED.md` | corrected | [daily-audit](daily-audit.json) |
| `docs/GLOSSARY.md` | corrected | [daily-audit](daily-audit.json) |
| `docs/INFERENCE_TARGETS.md` | source_checked_unchanged | [agents-audit](agents-audit.json) |
| `docs/INTEGRATIONS.md` | corrected | [agents-audit](agents-audit.json), [integration-addenda](integration-addenda.json) |
| `docs/INTERVIEW.md` | source_checked_unchanged | [daily-audit](daily-audit.json) |
| `docs/IPAD.md` | corrected | [root-audit](root-audit.json) |
| `docs/KERNEL.md` | corrected | [architecture-audit](architecture-audit.json) |
| `docs/MCP_SIDECAR.md` | source_checked_unchanged | [agents-audit](agents-audit.json) |
| `docs/MEETING_AFTERCARE.md` | corrected | [capture-audit](capture-audit.json) |
| `docs/MEETING_ARCHITECTURE.md` | source_checked_unchanged | [capture-audit](capture-audit.json) |
| `docs/MEETING_INTELLIGENCE.md` | corrected | [capture-audit](capture-audit.json) |
| `docs/MEETING_MODE_GUIDE.md` | corrected | [capture-audit](capture-audit.json), [integration-addenda](integration-addenda.json) |
| `docs/MODELS.md` | source_checked_unchanged | [agents-audit](agents-audit.json) |
| `docs/MODEL_RUNTIME.md` | source_checked_unchanged | [agents-audit](agents-audit.json) |
| `docs/OPERATIONS.md` | source_checked_unchanged | [agents-audit](agents-audit.json) |
| `docs/PEOPLE_INTEGRATION.md` | source_checked_unchanged | [daily-audit](daily-audit.json) |
| `docs/PEOPLE_SECURITY.md` | source_checked_unchanged | [capture-audit](capture-audit.json) |
| `docs/PLATFORMS.md` | generated_checked | [capture-audit](capture-audit.json) |
| `docs/PLUGIN_AUTHORING.md` | corrected | [sdk-audit](sdk-audit.json) |
| `docs/PROJECT_ROOMS.md` | corrected | [daily-audit](daily-audit.json) |
| `docs/REACH_RUNNER.md` | corrected | [agents-audit](agents-audit.json) |
| `docs/README.md` | corrected | [root-audit](root-audit.json) |
| `docs/RELATIONSHIP_AWARE_MEMORY.md` | corrected | [architecture-audit](architecture-audit.json) |
| `docs/RELEASING.md` | source_checked_unchanged | [capture-audit](capture-audit.json) |
| `docs/SECURITY.md` | source_checked_unchanged | [capture-audit](capture-audit.json) |
| `docs/SECURITY_MODEL.md` | source_checked_unchanged | [capture-audit](capture-audit.json) |
| `docs/STORAGE_AND_MIGRATIONS.md` | source_checked_unchanged | [capture-audit](capture-audit.json) |
| `docs/SYSTEM_ARCHITECTURE.md` | corrected | [architecture-audit](architecture-audit.json) |
| `docs/SYSTEM_INTEGRATION_MAP.md` | source_checked_unchanged | [architecture-audit](architecture-audit.json) |
| `docs/TROUBLESHOOTING.md` | source_checked_unchanged | [agents-audit](agents-audit.json) |
| `docs/USER_GUIDE.md` | corrected | [daily-audit](daily-audit.json) |
| `docs/USE_CASES.md` | source_checked_unchanged | [daily-audit](daily-audit.json) |
| `docs/VOICE_COMMANDS.md` | corrected | [capture-audit](capture-audit.json) |
| `docs/WEB_DESK.md` | corrected | [daily-audit](daily-audit.json) |
| `docs/WEB_UI_UX_SYSTEM_AUDIT.md` | corrected | [root-audit](root-audit.json) |
| `docs/WHAT_IS_HOLDSPEAK.md` | source_checked_unchanged | [daily-audit](daily-audit.json) |
| `docs/calls.md` | corrected | [daily-audit](daily-audit.json), [integration-addenda](integration-addenda.json) |
| `docs/phone.md` | source_checked_unchanged | [daily-audit](daily-audit.json) |
| `docs/programs.md` | corrected | [daily-audit](daily-audit.json) |

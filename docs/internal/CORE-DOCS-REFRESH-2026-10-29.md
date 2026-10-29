# Core documentation refresh, 2026-10-29

Status: DRAFT. UNCHECKED — awaiting Muad'Dib.

## Current source correction

The initial local `main` was stale. Advisory review found `origin/main` 153 commits ahead, including Programs, Calls, Phone, and newer Ask/engine controls. The initial audit is preserved in `d60dc2c83` on `docs/readme-agentic-os`; its 130 passing documentation checks apply only to that source base.

The active worktree is now `/Users/karol/.codex/worktrees/core-docs-current/HoldSpeak`, branch `docs/core-docs-refresh`, based on `c161be0e8`. Rewrite drafts were transferred through file-level three-way merges, preserving new upstream files. Conflict inputs live under `.tmp/core-merge/` as `.ours` (rewrite), `.base` (initial source), and `.theirs` (current main). No Git checkout, reset, stash, restore, clean, or switch is used.

All current UI and behavior claims must be reconciled against this fresh source. Generated files remain current-main-owned until regeneration. Earlier source and test results are historical, not final verification. Add and integrate the current Programs, Calls, and Phone flows and their availability limits.


The owner requested a rewrite and update of all core documentation, continuing the README work on this worktree. His product definition is an agentic-first, web-based AI operating system. Document the implemented flows without converting planned work into shipped claims.

## Settled design

- One narrative: Desk objects and context, Ask/Threads with tools, coding-agent handoffs, automation, inspection and follow-through.
- Voice typing and meeting capture remain first-class inputs. They do not limit the product definition to two modes.
- Explain prerequisites, trigger, action, result, persistence, execution host, and relevant limits at the point of use.
- Use simple American English and exact current UI labels. Follow `docs/internal/DOCS_STYLE.md`.
- Distinguish a CLI used as an inference engine from a launched coding agent, and a persona from either.
- Generated inventories retain their source ownership. Update them through their generators only when needed.
- Preserve valid technical detail and inbound anchors. Remove obsolete instructions from active guidance. Do not rewrite historical evidence or amend the Constitution.
- No product code changes, installs, real Desk writes, external sends, launched product agents, or hardware walks.

## Worktree and lanes

All lanes edit disjoint files in `/Users/karol/.codex/worktrees/readme-agentic-os/HoldSpeak`, branch `docs/readme-agentic-os`. Base at start: `8deea2888`. Anchors can drift as sibling lanes write: re-read exact files before changing a reference.

| Lane | Files | Responsibility |
| --- | --- | --- |
| Daily work | Getting Started, User Guide, Desk, Use cases, Architecture work, Interview, Project Rooms, Environments, Desk Memory, People integration, Glossary | Rewrite task journeys and reconcile active controls. |
| Agents and operations | Agents and Threads, Automation, Coder integration, Agent hooks, MCP sidecar, Reach Runner, Gate, Cadence, Integrations, Models, Inference targets, Execution destinations, Configuration reference, Troubleshooting, Operations | Rewrite delegation, recurring work, engine selection, operational recovery. |
| Capture and boundaries | Meeting mode, Aftercare, Intelligence, Meeting architecture, Dictation pipeline, Dictation Copilot, Dictation architecture, Voice commands, Activity prebriefing, Security, People security, Authority, Authority model, Security model, Platforms, Releasing, Storage and migrations | Reconcile capture, boundary and recovery contracts with the product source. |
| Root | Overview, documentation index, system/runtime/domain/Desk architecture references, extension references and inventory review, contributor entry, coverage record | Integrate the product model, check technical accuracy, validate links/claims and record remaining limits. |

## Validation and shipping

Workers run only `python3 scripts/check_docs.py <their Markdown paths>` and `git diff --check`. No pytest, vitest, browser suite or graph walk in worker lanes. The root runs scoped navigation, drift, registered-claim and generated-inventory guards under `scripts/test_lock.py` with an isolated HOME. No full suite or metal tests. Product code is unchanged, so screenshots cannot establish a new documentation claim. A browser or hardware flow is not claimed observed from source inspection.

Workers never stage or commit. Return changed paths, source anchors checked, exact validation output and limits, then hold for SHIP. The root serializes explicit-path staging and commits. No merge is authorized by this record.


## Current-source result

The active rewrite is based on `c161be0e8`. It updates 64 of the 73 public Markdown documents in the entry/index set. The other nine were reviewed and retained because their technical contract remains useful or a generator owns the file. Programs, Calls, The Line, and Phone are part of the current product narrative. The incomplete iPhone-app transport is not presented as delivered.

Source integration resolved the stale-base finding without moving or cleaning either checkout. The earlier work is preserved on `docs/readme-agentic-os`; the fresh branch is `docs/core-docs-refresh`. No product code, configuration defaults, tests, or installed packages changed.

### Verified on the current source

- Focused collection: **130 tests collected in 0.40s** across navigation, doc drift, MCP roster, registered claims, API roster, architecture tooling, and graph-reference tests.
- Quiet-tree run, under the machine lock with an isolated HOME: **130 passed in 5.65s**.
- Public navigation: **73 documents checked**, all local links and heading targets resolve.
- Mermaid syntax: **28 diagrams parsed** across 72 Markdown files containing README and the public guides; no parse failures. This is syntax validation, not screenshot rendering.
- Architecture metadata: **4 shards, 157 records, validation passed**.
- Architecture generation: **10 outputs checked** after regeneration from corrected metadata.
- Configuration and API reference generators: current and checked.
- `git diff --check`: passed; no conflict markers remain.

The source-data repair updates 12 stale paths/anchors. A renamed assertion is marked `not_run` rather than inheriting an earlier passing execution. Other moved test records retain their historical provenance. Generated evidence counts remain historical and do not claim new runtime execution.

No full application suite, browser, microphone, provider, live call, agent launch, external send, or owner Desk write was used for this documentation change. The required pre-merge quick check has not run. This handover prepares a documentation draft for review and does not merge it. No new screenshot or owner aesthetic acceptance is claimed.

### Main corrections checked against implementation

- `AskPanel.tsx` and `askFace.tsx`: automatically retained conversation, Recent rail, ⌘N, scope menu, References, and separate Note/task actions. Parked Thread mode, slash, fork, and call controls are identified as API/parked capabilities.
- `desk_window_service.py` and `compositor/hubWindows.ts`: shared hub windows, view-local contextual exceptions, and browser cache.
- `mcp/server.py`, tool authority, resources, and People configuration: proxy-only sidecar, current 306-tool roster, resource discovery counts, saved People setting, environment override, and launched-agent read scope.
- `program_service.py`, `program_runner.py`, `program_rules.py`, `program_verifier.py`, and `program_handoff.py`: conditional gates, control ladder, usage handoff, owner questions, and repository evidence.
- `calls/`, `line/`, and `phone/`: line adapter, authenticated turns, confirmation, stored call output, attention rules, and the incomplete app transport.
- `recipe_catalog.py` and its routes: read-only descriptor/plan catalogue, separate from executable feature controls and general Automation scheduling.

### Public document coverage

| Document | Disposition |
| --- | --- |
| `README.md` | Updated and reconciled against the current source. |
| `CONTRIBUTING.md` | Updated and reconciled against the current source. |
| `docs/ACTIVITY_PREBRIEFING.md` | Updated and reconciled against the current source. |
| `docs/AGENTS_AND_THREADS.md` | Updated and reconciled against the current source. |
| `docs/AGENT_HOOK_INSTALL.md` | Updated and reconciled against the current source. |
| `docs/AIPI_LITE.md` | Updated and reconciled against the current source. |
| `docs/ARCHITECTURE.md` | Updated and reconciled against the current source. |
| `docs/ARCHITECTURE_WORK.md` | Updated and reconciled against the current source. |
| `docs/AUTHORITY.md` | Updated and reconciled against the current source. |
| `docs/AUTHORITY_MODEL.md` | Updated and reconciled against the current source. |
| `docs/AUTOMATION.md` | Updated and reconciled against the current source. |
| `docs/CADENCE.md` | Updated and reconciled against the current source. |
| `docs/CODER_INTEGRATION.md` | Updated and reconciled against the current source. |
| `docs/COMPANIONS_ARCHITECTURE.md` | Updated and reconciled against the current source. |
| `docs/DATA_MODEL.md` | Updated and reconciled against the current source. |
| `docs/DESK_ARCHITECTURE.md` | Updated and reconciled against the current source. |
| `docs/DESK_MEMORY.md` | Updated and reconciled against the current source. |
| `docs/DESK_OBJECT_MODEL.md` | Updated and reconciled against the current source. |
| `docs/DICTATION_ARCHITECTURE.md` | Updated and reconciled against the current source. |
| `docs/DICTATION_COPILOT.md` | Updated and reconciled against the current source. |
| `docs/DICTATION_PIPELINE_GUIDE.md` | Updated and reconciled against the current source. |
| `docs/DOMAIN_MODEL.md` | Updated and reconciled against the current source. |
| `docs/ENVIRONMENTS.md` | Updated and reconciled against the current source. |
| `docs/EXECUTION_DESTINATIONS.md` | Updated and reconciled against the current source. |
| `docs/FIREFOX_EXTENSION_GUIDE.md` | Updated and reconciled against the current source. |
| `docs/GATE.md` | Updated and reconciled against the current source. |
| `docs/GETTING_STARTED.md` | Updated and reconciled against the current source. |
| `docs/GLOSSARY.md` | Updated and reconciled against the current source. |
| `docs/INFERENCE_TARGETS.md` | Updated and reconciled against the current source. |
| `docs/INTEGRATIONS.md` | Updated and reconciled against the current source. |
| `docs/INTERVIEW.md` | Updated and reconciled against the current source. |
| `docs/IPAD.md` | Updated and reconciled against the current source. |
| `docs/KERNEL.md` | Updated and reconciled against the current source. |
| `docs/MCP_SIDECAR.md` | Updated and reconciled against the current source. |
| `docs/MEETING_AFTERCARE.md` | Updated and reconciled against the current source. |
| `docs/MEETING_ARCHITECTURE.md` | Updated and reconciled against the current source. |
| `docs/MEETING_INTELLIGENCE.md` | Updated and reconciled against the current source. |
| `docs/MEETING_MODE_GUIDE.md` | Updated and reconciled against the current source. |
| `docs/MODELS.md` | Updated and reconciled against the current source. |
| `docs/MODEL_RUNTIME.md` | Updated and reconciled against the current source. |
| `docs/OPERATIONS.md` | Updated and reconciled against the current source. |
| `docs/PEOPLE_INTEGRATION.md` | Updated and reconciled against the current source. |
| `docs/PEOPLE_SECURITY.md` | Updated and reconciled against the current source. |
| `docs/PLUGIN_AUTHORING.md` | Updated and reconciled against the current source. |
| `docs/PROJECT_ROOMS.md` | Updated and reconciled against the current source. |
| `docs/REACH_RUNNER.md` | Updated and reconciled against the current source. |
| `docs/README.md` | Updated and reconciled against the current source. |
| `docs/RELATIONSHIP_AWARE_MEMORY.md` | Updated and reconciled against the current source. |
| `docs/RELEASING.md` | Updated and reconciled against the current source. |
| `docs/SECURITY.md` | Updated and reconciled against the current source. |
| `docs/SECURITY_MODEL.md` | Updated and reconciled against the current source. |
| `docs/STORAGE_AND_MIGRATIONS.md` | Updated and reconciled against the current source. |
| `docs/SYSTEM_ARCHITECTURE.md` | Updated and reconciled against the current source. |
| `docs/SYSTEM_INTEGRATION_MAP.md` | Updated and reconciled against the current source. |
| `docs/TROUBLESHOOTING.md` | Updated and reconciled against the current source. |
| `docs/USER_GUIDE.md` | Updated and reconciled against the current source. |
| `docs/USE_CASES.md` | Updated and reconciled against the current source. |
| `docs/VOICE_COMMANDS.md` | Updated and reconciled against the current source. |
| `docs/WEB_DESK.md` | Updated and reconciled against the current source. |
| `docs/WEB_UI_UX_SYSTEM_AUDIT.md` | Updated and reconciled against the current source. |
| `docs/WHAT_IS_HOLDSPEAK.md` | Updated and reconciled against the current source. |
| `docs/calls.md` | Updated and reconciled against the current source. |
| `docs/phone.md` | Updated and reconciled against the current source. |
| `docs/programs.md` | Updated and reconciled against the current source. |
| `docs/ACTUATOR_DEVELOPMENT.md` | Specialist protocol/development contract reviewed and retained. |
| `docs/AIPI_LITE_DEV_WORKFLOW.md` | Specialist protocol/development contract reviewed and retained. |
| `docs/API_REFERENCE.md` | Generator-owned reference, checked through its existing generator or roster guard. |
| `docs/API_SURFACE.md` | Generator-owned reference, checked through its existing generator or roster guard. |
| `docs/CAPABILITIES.md` | Generator-owned reference, checked through its existing generator or roster guard. |
| `docs/CONFIGURATION_REFERENCE.md` | Generator-owned reference, checked through its existing generator or roster guard. |
| `docs/CONNECTOR_DEVELOPMENT.md` | Specialist protocol/development contract reviewed and retained. |
| `docs/DEVICE_PROTOCOL.md` | Specialist protocol/development contract reviewed and retained. |
| `docs/PLATFORMS.md` | Generator-owned reference, checked through its existing generator or roster guard. |


## README visual revision, 2026-10-29

The owner requested an alluring, modern, simple README that shows HoldSpeak's potential with screenshots. The revised page starts with the current Desk and a concrete question, then follows thoughts, meetings, coding agents, Programs, projects, Automations, and phone-sized browser work. It has seven screenshots with descriptive alt text and captions. The text is about one third shorter than the preceding draft. Product code is unchanged.

### Screenshot provenance

All captures were already in this repository. No new product capture, live flow, provider request, owner Desk write, or successful real Program execution is claimed. The Program screenshots use fixture check/PR states, disclosed beside the first Program image and in the gallery note.

| README asset | Existing source | Natural dimensions | SHA-256 prefix |
| --- | --- | --- | --- |
| `docs/assets/readme/desk-project-room.jpg` | Existing public hero, regenerated in `a445cc060` | 1440 × 900 | `aa6bf6defcfe` |
| `docs/assets/readme/desk-meeting-review.jpg` | Existing public Today capture, regenerated in `a445cc060` | 1440 × 900 | `4cd44ed40159` |
| `docs/assets/readme/agents.png` | `docs/internal/betterment/native-experience/atlas-2026-10-27/agents-1440.png`, exact copy | 794 × 568 | `9758184517b1` |
| `docs/assets/programs/program-your-turn-1440.png` | Existing public Programs fixture capture | 1440 × 900 | `0d9d47f4dc73` |
| `docs/assets/readme/project.png` | `docs/internal/betterment/native-experience/atlas-2026-10-27/room-1440.png`, exact copy | 848 × 570 | `84a4c4e01c94` |
| `docs/assets/readme/ask-mobile.png` | `docs/internal/betterment/native-experience/atlas-2026-10-27/ask-answer-top-393.png`, exact copy | 393 × 852 | `b8e8266fcb49` |
| `docs/assets/programs/program-running-393.png` | Existing public Programs fixture capture | 393 × 852 | `39f2a3248d52` |

Root inspected every source image. A standalone local Markdown preview was rendered at 1440 and 393 pixels in a new headless browser context. All seven images decoded at each width, there was one H1, and the page had no horizontal overflow. Root inspected the opening and phone gallery at both sizes. This is a README layout check with approximate GitHub styling, not a live product walk or owner aesthetic acceptance. Preview files and machine reports are under `.tmp/readme-preview/`.

The revision's focused documentation check ran under the test lock with an isolated HOME: **88 passed in 4.03s**. The public navigation checker reports **73 files checked**. The earlier broader validation remains recorded above; it is not described as a new run. The extra advisory response and disposition are in `checks/core-docs-claude-p-invoked-by-astra.md`. Status remains UNCHECKED, awaiting Muad'Dib.

The README revision removes its overview diagram. The other 27 public Mermaid diagrams are unchanged from the earlier syntax validation.

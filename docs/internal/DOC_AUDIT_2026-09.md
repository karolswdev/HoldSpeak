# Documentation review: September 2026

Review date: 2026-09-05. Implementation baseline: `075d6833` on `main`.
Change branch: `docs/product-documentation-refresh`.
This is one documentation maintenance change outside the roadmap story workflow.

## Requirement and interpretation

The owner requested an overall documentation refresh PR and named ASD-DTE100.
A search found no authoritative standard under that exact identifier.
The authoritative ASD site identifies ASD-STE100 Simplified Technical English, Issue 9, dated 2025-01-15.
The owner clarification remains pending. This change provisionally uses ASD-STE100.

Sources consulted:

- [Official standard and dictionary](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf).
- [Official overview](https://www.asd-ste100.org/about_STE.html).
- [Download and compliance guidance](https://www.asd-ste100.org/STE_downloads.html).

The private working copy of the standard is not part of the commit.
The repository contains its own writing policy and technical terminology register.
It does not redistribute the standard's dictionary.

## Documentation model

The refresh uses three distinct layers:

1. User guides describe tasks, current controls, expected results, and recovery.
2. Technical references describe contracts, architecture, and programmatic interfaces.
3. Specifications and evidence distinguish target requirements from implemented and verified behavior.

This organization is a HoldSpeak convention. It is not a document-structure mandate from ASD-STE100.
The language policy supplies controlled-English review requirements within those layers.

## Scope

| Area | Treatment |
| --- | --- |
| Root README, docs index, Getting Started | Rewritten around installation, daily tasks, current controls, and version boundaries. |
| Interview | New public guide for all sections, source-backed context, suggestion choices, Try draft, repeat visits, and limits. |
| Architecture work | New manual recipes for decision reviews, meeting preparation, agent briefs, and recurring-review trials. |
| Automation | New map of triggers, clients, runtime dependencies, authority, and supported execution paths. |
| Desk, Places, Models, Cadence, Project Rooms | Rewritten for current behavior. Obsolete UI instructions and screenshots removed from these guides. |
| User Guide | Revised entry map, installation pointer, Threads, Interview distinction, Settings entries, and related links. Detailed existing sections retained. |
| Dictation and Meeting guides | Corrected model setup links and keyed-provider instructions to match the current Concierge and owner API. Other detailed procedures retained. |
| Authority, Security, Architecture | Added current default, Interview state/retention, and conversation/controller boundaries. Existing deep contracts retained. |
| MCP reference | Corrected narrative totals and setup drivers. Removed duplicate numeric heading claims. Generated roster retained. |
| Reach Runner | Replaced machine-specific setup with explicit placeholders and corrected the Heartbeat operation behind its legacy log label. |
| Contributor workflow | Corrected environment setup and generated commit contract. Added documentation review and validation commands. |
| Editorial policy | Replaced malformed style guide, added ASD reference and technical terms, and updated canonical feature names. |
| Navigation maintenance | Added an independent local-link/heading checker, regression tests, and a CI job. |

The public glossary defines product terms. The internal terminology register records their editorial scope.
The index links current user guides and the existing Interview specification package in both directions.

## Source review

| Claim | Implementation or contract inspected |
| --- | --- |
| Installation and Web build | [Package contract](../../pyproject.toml), [build hook](../../hatch_build.py), [Web scripts](../../web/package.json) |
| Current menus and creation | [Verb registry](../../web/src/desk/verbRegistry.ts), [menu bar](../../web/src/desk/components/DeskMenuBar.tsx) |
| Interview sections and limits | [Descriptors](../../holdspeak/services/interview_contracts.py), [service](../../holdspeak/services/interview_service.py), [MCP family](../../holdspeak/mcp/families/interview.py) |
| Try draft and saved context | [Interview panel](../../web/src/desk/components/InterviewPanel.tsx), [Thread window](../../web/src/desk/pullouts/ThreadPullout.tsx) |
| Thread policies and modes | [Tool gate](../../holdspeak/services/thread_tools.py), [mode seeds](../../holdspeak/services/thread_modes.py) |
| Models and current entry points | [Concierge](../../web/src/features/concierge/ConciergeCore.tsx), [controller](../../web/src/features/concierge/useConciergeController.ts), [Settings](../../web/src/pages/cores/SettingsCore.tsx) |
| Current Project creation and Room controls | [Project creation](../../web/src/features/project-room/door/DoorCore.tsx), [source controller](../../web/src/features/project-room/door/useDoorController.ts), [Room](../../web/src/features/project-room/ProjectRoomCore.tsx) |
| Model quality and delivery limits | [Interview delivery record](architect-assistant/DELIVERY_STATUS.md), [verification](architect-assistant/VALIDATION.md) |
| Authority and default | [Control mode configuration](../../holdspeak/config/core.py), [authority guide](../AUTHORITY.md), Thread gate |
| Remote runner | [Runner implementation](../../scripts/reach_runner.py), including `heartbeat.run_now`, arguments, and exit codes |
| Cadence behavior | [Cadence service](../../holdspeak/services/cadence_service.py), [Cadence package](../../holdspeak/cadence/), [Telegram surface](../../holdspeak/cadence_telegram.py) |

No feature delivery, owner acceptance, live microphone readiness, or model-quality improvement is claimed by this documentation change.
The running owner preview and original feature checkout are outside this PR's mutations.

## Preserved technical and historical material

[Environment verification](ENVIRONMENT_VERIFICATION.md) retains the previous public guide's implementation and test record with a provenance note.
Its recorded output remains historical. It is not a new execution claim.
[Meeting output schema](MEETING_OUTPUT_SCHEMA.md) retains the technical schema material moved from the Models user guide.

The existing Interview SRS, contracts, delivery plans, and failed live-model observations remain intact.
This refresh does not mark later Interview releases or autonomous orchestration complete.

## Language review and limits

The rewritten guides use short sentences, direct instructions, explicit conditions, consistent names, and separate task/result explanations.
The glossary and terminology register distinguish labels, technical nouns, verbs, and ordinary prose.
Procedural and descriptive sentence lengths were reviewed during the editorial pass.
Exact code, schema, and UI labels retain their required spelling.

The retained long references and historical corpus have not received a complete dictionary and semantic review.
Automated navigation, count, and vocabulary checks are not an STE conformance assessment.
This PR claims an STE-based documentation policy and a substantial editorial refresh, not certified conformance of the entire repository.
A full conformance claim requires review against the official dictionary, approved meanings, and every applicable writing rule.

## Verification

Baseline documentation contract run:

```text
2 failed, 33 passed in 19.69s
FAILED test_mcp_tool_count_claims_match_registry
FAILED test_no_user_facing_doc_uses_dashes_in_prose
```

The baseline index stated 214 tools while the registry contained 222.
The Places guide contained an internal verification heading, and the Desk guide contained a disallowed prose dash.
The refresh corrects those defects without weakening the existing guards.

Final verification used the isolated Python driver and included the new navigation regression suite:

```sh
python docs/internal/architect-assistant/proof/run_tests.py -q --tb=short tests/unit/test_doc_drift_guard.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_api_surface.py tests/unit/test_docs_navigation.py
```

Observed output:

```text
............................................                             [100%]
44 passed in 6.70s
```

The new CI job also runs the nine navigation regressions through standard-library unittest.
That independent invocation passed locally.
Additional observed checks:

```text
Documentation navigation: 37 files checked; local targets and Markdown headings resolve.
Documentation navigation: 6 files checked; local targets and Markdown headings resolve.
All checks passed!
Documentation CI job: valid YAML and expected standalone check commands.
Markdown parse review: 37 public files parsed with CommonMark and tables.
All public pages have one top-level title.
```

The lint result covers `scripts/check_docs.py` and `tests/unit/test_docs_navigation.py`.
The six-file link run covers the new editorial, review, moved-reference, and Interview-package navigation.
`git diff --check` produced no errors.

A local CommonMark preview rendered Interview, Getting Started, and Automation at widths 1440 and 393.
The final six render checks reported no page overflow.
The initial Automation table overflowed at phone width, so its guide links moved into the path column.
The final Interview desktop preview and Automation phone preview were visually inspected.
This preview uses local review CSS. It does not assert identical layout in every Markdown host.

An approximate sentence scan of the 14 rewritten guides found no over-limit review candidates before the final keyed-provider clarification.
The scan counted procedural and descriptive sentences separately and supported the manual review.
It did not validate approved dictionary meanings or establish STE conformance.
The substantive language-review limits above still apply.

## Maintenance

For future behavior changes, update the owning user procedure and technical contract in the same PR.
Run the navigation and existing drift checks from [Contributing](../../CONTRIBUTING.md).
Use the [writing standard](DOCS_STYLE.md) and [terminology register](DOCS_TERMINOLOGY.md) for the language review.
Record any remaining uncertainty instead of changing a target requirement into a present-tense capability claim.

## See also

- [Documentation index](../README.md): current task map.
- [Writing standard](DOCS_STYLE.md): language and maintenance requirements.
- [August audit](DOC_AUDIT_2026-08.md): previous historical review.

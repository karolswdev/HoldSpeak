# HoldSpeak documentation

HoldSpeak is an agentic-first, web-based AI operating system backed by a local hub.
Use these guides to take work from context to a result you can inspect.
Start with [What is HoldSpeak?](WHAT_IS_HOLDSPEAK.md) or the [root README](../README.md).

## Choose a complete flow

| You want to | Start here | Continue with |
| --- | --- | --- |
| Turn an idea into useful work | [Notes and thought development](USER_GUIDE.md#develop-a-thought) | [Architecture work](ARCHITECTURE_WORK.md) |
| Take a meeting through follow-up | [Meeting mode](MEETING_MODE_GUIDE.md) | [Intelligence](MEETING_INTELLIGENCE.md), [Aftercare](MEETING_AFTERCARE.md) |
| Ask about records and use tools | [The Desk](WEB_DESK.md#ask-about-your-work) | [Agents and Threads](AGENTS_AND_THREADS.md) |
| Hand a task to a coding agent | [Coder integration](CODER_INTEGRATION.md) | [Agent hooks](AGENT_HOOK_INSTALL.md), [Gate](GATE.md) |
| Work with several live terminals | [Terminals](TERMINALS.md) | [Coder integration](CODER_INTEGRATION.md) |
| Run a multi-step implementation goal | [Programs](programs.md) | [Coder integration](CODER_INTEGRATION.md) |
| Work by phone or receive a work call | [Calls and The Line](calls.md) | [Phone](phone.md) |
| Make a useful job repeat | [Automation](AUTOMATION.md) | [Project Watches](PROJECT_ROOMS.md), [Cadence](CADENCE.md) |
| Lead a Project or prepare for a 1:1 | [Project Rooms](PROJECT_ROOMS.md) | [People](PEOPLE_INTEGRATION.md), [Memory](RELATIONSHIP_AWARE_MEMORY.md) |
| Put spoken words in another app | [Voice typing](USER_GUIDE.md#voice-typing) | [Dictation pipeline](DICTATION_PIPELINE_GUIDE.md) |
| Repair a failed run | [Troubleshooting](TROUBLESHOOTING.md) | [Operations](OPERATIONS.md), [Models](MODELS.md) |

The [Use cases](USE_CASES.md) guide connects starts, actions, results, and completion checks.
A model answer, queued job, proposal, agent launch, and completed effect have different meanings.
The owning guide explains how to inspect the result.

## Use

| Task | Guide |
| --- | --- |
| Install and try the Desk | [Getting Started](GETTING_STARTED.md) |
| Find a daily control or task | [User Guide](USER_GUIDE.md) |
| Open tools, arrange windows, and file records | [The Desk](WEB_DESK.md) |
| Understand a product term | [Glossary](GLOSSARY.md) |
| Develop goals, Projects, and working context | [Interview](INTERVIEW.md) |
| Prepare a decision or implementation brief | [Architecture work](ARCHITECTURE_WORK.md) |
| Review current work and retained attention | [Desk Memory](DESK_MEMORY.md) |
| Find earlier records and source evidence | [Memory](RELATIONSHIP_AWARE_MEMORY.md) |
| Prepare with confidential People context | [People integration](PEOPLE_INTEGRATION.md), [People security](PEOPLE_SECURITY.md) |
| Choose wallpaper and presentation preferences | [Environments](ENVIRONMENTS.md) |
| Correct, enrich, and replay dictation | [Dictation Copilot](DICTATION_COPILOT.md), [Dictation pipeline](DICTATION_PIPELINE_GUIDE.md) |
| Use spoken commands | [Voice commands](VOICE_COMMANDS.md) |
| Attach recent activity to dictation | [Activity prebriefing](ACTIVITY_PREBRIEFING.md) |

## Configure

| Task | Guide |
| --- | --- |
| Select engines and assign jobs | [Models](MODELS.md), [Inference targets](INFERENCE_TARGETS.md) |
| Configure recurring work and result placement | [Automation](AUTOMATION.md) |
| Configure Project sources and Steward behavior | [Project Rooms](PROJECT_ROOMS.md) |
| Choose operation authority | [Control modes](AUTHORITY.md) |
| Set up installed coding-agent hooks | [Agent hooks](AGENT_HOOK_INSTALL.md) |
| Understand held agent tool calls | [Gate](GATE.md) |
| Connect an MCP client, 318 tools across 52 families | [MCP sidecar](MCP_SIDECAR.md) |
| Run a remote Project sweep | [Reach Runner](REACH_RUNNER.md) |
| Configure sources and outgoing destinations | [Integrations](INTEGRATIONS.md) |
| Understand execution placement | [Execution destinations](EXECUTION_DESTINATIONS.md) |
| Look up a configuration field | [Configuration reference](CONFIGURATION_REFERENCE.md) |

The full MCP catalogue is larger than any individual caller's allowed palette.
A tool's presence does not grant permission to execute it.

## Extend

| Task | Guide |
| --- | --- |
| Add a typed meeting output | [Plugin authoring](PLUGIN_AUTHORING.md) |
| Read activity from another tool | [Connector development](CONNECTOR_DEVELOPMENT.md) |
| Add a supported external effect | [Actuator development](ACTUATOR_DEVELOPMENT.md) |
| Find HTTP operations | [API surface](API_SURFACE.md), [API reference](API_REFERENCE.md) |
| Find implementation and evidence metadata | [Capabilities](CAPABILITIES.md) |
| Change the web surface | [Design author map](../web/README.md#design-author-map), [Desk architecture](DESK_ARCHITECTURE.md) |
| Compose shared controls and document patterns | [Surface contract](../web/src/desk/surface/contract.md), [UI contract](WEB_UI_UX_SYSTEM_AUDIT.md) |
| Set up and submit a development change | [Contributing](../CONTRIBUTING.md) |

## Operate

| Task | Guide |
| --- | --- |
| Diagnose, back up, and restore | [Operations](OPERATIONS.md) |
| Recover a failed job or named refusal | [Troubleshooting](TROUBLESHOOTING.md) |
| Upgrade or prepare a release | [Releasing](RELEASING.md) |
| Understand schema reconciliation and storage | [Storage and migrations](STORAGE_AND_MIGRATIONS.md) |
| Understand data boundaries | [Security and privacy](SECURITY.md), [Security model](SECURITY_MODEL.md) |
| Check platform-specific metadata | [Platform matrix](PLATFORMS.md) |

## Architecture

| Question | Reference |
| --- | --- |
| How do the parts fit? | [System architecture](SYSTEM_ARCHITECTURE.md) |
| How does a work flow execute? | [Architecture](ARCHITECTURE.md) |
| Which process and boundary owns it? | [System integration map](SYSTEM_INTEGRATION_MAP.md) |
| Which record owns the content or result? | [Domain model](DOMAIN_MODEL.md), [Data model](DATA_MODEL.md) |
| How do model choices become attempts? | [Model runtime](MODEL_RUNTIME.md) |
| How are operations admitted and recovered? | [Kernel](KERNEL.md), [Authority model](AUTHORITY_MODEL.md) |
| How do windows and objects work? | [Desk architecture](DESK_ARCHITECTURE.md), [Desk object model](DESK_OBJECT_MODEL.md) |
| How does speech become typed text? | [Dictation architecture](DICTATION_ARCHITECTURE.md) |
| How does meeting intelligence persist? | [Meeting architecture](MEETING_ARCHITECTURE.md), [Intelligence](MEETING_INTELLIGENCE.md) |
| How do other clients reach the hub? | [Companion architecture](COMPANIONS_ARCHITECTURE.md) |

## Calls, Phone, and optional clients

[Calls](calls.md) documents phone conversations and The Line adapter.
[Phone](phone.md) documents attention rules, configured number calls, and the incomplete iPhone-app transport.

<a id="optional-clients-and-devices"></a>

The browser Desk is the main product surface.
These integrations have their own installation, transport, and availability limits.

| Integration | Guide |
| --- | --- |
| Swift iPad client | [iPad](IPAD.md) |
| ESP32-S3 audio device | [AIPI-Lite](AIPI_LITE.md), [development workflow](AIPI_LITE_DEV_WORKFLOW.md) |
| Compatible audio bridge | [Device protocol](DEVICE_PROTOCOL.md) |
| Firefox activity extension | [Firefox extension](FIREFOX_EXTENSION_GUIDE.md) |

## Internal records

[Internal documentation](internal/) holds canon, source audits, plans, and historical verification.
A plan describes intended work. A release record establishes only its named revision and observed scope.
Neither is a substitute for the current public procedure or implementation source.

The [native-experience package](internal/betterment/native-experience/README.md) records the React-stack direction and delivery research.
The [modernization record](internal/betterment/MODERNIZATION-IMPLEMENTATION-2026-10-22.md) records its implementation scope and verification.
The [documentation writing standard](internal/DOCS_STYLE.md) defines language and source-review requirements.

Generated inventories keep their recorded snapshot and evidence labels.
The API surface lists reference-app routes, including compatibility handlers that can return a named refusal.
Consumer tags are static source matches and can include parked clients.
The capability and platform tables cover a pinned metadata baseline, not every current feature.
Read each task guide for its active controls and required setup.
Source review, passing fixture tests, and a working physical deployment are different evidence.

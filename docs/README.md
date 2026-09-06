# HoldSpeak documentation

Use these guides to install HoldSpeak, prepare work, and configure its tools.
The guides describe `main`. Check your installed version when a control is absent.

## Start here

| You want to | Read |
| --- | --- |
| Install HoldSpeak and capture a sentence | [Getting Started](GETTING_STARTED.md) |
| Find a daily task or product control | [User Guide](USER_GUIDE.md) |
| Use Desk objects and windows | [The Desk](WEB_DESK.md) |
| Select an environment or use Settle in | [Places](ENVIRONMENTS.md) |
| Understand product terms | [Glossary](GLOSSARY.md) |

## Prepare your work

| You want to | Read |
| --- | --- |
| Describe goals, Projects, cadences, and decisions | [Interview](INTERVIEW.md) |
| Prepare an architecture decision or agent brief | [Architecture work recipes](ARCHITECTURE_WORK.md) |
| Continue a conversation with tools and sources | [Threads](USER_GUIDE.md#threads) |
| Refine a Note through questions | [Develop a thought](USER_GUIDE.md#develop-a-thought) |
| Connect project sources and configure Watches | [Project Rooms](PROJECT_ROOMS.md) |
| Use confidential relationship records | [People integration](PEOPLE_INTEGRATION.md) and [People security](PEOPLE_SECURITY.md) |

## Dictate and meet

| You want to | Read |
| --- | --- |
| Dictate into another app | [Voice typing](USER_GUIDE.md#voice-typing) |
| Configure project facts and optional model rewriting | [Dictation pipeline](DICTATION_PIPELINE_GUIDE.md) |
| Follow a coding prompt example | [Dictation Copilot](DICTATION_COPILOT.md) |
| Map spoken keywords to configured actions | [Voice commands](VOICE_COMMANDS.md) |
| Review recent activity before dictation | [Activity pre-briefing](ACTIVITY_PREBRIEFING.md) |
| Record, import, or review a meeting | [Meeting mode](MEETING_MODE_GUIDE.md) |
| Review attention items and Receipts | [Desk memory](DESK_MEMORY.md) |
| Find earlier work across your records | [Relationship-aware memory](RELATIONSHIP_AWARE_MEMORY.md) |

## Configure models and automation

| You want to | Read |
| --- | --- |
| Select engines and assign capabilities | [Models](MODELS.md) |
| Choose a manual, event, or scheduled execution path | [Automation](AUTOMATION.md) |
| Review unresolved work and prepare next actions | [Cadence](CADENCE.md) |
| Understand permissions before an effect | [Control modes](AUTHORITY.md) |
| Connect Claude Code or Codex sessions | [Agent hooks](AGENT_HOOK_INSTALL.md) |
| Run a remote sweep and Project Steward | [Reach Runner](REACH_RUNNER.md) |

## Build and integrate

The MCP sidecar exposes 222 tools across 40 families.
Its generated roster is the reference for tool names and membership.
Discovery and execution also depend on the caller's permissions.

| You want to | Read |
| --- | --- |
| Use the MCP service contract | [MCP sidecar](MCP_SIDECAR.md) |
| Find an HTTP route and its consumers | [API surface](API_SURFACE.md) |
| Understand the runtime and data flow | [Architecture](ARCHITECTURE.md) |
| Write a meeting plugin | [Plugin authoring](PLUGIN_AUTHORING.md) |
| Write an activity connector | [Connector development](CONNECTOR_DEVELOPMENT.md) |
| Install the browser activity connector | [Firefox extension](FIREFOX_EXTENSION_GUIDE.md) |
| Develop a portable device | [AIPI-Lite workflow](AIPI_LITE_DEV_WORKFLOW.md) and [Device protocol](DEVICE_PROTOCOL.md) |

## Operate and recover

- [Security & Privacy](SECURITY.md): storage, network boundaries, and secret handling.
- [Release and recovery](RELEASING.md): backups, restore, packaging, and release checks.
- [Inference placement](INFERENCE_TARGETS.md): current terminology and model routing references.

## Documentation and specifications

User guides describe implemented behavior. Internal specifications can also describe planned behavior.
Read each specification's status and verification record before you treat it as an available capability.

- [Interview specification package](internal/architect-assistant/README.md): requirements, contracts, recipes, delivery status, and verification limits.
- [Project Rooms specification package](internal/project-rooms/README.md): product, Web, domain, and MCP contracts.
- [Contributing](../CONTRIBUTING.md): documentation changes and required checks.
- [Writing standard](internal/DOCS_STYLE.md): ASD-STE100 reference, page structure, and review requirements.
- [Documentation review](internal/DOC_AUDIT_2026-09.md): this refresh's scope, source checks, and remaining language review.

Historical plans and design records remain under [internal](internal/).
Historical evidence does not establish the current product state.

## See also

- [Product overview](../README.md): capabilities and platform support.
- [Getting Started](GETTING_STARTED.md): the first successful task.
- [Glossary](GLOSSARY.md): product terms and their meanings.

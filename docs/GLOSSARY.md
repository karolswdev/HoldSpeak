# Glossary

Use these meanings when you read HoldSpeak guides.
Capitalized product names identify specific records, modes, or controls.
The names match the live Desk on 2026-10-27. A former name keeps its row and points to the current one.

| Term | Meaning |
| --- | --- |
| agent | A saved persona with instructions and selected context. It is distinct from a live Coder session. |
| Artifact | A saved output record with information about its source or creator. |
| Archive | The place for records that you put away. Open it with Go > Archive or Search. You can restore a record from it. |
| arrival | The former name of the Desk home screen. Use Today. |
| Ask | The one window for questions about your work (Go > Ask AI, or ⌘I). About sets what it reads. Saved conversations are under Recent. |
| assignment | A model selection for a capability, group, or eligible saved item. |
| automation | Work started by a configured trigger and executed through a supported path. A suggestion alone is not an automation. |
| Automations | The product surface for watch/reaction configuration outside Project-scoped Watches. |
| Cadence | The system that reviews unresolved work and prepares next actions. Its background loop is off by default. |
| cadence | A desired repetition frequency. An Interview cadence preference does not configure the Cadence system. |
| capability | A registered kind of work with model and execution requirements. |
| Chair | The former name of the Desk home view. Use Today and Needs you. |
| Coder session | A live coding session that HoldSpeak can observe or steer through supported controls. |
| Accounts | The Settings section for connections to services. |
| Concierge | The former name of model setup. Use HoldSpeak > Engines. |
| Runs on | The former name of Engines. Use HoldSpeak > Engines. |
| connector | A component that obtains context from a configured source. Its permissions and data boundary depend on that source. |
| Control mode | The Secure, Normal, or YOLO policy preset for future operations. Set it in Settings > Agents > Agents act. |
| correction | A stored dictation rule. A text correction rewrites a heard phrase in the transcript. A routing correction nudges the block or the delivery target of a similar utterance. |
| decision record | A durable record of a decision and its available rationale. It does not establish organizational acceptance by itself. |
| Desk | The product's operating surface for records and tools. |
| dock | The floating bar at the bottom of the Desk. It opens Today, Meetings, People, Agents and Speak, holds iconified windows, and has the record button. |
| dictation journal | One row per dictation run on this device, with the transcript, the delivered text, the route, the latency, and the corrections that fired. |
| dictation pipeline | The stages that route or transform dictated text before delivery. |
| egress | Transfer of data outside the current machine or applicable execution boundary. |
| engine | A model runtime, endpoint, or model option shown in Engines. |
| Engines | The window where you select the engine for each job (HoldSpeak > Engines). |
| Everyday context | The editable starter prompts that you can explicitly attach as AI context. |
| Floor | The former name of a separate spatial Desk view. The Desk itself now shows records as icons. |
| grant | Bounded authority for an operation, destination, and scope, with expiry and use limits. |
| grounding | Use of selected source records as context for a model result. A source reference does not prove the result is correct. |
| Heartbeat | The unattended sweep, configured in Settings > Notices. It is distinct from Cadence. |
| hub | The HoldSpeak runtime and data host that the Web app or a paired device uses. |
| inference | A model execution that produces a result from input. |
| Interview | The Thread mode for repeatable context and suggestions. It runs through the hub API and MCP. The Thought Workbench also has a separate Interview pane. |
| Learned | The Speak wing that lists stored corrections and their applied counts. |
| MCP | Model Context Protocol. Clients use it to discover and call exposed tools and read resources. |
| Model Library | The service that records model availability, deployment information, and readiness. |
| Needs you | The ranked list of what waits on you across every Project (Go > Needs you, or ⌃J). Today shows its first rows. |
| Note | An editable text record. Its window shows the Markdown in place, including Mermaid diagrams. |
| People | The protected surface for confidential relationship records and permitted shared intent. |
| Places | The former name of the wallpaper picker. Use Settings > Desk > Wallpaper. |
| Project | A record that groups an outcome and related sources or work. |
| Project facts | Exact values from the `kb:` map in `.holdspeak/project.yaml`, inserted into applicable dictation templates. |
| Project context | The separate `.hs/` files that can guide an optional model rewrite. |
| Project Room | The working surface for one Project, its sources, changes, decisions, and automation controls. |
| proposal | A candidate action or decision that has its own review, authority, and execution states. |
| Reach | The remote MCP transport with scoped credentials. |
| Receipt | An execution record that identifies an operation, its boundary, and its result. |
| Resourceful | The product's bounded overnight maintenance capability. |
| Rhythm | The former Settings module for the Heartbeat. Use Settings > Notices. |
| Settle in | A temporary Desk view with reduced navigation controls. |
| sidecar | The local MCP process that accesses HoldSpeak services without hosting the Web runtime. |
| Speak | The voice-typing window. |
| Steward | The Project component that evaluates observed work and produces supported results under its configured policy. |
| suggestion | An Interview idea with a basis, feasibility, and recorded user choice. It is distinct from an executed action. |
| sweep | One Heartbeat evaluation pass. |
| Thought | The former interface name for a Note being worked on. The interface uses Note. |
| Today | The Desk home window: what needs you, the day ahead, and the next 1:1. It is the first icon in the dock (⌃1). |
| Wallpaper | The background selected in Settings > Desk. |
| Thread | A saved conversation with model turns, references, and applicable tools. Ask opens it from Recent. |
| tool | A named callable operation. Its existence does not grant execution authority. |
| Watch | A Project-scoped configuration that observes a source population and evaluates specified conditions. |
| Zone | A Desk container for filed objects. |

## See also

- [Documentation index](README.md): guides organized by task.
- [Automation](AUTOMATION.md): triggers, workers, and authority.
- [Models](MODELS.md): engines, availability, and assignments.
- [Control modes](AUTHORITY.md): review, authorization, and execution.

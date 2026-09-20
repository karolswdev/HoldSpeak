# API reference

This reference supplements [API surface](API_SURFACE.md). The existing real-app
generator owns the route roster; this census adds static handler evidence.
It does not invent request/response schemas for raw `Request` handlers.

Source snapshot: `675401a857b85336d4acaa8c65383dfc9636e4c8`. **693 method/route entries**.

**Verification boundary:** inspect the [full endpoint ledger](generated/api-reference.json)
and the [declared OpenAPI schemas](generated/openapi.json) for transport models.
The ledger records parameters, body-key reads, declared responses, literal errors,
service calls, source line, client tags and candidate tests. Candidate tests are
text matches, not assertion evidence. Helper validators, middleware, dynamically
composed paths and semantic authority/idempotency still require source review.

## Read an endpoint

1. Find its method and route in the ledger or existing API surface.
2. Open the defining source and handler evidence. Follow raw-body validators.
3. Follow service calls into authority, dispatch, persistence and receipt.
4. Match the operation to the capability registry and inspect test assertions.
5. Run the scoped tests with isolated HOME; record the actual result.

The hub transport, owner/principal checks, proposal decisions and kernel
execution authority are distinct. A POST can be a preview; a GET is not by
itself proof of safe information disclosure. See [Authority](AUTHORITY_MODEL.md)
and [Security](SECURITY_MODEL.md). The browser uses `web/src/lib/api.ts` and
the shared RuntimeBus. Companion client tags come from the existing generator.

## Route groups

| Defining module | Entries |
| --- | ---: |
| `device_audio_ws` | 1 |
| `fastapi.applications` | 4 |
| `web.routes.activity.candidates` | 6 |
| `web.routes.activity.enrichment` | 14 |
| `web.routes.activity.ledger` | 7 |
| `web.routes.activity.nudges` | 4 |
| `web.routes.activity.plugin_jobs` | 5 |
| `web.routes.activity.rules` | 6 |
| `web.routes.authority` | 7 |
| `web.routes.automations` | 22 |
| `web.routes.cadence` | 13 |
| `web.routes.calendar_events` | 3 |
| `web.routes.calendar_snapshot` | 2 |
| `web.routes.calendar_sources` | 1 |
| `web.routes.concierge` | 5 |
| `web.routes.connections` | 2 |
| `web.routes.constitutional` | 3 |
| `web.routes.core` | 2 |
| `web.routes.decision_records` | 9 |
| `web.routes.decisions` | 8 |
| `web.routes.delivery` | 4 |
| `web.routes.delivery_attempts` | 2 |
| `web.routes.delivery_dossiers` | 3 |
| `web.routes.delivery_factory` | 3 |
| `web.routes.delivery_node` | 5 |
| `web.routes.delivery_prs` | 9 |
| `web.routes.delivery_terminal` | 5 |
| `web.routes.desk_actuators` | 7 |
| `web.routes.desk_seed` | 2 |
| `web.routes.dictation.agent` | 5 |
| `web.routes.dictation.blocks` | 6 |
| `web.routes.dictation.floor` | 3 |
| `web.routes.dictation.intents` | 4 |
| `web.routes.dictation.kb` | 4 |
| `web.routes.dictation.pipeline` | 14 |
| `web.routes.dictation.project_docs` | 5 |
| `web.routes.door` | 1 |
| `web.routes.follow_through` | 3 |
| `web.routes.front_door` | 4 |
| `web.routes.inference_assignments` | 5 |
| `web.routes.mcp_http` | 5 |
| `web.routes.meeting_import` | 1 |
| `web.routes.meetings.action_items` | 7 |
| `web.routes.meetings.aftercare` | 6 |
| `web.routes.meetings.crud` | 9 |
| `web.routes.meetings.insights` | 3 |
| `web.routes.meetings.intel` | 8 |
| `web.routes.meetings.live` | 5 |
| `web.routes.meetings.speakers` | 3 |
| `web.routes.memory` | 2 |
| `web.routes.mesh` | 5 |
| `web.routes.missioncontrol` | 10 |
| `web.routes.model_library` | 7 |
| `web.routes.monday_brief` | 4 |
| `web.routes.pages` | 19 |
| `web.routes.people` | 26 |
| `web.routes.primitives.ask` | 5 |
| `web.routes.primitives.chains` | 7 |
| `web.routes.primitives.decisions` | 7 |
| `web.routes.primitives.directories` | 8 |
| `web.routes.primitives.invocations` | 3 |
| `web.routes.primitives.kbs` | 8 |
| `web.routes.primitives.model_profiles` | 8 |
| `web.routes.primitives.notes` | 5 |
| `web.routes.primitives.profiles` | 11 |
| `web.routes.primitives.recipes` | 9 |
| `web.routes.primitives.thoughts` | 20 |
| `web.routes.primitives.workbenches` | 22 |
| `web.routes.primitives.workflows` | 7 |
| `web.routes.project_briefs` | 8 |
| `web.routes.project_door` | 2 |
| `web.routes.project_reviews` | 5 |
| `web.routes.project_setup` | 12 |
| `web.routes.project_updates` | 6 |
| `web.routes.projections` | 2 |
| `web.routes.projects` | 35 |
| `web.routes.proposals` | 7 |
| `web.routes.providers` | 16 |
| `web.routes.repositories` | 10 |
| `web.routes.roadmaps` | 4 |
| `web.routes.scheduled_recordings` | 6 |
| `web.routes.setup` | 14 |
| `web.routes.steward` | 10 |
| `web.routes.sync` | 2 |
| `web.routes.system.agent_capabilities` | 1 |
| `web.routes.system.coder_factory_routes` | 2 |
| `web.routes.system.coder_steering_routes` | 16 |
| `web.routes.system.coders` | 6 |
| `web.routes.system.gate_routes` | 12 |
| `web.routes.system.health` | 3 |
| `web.routes.system.kernel_routes` | 7 |
| `web.routes.system.settings` | 6 |
| `web.routes.system.settings_secrets` | 3 |
| `web.routes.system.voice` | 7 |
| `web.routes.system.voice_stream` | 1 |
| `web.routes.system.ws` | 1 |
| `web.routes.threads` | 18 |
| `web.routes.tts` | 3 |
| `web.routes.watches` | 10 |

## Regenerate and check

Run the existing `scripts/gen_api_surface.py` when routes or client calls change,
then `python scripts/philo_api_reference.py`. Use `--check` to detect ledger drift.
The existing `tests/unit/test_api_surface.py` compares membership with the real
assembled application. This supplementary ledger must not replace that check.

No OpenAPI field is treated as a complete contract when the handler parses its
own request. The unresolved semantic fields are visible in every endpoint row
and count as coverage gaps, rather than receiving a default “approved” value.

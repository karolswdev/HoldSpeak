# API reference

This reference supplements [API surface](API_SURFACE.md). The existing real-app
generator owns the route roster; this census adds static handler evidence.
It does not invent request/response schemas for raw `Request` handlers.

Census baseline snapshot: `675401a857b85336d4acaa8c65383dfc9636e4c8`. Handler evidence and test candidates are read from the current working tree at generation. **827 method/route entries**.

**Verification boundary:** inspect the full endpoint ledger, `docs/generated/api-reference.json` (not in git; run `scripts/gen_docs.sh` to write it),
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
| `web.routes.activity.candidates` | 4 |
| `web.routes.activity.enrichment` | 4 |
| `web.routes.activity.ledger` | 5 |
| `web.routes.activity.nudges` | 3 |
| `web.routes.activity.plugin_jobs` | 4 |
| `web.routes.activity.rules` | 5 |
| `web.routes.agent_hand` | 17 |
| `web.routes.authority` | 7 |
| `web.routes.automations` | 8 |
| `web.routes.briefing` | 14 |
| `web.routes.cadence` | 10 |
| `web.routes.calendar_events` | 3 |
| `web.routes.calendar_snapshot` | 2 |
| `web.routes.calendar_sources` | 1 |
| `web.routes.calls` | 20 |
| `web.routes.channels` | 11 |
| `web.routes.concierge` | 8 |
| `web.routes.connections` | 4 |
| `web.routes.constitutional` | 3 |
| `web.routes.core` | 2 |
| `web.routes.decision_records` | 10 |
| `web.routes.decisions` | 8 |
| `web.routes.delivery` | 3 |
| `web.routes.delivery_attempts` | 2 |
| `web.routes.delivery_dossiers` | 3 |
| `web.routes.delivery_factory` | 3 |
| `web.routes.delivery_node` | 4 |
| `web.routes.delivery_prs` | 8 |
| `web.routes.delivery_terminal` | 6 |
| `web.routes.desk_actuators` | 7 |
| `web.routes.desk_parked` | 1 |
| `web.routes.desk_seed` | 2 |
| `web.routes.desk_windows` | 5 |
| `web.routes.dictation.agent` | 2 |
| `web.routes.dictation.blocks` | 6 |
| `web.routes.dictation.floor` | 2 |
| `web.routes.dictation.intents` | 4 |
| `web.routes.dictation.kb` | 4 |
| `web.routes.dictation.pipeline` | 14 |
| `web.routes.dictation.project_docs` | 2 |
| `web.routes.door` | 2 |
| `web.routes.follow_through` | 2 |
| `web.routes.inference_assignments` | 7 |
| `web.routes.mcp_http` | 9 |
| `web.routes.meeting_import` | 2 |
| `web.routes.meetings.action_items` | 3 |
| `web.routes.meetings.aftercare` | 6 |
| `web.routes.meetings.crud` | 12 |
| `web.routes.meetings.insights` | 3 |
| `web.routes.meetings.intel` | 9 |
| `web.routes.meetings.live` | 5 |
| `web.routes.meetings.speakers` | 1 |
| `web.routes.memory` | 6 |
| `web.routes.mesh` | 5 |
| `web.routes.missioncontrol` | 10 |
| `web.routes.model_library` | 2 |
| `web.routes.monday_brief` | 5 |
| `web.routes.onboarding` | 13 |
| `web.routes.pages` | 22 |
| `web.routes.people` | 30 |
| `web.routes.phone` | 19 |
| `web.routes.primitives.ask` | 7 |
| `web.routes.primitives.chains` | 5 |
| `web.routes.primitives.decisions` | 6 |
| `web.routes.primitives.directories` | 8 |
| `web.routes.primitives.invocations` | 2 |
| `web.routes.primitives.kbs` | 8 |
| `web.routes.primitives.model_profiles` | 8 |
| `web.routes.primitives.note_outcomes` | 5 |
| `web.routes.primitives.notes` | 5 |
| `web.routes.primitives.profiles` | 5 |
| `web.routes.primitives.recipes` | 9 |
| `web.routes.primitives.thoughts` | 21 |
| `web.routes.primitives.workbenches` | 32 |
| `web.routes.primitives.workflows` | 5 |
| `web.routes.programs` | 37 |
| `web.routes.project_briefs` | 8 |
| `web.routes.project_door` | 3 |
| `web.routes.project_reviews` | 5 |
| `web.routes.project_setup` | 1 |
| `web.routes.project_updates` | 13 |
| `web.routes.projections` | 2 |
| `web.routes.projects` | 33 |
| `web.routes.proposals` | 9 |
| `web.routes.providers` | 14 |
| `web.routes.recordings` | 13 |
| `web.routes.repositories` | 11 |
| `web.routes.roadmaps` | 4 |
| `web.routes.scheduled_recordings` | 6 |
| `web.routes.setup` | 15 |
| `web.routes.steward` | 10 |
| `web.routes.sync` | 3 |
| `web.routes.system.agent_capabilities` | 1 |
| `web.routes.system.coder_factory_routes` | 2 |
| `web.routes.system.coder_relay_routes` | 5 |
| `web.routes.system.coder_steering_routes` | 11 |
| `web.routes.system.coders` | 7 |
| `web.routes.system.gate_routes` | 13 |
| `web.routes.system.health` | 3 |
| `web.routes.system.kernel_routes` | 7 |
| `web.routes.system.settings` | 6 |
| `web.routes.system.settings_secrets` | 3 |
| `web.routes.system.ui_feedback` | 3 |
| `web.routes.system.voice` | 7 |
| `web.routes.system.voice_stream` | 1 |
| `web.routes.system.ws` | 1 |
| `web.routes.threads` | 17 |
| `web.routes.today` | 1 |
| `web.routes.tts` | 3 |
| `web.routes.walks` | 5 |
| `web.routes.watches` | 9 |

## Regenerate and check

Run the existing `scripts/gen_api_surface.py` when routes or client calls change,
then `python scripts/philo_api_reference.py`. The JSON ledger is not in git; `scripts/gen_docs.sh` writes it.
The existing `tests/unit/test_api_surface.py` compares membership with the real
assembled application. This supplementary ledger must not replace that check.

No OpenAPI field is treated as a complete contract when the handler parses its
own request. The unresolved semantic fields are visible in every endpoint row
and count as coverage gaps, rather than receiving a default “approved” value.

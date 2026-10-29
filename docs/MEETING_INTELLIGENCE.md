# Meeting intelligence

Meeting intelligence reads a saved transcript, chooses the assigned inference
route, and writes a summary job result. It is model work, not capture. A model
route can be local, remote, a supported CLI inference engine, or a mesh node.

## How it runs

`MeetingIntelService` creates a durable job for
`POST /api/meetings/{meeting_id}/intelligence/run`. The job freezes the selected
route and records attempts, status, and the terminal result. The queue can be
processed by the hub or by `holdspeak intel --process`.

The route is selected from current model assignments. The legacy
`meeting.intel_provider` value does not force local execution. The UI exposes
the planned host before a run and the receipt records the host that handled it.

If the route is not ready, the job can remain queued or enter recovery. Retry
and skip are explicit recovery actions. A failed plugin does not erase a valid
summary from another plugin.

## Presets and intents

Routing profiles are presets: `balanced`, `architect`, `delivery`, `product`,
and `incident`. The intent router can select architecture, delivery, product,
incident, or communications plugins. A profile changes selection rules. It does
not change authority or the model destination.

Use the preview route or a CLI dry run to inspect selection without changing the
meeting:

```console
holdspeak intel --route-dry-run MEETING_ID --profile architect
```

## Built-in plugins

The plugin registry includes decision, requirement, action-owner, risk,
dependency, milestone, architecture, and communication extractors. The exact
set is source-owned by `holdspeak/plugins/meeting` and the plugin registry.
Each plugin needs an assignment. A missing assignment produces a recorded skip,
not an invented local result.

## Run states

The queue distinguishes planned, running, completed, failed, skipped, and
recoverable work. Read `GET /api/intel/jobs`,
`GET /api/intel/summary`, and the meeting's `intel-recovery` route when a card
does not complete.

## Actuators

Intelligence proposes records. It does not silently confirm a decision, close an
action, file an issue, or send a channel message. Review routes act on proposed
meeting outcomes. Later external effects use the central operation policy.

## Where results appear

The summary, topics, proposals, and artifacts are saved with the meeting. The
intent timeline and plugin run history are available from:

- `GET /api/meetings/{meeting_id}/intent-timeline`
- `GET /api/meetings/{meeting_id}/plugin-runs`
- `GET /api/meetings/{meeting_id}/artifacts`
- `GET /api/meetings/{meeting_id}/prepared`

The source transcript remains the evidence. A model output can be wrong, so
inspect its source segment before you keep a proposal or send a draft.

## See also

- [Meeting Mode guide](MEETING_MODE_GUIDE.md#after-the-meeting)
- [Meeting architecture](MEETING_ARCHITECTURE.md)
- [Aftercare](MEETING_AFTERCARE.md)
- [Models](MODELS.md)
- [Security](SECURITY.md)

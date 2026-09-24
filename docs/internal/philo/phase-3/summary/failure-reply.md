# PHILO-3-02 failure reply

The retained provider failure reply is
`tests/fixtures/philo3_summary_failure_reply.json`. It is a recorded
provider-boundary substitution. It does not seed a meeting, job, receipt, or
failure row in the database.

## Shape read by the rig

`scripts/graph_walk.py:1019-1035` reads the JSON object into `_ReplayIntel` and
constructs the product `IntelResult` with these fields:

| Field | Value in the fixture | Reader use |
| --- | --- | --- |
| `provider` | `recorded-provider` | Recorded as the active provider identity. |
| `model` | `philo3-summary-failure` | Recorded as the active model identity. |
| `topics` | `[]` | The result has no topics. |
| `action_items` | `[]` | The result has no action items. |
| `summary` | `""` | The result has no summary. |
| `error` | A non-empty recorded failure string | Becomes `IntelResult.error`. |

`holdspeak/meeting_session/deferred_bound.py:42-76` reads a returned result's
`error` and raises the content-free `provider_error_result` failure. The queue,
persistence, receipts, and face remain the product's path. The error text in
this fixture is therefore a trigger for that path, not a planted durable
database value.

## Atlas boundary contract for the later rig worker

The boundary step must use the exact field `reply`:

```json
{
  "kind": "boundary",
  "label": "recorded provider failure at the provider boundary",
  "substitute": "engine_reply",
  "reply": "tests/fixtures/philo3_summary_failure_reply.json",
  "adapter": "labelled-substitution"
}
```

The path is relative to the repository root. `case_engine_replay` reads
`step.get("reply")` (`scripts/graph_walk.py:2409-2414`), and the run starts the
hub with that repository path (`scripts/graph_walk.py:3055-3065`). The boundary
then hashes the same `reply` path and compares it with the installed reply
(`scripts/graph_walk.py:2267-2287`). The older `reply_path` spelling is not read
by this consumer.

The hub installs the object inside its own process at
`holdspeak.intel.providers._configured_engine` and
`holdspeak.intel.engine.MeetingIntel` (`scripts/graph_walk.py:1068-1086`). The
later worker must therefore keep `reply` on every failure boundary and must not
label a boundary without starting the hub with this reply.

## Read-only validation

Command:

```text
HOME=$(mktemp -d) uv run python -m json.tool tests/fixtures/philo3_summary_failure_reply.json >/dev/null
```

Output:

```text
(no output; exit code 0)
```

No atlas case was run. This artifact does not prove queue settlement, face
rendering, restart retrieval, or the real LAN provider.

Astra also read the actual consumer and ran this file through the rig's real
`_ReplayIntel.analyze` and the product's real `BoundMeetingAdapter.dispatch`.
The adapter raised `BoundMeetingProviderFailure` with reason
`provider_error_result`, as required. Source/WAV hashes and audio format were
verified in the same isolated-HOME probe. [Retained output](fixture-verification.txt).
No hub, database, network or model call was made by that probe.

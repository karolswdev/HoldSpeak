# Evidence - HS-133-11

- **Story:** HS-133-11 - The walk
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-16T17:00:05Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run python scripts/mcp_walk.py --json-out pm/roadmap/holdspeak/phase-133-the-honest-sidecar/assets/mcp-walk-transcript.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2c987ca4d639acb85ca85a1149a825096d870e96

```text
MCP walk: isolated HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs-mcp-walk-k3e2hn1b

--- initialize ---
  [PASS] protocolVersion  -- 2024-11-05
  [PASS] serverInfo.name  -- holdspeak-mcp

--- tools/list ---
  [PASS] tool_count_82  -- got 82
  [PASS] all_schemas_closed

--- resources/list ---
  [PASS] static_resources_14  -- got 14
  [PASS] resource_templates_10  -- got 10
  [PASS] total_resources_24  -- got 24
  [PASS] cadence_status_resource_listed  -- ['holdspeak://desk/schema', 'holdspeak://desk/verbs', 'holdspeak://desk/constitution', 'holdspeak://desk/inference-targets', 'holdspeak://desk/snapshot', 'holdspeak://workbenches', 'holdspeak://recipes', 'holdspeak://profiles', 'holdspeak://dictation/journal', 'holdspeak://follow-through/board', 'holdspeak://briefs/latest', 'pipeline://events/recent', 'pipeline://events/stats', 'holdspeak://cadence/status']

--- desk family ---
  [PASS] desk.list_ok  -- []

--- ask family ---
  [PASS] ask.models_ok  -- [{"id": "this_machine", "name": "Qwen3.5-9B-Instruct-Q6_K", "profile_id": null, "source": "hub"}]

--- settings family ---
  [PASS] settings.get_ok
  [PASS] settings._revision_present  -- keys: ['_placement', '_revision', '_secrets', 'cadence', 'cadence_telegram', 'config_version', 'control_mode', 'device', 'dictation', 'hotkey']
  [PASS] settings.no_secret_leak  -- secret check passed

--- settings.update round-trip ---
  [PASS] settings.update_ok
  [PASS] settings.update_roundtrip  -- got 0.42

--- coder family ---
  [PASS] coder.list_ok  -- []

--- memory family ---
  [PASS] memory.search_ok  -- {"hits": [], "page": {"count": 0, "limit": 50, "offset": 0, "total": 0}, "ranking": {"interleave": "kind_rank_tiers_then

--- cadence family ---
  [PASS] cadence.status_ok  -- {"counts": {}, "egress": {"label": "Local only", "scope": "local"}, "enabled": false, "max_nudges_per_day": 12, "policie

--- cadence/status resource ---
  [PASS] cadence_status_resource_read  -- {'jsonrpc': '2.0', 'id': 12, 'result': {'contents': [{'uri': 'holdspeak://cadence/status', 'mimeType': 'application/json
  [PASS] cadence.snooze_error_unknown_loop  -- isError=True

--- sequence family ---
  [PASS] sequence.cancel_error_unknown_parent  -- isError=True

--- plugin_job family ---
  [PASS] plugin_job.summary_ok  -- {"failed_jobs": 0, "next_retry_at": null, "queued_due_jobs": 0, "queued_jobs": 0, "running_jobs": 0, "scheduled_retry_jo
  [PASS] plugin_job.retry_error_unknown_job  -- isError=True

--- ping ---
  [PASS] ping_ok

Transcript written to pm/roadmap/holdspeak/phase-133-the-honest-sidecar/assets/mcp-walk-transcript.json

============================================================
MCP walk: 24 assertions, 24 passed, 0 failed
============================================================
```

### Captured run — 2026-08-16T17:01:05Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.LSnZa3ht37 uv run python scripts/mcp_walk.py --live-43 --endpoint http://192.168.1.43:8080 --json-out pm/roadmap/holdspeak/phase-133-the-honest-sidecar/assets/mcp-walk-transcript-live43.json`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2c987ca4d639acb85ca85a1149a825096d870e96

```text
MCP walk: isolated HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs-mcp-walk-gjfvhqmg

--- initialize ---
  [PASS] protocolVersion  -- 2024-11-05
  [PASS] serverInfo.name  -- holdspeak-mcp

--- tools/list ---
  [PASS] tool_count_82  -- got 82
  [PASS] all_schemas_closed

--- resources/list ---
  [PASS] static_resources_14  -- got 14
  [PASS] resource_templates_10  -- got 10
  [PASS] total_resources_24  -- got 24
  [PASS] cadence_status_resource_listed  -- ['holdspeak://desk/schema', 'holdspeak://desk/verbs', 'holdspeak://desk/constitution', 'holdspeak://desk/inference-targets', 'holdspeak://desk/snapshot', 'holdspeak://workbenches', 'holdspeak://recipes', 'holdspeak://profiles', 'holdspeak://dictation/journal', 'holdspeak://follow-through/board', 'holdspeak://briefs/latest', 'pipeline://events/recent', 'pipeline://events/stats', 'holdspeak://cadence/status']

--- desk family ---
  [PASS] desk.list_ok  -- []

--- ask family ---
  [PASS] ask.models_ok  -- [{"id": "this_machine", "name": "Qwen3.5-9B-Instruct-Q6_K", "profile_id": null, "source": "hub"}]

--- settings family ---
  [PASS] settings.get_ok
  [PASS] settings._revision_present  -- keys: ['_placement', '_revision', '_secrets', 'cadence', 'cadence_telegram', 'config_version', 'control_mode', 'device', 'dictation', 'hotkey']
  [PASS] settings.no_secret_leak  -- secret check passed

--- settings.update round-trip ---
  [PASS] settings.update_ok
  [PASS] settings.update_roundtrip  -- got 0.42

--- coder family ---
  [PASS] coder.list_ok  -- []

--- memory family ---
  [PASS] memory.search_ok  -- {"hits": [], "page": {"count": 0, "limit": 50, "offset": 0, "total": 0}, "ranking": {"interleave": "kind_rank_tiers_then

--- cadence family ---
  [PASS] cadence.status_ok  -- {"counts": {}, "egress": {"label": "Local only", "scope": "local"}, "enabled": false, "max_nudges_per_day": 12, "policie

--- cadence/status resource ---
  [PASS] cadence_status_resource_read  -- {'jsonrpc': '2.0', 'id': 12, 'result': {'contents': [{'uri': 'holdspeak://cadence/status', 'mimeType': 'application/json
  [PASS] cadence.snooze_error_unknown_loop  -- isError=True

--- sequence family ---
  [PASS] sequence.cancel_error_unknown_parent  -- isError=True

--- plugin_job family ---
  [PASS] plugin_job.summary_ok  -- {"failed_jobs": 0, "next_retry_at": null, "queued_due_jobs": 0, "queued_jobs": 0, "running_jobs": 0, "scheduled_retry_jo
  [PASS] plugin_job.retry_error_unknown_job  -- isError=True

--- live .43 leg (endpoint=http://192.168.1.43:8080) ---
  .43 loaded model: Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf
  control ask.models: [{"id": "this_machine", "name": "Qwen3.5-9B-Instruct-Q6_K", "profile_id": null, "source": "hub"}]
  [PASS] live43_profile_create  -- id=target_8dc364105d62
  [FAIL] live43_ask.run  -- {'jsonrpc': '2.0', 'id': 19, 'result': {'content': [{'type': 'text', 'text': '{"error": "Destination \'walk-43-live\' names no on-device model file"}'}], 'isError': True}}

--- ping ---
  [PASS] ping_ok

Transcript written to pm/roadmap/holdspeak/phase-133-the-honest-sidecar/assets/mcp-walk-transcript-live43.json

============================================================
MCP walk: 26 assertions, 25 passed, 1 failed
============================================================

Failed assertions:
  25. live43_ask.run  -- {'jsonrpc': '2.0', 'id': 19, 'result': {'content': [{'type': 'text', 'text': '{"error": "Destination \'walk-43-live\' names no on-device model file"}'}], 'isError': True}}
```

### Captured run — 2026-08-16T17:01:53Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ugCaESChdf uv run python scripts/mcp_walk.py --live-43 --endpoint http://192.168.1.43:8080 --json-out pm/roadmap/holdspeak/phase-133-the-honest-sidecar/assets/mcp-walk-transcript-live43.json`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2c987ca4d639acb85ca85a1149a825096d870e96

```text
MCP walk: isolated HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs-mcp-walk-ottd49av

--- initialize ---
  [PASS] protocolVersion  -- 2024-11-05
  [PASS] serverInfo.name  -- holdspeak-mcp

--- tools/list ---
  [PASS] tool_count_82  -- got 82
  [PASS] all_schemas_closed

--- resources/list ---
  [PASS] static_resources_14  -- got 14
  [PASS] resource_templates_10  -- got 10
  [PASS] total_resources_24  -- got 24
  [PASS] cadence_status_resource_listed  -- ['holdspeak://desk/schema', 'holdspeak://desk/verbs', 'holdspeak://desk/constitution', 'holdspeak://desk/inference-targets', 'holdspeak://desk/snapshot', 'holdspeak://workbenches', 'holdspeak://recipes', 'holdspeak://profiles', 'holdspeak://dictation/journal', 'holdspeak://follow-through/board', 'holdspeak://briefs/latest', 'pipeline://events/recent', 'pipeline://events/stats', 'holdspeak://cadence/status']

--- desk family ---
  [PASS] desk.list_ok  -- []

--- ask family ---
  [PASS] ask.models_ok  -- [{"id": "this_machine", "name": "Qwen3.5-9B-Instruct-Q6_K", "profile_id": null, "source": "hub"}]

--- settings family ---
  [PASS] settings.get_ok
  [PASS] settings._revision_present  -- keys: ['_placement', '_revision', '_secrets', 'cadence', 'cadence_telegram', 'config_version', 'control_mode', 'device', 'dictation', 'hotkey']
  [PASS] settings.no_secret_leak  -- secret check passed

--- settings.update round-trip ---
  [PASS] settings.update_ok
  [PASS] settings.update_roundtrip  -- got 0.42

--- coder family ---
  [PASS] coder.list_ok  -- []

--- memory family ---
  [PASS] memory.search_ok  -- {"hits": [], "page": {"count": 0, "limit": 50, "offset": 0, "total": 0}, "ranking": {"interleave": "kind_rank_tiers_then

--- cadence family ---
  [PASS] cadence.status_ok  -- {"counts": {}, "egress": {"label": "Local only", "scope": "local"}, "enabled": false, "max_nudges_per_day": 12, "policie

--- cadence/status resource ---
  [PASS] cadence_status_resource_read  -- {'jsonrpc': '2.0', 'id': 12, 'result': {'contents': [{'uri': 'holdspeak://cadence/status', 'mimeType': 'application/json
  [PASS] cadence.snooze_error_unknown_loop  -- isError=True

--- sequence family ---
  [PASS] sequence.cancel_error_unknown_parent  -- isError=True

--- plugin_job family ---
  [PASS] plugin_job.summary_ok  -- {"failed_jobs": 0, "next_retry_at": null, "queued_due_jobs": 0, "queued_jobs": 0, "running_jobs": 0, "scheduled_retry_jo
  [PASS] plugin_job.retry_error_unknown_job  -- isError=True

--- live .43 leg (endpoint=http://192.168.1.43:8080) ---
  .43 loaded model: Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf
  control ask.models: [{"id": "this_machine", "name": "Qwen3.5-9B-Instruct-Q6_K", "profile_id": null, "source": "hub"}]
  [PASS] live43_profile_create  -- id=target_3bba3c7c805b
  [FAIL] live43_ask.run  -- {'jsonrpc': '2.0', 'id': 19, 'result': {'content': [{'type': 'text', 'text': '{"error": "Destination \'walk-43-live\' refused the run: openai package is not available"}'}], 'isError': True}}

--- ping ---
  [PASS] ping_ok

Transcript written to pm/roadmap/holdspeak/phase-133-the-honest-sidecar/assets/mcp-walk-transcript-live43.json

============================================================
MCP walk: 26 assertions, 25 passed, 1 failed
============================================================

Failed assertions:
  25. live43_ask.run  -- {'jsonrpc': '2.0', 'id': 19, 'result': {'content': [{'type': 'text', 'text': '{"error": "Destination \'walk-43-live\' refused the run: openai package is not available"}'}], 'isError': True}}
```

### Captured run — 2026-08-16T17:02:30Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.yQQ1XBaxlR uv run python scripts/mcp_walk.py --live-43 --endpoint http://192.168.1.43:8080 --json-out pm/roadmap/holdspeak/phase-133-the-honest-sidecar/assets/mcp-walk-transcript-live43.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2c987ca4d639acb85ca85a1149a825096d870e96

```text
MCP walk: isolated HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs-mcp-walk-r6uucw7u

--- initialize ---
  [PASS] protocolVersion  -- 2024-11-05
  [PASS] serverInfo.name  -- holdspeak-mcp

--- tools/list ---
  [PASS] tool_count_82  -- got 82
  [PASS] all_schemas_closed

--- resources/list ---
  [PASS] static_resources_14  -- got 14
  [PASS] resource_templates_10  -- got 10
  [PASS] total_resources_24  -- got 24
  [PASS] cadence_status_resource_listed  -- ['holdspeak://desk/schema', 'holdspeak://desk/verbs', 'holdspeak://desk/constitution', 'holdspeak://desk/inference-targets', 'holdspeak://desk/snapshot', 'holdspeak://workbenches', 'holdspeak://recipes', 'holdspeak://profiles', 'holdspeak://dictation/journal', 'holdspeak://follow-through/board', 'holdspeak://briefs/latest', 'pipeline://events/recent', 'pipeline://events/stats', 'holdspeak://cadence/status']

--- desk family ---
  [PASS] desk.list_ok  -- []

--- ask family ---
  [PASS] ask.models_ok  -- [{"id": "this_machine", "name": "Qwen3.5-9B-Instruct-Q6_K", "profile_id": null, "source": "hub"}]

--- settings family ---
  [PASS] settings.get_ok
  [PASS] settings._revision_present  -- keys: ['_placement', '_revision', '_secrets', 'cadence', 'cadence_telegram', 'config_version', 'control_mode', 'device', 'dictation', 'hotkey']
  [PASS] settings.no_secret_leak  -- secret check passed

--- settings.update round-trip ---
  [PASS] settings.update_ok
  [PASS] settings.update_roundtrip  -- got 0.42

--- coder family ---
  [PASS] coder.list_ok  -- []

--- memory family ---
  [PASS] memory.search_ok  -- {"hits": [], "page": {"count": 0, "limit": 50, "offset": 0, "total": 0}, "ranking": {"interleave": "kind_rank_tiers_then

--- cadence family ---
  [PASS] cadence.status_ok  -- {"counts": {}, "egress": {"label": "Local only", "scope": "local"}, "enabled": false, "max_nudges_per_day": 12, "policie

--- cadence/status resource ---
  [PASS] cadence_status_resource_read  -- {'jsonrpc': '2.0', 'id': 12, 'result': {'contents': [{'uri': 'holdspeak://cadence/status', 'mimeType': 'application/json
  [PASS] cadence.snooze_error_unknown_loop  -- isError=True

--- sequence family ---
  [PASS] sequence.cancel_error_unknown_parent  -- isError=True

--- plugin_job family ---
  [PASS] plugin_job.summary_ok  -- {"failed_jobs": 0, "next_retry_at": null, "queued_due_jobs": 0, "queued_jobs": 0, "running_jobs": 0, "scheduled_retry_jo
  [PASS] plugin_job.retry_error_unknown_job  -- isError=True

--- live .43 leg (endpoint=http://192.168.1.43:8080) ---
  .43 loaded model: Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf
  control ask.models: [{"id": "this_machine", "name": "Qwen3.5-9B-Instruct-Q6_K", "profile_id": null, "source": "hub"}]
  [PASS] live43_profile_create  -- id=target_1b66e14619b6
  [PASS] live43_receipt_model_matches  -- receipt=Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf, endpoint=Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf
  treatment ask.models: [{"id": "this_machine", "name": "Qwen3.5-9B-Instruct-Q6_K", "profile_id": null, "source": "hub"}, {"id": "target_1b66e14619b6", "name": "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf", "profile_id": "target_1b66e14
  control-vs-treatment: control=[{"id": "this_machine", "name": "Qwen3.5-9B-Instruct-Q6_K", "profile_id": null, "source": "hub"}], treatment=[{"id": "this_machine", "name": "Qwen3.5-9B-Instruct-Q6_K", "profile_id": null, "source": "hub"}, {"
  receipt model: Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf
  endpoint model: Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf
  match: True

--- ping ---
  [PASS] ping_ok

Transcript written to pm/roadmap/holdspeak/phase-133-the-honest-sidecar/assets/mcp-walk-transcript-live43.json

============================================================
MCP walk: 26 assertions, 26 passed, 0 failed
============================================================
```

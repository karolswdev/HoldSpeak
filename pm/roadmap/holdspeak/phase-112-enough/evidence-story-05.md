# Evidence - HS-112-05

- **Story:** HS-112-05 - The sitting walk
- **Status:** done
- **Date:** 2026-08-02

## Proof

### Captured run — 2026-08-02T18:27:39Z

- **Command:** `bash -c ls pm/roadmap/holdspeak/phase-112-enough/assets/hs-112-05/ | wc -l; echo '--- named refusal + idempotent replay (fresh hub 8123):'; curl -s -X POST http://127.0.0.1:8123/api/dictation/remote -H 'Authorization: Bearer ukIOPIbTDA3bQ593XsEtKEC2RQODax4X' -H 'content-type: application/json' -d '{"text":"evidence leg","target_mode":"agent","require_agent":true,"raw":true,"delivery_id":"walk-evidence-1"}'; echo; curl -s -X POST http://127.0.0.1:8123/api/dictation/remote -H 'Authorization: Bearer ukIOPIbTDA3bQ593XsEtKEC2RQODax4X' -H 'content-type: application/json' -d '{"text":"evidence leg","target_mode":"agent","require_agent":true,"raw":true,"delivery_id":"walk-evidence-1"}'; echo; echo '--- seeded desk after reset:'; curl -s http://127.0.0.1:8123/api/directories -H 'Authorization: Bearer ukIOPIbTDA3bQ593XsEtKEC2RQODax4X' | python3 -c 'import json,sys; d=json.load(sys.stdin)["directories"]; print(len(d),"drawers:",sorted(x["name"] for x in d))'`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** dd82a1862fa505ec9ce77552f567408f9ba8565a

```text
      21
--- named refusal + idempotent replay (fresh hub 8123):
{"error":"no_awaiting_agent","refusal":"no_awaiting_agent","failure_category":"delivery_refused","delivered":false,"final_text":"","delivery_id":"walk-evidence-1","deduplicated":false}
{"deduplicated":true,"delivered":false,"delivery_id":"walk-evidence-1","error":"no_awaiting_agent","failure_category":"delivery_refused","final_text":"","refusal":"no_awaiting_agent"}
--- seeded desk after reset:
6 drawers: ['ADRs', 'Decisions', 'Inbox', 'Meetings', 'Reference', 'Rules']
```

# Phase 6 exit 3 — the Phase 5 rehearsal driver, three attempts

`scripts/philo5_his_words.py run --engine real` on merged main `f93e76fa`, a fresh Codex session per attempt through `scripts/astra`, one isolated hub per attempt (the DB path in each `hub-proof.json` is under `…/T/philo5-04-hub-*/`, never the owner's desk). LAN engine `http://192.168.1.43:8080` answered (`engine-preflight-curl.txt`).

| Attempt | Outcome | Step | Cause |
|---|---|---|---|
| `20260925T060112Z-his-words-real` | BLOCKED, 241.8 s | decision_thought (turn 3 of 4) | tool selection: Codex chose `door.add_item` (a follow-through task), not `desk.create`; `codex/decision_thought/last.md` |
| `20260925T060532Z-his-words-real` | BLOCKED, 202.6 s | decision_thought | the same tool selection: `door.add_item` |
| `20260925T060854Z-his-words-real` | BLOCKED, 227.8 s | decision_thought | Codex chose `desk.create` correctly (`decision_0c3fc998963d`); the driver then failed `MCP exchange reconciliation for 'list_mcp_resource_templates' found no unused matching /api/mcp row` |

Both causes are the INHERITED driver defects: tool selection = BACKLOG "PHILO-5-04 follow-ups", MCP discoverability row; reconciliation = BACKLOG "PHILO-6 follow-ups" row 2. No attempt reached the brief turn, so no rehearsal brief shot exists. Each attempt retains the transcript, the effective Codex config, the hub log, the DB-path proof, the DB snapshot, and the Desk shots of the steps it reached: `shots/summary/{1440,393}-before.png` (after the import) and `-after.png` (after the summary).

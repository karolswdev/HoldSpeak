# The Phase 5 rehearsal on the branch — three BLOCKED runs (not evidence of the brief)

`scripts/philo5_his_words.py run` (real LAN engine, Codex through MCP), run
three times on `feat/philo-6-a-badge-brief`. None reached the brief stage:

| Run | Stage reached | Block |
|---|---|---|
| `20260925T025811Z-his-words-real` | import, summary | `Codex turn decision_thought did not produce through MCP: ['desk.create']` |
| `20260925T030357Z-his-words-real` | import | `MCP exchange reconciliation for 'list_mcp_resource_templates' found no unused matching /api/mcp row` |
| `20260925T030841Z-his-words-real` | import, summary | `Codex turn decision_thought did not produce through MCP: ['desk.create']` |

The blocks are in the Codex turn (it chose `desk.create` for the decision) and
the driver's MCP reconciliation, before the brief. This story changed no
decision, desk or MCP code. Whether `origin/main` blocks the same way today
was not run (unknown). Retained, not deleted.

# Parked walk scripts

A prior walk script moves here only when every caller and every assertion
maps to a verified replacement in `scripts/graph_walk.py` (an atlas case with
a sealed `pass` observation) or to an explicit council disposition
(PHILO-2-07; `docs/internal/philo/briefs/graph-audit-brief.md` §9). A parked
script is kept, never deleted. Each parked script gets one mapping note below.

## Parked

None. On 2026-09-22 (PHILO-2-07, main `112561bd`) no walk script met the rule:

- The atlas (`docs/internal/philo/graph/atlas.json`, 73 cases) covers the
  eleven first-use jobs J1–J11. The prior walks prove other phases' surfaces.
- The council (`docs/internal/philo/graph/COUNCIL.md`) gave no disposition
  for any walk script.

## Not parked, and why

| Script | Callers in the tree | Why it stays |
|---|---|---|
| `automations_walk.py` | none | Workbench Automations/Resourceful shots (PR #461); no atlas case. Imports `chair_walk.py`. |
| `chair_walk.py` | `automations_walk.py`, `people_walk.py`, `people_walk_full.py`, `schedule_walk_hs136.py` import its harness | Phase 135 Chair shots at 1440/960; the atlas has no 960 case and no console-error predicate. Four live callers. |
| `desk_gl_walk.py` | none in code | GL world parity, drag, lasso, frame timing (HS-95-01); no atlas case. |
| `desk_walk/` | `walk_ownership_shots.py` | Phase 122–124 keyboard, MCP and observer walks; no atlas case. |
| `door_walk_hs144.py` | none in code | Dashboard Door cold/populated walk (HS-144-06); no atlas case. |
| `hs109_01_live_proof.py` … `hs109_04_live_proof.py` | `phase109_closeout_beats.py` (02–04) | Real-archive decision and memory proofs; no atlas case. They read the owner's real archive: do not run them under the current laws. |
| `hs109_05_walk.py` | none | Project Memory window on a copy of the real archive; no atlas case. Same law warning. |
| `hs109_06_process_window_walk.py` | none | Processes window with real kernel operations; no atlas case. |
| `hs111_11_terminal_walk.py` | none | xterm pane against a real tmux session; no atlas case. |
| `mcp_walk.py` | none in code (`tests/integration/test_hs165_mcp_walk.py` has its own `_mcp_walk_server`) | MCP sidecar JSON-RPC walk over every tool family; the rig has no MCP adapter and the atlas no MCP case. |
| `people_walk.py`, `people_walk_full.py` | `people_walk_full.py` imports `people_walk.py` | People ledger and Keychain proofs; no atlas case. |
| `phase93_keyboard_walk_evidence.py` | none | Phase 93 keyboard-only arrival; no atlas case. |
| `rails_walk_hs88.py`, `steer_walk_hs87.py` | `rails_walk_hs88.py` imports `steer_walk_hs87.py` | Rails and steering against real tmux and the `.43` model; no atlas case. |
| `schedule_walk_hs136.py` | none | Scheduled Recording surface; no atlas case. |
| `screenshot_hs86_walk.py` | none | The Phase 86 belt walk; no atlas case. |
| `settings_walk_139.py` | none | Settings Reckoning shots; no atlas case. |
| `surface_census_walk.py`, `surface_interaction_walk.py` | `surface_interaction_walk.py` and `surface_census_measure.js` use the census | Phase 202 inventory of every face; wider than the atlas. |
| `uat_site_walk.py` | none in code | The UAT site harness self-test; not a product walk. |
| `walk_hs83_live.py`, `walk_hs84_live.py`, `walk_hs85_live.py`, `walk_hsm25_live.py` | none | They drive a hub on `127.0.0.1:8765`, the owner's live hub. Do not run them under the current laws. No atlas case. |
| `walk_one_admission_path.py`, `walk_one_truth.py` | none | Phase 130–131 deployment and admission contracts with the LAN engine; no atlas case. |
| `walk_ownership_shots.py` | none | Phase 134 ownership shots; no atlas case. |
| `walk_working_desk.py`, `walk_working_desk_legs.py` | `chair_walk.py`, `settings_walk_139.py`, `surface_census_walk.py`, `surface_interaction_walk.py`, `walk_working_desk_legs.py` | The shared Phase 132 hub harness; five live callers. |
| `walk-129.mjs`, `walk-prep-114.sh` | none | Phase 129 geometry walk; no atlas case. `walk-prep-114.sh` deletes `$HOME/.local/share/holdspeak/holdspeak.db` and the config: run it only under an isolated HOME. |

To park one later: add the atlas cases that carry its assertions, run them
through `scripts/graph_walk.py` until each has a `pass` observation, move its
callers, then move the script here and replace its row above with the
mapping (script → case ids → observation run ids).

# Evidence - HS-89-03

- **Story:** HS-89-03 - Cross-machine steering — over the relay
- **Status:** done
- **Date:** 2026-07-08

## Proof

### Captured run — 2026-07-08T23:04:03Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9244985d-2dd6-4abf-a33c-7a099253c728/scratchpad/relay_live.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8740d310ae147fd03b5bb8860d02e8608058cbf5

```text
# node process pid=95273 up at http://127.0.0.1:8791; hub pid=95235 (different)
1) relay arm -> armed on node=beta pane=%0
2) relay keys C-c -> delivered (node beta)
3) relay steer -> delivered; 'REMOTE_STEER_OK' in the node's pane? True
4) node killed; relay -> node_offline (node beta) in 0.00s
5) unknown node -> unknown_node

HS-89-03 CROSS-MACHINE (two-process): PASS
```

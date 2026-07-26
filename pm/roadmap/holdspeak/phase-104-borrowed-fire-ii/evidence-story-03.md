# Evidence - HS-104-03

- **Story:** HS-104-03 - The gate under attack — restart, replay, TOCTOU
- **Status:** done
- **Date:** 2026-07-26

## The checklist, item by item

`tests/integration/test_gate_threat_model.py` (items 1/2/3/6/7/8 —
1, 2, 3, and 6 against a REAL spawned `holdspeak web` process,
SIGKILLed mid-hold and restarted, never a mock) plus the HS-104-02
unit pins for items 4 and 5:

1. **Restart mid-hold** — hub SIGKILLed with a proposal held; the
   polling hook denied; on restart the proposal read `invalidated`
   (audit row written), was absent from the held list, and a decide
   attempt got 409.
2. **Replay of a decided proposal** — re-POST of an approved key over
   real HTTP served the terminal state, minted nothing; audit: one
   `approved`, one `re_arrival`, one `proposed`.
3. **TOCTOU** — same key + different args hash: 409 `args_mismatch`,
   the original `invalidated` (refuse AND revoke), its `args_head`
   still the original payload the human would have seen, decide 409.
4. **Expiry race** — `test_expiry_race_exactly_one_terminal_state`
   (injectable clock, decision at expiry ± ε: exactly one winner,
   loser refused by the state machine).
5. **Double decision** —
   `test_double_decision_refused_with_standing_state` +
   `test_route_double_decision_409_names_standing` (first write wins,
   409 names the standing decision).
6. **Fail-closed integrity** — real-process kill mid-poll: deny.
   Unit pins: hub unreachable → deny; HTTP 500 → deny; poll timeout
   → deny. The hook has no allow-on-error path.
7. **Unarmed inertness** — no proposal row, no audit row, no hub
   contact, pinned latency budget (0.25s, in-process fast path).
8. **Redaction** — grep census: hub-side gate modules never name
   `tool_input`; the hook's wire body carries `args_sha256` +
   bounded `args_head` only.

## Mutation checks (the load-bearing three)

Each guard commented out made its test FAIL, then was restored
(outputs read; full run green after):

- **Item 1** — startup invalidation replaced with `pass`:
  `AssertionError: assert 'held' == 'invalidated'` (exit 1).
- **Item 3** — the args-mismatch branch forced to `if False`:
  `assert 200 == 409` (exit 1).
- **Item 6** — the mid-poll death deny replaced with
  `HookDecision(deny=None)`: `assert None is not None` (exit 1).

Restored tree: 6/6 threat tests + 29 gate unit + 4 census green.

## Proof

### Captured run — 2026-07-26T18:32:37Z

- **Command:** `uv run pytest -q tests/integration/test_gate_threat_model.py tests/unit/test_coder_gate.py tests/unit/test_gate_chokepoint.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fdb593347b85f39b6d3e1d274a0836df8bcaa479

```text
.......................................                                  [100%]
39 passed in 9.72s
```

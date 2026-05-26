# Evidence — HS-22-02 Gesture Contract For Agent And Meeting Actions

Date: 2026-05-24

## Scope Completed

- Added bridge-side pure gesture contract in `aipi-lite/bridge/companion_gestures.py`.
- Added focused tests in `aipi-lite/tests/test_companion_gestures.py`.
- Documented the gesture table in `gesture-contract.md`.
- Re-exported gesture contract types from `bridge.__init__` for follow-up bridge wiring.

## Contract Highlights

- Right hold-to-talk is the explicit agent-reply gesture while `agent_waiting`
  is fresh. It reuses the existing `start`/`stop` voice path.
- Left single tap preserves meeting bookmark priority whenever a meeting is
  active, including while an agent is waiting.
- Outside a meeting, left single tap shows the full agent question while an
  agent is waiting; otherwise it preserves the existing `last_segment` query.
- Stale agent context cannot be answered by voice; left single tap clears it.
- Left long press remains firmware-owned AP/provisioning behavior in every state.

## Validation

```text
scripts/aipi_test.sh -q tests/test_companion_gestures.py tests/test_companion_state.py tests/test_bookmark_gesture.py tests/test_remote_press.py
64 passed in 5.91s

cd aipi-lite && .venv/bin/ruff check bridge/companion_gestures.py tests/test_companion_gestures.py bridge/__init__.py
All checks passed!
```

Full-suite validation is recorded with the current working set after HS-22-03
or phase checkpoint commit.

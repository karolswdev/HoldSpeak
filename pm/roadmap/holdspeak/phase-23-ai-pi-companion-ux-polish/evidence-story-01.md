# Evidence — HS-23-01 Long Prompt Display

**Date:** 2026-05-26.
**Story:** [story-01-long-prompt-display.md](./story-01-long-prompt-display.md).
**Status:** done.

## What Changed

- Replaced bridge-side ambiguous question truncation with deterministic question
  windows.
- Agent waiting text now renders as a stable identity line plus a question
  line:

  ```text
  Codex | HoldSpeak | work:2.1 waiting
  [1/2] Should I update the bridge companion display so long Codex questions rotate
  more >
  ```

- Long questions advance across windows on successive companion polls instead
  of ending in unexplained `...`.
- Short questions still render as a single stable waiting state.
- Stale questions still flash stale-clear state instead of inviting an unsafe
  answer.

## Test Evidence

Focused bridge companion tests:

```text
$ aipi-lite/.venv/bin/python -m pytest aipi-lite/tests/test_companion_state.py aipi-lite/tests/test_companion_status.py -q
.....................                                                    [100%]
21 passed in 0.19s
```

Full AIPI regression:

```text
$ scripts/aipi_test.sh -q
................................................. [ 36%]
........................................................................ [ 72%]
......................................................                   [100%]
198 passed in 7.57s
```

HoldSpeak companion/runtime focused regression:

```text
$ .venv/bin/python -m pytest tests/unit/test_agent_context.py tests/unit/test_web_runtime.py tests/integration/test_web_server.py::TestCompanionStatusEndpoint -q
.......................................                                  [100%]
39 passed in 0.68s
```

Diff hygiene:

```text
$ git diff --check
<no output; passed>
```

## Product Notes

This closes the first Phase 23 product problem: AI PI no longer depends on an
opaque trailing ellipsis for long agent questions. The device still remains a
small attention surface, but it now has a deterministic long-text contract that
Phase 23 can build on for multi-session browsing.

Live-device observation was not used as the completion gate for this story. The
behavior is bridge-side and covered by deterministic tests; HS-23-05 remains
the planned multi-agent live dogfood story.


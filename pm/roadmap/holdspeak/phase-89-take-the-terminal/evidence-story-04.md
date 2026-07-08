# Evidence - HS-89-04

- **Story:** HS-89-04 - The robustness walk, the docs, the close
- **Status:** done
- **Date:** 2026-07-08

## Proof

### Captured run — 2026-07-08T23:12:31Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9244985d-2dd6-4abf-a33c-7a099253c728/scratchpad/walk.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f7473a684d2902648937c698c877bdfb486529c9

```text
=== HS-89-04 ROBUSTNESS WALK ===
  PASS  1 interrupt
  PASS  2 edit
  PASS  3 attach hand-started
  PASS  4 recycled->refuse+revoke
  PASS  5 remote steer + quiet-node refuse
  PASS  6 audit read-back

  audit heads (newest first):
    ✕ pane_gone     —     C-c
    ✓ delivered     %1    echo HAND_ATTACHED
    ✓ delivered     %0    "echo AB" BSpace "C" Enter
    ✓ delivered     %0    echo SHELL_ALIVE
    ✓ delivered     %0    C-c

WALK: PASS
```

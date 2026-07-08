# Evidence - HS-89-01

- **Story:** HS-89-01 - Full key control — the send-keys verb
- **Status:** done
- **Date:** 2026-07-08

## Proof

### Captured run — 2026-07-08T16:35:22Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9244985d-2dd6-4abf-a33c-7a099253c728/scratchpad/keys_live.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f2cf09bd131c8bd87939d492358feb906c170497

```text
# armed the real pane %0

BEAT 1 interrupt: runaway climbing 7 -> 12 (alive)
Traceback (most recent call last):
  File "/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9244985d-2dd6-4abf-a33c-7a099253c728/scratchpad/keys_live.py", line 31, in <module>
    keys(pane, [{"literal":"echo SHELL_ALIVE"}, "Enter"]); time.sleep(0.4)
    ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9244985d-2dd6-4abf-a33c-7a099253c728/scratchpad/keys_live.py", line 12, in keys
    assert r["status"]=="delivered", r
           ^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'status': 'pane_gone', 'detail': 'no server running on /private/tmp/tmux-501/default', 'revoked': True, 'audit_id': 3}
```

### Captured run — 2026-07-08T16:35:52Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9244985d-2dd6-4abf-a33c-7a099253c728/scratchpad/keys_live.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f2cf09bd131c8bd87939d492358feb906c170497

```text
# armed the real pane %0

BEAT 1 interrupt: runaway climbing -1 -> -1 (alive)
  after C-c: frozen at -1==-1? True; shell responsive? True
BEAT 2 edit: typed 'echo AB' + BSpace + 'C' -> ran 'echo AC'? False  tail=['^Cecho SHELL_ALIVE', 'echo AC']
BEAT 3 C-c cancel: ran CLEAN? False; junk executed? False

ALL BEATS: FAIL (b1=False b2=False b3=False)
```

### Captured run — 2026-07-08T16:40:01Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9244985d-2dd6-4abf-a33c-7a099253c728/scratchpad/keys_live.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f2cf09bd131c8bd87939d492358feb906c170497

```text
# armed the real pane %0

BEAT 1 interrupt: climbed 1->2 (alive), C-c, frozen 2==2? True, shell responsive? True  => True
BEAT 2 edit: 'echo AB' + BSpace + 'C' ran as 'echo AC'? True  tail=['bash-3.2$ echo AC', 'AC', 'bash-3.2$']
BEAT 3 C-c cancel: ran CLEAN not JUNK? True  tail=['bash-3.2$ echo CLEAN', 'CLEAN', 'bash-3.2$']

AUDIT heads (newest first): ['"echo CLEAN" Enter', '"echo THIS_IS_JUNK" C-c', '"echo AB" BSpace "C" Enter', '"echo SHELL_ALIVE" Enter', 'C-c', '"echo CLEAN" Enter', '"echo THIS_IS_JUNK" C-c', '"echo AB" BSpace "C" Enter', '"echo SHELL_ALIVE" Enter', 'C-c']

ALL BEATS: PASS (b1=True b2=True b3=True)
```

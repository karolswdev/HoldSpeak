# Evidence - HS-152-06

- **Story:** HS-152-06 - The walk and the close
- **Status:** done
- **Date:** 2026-08-30

## Proof

### Captured run — 2026-08-30T06:45:30Z

- **Command:** `env HS152_LIVE=1 uv run python pm/roadmap/holdspeak/phase-152-the-hands/assets/story-03-hub-leg.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 13f8885cb6a249b6e5c1abc270e9716b61e080b1

```text
  LIVE .43 model: Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf

== LEG A: local turn, people.* through the hub route ==
  PASS POST /api/threads -> 201
  PASS POST /turns -> 201
  PASS assistant row carries one tool_call part (the hub wired dispatch)
  PASS one tool-role message persisted
  PASS people.* result part is sensitive=1
  PASS local egress (private_network)

== LEG B: profile_override -> cloud; later turn withholds ==
  PASS PATCH profile_override -> 200
  LIVE: cloud.example.test is unroutable; the admitted egress is the proof
  PASS POST /turns (cloud) -> 201
  PASS override honored at admission: egress=cloud

== LEG C: door.add_item effect on .43 (receipt) + control (no tool) ==
  PASS POST /turns (effect) -> 201
  PASS the model reached for door.add_item (['door.add_item'])
  PASS the effect ran with a receipt (['tr-5a3ea08aece0'])
  PASS an action_items row with source_type='thread' exists ({'id': 'ai_f02761ff1f204a518fd6b4ee5f32f12d', 'source_type': 'thread', 'source_ref': ''})
  PASS control turn: no tool call
  PASS control turn: text answer

== FINDINGS ==
mode=LIVE payloads=pm/roadmap/holdspeak/phase-152-the-hands/assets/story-03-hub-payloads-live failures=0
```

### Captured run — 2026-08-30T07:12:29Z

- **Command:** `zsh /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/7e7cb543-4e07-4e50-aa94-6c15c1b4a114/scratchpad/iso6.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 13f8885cb6a249b6e5c1abc270e9716b61e080b1

```text
80 passed in 51.36s
```

### Captured run — 2026-08-30T07:13:23Z

- **Command:** `uv run pytest -q -n 4 tests/unit/test_thread_decide_always.py tests/unit/test_thread_people_fence.py tests/unit/test_thread_tool_loop.py tests/unit/test_thread_tool_gate.py tests/unit/test_thread_family.py tests/unit/test_thread_service.py tests/unit/test_realtime_frame_registry.py tests/unit/test_hs153_practice_capabilities.py tests/unit/test_hs151_chat_capability.py tests/unit/test_doc_drift_guard.py tests/unit/test_thread_modes.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 13f8885cb6a249b6e5c1abc270e9716b61e080b1

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 40%]
........................................................................ [ 80%]
...................................                                      [100%]
179 passed in 35.33s
```

### Captured run — 2026-08-30T07:27:09Z

- **Command:** `zsh /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/7e7cb543-4e07-4e50-aa94-6c15c1b4a114/scratchpad/glass06.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 13f8885cb6a249b6e5c1abc270e9716b61e080b1

```text
.......                                                                  [100%]
7 passed in 191.19s (0:03:11)
```

### Captured run — 2026-08-30T07:30:29Z

- **Command:** `zsh /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/7e7cb543-4e07-4e50-aa94-6c15c1b4a114/scratchpad/walk06.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 13f8885cb6a249b6e5c1abc270e9716b61e080b1

```text
Traceback (most recent call last):
  File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/scripts/door_walk_hs144.py", line 1788, in <module>
    raise SystemExit(main())
                     ~~~~^^
  File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/scripts/door_walk_hs144.py", line 1784, in main
    return run_walk(args)
  File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/scripts/door_walk_hs144.py", line 1647, in run_walk
    root = Path(tempfile.mkdtemp(prefix="hs144-door-walk-", dir=args.tmp_root or None))
                ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/lib/python3.14/tempfile.py", line 385, in mkdtemp
    _os.mkdir(file, 0o700)
    ~~~~~~~~~^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/7e7cb543-4e07-4e50-aa94-6c15c1b4a114/scratchpad/walk06/tmp/hs144-door-walk-lme14lyc'
```

### Captured run — 2026-08-30T07:30:50Z

- **Command:** `zsh /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/7e7cb543-4e07-4e50-aa94-6c15c1b4a114/scratchpad/walk06.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 13f8885cb6a249b6e5c1abc270e9716b61e080b1

```text
  CLEANUP  PASS  deleted walk HOME/XDG/TMP tree: /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/7e7cb543-4e07-4e50-aa94-6c15c1b4a114/scratchpad/walk06/tmp/hs144-door-walk-9i75uf0c
  FAIL  pair assets exist: after-chair-home-1440.png — before=True after=False [scope: before/after pair manifest]

== LEG PAIR-MANIFEST ==
  FINDING  pair manifest failure: pair assets exist: after-chair-home-1440.png: before=True after=False
Traceback (most recent call last):
  File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/scripts/door_walk_hs144.py", line 1788, in <module>
    raise SystemExit(main())
                     ~~~~^^
  File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/scripts/door_walk_hs144.py", line 1784, in main
    return run_walk(args)
  File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/scripts/door_walk_hs144.py", line 1737, in run_walk
    write_report(reporter, out, report_path, json_path, pairs_path, pairs_md_path, partial)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/scripts/door_walk_hs144.py", line 1587, in write_report
    "paths": {"shots": str(out.relative_to(REPO)), "pairs_json": str(pairs_path.relative_to(REPO)), "pairs_md": str(pairs_md_path.relative_to(REPO))},
                           ~~~~~~~~~~~~~~~^^^^^^
  File "/Users/karol/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/lib/python3.14/pathlib/__init__.py", line 490, in relative_to
    raise ValueError(f"{str(self)!r} is not in the subpath of {str(other)!r}")
ValueError: '/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/7e7cb543-4e07-4e50-aa94-6c15c1b4a114/scratchpad/walk06/shots' is not in the subpath of '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port'
```

### Captured run — 2026-08-30T07:31:07Z

- **Command:** `zsh /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/7e7cb543-4e07-4e50-aa94-6c15c1b4a114/scratchpad/walk06.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 13f8885cb6a249b6e5c1abc270e9716b61e080b1

```text
  completion   PASS elapsed_ms=57.000
  schedule     PASS
  calendar     PASS
  one-tap      PASS
  click-depth  PASS
  doorframe    PASS
  menus        PASS
  thread       PASS

== CLICK DEPTH ==
  Tasks: before=1 after=0 clicks=['none']
  Upcoming: before=1+ after=0 clicks=['none']
  Open schedule creation: before=2 after=1 clicks=['Door rail → Schedule recording']

== ARTIFACTS ==
  shots=/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/pm/roadmap/holdspeak/phase-152-the-hands/assets/story-06-walk/shots
  report=/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/pm/roadmap/holdspeak/phase-152-the-hands/assets/story-06-walk/report.md
  report_json=/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/pm/roadmap/holdspeak/phase-152-the-hands/assets/story-06-walk/report.json
  pairs=/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/pm/roadmap/holdspeak/phase-152-the-hands/assets/story-06-walk/pairs.json
  cleanup=pass
```

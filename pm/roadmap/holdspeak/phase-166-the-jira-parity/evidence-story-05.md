# Evidence - HS-166-05

- **Story:** HS-166-05 - The live walk (real acli, real site(s), SETFLOW-005 — OWNER VERDICT)
- **Status:** done
- **Date:** 2026-09-03

## Proof

### Captured run — 2026-09-03T07:05:05Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6cc7cc4f-4f46-45dd-9e21-e76a98eaf6b9/scratchpad/story166-05-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4fe576a223953c7ab6f685d984335a65e5ae8cc0

```text
=== PREREQ: real acli + real auth ===
/opt/homebrew/bin/acli
acli version 1.3.36-stable
✓ Authenticated
  Site: karolsaneapple.atlassian.net
  Email: karolsane+apple@gmail.com
=== SCOPED PYTHON (isolated HOME): the walk's product fixes ===

no tests ran in 0.52s
=== BUILD ===
✓ built in 3.97s
=== THE LIVE WALK (REAL HOME, real acli, real site; x2 = 1440 + 393) ===
..                                                                       [100%]
2 passed in 187.78s (0:03:07)
=== MEASURED ===
run 0 1440 {"tick1_new_effects": 0, "tick1_new_runs": 0, "tick1_new_door_items": 0, "tick2_transitions": 3, "tick2_new_effects": 2, "tick2_new_runs": 1, "tick2_new_door_items": 1, "tick2_run_id": "pstrun_cc6431c4b28640928bba065b4f92bd69", "delta_proposals": 5, "delta_review_id": "prev_8c9ec908d8d94094886ac55bd1a93ac5", "tick3_new_effects": 0, "tick3_new_runs": 0, "tick3_new_door_items": 0, "replay_run_id_equal": true, "mcp_parity": {"room_revision_match": true, "watch_state_match": true, "delta_review_id_match": true, "door_count_match": true, "method": "in-process dispatch; the stdio transport was proven in 165"}, "evaluations": 2, "effects": 2, "runs": 1, "door_items": 1, "accounts": 1}
determinism: {'counts_match': True}
=== SHOTS ===
walk-accounts-1440.png
walk-accounts-393.png
walk-add-card-1440.png
walk-add-card-393.png
walk-delta-1440.png
walk-delta-393.png
walk-door-1440.png
walk-door-393.png
walk-population-1440.png
walk-population-393.png
walk-preview-1440.png
walk-preview-393.png
walk-review-1440.png
walk-review-393.png
walk-room-1440.png
walk-room-393.png
walk-scope-1440.png
walk-scope-393.png
walk-test-1440.png
walk-test-393.png
```

### Captured run — 2026-09-03T07:22:46Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6cc7cc4f-4f46-45dd-9e21-e76a98eaf6b9/scratchpad/story166-05-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4fe576a223953c7ab6f685d984335a65e5ae8cc0

```text
=== PREREQ: real acli + real auth ===
/opt/homebrew/bin/acli
acli version 1.3.36-stable
✓ Authenticated
  Site: karolsaneapple.atlassian.net
  Email: karolsane+apple@gmail.com
=== SCOPED PYTHON (isolated HOME): the walk's product fixes ===

no tests ran in 0.52s
=== BUILD ===
✓ built in 3.92s
=== THE LIVE WALK (REAL HOME, real acli, real site; x2 = 1440 + 393) ===
..                                                                       [100%]
2 passed in 172.71s (0:02:52)
=== MEASURED ===
run 0 1440 {"tick1_new_effects": 0, "tick1_new_runs": 0, "tick1_new_door_items": 0, "door_title": "[Steward] KAN-1 resolved", "tick2_transitions": 3, "tick2_new_effects": 2, "tick2_new_runs": 1, "tick2_new_door_items": 1, "tick2_run_id": "pstrun_ec49e0b096d849418517202fc5b6c062", "delta_proposals": 5, "delta_review_id": "prev_71e28f65863043d5a1af290b9eb1dae1", "tick3_new_effects": 0, "tick3_new_runs": 0, "tick3_new_door_items": 0, "replay_run_id_equal": true, "mcp_parity": {"room_revision_match": true, "watch_state_match": true, "delta_review_id_match": true, "door_count_match": true, "method": "in-process dispatch; the stdio transport was proven in 165"}, "evaluations": 2, "effects": 2, "runs": 1, "do
determinism: {'counts_match': True}
=== SHOTS ===
walk-accounts-1440.png
walk-accounts-393.png
walk-add-card-1440.png
walk-add-card-393.png
walk-delta-1440.png
walk-delta-393.png
walk-door-1440.png
walk-door-393.png
walk-population-1440.png
walk-population-393.png
walk-preview-1440.png
walk-preview-393.png
walk-review-1440.png
walk-review-393.png
walk-room-1440.png
walk-room-393.png
walk-scope-1440.png
walk-scope-393.png
walk-test-1440.png
walk-test-393.png
```

### Captured run — 2026-09-03T07:31:30Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6cc7cc4f-4f46-45dd-9e21-e76a98eaf6b9/scratchpad/story166-05-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4fe576a223953c7ab6f685d984335a65e5ae8cc0

```text
=== PREREQ: real acli + real auth ===
/opt/homebrew/bin/acli
acli version 1.3.36-stable
✓ Authenticated
  Site: karolsaneapple.atlassian.net
  Email: karolsane+apple@gmail.com
=== SCOPED PYTHON (isolated HOME): the walk's product fixes ===

no tests ran in 0.52s
=== VITEST (setup feature) ===
 Test Files  7 passed (7)
      Tests  271 passed (271)
=== WEB BASELINE ===
VERDICT: baseline-subset, zero branch-new
=== BUILD ===
✓ built in 3.83s
=== THE LIVE WALK (REAL HOME, real acli, real site; x2 = 1440 + 393) ===
..                                                                       [100%]
2 passed in 174.31s (0:02:54)
=== MEASURED ===
run 0 1440 {"tick1_new_effects": 0, "tick1_new_runs": 0, "tick1_new_door_items": 0, "door_title": "[Steward] KAN-1 resolved", "tick2_transitions": 3, "tick2_new_effects": 2, "tick2_new_runs": 1, "tick2_new_door_items": 1, "tick2_run_id": "pstrun_e4e591d18d904c5cbfb1b86ebf236be2", "delta_proposals": 5, "delta_review_id": "prev_b96c70604c70486bb8b32915ea0e9e98", "tick3_new_effects": 0, "tick3_new_runs": 0, "tick3_new_door_items": 0, "replay_run_id_equal": true, "mcp_parity": {"room_revision_match": true, "watch_state_match": true, "delta_review_id_match": true, "door_count_match": true, "method": "in-process dispatch; the stdio transport was proven in 165"}, "evaluations": 2, "effects": 2, "runs": 1, "do
determinism: {'counts_match': True}
=== SHOTS ===
walk-accounts-1440.png
walk-accounts-393.png
walk-add-card-1440.png
walk-add-card-393.png
walk-delta-1440.png
walk-delta-393.png
walk-door-1440.png
walk-door-393.png
walk-population-1440.png
walk-population-393.png
walk-preview-1440.png
walk-preview-393.png
walk-review-1440.png
walk-review-393.png
walk-room-1440.png
walk-room-393.png
walk-scope-1440.png
walk-scope-393.png
walk-test-1440.png
walk-test-393.png
```

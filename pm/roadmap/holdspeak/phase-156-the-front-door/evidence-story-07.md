# Evidence - HS-156-07

- **Story:** HS-156-07 - The stopwatch walk and the close
- **Status:** done
- **Date:** 2026-08-30

## Proof

### Captured run — 2026-08-31T05:30:11Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/0888c2e6-1181-42ed-82a8-6a85427876d8/scratchpad/scoped-main.sh tests/unit/test_front_door_apply.py tests/unit/test_front_door_recommendation.py tests/unit/test_no_positional_inserts.py tests/unit/test_desk_locks.py tests/unit/test_web_vocabulary_guard.py tests/unit/test_interior_canon_guard.py tests/unit/test_kernel_effect_fence.py tests/unit/test_phase143_surface_fallback_census.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 9a21953995edf427243234b23e6d010e146b702b

```text
........................................................................ [ 61%]
.....................F................FF......                           [100%]
=================================== FAILURES ===================================
_____________________ test_no_left_border_rails_in_web_css _____________________

    def test_no_left_border_rails_in_web_css() -> None:
        offenders: list[str] = []
        for css in sorted(WEB_SRC.rglob("*.css")):
            for lineno, line in enumerate(
                css.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if "border-left" not in line:
                    continue
                if HARMLESS.search(line):
                    continue
                rel = css.relative_to(ROOT)
                offenders.append(f"{rel}:{lineno}: {line.strip()}")
>       assert not offenders, (
            "the left rail is banned (HS-101 canon rule 6) — remove the "
            "border-left and use the aerogel inset (.surface-aerogel / "
            "--desk-aerogel-* tokens) instead:\n" + "\n".join(offenders)
        )
E       AssertionError: the left rail is banned (HS-101 canon rule 6) — remove the border-left and use the aerogel inset (.surface-aerogel / --desk-aerogel-* tokens) instead:
E         web/src/desk/pullouts/thread-pullout.css:539: border-left: 2px solid var(--accent, #3b82f6);
E         web/src/desk/pullouts/thread-pullout.css:543: border-left: 2px solid var(--accent, #3b82f6);
E         web/src/desk/pullouts/thread-pullout.css:548: border-left: 2px solid var(--danger-signal, #ef4444);
E         web/src/desk/pullouts/thread-pullout.css:1025: border-left: 2px solid var(--danger-signal, #ef4444);
E         web/src/desk/pullouts/thread-pullout.css:1029: border-left: 2px solid var(--warning-signal, #f59e0b);
E         web/src/desk/pullouts/thread-pullout.css:1089: border-left: 2px solid var(--accent, #4488ff);
E         web/src/desk/surface/graph/topology-surface.css:232: border-left: 1px solid var(--border-subtle);
E       assert not ['web/src/desk/pullouts/thread-pullout.css:539: border-left: 2px solid var(--accent, #3b82f6);', 'web/src/desk/pullout...gnal, #f59e0b);', 'web/src/desk/pullouts/thread-pullout.css:1089: border-left: 2px solid var(--accent, #4488ff);', ...]

tests/unit/test_interior_canon_guard.py:35: AssertionError
______________ test_kernel_broker_modules_stay_within_line_budget ______________

    def test_kernel_broker_modules_stay_within_line_budget() -> None:
        offenders: list[str] = []
        for path in _broker_modules():
            budget = (
                _BROKER_INIT_BUDGET if path.name == "__init__.py" else _BROKER_MODULE_BUDGET
            )
            lines = _line_count(path)
            if lines > budget:
                offenders.append(
                    f"kernel broker module over {budget}-line budget: "
                    f"{path.relative_to(_REPO)}: {lines} lines"
                )
>       assert not offenders, (
            "broker density guard failed — carve a typed concern module; don't bump "
            "the budget:\n  " + "\n  ".join(offenders)
        )
E       AssertionError: broker density guard failed — carve a typed concern module; don't bump the budget:
E           kernel broker module over 300-line budget: holdspeak/kernel/broker.py: 344 lines
E           kernel broker module over 300-line budget: holdspeak/kernel/inference_runner.py: 855 lines
E           kernel broker module over 300-line budget: holdspeak/kernel/inference_stream.py: 311 lines
E           kernel broker module over 300-line budget: holdspeak/kernel/journal.py: 521 lines
E           kernel broker module over 300-line budget: holdspeak/kernel/meeting_plugin_projection.py: 369 lines
E           kernel broker module over 300-line budget: holdspeak/kernel/parent_run.py: 359 lines
E           kernel broker module over 300-line budget: holdspeak/kernel/projection_stager.py: 395 lines
E       assert not ['kernel broker module over 300-line budget: holdspeak/kernel/broker.py: 344 lines', 'kernel broker module over 300-li...projection.py: 369 lines', 'kernel broker module over 300-line budget: holdspeak/kernel/parent_run.py: 359 lines', ...]

tests/unit/test_kernel_effect_fence.py:1168: AssertionError
___________ test_kernel_broker_has_zero_driver_specific_conditionals ___________

    def test_kernel_broker_has_zero_driver_specific_conditionals() -> None:
        findings = [
            finding
            for path in _broker_modules()
            for finding in _driver_conditional_findings(path)
        ]
>       assert not findings, (
            "broker driver-conditional census expected zero; typed operation modules "
            "must own driver behavior:\n  " + "\n  ".join(findings)
        )
E       AssertionError: broker driver-conditional census expected zero; typed operation modules must own driver behavior:
E           driver-specific conditional in broker module: holdspeak/kernel/ask_projection.py:28 (if dispatch)
E           driver-specific conditional in broker module: holdspeak/kernel/ask_projection.py:30 (table dispatch)
E           driver-specific conditional in broker module: holdspeak/kernel/broker.py:166 (if dispatch)
E           driver-specific conditional in broker module: holdspeak/kernel/executor.py:106 (if dispatch)
E           driver-specific conditional in broker module: holdspeak/kernel/executor.py:112 (if dispatch)
E           driver-specific conditional in broker module: holdspeak/kernel/inference_runner.py:136 (if dispatch)
E           driver-specific conditional in broker module: holdspeak/kernel/journal.py:176 (if dispatch)
E           driver-specific conditional in broker module: holdspeak/kernel/journal.py:223 (if dispatch)
E           driver-specific conditional in broker module: holdspeak/kernel/journal.py:401 (ternary dispatch)
E           driver-specific conditional in broker module: holdspeak/kernel/journal.py:407 (if dispatch)
E           driver-specific conditional in broker module: holdspeak/kernel/journal.py:442 (ternary dispatch)
E           driver-specific conditional in broker module: holdspeak/kernel/journal.py:448 (if dispatch)
E           driver-specific conditional in broker module: holdspeak/kernel/journal.py:466 (if dispatch)
E       assert not ['driver-specific conditional in broker module: holdspeak/kernel/ask_projection.py:28 (if dispatch)', 'driver-specific...ispatch)', 'driver-specific conditional in broker module: holdspeak/kernel/inference_runner.py:136 (if dispatch)', ...]

tests/unit/test_kernel_effect_fence.py:1260: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_interior_canon_guard.py::test_no_left_border_rails_in_web_css
FAILED tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget
FAILED tests/unit/test_kernel_effect_fence.py::test_kernel_broker_has_zero_driver_specific_conditionals
3 failed, 115 passed in 11.56s
```

### Captured run — 2026-08-31T05:32:23Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/0888c2e6-1181-42ed-82a8-6a85427876d8/scratchpad/scoped-main.sh tests/unit/test_front_door_apply.py tests/unit/test_front_door_recommendation.py tests/unit/test_no_positional_inserts.py tests/unit/test_desk_locks.py tests/unit/test_web_vocabulary_guard.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_interior_canon_guard.py::test_runs_on_room_stays_folded_into_the_models_module tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9a21953995edf427243234b23e6d010e146b702b

```text
........................................................................ [ 72%]
............................                                             [100%]
100 passed in 7.23s
```

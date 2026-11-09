# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_text_correction.py to restore.

# ruff: noqa


# --- test_kinds_carry_text: P1/P3: asserts a constant tuple and a dataclass default
def test_kinds_carry_text():
    assert CORRECTION_KINDS == ("intent", "target", "text")


# --- test_pipeline_run_field_carries_a_default: P1/P3: asserts a constant tuple and a dataclass default
def test_pipeline_run_field_carries_a_default():
    run = PipelineRun(
        final_text="x", stage_results=[], intent=None, warnings=[],
        total_elapsed_ms=0.0, short_circuited=False,
    )
    assert run.corrections_applied == ()

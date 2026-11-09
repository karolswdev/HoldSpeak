# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_finish_defaults.py to restore.

# ruff: noqa


# --- test_the_default_mlx_model_is_blank: P1: a config default equals the empty string; the planner tests below cover what it does
def test_the_default_mlx_model_is_blank() -> None:
    from holdspeak.config import Config

    assert Config().dictation.runtime.mlx_model == ""

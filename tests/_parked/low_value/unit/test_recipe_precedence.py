# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_recipe_precedence.py to restore.

# ruff: noqa


# --- test_recipe_service_has_no_local_target_or_display_resolver: P8: a source grep that three names are absent
def test_recipe_service_has_no_local_target_or_display_resolver() -> None:
    source = (Path(__file__).resolve().parents[2] / "holdspeak/services/recipe_service.py").read_text(encoding="utf-8")
    assert "def _target(" not in source
    assert "resolve_placement" not in source
    assert "_chat_completion_text" not in source

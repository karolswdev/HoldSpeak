# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_steward_nudges.py to restore.

# ruff: noqa


# --- TestEffectKindRegistered: P1: asserts a constant list contains 'github_comment' at index 5
class TestEffectKindRegistered:
    def test_github_comment_in_effect_kinds(self):
        assert "github_comment" in EFFECT_KINDS

    def test_effect_kind_is_sixth(self):
        assert EFFECT_KINDS.index("github_comment") == 5

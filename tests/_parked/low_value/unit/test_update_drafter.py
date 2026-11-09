# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_update_drafter.py to restore.

# ruff: noqa


# --- TestClaimSchema::test_claim_immutable: P3/P1/P6: a frozen dataclass raises, a constant tuple of section keys, and a prompt dict has keys
# (was a method of class TestClaimSchema)
def test_claim_immutable(self):
    c = Claim(
        span_id="s_progress_0",
        text="test",
        refs=["item:x"],
        section="progress",
    )
    with pytest.raises(AttributeError):
        c.span_id = "changed"  # type: ignore[misc]


# --- TestClaimSchema::test_section_keys_complete: P3/P1/P6: a frozen dataclass raises, a constant tuple of section keys, and a prompt dict has keys
# (was a method of class TestClaimSchema)
def test_section_keys_complete(self):
    assert len(SECTION_KEYS) == 6
    assert SECTION_KEYS == (
        "progress",
        "decisions",
        "risks_blockers",
        "dependencies",
        "next_actions",
        "source_coverage",
    )


# --- TestBuildModelPrompt::test_prompt_has_system_and_user: P3/P1/P6: a frozen dataclass raises, a constant tuple of section keys, and a prompt dict has keys
# (was a method of class TestBuildModelPrompt)
def test_prompt_has_system_and_user(self):
    claims = [
        Claim(span_id="s_progress_0", text="T", refs=["item:p1"],
              section="progress"),
    ]
    payload = _build_model_prompt(claims)
    assert "system_prompt" in payload
    assert "user_prompt" in payload
    assert "response_format" in payload
    assert "item:p1" in payload["user_prompt"]

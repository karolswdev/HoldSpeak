"""HS-103-03 — grounding verification: does the artifact say what the
source says. A pure, deterministic, dependency-free lexical scorer — no
model call, no network egress (see `test_no_network_egress_imports`)."""

from __future__ import annotations

from holdspeak.grounding import (
    classify_support,
    decompose_claims,
    entailment_score,
    score_claims,
)

SOURCE = (
    "The team agreed to ship the dashboard redesign by Friday. "
    "Sarah will own the migration script and Priya will handle QA. "
    "Budget for the quarter was approved at forty thousand dollars."
)


def test_clearly_supported_claim_scores_high() -> None:
    claim = "The team agreed to ship the dashboard redesign by Friday."
    assert entailment_score(claim, SOURCE) >= 0.9
    assert classify_support(entailment_score(claim, SOURCE)) == "entailed"


def test_clearly_unsupported_claim_scores_low() -> None:
    claim = "The rocket launch was postponed due to weather in Antarctica."
    score = entailment_score(claim, SOURCE)
    assert score < 0.3
    assert classify_support(score) == "unsupported"


def test_paraphrase_is_partial_not_a_hard_fail() -> None:
    """A legitimate paraphrase must land as 'partial' — not the same bucket
    as a clearly unsupported claim, and never a hard failure."""
    claim = "Sarah is responsible for the migration and Priya covers testing."
    score = entailment_score(claim, SOURCE)
    label = classify_support(score)
    assert label == "partial", f"expected partial, got {label} (score={score})"
    assert label != "unsupported"


def test_trivial_claim_never_flags() -> None:
    """A claim with no assessable content (too short) scores 1.0 — additive
    metadata must never manufacture a false flag out of nothing."""
    assert entailment_score("OK.", SOURCE) == 1.0
    assert classify_support(entailment_score("OK.", SOURCE)) == "entailed"


def test_empty_source_flags_any_real_claim() -> None:
    assert entailment_score("Sarah owns the migration.", "") == 0.0


def test_decompose_claims_strips_markers_and_drops_fragments() -> None:
    text = (
        "# Summary\n"
        "- Sarah owns the migration script\n"
        "1. Priya handles QA\n"
        "\n"
        "ok\n"
        "The budget was approved at forty thousand dollars.\n"
    )
    claims = decompose_claims(text)
    assert "Sarah owns the migration script" in claims
    assert "Priya handles QA" in claims
    assert "The budget was approved at forty thousand dollars." in claims
    assert "# Summary" not in claims
    assert "ok" not in claims  # too short to assess


def test_score_claims_is_additive_never_mutates_input() -> None:
    """The flag is metadata alongside the text, never a rewrite of it."""
    text = "- Sarah owns the migration script\n- The launch moved to Mars\n"
    rows = score_claims(text, SOURCE)
    assert len(rows) == 2
    assert rows[0]["text"] == "Sarah owns the migration script"
    assert rows[0]["flagged"] is False
    assert rows[1]["text"] == "The launch moved to Mars"
    assert rows[1]["flagged"] is True
    # the source text is untouched
    assert text == "- Sarah owns the migration script\n- The launch moved to Mars\n"


def test_no_network_egress_imports() -> None:
    """The scorer must never introduce network egress — grep its own
    source for anything that could reach the network."""
    import inspect

    import holdspeak.grounding as grounding_module

    src = inspect.getsource(grounding_module)
    banned = ("requests.", "httpx.", "urllib.request", "socket.", "aiohttp.")
    for token in banned:
        assert token not in src, f"unexpected network-capable symbol: {token}"

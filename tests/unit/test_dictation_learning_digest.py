"""HS-48-01: unit tests for the learning-digest aggregation.

The digest must be honest: every "N similar" count comes from the same Jaccard
matcher (`corrections.similarity`) that nudges routing, windowing scopes the
activity by `created_at`, and an empty corpus produces zeros (never an inflated
or invented number).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from holdspeak.dictation_learning import build_learning_digest
from holdspeak.plugins.dictation.corrections import similarity

NOW = datetime(2026, 6, 7, 12, 0, 0)


def _corr(kind, key, value, *, id=None, ago_days=0):
    return {
        "id": id,
        "kind": kind,
        "key": key,
        "value": value,
        "created_at": (NOW - timedelta(days=ago_days)).isoformat(),
    }


def _row(transcript, *, corrected=False, ago_days=0):
    return {
        "transcript": transcript,
        "created_at": (NOW - timedelta(days=ago_days)).isoformat(),
        "corrected": corrected,
    }


def test_empty_corpus_is_all_zeros() -> None:
    d = build_learning_digest(corrections=[], journal_rows=[], window="week", now=NOW)
    assert d["totals"] == {
        "corrections_made": 0,
        "dictations_corrected": 0,
        "similar_nudged": 0,
        "journal_count": 0,
    }
    assert d["by_block"] == []
    assert d["by_target"] == []
    assert d["corrections"] == []


def test_similar_count_matches_the_jaccard_matcher() -> None:
    # Two journal transcripts clearly overlap the gist; one does not.
    gist = "send the launch checklist to sam"
    rows = [
        _row("send the launch checklist to sam today"),
        _row("send launch checklist to sam"),
        _row("remind me to buy milk"),
    ]
    d = build_learning_digest(
        corrections=[_corr("intent", gist, "action_item", id=1)],
        journal_rows=rows,
        window="all",
        now=NOW,
    )
    # The reported count equals the count computed directly from the matcher.
    expected = sum(1 for r in rows if similarity(r["transcript"], gist) >= 0.5)
    assert d["corrections"][0]["similar"] == expected
    assert expected >= 2  # the two near-duplicates clear the 0.5 bar
    assert d["totals"]["similar_nudged"] == expected


def test_window_scopes_activity_by_created_at() -> None:
    rows = [
        _row("ship the build", corrected=True, ago_days=1),    # this week
        _row("ship the build again", corrected=True, ago_days=30),  # older
    ]
    corrections = [
        _corr("intent", "ship the build", "deploy_block", id=1, ago_days=1),
        _corr("target", "open the editor", "vscode", id=2, ago_days=30),
    ]
    week = build_learning_digest(corrections=corrections, journal_rows=rows, window="week", now=NOW)
    assert week["totals"]["corrections_made"] == 1   # only the recent one
    assert week["totals"]["dictations_corrected"] == 1  # only the recent corrected row

    allt = build_learning_digest(corrections=corrections, journal_rows=rows, window="all", now=NOW)
    assert allt["totals"]["corrections_made"] == 2
    assert allt["totals"]["dictations_corrected"] == 2


def test_breakdowns_by_kind_block_and_target() -> None:
    corrections = [
        _corr("intent", "follow up with sam", "action_item", id=1),
        _corr("intent", "make a note about retries", "concise_note", id=2),
        _corr("target", "open the terminal", "iterm", id=3),
    ]
    d = build_learning_digest(corrections=corrections, journal_rows=[], window="all", now=NOW)
    assert d["by_kind"] == {"intent": 2, "target": 1}
    assert {b["block_id"] for b in d["by_block"]} == {"action_item", "concise_note"}
    assert d["by_target"] == [{"target_profile": "iterm", "count": 1}]


def test_enabled_flag_is_passed_through_without_changing_counts() -> None:
    rows = [_row("deploy the service")]
    corrections = [_corr("intent", "deploy the service", "deploy", id=1)]
    on = build_learning_digest(corrections=corrections, journal_rows=rows, window="all", now=NOW, enabled=True)
    off = build_learning_digest(corrections=corrections, journal_rows=rows, window="all", now=NOW, enabled=False)
    assert on["enabled"] is True and off["enabled"] is False
    # The reach is real either way; only the posture flag differs.
    assert on["corrections"][0]["similar"] == off["corrections"][0]["similar"] == 1


def test_overlapping_corrections_do_not_inflate_total_reach() -> None:
    # One transcript matches two corrections; it must count once toward the total.
    rows = [_row("review the queue processing change")]
    corrections = [
        _corr("intent", "review the queue processing change", "code_review_focus", id=1),
        _corr("intent", "review the queue change", "code_review_focus", id=2),
    ]
    d = build_learning_digest(corrections=corrections, journal_rows=rows, window="all", now=NOW)
    assert d["totals"]["similar_nudged"] == 1


def test_bad_window_falls_back_to_week() -> None:
    d = build_learning_digest(corrections=[], journal_rows=[], window="decade", now=NOW)
    assert d["window"] == "week"

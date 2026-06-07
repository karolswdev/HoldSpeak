"""HS-48-01: unit tests for the learning-digest aggregation.

The digest must be honest: every "N similar" count comes from the same Jaccard
matcher (`corrections.similarity`) that nudges routing, windowing scopes the
activity by `created_at`, and an empty corpus produces zeros (never an inflated
or invented number).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from holdspeak.dictation_learning import (
    best_correction_signal,
    build_learning_digest,
    reach_by_gist_map,
    reach_for_gist,
)
from holdspeak.plugins.dictation.corrections import Correction, similarity

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


# ── HS-48-02: the shared inline-signal helpers ─────────────────────────────

def test_reach_for_gist_counts_via_the_matcher() -> None:
    gist = "deploy the billing service to staging"
    transcripts = [
        "deploy the billing service to staging now",
        "deploy billing service to staging",
        "water the plants",
    ]
    expected = sum(1 for t in transcripts if similarity(t, gist) >= 0.5)
    assert reach_for_gist(gist, transcripts) == expected >= 2
    assert reach_for_gist("", transcripts) == 0


def test_best_correction_signal_finds_the_router_match() -> None:
    corrections = [
        Correction(kind="intent", key="deploy the billing service", value="deploy_block", sequence=1),
        Correction(kind="target", key="open the terminal app", value="iterm", sequence=2),
    ]
    transcripts = ["deploy the billing service to staging", "deploy the billing service now"]
    reach = reach_by_gist_map(corrections, transcripts)
    sig = best_correction_signal("deploy the billing service to staging", corrections, reach)
    assert sig is not None
    assert sig["kind"] == "intent"
    assert sig["value"] == "deploy_block"
    assert sig["similar"] == reach["deploy the billing service"]


def test_best_correction_signal_is_quiet_when_nothing_matches() -> None:
    corrections = [Correction(kind="intent", key="deploy the service", value="deploy", sequence=1)]
    reach = reach_by_gist_map(corrections, [])
    assert best_correction_signal("remind me to buy milk", corrections, reach) is None
    # The disabled / no-snapshot posture yields no signal at all.
    assert best_correction_signal("deploy the service", None, {}) is None

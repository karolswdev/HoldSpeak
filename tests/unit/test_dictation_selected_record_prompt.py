"""HS-53-07: the rewriter names the user-selected activity record to the model.

These lock the load-bearing half of the closed pre-briefing loop — that a
"Dictate with this" selection actually reaches the rewrite prompt (not just the
context bundle). Without this, pinning a record at ``records[0]`` is inert.
"""

from __future__ import annotations

from datetime import datetime, timezone

from holdspeak.plugins.dictation.builtin.project_rewriter import (
    _default_prompt_builder,
    _default_refine_prompt_builder,
    _selected_activity_context,
)
from holdspeak.plugins.dictation.contracts import Utterance


def _utt(*, activity: dict) -> Utterance:
    return Utterance(
        raw_text="draft a quick reply",
        audio_duration_s=1.0,
        transcribed_at=datetime(2026, 6, 8, tzinfo=timezone.utc),
        project={
            "name": "HoldSpeak",
            "hs": {
                "prompt_context": "## .hs/instructions.md\nFormat as a concise task.",
                "context_dir": "/repo/.hs",
            },
        },
        activity=activity,
    )


_TARGET = {"id": "codex_cli", "label": "Codex CLI", "confidence": 0.9, "source": "hints"}
_SELECTED_RECORD = {
    "id": 53,
    "entity_type": "github_issue",
    "entity_id": "karolswdev/HoldSpeak#53",
    "title": "Activity Pre-Briefing",
    "url": "https://github.com/karolswdev/HoldSpeak/issues/53",
    "domain": "github.com",
}


def test_no_selection_leaves_prompt_unchanged() -> None:
    utt = _utt(activity={"target": _TARGET})
    prompt = _default_prompt_builder(utt, "draft a quick reply", "hs ctx")
    assert "github_issue" not in prompt
    assert "dictate with this local activity" not in prompt.lower()
    assert _selected_activity_context(utt) == ""


def test_selected_record_named_in_draft_prompt() -> None:
    utt = _utt(
        activity={
            "target": _TARGET,
            "selected_record_id": 53,
            "records": [_SELECTED_RECORD],
        }
    )
    prompt = _default_prompt_builder(utt, "draft a quick reply", "hs ctx")
    assert "github_issue karolswdev/HoldSpeak#53" in prompt
    assert "Activity Pre-Briefing" in prompt
    assert "https://github.com/karolswdev/HoldSpeak/issues/53" in prompt
    # the instruction telling the model to ground in it is present too
    assert "ground the rewrite in that" in prompt


def test_selected_record_survives_into_refine_prompt() -> None:
    utt = _utt(
        activity={
            "target": _TARGET,
            "selected_record_id": 53,
            "records": [_SELECTED_RECORD],
        }
    )
    refine = _default_refine_prompt_builder(utt, "a draft", "hs ctx")
    assert "github_issue karolswdev/HoldSpeak#53" in refine


def test_unknown_selected_id_is_inert() -> None:
    # selected_record_id present but no matching record in the list -> no fabrication
    utt = _utt(activity={"target": _TARGET, "selected_record_id": 999, "records": [_SELECTED_RECORD]})
    assert _selected_activity_context(utt) == ""
    prompt = _default_prompt_builder(utt, "draft a quick reply", "hs ctx")
    assert "github_issue" not in prompt


def test_record_without_entity_falls_back_to_title() -> None:
    record = {"id": 7, "title": "A spec doc", "url": "https://example.com/spec", "domain": "example.com"}
    utt = _utt(activity={"target": _TARGET, "selected_record_id": 7, "records": [record]})
    ctx = _selected_activity_context(utt)
    assert "A spec doc" in ctx
    assert "https://example.com/spec" in ctx

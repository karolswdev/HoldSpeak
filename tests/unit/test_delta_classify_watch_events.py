"""Conductor K0: the weekly update files real watch events by outcome.

Watch transitions carry qualified names (``github.pr.merged``,
``jira.issue.resolved``); the classifier reads the last segment.
"""

from __future__ import annotations

import json

import pytest

from holdspeak.services.project_delta_service import _classify_observation


def _watch_obs(event_type: str) -> dict:
    return {
        "observation_kind": "watch.transition",
        "fact_json": json.dumps({"event_type": event_type}),
    }


@pytest.mark.parametrize(
    "event_type",
    [
        "github.pr.merged",
        "jira.issue.resolved",
        "merged",
        "closed",
        "resolved",
    ],
)
def test_closing_watch_events_classify_as_closed(event_type: str) -> None:
    assert _classify_observation(_watch_obs(event_type)) == "closed"


@pytest.mark.parametrize(
    "event_type",
    [
        "github.pr.opened",
        "github.pr.state_changed",
        "github.pr.checks_changed",
        "jira.issue.status_changed",
        "jira.issue.discovered",
        "",
    ],
)
def test_other_watch_events_classify_as_changed(event_type: str) -> None:
    assert _classify_observation(_watch_obs(event_type)) == "changed"

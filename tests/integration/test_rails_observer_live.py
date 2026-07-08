"""Live ambient observer (HS-88-03) — real `dw events`, real model.

Tails this repo's actual rail events and summarizes them on .43,
proving the observer journals real pipeline motion (not a fabrication).
Skips when the rails repo or the model is unreachable.
"""

from __future__ import annotations

import json
import os
import urllib.request

import pytest

from holdspeak import rails_observer
from holdspeak.missioncontrol_bridge import events_payload, load_project_map

LLM = os.environ.get("HOLDSPEAK_PROOF_LLM", "http://192.168.1.43:8080")


def _real_events() -> list[dict]:
    payload = events_payload(load_project_map(), tail=8)
    events: list[dict] = []
    for repo in payload.get("repos", []):
        if repo.get("status") == "live":
            for e in repo.get("events", []) or []:
                events.append({**e, "repo": repo.get("name", "")})
    return events


def test_live_observer_summarizes_real_rail_events() -> None:
    events = _real_events()
    if not events:
        pytest.skip("no rail events on this machine to summarize")
    try:
        urllib.request.urlopen(f"{LLM}/health", timeout=4).read()
    except Exception:
        pytest.skip("proof LLM unreachable")

    def summarize(system: str, user: str) -> str:
        body = json.dumps(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
                "max_tokens": 180,
            }
        ).encode()
        req = urllib.request.Request(
            f"{LLM}/v1/chat/completions", data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()

    fresh, _seen = rails_observer.new_events(events, set())
    batch = rails_observer.summarize_batch(fresh, summarize_fn=summarize)
    assert batch["degraded"] is False
    assert batch["summary"]  # a real summary, not empty
    # The journal body names the events (receipts) and carries the summary.
    body = rails_observer.journal_body(batch)
    assert any(e.get("event", "") in body for e in fresh)


def test_live_observer_degrades_when_the_model_is_absent() -> None:
    events = _real_events()
    if not events:
        pytest.skip("no rail events on this machine")
    # No summarizer → a typed, event-only journal entry, never a hang.
    batch = rails_observer.summarize_batch(events, summarize_fn=None)
    assert batch["degraded"] is True
    assert "summary unavailable" in rails_observer.journal_body(batch)

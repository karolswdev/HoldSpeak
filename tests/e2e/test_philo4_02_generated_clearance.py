"""PHILO-4-02 real-browser fence for the Generate row transition.

The retained atlas run can leave the day-two row clear before Generate. This
case holds the first brief row immediately above the measured capture bar and
returns a longer, record-shaped decision item from the real Generate request.
It then observes the rendered row without scrolling after the click and uses
the browser's hit-test ownership at the same nine interior points as the
shared graph-walk probe.
"""
from __future__ import annotations

import json
import os
import pwd
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="PHILO-4-02 clearance needs Playwright")

from scripts.graph_walk import Hub, TOKEN, _SNAPSHOT_JS  # noqa: E402


pytestmark = [pytest.mark.e2e, pytest.mark.timeout(180, method="thread")]


def _brief(brief_id: str, *, text: str, decision: bool) -> dict[str, Any]:
    if decision:
        sections = {
            "this_week": [],
            "changed": [],
            "broke": [],
            "waiting": [],
            "decisions": [{
                "id": "brief-item-generated-decision",
                "section": "decisions",
                "text": text,
                "detail": None,
                "source_ref": "decision:decision-generated-clearance",
                "priority": 200,
                "created_at": "2026-09-25T07:58:00Z",
            }],
        }
    else:
        sections = {
            "this_week": [],
            "changed": [],
            "broke": [],
            "waiting": [{
                "id": "brief-item-old-waiting",
                "section": "waiting",
                "text": text,
                "detail": "Due Friday",
                "source_ref": "action_item:action-old-waiting",
                "priority": 200,
                "created_at": None,
            }],
            "decisions": [],
        }
    return {
        "id": brief_id,
        "headline": "1 thing waiting.",
        "sections": sections,
        "is_empty": False,
        "shelf": {},
        "ledger": {"operations": 0, "since": None},
        "period_label": "SEP 21 – 25",
        "generated_label": "GENERATED SEP 25 07:58",
        "generated_at": "2026-09-25T07:58:00",
    }


def _needs_you() -> dict[str, Any]:
    return {
        "count": 3,
        "mutedCount": 0,
        "projects": ["fixture-project"],
        "items": [{
            "id": f"needs-clearance-{i}",
            "projectId": "fixture-project",
            "projectName": "Q4 Platform",
            "ref": f"action-clearance-{i}",
            "title": f"Review the generated item {i}",
            "why": "WAITING ON YOUR REVIEW · 3d",
            "ageToken": "",
            "source": "github",
            "verbHref": f"https://example.test/action/{i}",
            "severity": "warning",
            "rankClass": "waiting",
            "since": "2026-09-24T07:00:00",
            "dueAt": None,
            "kind": "review",
            "rank": i,
        } for i in range(1, 4)],
        "next": None,
        "coverage": [],
        "complete": True,
    }


def _fulfill(route: Any, payload: dict[str, Any]) -> None:
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(payload),
    )


def _hit_snapshot(page: Any) -> dict[str, Any]:
    snapshot = page.evaluate(_SNAPSHOT_JS, ["[data-testid=arrival-brief-row]", None, None])
    # Guard the incoming probe field: a truthy text/visible response without
    # the real measured rect is not evidence of rendered clearance.
    hit = snapshot.get("hit_test")
    assert isinstance(hit, dict), snapshot
    assert isinstance(hit.get("rect"), dict), snapshot
    assert set(("x", "y", "w", "h")) <= set(hit["rect"]), snapshot
    return snapshot


def test_generate_replacement_row_is_owned_above_the_real_capture_bar(
    tmp_path: Path,
) -> None:
    initial = _brief(
        "brief-clearance-before",
        text="Old short waiting row",
        decision=False,
    )
    generated = _brief(
        "brief-clearance-after",
        text=(
            "Review decision: Keep the generated decision readable after the "
            "capture bar wraps at the owner phone width"
        ),
        decision=True,
    )
    needs = _needs_you()
    hub = Hub(tmp_path / "home", token=TOKEN).start()
    try:
        from playwright.sync_api import sync_playwright

        browser_cache = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        if not browser_cache:
            browser_cache = str(Path(pwd.getpwuid(os.getuid()).pw_dir) / "Library/Caches/ms-playwright")
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browser_cache
        with sync_playwright() as play:
            browser = play.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 393, "height": 852})
            page.emulate_media(reduced_motion="reduce")
            calls = {"generate": 0}

            def route_payload(route: Any) -> None:
                path = route.request.url.split("?", 1)[0].rsplit(hub.url, 1)[-1]
                if path == "/api/brief/latest":
                    _fulfill(route, initial)
                elif path == "/api/brief/generate":
                    calls["generate"] += 1
                    _fulfill(route, generated)
                elif path == "/api/desk/needs-you":
                    _fulfill(route, needs)
                elif path == "/api/door":
                    _fulfill(route, {"board": {}, "counts": {}, "upcoming": [], "calendar_configured": False})
                elif path == "/api/inference/assignments":
                    _fulfill(route, {"schema": "InferenceAssignmentSummary@1", "rows": [], "task_overrides": [], "issue_count": 0})
                else:
                    route.fallback()

            page.route("**/api/**", route_payload)
            page.goto(f"{hub.url}/?token={TOKEN}", wait_until="load")
            continue_later = page.get_by_role("button", name="Continue later", exact=True)
            try:
                continue_later.click(timeout=10_000)
            except Exception:  # returning desk: the first-use gate is absent
                pass
            page.get_by_test_id("arrival-capture-bar").wait_for(timeout=10_000)
            page.get_by_test_id("arrival-brief-row").wait_for()
            generate = page.get_by_test_id("arrival-brief-generate")
            generate.wait_for()

            before = _hit_snapshot(page)
            before_bar = page.get_by_test_id("arrival-capture-bar").bounding_box()
            assert before_bar is not None
            # Setup may leave the real Chair at a different scroll position.
            # Place the existing short row two pixels above the measured bar;
            # this is setup positioning, before Generate, never a post-click
            # scroll or a synthetic DOM row.
            page.evaluate(
                """() => {
                  const chair = document.querySelector('[data-testid=chair]');
                  const row = document.querySelector('[data-testid=arrival-brief-row]');
                  const bar = document.querySelector('[data-testid=arrival-capture-bar]');
                  if (!chair || !row || !bar) throw new Error('clearance setup nodes missing');
                  const rowRect = row.getBoundingClientRect();
                  const barRect = bar.getBoundingClientRect();
                  chair.scrollTop += rowRect.bottom - barRect.top + 2;
                }"""
            )
            before = _hit_snapshot(page)
            before_bar = page.get_by_test_id("arrival-capture-bar").bounding_box()
            assert before_bar is not None
            before_rect = before["hit_test"]["rect"]
            assert before_rect["y"] + before_rect["h"] <= before_bar["y"] - 1, before
            generate_box = generate.bounding_box()
            assert generate_box is not None and generate_box["y"] >= 0 and generate_box["y"] + generate_box["height"] <= 852, generate_box

            generate.click()
            page.get_by_text("Review decision: Keep the generated decision readable after the capture bar wraps at the owner phone width", exact=True).wait_for()
            page.wait_for_timeout(100)
            after = _hit_snapshot(page)
            after_bar = page.get_by_test_id("arrival-capture-bar").bounding_box()
            assert after_bar is not None
            assert calls["generate"] == 1
            assert after["text"] == generated["sections"]["decisions"][0]["text"] + "\nAck\nDefer"
            after_rect = after["hit_test"]["rect"]
            print(json.dumps({
                "boundary": "browser API fixture; real built Chair and Generate",
                "before": {"hit_test": before["hit_test"], "clearance": before.get("arrival_clearance")},
                "after": {"hit_test": after["hit_test"], "clearance": after.get("arrival_clearance")},
            }, indent=2))
            # Project the replacement's real rendered height at the old row's
            # position. It must cross the real bar; the final observed row may
            # be higher because the product's success seam clears it.
            assert before_rect["y"] + after_rect["h"] > before_bar["y"], {
                "before": before,
                "after": after,
            }
            assert after_rect["w"] > 0 and after_rect["h"] > 0, after
            assert after["hit_test"]["in_viewport"] is True, after
            assert after["hit_test"]["all_owned"] is True, after
            browser.close()
    finally:
        hub.stop()

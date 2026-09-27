"""PHILO-8-03 (Codex Astra r1, blocking) -- a late follow-up is BLOCKED, never a pass.

Codex Astra showed that an 8.5 s pause after the pending check in
`case.p8.delete_then_leave.gone` made the case PASS on the pre-fix product:
the receipt had already said "Removal committed" before the face click, so
the TIMER produced the DELETE and the 404 that the predicate credits to
leaving the face. The fix: the follow-up declares `requires` (the receipt
pending, Undo offered, at least 2 s left), re-read at delivery.

This fence runs the REAL atlas case through the REAL rig and a real hub, and
injects the same pause in-process (a wrapper around `_ui_step`, test only)
right before the guarded face click. Expected: `blocked`, with the guard named.
Red before the fix: the r1 atlas (no `requires`) and the r1 rig pass it.
Set PHILO8_GUARD_RED=1 to strip the guard and watch it pass (the red leg).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts import graph_walk as gw

pytest.importorskip("playwright.sync_api", reason="the guard fence drives a real page")

REPO = Path(__file__).resolve().parents[2]
ATLAS8 = REPO / "docs/internal/philo/graph/atlas-phase8.json"
CASE = "case.p8.delete_then_leave.gone"
PAUSE_MS = 8_500


@pytest.mark.e2e
@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_a_face_change_after_the_window_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                    width: int) -> None:
    atlas = json.loads(ATLAS8.read_text())
    case = next(c for c in atlas["cases"] if c["id"] == CASE)
    if os.environ.get("PHILO8_GUARD_RED"):
        for step in case["trigger"]["then"]:
            step.pop("requires", None)
    atlas["cases"] = [case]
    path = tmp_path / "atlas-one.json"
    path.write_text(json.dumps(atlas))

    real = gw._ui_step
    state = {"paused": False}

    def late(page, step, hub=None):
        # The face click that must land inside the window: wait it out first.
        if step.get("selector") == "[data-testid=chair-floor-toggle]" and not state["paused"] \
                and page is not None and page.locator(".undo-receipt").count():
            state["paused"] = True
            page.wait_for_timeout(PAUSE_MS)
        return real(page, step, hub)

    monkeypatch.setattr(gw, "_ui_step", late)
    record = gw.run_case(path, CASE, brain="muaddib", viewport=width, out=tmp_path / "runs",
                         engine="none")
    notes = " | ".join(record.get("notes", []))
    print(f"{width}: verdict {record['verdict']}; paused {state['paused']}; {notes[:400]}")
    assert state["paused"], "the pause was never injected (the receipt never showed)"
    assert record["verdict"] == "blocked", (record["verdict"], notes)
    assert "guard" in notes and "did not hold at delivery" in notes, notes

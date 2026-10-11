"""The PHILO-13-06 open-grammar seed (moved out of test_philo13_06_open_glass.py).

The canvas week (test_philo13_11_chair_glass._seed), then the calendar and
Priya's request, all through the real producers on a booted hub. Used by
tests/e2e/test_philo13_07_remembers_glass.py and the open-grammar successor
tests/integration/test_desk_chair.py.
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .test_philo13_11_chair_glass import _seed as _canvas_seed

TOKEN = "philo13-06-open"
COMMITMENT = "Review the rollout plan before Friday"
ONE_ON_ONE = "1:1 Priya / Karol"


def _http(base: str, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        base + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"authorization": f"Bearer {TOKEN}", "content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
    return json.loads(raw) if raw.strip().startswith(("{", "[")) else {}


def _seed(home: Path, base: str) -> dict[str, Any]:
    """The canvas week, then the calendar and Priya's request (real producers)."""
    _canvas_seed(home)
    _http(base, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    people = {r["display_name"]: r["id"] for r in _http(base, "GET", "/api/people/relationships")["relationships"]}
    priya = people["Priya Nair"]
    req = _http(base, "POST", f"/api/people/relationships/{priya}/requests", {"body": COMMITMENT})["request"]
    _http(base, "POST", f"/api/people/requests/{req['id']}/accept", {})

    utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HoldSpeak//PHILO13-06//EN"]
    for uid, starts, mins, title in (
        ("p13-06-1on1", utc + timedelta(minutes=50), 30, ONE_ON_ONE),
        ("p13-06-sync", utc + timedelta(minutes=110), 45, "Ledger cutover sync"),
    ):
        lines += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTART:{starts.strftime('%Y%m%dT%H%M%SZ')}",
                  f"DTEND:{(starts + timedelta(minutes=mins)).strftime('%Y%m%dT%H%M%SZ')}",
                  f"SUMMARY:{title}", "END:VEVENT"]
    lines += ["END:VCALENDAR", ""]
    ics = home / "week.ics"
    ics.write_text("\r\n".join(lines), encoding="utf-8")
    _http(base, "PUT", "/api/settings",
          {"calendar": {"sources": [{"id": "p13-06-week", "label": "Work", "url": str(ics), "enabled": True}]}})
    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
    assert CalendarIngestConductor().refresh() is True
    events = {e["title"]: e for e in _http(base, "GET", "/api/calendar/events")["events"]}
    _http(base, "POST", f"/api/calendar/events/{events['Ledger cutover sync']['id']}/link", {"project_id": "p-ledger"})
    _http(base, "POST", f"/api/people/relationships/{priya}/calendar-links",
          {"uid": "p13-06-1on1", "source_id": "p13-06-week", "label": ONE_ON_ONE})
    brief = _http(base, "POST", "/api/brief/generate", {})
    decisions = [i for i in (brief.get("sections") or {}).get("decisions", []) if i["text"].startswith("Review decision:")]
    assert decisions, "the brief carries a decision to review"
    return {"priya": priya, "decision_row": decisions[0]["text"],
            "decision_title": decisions[0]["text"].split(": ", 1)[1]}

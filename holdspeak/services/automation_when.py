"""Betterment A4 — the When line of an automation, in plain choices.

Three choices (DESIGN §4): a schedule (every day / weekday / week on a day /
hour, at a time), something that happens, or only a press of Run now. A
schedule is stored as cron; the user never sees the cron.

"When something happens" lists only the events the hub can deliver today:
the connector presets whose snapshot adapter runs from the preset alone
(``automation_presets.py``: GitHub). Jira's preset needs a connection
(``site|email``) that the preset does not carry, so it is not offered. No
service event says that a meeting ended (``meeting.auto_intel_enqueued``
fires only when auto-summary is on and an engine is set), so "A meeting
ends" is not offered either.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

from .errors import ValidationError

#: The events the hub can deliver, in the words the When editor shows.
EVENT_WORDS: dict[str, str] = {
    "github-review-requested": "GitHub asks me to review",
    "github-checks-failed": "A pull request's checks fail",
    "github-pr-merged": "A pull request is merged",
}

EVERY = ("day", "weekday", "week", "hour")
_TIME = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def event_choices() -> list[dict[str, Any]]:
    """The events the When editor offers: deliverable presets only."""
    from holdspeak.automation_presets import list_automation_presets

    out = []
    for preset in list_automation_presets():
        words = EVENT_WORDS.get(preset["id"])
        if not words or not preset.get("adapter_ready") or preset.get("connector_id") != "gh":
            continue
        out.append({"id": preset["id"], "words": words, "needs": "repository",
                    "event_pattern": preset["event_pattern"]})
    return out


def cron_for(choice: dict[str, Any]) -> str:
    """A schedule choice as cron. Refuses what the pickers cannot make."""
    every = str(choice.get("every") or "")
    if every not in EVERY:
        raise ValidationError("Choose every day, every weekday, a day of the week or every hour")
    if every == "hour":
        return "0 * * * *"
    match = _TIME.match(str(choice.get("time") or ""))
    if not match:
        raise ValidationError("Choose a time, for example 15:00")
    hour, minute = int(match.group(1)), int(match.group(2))
    if every == "day":
        return f"{minute} {hour} * * *"
    if every == "weekday":
        return f"{minute} {hour} * * 1-5"
    day = choice.get("day")
    if isinstance(day, bool) or not isinstance(day, int) or not 0 <= day <= 6:
        raise ValidationError("Choose a day of the week")
    return f"{minute} {hour} * * {day}"


def next_run_at(cron: Optional[str], enabled: bool) -> Optional[str]:
    """When the schedule fires next (UTC ISO), only while it is on."""
    if not enabled or not str(cron or "").strip():
        return None
    from holdspeak.cron import next_cron_fire
    from holdspeak.timestamps import local_wall

    # The conductor reads cron on the hub's wall clock (cron_is_due), so the
    # scan is on that clock too; a naive candidate's timestamp() is local.
    fire = next_cron_fire(str(cron), after=local_wall())
    if fire is None:
        return None
    return datetime.fromtimestamp(fire, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

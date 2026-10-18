"""Betterment D6: people come from his work.

A read that names the people his work already mentions and People does not
hold yet: meeting speakers and action-item owners, calendar series named
"1:1 with X" (or with one other attendee), and Jira assignees on the issues
his Project watches already read. Nothing here writes; ``PeopleService``
adds a suggestion on the owner's press.

The names come from the plaintext desk (meetings, calendar, watch
snapshots); People content only filters them (a name a Person already has,
a name he hid with "Not a person").
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from .meeting_kind import _ONE_ON_ONE_TITLE, is_one_on_one

#: Words that are never a person's name ("Do it", "Team", "Speaker 2").
_NOT_NAMES = frozenset({
    "a", "all", "an", "and", "anyone", "everybody", "everyone", "group", "i",
    "it", "me", "mic", "n/a", "na", "nobody", "none", "others", "remote",
    "someone", "speaker", "system", "tbd", "team", "the", "them", "they", "to",
    "unassigned", "unknown", "us", "we", "you", "do", "owner", "manager",
    "with", "of", "for", "on", "in", "our", "my", "your", "guest", "host",
})
_NAME_WORD = re.compile(r"^[A-Z][A-Za-z'\-.]*$")
#: Words a 1:1 title adds around the name ("Weekly 1:1 with Mira").
_TITLE_FILLER = frozenset({
    "with", "and", "weekly", "biweekly", "monthly", "sync", "catch", "up",
    "catchup", "check", "in", "checkin", "meeting", "chat", "call", "x",
})
_TITLE_SPLIT = re.compile(r"[\s/<>&|,:+()\[\]\-]+")


def name_like(value: Any) -> str:
    """The cleaned name when ``value`` reads as a person's name, else ``""``.

    One to three words, each a capitalised word of letters, none a common
    word: "Mira", "Mira Okafor" pass; "Do it", "Team", "Speaker 2" do not.
    """
    clean = " ".join(str(value or "").split())
    words = clean.split(" ") if clean else []
    if not 1 <= len(words) <= 3 or len(clean) > 60:
        return ""
    for word in words:
        if not _NAME_WORD.match(word) or word.casefold().strip(".") in _NOT_NAMES:
            return ""
    return clean


def name_from_email(address: Any) -> str:
    """"mira.okafor@x.com" reads "Mira Okafor"; anything else reads ``""``."""
    local = str(address or "").strip().lower().removeprefix("mailto:").split("@", 1)[0]
    parts = [p for p in re.split(r"[._\-]+", local) if p.isalpha()]
    if not 1 <= len(parts) <= 3:
        return ""
    return name_like(" ".join(p.capitalize() for p in parts))


def name_from_one_on_one_title(title: str, is_self: Callable[[str], bool]) -> str:
    """"1:1 with Mira", "Mira / Karol 1:1", "Mira <> Karol" read "Mira"."""
    rest = _ONE_ON_ONE_TITLE.sub(" ", str(title or ""))
    words = [w for w in _TITLE_SPLIT.split(rest) if w and w.casefold() not in _TITLE_FILLER]
    words = [w for w in words if not is_self(w)]
    return name_like(" ".join(words))


@dataclass
class _Suggestion:
    name: str
    said: set[str] = field(default_factory=set)
    meetings: dict[str, tuple[str, str]] = field(default_factory=dict)  # id -> (title, started_at)
    promises: int = 0
    one_on_one: bool = False
    series: dict[str, str] | None = None
    jira: bool = False


def _key(name: str) -> str:
    return " ".join(name.split()).casefold()


def collect(
    db: Any,
    *,
    is_self: Callable[[str], bool],
    is_known: Callable[[str], bool],
    hidden: Iterable[str],
    now_iso: str,
) -> list[dict[str, Any]]:
    """The suggestions, best first. ``is_known``: a Person already has the name."""
    hidden_keys = {_key(h) for h in hidden if str(h).strip()}
    found: dict[str, _Suggestion] = {}

    def keep(raw: Any) -> _Suggestion | None:
        name = name_like(raw)
        if not name or is_self(name) or is_known(name):
            return None
        key = _key(name)
        if key in hidden_keys:
            return None
        if key not in found:
            found[key] = _Suggestion(name=name)
        found[key].said.add(name)
        return found[key]

    with db._connection() as conn:
        meetings = {
            str(row["id"]): row for row in conn.execute(
                "SELECT id, title, started_at, mic_label, remote_label FROM meetings WHERE COALESCE(parked, 0) = 0",
            )
        }
        speakers: dict[str, set[str]] = {}
        for row in conn.execute("SELECT DISTINCT meeting_id, speaker FROM segments"):
            meeting = meetings.get(str(row["meeting_id"]))
            speaker = " ".join(str(row["speaker"] or "").split())
            if meeting is None or not speaker:
                continue
            if speaker.casefold() in {str(meeting["mic_label"] or "").casefold(), str(meeting["remote_label"] or "").casefold()}:
                continue
            speakers.setdefault(str(row["meeting_id"]), set()).add(speaker)
        owners = conn.execute(
            """SELECT owner, meeting_id, status FROM action_items
                WHERE TRIM(COALESCE(owner, '')) <> ''
                  AND COALESCE(review_state, '') <> 'dismissed'""",
        ).fetchall()
        calendar = conn.execute(
            """SELECT uid, source_id, source_label, title, starts_at, attendees_json
                 FROM calendar_events ORDER BY starts_at, id""",
        ).fetchall()
        watches = conn.execute(
            """SELECT snapshot_json FROM connector_watches
                WHERE connector_id = 'jira' AND query_kind = 'issues'
                  AND COALESCE(enabled, 1) = 1 AND snapshot_json IS NOT NULL""",
        ).fetchall()

    # Meetings: who spoke and who was given a promise.
    for meeting_id, names in speakers.items():
        meeting = meetings[meeting_id]
        others = [n for n in names if not is_self(n)]
        one_on_one = is_one_on_one(meeting["title"], names | {"Me"}, others) if len(others) == 1 else False
        for name in names:
            found_row = keep(name)
            if found_row is None:
                continue
            found_row.meetings[meeting_id] = (str(meeting["title"] or ""), str(meeting["started_at"] or ""))
            found_row.one_on_one = found_row.one_on_one or one_on_one
    for row in owners:
        meeting = meetings.get(str(row["meeting_id"] or ""))
        if row["meeting_id"] and meeting is None:
            continue  # a parked meeting's promise
        found_row = keep(row["owner"])
        if found_row is None:
            continue
        if meeting is not None:
            found_row.meetings[str(row["meeting_id"])] = (str(meeting["title"] or ""), str(meeting["started_at"] or ""))
        if str(row["status"] or "") not in {"done", "dismissed", "completed"}:
            found_row.promises += 1

    # Calendar: a series named "1:1 with X", or with one other attendee.
    series: dict[tuple[str, str], dict[str, Any]] = {}
    for row in calendar:
        ident = (str(row["uid"]), str(row["source_id"] or ""))
        entry = series.setdefault(ident, {"title": str(row["title"] or ""), "label": str(row["source_label"] or ""),
                                          "next": "", "attendees": []})
        if not entry["next"] and str(row["starts_at"]) >= now_iso:
            entry["next"] = str(row["starts_at"])
        try:
            entry["attendees"] = [str(a) for a in json.loads(row["attendees_json"] or "[]")]
        except (TypeError, ValueError):
            pass
    for (uid, source_id), entry in series.items():
        others = [a for a in entry["attendees"] if not is_self(name_from_email(a))]
        from_mail = [name_from_email(a) for a in others]
        titled = name_from_one_on_one_title(entry["title"], is_self) if _ONE_ON_ONE_TITLE.search(entry["title"]) else ""
        name = ""
        if titled:
            # The calendar knows the full name when one attendee's starts with it.
            full = [n for n in from_mail if n and _key(n).split(" ")[0] == _key(titled).split(" ")[0]]
            name = full[0] if len(full) == 1 and len(full[0].split()) > len(titled.split()) else titled
        elif len(others) == 1 and from_mail[0]:
            name = from_mail[0]
        if not name:
            continue
        found_row = keep(name)
        if found_row is None:
            # A spoken first name may already be a suggestion: the series joins it.
            continue
        if titled and _key(titled) != _key(name):
            found_row.said.add(titled)
        found_row.one_on_one = True
        if found_row.series is None:
            found_row.series = {"uid": uid, "source_id": source_id, "label": entry["title"],
                                "source_label": entry["label"], "next_starts_at": entry["next"]}

    # Jira: assignees on the issues his watches read.
    for row in watches:
        try:
            snapshot = json.loads(row["snapshot_json"])
        except (TypeError, ValueError):
            continue
        entities = snapshot.get("entities") if isinstance(snapshot, dict) else None
        values = entities.values() if isinstance(entities, dict) else entities if isinstance(entities, list) else []
        for entity in values:
            if isinstance(entity, dict):
                found_row = keep(entity.get("assignee"))
                if found_row is not None:
                    found_row.jira = True

    _merge_first_names(found)
    out = [_view(key, row) for key, row in found.items()]
    out.sort(key=lambda s: (not s["series"], not s["one_on_one"], -s["promise_count"], -s["meeting_count"], s["name"].casefold()))
    return out


def _merge_first_names(found: dict[str, _Suggestion]) -> None:
    """"Mira" (said) and "Mira Okafor" (calendar or Jira) are one person when
    exactly one full name starts with that first name."""
    for key in [k for k in found if " " not in k]:
        fuller = [k for k in found if " " in k and k.split(" ")[0] == key]
        if len(fuller) != 1:
            continue
        into, row = found[fuller[0]], found.pop(key)
        into.said |= row.said
        into.meetings.update(row.meetings)
        into.promises += row.promises
        into.one_on_one = into.one_on_one or row.one_on_one
        into.series = into.series or row.series
        into.jira = into.jira or row.jira


def _view(key: str, row: _Suggestion) -> dict[str, Any]:
    newest = sorted(row.meetings.items(), key=lambda item: item[1][1], reverse=True)
    said = sorted((s for s in row.said if _key(s) != key), key=len)
    if row.series:
        source = "1:1 series"
    elif newest:
        source = "meeting"
    else:
        source = "jira"
    return {
        "key": key,
        "name": row.name,
        "said": said[0] if said else "",
        "relationship_kind": "direct_report" if row.one_on_one else "peer",
        "source": source,
        "one_on_one": row.one_on_one,
        "series": row.series,
        "jira": row.jira,
        "meeting_count": len(row.meetings),
        "promise_count": row.promises,
        "meetings": [{"id": mid, "title": title, "started_at": at} for mid, (title, at) in newest[:3]],
    }

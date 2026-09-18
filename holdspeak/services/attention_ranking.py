"""HS-200-15 -- the attention ranking and the dedup (pure functions).

The settled design (D2(b), ruling N1; the owner's verdict Q1) fixes the
ranking key for every attention row on the arrival:

    | Rank | Class          | Ordered within the class by         |
    |------|----------------|-------------------------------------|
    | 1    | overdue        | most overdue first                  |
    | 2    | due_today      | earliest due time first             |
    | 3    | not_run        | oldest meeting first                |
    | 4    | no_due_date    | most recently changed first         |
    | 5    | waiting        | longest waiting first               |
    | --   | tie-break      | the stable item id                  |

Severity is NOT a sort key: it rides the row's reason token in its own
ink and never reorders a class, so a failing source cannot lower a
known item by disappearing (C4).  Every key is an OBSERVABLE fact --
a due date, an observation time, a stable id -- never a model score
(story 15 "Out: opaque model-only priority ranking").

The dedup key (AC3): one obligation projected by a Watch, a meeting
and a person is ONE row whose constituent projections stay traceable
in ``sources``.  Two projections are one obligation ONLY when they come
from DIFFERENT sources, name the same Project and the same thing (the
title, normalised: case, spacing, a leading issue key or PR number
stripped), and their refs agree -- the leading ``KAN-7`` / ``#612`` --
or one side carries no ref (a meeting's proposal names no key).  Two
projections that share a SOURCE and carry distinct refs are never one
obligation: ``KAN-7 Rotate the staging credentials`` and ``KAN-12
Rotate the staging credentials`` are two tickets (counsel P0-1).

Both functions are deterministic: the same input, in any order, yields
the same output, byte for byte.
"""
from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any, Iterable

#: The closed class vocabulary, in rank order.
RANK_CLASSES: tuple[str, ...] = (
    "overdue", "due_today", "not_run", "no_due_date", "waiting",
)
_RANK = {name: index for index, name in enumerate(RANK_CLASSES)}

_SEVERITY_ORDER = {"danger": 0, "warning": 1, "info": 2}

# A leading issue key (``KAN-7``), PR number (``#612``) or bare ticket
# number, then the rest of the title.
_LEADING_REF = re.compile(r"^(?:#\d+|[A-Z][A-Z0-9]+-\d+)\s+")
_WS = re.compile(r"\s+")


# ── time helpers ──────────────────────────────────────────────────────


def _parse_stamp(value: Any) -> datetime | None:
    """An ISO stamp (date or datetime) as a naive local datetime; None when
    the value is not a time (an unknown time makes no claim)."""
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _epoch(value: Any) -> float:
    """Seconds for an ISO stamp; +inf when unknown so it sorts LAST in
    every class (an unknown time is never promoted)."""
    parsed = _parse_stamp(value)
    return parsed.timestamp() if parsed is not None else math.inf


def _observed_since(item: dict[str, Any]) -> Any:
    """The item's own observation/change time.  The aggregate carries the
    Room's ``since`` as ``ageToken`` (an ISO stamp, not a token) and, from
    HS-200-15, as ``since`` too."""
    return item.get("since") or item.get("ageToken") or item.get("observedAt")


# ── classification ───────────────────────────────────────────────────


def classify(item: dict[str, Any], now: datetime) -> str:
    """The rank class of one attention row, from observable facts only.

    A known due date decides first (overdue / due today / waiting); then
    the reason token's head word; anything else has no due date.
    """
    due = _parse_stamp(item.get("dueAt") or item.get("due_at"))
    if due is not None:
        if due.date() < now.date():
            return "overdue"
        if due.date() == now.date():
            return "due_today"
        return "waiting"
    why = str(item.get("why") or "").strip().upper()
    if why.startswith("OVERDUE"):
        return "overdue"
    if why.startswith("DUE TODAY"):
        return "due_today"
    if why.startswith("NOT RUN") or item.get("kind") == "intel_not_run":
        return "not_run"
    if why.startswith("WAITING"):
        return "waiting"
    return "no_due_date"


def _within_class_key(rank_class: str, item: dict[str, Any]) -> float:
    due = item.get("dueAt") or item.get("due_at")
    since = _observed_since(item)
    if rank_class == "overdue":
        # Most overdue first: the earliest due date; a Watch that only
        # knows the overdue-since stamp uses that.
        return _epoch(due if due else since)
    if rank_class == "due_today":
        return _epoch(due)
    if rank_class == "not_run":
        return _epoch(since)
    if rank_class == "no_due_date":
        # Most recently changed first.
        stamp = _epoch(since)
        return -stamp if stamp != math.inf else math.inf
    # waiting: longest waiting first.
    return _epoch(since if since else due)


def sort_key(item: dict[str, Any], now: datetime) -> tuple[int, float, str]:
    """The complete, deterministic ranking key for one row."""
    rank_class = str(item.get("rankClass") or classify(item, now))
    if rank_class not in _RANK:
        rank_class = classify(item, now)
    return (
        _RANK[rank_class],
        _within_class_key(rank_class, item),
        str(item.get("id") or ""),
    )


def rank_items(
    items: Iterable[dict[str, Any]], now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Rank attention rows.  Returns NEW dicts, each stamped with its
    ``rankClass`` and 1-based ``rank``; the input is not mutated."""
    clock_now = now or datetime.now()
    out: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        row["rankClass"] = classify(row, clock_now)
        out.append(row)
    out.sort(key=lambda row: sort_key(row, clock_now))
    for position, row in enumerate(out, start=1):
        row["rank"] = position
    return out


# ── dedup ────────────────────────────────────────────────────────────


def normalize_title(title: Any) -> str:
    """The comparable form of a title: lower-cased, whitespace collapsed,
    a leading issue key / PR number dropped.  ``str.lower`` (not
    ``casefold``) so it mirrors JavaScript's ``toLowerCase`` byte for byte
    (``Straße`` stays ``straße`` on both sides)."""
    text = _WS.sub(" ", str(title or "").strip())
    text = _LEADING_REF.sub("", text)
    return text.lower()


def projection_ref(item: dict[str, Any]) -> str:
    """The projection's own ref: the leading issue key / PR number of its
    title (``KAN-7``, ``#612``), or "" when it has none."""
    text = _WS.sub(" ", str(item.get("title") or "").strip())
    match = _LEADING_REF.match(text)
    return match.group(0).strip().upper() if match else ""


def _may_merge(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Two projections may be one obligation only ACROSS sources, with
    agreeing refs or one side without a ref."""
    if str(a.get("source") or "") == str(b.get("source") or ""):
        return False
    ra, rb = projection_ref(a), projection_ref(b)
    return not ra or not rb or ra == rb


def _clusters(group: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Partition one (project, title) group into obligations.  Greedy and
    order-stable: a row joins the first cluster every member of which it
    may merge with, else starts its own."""
    out: list[list[dict[str, Any]]] = []
    for row in group:
        for cluster in out:
            if all(_may_merge(row, member) for member in cluster):
                cluster.append(row)
                break
        else:
            out.append([row])
    return out


def _projection(item: dict[str, Any]) -> dict[str, Any]:
    """One constituent projection of a merged row, for the disclosure."""
    return {
        "id": item.get("id"),
        "source": item.get("source", ""),
        "title": item.get("title", ""),
        "why": item.get("why", ""),
        "severity": item.get("severity", "info"),
        "fromLastObservation": bool(item.get("fromLastObservation")),
        "observedAt": item.get("observedAt"),
        "verbHref": item.get("verbHref"),
    }


def _head_key(item: dict[str, Any], now: datetime) -> tuple[int, float, int, str]:
    rank, within, ident = sort_key(item, now)
    return (rank, within, _SEVERITY_ORDER.get(str(item.get("severity", "info")), 2), ident)


def _merge(group: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
    ordered = sorted(group, key=lambda row: _head_key(row, now))
    head = dict(ordered[0])
    head["sources"] = [_projection(row) for row in ordered]
    head["dedupCount"] = len(ordered)
    # The most severe projection colours the row.
    head["severity"] = min(
        (str(row.get("severity", "info")) for row in ordered),
        key=lambda sev: _SEVERITY_ORDER.get(sev, 2),
    )
    # A merged row is remembered only when EVERY projection is; one fresh
    # observation of the obligation is an observation of the obligation.
    remembered = [row for row in ordered if row.get("fromLastObservation")]
    if len(remembered) == len(ordered):
        head["fromLastObservation"] = True
        head["observedAt"] = max(
            (str(row.get("observedAt") or "") for row in remembered), default=None,
        ) or None
    else:
        head.pop("fromLastObservation", None)
        head.pop("observedAt", None)
    return head


def dedup_items(
    items: Iterable[dict[str, Any]], now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Collapse duplicate projections of one obligation into ONE row.

    Every returned row carries ``sources`` (its constituent projections,
    most urgent first) and ``dedupCount``.  Rows that share a normalised
    title and a Project merge only across sources with agreeing (or
    absent) refs -- see ``_may_merge``; a projection with NO Project (a
    Door card) joins the one Project that names the same thing, and
    stands alone when several do.  The input is not mutated and the
    output order is the input order of each group's first member.
    """
    clock_now = now or datetime.now()
    rows = [dict(item) for item in items]
    by_title: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for row in rows:
        key = normalize_title(row.get("title"))
        if key not in by_title:
            by_title[key] = []
            order.append(key)
        by_title[key].append(row)

    out: list[dict[str, Any]] = []
    for key in order:
        group = by_title[key]
        if not key:
            # An untitled row is nobody's duplicate.
            for row in group:
                out.append(_merge([row], clock_now))
            continue
        with_project: dict[str, list[dict[str, Any]]] = {}
        project_order: list[str] = []
        orphans: list[dict[str, Any]] = []
        for row in group:
            pid = str(row.get("projectId") or "")
            if not pid:
                orphans.append(row)
                continue
            if pid not in with_project:
                with_project[pid] = []
                project_order.append(pid)
            with_project[pid].append(row)
        if len(project_order) == 1 and orphans:
            with_project[project_order[0]].extend(orphans)
            orphans = []
        for pid in project_order:
            for cluster in _clusters(with_project[pid]):
                out.append(_merge(cluster, clock_now))
        if orphans:
            if len(project_order) == 0:
                for cluster in _clusters(orphans):
                    out.append(_merge(cluster, clock_now))
            else:
                for row in orphans:
                    out.append(_merge([row], clock_now))
    return out


def rank_and_dedup(
    items: Iterable[dict[str, Any]], now: datetime | None = None,
) -> list[dict[str, Any]]:
    """The one call the aggregate makes: dedup, then rank."""
    clock_now = now or datetime.now()
    return rank_items(dedup_items(items, clock_now), clock_now)


__all__ = [
    "RANK_CLASSES",
    "classify",
    "sort_key",
    "rank_items",
    "normalize_title",
    "projection_ref",
    "dedup_items",
    "rank_and_dedup",
]

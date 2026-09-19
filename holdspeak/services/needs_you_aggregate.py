"""Cached needs-you aggregate (HS-171-03).

Moves the N+1 aggregation out of the route into a pure function
(``build_aggregate``) and wraps it in a stale-while-refresh cache
(``cached_aggregate``).  The cadence sweep calls ``invalidate`` after
each tick; the route reads ``cached_aggregate`` which is O(1) on a warm
cache.

The sibling HeartbeatService (holdspeak/services/heartbeat_service.py)
can call ``build_aggregate`` or ``cached_aggregate`` directly -- this
module is the SINGLE owner of the aggregate shape.

HS-200-07 (C4) -- coverage and partial results
----------------------------------------------
The aggregate carries one COVERAGE RECORD for every expected source, so
an empty result can never be read as an all-clear when a source was not
observed:

  ``coverage`` -- a list of
      ``{source_id, kind, state, observed_at, repair, reason, label,
         project_id}``
      with ``kind`` in ``project | watch | meeting | commitment`` and
      ``state`` in ``available | stale | failed | forbidden |
      unavailable``.
  ``complete`` -- True only when EVERY expected source is ``available``.
  ``computedAt`` -- when the AGGREGATE was computed; it says nothing
      about any source's freshness (each record carries its own
      ``observed_at``).

A failed source does not drop its items: the builder remembers the last
successful observation per source (``LastKnownStore`` -- the aggregate's
own memory, NOT a second attention store; HS-200-13 made it durable in
``needs_you_last_known`` so a hub restart still replays what a failed
source last said) and replays
those items marked ``fromLastObservation`` with the ``observedAt`` of
that observation, so a severity can never fall by disappearance.  When
the source recovers, the fresh items replace the remembered ones by
their stable ``id``.

HS-200-15 -- ranking, dedup, and the wire fields they read
----------------------------------------------------------
Every row carries ``since`` (the Room's change stamp), ``dueAt`` (when
the source knows one), ``rankClass`` (``overdue | due_today | not_run |
no_due_date | waiting``), ``rank`` (1-based), ``sources`` (the
constituent projections, most urgent first) and ``dedupCount``.  The
pure functions live in ``attention_ranking.py``; ``items`` is returned
in rank order.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable

from .attention_ranking import rank_and_dedup

log = logging.getLogger(__name__)

_SEVERITY_ORDER = {"danger": 0, "warning": 1, "info": 2}

# ── C4 coverage vocabulary ───────────────────────────────────────────

COVERAGE_STATES = ("available", "stale", "failed", "forbidden", "unavailable")
COVERAGE_KINDS = ("project", "watch", "meeting", "commitment")

#: A live source whose last successful check is older than this is
#: reported ``stale`` -- observed once, but not recently enough to
#: stand for "available now".
DEFAULT_SOURCE_STALE_AFTER_S = 6 * 3600.0

#: The room sections the aggregate depends on, by coverage kind.  The
#: Room computes them all on one read, so this costs no extra query.
_SECTION_KINDS = (("meetings", "meeting"), ("commitments", "commitment"))


def _repair(state: str, kind: str, project_id: str, reason: str | None) -> dict[str, Any]:
    """The repair path for a coverage record: a token + the owning verb.

    ``href`` is the owning ROUTE (never an API path); the face maps the
    verb to its own action (Retry re-reads the aggregate fresh).
    """
    room_href = f"/projects/{project_id}" if project_id else "/projects"
    if state == "forbidden":
        return {"token": "FORBIDDEN", "verb": "Open source", "href": room_href}
    if kind == "watch":
        if state == "failed":
            return {"token": "CANT CHECK", "verb": "Reconnect", "href": "/settings"}
        if state == "stale":
            return {"token": "STALE", "verb": "Retry", "href": room_href}
        return {
            "token": "PAUSED" if reason == "paused" else "NEVER CHECKED",
            "verb": "Open source",
            "href": room_href,
        }
    if state == "stale":
        return {"token": "STALE", "verb": "Retry", "href": room_href}
    if state == "unavailable":
        return {"token": "NOT OBSERVED", "verb": "Retry", "href": room_href}
    return {"token": "READ FAILED", "verb": "Retry", "href": room_href}


def _coverage_row(
    *,
    source_id: str,
    kind: str,
    state: str,
    observed_at: str | None,
    label: str,
    project_id: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """One coverage record.  ``available`` rows carry no repair path."""
    row: dict[str, Any] = {
        "source_id": source_id,
        "kind": kind,
        "state": state,
        "observed_at": observed_at,
        "label": label,
        "project_id": project_id,
        "reason": reason,
        "repair": None,
    }
    if state != "available":
        row["repair"] = _repair(state, kind, project_id, reason)
    return row


def _classify_read_failure(exc: BaseException) -> tuple[str, str]:
    """Map a Room read failure to (coverage state, reason).

    Authority refusals are ``forbidden`` (nothing to retry); a missing
    Room is ``unavailable``; everything else is ``failed``.
    """
    name = type(exc).__name__.lower()
    text = f"{name} {exc}".lower()
    if isinstance(exc, PermissionError) or any(
        word in text for word in ("forbidden", "permission", "not authorized",
                                  "unauthorized", "denied")
    ):
        return "forbidden", "not permitted"
    if "notfound" in name or "does not exist" in text:
        return "unavailable", "not found"
    return "failed", (str(exc).split("\n")[0][:200] or type(exc).__name__)


def _item_id(project_id: str, item: dict[str, Any]) -> str:
    """A stable id for one attention row, for dedup and reconciliation.

    A proposal is identified by its own durable id; every other row by
    (project, source, ref) -- the same triple the Room derives it from.
    """
    if item.get("proposalId"):
        return f"proposal:{item['proposalId']}"
    return f"{project_id}:{item.get('source', '')}:{item.get('ref', '')}"


#: A remembered observation older than this is not replayed: a source that
#: has not been read for two weeks is stated as unobserved (coverage names
#: it), never replayed as a fortnight-old "still true" (counsel P1-4).
REPLAY_HORIZON_DAYS = 14


class LastKnownStore:
    """Per-source memory of the last SUCCESSFUL observation.

    Thread-safe.  It is the aggregate's own memory, not a second attention
    store.  HS-200-15 left it process-local; HS-200-13 (AC5) gives it an
    optional ``db_factory``: every ``remember`` writes through to
    ``needs_you_last_known`` and a cold ``recall`` reads the row back, so a
    hub restart replays what a failed source last said instead of forgetting
    it (coverage still names the failure either way -- the result is never
    read as an all-clear).  Without a factory it behaves exactly as before.

    Three bounds (counsel-on-built P1-4): ``recall`` returns nothing for an
    observation older than ``REPLAY_HORIZON_DAYS``; ``forget_except`` drops
    the sources a successful project read no longer lists (archived,
    unlinked); and a recall re-reads the durable row when it is newer than
    the in-memory copy, so several stores over one database agree.  The
    process shares ONE store: ``shared_last_known`` (below) returns the
    composition root's, else the module default, bound to the database.
    """

    def __init__(self, db_factory: Callable[[], Any] | None = None) -> None:
        self._lock = threading.Lock()
        self._by_source: dict[str, dict[str, Any]] = {}
        self._db_factory = db_factory

    def bind(self, db_factory: Callable[[], Any]) -> "LastKnownStore":
        """Attach the database this store writes through (once)."""
        if self._db_factory is None:
            self._db_factory = db_factory
        return self

    @property
    def durable(self) -> bool:
        return self._db_factory is not None

    def forget_except(self, keep: set[str], *, prefix: str = "project:") -> int:
        """Drop remembered sources under ``prefix`` that are not in ``keep``
        (the set a SUCCESSFUL project read just produced).  Returns how many."""
        dropped = 0
        with self._lock:
            for source_id in [k for k in self._by_source if k.startswith(prefix) and k not in keep]:
                del self._by_source[source_id]
                dropped += 1
        if self._db_factory is not None:
            try:
                db = self._db_factory()
                with db._connection() as conn:
                    rows = conn.execute(
                        "SELECT source_id FROM needs_you_last_known WHERE source_id LIKE ?",
                        (prefix + "%",),
                    ).fetchall()
                    stale = [str(r["source_id"]) for r in rows if str(r["source_id"]) not in keep]
                    for source_id in stale:
                        conn.execute("DELETE FROM needs_you_last_known WHERE source_id = ?", (source_id,))
                    dropped = max(dropped, len(stale))
            except Exception as exc:
                log.warning("needs-you: last-known prune failed: %s", exc)
        return dropped

    def remember(self, source_id: str, *, items: list[dict[str, Any]],
                 observed_at: str, label: str = "", project_id: str = "") -> None:
        with self._lock:
            self._by_source[source_id] = {
                "items": [dict(row) for row in items],
                "observed_at": observed_at,
                "label": label,
                "project_id": project_id,
            }
        if self._db_factory is None:
            return
        try:
            db = self._db_factory()
            with db._connection() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO needs_you_last_known
                       (source_id, project_id, label, observed_at, items_json, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (source_id, project_id or "", label or "", observed_at,
                     json.dumps(items, sort_keys=True, default=str),
                     datetime.now().isoformat()),
                )
        except Exception as exc:  # the durable copy is belt, never the loop
            log.warning("needs-you: last-known write failed for %s: %s", source_id, exc)

    def _read_durable(self, source_id: str, *, replace: bool = False) -> dict[str, Any] | None:
        if self._db_factory is None:
            return None
        try:
            db = self._db_factory()
            with db._connection() as conn:
                row = conn.execute(
                    "SELECT * FROM needs_you_last_known WHERE source_id = ?", (source_id,)
                ).fetchone()
        except Exception as exc:
            log.warning("needs-you: last-known read failed for %s: %s", source_id, exc)
            return None
        if row is None:
            return None
        try:
            items = json.loads(row["items_json"] or "[]")
        except (TypeError, ValueError):
            items = []
        entry = {
            "items": [dict(r) for r in items if isinstance(r, dict)],
            "observed_at": str(row["observed_at"]),
            "label": str(row["label"] or ""),
            "project_id": str(row["project_id"] or ""),
        }
        with self._lock:
            if replace:
                held = self._by_source.get(source_id)
                if held is None or str(entry["observed_at"]) > str(held["observed_at"]):
                    self._by_source[source_id] = entry
            else:
                self._by_source.setdefault(source_id, entry)
        return entry

    def recall(self, source_id: str, *, now: datetime | None = None) -> dict[str, Any] | None:
        with self._lock:
            entry = self._by_source.get(source_id)
        if self._db_factory is not None:
            # Another store over the same database may have observed since
            # (the hub's cache, the heartbeat, the sidecar): the newer row wins.
            durable = self._read_durable(source_id, replace=True)
            if durable is not None and (
                entry is None or str(durable["observed_at"]) > str(entry["observed_at"])
            ):
                entry = durable
        if entry is None:
            return None
        horizon = (now or datetime.now()) - timedelta(days=REPLAY_HORIZON_DAYS)
        if _older_than(str(entry["observed_at"]), horizon):
            return None
        return {
            "items": [dict(row) for row in entry["items"]],
            "observed_at": entry["observed_at"],
            "label": entry["label"],
            "project_id": entry["project_id"],
        }

    def source_ids(self) -> list[str]:
        with self._lock:
            ids = set(self._by_source)
        if self._db_factory is not None:
            try:
                db = self._db_factory()
                with db._connection() as conn:
                    ids.update(
                        str(r["source_id"]) for r in
                        conn.execute("SELECT source_id FROM needs_you_last_known").fetchall()
                    )
            except Exception as exc:
                log.warning("needs-you: last-known listing failed: %s", exc)
        return sorted(ids)

    def clear(self) -> None:
        with self._lock:
            self._by_source.clear()
        if self._db_factory is not None:
            try:
                db = self._db_factory()
                with db._connection() as conn:
                    conn.execute("DELETE FROM needs_you_last_known")
            except Exception as exc:
                log.warning("needs-you: last-known clear failed: %s", exc)


#: The default store the live runtime uses.
_LAST_KNOWN = LastKnownStore()


def last_known_store() -> LastKnownStore:
    """The process-wide last-known store (tests may clear it)."""
    return _LAST_KNOWN


def shared_last_known(db_factory: Callable[[], Any] | None = None) -> LastKnownStore:
    """ONE durable store per process (counsel P1-4).

    The composition root (HS-200-45 ``RuntimeServices.needs_you_last_known``)
    carries it when a hub installed one; otherwise the module default is
    used.  Either way the store is bound to ``db_factory`` on first use, so
    the arrival route, the heartbeat and the MCP sidecar replay the same
    memory and prune it together.
    """
    store: LastKnownStore | None = None
    try:
        from holdspeak.runtime import composition as _composition
        root = _composition.installed()
        if root is not None:
            store = getattr(root, "needs_you_last_known", None)
            if store is None and not getattr(root, "bare_root", True):
                store = _LAST_KNOWN
                root.needs_you_last_known = store
    except Exception:  # pragma: no cover - the root is optional here
        store = None
    if store is None:
        store = _LAST_KNOWN
    if db_factory is not None:
        store.bind(db_factory)
    return store


# ── Pure aggregate builder (the N+1 lives here, nowhere else) ─────────


def build_aggregate(
    *,
    list_projects: Callable[..., list[dict[str, Any]]],
    room: Callable[..., dict[str, Any]],
    principal: Any,
    door_upcoming: Callable[..., list[dict[str, Any]]] | None = None,
    now: datetime | None = None,
    last_known: LastKnownStore | None = None,
    source_stale_after_s: float = DEFAULT_SOURCE_STALE_AFTER_S,
) -> dict[str, Any]:
    """Build the full needs-you payload.

    Parameters mirror the dependencies the route used to close over:
    ``list_projects`` and ``room`` come from ProjectService;
    ``door_upcoming`` from DoorService._upcoming (optional).

    Returns the SAME shape the route returned before, plus ``computedAt``
    and (HS-200-07) ``coverage`` + ``complete``.  ``now`` is injectable so
    source staleness is deterministic under test.
    """
    clock_now = now or datetime.now()
    memory = last_known if last_known is not None else _LAST_KNOWN
    items: list[dict[str, Any]] = []
    project_ids: set[str] = set()
    coverage: list[dict[str, Any]] = []
    carried: list[dict[str, Any]] = []

    try:
        projects = list_projects(principal, {"include_archived": False})
        project_list_failed = False
    except Exception as exc:
        # The expected-source set itself could not be read.  Every source
        # remembered from an earlier build is reported as not observed and
        # replays its last-known items; nothing here can read as complete.
        log.warning("needs-you: project list unavailable: %s", exc)
        projects = []
        project_list_failed = True
        state, reason = _classify_read_failure(exc)
        coverage.append(_coverage_row(
            source_id="projects", kind="project", state=state,
            observed_at=None, label="Projects", project_id="", reason=reason,
        ))

    seen_projects: set[str] = set()
    for proj in projects:
        pid = proj.get("id") or ""
        if not pid:
            continue
        seen_projects.add(pid)
        pname = proj.get("name") or proj.get("title") or ""
        source_id = f"project:{pid}"
        try:
            rm = room(principal, pid)
        except Exception as exc:
            state, reason = _classify_read_failure(exc)
            remembered = memory.recall(source_id, now=clock_now)
            coverage.append(_coverage_row(
                source_id=source_id, kind="project", state=state,
                observed_at=(remembered or {}).get("observed_at"),
                label=pname, project_id=pid, reason=reason,
            ))
            carried.extend(_carry(remembered))
            continue

        needs = rm.get("needsYou", {})
        if needs.get("state") != "ok":
            remembered = memory.recall(source_id, now=clock_now)
            coverage.append(_coverage_row(
                source_id=source_id, kind="project", state="failed",
                observed_at=(remembered or {}).get("observed_at"),
                label=pname, project_id=pid,
                reason=str(needs.get("error_code") or "needs_you_read_failed"),
            ))
            carried.extend(_carry(remembered))
            coverage.extend(room_coverage(
                rm, pid, pname, now=clock_now,
                stale_after_s=source_stale_after_s,
            ))
            continue

        observed_at = str(rm.get("observed_at") or clock_now.isoformat())
        fresh: list[dict[str, Any]] = []
        for item in needs.get("items") or []:
            row: dict[str, Any] = {
                "projectId": pid,
                "projectName": pname,
                "ref": item.get("title", ""),
                "title": item.get("title", ""),
                "why": item.get("why", ""),
                "ageToken": item.get("since", ""),
                # HS-200-15: the observable facts the ranking reads --
                # the Room's own change/observation stamp and, where the
                # source knows one, the due date.
                "since": item.get("since", ""),
                "dueAt": item.get("due_at") or item.get("dueAt"),
                "kind": item.get("kind"),
                "source": item.get("source", ""),
                "verbHref": item.get("url") or item.get("verbHref"),
                "severity": item.get("severity", "info"),
            }
            # HS-200-13 (AC3): a commitment row carries what its verbs need
            # -- the action item the verb writes to, the typed unknowns, and
            # the ONE lawful next action the producer chose.
            if item.get("commitment_id"):
                row["commitmentId"] = item["commitment_id"]
                row["actionItemId"] = item.get("action_item_id")
                row["owner"] = item.get("owner")
                row["unknowns"] = list(item.get("unknowns") or [])
                row["nextAction"] = item.get("next_action")
                row["decisionRecordId"] = item.get("decision_record_id")
            if item.get("proposal_id"):
                row["proposalId"] = item["proposal_id"]
                row["proposalKind"] = item.get("proposal_kind", "action")
                row["proposalHost"] = item.get("host")
                row["proposalDue"] = item.get("due_hint")
                row["meetingTitle"] = item.get("meeting_title")
            row["id"] = _item_id(pid, row)
            fresh.append(row)
            project_ids.add(pid)
        items.extend(fresh)
        # The recovery seam: this observation replaces what the source
        # last said, so a recovered Room reconciles by stable id.
        memory.remember(source_id, items=fresh, observed_at=observed_at,
                        label=pname, project_id=pid)
        coverage.append(_coverage_row(
            source_id=source_id, kind="project", state="available",
            observed_at=observed_at, label=pname, project_id=pid,
        ))
        coverage.extend(room_coverage(
            rm, pid, pname, now=clock_now, stale_after_s=source_stale_after_s,
        ))

    if not project_list_failed:
        # The project list is the expected-source set: a source it no longer
        # names (archived, deleted) is forgotten, so a later list failure
        # cannot replay a ghost (counsel P1-4).
        memory.forget_except({f"project:{pid}" for pid in seen_projects})

    if project_list_failed:
        for source_id in memory.source_ids():
            if not source_id.startswith("project:"):
                continue
            remembered = memory.recall(source_id, now=clock_now)
            if remembered is None:
                # Beyond the replay horizon: unobserved, not "still true".
                continue
            coverage.append(_coverage_row(
                source_id=source_id, kind="project", state="failed",
                observed_at=remembered.get("observed_at"),
                label=remembered.get("label") or "",
                project_id=remembered.get("project_id") or "",
                reason="project list unavailable",
            ))
            carried.extend(_carry(remembered))

    # Carried items keep their severity and are named as remembered, so a
    # source that vanished cannot lower a known item by disappearing.
    known_ids = {row.get("id") for row in items}
    for row in carried:
        if row.get("id") in known_ids:
            continue
        known_ids.add(row.get("id"))
        items.append(row)
        if row.get("projectId"):
            project_ids.add(str(row["projectId"]))

    # HS-200-15 (AC2, AC3): duplicate projections of one obligation
    # collapse to one row with traceable ``sources``; the rows are then
    # ranked by observable urgency (overdue, due today, not run, no due
    # date, waiting), age within the class, and the stable id as the
    # tie-break.  Severity is NOT a sort key (D2(b)).
    items = rank_and_dedup(items, clock_now)

    next_item = None
    if door_upcoming is not None:
        try:
            upcoming = door_upcoming(datetime.now())
            if upcoming:
                first = upcoming[0]
                next_item = {
                    "label": first.get("title", ""),
                    "at": first.get("starts_at"),
                }
        except Exception:
            pass

    computed_at = clock_now.isoformat()
    return {
        "count": len(items),
        "projects": sorted(project_ids),
        "items": items,
        "next": next_item,
        # computedAt is the AGGREGATE's clock; each coverage record carries
        # its source's own observed_at (C4: the two are distinct).
        "computedAt": computed_at,
        "stale": False,
        "sweepId": None,
        "coverage": coverage,
        "complete": all(row["state"] == "available" for row in coverage),
    }


def _carry(remembered: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Replay a failed source's last-known items, marked as remembered."""
    if not remembered or not remembered.get("items"):
        return []
    out: list[dict[str, Any]] = []
    for row in remembered["items"]:
        carried = dict(row)
        carried["fromLastObservation"] = True
        carried["observedAt"] = remembered.get("observed_at")
        out.append(carried)
    return out


def room_coverage(
    rm: dict[str, Any], project_id: str, project_name: str, *,
    now: datetime | None = None,
    stale_after_s: float = DEFAULT_SOURCE_STALE_AFTER_S,
) -> list[dict[str, Any]]:
    """Every non-project C4 coverage row for one Room projection.

    **``now`` is a LOCAL wall clock, naive.** This is load-bearing and it
    is the one thing a caller can get wrong without noticing. Source
    timestamps arrive from the Room as offset-aware UTC (SQLite
    ``datetime('now')`` through ``aware_iso``), and
    :func:`_older_than` converts them to LOCAL time before comparing them
    to the horizon derived from this argument. Pass a UTC clock and every
    source west of Greenwich reads stale by the offset; pass an aware
    datetime and the comparison silently drifts the same way.
    ``build_aggregate`` passes ``datetime.now()``, and so should you.
    ``None`` means exactly that.

    The PUBLIC seam over :func:`_section_coverage` and
    :func:`_watch_coverage` (HS-200-17 ruling R17-9).  The arrival
    aggregate below calls it, and so does anything else that needs the
    same answer: a second caller deriving these states by hand is exactly
    the defect that ruling was written for -- a hand-rolled mapping
    reported ``available`` for a ``cant_check`` watch while this producer
    reported ``failed``.

    Callers that need one state per KIND rather than one row per source
    must not average or pick arbitrarily; reduce to the WORST row, so a
    summary can never read better than the sources behind it.
    """
    clock = now or datetime.now()
    return [
        *_section_coverage(rm, project_id, project_name),
        *_watch_coverage(rm, project_id, project_name, clock, stale_after_s),
    ]


def _section_coverage(
    rm: dict[str, Any], pid: str, pname: str,
) -> list[dict[str, Any]]:
    """Coverage for the Room sections the attention list draws on.

    An ``absent`` section is not an expected source (the Room does not
    build it), so it is not claimed either way.
    """
    out: list[dict[str, Any]] = []
    observed_at = rm.get("observed_at")
    for key, kind in _SECTION_KINDS:
        section = rm.get(key) or {}
        state = str(section.get("state") or "")
        if state == "absent" or not state:
            continue
        if state == "ok":
            out.append(_coverage_row(
                source_id=f"{kind}:{pid}", kind=kind, state="available",
                observed_at=str(observed_at) if observed_at else None,
                label=pname, project_id=pid,
            ))
        else:
            out.append(_coverage_row(
                source_id=f"{kind}:{pid}", kind=kind, state="failed",
                observed_at=None, label=pname, project_id=pid,
                reason=str(section.get("error_code") or state),
            ))
    return out


def _watch_coverage(
    rm: dict[str, Any], pid: str, pname: str,
    now: datetime, stale_after_s: float,
) -> list[dict[str, Any]]:
    """Coverage for every Watch-backed source of a Room.

    The Room already computed these rows (``sources``); the mapping is
    its own vocabulary, unchanged: ``live`` observed recently is
    available, ``live`` observed long ago is stale, a never-checked
    ``live`` source and a paused one are unavailable, ``cant_check`` is
    failed with the Room's plain reason.
    """
    sources = rm.get("sources") or {}
    if str(sources.get("state") or "") != "ok":
        # The sources read itself failed; the project row already says so.
        return []
    out: list[dict[str, Any]] = []
    horizon = now - timedelta(seconds=stale_after_s)
    for src in sources.get("items") or []:
        watch_id = str(src.get("watchId") or "")
        label = " ".join(
            part for part in (str(src.get("provider") or ""), str(src.get("scope") or ""))
            if part
        ) or pname
        checked_at = src.get("checkedAt")
        w_state = str(src.get("state") or "")
        if w_state == "cant_check":
            state, reason = "failed", (src.get("plainReason") or "cannot check")
        elif w_state == "paused":
            state, reason = "unavailable", "paused"
        elif not checked_at:
            state, reason = "unavailable", "never checked"
        elif _older_than(str(checked_at), horizon):
            state, reason = "stale", "not checked recently"
        else:
            state, reason = "available", None
        out.append(_coverage_row(
            source_id=f"watch:{watch_id}" if watch_id else f"watch:{pid}:{label}",
            kind="watch", state=state,
            observed_at=str(checked_at) if checked_at else None,
            label=label, project_id=pid, reason=reason,
        ))
    return out


def _older_than(stamp: str, horizon: datetime) -> bool:
    """True when an ISO stamp is older than the horizon (unparsable = no claim)."""
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    reference = horizon.astimezone().replace(tzinfo=None) if horizon.tzinfo else horizon
    return parsed < reference


# ── Dirty marker (durable, cross-thread) ────────────────────────────

_DIRTY_MARKER_ID = "needs_you_aggregate"


def mark_needs_you_dirty(db: Any) -> None:
    """HS-172-03: write a dirty marker so the cache refreshes on next read.

    Uses ``desk_projection_state`` with a well-known projection_id.
    Thread-safe (INSERT OR REPLACE is atomic in SQLite WAL mode).
    """
    now = datetime.now().isoformat()
    with db._connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO desk_projection_state
               (projection_id, attention_state, updated_at)
               VALUES (?, 'unseen', ?)""",
            (_DIRTY_MARKER_ID, now),
        )


def _read_dirty_at(db: Any) -> str | None:
    """Read the dirty marker's timestamp (None when no marker exists)."""
    with db._connection() as conn:
        row = conn.execute(
            "SELECT updated_at FROM desk_projection_state WHERE projection_id = ?",
            (_DIRTY_MARKER_ID,),
        ).fetchone()
    return str(row["updated_at"]) if row else None


# ── Stale-while-refresh cache ────────────────────────────────────────


class NeedsYouCache:
    """Thread-safe stale-while-refresh cache for the aggregate.

    ``max_age_s`` defaults to 900 (15 min, matching the default cadence
    interval).  A call to ``invalidate()`` marks the cache stale
    immediately; the next ``get()`` triggers a rebuild via the
    ``builder`` callback.

    HS-172-03: on every ``get()``, the cache also checks the durable
    dirty marker in ``desk_projection_state``. A marker newer than the
    cached ``computedAt`` forces a rebuild, so proposals/confirm/dismiss
    are visible within the 60 s arrival poll without cross-thread singleton
    hunts.

    HS-200-07 (C4): the cache is SINGLE-FLIGHT -- concurrent readers that
    all miss produce exactly ONE builder call; the others wait on the
    build lock and read the result it produced.  Invalidation marks the
    cache stale but KEEPS the last good payload (coverage included), and
    a build that raises serves that payload with ``stale: True`` and its
    own observation times rather than a fresh-looking empty result.
    """

    def __init__(
        self,
        builder: Callable[[], dict[str, Any]],
        *,
        max_age_s: float = 900.0,
        db_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._builder = builder
        self._max_age_s = max_age_s
        self._db_factory = db_factory
        self._lock = threading.Lock()
        self._build_lock = threading.Lock()
        self._data: dict[str, Any] | None = None
        self._computed_at: float = 0.0
        self._computed_wall: str = ""  # ISO wall-clock at last rebuild
        self._sweep_id: str | None = None
        self._dirty = False
        #: Completed builds -- a waiter that sees a newer generation reads
        #: that build's result instead of doing its own.
        self._generation = 0
        #: Builder invocations -- the concurrency bound tests read this.
        self.build_count = 0

    # ── staleness ────────────────────────────────────────────────────

    def _is_stale(self, *, force: bool) -> bool:
        now = time.monotonic()
        with self._lock:
            if force or self._dirty or self._data is None:
                return True
            if (now - self._computed_at) >= self._max_age_s:
                return True
        # HS-172-03: check durable dirty marker.
        if self._db_factory is not None:
            try:
                dirty_at = _read_dirty_at(self._db_factory())
                if dirty_at and dirty_at > self._computed_wall:
                    return True
            except Exception:
                pass
        return False

    def get(self, *, force: bool = False) -> dict[str, Any]:
        """Return the cached aggregate; rebuild on miss, force, or dirty marker."""
        if not self._is_stale(force=force):
            with self._lock:
                if self._data is not None:
                    return self._data

        # Single flight: the first caller builds, the rest wait here and
        # then read what it produced (bound: ONE build per stale window,
        # concurrent forces included -- a build that finished while this
        # caller waited IS its rebuild).
        with self._lock:
            generation = self._generation
        with self._build_lock:
            with self._lock:
                if self._generation != generation and self._data is not None:
                    return self._data
            try:
                self.build_count += 1
                data = self._builder()
            except Exception as exc:
                with self._lock:
                    last = self._data
                if last is None:
                    raise
                log.warning("needs-you: rebuild failed, serving stale: %s", exc)
                # Honest: the payload is the LAST observation, said so.
                return {**last, "stale": True}
            wall = datetime.now().isoformat()
            with self._lock:
                data["stale"] = False
                data["sweepId"] = self._sweep_id
                self._data = data
                self._computed_at = time.monotonic()
                self._computed_wall = wall
                self._dirty = False
                self._generation += 1
            return data

    def invalidate(self, *, sweep_id: str | None = None) -> None:
        """Mark the cache stale; the next ``get()`` will rebuild.

        The last good payload is KEPT so a failing rebuild still has its
        coverage and observation times to serve (never a fresh-looking
        empty result).
        """
        with self._lock:
            self._dirty = True
            self._computed_at = 0.0
            self._computed_wall = ""
            if sweep_id is not None:
                self._sweep_id = sweep_id

    def peek(self) -> dict[str, Any] | None:
        """Return the cached data without rebuilding (for tests)."""
        with self._lock:
            if self._data is None:
                return None
            age = time.monotonic() - self._computed_at
            stale = self._dirty or age >= self._max_age_s
            return {**self._data, "stale": stale}


def cached_aggregate(
    cache: NeedsYouCache,
    *,
    force: bool = False,
    max_age_s: float | None = None,
) -> dict[str, Any]:
    """Convenience wrapper: read from the cache, optionally force.

    ``max_age_s`` is ignored here (lifetime is set on the cache); the
    parameter exists so the sibling HeartbeatService can call this with
    a signature that mirrors the design doc.
    """
    return cache.get(force=force)


__all__ = [
    "build_aggregate",
    "cached_aggregate",
    "mark_needs_you_dirty",
    "NeedsYouCache",
    "LastKnownStore",
    "last_known_store",
    "shared_last_known",
    "REPLAY_HORIZON_DAYS",
    "COVERAGE_STATES",
    "COVERAGE_KINDS",
    "DEFAULT_SOURCE_STALE_AFTER_S",
    "room_coverage",
]

"""Bounded background refresh of configured ICS projections (HS-144-02, HS-146-01).

This conductor owns only calendar source I/O, projection replacement, and the
existing kernel receipts that make failed or skipped untrusted input visible.
It deliberately has no recording, mic-floor, route-plan, or browser concerns.
"""
from __future__ import annotations

import hashlib
import math
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .calendar_ingest import MAX_FEED_BYTES, parse_calendar_bytes
from .config import (
    Config,
    calendar_source_revision,
    calendar_subscription_revision,
    validate_calendar_subscription,
)
from .config.integrations import CALENDAR_REFRESH_SECONDS, CalendarSource, _source_label
from .logging_config import get_logger


log = get_logger("calendar_ingest_conductor")


@dataclass(frozen=True)
class CalendarSourceError(RuntimeError):
    """A classified source-boundary failure which never reaches the hub loop."""

    error_class: str
    redirect_target: str = ""

    def __str__(self) -> str:
        return self.error_class


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Turn every HTTP redirect into an explicit, inspectable refusal."""

    def _refuse_redirect(self, headers: Any) -> None:
        raise CalendarSourceError(
            "calendar_source_redirect", str(headers.get("Location", "")).strip()
        )

    def http_error_301(self, request: Any, fp: Any, code: int, msg: str, headers: Any) -> Any:
        self._refuse_redirect(headers)

    def http_error_302(self, request: Any, fp: Any, code: int, msg: str, headers: Any) -> Any:
        self._refuse_redirect(headers)

    def http_error_303(self, request: Any, fp: Any, code: int, msg: str, headers: Any) -> Any:
        self._refuse_redirect(headers)

    def http_error_307(self, request: Any, fp: Any, code: int, msg: str, headers: Any) -> Any:
        self._refuse_redirect(headers)

    def http_error_308(self, request: Any, fp: Any, code: int, msg: str, headers: Any) -> Any:
        self._refuse_redirect(headers)


class CalendarSourceReader:
    """Read one already-validated local file or HTTPS source within hard bounds.

    No credentials, request-header bag, cookies, redirect follow-up, or proxy
    configuration is accepted by this API.  Disabling inherited proxies avoids
    accidentally attaching proxy credentials to the bounded fetch.
    """

    timeout_seconds = 10.0
    max_bytes = MAX_FEED_BYTES

    def __init__(self, *, opener: Any | None = None) -> None:
        self._opener = opener or urllib.request.build_opener(
            urllib.request.ProxyHandler({}), _NoRedirectHandler()
        )

    def read(self, subscription: str) -> bytes:
        """Read a validated source, raising only a classified source failure."""
        try:
            source = validate_calendar_subscription(subscription)
        except ValueError as exc:
            raise CalendarSourceError("calendar_source_invalid") from exc
        if not source:
            raise CalendarSourceError("calendar_source_disabled")
        if source.lower().startswith("https://"):
            return self._read_https(source)
        return self._read_file(source)

    def _read_file(self, source: str) -> bytes:
        path = Path(source).expanduser()
        try:
            if path.stat().st_size > self.max_bytes:
                raise CalendarSourceError("calendar_source_too_large")
            with path.open("rb") as stream:
                return stream.read(self.max_bytes)
        except CalendarSourceError:
            raise
        except OSError as exc:
            raise CalendarSourceError("calendar_source_file_error") from exc

    def _read_https(self, source: str) -> bytes:
        # A bare Request has no caller-controlled headers.  In particular, this
        # boundary has no Authorization/Cookie/token/header facility.
        request = urllib.request.Request(source)
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                content_length = response.headers.get("Content-Length")
                if content_length is not None and int(content_length) > self.max_bytes:
                    raise CalendarSourceError("calendar_source_too_large")
                raw = response.read(self.max_bytes + 1)
        except CalendarSourceError:
            raise
        except urllib.error.HTTPError as exc:
            if 300 <= exc.code < 400:
                raise CalendarSourceError(
                    "calendar_source_redirect",
                    str(exc.headers.get("Location", "")).strip(),
                ) from exc
            raise CalendarSourceError("calendar_source_http_error") from exc
        except (TimeoutError, urllib.error.URLError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, TimeoutError) or "timed out" in str(reason).lower():
                raise CalendarSourceError("calendar_source_timeout") from exc
            raise CalendarSourceError("calendar_source_network_error") from exc
        if len(raw) > self.max_bytes:
            raise CalendarSourceError("calendar_source_too_large")
        return raw


class CalendarIngestConductor:
    """Refresh calendar projections at boot and then every fifteen minutes."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] | None = None,
        db_factory: Callable[[], Any] | None = None,
        source_reader: CalendarSourceReader | Callable[[str], bytes] | None = None,
        config_loader: Callable[[], Config] | None = None,
        tick_interval: float = CALENDAR_REFRESH_SECONDS,
    ) -> None:
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._clock = clock or time.time
        self._db_factory = db_factory
        self._source_reader = source_reader or CalendarSourceReader()
        self._config_loader = config_loader or Config.load
        self._tick_interval = tick_interval

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="calendar-ingest-conductor"
        )
        self._thread.start()
        log.info("Calendar ingest conductor started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            # join must outlast the 10s HTTP timeout so stop() means stopped
            self._thread.join(timeout=12)
        log.info("Calendar ingest conductor stopped")

    def refresh(self) -> bool:
        """Perform one contained refresh; return whether any projection was applied."""
        try:
            config = self._config_loader()
        except Exception as exc:
            self._write_refresh_failure("invalid_config", error_class="invalid_config")
            log.warning("Calendar configuration reload failed: %s", exc)
            return False

        sources = [s for s in config.calendar.sources if s.enabled]
        if not sources:
            return False

        any_applied = False
        enabled_ids = [s.id for s in sources]
        for source in sources:
            if self._refresh_source(source):
                any_applied = True

        try:
            self._get_db().calendar_events.delete_sources_not_in(enabled_ids)
        except Exception as exc:
            log.error("Calendar orphan cleanup failed: %s", exc)

        # HS-175-02: run the event-to-Room matcher after each refresh.
        if any_applied:
            try:
                self._run_event_room_matcher()
            except Exception as exc:
                log.error("Event-to-Room matcher failed: %s", exc)

        return any_applied

    def _run_event_room_matcher(self) -> None:
        """HS-175-02: match calendar events to Rooms by title.

        H3 (counsel): a title match requires the Room name (>= 4 chars) as a
        whole-word substring of the event title; one-word Room names of <= 3
        chars never auto-match (too high false-positive risk).

        Manual links are preserved (they override the matcher).  Attendee
        match is wired as a seam that returns nothing until the parser
        extracts attendees (D4 H3 / H5).
        """
        import re

        db = self._get_db()
        events = db.calendar_events.list_all()
        if not events:
            return

        # Load all non-archived projects (Rooms).
        try:
            projects = db.projects.list_projects(include_archived=False)
        except Exception as exc:
            log.error("Event-Room matcher: failed to load projects: %s", exc)
            return

        # Build matcher candidates: Room name and Watch query strings.
        room_candidates: list[tuple[str, str, str]] = []  # (project_id, name, kind)
        for proj in projects:
            name = getattr(proj, "name", "") or ""
            pid = getattr(proj, "id", "") or ""
            if not pid or not name:
                continue
            room_candidates.append((pid, name, "room_name"))
            # Also try Watch query strings from connector_watches.
            try:
                with db._connection() as conn:
                    watches = conn.execute(
                        "SELECT query FROM connector_watches WHERE project_id = ?",
                        (pid,),
                    ).fetchall()
                for w in watches:
                    q = str(w["query"] or "").strip()
                    if q:
                        room_candidates.append((pid, q, "watch_query"))
            except Exception:
                pass

        if not room_candidates:
            return

        links: list[tuple[str, str, str]] = []
        for event in events:
            title = (event.title or "").strip()
            if not title:
                continue
            title_lower = title.lower()
            best_match: tuple[str, int] | None = None  # (project_id, match_length)
            for pid, candidate, _kind in room_candidates:
                candidate_stripped = candidate.strip()
                if len(candidate_stripped) < 4:
                    # H3: skip short names (too high false-positive risk).
                    continue
                candidate_lower = candidate_stripped.lower()
                # Whole-word substring match.
                pattern = r'\b' + re.escape(candidate_lower) + r'\b'
                if re.search(pattern, title_lower):
                    # Prefer the LONGEST matching Room name.
                    if best_match is None or len(candidate_stripped) > best_match[1]:
                        best_match = (pid, len(candidate_stripped))
            if best_match is not None:
                links.append((event.id, best_match[0], "title"))

        try:
            db.calendar_event_projects.replace_auto_links(links)
        except Exception as exc:
            log.error("Event-Room matcher: failed to persist links: %s", exc)

    def _refresh_source(self, source: CalendarSource) -> bool:
        """Fetch, parse, and replace projection for one source."""
        try:
            url = validate_calendar_subscription(source.url)
        except Exception as exc:
            self._write_refresh_failure(
                source.id, error_class="invalid_config"
            )
            log.warning("Calendar source %s validation failed: %s", source.id, exc)
            return False
        if not url:
            return False

        revision = calendar_source_revision(source.id, url)
        try:
            raw = self._read_source(url)
        except CalendarSourceError as exc:
            self._write_refresh_failure(
                revision,
                error_class=exc.error_class,
                redirect_target=exc.redirect_target,
            )
            log.warning("Calendar refresh source failure (%s): %s", source.id, exc.error_class)
            return False
        except Exception as exc:
            self._write_refresh_failure(revision, error_class="calendar_source_unexpected")
            log.exception("Calendar source reader failed unexpectedly (%s): %s", source.id, exc)
            return False

        now_epoch = self._clock()
        result = parse_calendar_bytes(
            raw,
            now=datetime.fromtimestamp(now_epoch, tz=timezone.utc),
            subscription_revision=revision,
        )
        if not result.succeeded:
            self._write_refresh_failure(revision, error_class=result.feed_error or "calendar_feed_failed")
            log.warning("Calendar feed parse failure (%s): %s", source.id, result.feed_error)
            return False

        # D3b: capture linked schedules' event data BEFORE replace so R2
        # nearest-matching has the old starts_at.  The pre-read is a separate
        # transaction (the connection pattern does not share); reconciliation
        # is idempotent and catches its own errors, so a gap is harmless.
        db = self._get_db()
        pre_replace_events: dict[str, dict[str, Any]] = {}
        try:
            linked = db.scheduled_recordings.list_linked_for_source(source.id)
            for sched in linked:
                if sched.calendar_event_id:
                    ev = db.calendar_events.get(sched.calendar_event_id)
                    if ev is not None:
                        pre_replace_events[sched.id] = {
                            "calendar_event_id": ev.id,
                            "starts_at": ev.starts_at,
                            "ends_at": ev.ends_at,
                            "title": ev.title,
                            "uid": ev.uid,
                        }
        except Exception as exc:
            log.warning("Pre-replace event snapshot failed (%s): %s", source.id, exc)
            # Proceed: reconciliation degrades to R3 for anything it cannot
            # reconstruct, which is safer than skipping the whole refresh.

        try:
            db.calendar_events.replace_projection(
                revision,
                result.events,
                seen_at=now_epoch,
                source_id=source.id,
                source_label=_source_label(source),
            )
        except Exception as exc:
            self._write_refresh_failure(revision, error_class="calendar_projection_failed")
            log.exception("Calendar projection replacement failed (%s): %s", source.id, exc)
            return False

        # HS-147-03 D3a: reconcile linked schedules for THIS source only.
        # Idempotent, catches its own exceptions, never propagates (D3b).
        self._reconcile_linked_schedules(
            db, source.id, pre_replace_events, now_epoch,
        )

        # HS-175-03: auto-create event-born recordings for events with a
        # meeting_url, controlled by the owner's auto_record setting.
        self._create_event_born_recordings(db, source.id, now_epoch)

        for skip in result.skips:
            self._write_event_skip(revision, skip.event_ref, skip.reason)
        return True

    # ── HS-147-03: post-replace reconciliation ─────────────────────

    def _reconcile_linked_schedules(
        self,
        db: Any,
        source_id: str,
        pre_replace_events: dict[str, dict[str, Any]],
        now_epoch: float,
    ) -> None:
        """Reconcile linked schedules after a source's projection is replaced.

        Idempotent, catches its own exceptions, logs, never propagates (D3b).
        Scoped to the refreshed source only (D3a).
        X1: only idle rows are read (list_linked_for_source filters state).
        """
        try:
            linked = db.scheduled_recordings.list_linked_for_source(source_id)
        except Exception as exc:
            log.error("Reconcile: failed to list linked schedules for %s: %s", source_id, exc)
            return

        for sched in linked:
            try:
                self._reconcile_one(db, sched, pre_replace_events, now_epoch)
            except Exception as exc:
                log.error(
                    "Reconcile: schedule %s (event %s) failed: %s",
                    sched.id, sched.calendar_event_id, exc,
                )

    def _reconcile_one(
        self,
        db: Any,
        sched: Any,
        pre_replace_events: dict[str, dict[str, Any]],
        now_epoch: float,
    ) -> None:
        """Reconcile a single linked schedule against the new projection.

        R1: id survives -> refresh duration/title in place.
        R2: id gone, uid survives -> rebind to nearest occurrence.
        R3: uid gone -> cancel with event_removed.
        """
        # R1: check if the projection id still exists
        current_event = db.calendar_events.get(sched.calendar_event_id)
        if current_event is not None:
            # Projection id survived (starts_at unchanged).  Refresh
            # duration and title if ends_at or title changed.
            pre = pre_replace_events.get(sched.id)
            needs_refresh = False
            if pre is not None:
                if pre["ends_at"] != current_event.ends_at:
                    needs_refresh = True
                if pre["title"] != current_event.title:
                    needs_refresh = True
            else:
                # No pre-snapshot: refresh anyway to be safe.
                needs_refresh = True

            if needs_refresh:
                starts_at = datetime.fromisoformat(
                    current_event.starts_at.replace("Z", "+00:00")
                ).astimezone(timezone.utc)
                ends_at = datetime.fromisoformat(
                    current_event.ends_at.replace("Z", "+00:00")
                ).astimezone(timezone.utc)
                duration_seconds = (ends_at - starts_at).total_seconds()
                duration_minutes = min(max(1, math.ceil(duration_seconds / 60)), 480)
                db.scheduled_recordings.refresh_in_place(
                    sched.id,
                    duration_minutes=duration_minutes,
                    title=current_event.title,
                )
                log.info(
                    "Reconcile R1: refreshed schedule %s in place "
                    "(duration=%d, title=%s)",
                    sched.id, duration_minutes, current_event.title,
                )
            return

        # R2: id gone but uid might survive — look for occurrences with
        # the same (source_id, uid) in the new projection.
        uid = sched.calendar_uid
        source_id = sched.calendar_source_id
        if uid:
            candidates = self._find_uid_occurrences(db, source_id, uid)
            if candidates:
                # Pick the occurrence whose starts_at is nearest the old one.
                old_starts_epoch = self._old_starts_epoch(sched, pre_replace_events)
                best = min(
                    candidates,
                    key=lambda ev: abs(
                        datetime.fromisoformat(
                            ev.starts_at.replace("Z", "+00:00")
                        ).timestamp() - old_starts_epoch
                    ),
                )
                # Compute new fire time and duration
                new_starts = datetime.fromisoformat(
                    best.starts_at.replace("Z", "+00:00")
                ).astimezone(timezone.utc)
                new_ends = datetime.fromisoformat(
                    best.ends_at.replace("Z", "+00:00")
                ).astimezone(timezone.utc)
                duration_seconds = (new_ends - new_starts).total_seconds()
                duration_minutes = min(max(1, math.ceil(duration_seconds / 60)), 480)

                # next_fire_at: starts_at - 60s, or now if already started
                now_dt = datetime.fromtimestamp(now_epoch, tz=timezone.utc)
                if new_starts <= now_dt:
                    next_fire_at = now_epoch
                else:
                    next_fire_at = (new_starts - timedelta(seconds=60)).timestamp()

                # L1 check: if the rebind target is already armed by another
                # enabled schedule, treat as R3 (the counsel-ledgered case).
                try:
                    with db._connection() as conn:
                        existing = conn.execute(
                            """SELECT id FROM scheduled_recordings
                               WHERE calendar_event_id = ?
                                 AND enabled = 1
                                 AND id != ?
                               LIMIT 1""",
                            (best.id, sched.id),
                        ).fetchone()
                    if existing:
                        log.warning(
                            "Reconcile R2->R3: rebind target %s already armed "
                            "by %s; cancelling schedule %s",
                            best.id, existing["id"], sched.id,
                        )
                        db.scheduled_recordings.cancel_for_event_removed(sched.id)
                        return
                except Exception as exc:
                    log.error("Reconcile L1 check failed for %s: %s", sched.id, exc)
                    # On L1 check failure, cancel to be safe (never violate the index).
                    db.scheduled_recordings.cancel_for_event_removed(sched.id)
                    return

                db.scheduled_recordings.rebind_event(
                    sched.id,
                    calendar_event_id=best.id,
                    next_fire_at=next_fire_at,
                    duration_minutes=duration_minutes,
                    title=best.title,
                )
                log.info(
                    "Reconcile R2: rebound schedule %s to event %s "
                    "(new fire at %s, duration=%d)",
                    sched.id, best.id,
                    datetime.fromtimestamp(next_fire_at, tz=timezone.utc).isoformat(),
                    duration_minutes,
                )
                return

        # R3: uid gone from the projection -> cancel.
        db.scheduled_recordings.cancel_for_event_removed(sched.id)
        log.info(
            "Reconcile R3: cancelled schedule %s (event %s removed from feed)",
            sched.id, sched.calendar_event_id,
        )

    def _find_uid_occurrences(self, db: Any, source_id: str, uid: str) -> list[Any]:
        """Find all projection rows for (source_id, uid) after replace."""
        try:
            with db._connection() as conn:
                rows = conn.execute(
                    """SELECT * FROM calendar_events
                       WHERE source_id = ? AND uid = ?
                       ORDER BY starts_at""",
                    (source_id, uid),
                ).fetchall()
            from .db.calendar_events import _row_to_model as _ce_row
            return [_ce_row(r) for r in rows]
        except Exception as exc:
            log.error("Reconcile: uid lookup failed for %s/%s: %s", source_id, uid, exc)
            return []

    def _old_starts_epoch(
        self,
        sched: Any,
        pre_replace_events: dict[str, dict[str, Any]],
    ) -> float:
        """Recover the old starts_at epoch for nearest-occurrence matching.

        Prefers the pre-replace snapshot; falls back to reconstructing from
        next_fire_at + 60s (valid for future arms; close enough for fire-now).
        """
        pre = pre_replace_events.get(sched.id)
        if pre is not None:
            try:
                return datetime.fromisoformat(
                    pre["starts_at"].replace("Z", "+00:00")
                ).timestamp()
            except Exception:
                pass
        # Fallback: next_fire_at + 60s (the 60s lead rule).
        if sched.next_fire_at is not None:
            return sched.next_fire_at + 60
        # Last resort: use created_at as a rough proxy.
        return sched.created_at

    # ── HS-175-03: event-born recordings ────────────────────────────

    def _create_event_born_recordings(
        self,
        db: Any,
        source_id: str,
        now_epoch: float,
    ) -> None:
        """Auto-create recordings for calendar events with meeting URLs.

        Controlled by ``meeting.auto_record``:
        - ``off``: do nothing (Article IV: arming is his act).
        - ``all_calendar``: every event with a ``meeting_url``.
        - ``room_linked``: only events linked to a Room via
          ``calendar_event_projects``.

        Idempotent: the unique index ``idx_scheduled_recordings_calendar_event_armed``
        prevents duplicate arms.  Catches its own exceptions.
        """
        try:
            config = self._config_loader()
        except Exception as exc:
            log.warning("Event-born recordings: config load failed: %s", exc)
            return

        auto_record = getattr(config.meeting, "auto_record", "off")
        if auto_record == "off":
            return

        lead_minutes = getattr(config.meeting, "auto_record_lead_minutes", 5)
        now_dt = datetime.fromtimestamp(now_epoch, tz=timezone.utc)

        try:
            with db._connection() as conn:
                rows = conn.execute(
                    """SELECT id, uid, title, starts_at, ends_at, meeting_url,
                              source_id, source_label
                       FROM calendar_events
                       WHERE source_id = ?
                         AND meeting_url IS NOT NULL
                         AND meeting_url != ''
                         AND starts_at > ?
                       ORDER BY starts_at""",
                    (source_id, self._utc_iso(now_dt)),
                ).fetchall()
        except Exception as exc:
            log.error("Event-born recordings: event query failed: %s", exc)
            return

        # When room_linked, check the calendar_event_projects table.
        linked_event_ids: set[str] | None = None
        if auto_record == "room_linked":
            try:
                with db._connection() as conn:
                    linked_rows = conn.execute(
                        "SELECT calendar_event_id FROM calendar_event_projects"
                    ).fetchall()
                linked_event_ids = {r["calendar_event_id"] for r in linked_rows}
            except Exception:
                # Table may not exist yet (the A lane builds it).
                # Treat every event as unlinked -- create nothing.
                log.info(
                    "Event-born recordings: calendar_event_projects not available; "
                    "treating all events as unlinked"
                )
                return

        for row in rows:
            event_id = row["id"]

            # Room-linked filter.
            if linked_event_ids is not None and event_id not in linked_event_ids:
                continue

            # Compute fire time: starts_at - lead_minutes.
            try:
                starts_at = datetime.fromisoformat(
                    row["starts_at"].replace("Z", "+00:00")
                ).astimezone(timezone.utc)
                ends_at = datetime.fromisoformat(
                    row["ends_at"].replace("Z", "+00:00")
                ).astimezone(timezone.utc)
            except Exception as exc:
                log.warning(
                    "Event-born recordings: bad timestamp on event %s: %s",
                    event_id, exc,
                )
                continue

            fire_at = (starts_at - timedelta(minutes=lead_minutes)).timestamp()
            duration_seconds = (ends_at - starts_at).total_seconds()
            duration_minutes = min(max(1, int(duration_seconds / 60 + 0.5)), 480)

            try:
                db.scheduled_recordings.create(
                    title=row["title"] or "",
                    cron_expr="",
                    tz="UTC",
                    one_shot=True,
                    duration_minutes=duration_minutes,
                    enabled=True,
                    next_fire_at=fire_at,
                    calendar_event_id=event_id,
                    calendar_uid=row["uid"] or "",
                    calendar_source_id=source_id,
                    born_from="calendar_event",
                )
                self._write_event_born_receipt(event_id, row["title"] or "")
                log.info(
                    "Event-born recording created for event %s (%s)",
                    event_id, row["title"],
                )
            except Exception as exc:
                # IntegrityError from the unique index means a live arm
                # already exists — idempotent, not an error.
                if "UNIQUE constraint failed" in str(exc):
                    continue
                log.error(
                    "Event-born recording creation failed for event %s: %s",
                    event_id, exc,
                )

    def _write_event_born_receipt(self, event_id: str, title: str) -> None:
        """Receipt for an auto-created event-born recording."""
        digest = hashlib.sha256(
            f"event_born:{event_id}".encode("utf-8")
        ).hexdigest()
        self._write_receipt(
            revision=f"event_born:{digest[:16]}",
            category="scheduled_recording",
            state="succeeded",
            outcome="scheduled_recording.created.calendar_event",
            result_ref=f"calendar_event:{event_id}",
            discriminator=f"event_born:{event_id}",
        )

    @staticmethod
    def _utc_iso(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    def _loop(self) -> None:
        # Boot is an actual refresh, not merely a delayed first cadence tick.
        self.refresh()
        while not self._stop.wait(self._tick_interval):
            self.refresh()

    def _get_db(self) -> Any:
        if self._db_factory is not None:
            return self._db_factory()
        from .db import get_database

        return get_database()

    def _read_source(self, subscription: str) -> bytes:
        reader = self._source_reader
        if callable(reader) and not hasattr(reader, "read"):
            return reader(subscription)
        return reader.read(subscription)  # type: ignore[union-attr]

    def _write_event_skip(self, revision: str, event_ref: str, reason: str) -> None:
        event_hash = hashlib.sha256(event_ref.encode("utf-8")).hexdigest()[:16]
        self._write_receipt(
            revision=revision,
            category="event",
            state="refused",
            outcome="calendar_event_skipped",
            result_ref=f"calendar-event:{event_hash}:{reason}",
            discriminator=f"{event_hash}:{reason}",
        )

    def _write_refresh_failure(
        self,
        revision: str,
        *,
        error_class: str,
        redirect_target: str = "",
    ) -> None:
        # Redirects are a refusal: the owner approved the original host, not an
        # undisclosed follow-up target.  Other source and parse failures remain
        # failures and retain the last known-good projection.
        state = "refused" if error_class == "calendar_source_redirect" else "failed"
        target = redirect_target or error_class
        self._write_receipt(
            revision=revision,
            category="refresh",
            state=state,
            outcome="calendar_refresh_failed",
            result_ref=f"calendar-source:{revision[:16]}:{target}",
            discriminator=f"{error_class}:{target}",
        )

    def _write_receipt(
        self,
        *,
        revision: str,
        category: str,
        state: str,
        outcome: str,
        result_ref: str,
        discriminator: str,
    ) -> None:
        """Insert one deterministic existing-kernel receipt, once per failure."""
        digest = hashlib.sha256(
            f"{revision}\0{category}\0{discriminator}".encode("utf-8")
        ).hexdigest()
        idempotency_key = f"calendar:{digest}"
        operation_id = f"ci_op_{digest[:24]}"
        receipt_id = f"ci_rcpt_{digest[:24]}"
        now = self._clock()
        try:
            with self._get_db()._connection() as conn:
                cursor = conn.execute(
                    """INSERT OR IGNORE INTO kernel_operations
                       (operation_id, request_id, idempotency_key, name, version,
                        principal_kind, principal_identity, target_ref, placement,
                        envelope_sha256, policy_version, authority_basis,
                        state, revision, native_id, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?,?)""",
                    (
                        operation_id,
                        idempotency_key,
                        idempotency_key,
                        "calendar_ingest",
                        1,
                        "scheduler",
                        f"calendar-ingest:{revision[:16]}",
                        "calendar:subscription",
                        "local",
                        "",
                        "",
                        "calendar-subscription",
                        state,
                        operation_id,
                        now,
                        now,
                    ),
                )
                if cursor.rowcount:
                    conn.execute(
                        """INSERT INTO kernel_receipts
                           (receipt_id, operation_id, state, outcome, result_ref, created_at)
                           VALUES (?,?,?,?,?,?)""",
                        (receipt_id, operation_id, state, outcome, result_ref, now),
                    )
        except Exception as exc:
            log.error("Calendar receipt write failed: %s", exc)


_conductor: CalendarIngestConductor | None = None


def start_calendar_ingest_conductor(**kwargs: Any) -> CalendarIngestConductor:
    """Create the one process-global calendar conductor exactly once.

    HS-175-02: the standalone thread is retired -- the heartbeat sweep
    calls ``refresh()`` on each tick.  The conductor object is still
    created so its ``refresh()`` method is callable.  The initial boot
    refresh is performed synchronously here so the first projection is
    populated before the first heartbeat tick (matching the old start()
    behaviour of doing one immediate refresh at boot).
    """
    global _conductor
    if _conductor is None:
        _conductor = CalendarIngestConductor(**kwargs)
    # Boot refresh (synchronous, no thread).
    try:
        _conductor.refresh()
    except Exception as exc:
        log.warning("Calendar boot refresh failed: %s", exc)
    return _conductor


def stop_calendar_ingest_conductor() -> None:
    """Stop and clear the global conductor during hub shutdown.

    HS-175-02: stop() still works (idempotent); it stops the legacy
    thread if one was running from an older code path.
    """
    global _conductor
    if _conductor is not None:
        _conductor.stop()
        _conductor = None

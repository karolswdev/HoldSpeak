"""Bounded background refresh of configured ICS projections (HS-144-02, HS-146-01).

This conductor owns only calendar source I/O, projection replacement, and the
existing kernel receipts that make failed or skipped untrusted input visible.
It deliberately has no recording, mic-floor, route-plan, or browser concerns.
"""
from __future__ import annotations

import hashlib
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
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

        return any_applied

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

        try:
            self._get_db().calendar_events.replace_projection(
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
        for skip in result.skips:
            self._write_event_skip(revision, skip.event_ref, skip.reason)
        return True

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
    """Start the one process-global calendar conductor exactly once."""
    global _conductor
    if _conductor is None:
        _conductor = CalendarIngestConductor(**kwargs)
    _conductor.start()
    return _conductor


def stop_calendar_ingest_conductor() -> None:
    """Stop and clear the global conductor during hub shutdown."""
    global _conductor
    if _conductor is not None:
        _conductor.stop()
        _conductor = None

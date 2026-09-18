"""HS-171-02: HeartbeatService -- the sweep scheduler and aggregate cache.

The heartbeat is the unattended cadence that evaluates due watches on a
configurable interval, caches the needs-you aggregate, and receipts every
sweep through the kernel (Article XI.2).

Settings are stored in the cadence_policies table (key `heartbeat`),
not in Config TOML -- the TOML file is the owner's hand-edited runtime
config; the heartbeat interval is a server-side operational setting.

M3 (counsel): this service does NOT re-implement the aggregate builder.
It delegates to ``needs_you_aggregate.build_aggregate`` /
``NeedsYouCache`` -- that module is the single owner of the shape.

M1 (counsel): the muted_projects setting is passed through to the
aggregate builder; muted items are marked ``muted: true`` and excluded
from the count that drives the notification edge.

N2 (counsel): the sweep receipt's ``outcomes`` is bounded -- a summary
of counts per outcome state + failing watch ids only.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.observer import NullObserver, PipelineObserver

log = logging.getLogger(__name__)

# Defaults
_DEFAULT_SWEEP_EVERY = 15       # minutes
_DEFAULT_QUIET_START = 22       # hour
_DEFAULT_QUIET_END = 8          # hour
_DEFAULT_NOTIFY = "edge"        # off | edge | every_sweep
_HEARTBEAT_POLICY_ID = "heartbeat"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _as_item_map(value: Any) -> dict[str, dict[str, str]]:
    """HS-200-15: the persisted notified set as
    ``{item_id: {"project": <id>, "class": <rank class>}}``.

    Tolerates the shapes a config row may hold (a mapping of entries, a
    mapping of bare project ids from the first cut, or a bare list of ids)
    and never raises on garbage.
    """
    if isinstance(value, dict):
        out: dict[str, dict[str, str]] = {}
        for k, v in value.items():
            if isinstance(v, dict):
                out[str(k)] = {"project": str(v.get("project") or ""),
                               "class": str(v.get("class") or "")}
            else:
                out[str(k)] = {"project": str(v or ""), "class": ""}
        return out
    if isinstance(value, (list, tuple, set)):
        return {str(k): {"project": "", "class": ""} for k in value}
    return {}


def _now_epoch() -> float:
    return time.time()


def _summarize_outcomes(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    """N2: bounded receipt summary -- counts per state + failing watch ids only.

    Instead of dumping the full unbounded outcomes list into the receipt,
    produce a compact summary: how many evaluated/skipped/failed, and the
    watch_ids of any that failed.
    """
    counts: dict[str, int] = {}
    failed_ids: list[str] = []
    for o in outcomes:
        state = o.get("outcome", "unknown")
        counts[state] = counts.get(state, 0) + 1
        if state in ("error", "failed"):
            wid = o.get("watch_id", "")
            if wid:
                failed_ids.append(wid)
    return {
        "counts": counts,
        "total": len(outcomes),
        "failed_watch_ids": failed_ids,
    }


class HeartbeatService:
    """Owns the heartbeat sweep settings, the sweep loop, and the aggregate cache."""

    def __init__(
        self,
        db: Database,
        *,
        observer: PipelineObserver | None = None,
        watch_service: Any | None = None,
        notifier: Any | None = None,
        calendar_conductor: Any | None = None,
        clock: Any | None = None,
        local_zone: Any | None = None,
    ) -> None:
        self._db = db
        self._observer = observer or NullObserver()
        self._watch_service = watch_service
        self._notifier = notifier  # injectable for tests; None = OS default
        # HS-175-02: the calendar refresh rides the heartbeat sweep.
        self._calendar_conductor = calendar_conductor
        # HS-200-03: the sweep read the clock TWICE — once as aware UTC for the
        # receipt and once as naive local for the quiet-hours test — so the two
        # could straddle a second, and neither could be injected. A sweep held
        # by quiet hours writes no `calendar` sub-receipt, which is why
        # tests/unit/test_hs175_calendar_wire.py passed by day and failed on any
        # machine running it between 22:00 and 08:00 local, the CI runner
        # included. One injectable instant now serves both readings.
        self._clock = clock
        # Quiet hours are LOCAL hours, so the zone is as much an input as the
        # instant. Injecting the instant alone is not enough: a fixed UTC noon
        # is midnight in Auckland and still lands inside the default window.
        # None keeps production behaviour -- this machine's own zone.
        self._local_zone = local_zone

    def _now_utc(self) -> datetime:
        """The current instant, aware and in UTC, from the injected clock."""
        if self._clock is None:
            return datetime.now(timezone.utc)
        now = self._clock()
        return now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)

    def _now_local(self) -> datetime:
        """The one sweep instant expressed in the quiet-hours zone."""
        return self._now_utc().astimezone(self._local_zone)

    # ── Settings ───────────────────────────────────────────────────────

    def get_settings(self) -> dict[str, Any]:
        """Read heartbeat settings from cadence_policies."""
        policy = self._db.cadence.get_policy(_HEARTBEAT_POLICY_ID)
        if policy is None:
            return self._defaults()
        config = policy.config if hasattr(policy, "config") else (policy.get("config") if isinstance(policy, dict) else {})
        return {
            "sweep_every_minutes": int(config.get("sweep_every_minutes", _DEFAULT_SWEEP_EVERY)),
            "quiet_hours": {
                "start": int(config.get("quiet_start", _DEFAULT_QUIET_START)),
                "end": int(config.get("quiet_end", _DEFAULT_QUIET_END)),
            },
            "notify": str(config.get("notify", _DEFAULT_NOTIFY)),
            "muted_projects": list(config.get("muted_projects", [])),
            "last_sweep_at": config.get("last_sweep_at"),
            "next_sweep_at": config.get("next_sweep_at"),
            "last_notified_count": int(config.get("last_notified_count", 0)),
            # HS-200-15: the notified ITEM SET (id -> project), so a
            # restart re-notifies nothing and a same-count change fires.
            "last_notified_items": _as_item_map(config.get("last_notified_items")),
            "last_notify_outcome": str(config.get("last_notify_outcome") or ""),
            # HS-174-08: remote runner settings.
            "runs_on": str(config.get("runs_on", "local")),
            "remote_hosts": self._compute_remote_hosts(),
            "last_remote_run_at": self._last_remote_run_at(),
        }

    def update_settings(self, patch: dict[str, Any]) -> dict[str, Any]:
        """Update heartbeat settings. Returns the new state."""
        current = self.get_settings()
        if "sweep_every_minutes" in patch:
            val = int(patch["sweep_every_minutes"])
            if val < 1:
                val = 1
            if val > 1440:
                val = 1440
            current["sweep_every_minutes"] = val
        if "quiet_hours" in patch:
            qh = patch["quiet_hours"]
            if isinstance(qh, dict):
                if "start" in qh:
                    current["quiet_hours"]["start"] = int(qh["start"]) % 24
                if "end" in qh:
                    current["quiet_hours"]["end"] = int(qh["end"]) % 24
        if "notify" in patch:
            n = str(patch["notify"])
            if n in ("off", "edge", "every_sweep"):
                current["notify"] = n
        if "muted_projects" in patch:
            current["muted_projects"] = list(patch["muted_projects"])
        # HS-174-08: runs_on setting. Selecting a remote host holds the
        # WHOLE local sweep, not just the notification -- and since
        # HS-200-43 R1 the heartbeat is the ONLY scheduler for graduated
        # watches, so a non-"local" value stops local watch evaluation
        # entirely until it is set back. The remote host is expected to
        # run its own sweep; nothing here verifies that it does.
        if "runs_on" in patch:
            val = str(patch["runs_on"]).strip()
            current["runs_on"] = val if val else "local"
        self._persist(current)
        return current

    def _defaults(self) -> dict[str, Any]:
        return {
            "sweep_every_minutes": _DEFAULT_SWEEP_EVERY,
            "quiet_hours": {"start": _DEFAULT_QUIET_START, "end": _DEFAULT_QUIET_END},
            "notify": _DEFAULT_NOTIFY,
            "muted_projects": [],
            "last_sweep_at": None,
            "next_sweep_at": None,
            "last_notified_count": 0,
            "last_notified_items": {},
            "last_notify_outcome": "",
            # HS-174-08: remote runner defaults (computed values added in
            # get_settings; not stored).
            "runs_on": "local",
            "remote_hosts": self._compute_remote_hosts(),
            "last_remote_run_at": self._last_remote_run_at(),
        }

    def _persist(self, settings: dict[str, Any]) -> None:
        from holdspeak.cadence.models import CadencePolicy

        config = {
            "sweep_every_minutes": settings["sweep_every_minutes"],
            "quiet_start": settings["quiet_hours"]["start"],
            "quiet_end": settings["quiet_hours"]["end"],
            "notify": settings["notify"],
            "muted_projects": settings["muted_projects"],
            "last_sweep_at": settings.get("last_sweep_at"),
            "next_sweep_at": settings.get("next_sweep_at"),
            "last_notified_count": settings.get("last_notified_count", 0),
            "last_notified_items": _as_item_map(settings.get("last_notified_items")),
            "last_notify_outcome": str(settings.get("last_notify_outcome") or ""),
            # HS-174-08
            "runs_on": settings.get("runs_on", "local"),
        }
        self._db.cadence.upsert_policy(CadencePolicy(
            id=_HEARTBEAT_POLICY_ID,
            name=_HEARTBEAT_POLICY_ID,
            enabled=True,
            config=config,
        ))

    # ── HS-174-08: remote runner helpers ─────────────────────────────────

    def _compute_remote_hosts(self) -> list[str]:
        """Remote hosts that have called POST /api/mcp in the last 30 days.

        Derived from pipeline_events callers with origin='remote'.
        """
        thirty_days_ago = time.time() - 30 * 86400
        try:
            with self._db._connection() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT caller FROM pipeline_events "
                    "WHERE origin = 'remote' AND caller != '' "
                    "AND timestamp > ? "
                    "ORDER BY caller",
                    (thirty_days_ago,),
                ).fetchall()
            return [str(row["caller"]) for row in rows]
        except Exception:
            return []

    def _last_remote_run_at(self) -> str | None:
        """Newest heartbeat.sweep receipt with origin=remote (ISO string)."""
        try:
            with self._db._connection() as conn:
                row = conn.execute(
                    "SELECT timestamp FROM pipeline_events "
                    "WHERE service = 'HeartbeatService' AND method = 'run_sweep' "
                    "AND origin = 'remote' "
                    "ORDER BY timestamp DESC LIMIT 1",
                ).fetchone()
            if row:
                from datetime import datetime as _dt, timezone as _tz
                return _dt.fromtimestamp(
                    float(row["timestamp"]), _tz.utc,
                ).isoformat(timespec="seconds")
        except Exception:
            pass
        return None

    def record_held_remote(self, host: str) -> None:
        """Record that the local loop held because runs_on is a remote host.

        Writes a quiet pipeline_events row (no notification, no kernel receipt).

        HS-200-43 F3: this hold covers watch EVALUATION too. The heartbeat
        is the single scheduler, so while `runs_on` names a remote host no
        watch on this machine is evaluated -- fenced by
        `test_phase200_watch_arming.TestRemoteRunnerHoldsTheSweep`.
        """
        from holdspeak.services.observer import PipelineEvent

        event = PipelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            service="HeartbeatService",
            method="run_sweep",
            principal_kind="owner",
            principal_identity="heartbeat-conductor",
            args_summary=json.dumps({"held": True, "runs_on": host}),
            result_summary=json.dumps({"outcome": "held_remote_runs_on", "host": host}),
            error=None,
            error_code=None,
            duration_ms=0.0,
            correlation_id=str(uuid.uuid4()),
            is_async=False,
            origin="local",
            caller="",
            caller_identity="",
        )
        try:
            self._observer.on_event(event)
        except Exception:
            pass

    # ── In quiet hours? ────────────────────────────────────────────────

    def in_quiet_hours(self, now: datetime | None = None) -> bool:
        """Check whether the current time falls within quiet hours."""
        settings = self.get_settings()
        if now is None:
            # HS-200-03: default through the injected clock, in local hours,
            # so no caller can reach an un-injectable wall clock from here.
            now = self._now_local()
        hour = now.hour
        start = settings["quiet_hours"]["start"]
        end = settings["quiet_hours"]["end"]
        if start == end:
            return False
        if start < end:
            return start <= hour < end
        # Wraps midnight (e.g. 22..8)
        return hour >= start or hour < end

    # ── The sweep ──────────────────────────────────────────────────────

    def run_sweep(
        self,
        principal: Principal,
        *,
        owner_hand: bool = False,
    ) -> dict[str, Any]:
        """Run one heartbeat sweep: evaluate due watches, refresh aggregate, receipt.

        Returns the sweep receipt payload.

        ``owner_hand`` marks a sweep the owner asked for explicitly --
        `Run now` on the Rhythm row, or the `heartbeat.run_now` tool.  ONE
        keyword carries both exemptions, because they are one idea: he is
        standing there watching it happen.

        1. HS-200-43 F2 -- it evaluates EVERY due watch. The
           `WATCH_SWEEP_MAX` bound protects the UNATTENDED heartbeat
           thread, where nobody is waiting and the calendar refresh and
           the receipt queue behind ~28 serial `gh`/`acli` subprocesses.
        2. HS-200-43 P2-b -- it runs INSIDE quiet hours. `USER_GUIDE.md`
           has always promised "Run now triggers one immediate sweep
           (allowed during quiet hours)", but `held` was computed
           unconditionally, so Run now at 23:00 did nothing at all and
           reported success. The receipt records `quiet_overridden` when
           the sweep fired inside the window.
        """
        from holdspeak.services.watch_service import WATCH_SWEEP_MAX

        limit = None if owner_hand else WATCH_SWEEP_MAX
        t0 = time.time()
        now = self._now_utc()
        settings = self.get_settings()
        sweep_id = f"sweep_{uuid.uuid4().hex[:12]}"

        # Quiet hours check. Quiet hours are the owner's LOCAL hours, so the one
        # sweep instant is converted to this machine's zone rather than read
        # from the clock a second time.
        in_quiet = self.in_quiet_hours(self._now_local())
        # P2-b: the owner's hand overrides quiet hours; the scheduled
        # sweep does not. Recorded either way, so a receipt inside the
        # window is never silently indistinguishable from one outside it.
        held = in_quiet and not owner_hand
        quiet_overridden = in_quiet and owner_hand

        outcomes: list[dict[str, Any]] = []
        rooms_evaluated = 0
        watch_count = 0
        watches_baselined = 0
        watches_deferred = 0
        errors: list[dict[str, Any]] = []

        if not held:
            # Call WatchService.evaluate_due to evaluate all due watches
            if self._watch_service is not None:
                try:
                    results = self._watch_service.evaluate_due(
                        principal, limit=limit,
                    )
                    # HS-200-43 F2: the sweep is BOUNDED (WATCH_SWEEP_MAX
                    # per call, oldest-due first). What did not fit is not
                    # dropped -- it stays due for the next sweep -- but the
                    # receipt must say so, or a desk with more watches than
                    # the bound looks like a desk that finished its work.
                    # Read defensively: several existing tests inject a
                    # MagicMock watch service, whose attributes are Mocks.
                    _deferred = getattr(
                        self._watch_service, "last_sweep_deferred", 0,
                    )
                    if isinstance(_deferred, int):
                        watches_deferred = _deferred
                    if isinstance(results, list):
                        outcomes = results
                        # P2-a: a `baselined` outcome established a
                        # baseline and diffed NOTHING (HS-200-43 F1).
                        # Counting it as an evaluated watch would report
                        # work that did not happen.
                        watches_baselined = sum(
                            1 for o in results
                            if isinstance(o, dict)
                            and o.get("outcome") == "baselined"
                        )
                        watch_count = len(results) - watches_baselined
                        # Count unique projects from evaluated watches
                        project_ids = set()
                        for o in results:
                            wid = o.get("watch_id", "")
                            try:
                                with self._db._connection() as conn:
                                    row = conn.execute(
                                        "SELECT project_id FROM connector_watches WHERE id=?",
                                        (wid,),
                                    ).fetchone()
                                    if row and row["project_id"]:
                                        project_ids.add(row["project_id"])
                            except Exception:
                                pass
                            if o.get("outcome") in ("error", "failed"):
                                errors.append(o)
                        rooms_evaluated = len(project_ids)
                except Exception as exc:
                    log.error("heartbeat sweep evaluate_due failed: %s", exc)
                    errors.append({"error": str(exc)})

        # HS-175-02: calendar refresh rides the heartbeat sweep.
        # Own failure boundary: a conductor crash never breaks the loop.
        calendar_refresh_receipt: dict[str, Any] | None = None
        if not held and self._calendar_conductor is not None:
            try:
                applied = self._calendar_conductor.refresh()
                calendar_refresh_receipt = {
                    "kind": "calendar.refresh",
                    "applied": applied,
                }
                # Per-source outcomes with host for HTTPS sources.
                try:
                    config = self._calendar_conductor._config_loader()
                    source_outcomes: list[dict[str, str]] = []
                    for src in config.calendar.sources:
                        if src.enabled:
                            url = str(src.url or "")
                            entry: dict[str, str] = {"source_id": src.id}
                            if url.lower().startswith("https://"):
                                try:
                                    from urllib.parse import urlparse
                                    entry["host"] = urlparse(url).hostname or ""
                                except Exception:
                                    entry["host"] = ""
                            source_outcomes.append(entry)
                    if source_outcomes:
                        calendar_refresh_receipt["sources"] = source_outcomes
                except Exception:
                    pass
            except Exception as exc:
                log.error("heartbeat sweep calendar refresh failed: %s", exc)
                calendar_refresh_receipt = {
                    "kind": "calendar.refresh",
                    "applied": False,
                    "error": str(exc),
                }

        # HS-175-04: backfill meeting Watches for Rooms that have linked
        # meetings but no meeting Watch yet.  Idempotent (ensure_meeting_watch
        # checks before creating).  Own failure boundary.
        # HS-175 counsel C7(a): a Room with a meeting Watch in ANY state
        # (retired included) is never backfilled -- Retire is the owner's
        # word and the sweep does not take it back.
        meeting_watch_backfill: dict[str, Any] | None = None
        if not held:
            try:
                from holdspeak.services.watch_service import ensure_meeting_watch
                with self._db._connection() as conn:
                    rows = conn.execute(
                        """SELECT DISTINCT mp.project_id
                           FROM meeting_projects mp
                           WHERE NOT EXISTS (
                               SELECT 1 FROM connector_watches cw
                               WHERE cw.project_id = mp.project_id
                                 AND cw.connector_id = 'meeting'
                           )""",
                    ).fetchall()
                created = 0
                for row in rows:
                    result = ensure_meeting_watch(
                        self._db, str(row["project_id"]), why="backfill",
                    )
                    if result is not None:
                        created += 1
                if created > 0:
                    meeting_watch_backfill = {
                        "kind": "meeting_watch.backfill",
                        "created": created,
                    }
            except Exception as exc:
                log.error("heartbeat meeting watch backfill failed: %s", exc)
                meeting_watch_backfill = {
                    "kind": "meeting_watch.backfill",
                    "created": 0,
                    "error": str(exc),
                }

        # M3: Refresh the aggregate cache via the canonical builder
        self.refresh_aggregate(principal, sweep_id=sweep_id)

        duration_ms = (time.time() - t0) * 1000

        # Compute next sweep time
        sweep_minutes = settings["sweep_every_minutes"]
        next_at = (now + timedelta(minutes=sweep_minutes)).isoformat(timespec="seconds")

        # Persist timestamps
        settings["last_sweep_at"] = now.isoformat(timespec="seconds")
        settings["next_sweep_at"] = next_at
        self._persist(settings)

        # N2: Build the receipt with bounded outcomes summary
        receipt = {
            "kind": "heartbeat.sweep",
            "at": now.isoformat(timespec="seconds"),
            "rooms": rooms_evaluated,
            "watches": watch_count,
            "watches_baselined": watches_baselined,
            "watches_deferred": watches_deferred,
            "quiet_overridden": quiet_overridden,
            "duration_ms": round(duration_ms, 1),
            "held": held,
            "errors": len(errors),
            "outcomes": _summarize_outcomes(outcomes),
        }
        # HS-175-02: calendar refresh receipt rides along.
        if calendar_refresh_receipt is not None:
            receipt["calendar"] = calendar_refresh_receipt
        # HS-175-04: meeting watch backfill receipt rides along.
        if meeting_watch_backfill is not None:
            receipt["meeting_watch_backfill"] = meeting_watch_backfill

        # Write kernel receipt (Article XI.2)
        self._write_receipt(receipt)

        # Write pipeline_events
        self._write_pipeline_event(receipt, duration_ms)

        # D3 notifier: run the notification decision after every sweep.
        # Own failure boundary -- a notifier crash never breaks the loop.
        try:
            notify_receipt = self._run_notification_decision(principal, settings)
            receipt["notify"] = notify_receipt
        except Exception as exc:
            log.error("heartbeat notification decision failed: %s", exc)
            receipt["notify"] = {
                "kind": "heartbeat.notify",
                "outcome": "error",
                "error": str(exc),
            }

        return receipt

    def _write_receipt(self, receipt: dict[str, Any]) -> None:
        """Write a kernel receipt for the sweep."""
        receipt_id = f"hb_rcpt_{uuid.uuid4().hex[:12]}"
        operation_id = f"hb_op_{uuid.uuid4().hex[:12]}"
        idem_key = f"heartbeat:{receipt['at']}:{uuid.uuid4().hex[:8]}"
        now = _now_epoch()
        state = "succeeded" if not receipt.get("errors") else "failed"
        outcome = json.dumps(receipt, default=str, separators=(",", ":"))

        try:
            with self._db._connection() as conn:
                conn.execute(
                    """INSERT INTO kernel_operations
                       (operation_id, request_id, idempotency_key, name, version,
                        principal_kind, principal_identity, target_ref, placement,
                        envelope_sha256, policy_version, authority_basis,
                        state, revision, native_id, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?,?)""",
                    (
                        operation_id,
                        idem_key,
                        idem_key,
                        "heartbeat.sweep",
                        1,
                        "owner",
                        "heartbeat-service",
                        "heartbeat:sweep",
                        "local",
                        "",
                        "",
                        "heartbeat-conductor",
                        state,
                        operation_id,
                        now,
                        now,
                    ),
                )
                conn.execute(
                    """INSERT INTO kernel_receipts
                       (receipt_id, operation_id, state, outcome, result_ref, created_at)
                       VALUES (?,?,?,?,?,?)""",
                    (receipt_id, operation_id, state, outcome, "", now),
                )
        except Exception as exc:
            log.error("heartbeat receipt write failed: %s", exc)

    def _write_pipeline_event(self, receipt: dict[str, Any], duration_ms: float) -> None:
        """Write a pipeline_events row for the sweep.

        HS-174-04: propagates origin/caller/caller_identity from the
        context vars so a remote-triggered sweep carries origin=remote.
        """
        from holdspeak.services.observer import PipelineEvent, _origin, _caller, _caller_identity

        event = PipelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            service="HeartbeatService",
            method="run_sweep",
            principal_kind="owner",
            principal_identity="heartbeat-conductor",
            args_summary="{}",
            result_summary=json.dumps(
                {"watches": receipt["watches"], "rooms": receipt["rooms"],
                 "held": receipt["held"]},
                default=str, separators=(",", ":")),
            error=None if not receipt.get("errors") else f"{receipt['errors']} errors",
            error_code=None,
            duration_ms=duration_ms,
            correlation_id=str(uuid.uuid4()),
            is_async=False,
            # HS-174-04: inherit origin from the calling context.
            origin=_origin.get("local"),
            caller=_caller.get(""),
            caller_identity=_caller_identity.get(""),
        )
        try:
            self._observer.on_event(event)
        except Exception:
            pass

    # ── D3 notification decision (wired from run_sweep) ────────────────

    def _run_notification_decision(
        self, principal: Principal, settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate the notification edge after a sweep and fire if appropriate.

        HS-200-15 (AC4): the edge is the ITEM SET, not the count.  The
        notified set (``last_notified_items``, id -> project) is persisted
        in the heartbeat policy config so a restart re-notifies nothing;
        ``last_notified_count`` is kept for the settings face.  The five
        transitions are explicit -- see ``desktop_notify.ItemSetEdge`` --
        and the receipt vocabulary is: ``sent``, ``held_quiet_hours``,
        ``held_no_edge``, ``held_coverage_incomplete`` (zero items over an
        unobserved source is NOT an all-clear), ``off``, ``error``.
        """
        from holdspeak.desktop_notify import ItemSetEdge, heartbeat_notify
        from holdspeak.services.needs_you_aggregate import _item_id

        notify_mode = settings.get("notify", _DEFAULT_NOTIFY)

        # Fast path: notifications disabled.
        if notify_mode == "off":
            receipt = {"kind": "heartbeat.notify", "outcome": "off"}
            self._write_notify_receipt(receipt)
            return receipt

        # ONE aggregate build serves the count, the ids and the body.
        agg = self._build_aggregate_via_canonical(principal)
        all_items = list(agg.get("items", []))
        unmuted = [it for it in all_items if not it.get("muted")]
        count = int(agg.get("count", len(unmuted)))
        project_count = len(agg.get("projects", []))
        content_items = unmuted
        complete = bool(agg.get("complete", True))

        def _id_of(item: dict[str, Any]) -> str:
            return str(item.get("id") or _item_id(str(item.get("projectId") or ""), item))

        current_ids = {
            _id_of(it): {"project": str(it.get("projectId") or ""),
                         "class": str(it.get("rankClass") or "")}
            for it in unmuted
        }
        present_ids = {_id_of(it) for it in all_items}
        # Prune only where the Project was FULLY observed on this pass: an
        # id whose Project has any source cant_check / stale / failed stays
        # remembered (recovery re-notifies nothing); an id whose Project no
        # longer exists is dropped.  No coverage on the wire = every
        # Project observed.
        coverage = agg.get("coverage")
        observed_projects: set[str] | None
        known_projects: set[str] | None
        if isinstance(coverage, list) and coverage:
            known_projects = {
                str(row.get("project_id") or "")
                for row in coverage if row.get("project_id")
            }
            unobserved = {
                str(row.get("project_id") or "")
                for row in coverage
                if row.get("project_id") and row.get("state") != "available"
            }
            observed_projects = known_projects - unobserved
        else:
            observed_projects = None
            known_projects = None

        # Recover the persisted edge state (the notified item set).
        persisted_edge = int(settings.get("last_notified_count", 0))
        edge = ItemSetEdge(notified=_as_item_map(settings.get("last_notified_items")))

        quiet_start = settings["quiet_hours"]["start"]
        quiet_end = settings["quiet_hours"]["end"]

        # The notification decision.  The quiet-hours instant is the same
        # injectable local clock the sweep reads (HS-200-03), never a
        # second wall-clock read.
        result = heartbeat_notify(
            count,
            project_count,
            edge=edge,
            item_ids=current_ids,
            quiet_hours_start=quiet_start,
            quiet_hours_end=quiet_end,
            content_items=content_items,
            notify_content=False,
            receipt_writer=None,
            _notifier=self._notifier,
            now=self._now_local().replace(tzinfo=None),
        )

        # For mode "edge", rely on the edge detector (heartbeat_notify
        # already checked it).  For "every_sweep", skip the edge and fire
        # on any non-zero count not held by quiet hours.
        if notify_mode == "every_sweep" and not result["fired"] and result["reason"] == "no_edge":
            # Override edge: fire if count > 0 and not quiet.
            if count > 0:
                from holdspeak.desktop_notify import notify as _do_notify

                if project_count > 1:
                    body = f"{count} need you across {project_count} projects"
                else:
                    body = f"{count} need you"
                _notifier = self._notifier or _do_notify
                fired = _notifier("HoldSpeak", body, click_url=None)
                if fired:
                    edge.mark_fired(current_ids)
                result["fired"] = fired
                result["reason"] = "fired" if fired else "dispatch_failed"

        # Map to receipt vocabulary.
        if result["fired"]:
            outcome = "sent"
        elif result.get("held") and result["reason"] == "quiet_hours":
            outcome = "held_quiet_hours"
        elif result["reason"] == "no_edge" and count == 0 and not complete:
            # Zero items over an unobserved source: nothing to say, and
            # NEVER an all-clear (C4).
            outcome = "held_coverage_incomplete"
        elif result["reason"] == "no_edge":
            outcome = "held_no_edge"
        elif result["reason"] == "dispatch_failed":
            outcome = "error"
        else:
            outcome = "held_no_edge"

        receipt = {
            "kind": "heartbeat.notify",
            "outcome": outcome,
            "count": count,
            "projectCount": project_count,
            "fired": result["fired"],
            "newItems": int(result.get("newItems", 0)),
            "escalatedItems": int(result.get("escalatedItems", 0)),
            "complete": complete,
            "lastNotifiedCount": persisted_edge,
        }

        # Persist the edge state for restart survival: the notified set,
        # pruned per the recovery rule, and the count the settings face
        # shows -- written ONLY when the set or the outcome changed
        # (counsel P1-5), never on every sweep.
        before = _as_item_map(settings.get("last_notified_items"))
        edge.prune(present_ids, observed_projects, known_projects)
        after = edge.notified
        new_count = count if result["fired"] else persisted_edge
        if (after != before
                or outcome != str(settings.get("last_notify_outcome") or "")
                or new_count != persisted_edge):
            self._persist_edge(new_count, after, outcome)
        self._write_notify_receipt(receipt)
        return receipt

    def _persist_edge(
        self,
        count: int,
        notified_items: dict[str, dict[str, str]] | None = None,
        outcome: str | None = None,
    ) -> None:
        """Persist the last-notified count (and, HS-200-15, the notified
        item set and the last outcome) in the heartbeat policy config."""
        settings = self.get_settings()
        settings["last_notified_count"] = count
        if notified_items is not None:
            settings["last_notified_items"] = {k: dict(v) for k, v in notified_items.items()}
        if outcome is not None:
            settings["last_notify_outcome"] = outcome
        self._persist(settings)

    def _write_notify_receipt(self, receipt: dict[str, Any]) -> None:
        """Write a kernel receipt for the notification decision."""
        receipt_id = f"hbn_rcpt_{uuid.uuid4().hex[:12]}"
        operation_id = f"hbn_op_{uuid.uuid4().hex[:12]}"
        idem_key = f"heartbeat.notify:{_now_iso()}:{uuid.uuid4().hex[:8]}"
        now = _now_epoch()
        state = "succeeded" if receipt.get("outcome") != "error" else "failed"
        outcome_json = json.dumps(receipt, default=str, separators=(",", ":"))

        try:
            with self._db._connection() as conn:
                conn.execute(
                    """INSERT INTO kernel_operations
                       (operation_id, request_id, idempotency_key, name, version,
                        principal_kind, principal_identity, target_ref, placement,
                        envelope_sha256, policy_version, authority_basis,
                        state, revision, native_id, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?,?)""",
                    (
                        operation_id,
                        idem_key,
                        idem_key,
                        "heartbeat.notify",
                        1,
                        "owner",
                        "heartbeat-service",
                        "heartbeat:notify",
                        "local",
                        "",
                        "",
                        "heartbeat-conductor",
                        state,
                        operation_id,
                        now,
                        now,
                    ),
                )
                conn.execute(
                    """INSERT INTO kernel_receipts
                       (receipt_id, operation_id, state, outcome, result_ref, created_at)
                       VALUES (?,?,?,?,?,?)""",
                    (receipt_id, operation_id, state, outcome_json, "", now),
                )
        except Exception as exc:
            log.error("heartbeat notify receipt write failed: %s", exc)

    # ── Aggregate cache (M3: delegates to needs_you_aggregate) ─────────

    def _build_aggregate_via_canonical(
        self, principal: Principal | None = None,
    ) -> dict[str, Any]:
        """Build the aggregate via the canonical needs_you_aggregate.build_aggregate.

        M1: passes muted_project_ids from the heartbeat setting into the builder.
        Muted Rooms' items get ``muted: true`` and are excluded from ``count``
        but included in ``mutedCount``.
        """
        from holdspeak.services.needs_you_aggregate import build_aggregate
        from holdspeak.services.project_service import ProjectService

        ps = ProjectService(self._db, observer=self._observer)
        _p = principal or Principal(PrincipalKind.OWNER, "heartbeat")
        settings = self.get_settings()
        muted_ids = set(settings.get("muted_projects", []))

        aggregate = build_aggregate(
            list_projects=ps.list_projects,
            room=ps.room,
            principal=_p,
        )

        # M1: apply mute list -- mark muted items and split counts.
        items = aggregate.get("items", [])
        unmuted_items: list[dict[str, Any]] = []
        muted_count = 0
        for item in items:
            if item.get("projectId") in muted_ids:
                item["muted"] = True
                muted_count += 1
            else:
                item["muted"] = False
                unmuted_items.append(item)

        aggregate["count"] = len(unmuted_items)
        aggregate["mutedCount"] = muted_count
        return aggregate

    def refresh_aggregate(
        self, principal: Principal | None = None, *, sweep_id: str | None = None,
    ) -> dict[str, Any]:
        """Refresh the needs-you aggregate via the canonical builder.

        M3: delegates to needs_you_aggregate.build_aggregate -- this
        service does NOT re-implement the aggregate shape.
        """
        try:
            from holdspeak.services.needs_you_aggregate import NeedsYouCache

            _p = principal or Principal(PrincipalKind.OWNER, "heartbeat")

            # Build a one-shot cache and populate it.  In the live runtime
            # the NeedsYouCache lives on the route/context; here we call the
            # canonical builder directly.
            aggregate = self._build_aggregate_via_canonical(_p)
            if sweep_id:
                aggregate["sweepId"] = sweep_id
            return aggregate
        except Exception as exc:
            log.error("heartbeat aggregate refresh failed: %s", exc)
            # HS-200-07 (C4): a refresh that failed observed NOTHING; the
            # empty payload says so rather than reading as an all-clear.
            return {
                "count": 0, "projects": [], "items": [], "mutedCount": 0,
                "coverage": [{
                    "source_id": "projects", "kind": "project",
                    "state": "failed", "observed_at": None,
                    "label": "Projects", "project_id": "",
                    "reason": str(exc).split("\n")[0][:200] or type(exc).__name__,
                    "repair": {"token": "READ FAILED", "verb": "Retry",
                               "href": "/projects"},
                }],
                "complete": False,
            }

    def get_aggregate(self, principal: Principal | None = None) -> dict[str, Any]:
        """Return the aggregate (always fresh from the canonical builder)."""
        return self.refresh_aggregate(principal)

    # ── Muted-aware count for notification edge ────────────────────────

    def notification_count(self, principal: Principal | None = None) -> int:
        """M1: the count that drives the notification edge EXCLUDES muted.

        Badge = shade caption = notification = ONE count everywhere.
        """
        agg = self._build_aggregate_via_canonical(principal)
        return agg.get("count", 0)

    # ── Hub mirror ─────────────────────────────────────────────────────

    def hub_rhythm(self) -> dict[str, Any]:
        """Build the rhythm sub-object for GET /api/settings/hub."""
        settings = self.get_settings()
        # Count cadence loops
        loops = 0
        try:
            loops = len(self._db.cadence.list_loops())
        except Exception:
            pass
        return {
            "loops": loops,
            "sweepEveryMinutes": settings["sweep_every_minutes"],
            "nextSweepAt": settings.get("next_sweep_at"),
            "lastSweepAt": settings.get("last_sweep_at"),
            "quiet": {
                "start": settings["quiet_hours"]["start"],
                "end": settings["quiet_hours"]["end"],
                "held": self.in_quiet_hours(),
            },
        }

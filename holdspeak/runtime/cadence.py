"""CadenceMixin (CAD-1-04) — the in-runtime cadence tick.

Mirrors PluginQueueMixin: a daemon thread on `runtime_stop_event`, started by
WebRuntime.run() when one of its jobs is on. Two jobs, one setting each:

- the loop job (`config.cadence.enabled`, OFF by default): projects + scores
  loops, computes which are due, and pushes nudges to paired surfaces;
- the morning Brief job (`config.cadence.brief_enabled`, ON by default,
  PHILO-15 05): makes the day's Brief once per local day at
  `config.cadence.brief_hour`. Deterministic: no model, no egress.

With both jobs off the thread never starts.
"""
from __future__ import annotations

from holdspeak.timestamps import local_now
from typing import Optional

from ..logging_config import get_logger

log = get_logger("runtime.cadence")

#: The OWNER identity the scheduled morning Brief generates under.
BRIEF_PRINCIPAL_IDENTITY = "brief-conductor"


class CadenceMixin:
    def _cadence_enabled(self) -> bool:
        configured = bool(getattr(getattr(self.config, "cadence", None), "enabled", False))
        if not configured:
            return False
        from ..operation_policy import describe_operation, resolve_policy

        operation = describe_operation(
            operation_id="cadence:background-loop",
            family="sync_cadence",
            effect_class="cadence/tick",
            actor="runtime",
            destination="local_cadence_store",
            data_classes=("loop_metadata",),
            consequence="queue_executor",
        )
        return resolve_policy(
            operation,
            mode=getattr(self.config, "control_mode", "neutral"),
            source="config",
        ).outcome == "allowed"

    def _brief_job_enabled(self) -> bool:
        """The morning Brief job: ON by default (PHILO-15 05)."""
        return bool(getattr(getattr(self.config, "cadence", None), "brief_enabled", False))

    def _cadence_jobs_enabled(self) -> bool:
        """True when the cadence thread has a job to run."""
        return self._brief_job_enabled() or self._cadence_enabled()

    def _cadence_service(self):
        """Lazily build a CadenceService bound to the shared DB + config."""
        if getattr(self, "_cadence_service_obj", None) is None:
            from ..cadence.service import CadenceService
            from ..db import get_database

            self._cadence_service_obj = CadenceService(get_database(), self.config.cadence)
        return self._cadence_service_obj

    def _cadence_tick_once(self) -> None:
        from .announce_scope import announce_writes

        # The whole tick (loops, the brief push, the brief regenerate) is one
        # write with no request: ONE desk_changed frame when it changed a row.
        with announce_writes("cadence", "tick"):
            self._cadence_tick_body()

    def _cadence_tick_body(self) -> None:
        try:
            if self._cadence_enabled():
                result = self._cadence_service().tick()
                if result.due:
                    log.info(
                        "cadence tick: %d projected, %d open, %d due",
                        result.projected, result.open_loops, result.due_count,
                    )
                    self._push_due_to_telegram(result.due)
                self._maybe_push_daily_brief()
            if self._brief_job_enabled():
                self._maybe_regenerate_brief()
            self._invalidate_needs_you_cache()
        except Exception as exc:  # never let the tick crash the runtime
            log.error("cadence tick failed: %s", exc)

    def _maybe_push_daily_brief(self) -> None:
        """First-activity morning push (CAD-5): once per day, after quiet hours, send the
        brief to paired Telegram chats. Off unless the Telegram surface is active."""
        tg = getattr(self.config, "cadence_telegram", None)
        if tg is None or not tg.is_active or not tg.allowed_chat_ids:
            return
        try:

            from ..cadence.brief import should_send_daily_brief
            from ..cadence.models import CadencePolicy
            from ..cadence_telegram import TelegramSurface
            from ..db import get_database

            db = get_database()
            policy = db.cadence.get_policy("daily_brief")
            last_sent = (policy.config.get("last_sent_date") if policy else None)
            earliest = int(getattr(self.config.cadence, "quiet_hours_end", 8))
            now = local_now()
            if not should_send_daily_brief(now, last_sent_date=last_sent, earliest_hour=earliest):
                return
            surface = TelegramSurface(db, tg)
            for chat_id in tg.allowed_chat_ids:
                surface.send_brief(chat_id)
            db.cadence.upsert_policy(CadencePolicy(
                name="daily_brief", config={"last_sent_date": now.strftime("%Y-%m-%d")}))
            log.info("cadence: pushed the daily brief to %d chat(s)", len(tg.allowed_chat_ids))
        except Exception as exc:
            log.error("cadence daily brief failed: %s", exc)

    def _maybe_regenerate_brief(self) -> None:
        """HS-171-06: regenerate the Monday brief on its own cadence.

        Once per local day, at or after ``brief_hour`` (PHILO-15 05: 06:00 by
        default, so the Brief is there before the owner arrives), call
        MondayBriefService.generate().  Quiet hours do not hold it: the Brief
        is deterministic and sends nothing.  The regeneration is receipted via
        pipeline_events; the Brief shows its own GENERATED time.
        """
        try:

            from ..cadence.brief import should_send_daily_brief
            from ..cadence.models import CadencePolicy
            from ..db import get_database
            from ..principals import Principal, PrincipalKind

            db = get_database()
            policy = db.cadence.get_policy("brief_regeneration")
            last_regen = (policy.config.get("last_regen_date") if policy else None)
            earliest = int(getattr(self.config.cadence, "brief_hour", 6)) % 24
            now = local_now()
            if not should_send_daily_brief(now, last_sent_date=last_regen, earliest_hour=earliest):
                return

            from ..services.monday_brief_service import MondayBriefService

            brief_svc = MondayBriefService(db)
            # PHILO-15 05 (Astra r1 P1): the owner's own reads.  A SERVICE
            # principal is refused the assignment and decision reads, so the
            # scheduled Brief said "No changes" while the owner's Generate
            # said "1 thing waiting".  The Brief is deterministic and sends
            # nothing (the heartbeat precedent: runtime/heartbeat.py).
            brief_principal = Principal(PrincipalKind.OWNER, BRIEF_PRINCIPAL_IDENTITY)
            brief = brief_svc.generate(brief_principal, now=now)

            db.cadence.upsert_policy(CadencePolicy(
                name="brief_regeneration",
                config={"last_regen_date": now.strftime("%Y-%m-%d")},
            ))

            # Receipt via pipeline_events.
            from ..services.observer import PipelineEvent
            from ..services.sqlite_observer import SQLiteObserver
            import time as _time
            import uuid as _uuid

            observer = SQLiteObserver(db._connection)
            item_count = getattr(brief, "item_count", 0) or len(getattr(brief, "items", []))
            observer.on_event(PipelineEvent(
                event_id=str(_uuid.uuid4()),
                timestamp=_time.time(),
                service="heartbeat",
                method="brief.regenerated",
                principal_kind="service",
                principal_identity="heartbeat",
                args_summary="{}",
                result_summary=f"items={item_count}",
                error=None,
                error_code=None,
                duration_ms=0,
                correlation_id="",
                is_async=False,
            ))
            log.info("heartbeat: regenerated the Monday brief (%d items)", item_count)
        except Exception as exc:
            log.error("heartbeat brief regeneration failed: %s", exc)

    def _invalidate_needs_you_cache(self) -> None:
        """HS-171-03: invalidate the needs-you aggregate cache after a tick."""
        try:
            cache = getattr(self, "_needs_you_cache", None)
            if cache is None:
                # Try the web context's cache (set by the route builder).
                ctx = getattr(self, "_web_context", None)
                if ctx is not None:
                    cache = getattr(ctx, "_needs_you_cache", None)
            if cache is not None:
                import uuid as _uuid
                cache.invalidate(sweep_id=str(_uuid.uuid4()))
                log.debug("heartbeat: invalidated needs-you cache")
        except Exception as exc:
            log.error("heartbeat: failed to invalidate needs-you cache: %s", exc)

    def _push_due_to_telegram(self, due_loops) -> None:
        """Deliver due nudges to paired Telegram chats (CAD-4-05) — off unless the
        Telegram surface is enabled + has a token + a paired chat."""
        tg = getattr(self.config, "cadence_telegram", None)
        if tg is None or not tg.is_active or not tg.allowed_chat_ids:
            return
        try:
            from ..cadence_telegram import TelegramSurface
            from ..db import get_database

            sent = TelegramSurface(get_database(), tg).push_due_nudges(due_loops)
            if sent:
                log.info("cadence: pushed %d nudge(s) to Telegram", sent)
        except Exception as exc:
            log.error("cadence telegram push failed: %s", exc)

    def _cadence_loop(self) -> None:
        interval = max(30, int(getattr(self.config.cadence, "tick_interval_seconds", 300)))
        # An initial settle so startup isn't contended; then tick on the interval.
        while not self.runtime_stop_event.wait(interval):
            self._cadence_tick_once()

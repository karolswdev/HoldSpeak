"""Transport-neutral access to the durable dictation journal (HS-122-05)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import csv
import io
import json
from typing import Any

from ..config import Config
from ..db.core import Database
from ..principals import Principal
from holdspeak.services.errors import NotFound, ValidationError


@observe_service
class DictationService:
    def __init__(
        self,
        db: Database | None = None,
        journal_repository: Any | None = None,
        journal_available: bool = True,
        delivery_repository: Any | None = None,
        *,
        observer: PipelineObserver | None = None,
    ) -> None:
        if db is None:
            from ..db import get_database

            db = get_database()
        self._db = db
        self._journal = journal_repository if journal_available else None
        if self._journal is None and journal_available:
            self._journal = db.dictation_journal
        self._deliveries = (
            delivery_repository
            if delivery_repository is not None
            else db.dictation_deliveries
        )
        self._observer = observer or NullObserver()

    def list_journal(
        self,
        principal: Principal,
        *,
        limit: int = 200,
        cursor: int | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        from ..plugins.dictation.journal import VALID_SOURCES

        clean_source = source if source in VALID_SOURCES else None
        records: list[Any] = []
        if self._journal is not None:
            if cursor is None:
                records = self._journal.recent(limit=limit, source=clean_source)
            else:
                # HS-176-03: `before` is a PAGE cursor, so it has to bound the
                # query, not the page it produced — filtering the newest `limit`
                # rows after the fact returns nothing once the cursor is older
                # than the first page. Prefer the repository's own `before`;
                # fall back to an unbounded read + slice while it lands.
                try:
                    records = self._journal.recent(
                        limit=limit, source=clean_source, before=cursor
                    )
                except TypeError:
                    records = [
                        record
                        for record in self._journal.recent(source=clean_source)
                        if record.id < cursor
                    ][: max(0, int(limit))]
        cfg = Config.load().dictation.pipeline
        return {
            "enabled": bool(getattr(cfg, "journal_enabled", True)),
            "retention": int(getattr(cfg, "journal_retention", 500)),
            "count": self._journal.count() if self._journal is not None else 0,
            # HS-176 counsel C4: the Speak footer's `N TODAY` token. `count` is
            # the all-time RETAINED total and stays what it is (Export and the
            # journal's own trust statement read it); `today` is the count the
            # token actually claims — rows on the local calendar day.
            # `getattr` because a bare/legacy repository double may not carry
            # the method; absent-as-zero, never an error into a journal read.
            "today": self._count_today(),
            "items": [self._entry(record) for record in records],
        }

    def _count_today(self) -> int:
        if self._journal is None:
            return 0
        counter = getattr(self._journal, "count_today", None)
        if not callable(counter):
            return 0
        try:
            return int(counter())
        except Exception:
            return 0

    def get_entry(self, principal: Principal, entry_id: int) -> dict[str, Any]:
        entry = self._journal.get(entry_id) if self._journal is not None else None
        if entry is None:
            raise NotFound("journal entry", str(entry_id))
        return self._entry(entry)

    def export_journal(self, principal: Principal, format: str = "json") -> dict[str, Any]:
        entries = [
            self._entry(record)
            for record in (self._journal.recent() if self._journal is not None else [])
        ]
        if format == "json":
            return {"format": "json", "content": json.dumps(entries, indent=2, sort_keys=True)}
        if format == "csv":
            output = io.StringIO()
            fields = list(entries[0]) if entries else ["id", "created_at", "source", "transcript", "final_text"]
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for entry in entries:
                writer.writerow({key: self._csv_value(value) for key, value in entry.items()})
            return {"format": "csv", "content": output.getvalue()}
        raise ValidationError("format must be json or csv")

    def clear_journal(self, principal: Principal) -> dict[str, Any]:
        if self._journal is None:
            raise NotFound("journal", "default")
        removed = self._journal.clear()
        return {"cleared": True, "removed": removed, "count": self._journal.count()}

    def claim_delivery(
        self, principal: Principal, delivery_id: str, *, request_hash: str
    ) -> dict[str, Any]:
        clean_id = str(delivery_id or "").strip()
        if not clean_id:
            raise ValidationError("delivery_id must be a non-empty identifier")
        return self._deliveries.claim(clean_id, request_hash=request_hash)

    def complete_delivery(
        self,
        principal: Principal,
        delivery_id: str,
        *,
        response_status: int,
        response: dict[str, Any],
    ) -> None:
        self._deliveries.complete(
            delivery_id, response_status=response_status, response=response
        )

    def fail_delivery(
        self,
        principal: Principal,
        delivery_id: str,
        *,
        response_status: int,
        response: dict[str, Any],
        error: str,
    ) -> None:
        self._deliveries.fail(
            delivery_id,
            response_status=response_status,
            response=response,
            error=error,
        )

    def submit_dictation(
        self,
        principal: Principal,
        text: str,
        *,
        aim: str | None = None,
        source: str = "dictation",
    ) -> dict[str, Any]:
        clean_text = str(text or "").strip()
        if not clean_text:
            raise ValidationError("text must be a non-empty string")
        if source not in {"dictation", "dry_run", "browser", "hotkey"}:
            raise ValidationError("unknown dictation source")
        if self._journal is None:
            raise NotFound("journal", "default")
        cfg = Config.load().dictation.pipeline
        entry = self._journal.record(
            source=source,
            transcript=clean_text,
            final_text=clean_text,
            intent=aim,
            retention=int(getattr(cfg, "journal_retention", 500)),
        )
        return {"success": True, "final_text": clean_text, "entry": self._entry(entry)}

    @staticmethod
    def _csv_value(value: Any) -> Any:
        if isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True)
        return value

    @staticmethod
    def _entry(record: Any) -> dict[str, Any]:
        return {
            "id": record.id,
            "created_at": record.created_at,
            "source": record.source,
            "transcript": record.transcript,
            "final_text": record.final_text,
            "project_root": record.project_root,
            "intent": record.intent,
            "block_id": record.block_id,
            "target_profile": record.target_profile,
            "stage_ms": record.stage_ms,
            "total_ms": record.total_ms,
            "rewrite_pass_ms": record.rewrite_pass_ms,
            "confidence": record.confidence,
            "warnings": record.warnings,
            "corrected": record.corrected,
            "correction_id": record.correction_id,
            # HS-176-02 (R5): the two stored facts, split and both named.
            # `taught_from` is the existing `corrected` column under its true
            # meaning — "he taught FROM this row"; `corrections_applied` is the
            # new per-run fact — "these stored rules fired ON this row". The
            # `getattr` keeps a record shape that predates the column working.
            "taught_from": bool(record.corrected),
            "corrections_applied": [
                int(x) for x in (getattr(record, "corrections_applied", None) or [])
            ],
        }

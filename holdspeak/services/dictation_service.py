"""Transport-neutral access to the durable dictation journal (HS-122-05)."""
from __future__ import annotations

import csv
import io
import json
from typing import Any

from ..config import Config
from ..db.core import Database
from ..principals import Principal
from .primitive_service import NotFound, ValidationError


class DictationService:
    def __init__(
        self,
        db: Database,
        *,
        journal_repository: Any | None = None,
        journal_available: bool = True,
    ) -> None:
        self._db = db
        self._journal = journal_repository if journal_available else None
        if self._journal is None and journal_available:
            self._journal = db.dictation_journal

    def list_journal(
        self,
        principal: Principal,
        *,
        limit: int = 200,
        cursor: int | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        clean_source = source if source in {"dictation", "dry_run", "browser", "hotkey"} else None
        records = (
            self._journal.recent(limit=limit, source=clean_source)
            if self._journal is not None
            else []
        )
        if cursor is not None:
            records = [record for record in records if record.id < cursor]
        cfg = Config.load().dictation.pipeline
        return {
            "enabled": bool(getattr(cfg, "journal_enabled", True)),
            "retention": int(getattr(cfg, "journal_retention", 500)),
            "count": self._journal.count() if self._journal is not None else 0,
            "items": [self._entry(record) for record in records],
        }

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
        }

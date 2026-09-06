"""HS-45-01: the dictation journal recorder — a side-channel over the pipeline.

The pipeline's `on_run` hook feeds per-stage telemetry
(`telemetry_store.DictationTelemetryStore`); this recorder is its *durable*
sibling. After a pipeline run completes — the same post-run seam telemetry uses
— the live runtime (`web_runtime`) and the dry-run path
(`web/routes/dictation/_helpers`) hand the `PipelineRun` plus its surrounding
context here, and it writes one row through `db.dictation_journal`, tagged by
`source` (`"dictation"` | `"dry_run"`).

It is **best-effort and side-channel**: a journal write must never alter the
typed output or break a dictation, so every failure is swallowed. With no
repository (a bare server / a test) or `enabled=False` it is a no-op and the
dictation behaves byte-identically. The transcript + final text are redacted
when they trip the same `looks_like_secret` check the correction store uses, so
a journal row never carries a secret.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Optional

from holdspeak.project_doc_suggestions import looks_like_secret

if TYPE_CHECKING:  # pragma: no cover - typing only
    from holdspeak.db.journal import DictationJournalRepository

#: Run sources this recorder accepts (mirrors the repo's `VALID_JOURNAL_SOURCES`).
VALID_SOURCES = ("dictation", "dry_run", "browser", "hotkey")
_REDACTED = "[redacted: possible secret]"


def passthrough_run(text: str) -> Any:
    """A run-shaped record for a dictation the pipeline never touched (F-07).

    With `pipeline.enabled=false` there is no `PipelineRun`, but
    `journal_enabled` still promises the review surface a record. This carries
    exactly what `DictationJournalRecorder.record` reads: no stages, no intent,
    final text = the transcript, and a warning naming why the trace is empty.
    """
    from types import SimpleNamespace

    return SimpleNamespace(
        final_text=str(text or ""),
        stage_results=[],
        total_elapsed_ms=0.0,
        warnings=["dictation pipeline disabled"],
        intent=None,
        short_circuited=True,
    )


def filter_secret(text: str) -> str:
    """Redact the whole field if it trips the shared secret check.

    Whole-field redaction (rather than substring scrubbing) is the safe posture
    for a private journal: a known secret can never partially survive.
    """
    text = str(text or "")
    return _REDACTED if looks_like_secret(text) else text


def extract_stage_ms(run: object) -> tuple[dict[str, float], list[float]]:
    """Per-stage `elapsed_ms` + the project-rewriter's per-pass timings.

    Mirrors `telemetry_store.DictationTelemetryStore.record_run` so the journal's
    latency view matches the readiness telemetry exactly.
    """
    stage_ms: dict[str, float] = {}
    rewrite_pass_ms: list[float] = []
    for sr in getattr(run, "stage_results", []) or []:
        sid = str(getattr(sr, "stage_id", "") or "")
        if not sid:
            continue
        stage_ms[sid] = float(getattr(sr, "elapsed_ms", 0.0) or 0.0)
        meta = getattr(sr, "metadata", {}) or {}
        if sid == "project-rewriter" and meta.get("rewrite_pass_ms"):
            rewrite_pass_ms = [float(x) for x in meta["rewrite_pass_ms"]]
    return stage_ms, rewrite_pass_ms


def _target_name(target_profile: Any) -> Optional[str]:
    """A target-profile id from a `TargetProfile` object or its `to_dict` form."""
    if target_profile is None:
        return None
    tid = getattr(target_profile, "id", None)
    if tid:
        return str(tid)
    if isinstance(target_profile, dict):
        return str(target_profile.get("id") or "") or None
    return None


def _correction_ids(run: object, target_profile: Any) -> list[int]:
    """The correction ids that fired on this run, deduplicated, in order.

    Two sources (HS-176-02, ruling R2):

    - `run.corrections_applied` — the `text` rules applied at the pipeline's
      transcript seam plus the intent nudge's rule. Read with `getattr` because
      `passthrough_run` above fakes a run with a `SimpleNamespace` that has no
      such attribute (C5 note).
    - the target profile's own `details["correction_id"]`, stamped by
      `target_profile.apply_target_correction` when a `target` rule redirected
      the landing. `_target_name` drops everything but the id, so this is the
      only place the fact survives.
    """
    ids: list[int] = []
    for raw in getattr(run, "corrections_applied", ()) or ():
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value not in ids:
            ids.append(value)
    details = getattr(target_profile, "details", None)
    if isinstance(target_profile, dict):
        details = target_profile.get("details")
    if isinstance(details, dict) and details.get("correction_id") is not None:
        try:
            value = int(details["correction_id"])
        except (TypeError, ValueError):
            value = None  # type: ignore[assignment]
        if value is not None and value not in ids:
            ids.append(value)
    return ids


def _frame_from_row(row: Any) -> dict[str, Any]:
    """The `dictation.journal.entry` bus frame, built from the STORED row.

    Redaction is by construction: `record` secret-filters the transcript and
    the final text *before* the repository call, and this frame reads the row
    the repository returned — so a redacted field cannot be bypassed here.

    `taught_from` is the existing `corrected` column under its true name ("he
    taught FROM this row"); `corrections_applied` is the opposite fact (ruling
    R5). `created_at` rides along because the Journal wing's lead slot is the
    time — a live-pushed row has no other source for it.
    """
    return {
        "id": int(getattr(row, "id", 0) or 0),
        "created_at": getattr(row, "created_at", None),
        "source": getattr(row, "source", None),
        "transcript": getattr(row, "transcript", "") or "",
        "final_text": getattr(row, "final_text", "") or "",
        "total_ms": float(getattr(row, "total_ms", 0.0) or 0.0),
        "corrections_applied": [int(x) for x in (getattr(row, "corrections_applied", []) or [])],
        "taught_from": bool(getattr(row, "corrected", False)),
        "intent_tag": getattr(row, "block_id", None),
        "target_profile": getattr(row, "target_profile", None),
    }


class DictationJournalRecorder:
    """Writes one journal row per pipeline run, best-effort, secret-filtered.

    Constructed once per server with the durable repository (or None — a bare
    server / test, which makes every `record` a no-op and keeps dictation
    byte-identical). Both the live runtime and the dry-run path share the one
    instance via `server.dictation_journal`.
    """

    def __init__(
        self,
        repository: "Optional[DictationJournalRepository]" = None,
        *,
        broadcast: "Optional[Callable[[str, dict[str, Any]], None]]" = None,
    ) -> None:
        self._repository = repository
        # HS-176-02: the live-frame handle (`WebServer.broadcast`, wired at
        # `web_server.py`). It reads its event loop at call time, no-ops without
        # one, and hands off with `run_coroutine_threadsafe`, so it can neither
        # block nor raise into the dictation thread. A recorder built WITHOUT it
        # is byte-identical to the Phase 45 recorder: every bare server and
        # every test broadcasts nothing.
        self._broadcast = broadcast

    @property
    def repository(self) -> "Optional[DictationJournalRepository]":
        return self._repository

    def record(
        self,
        run: object,
        *,
        source: str,
        transcript: str,
        target_profile: Any = None,
        project_root: Any = None,
        enabled: bool = True,
        retention: Optional[int] = None,
    ) -> Any:
        """Persist one journal row for `run`; return the stored record (or None).

        Returns the `DictationJournalRecord` so a caller (the dry-run path) can
        reference the entry — e.g. to attach an in-the-moment correction
        (HS-45-03). A no-op (returns `None`) when journaling is disabled, no
        repository is attached, or the source is unknown. Never raises into the
        dictation path — every failure is swallowed and yields `None`.
        """
        if not enabled or self._repository is None:
            return None
        if str(source or "") not in VALID_SOURCES:
            return None
        try:
            intent = getattr(run, "intent", None)
            stage_ms, rewrite_pass_ms = extract_stage_ms(run)
            stored = self._repository.record(
                source=str(source),
                transcript=filter_secret(transcript),
                final_text=filter_secret(getattr(run, "final_text", "") or ""),
                intent=(getattr(intent, "raw_label", None) if intent else None),
                block_id=(getattr(intent, "block_id", None) if intent else None),
                target_profile=_target_name(target_profile),
                project_root=(str(project_root) if project_root else None),
                stage_ms=stage_ms,
                total_ms=float(getattr(run, "total_elapsed_ms", 0.0) or 0.0),
                rewrite_pass_ms=rewrite_pass_ms,
                confidence=(
                    float(getattr(intent, "confidence", 0.0))
                    if intent is not None
                    else None
                ),
                warnings=list(getattr(run, "warnings", []) or []),
                corrections_applied=_correction_ids(run, target_profile),
                retention=retention,
            )
        except Exception:  # pragma: no cover - journaling must never break typing
            return None
        self._emit(stored)
        return stored

    def _emit(self, row: Any) -> None:
        """Push one `dictation.journal.entry` frame for a stored row.

        Best-effort and side-channel like the write itself: a broadcast failure
        can never reach the dictation path. A recorder with no callable emits
        nothing.
        """
        if self._broadcast is None or row is None:
            return
        try:
            self._broadcast("dictation.journal.entry", _frame_from_row(row))
        except Exception:  # pragma: no cover - a frame must never break typing
            return

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

from typing import TYPE_CHECKING, Any, Optional

from holdspeak.project_doc_suggestions import looks_like_secret

if TYPE_CHECKING:  # pragma: no cover - typing only
    from holdspeak.db.journal import DictationJournalRepository

#: Run sources this recorder accepts (mirrors the repo's `VALID_JOURNAL_SOURCES`).
VALID_SOURCES = ("dictation", "dry_run")
_REDACTED = "[redacted: possible secret]"


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


class DictationJournalRecorder:
    """Writes one journal row per pipeline run, best-effort, secret-filtered.

    Constructed once per server with the durable repository (or None — a bare
    server / test, which makes every `record` a no-op and keeps dictation
    byte-identical). Both the live runtime and the dry-run path share the one
    instance via `server.dictation_journal`.
    """

    def __init__(
        self, repository: "Optional[DictationJournalRepository]" = None
    ) -> None:
        self._repository = repository

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
            return self._repository.record(
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
                retention=retention,
            )
        except Exception:  # pragma: no cover - journaling must never break typing
            return None

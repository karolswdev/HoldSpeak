#!/usr/bin/env python3
"""HoldSpeak dictation journal — true end-to-end proof (HS-45-01).

Drives the **real** all-features dictation pipeline against a real
OpenAI-compatible LLM endpoint (the `.43` homelab llama.cpp), exactly like the
HS-39 enrichment demo — and then journals the resulting `PipelineRun` through
the **real** `DictationJournalRepository` into a real on-disk SQLite DB, the
same code path the live runtime + dry-run use. It then reads the persisted row
back and renders the utterance's *afterlife*: what was said → how it routed →
what got typed → per-stage latency, now durable and reviewable.

This proves the Phase-45 spine end-to-end without a mic: a real run, a real DB
row, real routing/latency/target captured, secrets filtered.

Run it:

    HOLDSPEAK_DICTATION_E2E_BASE_URL=http://192.168.1.43:8080/v1 \
    HOLDSPEAK_DICTATION_E2E_MODEL=Qwen3.5-9B-UD-Q6_K_XL.gguf \
    uv run python scripts/journal_e2e_demo.py

`run_journal_e2e()` is what `tests/e2e/test_dictation_journal_e2e.py` exercises
(skipped when no endpoint is configured/reachable).
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from dictation_enrichment_demo import (  # noqa: E402
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEMO_PROJECT,
    DEMO_SPOKEN,
    SEEDED_BLOCK,
)


@dataclass
class JournalE2EResult:
    spoken: str
    enriched: str
    base_url: str
    model: str
    runtime_status: str
    # what the pipeline did
    intent_block: str | None
    intent_label: str | None
    confidence: float | None
    target_profile: str | None
    passes_run: int
    # the persisted journal row, read back from the DB
    row_id: int
    row_source: str
    row_transcript: str
    row_final_text: str
    row_intent: str | None
    row_block_id: str | None
    row_target: str | None
    row_confidence: float | None
    row_stage_ms: dict[str, float]
    row_total_ms: float
    row_rewrite_pass_ms: list[float]
    row_warnings: list[str]
    row_corrected: bool
    db_path: str

    @property
    def changed(self) -> bool:
        return self.row_final_text.strip() != self.spoken.strip()


def run_journal_e2e(
    *,
    project_dir: Path = DEMO_PROJECT,
    spoken_text: str = DEMO_SPOKEN,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    rewrite_passes: int = 2,
    timeout_seconds: float = 90.0,
    db_path: Path | None = None,
) -> JournalE2EResult:
    """Run the real pipeline once, journal it to a real DB, read the row back."""
    from holdspeak.config import DictationConfig, DictationPipelineConfig, LLMRuntimeConfig
    from holdspeak.db import Database
    from holdspeak.plugins.dictation.assembly import build_pipeline
    from holdspeak.plugins.dictation.contracts import Utterance
    from holdspeak.plugins.dictation.corrections import CorrectionStore
    from holdspeak.plugins.dictation.journal import DictationJournalRecorder
    from holdspeak.plugins.dictation.project_root import detect_project_for_cwd
    from holdspeak.target_profile import (
        apply_model_assisted_target,
        detect_target_profile_with_override,
    )

    cfg = DictationConfig(
        pipeline=DictationPipelineConfig(
            enabled=True,
            stages=["intent-router", "kb-enricher", "project-rewriter"],
            rewrite_passes=rewrite_passes,
            target_profile_override="auto",
            corrections_enabled=True,
            target_detect_llm_enabled=True,
            target_detect_llm_below=0.8,
            max_total_latency_ms=120_000,
            journal_enabled=True,
            journal_retention=500,
        ),
        runtime=LLMRuntimeConfig(
            backend="openai_compatible",
            openai_compatible_model=model,
            openai_compatible_base_url=base_url,
            openai_compatible_timeout_seconds=timeout_seconds,
        ),
    )

    project = detect_project_for_cwd(project_dir, prefer_agent_session=False)
    if project is None:
        raise RuntimeError(f"no project detected under {project_dir}")

    store = CorrectionStore()
    store.record("intent", spoken_text, SEEDED_BLOCK)

    build = build_pipeline(cfg, project_root=project_dir, corrections=store.snapshot())
    if build.runtime_status != "loaded":
        raise RuntimeError(
            f"runtime not loaded: {build.runtime_status} ({build.runtime_detail})"
        )

    hints: dict[str, Any] = {}
    heuristic = detect_target_profile_with_override(hints, "auto")
    final_target = apply_model_assisted_target(
        heuristic, runtime=build.runtime, hints=hints, text=spoken_text,
        enabled=True, below_confidence=0.8,
    )

    run = build.pipeline.run(
        Utterance(
            raw_text=spoken_text,
            audio_duration_s=0.0,
            transcribed_at=datetime.now(),
            project=project,
            activity={"target": final_target.to_dict()},
        )
    )

    # --- the actual subject under test: journal it to a real DB ---
    resolved_db = db_path or (Path(tempfile.mkdtemp(prefix="hs-journal-e2e-")) / "journal.db")
    db = Database(resolved_db)
    recorder = DictationJournalRecorder(repository=db.dictation_journal)
    wrote = recorder.record(
        run,
        source="dictation",
        transcript=spoken_text,
        target_profile=final_target,
        project_root=project_dir,
        enabled=True,
        retention=500,
    )
    if not wrote:
        raise RuntimeError("journal recorder refused to write the run")

    [row] = db.dictation_journal.recent(limit=1)
    intent = run.intent
    by_id = {s.stage_id: s for s in run.stage_results}
    pr = by_id.get("project-rewriter")
    pr_meta = dict(pr.metadata) if pr else {}

    return JournalE2EResult(
        spoken=spoken_text,
        enriched=run.final_text,
        base_url=base_url,
        model=model,
        runtime_status=build.runtime_status,
        intent_block=getattr(intent, "block_id", None),
        intent_label=getattr(intent, "raw_label", None),
        confidence=float(getattr(intent, "confidence", 0.0)) if intent else None,
        target_profile=final_target.id,
        passes_run=int(pr_meta.get("rewrite_passes_run", rewrite_passes)),
        row_id=row.id,
        row_source=row.source,
        row_transcript=row.transcript,
        row_final_text=row.final_text,
        row_intent=row.intent,
        row_block_id=row.block_id,
        row_target=row.target_profile,
        row_confidence=row.confidence,
        row_stage_ms=row.stage_ms,
        row_total_ms=row.total_ms,
        row_rewrite_pass_ms=row.rewrite_pass_ms,
        row_warnings=row.warnings,
        row_corrected=row.corrected,
        db_path=str(resolved_db),
    )


# --- rendering -------------------------------------------------------------

_ORANGE = "\x1b[38;2;255;107;53m"
_GREY = "\x1b[38;2;150;150;160m"
_GREEN = "\x1b[38;2;110;200;120m"
_BOLD = "\x1b[1m"
_RESET = "\x1b[0m"


def render(r: JournalE2EResult, *, color: bool = True) -> str:
    def c(text: str, code: str) -> str:
        return f"{code}{text}{_RESET}" if color else text

    stages = "  ".join(f"{k} {v:.0f}ms" for k, v in r.row_stage_ms.items()) or "(none)"
    passes = " + ".join(f"{ms:.0f}ms" for ms in r.row_rewrite_pass_ms) or "n/a"
    out: list[str] = [
        "",
        c("  HoldSpeak · Dictation Journal", _BOLD + _ORANGE)
        + c("   the utterance's afterlife (real run → real DB row)", _GREY),
        c(f"  model {r.model}  ·  runtime {r.runtime_status}  ·  db {r.db_path}", _GREY),
        "",
        c("  SPOKEN", _GREY) + f"   {r.spoken[:96]}…",
        c("  TYPED ", _GREY) + c(f"   {r.row_final_text[:96]}…", _GREEN),
        "",
        c("  ── persisted journal row ──────────────────────────────────", _ORANGE),
        f"  id            {r.row_id}",
        f"  source        {r.row_source}",
        f"  intent        {r.row_intent}  →  block {r.row_block_id}  @ conf "
        + (f"{r.row_confidence:.2f}" if r.row_confidence is not None else "—"),
        f"  target        {r.row_target}",
        f"  stage_ms      {stages}",
        f"  total_ms      {r.row_total_ms:.0f}",
        f"  rewrite_pass  {passes}",
        f"  warnings      {len(r.row_warnings)}",
        f"  corrected     {r.row_corrected}",
        "",
        c(f"  {len(r.spoken)} chars spoken → {len(r.row_final_text)} chars typed, "
          f"durably journaled and reviewable.", _GREY),
        "",
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    import logging

    logging.getLogger("dictation.stages.intent_router").setLevel(logging.ERROR)

    ap = argparse.ArgumentParser(description="HoldSpeak dictation journal e2e")
    ap.add_argument("--base-url", default=os.environ.get("HOLDSPEAK_DICTATION_E2E_BASE_URL", DEFAULT_BASE_URL))
    ap.add_argument("--model", default=os.environ.get("HOLDSPEAK_DICTATION_E2E_MODEL", DEFAULT_MODEL))
    ap.add_argument("--passes", type=int, default=2)
    args = ap.parse_args(argv)

    result = run_journal_e2e(base_url=args.base_url, model=args.model, rewrite_passes=args.passes)
    print(render(result, color=sys.stdout.isatty()))
    return 0 if (result.changed and result.row_source == "dictation") else 1


if __name__ == "__main__":
    raise SystemExit(main())

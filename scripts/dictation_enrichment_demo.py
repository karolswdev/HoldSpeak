#!/usr/bin/env python3
"""HoldSpeak dictation copilot — real spoken→enriched demo (HS-39).

Drives the **real** dictation pipeline (multi-pass project-rewriter, HS-39-01)
against a real OpenAI-compatible LLM endpoint, over a fixture project that has
`.hs/` context + code, and renders a before→after of rough "spoken" dictation
turning into a precise, project-grounded coding-agent task.

Run it:

    HOLDSPEAK_DICTATION_E2E_BASE_URL=http://192.168.1.43:8080/v1 \
    HOLDSPEAK_DICTATION_E2E_MODEL=Qwen3.5-9B-UD-Q6_K_XL.gguf \
    uv run python scripts/dictation_enrichment_demo.py

…or pass --base-url / --model / --spoken. The same `run_enrichment()` is what
`tests/e2e/test_dictation_enrichment_e2e.py` exercises (skipped when no
endpoint is configured/reachable).
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_PROJECT = REPO_ROOT / "tests" / "fixtures" / "dictation_demo_project"

# A realistic rambling dictation — what Whisper hands the pipeline after you
# hold the key and think out loud at a coding agent.
DEMO_SPOKEN = (
    "ok so um claude i need you to add idempotency to the charge endpoint "
    "because right now if the gateway retries we post the entry twice and the "
    "customer gets double charged which is really bad uh so use the idempotency "
    "key header that the client sends and store it somewhere and if we see the "
    "same key again just return what we returned the first time dont post "
    "another entry and yeah make sure it still balances and write a test for the "
    "retry case"
)

DEFAULT_BASE_URL = "http://192.168.1.43:8080/v1"
DEFAULT_MODEL = "Qwen3.5-9B-UD-Q6_K_XL.gguf"


@dataclass
class EnrichmentResult:
    spoken: str
    enriched: str
    project_name: str
    project_root: str
    hs_files: list[str]
    target_id: str
    model: str
    base_url: str
    rewrite_passes: int
    stage_reason: str
    suggestion: dict[str, str] | None
    elapsed_s: float
    runtime_status: str

    @property
    def changed(self) -> bool:
        return self.enriched.strip() != self.spoken.strip()


def run_enrichment(
    *,
    project_dir: Path = DEMO_PROJECT,
    spoken_text: str = DEMO_SPOKEN,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    target: str = "codex_cli",
    rewrite_passes: int = 2,
    timeout_seconds: float = 90.0,
) -> EnrichmentResult:
    """Run the real dictation pipeline once and return the before/after."""
    from holdspeak.config import DictationConfig, DictationPipelineConfig, LLMRuntimeConfig
    from holdspeak.plugins.dictation.assembly import build_pipeline
    from holdspeak.plugins.dictation.contracts import Utterance
    from holdspeak.plugins.dictation.project_root import detect_project_for_cwd
    from holdspeak.target_profile import detect_target_profile_with_override

    cfg = DictationConfig(
        pipeline=DictationPipelineConfig(
            enabled=True,
            stages=["project-rewriter"],
            rewrite_passes=rewrite_passes,
            target_profile_override=target,
            max_total_latency_ms=120_000,  # generous: this is a demo, not the live key path
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
    hs = project.get("hs") if isinstance(project, dict) else None
    _HS_KEYS = ("instructions", "context", "memory", "workflows", "issues", "terms", "targets")
    hs_files = [k for k in _HS_KEYS if isinstance(hs, dict) and str(hs.get(k) or "").strip()]

    build = build_pipeline(cfg, project_root=project_dir)
    if build.runtime_status != "loaded":
        raise RuntimeError(f"runtime not loaded: {build.runtime_status} ({build.runtime_detail})")

    target_profile = detect_target_profile_with_override({}, target)
    utt = Utterance(
        raw_text=spoken_text,
        audio_duration_s=0.0,
        transcribed_at=datetime.now(),
        project=project,
        activity={"target": target_profile.to_dict()},
    )

    start = time.perf_counter()
    run = build.pipeline.run(utt)
    elapsed = time.perf_counter() - start

    stage = run.stage_results[-1] if run.stage_results else None
    meta: dict[str, Any] = dict(stage.metadata) if stage else {}
    return EnrichmentResult(
        spoken=spoken_text,
        enriched=run.final_text,
        project_name=str(project.get("name") or project_dir.name),
        project_root=str(project.get("root") or project_dir),
        hs_files=hs_files,
        target_id=target_profile.id,
        model=model,
        base_url=base_url,
        rewrite_passes=int(meta.get("rewrite_passes_run", rewrite_passes)),
        stage_reason=str(meta.get("reason", "?")),
        suggestion=meta.get("project_doc_suggestion"),
        elapsed_s=elapsed,
        runtime_status=build.runtime_status,
    )


# --- rendering -------------------------------------------------------------

_ORANGE = (255, 107, 53)   # Signal accent
_DIM = "\x1b[2m"
_ITAL = "\x1b[3m"
_BOLD = "\x1b[1m"
_RESET = "\x1b[0m"
_GREEN = "\x1b[38;2;110;200;120m"
_GREY = "\x1b[38;2;150;150;160m"


def _use_color(flag: str | None) -> bool:
    if flag == "always":
        return True
    if flag == "never":
        return False
    return sys.stdout.isatty()


class _Paint:
    def __init__(self, on: bool) -> None:
        self.on = on

    def __call__(self, text: str, code: str) -> str:
        return f"{code}{text}{_RESET}" if self.on else text

    def orange(self, text: str) -> str:
        return self(text, f"\x1b[38;2;{_ORANGE[0]};{_ORANGE[1]};{_ORANGE[2]}m")


def _box(title: str, body: str, paint: _Paint, color: str, width: int = 78) -> str:
    inner = width - 2
    top = paint(f"┌─ {title} " + "─" * max(0, inner - len(title) - 3) + "┐", color)
    bot = paint("└" + "─" * inner + "┘", color)
    lines = [top]
    for para in body.strip().splitlines() or [""]:
        wrapped = textwrap.wrap(para, inner - 2) or [""]
        for w in wrapped:
            bar = paint("│", color)
            lines.append(f"{bar} {w.ljust(inner - 2)} {bar}")
    lines.append(bot)
    return "\n".join(lines)


_SUGGESTION_MARKER = "\n\n---\nContext preservation suggestion:"


def render(result: EnrichmentResult, *, color: bool = True) -> str:
    p = _Paint(color)
    # The rewriter appends the suggestion into the typed text; split it back out
    # so the ENRICHED box shows just the task and the suggestion gets its own box.
    task = result.enriched.split(_SUGGESTION_MARKER, 1)[0].rstrip()
    out: list[str] = []
    out.append("")
    out.append(p.orange(p("  HoldSpeak · Dictation Copilot", _BOLD)) + p("   spoken → enriched", _GREY))
    out.append(p(f"  project {result.project_name}  ·  target {result.target_id}  ·  "
                 f"model {result.model}", _GREY))
    out.append(p(f"  .hs context: {', '.join(result.hs_files) or '(none)'}  ·  "
                 f"rewrite passes: {result.rewrite_passes}", _GREY))
    out.append("")
    out.append(_box("SPOKEN  (raw dictation, what Whisper heard)",
                    result.spoken, p, _GREY))
    out.append(p("                                    │", _GREY))
    out.append(p("                                    ▼  project-aware multi-pass rewrite", _GREY))
    out.append(_box("ENRICHED  (project-grounded coding-agent task)",
                    task, p,
                    f"\x1b[38;2;{_ORANGE[0]};{_ORANGE[1]};{_ORANGE[2]}m" if color else ""))
    if result.suggestion:
        s = result.suggestion
        body = f"{s.get('target_path', '')}\n\n{s.get('rationale', '')}\n\n{s.get('content', '')}"
        out.append("")
        out.append(_box("CONTEXT-PRESERVATION SUGGESTION (.hs/, awaiting your OK)",
                        body, p, _GREEN))
    out.append("")
    delta = len(result.enriched) - len(result.spoken)
    out.append(p(f"  {len(result.spoken)} chars → {len(result.enriched)} chars "
                 f"(+{delta})  ·  {result.elapsed_s:.1f}s  ·  reason={result.stage_reason}", _GREY))
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="HoldSpeak dictation spoken→enriched demo")
    ap.add_argument("--base-url", default=os.environ.get("HOLDSPEAK_DICTATION_E2E_BASE_URL", DEFAULT_BASE_URL))
    ap.add_argument("--model", default=os.environ.get("HOLDSPEAK_DICTATION_E2E_MODEL", DEFAULT_MODEL))
    ap.add_argument("--project", default=str(DEMO_PROJECT))
    ap.add_argument("--spoken", default=DEMO_SPOKEN)
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--target", default="codex_cli")
    ap.add_argument("--color", choices=["auto", "always", "never"], default="auto")
    args = ap.parse_args(argv)

    result = run_enrichment(
        project_dir=Path(args.project),
        spoken_text=args.spoken,
        base_url=args.base_url,
        model=args.model,
        target=args.target,
        rewrite_passes=args.passes,
    )
    print(render(result, color=_use_color(args.color)))
    return 0 if result.changed else 1


if __name__ == "__main__":
    raise SystemExit(main())

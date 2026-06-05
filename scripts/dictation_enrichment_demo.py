#!/usr/bin/env python3
"""HoldSpeak dictation copilot — real all-features spoken→enriched demo (HS-39).

Drives the **real** dictation pipeline against a real OpenAI-compatible LLM
endpoint, over a fixture project with `.hs/` context + a block taxonomy + a
project KB + code, with **every Phase-39 feature firing at once**:

- HS-39-01 multi-pass rewriting (draft → critique → refine)
- HS-39-02 correction memory (a seeded session correction nudges routing)
- HS-39-03 model-assisted target detection (no window signal → infer from words)
- the kb-enricher injecting project facts for the matched block

…and renders a before→after of rough "spoken" dictation turning into a precise,
project-grounded coding-agent task, with a panel showing exactly what each
feature did.

Run it:

    HOLDSPEAK_DICTATION_E2E_BASE_URL=http://192.168.1.43:8080/v1 \
    HOLDSPEAK_DICTATION_E2E_MODEL=Qwen3.5-9B-UD-Q6_K_XL.gguf \
    uv run python scripts/dictation_enrichment_demo.py

The same `run_enrichment()` is what `tests/e2e/test_dictation_enrichment_e2e.py`
exercises (skipped when no endpoint is configured/reachable).
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

# The block the user corrected this kind of utterance to, last session (HS-39-02).
SEEDED_BLOCK = "agent_task_buildout"

DEFAULT_BASE_URL = "http://192.168.1.43:8080/v1"
DEFAULT_MODEL = "Qwen3.5-9B-UD-Q6_K_XL.gguf"

_SUGGESTION_MARKER = "\n\n---\nContext preservation suggestion:"


@dataclass
class EnrichmentResult:
    spoken: str
    enriched: str            # the typed text (task + appended suggestion)
    project_name: str
    project_root: str
    hs_files: list[str]
    model: str
    base_url: str
    runtime_status: str
    elapsed_s: float
    # HS-39-01 multi-pass
    passes_run: int
    pass_ms: list[float]
    # HS-39-02 correction memory
    seeded_correction_gist: str
    seeded_correction_block: str
    intent_block: str | None
    intent_confidence: float
    intent_corrected: bool
    correction_nudge: str | None
    router_classify_failed: bool
    # kb-enricher
    kb_applied_block: str | None
    # HS-39-03 model-assisted target
    target_heuristic_id: str
    target_heuristic_conf: float
    target_final_id: str
    target_final_conf: float
    target_final_source: str
    model_assisted_fired: bool
    # suggestion
    suggestion: dict[str, str] | None

    @property
    def task(self) -> str:
        return self.enriched.split(_SUGGESTION_MARKER, 1)[0].rstrip()

    @property
    def changed(self) -> bool:
        return self.task.strip() != self.spoken.strip()


def run_enrichment(
    *,
    project_dir: Path = DEMO_PROJECT,
    spoken_text: str = DEMO_SPOKEN,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    rewrite_passes: int = 2,
    timeout_seconds: float = 90.0,
) -> EnrichmentResult:
    """Run the real, all-features dictation pipeline once and return the result."""
    from holdspeak.config import DictationConfig, DictationPipelineConfig, LLMRuntimeConfig
    from holdspeak.plugins.dictation.assembly import build_pipeline
    from holdspeak.plugins.dictation.contracts import Utterance
    from holdspeak.plugins.dictation.corrections import CorrectionStore
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
            corrections_enabled=True,            # HS-39-02
            target_detect_llm_enabled=True,      # HS-39-03
            target_detect_llm_below=0.8,
            max_total_latency_ms=120_000,        # generous: a demo, not the live key path
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

    # HS-39-02: seed a session correction — last time, this kind of utterance was
    # misrouted, and the user corrected it to the agent-task block.
    store = CorrectionStore()
    store.record("intent", spoken_text, SEEDED_BLOCK)
    snapshot = store.snapshot()

    build = build_pipeline(cfg, project_root=project_dir, corrections=snapshot)
    if build.runtime_status != "loaded":
        raise RuntimeError(f"runtime not loaded: {build.runtime_status} ({build.runtime_detail})")

    # HS-39-03: simulate "no usable window signal" (Wayland/terminal reality) so
    # the heuristic is low-confidence and the LLM infers the target from words.
    hints: dict[str, Any] = {}
    heuristic = detect_target_profile_with_override(hints, "auto")
    final_target = apply_model_assisted_target(
        heuristic,
        runtime=build.runtime,
        hints=hints,
        text=spoken_text,
        enabled=True,
        below_confidence=0.8,
    )

    utt = Utterance(
        raw_text=spoken_text,
        audio_duration_s=0.0,
        transcribed_at=datetime.now(),
        project=project,
        activity={"target": final_target.to_dict()},
    )

    start = time.perf_counter()
    run = build.pipeline.run(utt)
    elapsed = time.perf_counter() - start

    by_id = {s.stage_id: s for s in run.stage_results}
    ir = by_id.get("intent-router")
    kb = by_id.get("kb-enricher")
    pr = by_id.get("project-rewriter")
    intent = run.intent
    pr_meta: dict[str, Any] = dict(pr.metadata) if pr else {}

    return EnrichmentResult(
        spoken=spoken_text,
        enriched=run.final_text,
        project_name=str(project.get("name") or project_dir.name),
        project_root=str(project.get("root") or project_dir),
        hs_files=hs_files,
        model=model,
        base_url=base_url,
        runtime_status=build.runtime_status,
        elapsed_s=elapsed,
        passes_run=int(pr_meta.get("rewrite_passes_run", rewrite_passes)),
        pass_ms=[float(x) for x in pr_meta.get("rewrite_pass_ms", [])],
        seeded_correction_gist=snapshot[0].key if snapshot else "",
        seeded_correction_block=SEEDED_BLOCK,
        intent_block=getattr(intent, "block_id", None),
        intent_confidence=float(getattr(intent, "confidence", 0.0) or 0.0),
        intent_corrected=bool(getattr(intent, "extras", {}).get("corrected")) if intent else False,
        correction_nudge=(dict(ir.metadata).get("correction_nudge") if ir else None),
        router_classify_failed=(bool(ir.warnings) if ir else False),
        kb_applied_block=(dict(kb.metadata).get("applied_block") if kb else None),
        target_heuristic_id=heuristic.id,
        target_heuristic_conf=heuristic.confidence,
        target_final_id=final_target.id,
        target_final_conf=final_target.confidence,
        target_final_source=final_target.source,
        model_assisted_fired=(final_target.source == "llm"),
        suggestion=pr_meta.get("project_doc_suggestion"),
    )


# --- rendering -------------------------------------------------------------

_ORANGE = (255, 107, 53)   # Signal accent
_BOLD = "\x1b[1m"
_RESET = "\x1b[0m"
_GREEN = "\x1b[38;2;110;200;120m"
_GREY = "\x1b[38;2;150;150;160m"
_BLUE = "\x1b[38;2;120;170;240m"


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

    @property
    def _orange_code(self) -> str:
        return f"\x1b[38;2;{_ORANGE[0]};{_ORANGE[1]};{_ORANGE[2]}m"

    def orange(self, text: str) -> str:
        return self(text, self._orange_code)


def _box(title: str, body: str, paint: _Paint, color: str, width: int = 78) -> str:
    inner = width - 2
    top = paint(f"┌─ {title} " + "─" * max(0, inner - len(title) - 3) + "┐", color)
    bot = paint("└" + "─" * inner + "┘", color)
    lines = [top]
    for para in body.strip().splitlines() or [""]:
        for w in (textwrap.wrap(para, inner - 2) or [""]):
            bar = paint("│", color)
            lines.append(f"{bar} {w.ljust(inner - 2)} {bar}")
    lines.append(bot)
    return "\n".join(lines)


def _features_panel(r: EnrichmentResult, p: _Paint) -> str:
    passes = " + ".join(f"{ms:.0f}ms" for ms in r.pass_ms) or "n/a"
    corrected = "✓" if r.intent_corrected else "—"
    ma = "✓ fired" if r.model_assisted_fired else "— (kept heuristic)"
    rescue = "  ← classifier missed; rescued by your correction" if r.router_classify_failed else ""
    rows = [
        p("  Features that fired this run", _BOLD),
        p("  ① multi-pass rewrite      ", _GREY) + f"{r.passes_run} passes  ({passes})",
        p("  ② correction memory       ", _GREY)
        + f"seeded intent→{r.seeded_correction_block};  router → "
        + f"{r.intent_block}@{r.intent_confidence:.2f} corrected {corrected}"
        + p(rescue, _GREY),
        p("  ③ model-assisted target   ", _GREY)
        + f"window signal: none → heuristic {r.target_heuristic_id}@{r.target_heuristic_conf:.2f} "
        + f"(<0.80) → {r.target_final_id}@{r.target_final_conf:.2f} src={r.target_final_source}  {ma}",
        p("  ④ kb-enricher injection   ", _GREY)
        + (f"block {r.kb_applied_block} → injected project facts (stack/invariants/DoD)"
           if r.kb_applied_block else "—"),
    ]
    return "\n".join(rows)


def render(result: EnrichmentResult, *, color: bool = True) -> str:
    p = _Paint(color)
    out: list[str] = []
    out.append("")
    out.append(p.orange(p("  HoldSpeak · Dictation Copilot", _BOLD))
               + p("   spoken → enriched   (all features)", _GREY))
    out.append(p(f"  project {result.project_name}  ·  model {result.model}  ·  "
                 f"{result.elapsed_s:.1f}s", _GREY))
    out.append(p(f"  .hs context: {', '.join(result.hs_files) or '(none)'}", _GREY))
    out.append("")
    out.append(_features_panel(result, p))
    out.append("")
    out.append(_box("SPOKEN  (raw dictation, what Whisper heard)", result.spoken, p, _GREY))
    out.append(p("                                    │", _GREY))
    out.append(p("                                    ▼  route · inject · multi-pass rewrite", _GREY))
    out.append(_box("ENRICHED  (project-grounded coding-agent task)",
                    result.task, p, p._orange_code if color else ""))
    if result.suggestion:
        s = result.suggestion
        body = f"{s.get('target_path', '')}\n\n{s.get('rationale', '')}\n\n{s.get('content', '')}"
        out.append("")
        out.append(_box("CONTEXT-PRESERVATION SUGGESTION (.hs/, awaiting your OK)", body, p, _GREEN))
    out.append("")
    out.append(p(f"  {len(result.spoken)} chars → {len(result.task)} chars "
                 f"(+{len(result.task) - len(result.spoken)})  ·  "
                 f"target {result.target_final_id}  ·  passes {result.passes_run}", _GREY))
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    # Keep the demo's stdout clean: the openai-compatible classify isn't
    # constrained-decoded, so the intent-router may log a parse warning — the
    # correction nudge rescues routing regardless (surfaced in the panel).
    import logging

    logging.getLogger("dictation.stages.intent_router").setLevel(logging.ERROR)

    ap = argparse.ArgumentParser(description="HoldSpeak dictation all-features demo")
    ap.add_argument("--base-url", default=os.environ.get("HOLDSPEAK_DICTATION_E2E_BASE_URL", DEFAULT_BASE_URL))
    ap.add_argument("--model", default=os.environ.get("HOLDSPEAK_DICTATION_E2E_MODEL", DEFAULT_MODEL))
    ap.add_argument("--project", default=str(DEMO_PROJECT))
    ap.add_argument("--spoken", default=DEMO_SPOKEN)
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--color", choices=["auto", "always", "never"], default="auto")
    args = ap.parse_args(argv)

    result = run_enrichment(
        project_dir=Path(args.project),
        spoken_text=args.spoken,
        base_url=args.base_url,
        model=args.model,
        rewrite_passes=args.passes,
    )
    print(render(result, color=_use_color(args.color)))
    return 0 if result.changed else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""End-to-end DIR-01 pipeline run through the `llama_cpp` backend (HS-3-03).

Goes one level higher than `tests/integration/test_runtime_llama_cpp.py`,
which only exercises `LlamaCppRuntime.classify`. This test builds the
full `DictationPipeline` (intent-router → kb-enricher) via
`assembly.build_pipeline` against a real GGUF and asserts that an
utterance matching one of the configured blocks resolves a
`{project.name}` placeholder via the kb-enricher.

Skipped cleanly when `llama-cpp-python` is not installed or the
default GGUF is not present. Per spec §13 risk #7, models are
downloaded manually.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from textwrap import dedent

import pytest

from holdspeak.config import Config
from holdspeak.plugins.dictation.contracts import Utterance


pytestmark = pytest.mark.requires_llama_cpp


DEFAULT_MODEL = Path("~/Models/gguf/Qwen2.5-3B-Instruct-Q4_K_M.gguf").expanduser()


def _have_model() -> bool:
    try:
        import llama_cpp  # noqa: F401  type: ignore[import-not-found]
    except Exception:
        return False
    return DEFAULT_MODEL.exists()


_BLOCKS_YAML = dedent(
    """
    version: 1
    default_match_confidence: 0.5
    blocks:
      - id: ai_prompt_buildout
        description: AI prompt buildout phase
        match:
          examples:
            - "Claude, build a function that..."
            - "ChatGPT, please create..."
          threshold: 0.4
        inject:
          mode: append
          template: |
            {raw_text}
            ---
            (project: {project.name})
      - id: documentation_exercise
        description: Documenting code or systems
        match:
          examples:
            - "This module is responsible for..."
          threshold: 0.4
        inject:
          mode: prepend
          template: "<!-- docs in {project.name} -->\\n{raw_text}"
    """
).strip()


@pytest.mark.skipif(
    not _have_model(),
    reason=f"llama-cpp-python and {DEFAULT_MODEL} are required for this integration test",
)
def test_full_pipeline_runs_through_llama_cpp_with_project_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Full pipeline: blocks load → router classifies → kb-enricher resolves project placeholders.

    The exact intent classification is model-driven (the test does
    not assert a specific block_id matched), but if any block matches
    above its threshold, the kb-enricher's template MUST resolve
    `{project.name}` from the detected project. The test covers both
    branches: matched-and-enriched, or unmatched-and-passthrough — what
    we forbid is a pipeline crash or a `{project.name}` placeholder
    leaking into the final text (DIR-F-007).
    """
    from holdspeak.plugins.dictation.assembly import build_pipeline
    from holdspeak.plugins.dictation.project_root import detect_project_for_cwd

    monkeypatch.setenv("HOME", str(tmp_path))
    project_root = tmp_path / "myproj"
    holdspeak_dir = project_root / ".holdspeak"
    holdspeak_dir.mkdir(parents=True)
    (holdspeak_dir / "blocks.yaml").write_text(_BLOCKS_YAML, encoding="utf-8")
    (project_root / "pyproject.toml").write_text(
        '[project]\nname = "myproj"\n', encoding="utf-8"
    )
    monkeypatch.chdir(project_root)

    project = detect_project_for_cwd()
    assert project is not None
    assert project["name"] == "myproj"

    cfg = Config()
    cfg.dictation.pipeline.enabled = True
    cfg.dictation.runtime.backend = "llama_cpp"
    cfg.dictation.runtime.llama_cpp_model_path = str(DEFAULT_MODEL)
    cfg.dictation.runtime.warm_on_start = False

    result = build_pipeline(
        cfg.dictation,
        project_root=Path(project["root"]),
        global_blocks_path=tmp_path / "no_global_blocks.yaml",  # force project-only
    )

    assert result.runtime_status == "loaded", (
        f"runtime did not load: {result.runtime_detail}"
    )
    assert len(result.blocks.blocks) == 2

    utt = Utterance(
        raw_text="Claude, build a function that returns the project name.",
        audio_duration_s=2.0,
        transcribed_at=datetime.now(),
        project=project,
    )

    run = result.pipeline.run(utt)

    # Pipeline ran end-to-end; no `{project.name}` placeholder leaked.
    assert "{project.name}" not in run.final_text
    assert isinstance(run.final_text, str)
    assert run.final_text  # non-empty
    # If the router matched, the kb-enricher resolved {project.name} → "myproj".
    # The presence of "myproj" in the final text means the matched-enriched
    # branch fired; absence means the model didn't classify above threshold,
    # which is also acceptable (DIR-F-001 — confidence below threshold is a
    # legitimate non-match).
    stage_ids = [sr.stage_id for sr in run.stage_results]
    assert "intent-router" in stage_ids
    assert "kb-enricher" in stage_ids
